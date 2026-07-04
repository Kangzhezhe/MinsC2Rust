"""Small automatic repair actions used after compiler feedback.

These helpers perform deterministic fixes such as aliasing case-mismatched test
fixtures. Risky synthesis remains LLM-driven; this module only owns repairs that
can be reasoned about from existing archive symbols.
"""

import copy
import os
import sys
from typing import Dict, List, Optional, Set, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from utils import normalize_rust_module_name
from pipeline.rust_archive import RustArchiveBuilder


class AutoRepairActions:
    """Deterministic post-verify repair helpers for `TranslationPipeline`."""

    @staticmethod
    def _collect_bucket_identifiers(bucket: Dict[str, str]) -> Set[str]:
        ids: Set[str] = set()
        for key, value in (bucket or {}).items():
            if key.isidentifier() and key != "extra":
                ids.add(key)
            for token in RustArchiveBuilder._iter_identifiers(value or ""):
                if token.isidentifier():
                    ids.add(token)
        return ids

    @staticmethod
    def _extract_declared_symbol_from_line(line: str) -> str:
        text = RustArchiveBuilder._strip_visibility_prefix((line or "").strip())
        if not text:
            return ""

        prefixes = ["static", "const", "type", "struct", "enum", "union", "trait"]
        for prefix in prefixes:
            marker = prefix + " "
            if text.startswith(marker):
                tail = text[len(marker) :].lstrip()
                if prefix == "static" and tail.startswith("mut "):
                    tail = tail[4:].lstrip()
                for token in RustArchiveBuilder._iter_identifiers(tail):
                    return token
                return ""

        if RustArchiveBuilder._line_starts_with_fn_decl(text):
            tokens = [tok for tok in RustArchiveBuilder._iter_identifiers(text)]
            for idx, tok in enumerate(tokens):
                if tok == "fn" and idx + 1 < len(tokens):
                    return tokens[idx + 1]
        return ""

    @staticmethod
    def _collect_declared_identifiers(bucket: Dict[str, str]) -> Set[str]:
        """Collect module-level value symbols declared in extra (const/static only)."""
        declared: Set[str] = set()
        for key, value in (bucket or {}).items():
            if key != "extra":
                # Only module prelude declarations in `extra` should seed value recovery.
                continue
            depth = 0
            for line in (value or "").splitlines():
                stripped = RustArchiveBuilder._strip_visibility_prefix(line.strip())
                # Only consider declarations at top-level scope.
                if depth == 0 and (stripped.startswith("const ") or stripped.startswith("static ")):
                    symbol = AutoRepairActions._extract_declared_symbol_from_line(line)
                    if symbol and symbol.isidentifier():
                        declared.add(symbol)
                depth += line.count("{")
                depth -= line.count("}")
                if depth < 0:
                    depth = 0
        return declared

    def _collect_effective_declared_values(
        self,
        archive: Dict[str, Dict[str, str]],
        source_name: str,
        include_files: List[str],
    ) -> Set[str]:
        module_name = normalize_rust_module_name(source_name)
        module_sources, _ = self._build_module_sources(archive, include_files)
        module_text = module_sources.get(module_name, "")
        return self._collect_declared_identifiers({"extra": module_text})

    def _auto_alias_missing_test_values(
        self,
        archive: Dict[str, Dict[str, str]],
        source_name: str,
        include_files: List[str],
        feedback: str,
    ) -> Tuple[Optional[Dict[str, Dict[str, str]]], str]:
        missing_values = self._extract_missing_named_entities(feedback, "value")
        if not missing_values:
            return None, "missing_values=none"

        source_bucket = archive.get(source_name, {})
        known_declared_ids = self._collect_effective_declared_values(archive, source_name, include_files)
        initial_declared_ids = set(known_declared_ids)
        extra = source_bucket.get("extra", "")

        alias_lines: List[str] = []
        for missing in missing_values:
            if not missing.isidentifier() or missing in known_declared_ids:
                continue

            candidates = [
                cand
                for cand in known_declared_ids
                if cand.isidentifier() and cand != missing and cand.lower() == missing.lower()
            ]
            if not candidates:
                continue

            # Prefer ALL_CAPS style for test fixtures.
            candidates.sort(key=lambda c: (not c.isupper(), len(c)))
            chosen = candidates[0]
            alias_line = f"use self::{chosen} as {missing};"
            if alias_line in extra or alias_line in alias_lines:
                continue

            alias_lines.append(alias_line)
            known_declared_ids.add(missing)

        if not alias_lines:
            blocked = [name for name in missing_values if name in initial_declared_ids]
            if blocked:
                return None, f"missing_values_already_declared: {', '.join(blocked[:6])}"
            return None, f"no_alias_candidates for {', '.join(missing_values[:6])}"

        updated = copy.deepcopy(archive)
        updated.setdefault(source_name, {})
        old_extra = updated[source_name].get("extra", "")
        updated[source_name]["extra"] = self._merge_extra(old_extra, "\n".join(alias_lines))
        return updated, ", ".join(alias_lines)

    def _auto_inject_missing_test_value_placeholders(
        self,
        archive: Dict[str, Dict[str, str]],
        source_name: str,
        include_files: List[str],
        feedback: str,
    ) -> Tuple[Optional[Dict[str, Dict[str, str]]], str]:
        missing_values = self._extract_missing_named_entities(feedback, "value")
        if not missing_values:
            return None, "missing_values=none"

        _ = (archive, source_name, include_files)
        # Keep placeholder declaration synthesis LLM-driven to avoid name-based type guesses.
        return None, f"llm_driven_placeholder_repair for {', '.join(missing_values[:6])}"

    @staticmethod
    def _is_missing_constructor_failure(feedback: str) -> bool:
        text = feedback or ""
        return "no function or associated item named `new` found for struct `" in text

    @staticmethod
    def _extract_missing_new_structs(feedback: str) -> List[str]:
        marker = "no function or associated item named `new` found for struct `"
        text = feedback or ""
        out: List[str] = []
        seen: Set[str] = set()
        i = 0
        while True:
            start = text.find(marker, i)
            if start == -1:
                break
            name_start = start + len(marker)
            name_end = text.find("`", name_start)
            if name_end == -1:
                break
            full = text[name_start:name_end].strip()
            short = full.split("::")[-1].strip()
            if short.isidentifier() and short not in seen:
                seen.add(short)
                out.append(short)
            i = name_end + 1
        return out

    def _auto_inject_missing_new_constructor(
        self,
        archive: Dict[str, Dict[str, str]],
        source_name: str,
        feedback: str,
    ) -> Tuple[Optional[Dict[str, Dict[str, str]]], str]:
        missing_structs = self._extract_missing_new_structs(feedback)
        if not missing_structs:
            return None, "missing_new_structs=none"

        _ = (archive, source_name)
        # Keep constructor synthesis LLM-driven to avoid struct-name-specific rewrites.
        return None, f"llm_driven_constructor_repair for {', '.join(missing_structs[:6])}"

    @staticmethod
    def _impl_contains_method(text: str, type_name: str, method_name: str) -> bool:
        if not text or not type_name or not method_name:
            return False

        marker = f"impl {type_name}"
        i = 0
        while True:
            start = text.find(marker, i)
            if start == -1:
                return False
            brace_start = text.find("{", start)
            if brace_start == -1:
                return False
            depth = 0
            j = brace_start
            while j < len(text):
                ch = text[j]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        block = text[brace_start : j + 1]
                        if RustArchiveBuilder._contains_identifier(block, "fn") and RustArchiveBuilder._contains_identifier(block, method_name):
                            if f"fn {method_name}(" in block:
                                return True
                        break
                j += 1
            i = start + len(marker)
