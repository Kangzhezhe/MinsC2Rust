"""Verification result scoring and scope selection helpers.

These helpers format Cargo diagnostics, score candidate compile results, and
choose which archive modules should be checked. They are separate from the main
translation loop so verification policy is easier to review and test.
"""

from typing import Dict, List, Optional, Set, Tuple


class VerificationFlow:
    """Cargo verification helpers used by `TranslationPipeline`."""

    def _format_verify_diagnostics_for_debug(
        self,
        verify_result,
        focus_modules: Optional[Set[str]] = None,
        max_items: int = 12,
        max_rendered_chars: int = 500,
    ) -> str:
        if not verify_result:
            return ""

        lines: List[str] = []
        kept = 0
        for diag in getattr(verify_result, "diagnostics", []) or []:
            module = (getattr(diag, "module", "") or "").strip()
            if focus_modules and module and module not in focus_modules:
                continue

            level = (getattr(diag, "level", "") or "").strip() or "unknown"
            code = (getattr(diag, "code", "") or "").strip() or "NO_CODE"
            line_no = int(getattr(diag, "line", 0) or 0)
            col_no = int(getattr(diag, "column", 0) or 0)
            message = (getattr(diag, "message", "") or "").strip()
            rendered = (getattr(diag, "rendered", "") or "").strip()

            lines.append(
                f"[{level}] {code} {module}:{line_no}:{col_no} {message}".strip()
            )
            if rendered:
                lines.append(self._clip_text(rendered, max_rendered_chars))
            kept += 1
            if kept >= max_items:
                break

        if not lines:
            lines.append(self._clip_text(verify_result.summarize_for_llm(max_items=max_items), 1800))

        raw_output = self._clip_text(getattr(verify_result, "raw_output", "") or "", 1800).strip()
        if raw_output:
            lines.append("[cargo-check-raw]")
            lines.append(raw_output)

        return "\n".join(line for line in lines if line).strip()

    def _build_failure_record(
        self,
        template_code: str,
        summary_feedback: str,
        detailed_compile_feedback: str = "",
        swe_feedback: str = "",
    ) -> str:
        blocks: List[str] = []
        template = (template_code or "").rstrip()
        if template:
            blocks.append(template)

        summary = (summary_feedback or "").strip() or "(empty)"
        blocks.append(f"// cargo check 错误摘要:\n{summary}")

        detail = (detailed_compile_feedback or "").strip()
        if detail:
            blocks.append(f"// cargo check 详细报错:\n{detail}")

        swe = (swe_feedback or "").strip()
        if swe:
            blocks.append(f"// CC-MINI Agent 输出:\n{swe}")

        return "\n\n".join(blocks)

    @staticmethod
    def _strip_cargo_check_raw(detail_text: str) -> str:
        text = str(detail_text or "")
        marker = "[cargo-check-raw]"
        pos = text.find(marker)
        if pos == -1:
            return text.strip()
        return text[:pos].strip()

    def _compose_model_compile_feedback(self, summary_feedback: str, detailed_feedback: str) -> str:
        summary = (summary_feedback or "").strip()
        detail = self._strip_cargo_check_raw(detailed_feedback)
        if detail:
            detail = self._clip_text(detail, max(200, self.model_feedback_detail_max_chars)).strip()

        if summary and detail:
            return (
                "[compile-summary]\n"
                + summary
                + "\n\n"
                + "[compile-detail]\n"
                + detail
            )
        if detail:
            return detail
        return summary

    @staticmethod
    def _score_single_diagnostic(diag) -> int:
        code = (getattr(diag, "code", "") or "").strip().upper()
        msg = (getattr(diag, "message", "") or "").lower()
        rendered = (getattr(diag, "rendered", "") or "").lower()

        if code == "TIMEOUT":
            return 10000
        if code in {"E0422", "E0425", "E0433"}:
            return 3000
        if code in {"E0382", "E0505", "E0506", "E0507", "E0597", "E0716"}:
            return 1800
        if "expected one of" in msg or "unclosed delimiter" in msg or "unexpected closing delimiter" in msg:
            return 2800
        if "cannot find" in msg or "use of undeclared" in msg or "cannot find" in rendered:
            return 2600
        return 1200

    def _score_verify_result(self, verify_result) -> Tuple[int, str]:
        if verify_result is None:
            return 900000, "missing verify result"
        if verify_result.success:
            return 0, "success"

        errors = [d for d in (verify_result.diagnostics or []) if (getattr(d, "level", "") or "") == "error"]
        warnings = [d for d in (verify_result.diagnostics or []) if (getattr(d, "level", "") or "") == "warning"]
        score = 0
        for diag in errors:
            score += self._score_single_diagnostic(diag)
        score += 30 * len(warnings)
        score += 200 * len(errors)
        if not errors:
            score += 2000
        return score, f"errors={len(errors)} warnings={len(warnings)}"
    def _collect_verify_scope_sources(
        self,
        source_name: str,
        include_files: List[str],
    ) -> List[str]:
        if not self.owner_scoped_verify:
            return include_files

        include_set = set(include_files)
        closure: Set[str] = set()
        stack = [source_name]

        def add_verify_deps(current: str) -> None:
            for dep in self.data_manager.include_dict.get(current, []):
                if dep in include_set and dep not in closure:
                    stack.append(dep)

            funcs_child = self.funcs_childs.get(current, {}) or {}
            for children in funcs_child.values():
                if not isinstance(children, list):
                    continue
                for child_name in children:
                    dep = self.data_manager.get_source_name_by_func_name(
                        child_name,
                        respect_scope=False,
                    )
                    if dep in include_set and dep not in closure:
                        stack.append(dep)

        while stack:
            current = stack.pop()
            if current in closure:
                continue
            closure.add(current)
            add_verify_deps(current)

        if self._is_test_source(source_name):
            scoped = [name for name in include_files if name in closure]
        else:
            scoped = [
                name
                for name in include_files
                if name in closure and not self._is_test_source(name)
            ]

        if source_name in include_set and source_name not in scoped:
            scoped.insert(0, source_name)

        return scoped or include_files

    @staticmethod
    def _bucket_has_translated_content(bucket: Dict[str, str]) -> bool:
        if not isinstance(bucket, dict) or not bucket:
            return False
        if (bucket.get("extra") or "").strip():
            return True
        for key, value in bucket.items():
            if key == "extra":
                continue
            if (value or "").strip():
                return True
        return False

    def _collect_archive_verify_sources(
        self,
        archive: Dict[str, Dict[str, str]],
        source_name: str,
        include_files: List[str],
    ) -> List[str]:
        if not self.verify_full_archive:
            return self._collect_verify_scope_sources(source_name, include_files)

        ordered_sources: List[str] = []
        seen: Set[str] = set()

        def add_source(name: str) -> None:
            if not name or name in seen:
                return
            bucket = archive.get(name, {})
            if not self._bucket_has_translated_content(bucket):
                return
            seen.add(name)
            ordered_sources.append(name)

        for name in self.source_names:
            add_source(name)
        for name in archive.keys():
            add_source(name)

        if source_name not in seen:
            seen.add(source_name)
            ordered_sources.append(source_name)

        if not ordered_sources:
            return [source_name]
        return ordered_sources

    def _resolve_verify_scopes(
        self,
        archive: Dict[str, Dict[str, str]],
        source_name: str,
        include_files: List[str],
    ) -> Tuple[List[str], List[str]]:
        archive_scope = self._collect_archive_verify_sources(archive, source_name, include_files)
        if self.verify_scope_mode != "layered":
            return archive_scope, []
        if not self.verify_full_archive:
            return archive_scope, []

        owner_scope = self._collect_verify_scope_sources(source_name, include_files)
        if not owner_scope:
            return archive_scope, []
        if set(owner_scope) == set(archive_scope):
            return archive_scope, []
        return owner_scope, archive_scope

    def _verify_archive_with_strategy(
        self,
        archive: Dict[str, Dict[str, str]],
        source_name: str,
        include_files: List[str],
        crate_name: str,
        remaining_budget: int,
        log_label: str,
    ):
        if remaining_budget <= 0:
            return None, 0, "budget-exhausted", []

        primary_scope, secondary_scope = self._resolve_verify_scopes(
            archive=archive,
            source_name=source_name,
            include_files=include_files,
        )

        module_sources, _ = self._build_module_sources(archive, primary_scope)
        verify_result = self.verifier.verify_modules(
            module_sources=module_sources,
            crate_name=crate_name,
        )
        used_verify = 1
        used_scope = list(primary_scope)
        stage = "primary"

        if secondary_scope and verify_result.success:
            if used_verify >= remaining_budget:
                self.logger.info(
                    f"[VERIFY-LAYERED-SKIP] {log_label} reason=budget primary_scope={len(primary_scope)} secondary_scope={len(secondary_scope)}"
                )
                return verify_result, used_verify, "layered-primary-only", used_scope

            secondary_sources, _ = self._build_module_sources(archive, secondary_scope)
            verify_result = self.verifier.verify_modules(
                module_sources=secondary_sources,
                crate_name=f"{crate_name}_full",
            )
            used_verify += 1
            used_scope = list(secondary_scope)
            stage = "layered-full"
        elif secondary_scope:
            stage = "layered-primary-failed"

        return verify_result, used_verify, stage, used_scope
