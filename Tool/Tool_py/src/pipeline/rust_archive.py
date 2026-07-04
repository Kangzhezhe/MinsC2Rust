"""Rust translation archive assembly and rendering helpers.

In this project an "archive" is the persistent in-memory translation result:
`{source_name: {"extra": module_level_rust, function_name: rust_function}}`.
This module owns the code that merges new LLM output into that archive, keeps
module-level declarations/imports stable, and renders archive buckets as Rust
module text for verification/export.
"""

import copy
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from utils import (
    dedupe_non_function_content,
    is_rust_snippet_brace_balanced,
    normalize_rust_module_name,
    split_rust_code_structural,
)
from pipeline.stats import record_ast_split_result
from pipeline.rust_module_renderer import RustModuleSourceRenderer


class RustArchiveBuilder:
    """Build and maintain Rust archive buckets for `TranslationPipeline`.

    The methods live on a behavior base because they need pipeline collaborators such as
    `data_manager`, `logger`, and response-parsing helpers. Keeping them in this
    focused module makes the archive contract explicit without changing the
    legacy checkpoint/result JSON shape.
    """

    def __init__(self, module_source_renderer=None):
        self.module_source_renderer = module_source_renderer

    def _renderer(self):
        renderer = getattr(self, "module_source_renderer", None)
        if renderer is None:
            renderer = RustModuleSourceRenderer(self)
            self.module_source_renderer = renderer
        return renderer

    @staticmethod
    def _is_ident_char(ch: str) -> bool:
        return ch.isalnum() or ch == "_"

    @staticmethod
    def _iter_identifiers(text: str) -> List[str]:
        out: List[str] = []
        buf: List[str] = []
        for ch in text:
            if RustArchiveBuilder._is_ident_char(ch):
                buf.append(ch)
            elif buf:
                out.append("".join(buf))
                buf = []
        if buf:
            out.append("".join(buf))
        return out

    @staticmethod
    def _extract_function_name_from_decl_line(line: str) -> str:
        ids = RustArchiveBuilder._iter_identifiers(line or "")
        for idx, token in enumerate(ids[:-1]):
            if token == "fn":
                return ids[idx + 1]
        return ""

    @staticmethod
    def _contains_identifier(text: str, ident: str) -> bool:
        for token in RustArchiveBuilder._iter_identifiers(text):
            if token == ident:
                return True
        return False

    @staticmethod
    def _collapse_whitespace(text: str) -> str:
        return " ".join((text or "").split())

    @staticmethod
    def _strip_visibility_prefix(line: str) -> str:
        text = (line or "").lstrip()
        if text.startswith("pub "):
            return text[4:].lstrip()
        if text.startswith("pub("):
            close_idx = text.find(")")
            if close_idx != -1:
                return text[close_idx + 1 :].lstrip()
        return text

    @staticmethod
    def _starts_decl_keyword(line: str, keywords: Set[str]) -> bool:
        text = RustArchiveBuilder._strip_visibility_prefix(line)
        if not text:
            return False
        first = text.split(None, 1)[0]
        return first in keywords

    @staticmethod
    def _line_starts_with_fn_decl(line: str) -> bool:
        text = RustArchiveBuilder._strip_visibility_prefix(line)
        if not text:
            return False

        # Accept common Rust qualifiers before fn.
        prefix_tokens = []
        for token in text.replace("\t", " ").split(" "):
            if token:
                prefix_tokens.append(token)
        if not prefix_tokens:
            return False

        valid_prefix = {"unsafe", "async", "const", "extern"}
        i = 0
        while i < len(prefix_tokens):
            token = prefix_tokens[i]
            if token == "fn":
                return i + 1 < len(prefix_tokens)
            if token in valid_prefix:
                i += 1
                # extern may be followed by ABI string token, tolerate it.
                if token == "extern" and i < len(prefix_tokens) and prefix_tokens[i].startswith('"'):
                    i += 1
                continue
            return False
        return False

    @staticmethod
    def _normalize_block_key(line: str) -> str:
        stripped = RustArchiveBuilder._strip_visibility_prefix((line or "").strip())
        return RustArchiveBuilder._collapse_whitespace(stripped)

    @staticmethod
    def _tokenize_path_for_test_detection(path: str) -> List[str]:
        token = []
        out = []
        for ch in path.lower().replace("\\", "/"):
            if ch.isalnum():
                token.append(ch)
            else:
                if token:
                    out.append("".join(token))
                    token = []
        if token:
            out.append("".join(token))
        return out

    @staticmethod
    def _split_top_level_items(text: str, delimiter: str = ",") -> List[str]:
        items: List[str] = []
        buf: List[str] = []
        depth_paren = 0
        depth_brace = 0
        depth_bracket = 0
        depth_angle = 0

        for ch in text:
            if ch == "(":
                depth_paren += 1
            elif ch == ")" and depth_paren > 0:
                depth_paren -= 1
            elif ch == "{":
                depth_brace += 1
            elif ch == "}" and depth_brace > 0:
                depth_brace -= 1
            elif ch == "[":
                depth_bracket += 1
            elif ch == "]" and depth_bracket > 0:
                depth_bracket -= 1
            elif ch == "<":
                depth_angle += 1
            elif ch == ">" and depth_angle > 0:
                depth_angle -= 1

            if (
                ch == delimiter
                and depth_paren == 0
                and depth_brace == 0
                and depth_bracket == 0
                and depth_angle == 0
            ):
                token = "".join(buf).strip()
                if token:
                    items.append(token)
                buf = []
                continue

            buf.append(ch)

        tail = "".join(buf).strip()
        if tail:
            items.append(tail)
        return items

    @staticmethod
    def _extract_use_import_name(token: str, base_path: str = "") -> str:
        text = (token or "").strip()
        if not text:
            return ""

        parts = text.split()
        if len(parts) >= 3 and parts[-2] == "as":
            alias = parts[-1].strip()
            return alias if alias.isidentifier() else ""

        if text == "*":
            return ""
        if text == "self":
            last = base_path.split("::")[-1].strip()
            return last if last.isidentifier() else ""

        main = text.split("::")[-1].strip()
        if main == "self":
            last = base_path.split("::")[-1].strip()
            return last if last.isidentifier() else ""
        return main if main.isidentifier() else ""

    @staticmethod
    def _parse_use_line(line: str) -> Tuple[str, List[str]]:
        stripped = (line or "").strip()
        if not stripped or not stripped.endswith(";"):
            return "", []

        payload = stripped[:-1].strip()
        if payload.startswith("pub "):
            payload = payload[4:].lstrip()
        if not payload.startswith("use "):
            return "", []

        clause = payload[4:].strip()
        if not clause:
            return "", []

        group_marker = "::{"
        if clause.endswith("}") and group_marker in clause:
            base_path, grouped = clause.rsplit(group_marker, 1)
            grouped = grouped[:-1]
            imports = []
            for item in RustArchiveBuilder._split_top_level_items(grouped):
                name = RustArchiveBuilder._extract_use_import_name(item, base_path=base_path)
                if name:
                    imports.append(name)
            return base_path.strip(), imports

        if "::" in clause:
            base_path, token = clause.rsplit("::", 1)
            name = RustArchiveBuilder._extract_use_import_name(token, base_path=base_path)
            return base_path.strip(), [name] if name else []

        return clause.strip(), []

    @staticmethod
    def _parse_use_crate_line(line: str) -> Tuple[str, List[str]]:
        base_path, imports = RustArchiveBuilder._parse_use_line(line)
        if not base_path.startswith("crate::"):
            return "", []
        tail = base_path[len("crate::") :]
        if not tail:
            return "", []
        module_name = tail.split("::", 1)[0].strip()
        if not module_name.isidentifier():
            return "", []
        return module_name, imports

    @staticmethod
    def _extract_decl_name(line: str) -> Tuple[str, str]:
        text = RustArchiveBuilder._strip_visibility_prefix(line)
        if not text:
            return "", ""
        tokens = [tok for tok in text.replace("\t", " ").split(" ") if tok]
        if len(tokens) < 2:
            return "", ""

        kind = tokens[0]
        if kind not in {"type", "struct", "enum", "trait", "const", "static", "union"}:
            return "", ""

        name_token_idx = 1
        if kind == "static" and len(tokens) >= 3 and tokens[1] == "mut":
            name_token_idx = 2
        if name_token_idx >= len(tokens):
            return "", ""

        ident_buf: List[str] = []
        for ch in tokens[name_token_idx]:
            if RustArchiveBuilder._is_ident_char(ch):
                ident_buf.append(ch)
            else:
                break
        name = "".join(ident_buf)
        return kind, name if name.isidentifier() else ""

    @staticmethod
    def _is_basic_delimiter_balanced(text: str) -> bool:
        if not text:
            return True

        stack: List[str] = []
        in_string = ""
        in_line_comment = False
        in_block_comment = False
        i = 0
        n = len(text)

        while i < n:
            ch = text[i]
            nxt = text[i + 1] if i + 1 < n else ""

            if in_line_comment:
                if ch == "\n":
                    in_line_comment = False
                i += 1
                continue

            if in_block_comment:
                if ch == "*" and nxt == "/":
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue

            if in_string:
                if ch == "\\":
                    i += 2
                    continue
                if ch == in_string:
                    in_string = ""
                i += 1
                continue

            if ch == "/" and nxt == "/":
                in_line_comment = True
                i += 2
                continue
            if ch == "/" and nxt == "*":
                in_block_comment = True
                i += 2
                continue
            if ch == '"':
                in_string = ch
                i += 1
                continue

            # Rust lifetime markers like `'a` / `'static` are not char literals.
            # Treat them as normal code tokens so they do not break balance checks.
            if ch == "'":
                after = text[i + 1] if i + 1 < n else ""
                after2 = text[i + 2] if i + 2 < n else ""
                if (after.isalpha() or after == "_") and after2 != "'":
                    i += 1
                    continue

                # Best-effort skip for Rust char literals (e.g. 'x', '\\n', '\\'').
                j = i + 1
                escaped = False
                closed = False
                while j < n:
                    cj = text[j]
                    if escaped:
                        escaped = False
                        j += 1
                        continue
                    if cj == "\\":
                        escaped = True
                        j += 1
                        continue
                    if cj == "'":
                        closed = True
                        break
                    if cj == "\n":
                        break
                    j += 1

                if closed:
                    i = j + 1
                    continue
                i += 1
                continue

            if ch in {"(", "[", "{"}:
                stack.append(ch)
            elif ch in {")", "]", "}"}:
                if not stack:
                    return False
                left = stack.pop()
                if (left, ch) not in {("(", ")"), ("[", "]"), ("{", "}")}:
                    return False
            i += 1

        return not stack and not in_block_comment and not in_string

    def _apply_response_to_archive(
        self,
        response_code: str,
        func_name: str,
        source_name: str,
        include_files: List[str],
        base_archive: Dict[str, Dict[str, str]],
        allowed_function_names: Optional[Set[str]] = None,
        enforce_forbidden_tokens: bool = True,
    ) -> Tuple[Optional[Dict[str, Dict[str, str]]], str]:
        """Merge one LLM response into a copied archive bucket.

        The method is intentionally defensive: model responses can contain
        helper functions, module-level declarations, or truncated code. Invalid
        fragments are rejected before they can corrupt the checkpoint-compatible
        `results.json` structure.
        """
        response_code, _, _ = self._extract_editable_function_directives(response_code)
        if enforce_forbidden_tokens:
            forbidden_hits = self._find_forbidden_c_pointer_tokens(response_code)
            if forbidden_hits:
                return (
                    None,
                    "LLM 输出包含被禁止类型（任何命名空间的 c_void 或 void* 均禁止）: "
                    + ", ".join(forbidden_hits),
                )

        split = split_rust_code_structural(response_code, tmp_dir=None)
        record_ast_split_result(split.ast_ok, split.fallback_used)
        if split.fallback_used:
            self.logger.info(
                f"[AST-SPLIT-FALLBACK] {source_name}:{func_name} {split.diagnostic}"
            )
        non_function_content = split.non_function_content
        function_content_dict = split.function_content_dict

        dropped_fn_names = []
        sanitized_functions = {}
        for name, code in function_content_dict.items():
            trimmed = self._trim_to_function_definition(code)
            if (
                trimmed
                and is_rust_snippet_brace_balanced(trimmed)
                and self._is_basic_delimiter_balanced(trimmed)
            ):
                sanitized_functions[name] = trimmed
            else:
                dropped_fn_names.append(name)
        function_content_dict = sanitized_functions
        if dropped_fn_names:
            self.logger.info(
                f"[FN-DROP] {source_name}:{func_name} dropped malformed functions: {', '.join(dropped_fn_names[:8])}"
            )
            if func_name in dropped_fn_names:
                return None, f"LLM 输出中的目标函数 {func_name} 语法不完整（括号/分隔符不匹配或函数体截断）。"

        response_local_helpers_for_allowed: Set[str] = set()
        if allowed_function_names is not None:
            allowed_roots_in_response = {
                name for name in function_content_dict.keys() if name in allowed_function_names
            }
            response_local_helpers_for_allowed = self._collect_response_local_helpers_for_roots(
                allowed_roots_in_response,
                function_content_dict,
            )
            filtered_function_content_dict: Dict[str, str] = {}
            dropped_disallowed: List[str] = []
            for name, code in function_content_dict.items():
                if name in allowed_function_names or name in response_local_helpers_for_allowed:
                    filtered_function_content_dict[name] = code
                else:
                    dropped_disallowed.append(name)
            function_content_dict = filtered_function_content_dict
            if dropped_disallowed:
                self.logger.info(
                    f"[FN-WHITELIST-DROP] {source_name}:{func_name} dropped disallowed functions: {', '.join(dropped_disallowed[:8])}"
                )

        source_bucket = base_archive.get(source_name, {})
        has_existing_target = func_name in source_bucket and bool(source_bucket.get(func_name, "").strip())
        has_meaningful_patch = self._is_meaningful_patch_content(non_function_content)

        if not function_content_dict:
            if has_existing_target and has_meaningful_patch:
                function_content_dict = {}
            else:
                return None, "LLM 输出无法解析到任何 Rust 函数定义。"

        if func_name not in function_content_dict:
            if has_existing_target:
                if not has_meaningful_patch:
                    return None, f"LLM 修复响应缺少目标函数 {func_name} 且未提供有效补丁内容。"
                # Patch mode: keep previous target function and merge returned fixes.
                self.logger.info(
                    f"[PATCH-MODE] {source_name}:{func_name} fix response missing target, reusing previous target implementation"
                )
            elif len(function_content_dict) == 1:
                only_name = next(iter(function_content_dict))
                function_content_dict = {func_name: function_content_dict[only_name]}
            else:
                return None, f"LLM 输出缺少目标函数 {func_name}。"

        candidate_results = copy.deepcopy(base_archive)
        candidate_results.setdefault(source_name, {})

        if non_function_content.strip():
            if self._is_test_source(source_name):
                if split.ast_ok:
                    sanitized_extra = non_function_content.strip()
                else:
                    sanitized_extra = self._sanitize_non_function_content(non_function_content)
            else:
                # For non-test modules keep full prelude/type declarations; over-sanitizing
                # can erase essential types and cause cascaded unresolved-symbol failures.
                sanitized_extra = dedupe_non_function_content(non_function_content).strip()
            if (
                sanitized_extra
                and is_rust_snippet_brace_balanced(sanitized_extra)
                and self._is_basic_delimiter_balanced(sanitized_extra)
            ):
                old_extra = candidate_results[source_name].get("extra", "")
                merged_extra = self._merge_extra(old_extra, sanitized_extra)
                candidate_results[source_name]["extra"] = merged_extra
            else:
                self.logger.info(
                    f"[EXTRA-DROP] {source_name}:{func_name} dropped unsupported or malformed non-function content"
                )

        allow_cross_module_writeback = bool(self.params.get("allow_cross_module_writeback", 0))
        local_response_helpers = self._collect_response_local_helpers_for_roots(
            {func_name} | (set(allowed_function_names or set()) & set(function_content_dict.keys())),
            function_content_dict,
        )

        for name, code in function_content_dict.items():
            owner = self.data_manager.get_source_name_by_func_name(
                name,
                respect_scope=False,
            )
            explicitly_allowed_cross_module = bool(allowed_function_names is not None and name in allowed_function_names)
            if not owner:
                if name == func_name:
                    owner = source_name
                elif name in local_response_helpers:
                    owner = source_name
                    self.logger.info(
                        f"[OWNER-LOCAL-FALLBACK] {source_name}:{func_name} accepted {name} into {source_name} (owner unresolved, referenced by target)"
                    )
                else:
                    self.logger.info(
                        f"[OWNER-UNKNOWN-DROP] {source_name}:{func_name} dropped {name} (owner unresolved)"
                    )
                    continue

            if owner not in include_files:
                if name == func_name:
                    owner = source_name
                else:
                    self.logger.info(
                        f"[OWNER-OUTSIDE-SCOPE-DROP] {source_name}:{func_name} dropped {name} owner={owner}"
                    )
                    continue

            owner_bucket = candidate_results.get(owner, {})
            owner_bucket_empty = self._is_effectively_empty_bucket(owner_bucket)

            # Keep repairs module-local by default to avoid contaminating dependency modules
            # with speculative rewrites returned in the same LLM response.
            if (not allow_cross_module_writeback) and owner != source_name and not owner_bucket_empty and not explicitly_allowed_cross_module:
                self.logger.info(
                    f"[CROSS-MODULE-DROP] {source_name}:{func_name} dropped {name} owned by {owner}"
                )
                continue
            if (not allow_cross_module_writeback) and owner != source_name and owner_bucket_empty and not explicitly_allowed_cross_module:
                self.logger.info(
                    f"[CROSS-MODULE-BOOTSTRAP] {source_name}:{func_name} accepted {name} into empty {owner}"
                )
            if (not allow_cross_module_writeback) and owner != source_name and explicitly_allowed_cross_module:
                self.logger.info(
                    f"[CROSS-MODULE-EDITABLE] {source_name}:{func_name} accepted {name} owned by {owner} via editable whitelist"
                )

            candidate_results.setdefault(owner, {})
            normalized_code = code.strip() + "\n"
            if not self._is_test_source(owner):
                normalized_code = self._ensure_public_function(normalized_code)

            existing_owner_fn = str(base_archive.get(owner, {}).get(name, "") or "")
            if (
                existing_owner_fn.strip()
                and not self._is_cycle_placeholder_function(existing_owner_fn)
                and self._is_cycle_placeholder_function(normalized_code)
            ):
                self.logger.info(
                    f"[PLACEHOLDER-OVERWRITE-DROP] {source_name}:{func_name} keep existing {owner}:{name}"
                )
                continue

            candidate_results[owner][name] = normalized_code

        # Keep extra/import topology in sync so results-style archives are directly reusable.
        self.sync_archive_imports(candidate_results, include_files=include_files)

        return candidate_results, ""

    @staticmethod
    def _is_effectively_empty_bucket(bucket: Dict[str, str]) -> bool:
        if not bucket:
            return True
        if (bucket.get("extra") or "").strip():
            return False
        for key, value in bucket.items():
            if key == "extra":
                continue
            if (value or "").strip():
                return False
        return True

    @staticmethod
    def _is_meaningful_patch_content(non_function_content: str) -> bool:
        text = (non_function_content or "").strip()
        if len(text) < 80:
            return False
        markers = ["use ", "pub ", "impl ", "struct ", "enum ", "type ", "const ", "static ", "fn "]
        lowered = text.lower()
        return any(marker in lowered for marker in markers)

    @staticmethod
    def _merge_extra(existing: str, incoming: str) -> str:
        """Merge module-level Rust declarations by identity instead of appending.

        `extra` commonly contains `use`, `struct`, `type`, `const`, `static`, and
        `impl` blocks. Replacing blocks with the same declaration key prevents
        LLM repair rounds from accumulating stale duplicate definitions.
        """
        incoming = dedupe_non_function_content(incoming).strip()
        existing = dedupe_non_function_content(existing).strip()
        if not incoming:
            return existing
        if not existing:
            return incoming + "\n"

        def split_blocks(text: str) -> List[str]:
            return RustArchiveBuilder._split_extra_blocks(text)

        def block_key(block: str) -> str:
            for line in block.splitlines():
                stripped = line.strip()
                if stripped:
                    if stripped.startswith("#") or stripped.startswith("//"):
                        continue
                    kind, symbol = RustArchiveBuilder._extract_decl_name(stripped)
                    if symbol:
                        # Key declarations by symbol identity so `Type` and `Type<T>`
                        # redefinitions are merged rather than accumulated.
                        return f"decl:{kind}:{symbol}"
                    return RustArchiveBuilder._normalize_block_key(stripped)
            fallback = block.strip()
            return RustArchiveBuilder._normalize_block_key(fallback)

        merged_blocks = []
        index_by_key = {}

        for block in split_blocks(existing):
            key = block_key(block)
            if key and key not in index_by_key:
                index_by_key[key] = len(merged_blocks)
                merged_blocks.append(block)

        for block in split_blocks(incoming):
            key = block_key(block)
            if not key:
                continue
            if key in index_by_key:
                merged_blocks[index_by_key[key]] = block
            else:
                index_by_key[key] = len(merged_blocks)
                merged_blocks.append(block)

        merged = "\n\n".join(merged_blocks).strip()
        if not merged:
            return ""
        return RustArchiveBuilder._dedupe_use_statements(merged).strip() + "\n"

    @staticmethod
    def _split_extra_blocks(text: str) -> List[str]:
        blocks = []
        current = []
        for line in (text or "").splitlines():
            stripped = line.strip()
            if not stripped:
                if current:
                    blocks.append("\n".join(current).strip())
                    current = []
                continue

            if stripped.startswith("use ") or stripped.startswith("pub use ") or stripped.startswith("extern crate "):
                if current:
                    blocks.append("\n".join(current).strip())
                    current = []
                blocks.append(line.rstrip().strip())
                continue

            current.append(line.rstrip())

        if current:
            blocks.append("\n".join(current).strip())
        return [block for block in blocks if block]

    @staticmethod
    def _extract_decl_symbol_from_block(block: str) -> Tuple[str, str]:
        for raw_line in (block or "").splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue
            return RustArchiveBuilder._extract_decl_name(stripped)
        return "", ""

    def _extract_decl_blocks(self, extra_content: str) -> Dict[str, str]:
        blocks: Dict[str, str] = {}
        for block in self._split_extra_blocks(extra_content):
            _, symbol = self._extract_decl_symbol_from_block(block)
            if symbol:
                blocks[symbol] = block
        return blocks

    def _preserve_owned_declaration_blocks(
        self,
        source_name: str,
        candidate_extra: str,
        previous_extra: str,
    ) -> Tuple[str, List[str]]:
        """Restore source-owned declarations that a later repair response dropped.

        Ownership comes from `DataManager`; this protects declarations whose
        canonical home is the current C source while still allowing declarations
        owned by other modules to be pruned or imported.
        """
        previous_blocks = self._extract_decl_blocks(previous_extra)
        if not previous_blocks:
            return (candidate_extra or "").strip(), []

        current_blocks = self._extract_decl_blocks(candidate_extra)
        merged_extra = (candidate_extra or "").strip()
        restored: List[str] = []

        for symbol, block in previous_blocks.items():
            if self.data_manager.get_decl_owner(symbol) != source_name:
                continue
            if symbol in current_blocks:
                continue
            merged_extra = self._merge_extra(merged_extra, block).strip() if merged_extra else block.strip()
            restored.append(symbol)

        return merged_extra, restored

    @staticmethod
    def _match_static_mut_counter_name(line: str) -> str:
        text = (line or "").strip()
        if not text:
            return ""

        # Support `pub`, `pub(crate)` visibility prefixes.
        if text.startswith("pub("):
            close_idx = text.find(")")
            if close_idx == -1:
                return ""
            text = text[close_idx + 1 :].lstrip()
        elif text.startswith("pub "):
            text = text[4:].lstrip()

        if not text.startswith("static"):
            return ""
        text = text[len("static") :].lstrip()
        if not text.startswith("mut"):
            return ""
        text = text[len("mut") :].lstrip()
        if not text:
            return ""

        ident_token = text.split(None, 1)[0]
        ident = ident_token.split(":", 1)[0].rstrip(";")
        return ident if ident.isidentifier() else ""

    @staticmethod
    def _sanitize_non_function_content(non_function_content: str) -> str:
        """Keep test prelude declarations while filtering obvious non-declaration noise."""
        text = non_function_content.strip()
        if not text:
            return ""

        lines = text.splitlines()
        kept_lines: List[str] = []
        pending_blank = False
        seen_static_mut_names: Set[str] = set()

        def append_line(raw: str) -> None:
            nonlocal pending_blank
            kept_lines.append(raw.rstrip())
            pending_blank = False

        def append_blank() -> None:
            nonlocal pending_blank
            if kept_lines and not pending_blank:
                kept_lines.append("")
                pending_blank = True

        def collect_until_semicolon(start_idx: int) -> Tuple[List[str], int]:
            block: List[str] = []
            idx = start_idx
            while idx < len(lines):
                block.append(lines[idx].rstrip())
                if ";" in lines[idx]:
                    return block, idx + 1
                idx += 1
            return block, idx

        def collect_brace_block(start_idx: int) -> Tuple[List[str], int]:
            block: List[str] = []
            idx = start_idx
            depth = 0
            seen_open = False
            while idx < len(lines):
                ln = lines[idx]
                block.append(ln.rstrip())
                opens = ln.count("{")
                closes = ln.count("}")
                if opens > 0:
                    seen_open = True
                depth += opens
                depth -= closes
                idx += 1
                if seen_open and depth <= 0:
                    break
            return block, idx

        i = 0
        while i < len(lines):
            line = lines[i]
            s = line.strip()
            if not s:
                append_blank()
                i += 1
                continue

            if s.startswith("#[") or s.startswith("#!["):
                append_line(line)
                i += 1
                continue
            if s.startswith("//") or s.startswith("/*") or s.startswith("*/") or s.startswith("*"):
                append_line(line)
                i += 1
                continue
            stripped_vis = RustArchiveBuilder._strip_visibility_prefix(s)
            if stripped_vis.startswith("use ") or s.startswith("extern crate"):
                block, i = collect_until_semicolon(i)
                for ln in block:
                    append_line(ln)
                continue
            counter_name = RustArchiveBuilder._match_static_mut_counter_name(s)
            if counter_name:
                if counter_name in seen_static_mut_names:
                    i += 1
                    continue
                seen_static_mut_names.add(counter_name)
                append_line(line)
                i += 1
                continue

            # Preserve common module-level declaration forms used by translated C tests.
            if RustArchiveBuilder._starts_decl_keyword(s, {"const", "static", "type"}):
                block, i = collect_until_semicolon(i)
                normalized_block = RustArchiveBuilder._normalize_test_decl_block(block)
                for ln in normalized_block:
                    append_line(ln)
                continue

            if RustArchiveBuilder._starts_decl_keyword(s, {"struct", "enum", "union", "trait"}) or stripped_vis.startswith("impl"):
                block, i = collect_brace_block(i)
                for ln in block:
                    append_line(ln)
                continue

            if stripped_vis.startswith("macro_rules!"):
                block, i = collect_brace_block(i)
                for ln in block:
                    append_line(ln)
                continue

            if s.endswith(";") and " fn " not in f" {s} ":
                append_line(line)
                i += 1
                continue

            # Drop residual non-declaration fragments to avoid polluting module prelude.
            i += 1

        return "\n".join(kept_lines).strip()

    @staticmethod
    def _is_test_source(source_name: str) -> bool:
        if not source_name:
            return False
        tokens = RustArchiveBuilder._tokenize_path_for_test_detection(source_name)
        return any(token in {"test", "tests"} for token in tokens)

    @staticmethod
    def _normalize_test_decl_block(block_lines: List[str]) -> List[str]:
        if not block_lines:
            return block_lines
        first = (block_lines[0] or "").strip()
        kind, symbol = RustArchiveBuilder._extract_decl_name(first)
        merged = " ".join((ln or "").strip() for ln in block_lines)
        if kind == "static" and symbol and ".map(" in merged and "String" in merged:
            return [f"pub static mut {symbol}: [[u8; 10]; 10000] = [[0; 10]; 10000];"]
        return [ln.rstrip() for ln in block_lines]

    @staticmethod
    def _ensure_public_function(fn_code: str) -> str:
        """Promote module-level helper functions to pub for cross-module visibility."""
        lines = fn_code.splitlines(True)
        for idx, raw in enumerate(lines):
            stripped = raw.lstrip()
            if not stripped:
                continue
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            if not RustArchiveBuilder._line_starts_with_fn_decl(stripped):
                continue
            if stripped.startswith("pub ") or stripped.startswith("pub("):
                return fn_code
            indent = raw[: len(raw) - len(stripped)]
            lines[idx] = f"{indent}pub {stripped}"
            return "".join(lines)
        return fn_code

    @staticmethod
    def _trim_to_function_definition(fn_code: str) -> str:
        """Drop any non-function prelude accidentally attached to a function chunk."""
        offset = 0
        for raw in fn_code.splitlines(True):
            stripped = raw.strip()
            if stripped and RustArchiveBuilder._line_starts_with_fn_decl(stripped):
                return fn_code[offset:].strip() + "\n"
            offset += len(raw)
        return ""

    @staticmethod
    def _cleanup_test_module_text(module_text: str, module_name: str = "") -> str:
        """Remove duplicated test prelude declarations that conflict with dependency imports."""
        if "use crate::" not in module_text:
            return module_text

        lines = module_text.splitlines()
        # Track brace depth before each line so cleanup rules only target module-level
        # declarations and never remove nested local helpers inside function bodies.
        depth_before_line: List[int] = [0] * len(lines)
        running_depth = 0
        for idx, raw_line in enumerate(lines):
            depth_before_line[idx] = running_depth
            running_depth += raw_line.count("{") - raw_line.count("}")
            if running_depth < 0:
                running_depth = 0

        local_fn_symbols: Set[str] = set()
        for idx, raw_line in enumerate(lines):
            if depth_before_line[idx] != 0:
                continue
            stripped = raw_line.strip()
            if not RustArchiveBuilder._line_starts_with_fn_decl(stripped):
                continue
            fn_name = RustArchiveBuilder._extract_function_name_from_decl_line(stripped)
            if fn_name:
                local_fn_symbols.add(fn_name)

        imported_symbols: Set[str] = set()
        for raw_line in lines:
            _, names = RustArchiveBuilder._parse_use_crate_line(raw_line.strip())
            for name in names:
                if name.isidentifier() and name not in local_fn_symbols:
                    imported_symbols.add(name)

        _ = module_name
        if not imported_symbols and not local_fn_symbols:
            return module_text

        kept: List[str] = []
        seen_decl_symbols: Set[str] = set()
        seen_fn_symbols: Set[str] = set()
        i = 0

        def skip_brace_block(start_idx: int) -> int:
            idx = start_idx
            depth = 0
            seen_open = False
            while idx < len(lines):
                opens = lines[idx].count("{")
                closes = lines[idx].count("}")
                if opens > 0:
                    seen_open = True
                depth += opens
                depth -= closes
                idx += 1
                if seen_open and depth <= 0:
                    break
            return idx

        def drop_trailing_type_attributes() -> None:
            while kept:
                tail = kept[-1].strip()
                if tail.startswith("#[") or tail.startswith("#!") or tail.startswith("///"):
                    kept.pop()
                    continue
                break

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            is_top_level_line = depth_before_line[i] == 0

            dep_module, dep_imports = RustArchiveBuilder._parse_use_crate_line(stripped)
            if dep_module and dep_imports:
                filtered_imports: List[str] = []
                seen_imports: Set[str] = set()
                for name in dep_imports:
                    if name in local_fn_symbols:
                        continue
                    if not name.isidentifier() or name in seen_imports:
                        continue
                    seen_imports.add(name)
                    filtered_imports.append(name)

                if filtered_imports != dep_imports:
                    if filtered_imports:
                        if len(filtered_imports) == 1:
                            kept.append(f"use crate::{dep_module}::{filtered_imports[0]};")
                        else:
                            kept.append(
                                f"use crate::{dep_module}::{{{', '.join(filtered_imports)}}};"
                            )
                    i += 1
                    continue

            kind, symbol = RustArchiveBuilder._extract_decl_name(stripped)
            if symbol:
                if symbol in seen_decl_symbols:
                    if kind in {"struct", "enum", "trait", "union"}:
                        drop_trailing_type_attributes()
                        i = skip_brace_block(i)
                    else:
                        i += 1
                    continue
                if symbol in imported_symbols:
                    # Keep local const/static fixtures to avoid reintroducing unresolved
                    # values when imported names are incomplete or unstable.
                    if kind in {"const", "static"}:
                        seen_decl_symbols.add(symbol)
                        kept.append(line)
                        i += 1
                        continue
                    if kind in {"struct", "enum", "trait", "union"}:
                        drop_trailing_type_attributes()
                        i = skip_brace_block(i)
                    else:
                        i += 1
                    continue
                seen_decl_symbols.add(symbol)

            if RustArchiveBuilder._line_starts_with_fn_decl(stripped) and is_top_level_line:
                fn_name = ""
                ids = RustArchiveBuilder._iter_identifiers(stripped)
                for idx, token in enumerate(ids[:-1]):
                    if token == "fn":
                        fn_name = ids[idx + 1]
                        break
                if not fn_name:
                    kept.append(line)
                    i += 1
                    continue
                if fn_name in seen_fn_symbols:
                    i = skip_brace_block(i)
                    continue
                seen_fn_symbols.add(fn_name)

            if stripped.startswith("impl") and imported_symbols:
                if any(RustArchiveBuilder._contains_identifier(stripped, sym) for sym in imported_symbols):
                    i = skip_brace_block(i)
                    continue

            kept.append(line)
            i += 1

        body = "\n".join(kept).strip()
        # Keep cleanup generic: do not apply symbol-name-specific rewrites.

        return body.strip() + "\n"

    @staticmethod
    def _drop_self_module_use_imports(module_text: str, module_name: str) -> str:
        """Remove `use crate::<self_module>::...` imports that reimport local symbols.

        This prevents E0255 conflicts where a module imports symbols from itself,
        then defines those symbols again in the same module.
        """
        if not module_text or not module_name:
            return module_text

        lines = module_text.splitlines()
        rewritten: List[str] = []

        for line in lines:
            stripped = line.strip()
            dep_module, _dep_imports = RustArchiveBuilder._parse_use_crate_line(stripped)
            if dep_module == module_name:
                # Drop all self-module imports unconditionally.
                continue
            rewritten.append(line)

        body = "\n".join(rewritten).strip()
        if not body:
            return ""
        return body + "\n"

    @staticmethod
    def _normalize_multiline_use_statements(module_text: str) -> str:
        """Collapse multi-line `use ...::{ ... };` blocks before import dedupe."""
        lines = (module_text or "").splitlines()
        normalized: List[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            starts_use = stripped.startswith("use ") or stripped.startswith("pub use ")
            if not starts_use:
                normalized.append(line)
                i += 1
                continue

            block = [line]
            i += 1
            while ";" not in block[-1] and i < len(lines):
                block.append(lines[i])
                i += 1

            if len(block) == 1:
                normalized.append(block[0])
                continue

            collapsed = " ".join(part.strip() for part in block if part.strip())
            normalized.append(collapsed)

        return "\n".join(normalized)

    @staticmethod
    def _dedupe_use_statements(module_text: str) -> str:
        """Drop duplicate `use ...;` lines introduced by iterative merges.

        Also canonicalize equivalent forms like `use a::x;` and `use a::{x};`
        to prevent E0252 from syntax-only duplication.
        """
        module_text = RustArchiveBuilder._normalize_multiline_use_statements(module_text)
        lines = module_text.splitlines()
        seen_use_keys: Set[str] = set()
        kept: List[str] = []
        grouped_symbols: Dict[str, Set[str]] = defaultdict(set)
        grouped_order: List[str] = []
        marker_prefix = "__USE_GROUP_MARKER__"
        marker_index = 0

        def can_group_use(stripped: str, base_path: str, symbols: List[str]) -> bool:
            if not base_path or not symbols:
                return False
            if stripped.startswith("pub use "):
                return False
            if " as " in stripped:
                return False
            if "*" in stripped:
                return False
            return True

        for line in lines:
            stripped = line.strip()
            base_path, symbols = RustArchiveBuilder._parse_use_line(stripped)
            if can_group_use(stripped, base_path, symbols):
                if base_path not in grouped_symbols:
                    grouped_order.append(base_path)
                    marker = f"{marker_prefix}{marker_index}"
                    marker_index += 1
                    kept.append(marker)
                grouped_symbols[base_path].update(sym for sym in symbols if sym and sym.isidentifier())
                continue

            if base_path:
                key = RustArchiveBuilder._collapse_whitespace(stripped)
                if key in seen_use_keys:
                    continue
                seen_use_keys.add(key)
            kept.append(line)

        grouped_lines: Dict[str, str] = {}
        for base_path in grouped_order:
            symbols = sorted(grouped_symbols.get(base_path, set()))
            if not symbols:
                continue
            if len(symbols) == 1:
                grouped_lines[base_path] = f"use {base_path}::{symbols[0]};"
            else:
                grouped_lines[base_path] = f"use {base_path}::{{{', '.join(symbols)}}};"

        resolved: List[str] = []
        group_cursor = 0
        for line in kept:
            if line.startswith(marker_prefix):
                if group_cursor < len(grouped_order):
                    base_path = grouped_order[group_cursor]
                    group_cursor += 1
                    grouped = grouped_lines.get(base_path)
                    if grouped:
                        resolved.append(grouped)
                continue
            resolved.append(line)

        return "\n".join(resolved).rstrip() + "\n"

    def _build_source_template(self, archive: Dict[str, Dict[str, str]], source_name: str) -> str:
        return self._renderer().build_source_template(archive, source_name)

    def _build_module_sources(
        self,
        archive: Dict[str, Dict[str, str]],
        include_files: List[str],
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        return self._renderer().build_module_sources(archive, include_files)

    @staticmethod
    def _build_std_imports(current_body: str) -> List[str]:
        # No hardcoded std symbol -> import path mapping here.
        # Keep std imports model/compiler-driven for better generalization.
        _ = current_body
        return []

    def _extract_export_names(self, source_name: str, source_bucket: Dict[str, str]) -> Set[str]:
        names: Set[str] = set()
        for name in source_bucket:
            if name != "extra" and name.isidentifier():
                names.add(name)

        extra = source_bucket.get("extra", "")
        if extra:
            # Track public type-level symbols declared in module prelude code.
            for raw in extra.splitlines():
                stripped = raw.strip()
                if not stripped.startswith("pub"):
                    continue
                kind, symbol = RustArchiveBuilder._extract_decl_name(stripped)
                if kind in {"struct", "enum", "trait", "type", "const", "static", "union"} and symbol:
                    owner = self.data_manager.get_decl_owner(symbol)
                    if owner and owner != source_name:
                        continue
                    names.add(symbol)
        return names

    def _build_dependency_imports(
        self,
        current_body: str,
        archive: Dict[str, Dict[str, str]],
        dep_sources: List[str],
    ) -> List[str]:
        if not dep_sources or not self.enable_dependency_import_guessing:
            return []

        dep_exports = {
            dep: self._extract_export_names(dep, archive.get(dep, {}))
            for dep in dep_sources
        }

        name_owner_count: Dict[str, int] = defaultdict(int)
        for names in dep_exports.values():
            for name in names:
                name_owner_count[name] += 1

        local_declared_names: Set[str] = set()
        for raw in current_body.splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            if RustArchiveBuilder._line_starts_with_fn_decl(stripped):
                ids = RustArchiveBuilder._iter_identifiers(stripped)
                for idx, token in enumerate(ids[:-1]):
                    if token == "fn":
                        local_declared_names.add(ids[idx + 1])
                        break
            _, symbol = RustArchiveBuilder._extract_decl_name(stripped)
            if symbol:
                local_declared_names.add(symbol)

        existing_dep_imports: Dict[str, Set[str]] = defaultdict(set)
        for raw in current_body.splitlines():
            mod_name, imports = RustArchiveBuilder._parse_use_crate_line(raw.strip())
            if not mod_name:
                continue
            for imported_name in imports:
                if imported_name.isidentifier():
                    existing_dep_imports[mod_name].add(imported_name)

        dep_imports: List[str] = []
        for dep in dep_sources:
            module_name = normalize_rust_module_name(dep)
            already_imported = existing_dep_imports.get(module_name, set())
            used_names = []
            for name in sorted(dep_exports.get(dep, set())):
                if name_owner_count.get(name, 0) != 1:
                    continue
                if name in local_declared_names:
                    continue
                if name in already_imported:
                    continue
                if RustArchiveBuilder._contains_identifier(current_body, name):
                    used_names.append(name)

            if used_names:
                dep_imports.append(f"use crate::{module_name}::{{{', '.join(used_names)}}};")

        return dep_imports

    @staticmethod
    def _prune_shadowed_extra(
        extra_content: str,
        dep_exports_by_module: Dict[str, Set[str]],
        hinted_dep_modules: Optional[Set[str]] = None,
    ) -> Tuple[str, List[str]]:
        """Remove local declarations that shadow imported dependency symbols."""
        text = (extra_content or "").strip()
        if not text or not dep_exports_by_module:
            return text, []

        active_dep_modules: Set[str] = set()
        for raw in text.splitlines():
            dep_module, _ = RustArchiveBuilder._parse_use_crate_line(raw.strip())
            if dep_module and dep_module in dep_exports_by_module:
                active_dep_modules.add(dep_module)

        if hinted_dep_modules:
            for dep_module in hinted_dep_modules:
                if dep_module in dep_exports_by_module:
                    active_dep_modules.add(dep_module)

        if not active_dep_modules:
            return text, []

        shadow_symbols: Set[str] = set()
        for dep_module in active_dep_modules:
            shadow_symbols.update(dep_exports_by_module.get(dep_module, set()))
        if not shadow_symbols:
            return text, []

        lines = text.splitlines()
        kept: List[str] = []
        removed: List[str] = []
        i = 0

        def drop_trailing_type_attributes() -> None:
            while kept:
                tail = kept[-1].strip()
                if tail.startswith("#[") or tail.startswith("#!") or tail.startswith("///"):
                    kept.pop()
                    continue
                break

        def skip_brace_block(start_idx: int) -> int:
            idx = start_idx
            depth = 0
            seen_open = False
            while idx < len(lines):
                opens = lines[idx].count("{")
                closes = lines[idx].count("}")
                if opens > 0:
                    seen_open = True
                depth += opens
                depth -= closes
                idx += 1
                if seen_open and depth <= 0:
                    break
            return idx

        def skip_until_semicolon(start_idx: int) -> int:
            idx = start_idx
            while idx < len(lines):
                if ";" in lines[idx]:
                    return idx + 1
                idx += 1
            return idx

        while i < len(lines):
            stripped = (lines[i] or "").strip()
            kind, symbol = RustArchiveBuilder._extract_decl_name(stripped)
            if symbol and symbol in shadow_symbols and kind in {"type", "struct", "enum", "trait", "union"}:
                removed.append(symbol)
                if kind in {"struct", "enum", "trait", "union"}:
                    drop_trailing_type_attributes()
                    i = skip_brace_block(i)
                    continue
                i = skip_until_semicolon(i)
                continue

            kept.append(lines[i].rstrip())
            i += 1

        cleaned = "\n".join(kept).strip()
        return cleaned, sorted(set(removed))

    def _build_source_body_for_import_sync(
        self,
        source_name: str,
        per_source: Dict[str, str],
    ) -> str:
        is_test_source = self._is_test_source(source_name)
        extra_content = (per_source.get("extra", "") or "").strip()
        if is_test_source:
            extra_content = self._sanitize_non_function_content(extra_content)

        fn_body_chunks: List[str] = []
        for fn_name, fn_code in per_source.items():
            if fn_name == "extra":
                continue
            normalized_fn = (fn_code or "").strip()
            trimmed_fn = self._trim_to_function_definition(normalized_fn)
            normalized_fn = trimmed_fn.strip() if trimmed_fn else ""
            if not normalized_fn:
                continue
            if not is_test_source:
                normalized_fn = self._ensure_public_function(normalized_fn + "\n").strip()
            fn_body_chunks.append(normalized_fn)

        body_chunks: List[str] = []
        if extra_content:
            body_chunks.append(extra_content)
        body_chunks.extend(fn_body_chunks)
        return "\n\n".join(body_chunks)

    def _persist_imports_for_source(
        self,
        archive: Dict[str, Dict[str, str]],
        source_name: str,
        include_file_set: Set[str],
    ) -> None:
        per_source = archive.get(source_name)
        if not isinstance(per_source, dict):
            return

        current_body = self._build_source_body_for_import_sync(source_name, per_source)
        dep_sources = self._collect_source_dependency_sources(source_name, include_file_set)

        dep_exports_by_module = {
            normalize_rust_module_name(dep): self._extract_export_names(dep, archive.get(dep, {}))
            for dep in dep_sources
        }
        old_extra = (per_source.get("extra", "") or "").strip()
        cleaned_extra, removed_shadowed = self._prune_shadowed_extra(
            old_extra,
            dep_exports_by_module,
            hinted_dep_modules=(
                {normalize_rust_module_name(dep) for dep in dep_sources}
                if self.enable_dependency_import_guessing
                else None
            ),
        )
        cleaned_extra, restored_owned = self._preserve_owned_declaration_blocks(
            source_name,
            cleaned_extra,
            old_extra,
        )
        if cleaned_extra != old_extra:
            per_source["extra"] = (cleaned_extra + "\n") if cleaned_extra else ""
            current_body = self._build_source_body_for_import_sync(source_name, per_source)
            if removed_shadowed or restored_owned:
                self.logger.info(
                    f"[SHADOW-PRUNE-SYNC] {source_name} removed={','.join(removed_shadowed[:8])} restored={','.join(restored_owned[:8])}"
                )

        std_imports = self._build_std_imports(current_body)
        dep_imports = self._build_dependency_imports(current_body, archive, dep_sources)

        import_lines = [line.strip() for line in (std_imports + dep_imports) if line.strip()]
        if not import_lines:
            return

        old_extra = (per_source.get("extra", "") or "").strip()
        merged_extra = old_extra
        for line in import_lines:
            if merged_extra:
                merged_extra = self._merge_extra(merged_extra, line).strip()
            else:
                merged_extra = line

        if not merged_extra:
            return

        module_name = normalize_rust_module_name(source_name)
        merged_extra = self._drop_self_module_use_imports(merged_extra, module_name)
        merged_extra = self._dedupe_use_statements(merged_extra).strip()
        merged_extra, restored_owned_after_import = self._preserve_owned_declaration_blocks(
            source_name,
            merged_extra,
            old_extra,
        )
        normalized_extra = merged_extra if merged_extra.endswith("\n") else merged_extra + "\n"
        if normalized_extra != per_source.get("extra", ""):
            per_source["extra"] = normalized_extra
            if restored_owned_after_import:
                self.logger.info(
                    f"[OWNER-DECL-RESTORE-SYNC] {source_name} restored={','.join(restored_owned_after_import[:8])}"
                )

    def sync_archive_imports(
        self,
        archive: Dict[str, Dict[str, str]],
        include_files: Optional[List[str]] = None,
    ) -> None:
        """Persist crate-local imports back into archive `extra` fields.

        Verification/export reads module text from the archive, so import sync is
        deliberately written back to the archive instead of being a transient
        rendering-only step.
        """
        if not isinstance(archive, dict):
            return

        if include_files:
            sources = [name for name in include_files if name in archive]
        else:
            sources = [name for name in self.source_names if name in archive]
            if not sources:
                sources = [name for name in archive.keys() if isinstance(archive.get(name), dict)]

        include_file_set = set(sources)
        for source_name in sources:
            self._persist_imports_for_source(archive, source_name, include_file_set)

    @staticmethod
    def _collect_response_local_helpers(
        target_name: str,
        function_content_dict: Dict[str, str],
    ) -> Set[str]:
        if not target_name or target_name not in function_content_dict:
            return set()

        referenced: Set[str] = {target_name}
        pending: List[str] = [target_name]
        available_names = set(function_content_dict.keys())

        while pending:
            current = pending.pop()
            body = function_content_dict.get(current, "")
            if not body:
                continue
            for candidate in available_names - referenced:
                if RustArchiveBuilder._contains_identifier(body, candidate):
                    referenced.add(candidate)
                    pending.append(candidate)

        referenced.discard(target_name)
        return referenced

    @staticmethod
    def _collect_response_local_helpers_for_roots(
        target_names: Set[str],
        function_content_dict: Dict[str, str],
    ) -> Set[str]:
        helper_names: Set[str] = set()
        for target_name in target_names:
            helper_names.update(
                RustArchiveBuilder._collect_response_local_helpers(
                    target_name,
                    function_content_dict,
                )
            )
        return helper_names

    @staticmethod
    def _is_path_separator(ch: str) -> bool:
        return ch in {"/", "_", "-"}

    @staticmethod
    def _normalize_token_for_case(text: str) -> str:
        return "".join(ch.lower() for ch in text if ch.isalnum() or ch == "_")

    @staticmethod
    def _use_imports_symbol(line: str, base_path: str, symbol: str) -> bool:
        parsed_base, imports = RustArchiveBuilder._parse_use_line(line)
        if parsed_base != base_path:
            return False
        return symbol in imports

    @staticmethod
    def _line_declares_static_mut(line: str, name: str) -> bool:
        text = RustArchiveBuilder._strip_visibility_prefix((line or "").strip())
        if not text.startswith("static"):
            return False
        rest = text[len("static") :].lstrip()
        if not rest.startswith("mut"):
            return False
        rest = rest[len("mut") :].lstrip()
        if not rest:
            return False
        token = rest.split(None, 1)[0]
        ident = token.split(":", 1)[0].rstrip(";")
        return ident == name

    @staticmethod
    def _replace_prefixed_numeric_identifier(text: str, prefix: str, replacement_prefix: str) -> str:
        if not text:
            return text

        out: List[str] = []
        i = 0
        n = len(text)
        plen = len(prefix)

        while i < n:
            boundary_left = i == 0 or not RustArchiveBuilder._is_ident_char(text[i - 1])
            if boundary_left and text.startswith(prefix, i):
                j = i + plen
                k = j
                while k < n and text[k].isdigit():
                    k += 1
                boundary_right = k == n or not RustArchiveBuilder._is_ident_char(text[k])
                if k > j and boundary_right:
                    out.append(replacement_prefix)
                    out.append(text[j:k])
                    i = k
                    continue
            out.append(text[i])
            i += 1

        return "".join(out)

    @staticmethod
    def _rewrite_fetch_add_counter_lines(text: str) -> str:
        _ = text
        return text or ""

    @staticmethod
    def _rewrite_counter_increment_lines(text: str) -> str:
        _ = text
        return text or ""

    @staticmethod
    def _strip_use_crate_lines(text: str) -> str:
        kept: List[str] = []
        for line in (text or "").splitlines():
            stripped = line.strip()
            base_path, _ = RustArchiveBuilder._parse_use_line(stripped)
            if base_path.startswith("crate::"):
                continue
            kept.append(line)
        return "\n".join(kept)
