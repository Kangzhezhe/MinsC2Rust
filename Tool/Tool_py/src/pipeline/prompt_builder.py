"""Prompt construction helpers for the translation pipeline.

This module owns initial translation prompts, repair prompts, editable-scope
templates, and diagnostic hint extraction. Keeping prompt assembly here makes
`TranslationPipeline` easier to read: the main class can focus on scheduling,
LLM calls, verification, and checkpoint-compatible state updates.
"""

import ast
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from prompts import (
    get_error_fixing_prompt,
    get_error_fixing_prompt_english,
    get_rust_function_conversion_prompt,
    get_rust_function_conversion_prompt_english,
)
from utils import dedupe_non_function_content, extract_related_items, normalize_rust_module_name
from pipeline.rust_archive import RustArchiveBuilder


@dataclass
class PromptContext:
    """All prompt fragments needed for one function translation attempt."""

    prompt: str
    source_name: str
    child_context: str
    names_list: List[str]
    before_details: str
    pointer_functions: List[str]
    bootstrap_decls: str = ""
    dependency_rust_hints: str = ""


class PromptBuilder:
    """Build translation and repair prompts used by `TranslationPipeline`."""

    @staticmethod
    def _render_prompt_code_block(language: str, content: str) -> str:
        body = (content or "").strip()
        if not body:
            return ""
        return f"```{language}\n{body}\n```"

    def _build_initial_rust_context_by_file(
        self,
        func_name: str,
        source_name: str,
        direct_child_functions: List[str],
        results: Dict[str, Dict[str, str]],
    ) -> str:
        ordered_sources: List[str] = []
        source_extras: Dict[str, str] = {}
        source_functions: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        seen_pairs: Set[Tuple[str, str]] = set()

        def add_source(candidate: str) -> None:
            if candidate and candidate not in ordered_sources:
                ordered_sources.append(candidate)

        add_source(source_name)
        source_bucket = results.get(source_name, {}) if isinstance(results.get(source_name), dict) else {}
        source_extra = (source_bucket.get("extra", "") or "").strip()
        if source_extra:
            source_extras[source_name] = source_extra

        for child_fun in direct_child_functions:
            if child_fun == func_name:
                continue
            child_func_content = self.data_manager.get_result(
                child_fun,
                results,
                respect_scope=True,
                preferred_source=source_name,
            )
            if not (child_func_content or "").strip():
                continue
            child_source_name = self.data_manager.get_source_name_by_func_name(
                child_fun,
                preferred_source=source_name,
                respect_scope=True,
            )
            if not child_source_name:
                continue

            add_source(child_source_name)
            child_bucket = (
                results.get(child_source_name, {})
                if isinstance(results.get(child_source_name), dict)
                else {}
            )
            child_extra = (child_bucket.get("extra", "") or "").strip()
            if child_extra and child_source_name not in source_extras:
                source_extras[child_source_name] = child_extra

            pair = (child_source_name, child_fun)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            source_functions[child_source_name].append((child_fun, (child_func_content or "").strip()))

        rendered: List[str] = []
        for src in ordered_sources:
            extra = source_extras.get(src, "")
            funcs = source_functions.get(src, [])
            if not extra and not funcs:
                continue

            module_name = normalize_rust_module_name(src)
            rendered.append(f"[Rust 文件] src/{module_name}.rs (source={src})")
            if extra:
                rendered.append(
                    f"- non_function_content(extra) [file=src/{module_name}.rs source={src}]"
                )
                rendered.append(self._render_prompt_code_block("rust", extra))
            for fn_name, fn_code in funcs:
                rendered.append(
                    f"- 函数: {fn_name} [file=src/{module_name}.rs source={src}]"
                )
                rendered.append(self._render_prompt_code_block("rust", fn_code))

        return "\n".join(part for part in rendered if part).strip()

    def _build_initial_c_context_by_file(
        self,
        func_names: List[str],
        preferred_source: str = "",
        respect_scope: bool = True,
    ) -> str:
        grouped: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        ordered_sources: List[str] = []
        seen_pairs: Set[Tuple[str, str]] = set()

        for func_name in func_names:
            owner_source = self.data_manager.get_source_name_by_func_name(
                func_name,
                preferred_source=preferred_source,
                respect_scope=respect_scope,
            )
            c_content, _, idx = self.data_manager.get_content(
                func_name,
                respect_scope=respect_scope,
                preferred_source=owner_source or preferred_source,
            )
            if idx == -1:
                continue
            c_code = (c_content or "").strip()
            if not c_code:
                continue

            src = self.source_names[idx]
            if src not in ordered_sources:
                ordered_sources.append(src)

            pair = (src, func_name)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            grouped[src].append((func_name, c_code))

        rendered: List[str] = []
        for src in ordered_sources:
            funcs = grouped.get(src, [])
            if not funcs:
                continue

            rendered.append(f"[C 文件] {src}.c (source={src})")
            for fn_name, c_code in funcs:
                rendered.append(f"- 函数: {fn_name} [file={src}.c source={src}]")
                rendered.append(self._render_prompt_code_block("c", c_code))

        return "\n".join(part for part in rendered if part).strip()

    def _build_initial_prompt_context(
        self,
        func_name: str,
        source_name: str,
        results: Dict[str, Dict[str, str]],
        funcs_child: Dict[str, List[str]],
    ) -> Optional[PromptContext]:
        direct_child_functions = self.data_manager.get_direct_child_functions(func_name, funcs_child)
        excluded_dep_notes: List[str] = []
        filtered_direct_child_functions: List[str] = []
        for child in direct_child_functions:
            if not child or child == func_name:
                continue
            owner_source = self.data_manager.get_source_name_by_func_name(
                child,
                preferred_source=source_name,
                respect_scope=True,
            )
            if not owner_source:
                owner_source = self.data_manager.get_source_name_by_func_name(
                    child,
                    preferred_source=source_name,
                    respect_scope=False,
                )
            if owner_source and self._is_excluded_source_name(owner_source):
                excluded_dep_notes.append(f"- {child} (source={owner_source})")
                continue
            filtered_direct_child_functions.append(child)
        direct_child_functions = filtered_direct_child_functions
        if self.ablation_no_context:
            source_context, _, _ = self.data_manager.get_content(
                func_name,
                respect_scope=True,
                preferred_source=source_name,
            )
            source_context = source_context or ""
            child_funs_c = f"{func_name},"
            child_context = ""
            child_funs = ""
            child_funs_c_list = [func_name]
            direct_child_functions = []
        else:
            source_context, child_funs_c, _ = self.data_manager.get_child_context_c(
                func_name,
                results,
                funcs_child,
                respect_scope=True,
                direct_only=True,
                preferred_source=source_name,
            )
            child_context, child_funs = self.data_manager.get_child_context(
                func_name,
                results,
                funcs_child,
                prompt_limit=10000,
                respect_scope=True,
                direct_only=True,
                preferred_source=source_name,
            )

            child_funs_c_list = [f for f in child_funs_c.strip(",").split(",") if f]
            filtered_child_funs_c_list: List[str] = []
            for name in child_funs_c_list:
                owner_source = self.data_manager.get_source_name_by_func_name(
                    name,
                    preferred_source=source_name,
                    respect_scope=True,
                )
                if not owner_source:
                    owner_source = self.data_manager.get_source_name_by_func_name(
                        name,
                        preferred_source=source_name,
                        respect_scope=False,
                    )
                if owner_source and self._is_excluded_source_name(owner_source):
                    if name != func_name:
                        excluded_dep_notes.append(f"- {name} (source={owner_source})")
                    continue
                filtered_child_funs_c_list.append(name)
            child_funs_c_list = filtered_child_funs_c_list
            child_funs_c = ",".join(child_funs_c_list)
            if child_funs_c:
                child_funs_c += ","
            if not child_funs_c_list:
                return None

        child_context_by_file = self._build_initial_rust_context_by_file(
            func_name=func_name,
            source_name=source_name,
            direct_child_functions=direct_child_functions,
            results=results,
        )
        source_context_by_file = self._build_initial_c_context_by_file(
            child_funs_c_list,
            preferred_source=source_name,
            respect_scope=True,
        )

        if self.ablation_no_context:
            names_list = []
            before_details = ""
            target_str = ""
        else:
            names_list, before_details = self.data_manager.get_details(
                child_funs_c_list,
                respect_scope=True,
                preferred_source=source_name,
            )
            before_details1 = extract_related_items(
                source_context,
                before_details,
                names_list,
                not_found=True,
                exlude_str=child_context,
            )
            target_str = extract_related_items(
                before_details1,
                before_details,
                names_list,
                not_found=True,
                exlude_str=child_context,
            )
            target_str = self._inject_ownership_into_c_decls(target_str, source_name)

        funcs_child_set = set(direct_child_functions)
        pointer_functions = [
            f for f in self.data_manager.all_pointer_funcs if f in funcs_child_set and f != func_name
        ]

        if self.ablation_no_context:
            prompt_child_context = ""
        else:
            prompt_child_context = child_context_by_file or child_context

        if self.ablation_no_constraints:
            prompt = (
                "Convert the following C function(s) to Rust function(s). Return code only.\n"
                f"Target function(s): {child_funs_c}\n"
                "C source:\n"
                f"{source_context_by_file or source_context}\n"
            )
            if prompt_child_context:
                prompt += "Available Rust context:\n" + prompt_child_context + "\n"
        elif self.params.get("enable_english_prompt"):
            prompt = get_rust_function_conversion_prompt_english(
                child_funs_c,
                child_funs,
                prompt_child_context,
                target_str,
                source_context_by_file or source_context,
            )
        else:
            prompt = get_rust_function_conversion_prompt(
                child_funs_c,
                child_funs,
                prompt_child_context,
                target_str,
                source_context_by_file or source_context,
                pointer_functions,
            )

        if not self.ablation_no_constraints:
            prompt += (
                "\n\n输出约束（必须遵守）：\n"
                "1) 只输出目标函数和最小必要 non-function 内容，不要整模块重写。 具体参考【输出与范围】\n"
                "2) 禁止输出 FFI/C 风格实现：不得出现 `std::ffi/core::ffi/libc/c_void/void*`、`*mut/*const`、`extern \"C\"`、`unsafe`；"
                "必须优先使用安全 Rust 抽象（引用、切片、Option/Result、Rc/RefCell/Box、Vec/String）。具体参考【安全与类型（硬约束）】\n"
            )
            if excluded_dep_notes:
                prompt += (
                    "\n\n依赖裁剪提示（高优先级）：\n"
                    "以下被依赖函数来自 excluded source，已从可调度集合移除，不应继续调用。\n"
                    "请删除/改写这些调用逻辑，改用当前可用模块中的等价安全 Rust 语义实现。\n"
                    + "\n".join(excluded_dep_notes[:20])
                    + "\n"
                )

        ownership_suggestions = self._format_ownership_suggestions(
            source_name=source_name,
            func_name=func_name,
            direct_child_functions=direct_child_functions,
        )
        if ownership_suggestions:
            prompt += (
                "\n\n非函数类型安全转换建议（来自 ownership index，必须严格遵守，优先级最高）：\n"
                "- 必须按建议的所有权/可空性/字段类型生成结构体与类型别名，不得随意替换为 Rc/RefCell/Box 等。\n"
                "- 若建议与已有代码冲突，需解释冲突并选择更严格的建议实现。\n"
                + ownership_suggestions
                + "\n"
            )

        dep_sources_for_prompt: List[str] = []
        bootstrap_sources: List[str] = [source_name]
        bootstrap_decls = ""
        dependency_rust_hints = ""

        if not self.ablation_no_context:
            dep_sources_for_prompt = self._collect_dependency_prompt_sources(
                source_name=source_name,
                func_name=func_name,
                results=results,
                funcs_child=funcs_child,
            )
            for dep_source in dep_sources_for_prompt:
                if dep_source and dep_source not in bootstrap_sources:
                    bootstrap_sources.append(dep_source)

            bootstrap_decls = self._build_bootstrap_decl_hints(bootstrap_sources)

            dependency_rust_hints = self._build_dependency_rust_hints(
                source_name=source_name,
                dep_sources=dep_sources_for_prompt,
                results=results,
            )
            if (not self.ablation_no_constraints) and dependency_rust_hints:
                prompt += (
                    "\n\n跨模块复用约束（高优先级）：\n"
                    "以下只给出直接依赖模块的可复用定义节选。优先 use 复用，不要在本模块重声明同名 type/struct/enum。\n"
                    "若本轮新增了依赖符号，请把 `use crate::...` 放入 non_function_content（即 `extra` 字段）。\n"
                    f"{dependency_rust_hints}\n"
                )
        else:
            bootstrap_decls = self._build_bootstrap_decl_hints(bootstrap_sources)

        return PromptContext(
            prompt=prompt,
            source_name=source_name,
            child_context=child_context,
            names_list=names_list,
            before_details=before_details,
            pointer_functions=pointer_functions,
            bootstrap_decls=bootstrap_decls,
            dependency_rust_hints=dependency_rust_hints,
        )

    def _format_ownership_suggestions(
        self,
        source_name: str,
        func_name: str,
        direct_child_functions: List[str],
    ) -> str:
        if not self.ownership_suggestions:
            return ""

        def add_item(lines: List[str], text: str) -> None:
            cleaned = (text or "").strip()
            if not cleaned:
                return
            if len(cleaned) > 900:
                cleaned = cleaned[:900] + "..."
            lines.append(cleaned)

        lines: List[str] = []
        func_key = f"{source_name}::{func_name}"
        for item in self.ownership_suggestions.get(func_key, []):
            add_item(lines, item)

        for child in direct_child_functions:
            child_key = f"{source_name}::{child}"
            for item in self.ownership_suggestions.get(child_key, []):
                add_item(lines, item)

        module_key = f"{source_name}::*"
        for item in self.ownership_suggestions.get(module_key, []):
            add_item(lines, item)

        if not lines:
            return ""
        return "\n".join(f"- {line}" for line in lines)

    def _inject_ownership_into_c_decls(self, before_details: str, source_name: str) -> str:
        if not before_details or not self.ownership_suggestions:
            return before_details

        blocks = [block for block in str(before_details).split("\n\n") if block.strip()]
        rendered_blocks: List[str] = []

        for block in blocks:
            candidate_idents: List[str] = []
            for raw in block.splitlines():
                stripped = raw.strip()
                if not stripped:
                    continue
                ids = self._iter_identifiers(stripped)
                for ident in reversed(ids):
                    if ident not in candidate_idents:
                        candidate_idents.append(ident)
            hints = []
            for ident in candidate_idents:
                hint_key = f"{source_name}::{ident}"
                if hint_key not in self.ownership_suggestions and ident.startswith("_"):
                    alt_key = f"{source_name}::{ident.lstrip('_')}"
                    if alt_key in self.ownership_suggestions:
                        hint_key = alt_key
                if hint_key not in self.ownership_suggestions and not ident.startswith("_"):
                    alt_keys = [f"{source_name}::_{ident}", f"{source_name}::_${ident}"]
                    for alt_key in alt_keys:
                        if alt_key in self.ownership_suggestions:
                            hint_key = alt_key
                            break
                for item in self.ownership_suggestions.get(hint_key, []):
                    cleaned = (item or "").strip()
                    if cleaned:
                        if len(cleaned) > 900:
                            cleaned = cleaned[:900] + "..."
                        hints.append(f"[必须遵守] 转换建议: {cleaned}")
            if hints:
                rendered_blocks.append(
                    "\n".join([
                        "[注意] 以下 C 声明对应的所有权/字段类型建议必须严格遵守，勿用默认 Rc/RefCell 替代。",
                        *hints,
                        block,
                    ])
                )
            else:
                rendered_blocks.append(block)

        return "\n\n".join(rendered_blocks).strip()

    def _collect_dependency_prompt_sources(
        self,
        source_name: str,
        func_name: str,
        results: Dict[str, Dict[str, str]],
        funcs_child: Dict[str, List[str]],
    ) -> List[str]:
        include_file_set = set(self.data_manager.all_include_files)
        ordered: List[str] = []
        seen: Set[str] = {source_name}

        def add_source(candidate: str) -> None:
            if not candidate or candidate in seen:
                return
            if candidate not in include_file_set:
                return
            if not isinstance(results.get(candidate), dict):
                return
            seen.add(candidate)
            ordered.append(candidate)

        for dep in self.data_manager.include_dict.get(source_name, []):
            add_source(dep)

        for child_fn in self.data_manager.get_direct_child_functions(func_name, funcs_child):
            add_source(
                self.data_manager.get_source_name_by_func_name(
                    child_fn,
                    respect_scope=False,
                )
            )
        return ordered

    def _collect_source_dependency_sources(
        self,
        source_name: str,
        include_file_set: Set[str],
    ) -> List[str]:
        ordered: List[str] = []
        seen: Set[str] = {source_name}

        def add_source(candidate: str) -> None:
            if not candidate or candidate in seen:
                return
            if candidate not in include_file_set:
                return
            seen.add(candidate)
            ordered.append(candidate)

        for dep in self.data_manager.include_dict.get(source_name, []):
            add_source(dep)

        funcs_child = self.funcs_childs.get(source_name, {}) or {}
        for children in funcs_child.values():
            if not isinstance(children, list):
                continue
            for child_name in children:
                add_source(
                    self.data_manager.get_source_name_by_func_name(
                        child_name,
                        respect_scope=False,
                    )
                )

        if not ordered:
            for dep in sorted(include_file_set):
                if dep != source_name:
                    ordered.append(dep)
        return ordered

    def _build_dependency_rust_hints(
        self,
        source_name: str,
        dep_sources: List[str],
        results: Dict[str, Dict[str, str]],
        max_modules: int = 3,
        max_lines_per_module: int = 8,
        max_chars: int = 1600,
    ) -> str:
        if not dep_sources:
            return ""

        blocks: List[str] = []
        total_chars = 0
        used_modules = 0

        for dep in dep_sources:
            if dep == source_name:
                continue
            bucket = results.get(dep)
            if not isinstance(bucket, dict) or not bucket:
                continue

            lines: List[str] = []
            seen_line_keys: Set[str] = set()

            def add_line(raw_line: str) -> None:
                nonlocal lines
                line = (raw_line or "").strip()
                if not line:
                    return
                key = RustArchiveBuilder._collapse_whitespace(line)
                if key in seen_line_keys:
                    return
                seen_line_keys.add(key)
                lines.append(line)

            extra = (bucket.get("extra") or "").strip()
            if extra:
                for raw in extra.splitlines():
                    stripped = raw.strip()
                    if not stripped:
                        continue
                    if stripped.startswith("use ") or stripped.startswith("pub use "):
                        continue
                    kind, _ = RustArchiveBuilder._extract_decl_name(stripped)
                    if kind in {"type", "struct", "enum", "trait", "const", "static", "union"}:
                        add_line(stripped)
                        if len(lines) >= max_lines_per_module:
                            break
                if len(lines) < max_lines_per_module:
                    for raw in extra.splitlines():
                        stripped = raw.strip()
                        if not stripped or not RustArchiveBuilder._line_starts_with_fn_decl(stripped):
                            continue
                        signature = stripped.split("{", 1)[0].strip()
                        if signature and not signature.endswith(";"):
                            signature += ";"
                        add_line(signature)
                        if len(lines) >= max_lines_per_module:
                            break

            if len(lines) < max_lines_per_module:
                for fn_name, fn_code in bucket.items():
                    if fn_name == "extra":
                        continue
                    trimmed_fn = RustArchiveBuilder._trim_to_function_definition((fn_code or "").strip())
                    if not trimmed_fn:
                        continue
                    for raw in trimmed_fn.splitlines():
                        stripped = raw.strip()
                        if not stripped:
                            continue
                        if not RustArchiveBuilder._line_starts_with_fn_decl(stripped):
                            break
                        signature = stripped.split("{", 1)[0].strip()
                        if signature and not signature.endswith(";"):
                            signature += ";"
                        add_line(signature)
                        break
                    if len(lines) >= max_lines_per_module:
                        break

            if not lines:
                continue

            module_name = normalize_rust_module_name(dep)
            block_lines = [f"[{module_name}] ({dep})"]
            block_lines.extend(lines[:max_lines_per_module])
            block = "\n".join(block_lines)
            if total_chars + len(block) > max_chars:
                break

            blocks.append(block)
            total_chars += len(block)
            used_modules += 1
            if used_modules >= max_modules:
                break

        if not blocks:
            return ""

        return "依赖模块已有 Rust 定义（节选）:\n" + "\n\n".join(blocks)

    def _build_fix_prompt(
        self,
        template_code: str,
        compile_feedback: str,
        prompt_ctx: PromptContext,
        diagnostic_codes: Optional[Set[str]] = None,
        editable_functions: Optional[List[str]] = None,
        readonly_dependency_hints: str = "",
    ) -> str:
        diagnostic_codes = diagnostic_codes or set()
        if self.ablation_no_constraints:
            return (
                "Fix the Rust compile errors below. Return code only.\n"
                "Rust code:\n"
                f"{template_code}\n\n"
                "Compiler feedback:\n"
                f"{compile_feedback}\n"
            )

        if self.params.get("enable_english_prompt"):
            prompt = get_error_fixing_prompt_english(template_code, compile_feedback)
            prompt += (
                "\n\nHard constraints:\n"
                "1) Do not redefine global/static/type/struct symbols that already exist in the module or imported dependencies.\n"
                "2) Prefer patching only the failing function bodies.\n"
                "3) Do not introduce any new unsafe blocks/unsafe fns. For mutable global writes, prefer atomics or safe wrappers; "
                "if a correct fix would require unsafe, emit handoff directive instead of forcing local unsafe edits.\n"
                "4) Preserve compiler-reported symbol names and signatures unless diagnostics explicitly require a rename.\n"
                "5) If you determine the issue requires cross-module coordinated edits beyond current editable scope,"
                " emit this directive at the very top and hand off immediately instead of repeated local hacks:\n"
                "   // handoff_to_swe: <root cause summary>\n"
                "6) If previous feedback says malformed/incomplete target function output (truncated body or unbalanced delimiters),"
                " do one of these only: (A) return a full balanced target function; (B) emit handoff directive."
                " Never keep returning partial function bodies.\n"
            )
            if {"E0428", "E0425", "E0433"} & set(diagnostic_codes or set()):
                prompt += (
                    "7) When fixing unresolved/duplicate symbols, keep one canonical definition per type name "
                    "and remove duplicate aliases/redefinitions (for example `Type` and `Type<T>` together).\n"
                )
            if {"E0506", "E0716", "E0597", "E0507", "E0382"} & set(diagnostic_codes or set()):
                prompt += (
                    "8) For borrow-checker errors, use short borrow scopes and intermediate owned values "
                    "(clone Rc handles, end Ref/RefMut before reassignment), instead of broad rewrites.\n"
                )
            return prompt

        before_details_compile = extract_related_items(
            compile_feedback,
            prompt_ctx.before_details,
            prompt_ctx.names_list,
            exlude_str=prompt_ctx.child_context,
        )
        before_details_compile = self._clip_text(before_details_compile, 900)
        prompt = get_error_fixing_prompt(
            template_code,
            compile_feedback,
            before_details_compile,
            prompt_ctx.pointer_functions,
            prompt_ctx.names_list,
        )
        prompt += (
            "\n\n修复约束：\n"
            "1) 保持编译器报错中的符号名与签名稳定，除非诊断明确要求改名或改签名。\n"
            "2) 若判断该问题必须跨模块联动改动、当前 editable 范围内无法稳妥修复，"
            "请在返回最前面输出以下指令并立即转交 CC-MINI，不要继续局部硬修：\n"
            "// handoff_to_swe: <根因摘要>\n"
        )

        if "E0277" in diagnostic_codes or ("E0277" in (compile_feedback or "")):
            prompt += (
                "7) 若报错显示类型未实现 `Debug/Clone/Copy/PartialEq` 等 trait，"
                "优先在对应 struct/enum 上补充合适的 `#[derive(...)]`，"
                "避免通过大范围改签名绕过类型约束。\n"
            )
        if "E0428" in diagnostic_codes or ("E0428" in (compile_feedback or "")):
            prompt += (
                "8) 出现重复定义(E0428)时：同名类型/静态/别名只保留一份，"
                "禁止同时保留 `Type` 与 `Type<T>` 两套同名定义；优先删除新增的重复声明。\n"
            )
        if {"E0506", "E0716", "E0597", "E0507", "E0382"} & set(diagnostic_codes or set()):
            prompt += (
                "9) 出现借用检查错误时："
                "将 `borrow()/borrow_mut()` 缩短到最小语句块，"
                "必要时先 `clone` Rc/值到局部变量，再做赋值与返回，"
                "不要在同一长生命周期借用中重赋 `node_rc/rover` 一类变量。\n"
            )

        missing_values = self._extract_missing_named_entities(compile_feedback, "value")
        missing_functions = self._extract_missing_named_entities(compile_feedback, "function")
        missing_types = self._extract_missing_named_entities(compile_feedback, "type")

        if missing_values:
            prompt += (
                "10) 本轮缺失值符号："
                + ", ".join(missing_values[:12])
                + "。请在模块级补齐对应 `const/static` 声明或恢复已存在定义，名称必须完全一致。\n"
            )
            if self._is_test_source(prompt_ctx.source_name):
                prompt += (
                    "10.1) 测试夹具恢复策略：若仅存在大小写不同的同义符号，"
                    "请统一为报错所需名称，或增加一个同类型别名声明以兼容调用点。\n"
                )

        if missing_functions:
            prompt += (
                "11) 本轮缺失函数符号："
                + ", ".join(missing_functions[:12])
                + "。请优先恢复/保留这些函数定义；若来自依赖模块，补充正确 `use crate::...` 导入。\n"
            )

        if missing_types:
            prompt += (
                "12) 本轮缺失类型符号："
                + ", ".join(missing_types[:12])
                + "。请补齐对应 type/struct/enum 定义，并确保同名类型只有一份定义。\n"
            )

        if self._is_test_source(prompt_ctx.source_name) and self._is_unresolved_symbol_failure(diagnostic_codes, compile_feedback):
            prompt += (
                "11) 对测试模块中的 `cannot find value` 错误："
                "优先补齐缺失的测试夹具常量/静态，"
                "名称与报错保持完全一致，并放在模块级 `const/static` 声明中。\n"
            )

        if prompt_ctx.bootstrap_decls and (missing_values or missing_functions or missing_types):
            focus_symbols: List[str] = []
            for sym in (missing_values + missing_functions + missing_types):
                focus_symbols.extend(sorted(self._symbol_case_variants(sym)))
            focused_hints = self._extract_hint_lines_for_symbols(prompt_ctx.bootstrap_decls, focus_symbols)
            if focused_hints:
                prompt += (
                    "\n\n与缺失符号直接相关的声明线索（已标注来源文件）：\n"
                    f"{focused_hints}\n"
                )

        if prompt_ctx.bootstrap_decls and self._is_unresolved_symbol_failure(diagnostic_codes, compile_feedback):
            prompt += (
                "\n\n补充声明参考（用于修复未解析类型/符号，已标注来源文件）：\n"
                f"{self._clip_text(prompt_ctx.bootstrap_decls, 1200)}\n"
            )
        if prompt_ctx.dependency_rust_hints:
            dep_hints = prompt_ctx.dependency_rust_hints
            if len(dep_hints) > 1200:
                dep_hints = dep_hints[:1200]
            prompt += (
                "\n\n依赖模块可复用定义参考：\n"
                f"{dep_hints}\n"
                "本轮修复优先在 non_function_content（extra）补充或修正 `use crate::...`，"
                "不要重新定义上述同名类型/符号。\n"
            )
        if editable_functions:
            prompt += (
                "\n\n当前允许修改的函数列表（由系统维护）：\n"
                + ", ".join(editable_functions[: self.fix_editable_function_limit])
                + "\n"
                + "这一轮只允许返回上述函数的完整定义；其他函数即使出现在上下文中，也只作参考，不允许返回其实现。\n"
                + "如果你判断下一轮需要查看完整定义或新增或移除可修改函数，请只在返回代码最前面附加以下注释指令：\n"
                + "// editable_functions_add: foo, bar\n"
                + "// editable_functions_remove: baz\n"
            )
        if readonly_dependency_hints and not self.ablation_no_context:
            prompt += (
                "\n\n参考当前允许修改函数的直接依赖声明：\n"
                f"{readonly_dependency_hints}\n"
                "如果需要修改其中某个直接依赖，请用 `// editable_functions_add: 函数名` 提议，系统会在下一轮把该直接依赖加入 editable 候选。\n"
            )
        return prompt

    @staticmethod
    def _extract_editable_function_directives(response_code: str) -> Tuple[str, List[str], List[str]]:
        add_names: List[str] = []
        remove_names: List[str] = []
        kept_lines: List[str] = []

        def parse_payload(payload: str) -> List[str]:
            out: List[str] = []
            seen: Set[str] = set()
            for raw in str(payload or "").replace(";", ",").split(","):
                name = raw.strip()
                if not name or not name.isidentifier() or name in seen:
                    continue
                seen.add(name)
                out.append(name)
            return out

        for line in str(response_code or "").splitlines():
            stripped = line.strip()
            lowered = stripped.lower()
            if lowered.startswith("// editable_functions_add:"):
                add_names.extend(parse_payload(stripped.split(":", 1)[1]))
                continue
            if lowered.startswith("// editable_functions_remove:"):
                remove_names.extend(parse_payload(stripped.split(":", 1)[1]))
                continue
            kept_lines.append(line)

        cleaned = "\n".join(kept_lines).strip()
        if cleaned:
            cleaned += "\n"
        return cleaned, add_names, remove_names

    @staticmethod
    def _extract_swe_handoff_directive(response_code: str) -> Tuple[str, str]:
        handoff_reasons: List[str] = []
        kept_lines: List[str] = []

        for line in str(response_code or "").splitlines():
            stripped = line.strip()
            lowered = stripped.lower()
            if lowered.startswith("// handoff_to_swe:") or lowered.startswith("// escalate_to_swe:"):
                payload = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
                if payload:
                    handoff_reasons.append(payload)
                continue
            kept_lines.append(line)

        cleaned = "\n".join(kept_lines).strip()
        if cleaned:
            cleaned += "\n"

        return cleaned, "；".join(handoff_reasons).strip()

    @staticmethod
    def _extract_function_signature(fn_code: str) -> str:
        trimmed = RustArchiveBuilder._trim_to_function_definition((fn_code or "").strip())
        if not trimmed:
            return ""
        for raw in trimmed.splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            if RustArchiveBuilder._line_starts_with_fn_decl(stripped):
                signature = stripped.split("{", 1)[0].strip()
                if signature and not signature.endswith(";"):
                    signature += ";"
                return signature
        return ""

    def _build_prompt_non_function_snippet(
        self,
        extra_content: str,
        max_lines: int = 12,
        max_chars: int = 700,
        preserve_type_blocks: bool = False,
    ) -> str:
        text = dedupe_non_function_content(extra_content or "").strip()
        if not text:
            return ""

        lines: List[str] = []
        seen: Set[str] = set()
        total_chars = 0

        def add_line(value: str) -> bool:
            nonlocal total_chars
            line = (value or "").strip()
            if not line:
                return False
            key = RustArchiveBuilder._collapse_whitespace(line)
            if key in seen:
                return False
            projected = total_chars + len(line) + 1
            if projected > max_chars:
                return False
            seen.add(key)
            lines.append(line)
            total_chars = projected
            return True

        if preserve_type_blocks:
            for block in self._split_extra_blocks(text):
                stripped_block = (block or "").strip()
                if not stripped_block:
                    continue

                first_line = ""
                for raw in stripped_block.splitlines():
                    if raw.strip():
                        first_line = raw.strip()
                        break
                if not first_line:
                    continue

                candidate = ""
                if first_line.startswith("use ") or first_line.startswith("pub use "):
                    candidate = first_line
                else:
                    kind, _ = self._extract_decl_symbol_from_block(stripped_block)
                    if kind in {"struct", "enum", "trait", "union"}:
                        candidate = stripped_block
                    elif kind in {"const", "static", "type"}:
                        candidate = first_line
                    elif RustArchiveBuilder._line_starts_with_fn_decl(first_line):
                        candidate = first_line.split("{", 1)[0].strip()
                        if candidate and not candidate.endswith(";"):
                            candidate += ";"

                if candidate and add_line(candidate) and len(lines) >= max_lines:
                    break

            return "\n\n".join(lines).strip()

        for block in self._split_extra_blocks(text):
            stripped_block = (block or "").strip()
            if not stripped_block:
                continue

            first_line = ""
            for raw in stripped_block.splitlines():
                if raw.strip():
                    first_line = raw.strip()
                    break
            if not first_line or first_line.startswith("#") or first_line.startswith("//"):
                continue

            candidate = ""
            if first_line.startswith("use ") or first_line.startswith("pub use "):
                candidate = first_line
            else:
                kind, _ = self._extract_decl_symbol_from_block(stripped_block)
                if kind in {"const", "static", "type"}:
                    candidate = first_line
                elif kind in {"struct", "enum", "trait", "union"}:
                    # Keep complete type blocks to avoid malformed declarations in prompt context.
                    candidate = stripped_block
                elif RustArchiveBuilder._line_starts_with_fn_decl(first_line):
                    candidate = first_line.split("{", 1)[0].strip()
                    if candidate and not candidate.endswith(";"):
                        candidate += ";"

            if candidate and add_line(candidate) and len(lines) >= max_lines:
                break

        return "\n".join(lines).strip()

    @staticmethod
    def _diagnostics_require_type_bodies(diagnostic_codes: Optional[Set[str]]) -> bool:
        codes = {str(code) for code in (diagnostic_codes or set()) if code}
        if not codes:
            return False
        # These diagnostics usually require concrete field/type bodies for effective fixes.
        critical = {
            "E0560",
            "E0559",
            "E0609",
            "E0071",
            "E0574",
            "E0412",
            # Borrow-checker fixes frequently depend on full field ownership layout.
            "E0597",
            "E0506",
            "E0716",
            "E0507",
            "E0382",
        }
        return bool(codes & critical)

    @staticmethod
    def _build_module_function_spans(module_text: str) -> List[Tuple[str, int, int]]:
        lines = str(module_text or "").splitlines()
        if not lines:
            return []

        spans: List[Tuple[str, int, int]] = []
        running_depth = 0
        current_name = ""
        current_start = 0

        for idx, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if running_depth == 0 and RustArchiveBuilder._line_starts_with_fn_decl(stripped):
                fn_name = RustArchiveBuilder._extract_function_name_from_decl_line(stripped)
                if fn_name:
                    if current_name:
                        spans.append((current_name, current_start, idx - 1))
                    current_name = fn_name
                    current_start = idx
            running_depth += raw.count("{") - raw.count("}")
            if running_depth < 0:
                running_depth = 0

        if current_name:
            spans.append((current_name, current_start, len(lines)))
        return spans

    @staticmethod
    def _find_function_for_line(spans: List[Tuple[str, int, int]], line_no: int) -> str:
        for fn_name, start, end in spans:
            if start <= line_no <= end:
                return fn_name
        return ""

    def _collect_required_editable_functions(
        self,
        verify_result,
        archive: Dict[str, Dict[str, str]],
        include_files: List[str],
        current_func_name: str,
    ) -> List[str]:
        ordered: List[str] = []
        seen: Set[str] = set()

        def add_name(name: str) -> None:
            if not name or name in seen:
                return
            seen.add(name)
            ordered.append(name)

        add_name(current_func_name)
        if not verify_result:
            return ordered

        module_sources, _ = self._build_module_sources(archive, include_files)
        span_cache: Dict[str, List[Tuple[str, int, int]]] = {}
        for diag in getattr(verify_result, "diagnostics", []) or []:
            if (getattr(diag, "level", "") or "") != "error":
                continue
            module_name = (getattr(diag, "module", "") or "").strip()
            line_no = int(getattr(diag, "line", 0) or 0)
            if not module_name or line_no <= 0 or module_name not in module_sources:
                continue
            if module_name not in span_cache:
                span_cache[module_name] = self._build_module_function_spans(module_sources[module_name])
            fn_name = self._find_function_for_line(span_cache[module_name], line_no)
            if fn_name:
                add_name(fn_name)
        return ordered

    def _collect_next_round_editable_candidates(
        self,
        test_source_name: str,
        basis_functions: List[str],
        archive: Dict[str, Dict[str, str]],
        include_files: List[str],
    ) -> List[str]:
        funcs_child = self.funcs_childs.get(test_source_name, {}) or {}
        include_set = set(include_files)
        ordered: List[str] = []
        seen: Set[str] = set()

        def add_name(name: str) -> None:
            if not name or name in seen:
                return
            owner = self.data_manager.get_source_name_by_func_name(name, respect_scope=False)
            if not owner or owner not in include_set:
                return
            if not (archive.get(owner, {}).get(name, "") or "").strip():
                return
            seen.add(name)
            ordered.append(name)

        for fn_name in basis_functions:
            for dep_fn in self.data_manager.get_direct_child_functions(fn_name, funcs_child):
                if dep_fn != fn_name:
                    add_name(dep_fn)
        return ordered

    def _reconcile_editable_functions(
        self,
        current: List[str],
        required: Optional[List[str]],
        add_names: Optional[List[str]],
        remove_names: Optional[List[str]],
        archive: Dict[str, Dict[str, str]],
        include_files: List[str],
        pinned_names: Optional[Set[str]] = None,
        next_round_candidate_names: Optional[List[str]] = None,
    ) -> List[str]:
        pinned = set(pinned_names or set())
        include_set = set(include_files)
        required = list(required or [])
        add_names = list(add_names or [])
        remove_names = set(remove_names or [])
        next_round_candidates = set(next_round_candidate_names or [])

        def is_available(name: str) -> bool:
            if not name:
                return False
            owner = self.data_manager.get_source_name_by_func_name(name, respect_scope=False)
            if not owner or owner not in include_set:
                return False
            return bool((archive.get(owner, {}).get(name, "") or "").strip())

        ordered: List[str] = []
        seen: Set[str] = set()
        for name in required + add_names + current:
            if not name or name in seen:
                continue
            if not is_available(name) and name not in pinned:
                continue
            if (
                name in add_names
                and name not in pinned
                and name not in current
                and next_round_candidates
                and name not in next_round_candidates
            ):
                continue
            seen.add(name)
            ordered.append(name)

        protected = set(required) | pinned
        ordered = [name for name in ordered if name in protected or name not in remove_names]

        if len(ordered) > self.fix_editable_function_limit:
            trimmed: List[str] = []
            trimmed_seen: Set[str] = set()
            for name in ordered:
                if name in protected and name not in trimmed_seen:
                    trimmed_seen.add(name)
                    trimmed.append(name)
            for name in ordered:
                if len(trimmed) >= self.fix_editable_function_limit:
                    break
                if name not in trimmed_seen:
                    trimmed_seen.add(name)
                    trimmed.append(name)
            ordered = trimmed

        return ordered or list(pinned) or required[:1]

    def _build_editable_fix_template(
        self,
        archive: Dict[str, Dict[str, str]],
        editable_functions: List[str],
        include_files: List[str],
        preferred_source: str,
        diagnostic_codes: Optional[Set[str]] = None,
    ) -> str:
        grouped: Dict[str, List[str]] = defaultdict(list)
        include_set = set(include_files)
        preserve_type_blocks = self._diagnostics_require_type_bodies(diagnostic_codes)
        for fn_name in editable_functions:
            owner = self.data_manager.get_source_name_by_func_name(fn_name, respect_scope=False)
            if not owner or owner not in include_set:
                continue
            if (archive.get(owner, {}).get(fn_name, "") or "").strip():
                grouped[owner].append(fn_name)

        ordered_sources = sorted(grouped.keys(), key=lambda name: (name != preferred_source, name))
        blocks: List[str] = []
        for source in ordered_sources:
            bucket = archive.get(source, {})
            items: List[str] = [f"// [editable-module] {normalize_rust_module_name(source)} ({source})"]
            extra_snippet = self._build_prompt_non_function_snippet(
                bucket.get("extra", ""),
                preserve_type_blocks=preserve_type_blocks,
            )
            if extra_snippet:
                items.append(extra_snippet)
            for fn_name in grouped[source]:
                code = (bucket.get(fn_name, "") or "").strip()
                if code:
                    items.append(code)
            block = "\n\n".join(item for item in items if item).strip()
            if block:
                blocks.append(block)
        return "\n\n".join(blocks).strip()

    def _build_readonly_dependency_signature_hints(
        self,
        test_source_name: str,
        editable_functions: List[str],
        archive: Dict[str, Dict[str, str]],
        include_files: List[str],
        preferred_source: str,
        max_chars: int = 1600,
    ) -> str:
        funcs_child = self.funcs_childs.get(test_source_name, {}) or {}
        editable_set = set(editable_functions)
        include_set = set(include_files)
        grouped: Dict[str, List[str]] = defaultdict(list)
        seen_keys: Set[Tuple[str, str]] = set()
        total_chars = 0

        for fn_name in editable_functions:
            for dep_fn in self.data_manager.get_direct_child_functions(fn_name, funcs_child):
                if dep_fn in editable_set:
                    continue
                owner = self.data_manager.get_source_name_by_func_name(dep_fn, respect_scope=False)
                if not owner or owner not in include_set:
                    continue
                dep_code = archive.get(owner, {}).get(dep_fn, "") or self.data_manager.get_result(dep_fn, archive, respect_scope=False)
                signature = self._extract_function_signature(dep_code)
                if not signature:
                    continue
                key = (owner, RustArchiveBuilder._collapse_whitespace(signature))
                if key in seen_keys:
                    continue
                projected = total_chars + len(signature) + len(owner) + 8
                if projected > max_chars:
                    break
                seen_keys.add(key)
                grouped[owner].append(signature)
                total_chars = projected

        if not grouped:
            return ""

        blocks: List[str] = []
        ordered_sources = sorted(grouped.keys(), key=lambda name: (name != preferred_source, name))
        for source in ordered_sources:
            lines = grouped[source][: self.fix_readonly_dependency_limit]
            if not lines:
                continue
            block = [f"[{normalize_rust_module_name(source)}] ({source})"]
            block.extend(lines)
            blocks.append("\n".join(block))
        return "\n\n".join(blocks)

    @staticmethod
    def _extract_diagnostic_codes(verify_result) -> Set[str]:
        if not verify_result:
            return set()
        codes = set()
        for diag in getattr(verify_result, "diagnostics", []) or []:
            code = (getattr(diag, "code", "") or "").strip()
            if code:
                codes.add(code)
        return codes

    @staticmethod
    def _extract_error_codes_from_text(text: str) -> Set[str]:
        if not text:
            return set()
        return set(re.findall(r"\bE\d{4}\b", text))

    def _collect_swe_prompt_diagnostic_codes(
        self,
        summary_feedback: str,
        detailed_feedback: str,
        verify_result,
        max_items: int = 10,
    ) -> List[str]:
        codes: Set[str] = set()
        codes.update(self._extract_diagnostic_codes(verify_result))
        codes.update(self._extract_error_codes_from_text(summary_feedback or ""))
        codes.update(self._extract_error_codes_from_text(detailed_feedback or ""))
        if not codes:
            return []
        return sorted(codes)[: max(1, int(max_items))]

    def _build_swe_strategy_notes(
        self,
        source_name: str,
        func_name: str,
        module_name: str,
        diagnostic_codes: List[str],
        compile_cmd: str,
    ) -> str:
        code_set = set(diagnostic_codes or [])
        lines: List[str] = [
            "CC-MINI 修复策略（泛化约束，避免脆弱补丁）:",
            "- 先做根因定位，再改代码；允许同轮处理同一根因链上的多处问题（如签名、调用点与借用关系联动修复）。",
            "- 优先语义正确修复（类型/借用/trait/签名），不要用临时绕过掩盖错误。",
            "- 禁止硬编码测试值、删除失败路径、或使用 panic!/todo!/unimplemented! 制造伪通过。",
            f"- 验收命令必须使用: {compile_cmd}（原样执行，禁止包装）。",
            "- 若失败，简要说明本轮未通过原因，并给出下一轮需规避的错误模式。",
            "- 修改范围以通过验收为准：可跨目标模块联动修改直接相关定义，避免被局部补丁限制。",
            "- 不要在函数体内插入大量推理式的注释"
        ]

        if diagnostic_codes:
            lines.append("- 本轮关键诊断码: " + ", ".join(diagnostic_codes))
        return "\n".join(lines).strip()

    @staticmethod
    def _is_unresolved_symbol_failure(diagnostic_codes: Set[str], feedback: str) -> bool:
        if {"E0422", "E0425", "E0433"} & set(diagnostic_codes or set()):
            return True
        text = feedback or ""
        return (
            "cannot find type" in text
            or "cannot find function" in text
            or "cannot find value" in text
            or "use of undeclared" in text
        )

    @staticmethod
    def _is_malformed_target_output_failure(feedback: str) -> bool:
        text = (feedback or "").lower()
        return (
            "语法不完整" in text
            or "函数体截断" in text
            or "括号/分隔符不匹配" in text
            or "malformed function" in text
            or "incomplete" in text and "function" in text
            or "unbalanced" in text and ("delimiter" in text or "brace" in text)
        )

    @staticmethod
    def _extract_decl_hints(source_extra_raw: str, max_chars: int = 7000) -> str:
        if not source_extra_raw:
            return ""
        text = str(source_extra_raw)
        marker = "extract_info:"
        idx = text.find(marker)
        chunks: List[str] = []

        if idx != -1:
            prefix = text[:idx].strip()
            suffix = text[idx + len(marker):].strip()

            if prefix:
                try:
                    parsed = ast.literal_eval(prefix)
                    if isinstance(parsed, dict):
                        for key, value in parsed.items():
                            if not isinstance(value, str):
                                continue
                            v = value.strip()
                            if not v:
                                continue
                            # Prefer concrete type/struct-related declarations from source metadata.
                            if key.startswith("_") or "typedef" in v or "struct" in v or "enum" in v:
                                chunks.append(v)
                except Exception:
                    chunks.append(prefix)

            if suffix:
                # Strip outer bracket wrapper like: [ ... ] to avoid noisy prompt tokens.
                if suffix.startswith("[") and suffix.endswith("]"):
                    suffix = suffix[1:-1].strip()
                chunks.append(suffix)
        else:
            chunks.append(text.strip())

        hints = "\n\n".join(chunk for chunk in chunks if chunk).strip()
        if len(hints) > max_chars:
            hints = hints[:max_chars]
        return hints

    def _build_bootstrap_decl_hints(
        self,
        source_names: List[str],
        max_chars: int = 9000,
    ) -> str:
        ordered_sources: List[str] = []
        seen_sources: Set[str] = set()
        for source_name in source_names or []:
            if not source_name or source_name in seen_sources:
                continue
            if source_name not in self.source_names:
                continue
            seen_sources.add(source_name)
            ordered_sources.append(source_name)

        blocks: List[str] = []
        total_chars = 0
        for source_name in ordered_sources:
            try:
                idx = self.source_names.index(source_name)
            except ValueError:
                continue

            source_bucket = self.data_manager.data[idx] if idx < len(self.data_manager.data) else {}
            source_extra_raw = ""
            if isinstance(source_bucket, dict):
                source_extra_raw = source_bucket.get("extra", "")

            hints = self._extract_decl_hints(source_extra_raw, max_chars=max_chars)
            if not hints:
                continue

            block = (
                f"[C 声明 file={source_name}.c source={source_name}]\n"
                f"{hints.strip()}"
            ).strip()
            projected = total_chars + len(block) + 2
            if projected > max_chars:
                remain = max_chars - total_chars
                if remain <= 0:
                    break
                block = block[:remain].rstrip()
                if not block:
                    break
                blocks.append(block)
                break

            blocks.append(block)
            total_chars = projected

        return "\n\n".join(blocks).strip()

    @staticmethod
    def _normalize_feedback_signature(feedback: str) -> str:
        if not feedback:
            return ""

        sig = RustArchiveBuilder._collapse_whitespace(str(feedback))

        normalized_tokens: List[str] = []
        for raw in sig.split(" "):
            token = raw.strip()
            if not token:
                continue

            parts = token.split(":")
            if len(parts) in {2, 3}:
                head = parts[0]
                if head and RustArchiveBuilder._is_ident_char(head[0]) and all(
                    RustArchiveBuilder._is_ident_char(ch) or ch == "-" for ch in head
                ):
                    numeric_tail = True
                    for p in parts[1:]:
                        if not p.isdigit():
                            numeric_tail = False
                            break
                    if numeric_tail:
                        normalized_tokens.append("<loc>")
                        continue

            normalized_tokens.append(token)

        return " ".join(normalized_tokens).strip()

    @staticmethod
    def _extract_missing_named_entities(feedback: str, entity_kind: str) -> List[str]:
        text = feedback or ""
        marker = f"cannot find {entity_kind} `"
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
            name = text[name_start:name_end].strip()
            if name and name not in seen and name.isidentifier():
                seen.add(name)
                out.append(name)
            i = name_end + 1

        return out

    @staticmethod
    def _extract_hint_lines_for_symbols(hints_text: str, symbols: List[str], max_lines: int = 24) -> str:
        if not hints_text or not symbols:
            return ""

        normalized_symbols = {s for s in symbols if s}
        if not normalized_symbols:
            return ""

        symbol_variants: Set[str] = set()
        for sym in normalized_symbols:
            symbol_variants.update(PromptBuilder._symbol_case_variants(sym))

        grouped: Dict[str, List[str]] = defaultdict(list)
        source_order: List[str] = []
        seen_entries: Set[Tuple[str, str]] = set()
        current_source = ""
        selected_count = 0

        for raw in hints_text.splitlines():
            line = raw.rstrip()
            if not line.strip():
                continue

            stripped = line.strip()
            if stripped.startswith("[C 声明 ") and stripped.endswith("]"):
                current_source = stripped
                continue

            matched = False
            for sym in symbol_variants:
                if RustArchiveBuilder._contains_identifier(line, sym):
                    matched = True
                    break
            if not matched:
                continue

            source_key = current_source or "[C 声明 file=unknown.c source=unknown]"
            entry_key = (source_key, line)
            if entry_key in seen_entries:
                continue

            seen_entries.add(entry_key)
            if source_key not in grouped:
                source_order.append(source_key)
            grouped[source_key].append(line)
            selected_count += 1
            if selected_count >= max_lines:
                break

        rendered: List[str] = []
        for source_key in source_order:
            rendered.append(source_key)
            for hint_line in grouped.get(source_key, []):
                rendered.append(f"- {hint_line}")

        return "\n".join(rendered)

    @staticmethod
    def _symbol_case_variants(symbol: str) -> Set[str]:
        if not symbol:
            return set()
        variants = {symbol}
        variants.add(symbol.lower())
        variants.add(symbol.upper())

        tokens = []
        token = []
        for ch in symbol:
            if ch.isalnum() or ch == "_":
                token.append(ch)
            elif token:
                tokens.append("".join(token))
                token = []
        if token:
            tokens.append("".join(token))

        if tokens:
            variants.add("_".join(tokens).lower())
            variants.add("_".join(tokens).upper())
        return {v for v in variants if v}
