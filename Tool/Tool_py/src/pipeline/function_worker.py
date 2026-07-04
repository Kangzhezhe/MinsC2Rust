"""Single-function translation worker loop.

This module contains the high-risk retry/regeneration loop for one function.
The code is intentionally moved mostly as-is from `TranslationPipeline` so the
main algorithm stays stable while the pipeline class becomes easier to scan.
"""

import copy
import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Set

from prompts import get_trajectory
from utils import (
    Memory,
    is_rust_snippet_brace_balanced,
    normalize_rust_module_name,
    remove_markdown_code_block,
)
from pipeline.stats import (
    increment_roundtrip_verify_failure_count,
    increment_roundtrip_verify_success_count,
    increment_error_count,
    increment_regenerate_count,
    increment_retry_count,
)


@dataclass
class FunctionRunState:
    """Mutable state for one function translation attempt.

    This is the first explicit boundary around `process_func`. The long loop
    still exists, but helpers can now receive the exact state they need instead
    of reading and writing a broad pipeline `self` namespace.
    """

    test_source_name: str
    source_name: str
    func_name: str
    include_files: List[str]
    results: Dict[str, Dict[str, str]]
    all_error_funcs_content: Dict[str, Dict[str, str]]
    once_retry_count_dict: Dict[str, Dict[str, int]]
    pending_accepted: Dict[str, Dict[str, str]] = field(default_factory=dict)
    runtime_status: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)
    source_runtime_status: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    repair_records: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    retry_count: int = 0
    verify_invocations: int = 0
    func_start_time: float = 0.0
    last_template: str = ""
    last_feedback: str = ""
    last_detailed_compile_feedback: str = ""
    last_swe_feedback: str = ""
    last_verify_signature: str = ""
    committed_archive: Optional[Dict[str, Dict[str, str]]] = None
    working_archive: Optional[Dict[str, Dict[str, str]]] = None
    active_verify_include_files: List[str] = field(default_factory=list)
    last_verify_result: Any = None
    last_verify_scope: List[str] = field(default_factory=list)
    last_diagnostic_codes: Set[str] = field(default_factory=set)
    timeout_reached: bool = False
    forced_stop: bool = False
    forced_stop_reason: str = ""
    swe_regen_notes: List[str] = field(default_factory=list)
    editable_functions: List[str] = field(default_factory=list)
    response_stage: str = "initial"
    response_allowed_functions: Optional[Set[str]] = None
    stagnant_verify_count: int = 0
    best_error_count: Optional[int] = None
    no_progress_retries: int = 0
    malformed_parse_retries: int = 0
    repeat_signature_count: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def add_verify_invocations(self, amount: int) -> None:
        self.verify_invocations += int(amount or 0)

    def record_verify_feedback(
        self,
        *,
        summary_feedback: str,
        detailed_feedback: str = "",
        diagnostic_codes: Optional[Set[str]] = None,
        verify_result: Any = None,
        verify_scope: Optional[List[str]] = None,
    ) -> None:
        self.last_feedback = summary_feedback or ""
        self.last_detailed_compile_feedback = detailed_feedback or ""
        self.last_diagnostic_codes = set(diagnostic_codes or set())
        if verify_result is not None:
            self.last_verify_result = verify_result
        if verify_scope is not None:
            self.last_verify_scope = list(verify_scope)

    def request_stop(self, reason: str, feedback: str = "") -> None:
        self.forced_stop = True
        self.forced_stop_reason = str(reason or "")
        if feedback:
            self.last_feedback = feedback

    def clear_stop(self) -> None:
        self.forced_stop = False
        self.forced_stop_reason = ""

    def mark_timeout(self, feedback: str) -> None:
        self.timeout_reached = True
        self.last_feedback = feedback or ""

    def reset_retry_tracking(self) -> None:
        self.stagnant_verify_count = 0
        self.last_verify_signature = ""
        self.best_error_count = None
        self.no_progress_retries = 0
        self.malformed_parse_retries = 0

    def record_swe_note(self, note: str, max_notes: int) -> None:
        text = (note or "").strip()
        if not text:
            return
        self.swe_regen_notes.append(text)
        self.swe_regen_notes = self.swe_regen_notes[-max(1, int(max_notes or 1)) :]


@dataclass(frozen=True)
class RuntimeTestRequest:
    """Input passed to the runtime test boundary after compile verification."""

    test_source_name: str
    source_name: str
    func_name: str
    include_files: List[str]
    archive: Dict[str, Dict[str, str]]


@dataclass(frozen=True)
class RuntimeTestResult:
    """Runtime test outcome, optionally carrying CC-MINI or test repair changes."""

    ok: bool
    message: str
    archive: Optional[Dict[str, Dict[str, str]]] = None


class RuntimeTestRunner(Protocol):
    def run(self, request: RuntimeTestRequest) -> RuntimeTestResult:
        ...


class FailureRecordBuilder(Protocol):
    def build(self, **kwargs: Any) -> str:
        ...


class _LegacyRuntimeTestRunner:
    """Adapter that keeps the current TranslationPipeline behavior intact."""

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def run(self, request: RuntimeTestRequest) -> RuntimeTestResult:
        ok, message, archive = self.pipeline._run_test_module_with_optional_swe_repair(
            test_source_name=request.test_source_name,
            source_name=request.source_name,
            func_name=request.func_name,
            include_files=request.include_files,
            archive=request.archive,
        )
        return RuntimeTestResult(ok=ok, message=message, archive=archive)


class _LegacyFailureRecordBuilder:
    """Adapter for the existing failure-record formatter on TranslationPipeline."""

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def build(self, **kwargs: Any) -> str:
        return self.pipeline._build_failure_record(**kwargs)


class FunctionTranslationWorker:
    """Run the translation, verification, repair, and fallback loop for one function."""

    def __init__(
        self,
        *,
        runtime_test_runner: Optional[RuntimeTestRunner] = None,
        failure_record_builder: Optional[FailureRecordBuilder] = None,
        logger=None,
    ):
        self.runtime_test_runner = runtime_test_runner
        self.failure_record_builder = failure_record_builder
        if logger is not None:
            self.logger = logger

    def _runtime_test_runner(self) -> RuntimeTestRunner:
        runner = getattr(self, "runtime_test_runner", None)
        if runner is not None:
            return runner
        return _LegacyRuntimeTestRunner(self)

    def _failure_record_builder(self) -> FailureRecordBuilder:
        builder = getattr(self, "failure_record_builder", None)
        if builder is not None:
            return builder
        return _LegacyFailureRecordBuilder(self)

    def _log_info(self, message: str) -> None:
        logger = getattr(self, "logger", None)
        if logger is not None and hasattr(logger, "info"):
            logger.info(message)

    def _log_warning(self, message: str) -> None:
        logger = getattr(self, "logger", None)
        if logger is not None and hasattr(logger, "warning"):
            logger.warning(message)

    @staticmethod
    def _commit_successful_archive(
        archive: Dict[str, Dict[str, str]],
        include_files: List[str],
        results: Dict[str, Dict[str, str]],
        all_error_funcs_content: Dict[str, Dict[str, str]],
        once_retry_count_dict: Dict[str, Dict[str, int]],
        source_name: str,
        func_name: str,
        retry_count: int,
    ) -> None:
        for src in include_files:
            if src in archive:
                results[src] = archive[src]

        FunctionTranslationWorker._clear_function_error_record(
            all_error_funcs_content,
            source_name,
            func_name,
        )

        once_retry_count_dict.setdefault(source_name, {})[func_name] = retry_count

    @staticmethod
    def _clear_function_error_record(
        all_error_funcs_content: Dict[str, Dict[str, str]],
        source_name: str,
        func_name: str,
    ) -> bool:
        source_errors = all_error_funcs_content.get(source_name, {})
        if func_name not in source_errors:
            return False
        del source_errors[func_name]
        if not source_errors and source_name in all_error_funcs_content:
            del all_error_funcs_content[source_name]
        return True

    @staticmethod
    def _merge_runtime_archive_results(
        runtime_archive: Optional[Dict[str, Dict[str, str]]],
        include_files: List[str],
        results: Dict[str, Dict[str, str]],
        all_error_funcs_content: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> None:
        """Merge runtime-test repairs back into checkpoint state.

        CC-MINI repairs run against a real Cargo project, so a successful runtime
        archive may contain fixes for more than the function currently being
        processed. When those fixed functions are merged into `results`, stale
        checkpoint error records for the same functions must be cleared as well;
        otherwise `results.json` and `all_error_funcs_content.json` disagree.
        """
        if runtime_archive is None:
            return
        for src in include_files:
            if src in runtime_archive:
                results[src] = runtime_archive[src]
                if all_error_funcs_content is None:
                    continue
                source_errors = all_error_funcs_content.get(src, {})
                for repaired_func in runtime_archive[src]:
                    source_errors.pop(repaired_func, None)
                if not source_errors and src in all_error_funcs_content:
                    del all_error_funcs_content[src]

    @staticmethod
    def _build_runtime_test_archive(
        stable_results: Dict[str, Dict[str, str]],
        accepted_archive: Dict[str, Dict[str, str]],
        include_files: List[str],
    ) -> Dict[str, Dict[str, str]]:
        runtime_archive = copy.deepcopy(stable_results)
        for src in include_files:
            if src in accepted_archive:
                runtime_archive[src] = copy.deepcopy(accepted_archive[src])
        return runtime_archive

    @staticmethod
    def _stage_pending_accepted(
        accepted_archive: Dict[str, Dict[str, str]],
        include_files: List[str],
        pending_accepted: Dict[str, Dict[str, str]],
    ) -> None:
        for src in include_files:
            if src in accepted_archive:
                pending_accepted[src] = copy.deepcopy(accepted_archive[src])

    @staticmethod
    def _clear_pending_for_archive(
        archive: Optional[Dict[str, Dict[str, str]]],
        include_files: List[str],
        pending_accepted: Dict[str, Dict[str, str]],
    ) -> None:
        if not archive:
            return
        for src in include_files:
            if src not in archive:
                continue
            pending_source = pending_accepted.get(src)
            if not isinstance(pending_source, dict):
                continue
            for func_name in archive[src]:
                pending_source.pop(func_name, None)
            if not pending_source and src in pending_accepted:
                del pending_accepted[src]

    @staticmethod
    def _archive_hash(archive: Optional[Dict[str, Dict[str, str]]]) -> str:
        payload = json.dumps(archive or {}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _record_runtime_status(
        *,
        runtime_status: Dict[str, Dict[str, Dict[str, Any]]],
        source_runtime_status: Dict[str, Dict[str, Any]],
        source_name: str,
        func_name: str,
        test_source_name: str,
        status: str,
        message: str,
    ) -> None:
        runtime_status.setdefault(source_name, {})[func_name] = {
            "status": status,
            "test_source": test_source_name,
            "message": message,
        }
        source_records = runtime_status.get(source_name, {})
        failed = sum(
            1
            for item in source_records.values()
            if item.get("status") in {"runtime_failed", "roundtrip_compile_failed"}
        )
        passed = sum(1 for item in source_records.values() if item.get("status") == "runtime_passed")
        deferred = sum(
            1
            for item in source_records.values()
            if item.get("status") == "runtime_deferred_source_complete"
        )
        if failed:
            source_status = "has_runtime_failures"
        elif passed:
            source_status = "runtime_ok"
        elif deferred:
            source_status = "runtime_deferred_source_complete"
        else:
            source_status = "runtime_ok"
        source_runtime_status[source_name] = {
            "status": source_status,
            "failed": failed,
            "passed": passed,
            "deferred": deferred,
        }

    @staticmethod
    def _record_runtime_repair(
        *,
        repair_records: Dict[str, List[Dict[str, Any]]],
        source_name: str,
        runtime_before: Dict[str, Dict[str, str]],
        runtime_after: Dict[str, Dict[str, str]],
        include_files: List[str],
        message: str,
    ) -> None:
        modified_files = [
            src
            for src in include_files
            if runtime_after.get(src) != runtime_before.get(src)
        ]
        if not modified_files:
            return
        bucket = repair_records.setdefault(source_name, [])
        bucket.append(
            {
                "attempt": len(bucket) + 1,
                "trigger": "runtime_repair",
                "failure_kind": "cargo_test",
                "modified_files": modified_files,
                "acceptance_command": "runtime_test_runner",
                "returncode": 0,
                "backfill_status": "merged",
                "archive_hash_before": FunctionTranslationWorker._archive_hash(runtime_before),
                "archive_hash_after": FunctionTranslationWorker._archive_hash(runtime_after),
                "summary": (message or "")[:500],
            }
        )

    def _run_compile_roundtrip_verification(
        self,
        *,
        archive: Dict[str, Dict[str, str]],
        state: FunctionRunState,
    ) -> tuple[bool, str]:
        verifier = getattr(self, "_verify_archive_with_strategy", None)
        if not callable(verifier):
            return True, "round-trip compile verification skipped: verifier unavailable"

        try:
            verify_result, used_verify, stage, used_scope = verifier(
                archive=archive,
                source_name=state.source_name,
                include_files=state.include_files,
                crate_name=f"roundtrip_{normalize_rust_module_name(state.source_name)}_{normalize_rust_module_name(state.func_name)}",
                remaining_budget=2,
                log_label=f"roundtrip:{state.source_name}:{state.func_name}",
            )
        except Exception as exc:
            increment_roundtrip_verify_failure_count()
            return False, f"round-trip cargo check exception: {exc}"

        if verify_result is not None and getattr(verify_result, "success", False):
            increment_roundtrip_verify_success_count()
            self._log_info(
                f"[ROUNDTRIP-CHECK-PASS] {state.source_name}:{state.func_name} stage={stage} used={used_verify} scope={len(used_scope or [])}"
            )
            return True, "round-trip cargo check passed"

        increment_roundtrip_verify_failure_count()
        if verify_result is None:
            return False, "round-trip cargo check failed: no verifier result"
        summarize = getattr(verify_result, "summarize_for_llm", None)
        if callable(summarize):
            try:
                detail = summarize(max_items=10)
            except TypeError:
                detail = summarize()
        else:
            detail = str(verify_result)
        return False, "round-trip cargo check failed: " + str(detail)

    def _commit_verified_translation_and_check_runtime_tests(
        self,
        *,
        accepted_archive: Dict[str, Dict[str, str]],
        include_files: List[str],
        results: Dict[str, Dict[str, str]],
        all_error_funcs_content: Dict[str, Dict[str, str]],
        once_retry_count_dict: Dict[str, Dict[str, int]],
        source_name: str,
        test_source_name: str,
        func_name: str,
        retry_count: int,
        verify_invocations: int,
        func_start_time: float,
        success_log_label: str,
        runtime_failure_log_label: str,
        success_detail: str = "",
        swe_feedback: str = "",
    ) -> bool:
        """Compatibility wrapper for old call sites inside `process_func`."""
        state = FunctionRunState(
            test_source_name=test_source_name,
            source_name=source_name,
            func_name=func_name,
            include_files=include_files,
            results=results,
            all_error_funcs_content=all_error_funcs_content,
            once_retry_count_dict=once_retry_count_dict,
            pending_accepted=getattr(self, "pending_accepted", {}),
            runtime_status=getattr(self, "runtime_status", {}),
            source_runtime_status=getattr(self, "source_runtime_status", {}),
            repair_records=getattr(self, "repair_records", {}),
            retry_count=retry_count,
            verify_invocations=verify_invocations,
            func_start_time=func_start_time,
        )
        return self.commit_accepted_translation(
            state=state,
            accepted_archive=accepted_archive,
            success_log_label=success_log_label,
            runtime_failure_log_label=runtime_failure_log_label,
            success_detail=success_detail,
            swe_feedback=swe_feedback,
        )

    def commit_accepted_translation(
        self,
        *,
        state: FunctionRunState,
        accepted_archive: Dict[str, Dict[str, str]],
        success_log_label: str,
        runtime_failure_log_label: str,
        success_detail: str = "",
        swe_feedback: str = "",
    ) -> bool:
        """Commit a compile-accepted translation, then enforce runtime-test parity.

        The compile verifier and runtime tests are intentionally separate stages.
        Runtime checking and failure formatting are injected dependencies, which
        makes this behavior testable without subclassing the worker or replacing
        private methods.
        """
        self._stage_pending_accepted(
            accepted_archive,
            state.include_files,
            state.pending_accepted,
        )
        state.once_retry_count_dict.setdefault(state.source_name, {})[
            state.func_name
        ] = state.retry_count
        runtime_archive = self._build_runtime_test_archive(
            state.results,
            accepted_archive,
            state.include_files,
        )
        runtime_result = self._runtime_test_runner().run(
            RuntimeTestRequest(
                test_source_name=state.test_source_name,
                source_name=state.source_name,
                func_name=state.func_name,
                include_files=list(state.include_files),
                archive=runtime_archive,
            )
        )
        if not runtime_result.ok:
            self._record_runtime_status(
                runtime_status=state.runtime_status,
                source_runtime_status=state.source_runtime_status,
                source_name=state.source_name,
                func_name=state.func_name,
                test_source_name=state.test_source_name,
                status="runtime_failed",
                message=runtime_result.message,
            )
            increment_error_count()
            template_code = accepted_archive.get(state.source_name, {}).get(
                state.func_name,
                state.pending_accepted.get(state.source_name, {}).get(state.func_name, ""),
            )
            failure_kwargs = {
                "template_code": template_code,
                "summary_feedback": "cargo check 通过，但 cargo test 未通过",
                "detailed_compile_feedback": runtime_result.message,
            }
            if swe_feedback:
                failure_kwargs["swe_feedback"] = swe_feedback
            state.all_error_funcs_content.setdefault(state.source_name, {})[
                state.func_name
            ] = self._failure_record_builder().build(**failure_kwargs)
            self._log_warning(
                f"[{runtime_failure_log_label}] {state.test_source_name}:{state.func_name} {runtime_result.message[:260]}"
            )
            return False

        roundtrip_archive = runtime_result.archive or accepted_archive
        roundtrip_ok, roundtrip_message = self._run_compile_roundtrip_verification(
            archive=roundtrip_archive,
            state=state,
        )
        if not roundtrip_ok:
            self._record_runtime_status(
                runtime_status=state.runtime_status,
                source_runtime_status=state.source_runtime_status,
                source_name=state.source_name,
                func_name=state.func_name,
                test_source_name=state.test_source_name,
                status="roundtrip_compile_failed",
                message=roundtrip_message,
            )
            increment_error_count()
            template_code = roundtrip_archive.get(state.source_name, {}).get(
                state.func_name,
                accepted_archive.get(state.source_name, {}).get(state.func_name, ""),
            )
            failure_kwargs = {
                "template_code": template_code,
                "summary_feedback": "cargo check 通过，但回灌 round-trip cargo check 未通过",
                "detailed_compile_feedback": roundtrip_message,
            }
            if swe_feedback:
                failure_kwargs["swe_feedback"] = swe_feedback
            state.all_error_funcs_content.setdefault(state.source_name, {})[
                state.func_name
            ] = self._failure_record_builder().build(**failure_kwargs)
            self._log_warning(
                f"[ROUNDTRIP-CHECK-FAIL] {state.source_name}:{state.func_name} {roundtrip_message[:260]}"
            )
            return False

        self._commit_successful_archive(
            accepted_archive,
            state.include_files,
            state.results,
            state.all_error_funcs_content,
            state.once_retry_count_dict,
            state.source_name,
            state.func_name,
            state.retry_count,
        )
        self._merge_runtime_archive_results(
            runtime_result.archive,
            state.include_files,
            state.results,
            state.all_error_funcs_content,
        )
        if runtime_result.archive is not None:
            self._record_runtime_repair(
                repair_records=state.repair_records,
                source_name=state.source_name,
                runtime_before=runtime_archive,
                runtime_after=runtime_result.archive,
                include_files=state.include_files,
                message=runtime_result.message,
            )
        self._clear_pending_for_archive(
            runtime_result.archive or accepted_archive,
            state.include_files,
            state.pending_accepted,
        )
        runtime_status = (
            "runtime_deferred_source_complete"
            if "deferred to source completion" in str(runtime_result.message or "")
            else "runtime_passed"
        )
        self._record_runtime_status(
            runtime_status=state.runtime_status,
            source_runtime_status=state.source_runtime_status,
            source_name=state.source_name,
            func_name=state.func_name,
            test_source_name=state.test_source_name,
            status=runtime_status,
            message=runtime_result.message,
        )

        detail = f" {success_detail.strip()}" if success_detail else ""
        self._log_info(
            f"[{success_log_label}] {state.test_source_name}:{state.func_name} verify_invocations={state.verify_invocations} elapsed={time.time() - state.func_start_time:.1f}s{detail} runtime={runtime_result.message}"
        )
        return True

    def record_final_failure(self, state: FunctionRunState) -> None:
        """Persist the terminal failure for one function attempt."""
        increment_error_count()
        state.all_error_funcs_content.setdefault(state.source_name, {})[
            state.func_name
        ] = self._failure_record_builder().build(
            template_code=state.last_template,
            summary_feedback=state.last_feedback,
            detailed_compile_feedback=state.last_detailed_compile_feedback,
            swe_feedback=state.last_swe_feedback,
        )
        self._log_warning(
            f"[FAIL] {state.test_source_name}:{state.func_name} "
            f"verify_invocations={state.verify_invocations} "
            f"elapsed={time.time() - state.func_start_time:.1f}s "
            f"last_signature={state.last_verify_signature[:180]} "
            f"{state.last_feedback[:300]}"
        )

    def process_func(
        self,
        test_source_name: str,
        func_name: str,
        depth: int,
        results: Dict[str, Dict[str, str]],
        all_error_funcs_content: Dict[str, Dict[str, str]],
        once_retry_count_dict: Dict[str, Dict[str, int]],
    ) -> None:
        func_start_time = time.time()

        funcs_child = self.funcs_childs[test_source_name]
        _, _, i = self.data_manager.get_content(func_name)
        if i == -1 or i not in self.data_manager.include_files_indices:
            return

        source_name = self.source_names[i]
        if self._is_excluded_source_name(source_name):
            self.logger.info(
                f"[SKIP-EXCLUDED-SOURCE] {test_source_name}:{func_name} source={source_name}"
            )
            return
        self.logger.info(f"[START] {test_source_name}:{func_name} depth={depth} source={source_name}")

        # Guard test-owned functions from force execution when direct deps are unfinished.
        # Do not apply this gate to dependency-module functions scheduled under a test source.
        if self._is_test_source(test_source_name) and self._is_test_source(source_name):
            unmet = self._collect_unfinished_direct_callees(
                test_source_name=test_source_name,
                func_name=func_name,
                results=results,
                all_error_funcs_content=all_error_funcs_content,
            )
            if unmet:
                source_errors = all_error_funcs_content.setdefault(source_name, {})
                if func_name not in source_errors:
                    source_errors[func_name] = (
                        "// 依赖函数未完成，跳过本轮: " + ", ".join(unmet[:8])
                    )
                self.logger.info(
                    f"[SKIP-BLOCKED-DEPS] {test_source_name}:{func_name} waiting_on={','.join(unmet[:6])}"
                )
                return

        # Auto-heal poisoned checkpoints: malformed snippets should be retranslated.
        source_bucket = results.get(source_name, {})
        existing_extra = source_bucket.get("extra", "")
        if existing_extra and not is_rust_snippet_brace_balanced(existing_extra):
            self.logger.warning(f"[RESET-BAD-EXTRA] {source_name} dropping malformed extra block from checkpoint")
            del source_bucket["extra"]
        elif existing_extra and self.hard_reject_c_pointers:
            forbidden_extra_hits = self._find_forbidden_c_pointer_tokens(existing_extra)
            if forbidden_extra_hits:
                self.logger.warning(
                    f"[KEEP-FORBIDDEN-EXTRA] {source_name} preserving checkpoint extra despite forbidden tokens={','.join(forbidden_extra_hits)}"
                )

        existing_fn = source_bucket.get(func_name, "")
        is_placeholder_existing_fn = self._is_cycle_placeholder_function(existing_fn)
        has_valid_existing_fn = (
            bool(existing_fn.strip())
            and is_rust_snippet_brace_balanced(existing_fn)
            and not is_placeholder_existing_fn
        )
        if is_placeholder_existing_fn:
            self.logger.info(
                f"[PLACEHOLDER-RETRY] {source_name}:{func_name} keep placeholder for continuation"
            )
        elif existing_fn.strip() and not has_valid_existing_fn:
            self.logger.warning(
                f"[RESET-BAD-FN] {source_name}:{func_name} dropping malformed function from checkpoint"
            )
            del source_bucket[func_name]
        elif existing_fn.strip() and self.hard_reject_c_pointers:
            forbidden_fn_hits = self._find_forbidden_c_pointer_tokens(existing_fn)
            if forbidden_fn_hits:
                self.logger.warning(
                    f"[KEEP-FORBIDDEN-FN] {source_name}:{func_name} preserving checkpoint function despite forbidden tokens={','.join(forbidden_fn_hits)}"
                )
        has_recorded_failure = func_name in all_error_funcs_content.get(source_name, {})

        if func_name in self.excluded_function_names:
            self.logger.info(
                f"[SKIP] {test_source_name}:{func_name} in excluded_functions"
            )
            return

        # Highest-priority guard: keep translated checkpoint code stable across reruns.
        if has_valid_existing_fn:
            if self._clear_function_error_record(all_error_funcs_content, source_name, func_name):
                self.logger.info(
                    f"[CLEAR-STALE-ERROR] {source_name}:{func_name} valid checkpoint function"
                )
            self.logger.info(
                f"[SKIP-EXISTING] {test_source_name}:{func_name} preserve existing checkpoint function"
            )
            return

        if self.skip_failed_functions and has_recorded_failure:
            self.logger.info(
                f"[SKIP-FAILED] {test_source_name}:{func_name} skip_failed_functions=1"
            )
            return

        prompt_ctx = self._build_initial_prompt_context(func_name, source_name, results, funcs_child)
        if prompt_ctx is None:
            all_error_funcs_content.setdefault(source_name, {})[func_name] = "// 上下文构建失败"
            increment_error_count()
            return

        cycle_stub_peers = self._cycle_probe_stub_plan.pop((test_source_name, func_name), [])
        cycle_stub_note = ""
        if cycle_stub_peers:
            cycle_stub_note = self._build_cycle_stub_prompt_note(
                test_source_name=test_source_name,
                source_name=source_name,
                cycle_peers=cycle_stub_peers,
                results=results,
            )
            if cycle_stub_note:
                prompt_ctx.prompt += "\n\n" + cycle_stub_note + "\n"

        if is_placeholder_existing_fn:
            prompt_ctx.prompt += (
                "\n\n当前目标函数是循环占位实现，请在本轮必须补全真实函数体：\n"
                f"1) 移除 `{self._cycle_placeholder_marker}` 与 `unimplemented!/todo!`。\n"
                "2) 保持函数名与签名不变，仅补全正确主体。\n"
                "3) 若仍依赖环内其他函数，可保留其占位体，后续轮次会继续补全。\n"
            )

        max_retries = min(7 + depth * 2, self.params["max_retries"])
        max_regenerations = min(4 + depth, self.params["max_regenerations"])
        if self.ablation_disable_feedback_loop:
            max_retries = 1
            max_regenerations = 1
        if func_name.startswith("test_"):
            max_retries = min(max_retries, 10)

        include_files = list(self.data_manager.all_include_files)
        run_state = FunctionRunState(
            test_source_name=test_source_name,
            source_name=source_name,
            func_name=func_name,
            include_files=include_files,
            results=results,
            all_error_funcs_content=all_error_funcs_content,
            once_retry_count_dict=once_retry_count_dict,
            pending_accepted=getattr(self, "pending_accepted", {}),
            runtime_status=getattr(self, "runtime_status", {}),
            source_runtime_status=getattr(self, "source_runtime_status", {}),
            repair_records=getattr(self, "repair_records", {}),
            retry_count=0,
            verify_invocations=0,
            func_start_time=func_start_time,
        )
        verify_include_files = self._collect_archive_verify_sources(results, source_name, include_files)
        run_state.active_verify_include_files = list(verify_include_files)
        focus_modules = {normalize_rust_module_name(source_name)}
        run_state.committed_archive = copy.deepcopy(results)
        run_state.working_archive = copy.deepcopy(results)
        candidate_verify_invocations = 0

        trajectory_memory = Memory(max_size=5, memory_type="Trajectory")
        llm_start = time.time()
        init_llm_timeout = self._compute_llm_timeout(func_start_time)
        if init_llm_timeout < self.min_llm_timeout_seconds:
            run_state.last_feedback = (
                f"函数处理超时: {func_name} 剩余预算不足，放弃首次生成（remaining={self._remaining_func_seconds(func_start_time):.1f}s）"
            )
            self.record_final_failure(run_state)
            return
        self.logger.info(
            f"[LLM-REQ] {test_source_name}:{func_name} model={self.llm_model} prompt_chars={len(prompt_ctx.prompt)} timeout={init_llm_timeout}s"
        )
        response, selected_chat_id, candidate_verify_invocations = self._generate_candidates_and_pick_best(
            prompt=prompt_ctx.prompt,
            llm_model=self.llm_model,
            timeout_seconds=init_llm_timeout,
            base_temperature=0.0,
            candidate_count=self.multi_candidate_count,
            test_source_name=test_source_name,
            source_name=source_name,
            func_name=func_name,
            include_files=include_files,
            verify_include_files=run_state.active_verify_include_files,
            base_archive=run_state.working_archive,
            remaining_verify_budget=self.max_verify_invocations_per_func,
            stage="initial",
        )
        run_state.add_verify_invocations(candidate_verify_invocations)
        self.logger.info(
            f"[LLM-RESP] {test_source_name}:{func_name} chat_id={selected_chat_id} elapsed={time.time() - llm_start:.1f}s response_chars={len(response) if response else 0} candidate_verify_used={candidate_verify_invocations}"
        )
        if response == "上下文长度超过限制":
            all_error_funcs_content.setdefault(source_name, {})[func_name] = "// 上下文长度超过限制"
            increment_error_count()
            return
        if self._is_llm_transport_error(response):
            fallback_model = self._fallback_model_name()
            fallback_timeout = max(self.min_llm_timeout_seconds, min(init_llm_timeout, 60))
            self.logger.warning(
                f"[LLM-ERROR] {test_source_name}:{func_name} first response unusable, retry with model={fallback_model}"
            )
            response, fallback_chat_id, _ = self._call_llm_logged(
                prompt=prompt_ctx.prompt,
                llm_model=fallback_model,
                timeout_seconds=fallback_timeout,
                temperature=0.0,
                test_source_name=test_source_name,
                source_name=source_name,
                func_name=func_name,
                stage="initial-fallback",
            )
            self.logger.info(
                f"[LLM-RESP-FALLBACK] {test_source_name}:{func_name} chat_id={fallback_chat_id} model={fallback_model} timeout={fallback_timeout}s response_chars={len(response) if response else 0}"
            )
            if response == "上下文长度超过限制":
                all_error_funcs_content.setdefault(source_name, {})[func_name] = "// 上下文长度超过限制"
                increment_error_count()
                return
            if self._is_llm_transport_error(response):
                run_state.last_feedback = f"LLM 首次生成失败: {(response or '').strip()[:240]}"
                self.record_final_failure(run_state)
                return

        run_state.last_verify_scope = list(run_state.active_verify_include_files)
        run_state.editable_functions = [func_name]
        for peer_name in cycle_stub_peers:
            if peer_name not in run_state.editable_functions:
                run_state.editable_functions.append(peer_name)
        max_global_stagnant = int(
            self.params.get("max_global_stagnant_retries", self.max_stagnant_retries + 3)
        )

        for regenerate_idx in range(max_regenerations):
            run_state.reset_retry_tracking()
            for retry_idx in range(max_retries):
                elapsed_func = time.time() - func_start_time
                if elapsed_func > self.max_func_seconds:
                    run_state.mark_timeout(
                        f"函数处理超时: {func_name} 已运行 {elapsed_func:.1f}s, 超过 max_func_seconds={self.max_func_seconds}s"
                    )
                    self.logger.warning(f"[FUNC-TIMEOUT] {test_source_name}:{func_name} {run_state.last_feedback}")
                    break

                self.logger.info(
                    f"[RETRY] {test_source_name}:{func_name} retry={retry_idx + 1}/{max_retries} regen={regenerate_idx + 1}/{max_regenerations}"
                )
                clean_response = remove_markdown_code_block(response)
                candidate_results, merge_error = self._apply_response_to_archive(
                    clean_response,
                    func_name,
                    source_name,
                    include_files,
                    run_state.working_archive,
                    allowed_function_names=run_state.response_allowed_functions,
                    enforce_forbidden_tokens=self.hard_reject_c_pointers and run_state.response_stage in {"initial", "regen"},
                )

                if merge_error:
                    run_state.last_feedback = merge_error
                    run_state.last_diagnostic_codes = set()
                    run_state.no_progress_retries += 1
                    is_malformed_output = self._is_malformed_target_output_failure(merge_error)
                    if is_malformed_output:
                        run_state.malformed_parse_retries += 1
                    else:
                        run_state.malformed_parse_retries = 0
                    self.logger.info(f"[PARSE-FAIL] {test_source_name}:{func_name} {merge_error[:200]}")

                    if (
                        is_malformed_output
                        and self.enable_cc_mini_agent_fallback
                        and run_state.malformed_parse_retries >= self.parse_fail_handoff_retries
                        and run_state.last_verify_result is not None
                        and not run_state.last_verify_result.success
                    ):
                        run_state.request_stop(
                            "early_fallback",
                            f"连续 {run_state.malformed_parse_retries} 次生成目标函数语法不完整，提前转交 CC-MINI fallback: "
                            + self._clip_text(merge_error, 180)
                        )
                        self.logger.info(
                            f"[EARLY-FALLBACK-PARSE] {test_source_name}:{func_name} {run_state.last_feedback}"
                        )
                        break

                    if run_state.no_progress_retries >= self.no_progress_regen_retries:
                        self.logger.info(
                            f"[EARLY-REGEN-NOPROGRESS-PARSE] {test_source_name}:{func_name} no progress for {run_state.no_progress_retries} parse retries"
                        )
                        break
                else:
                    run_state.malformed_parse_retries = 0
                    # Keep latest parsable archive so next fix prompt can patch incrementally.
                    run_state.working_archive = candidate_results
                    self._refresh_cycle_placeholder_state(
                        test_source_name=test_source_name,
                        results=run_state.working_archive,
                        focus_funcs=set(cycle_stub_peers + [func_name]),
                    )
                    run_state.active_verify_include_files = self._collect_archive_verify_sources(
                        candidate_results,
                        source_name,
                        include_files,
                    )
                    if run_state.verify_invocations >= self.max_verify_invocations_per_func:
                        run_state.request_stop(
                            "verify_budget",
                            f"verify 调用次数达到上限({self.max_verify_invocations_per_func})，提前停止当前函数。"
                        )
                        self.logger.info(
                            f"[EARLY-STOP] {test_source_name}:{func_name} {run_state.last_feedback}"
                        )
                        break
                    verify_start = time.time()
                    primary_scope, secondary_scope = self._resolve_verify_scopes(
                        archive=candidate_results,
                        source_name=source_name,
                        include_files=include_files,
                    )
                    self.logger.info(
                        f"[VERIFY-REQ] {test_source_name}:{func_name} archive_scope={len(run_state.active_verify_include_files)} primary_scope={len(primary_scope)} secondary_scope={len(secondary_scope)} budget_remain={max(0, self.max_verify_invocations_per_func - run_state.verify_invocations)}"
                    )
                    verify_result, used_verify, verify_stage, used_scope = self._verify_archive_with_strategy(
                        archive=candidate_results,
                        source_name=source_name,
                        include_files=include_files,
                        crate_name=f"verify_{normalize_rust_module_name(test_source_name)}",
                        remaining_budget=max(0, self.max_verify_invocations_per_func - run_state.verify_invocations),
                        log_label=f"{test_source_name}:{func_name}",
                    )
                    if verify_result is None:
                        run_state.request_stop(
                            "verify_budget",
                            f"verify 调用次数达到上限({self.max_verify_invocations_per_func})，提前停止当前函数。"
                        )
                        self.logger.info(
                            f"[EARLY-STOP] {test_source_name}:{func_name} {run_state.last_feedback}"
                        )
                        break

                    run_state.add_verify_invocations(used_verify)
                    run_state.last_verify_result = verify_result
                    run_state.last_verify_scope = list(used_scope)
                    self.logger.info(
                        f"[VERIFY-RESP] {test_source_name}:{func_name} elapsed={time.time() - verify_start:.1f}s success={verify_result.success} diagnostics={len(verify_result.diagnostics)} stage={verify_stage} cache_hit={int(getattr(verify_result, 'cache_hit', False))} used_verify={used_verify} scope={len(used_scope)}"
                    )
                    if not verify_result.success:
                        self.logger.info(
                            f"[VERIFY-SANDBOX] {test_source_name}:{func_name} sandbox={verify_result.sandbox_dir}"
                        )

                    if verify_result.success:
                        target_after = candidate_results.get(source_name, {}).get(func_name, "")
                        if self._is_cycle_placeholder_function(target_after):
                            run_state.last_feedback = (
                                f"目标函数 {func_name} 仍为占位实现（包含 unimplemented/todo），继续补全真实函数体。"
                            )
                            run_state.last_diagnostic_codes = {"PLACEHOLDER"}
                            run_state.no_progress_retries += 1
                            self.logger.info(
                                f"[VERIFY-PLACEHOLDER] {test_source_name}:{func_name} placeholder target cannot pass"
                            )
                            continue

                        active_cycle_set = self._cycle_placeholder_active.get(test_source_name, set())
                        if func_name in active_cycle_set:
                            active_cycle_set.discard(func_name)
                            if not active_cycle_set and test_source_name in self._cycle_placeholder_active:
                                del self._cycle_placeholder_active[test_source_name]
                        self._commit_verified_translation_and_check_runtime_tests(
                            accepted_archive=candidate_results,
                            include_files=include_files,
                            results=results,
                            all_error_funcs_content=all_error_funcs_content,
                            once_retry_count_dict=once_retry_count_dict,
                            source_name=source_name,
                            test_source_name=test_source_name,
                            func_name=func_name,
                            retry_count=retry_idx,
                            verify_invocations=run_state.verify_invocations,
                            func_start_time=func_start_time,
                            success_log_label="PASS",
                            runtime_failure_log_label="PASS-BUT-TEST-FAIL",
                            success_detail=f"retries={retry_idx} regenerations={regenerate_idx}",
                        )
                        return

                    if self._is_verify_timeout(verify_result):
                        if (not self.verify_full_archive) and len(run_state.active_verify_include_files) > 1:
                            run_state.active_verify_include_files = [source_name]
                            self.logger.info(
                                f"[VERIFY-SCOPE-SHRINK] {test_source_name}:{func_name} timeout -> source-only verify"
                            )
                        run_state.last_feedback = (
                            f"cargo verify 超时(returncode={verify_result.returncode})，"
                            f"下轮继续并使用更小验证范围。"
                        )
                        run_state.last_detailed_compile_feedback = self._format_verify_diagnostics_for_debug(
                            verify_result,
                            focus_modules=focus_modules,
                            max_items=6,
                            max_rendered_chars=300,
                        )
                        if run_state.last_detailed_compile_feedback:
                            self.logger.info(
                                f"[VERIFY-TIMEOUT-DETAIL] {test_source_name}:{func_name}\n{run_state.last_detailed_compile_feedback}"
                            )
                        run_state.last_diagnostic_codes = {"TIMEOUT"}
                        continue

                    run_state.last_feedback = verify_result.summarize_for_llm(max_items=25, focus_modules=focus_modules)
                    run_state.last_diagnostic_codes = self._extract_diagnostic_codes(verify_result)
                    self.logger.info(f"[VERIFY-FAIL] {test_source_name}:{func_name} {run_state.last_feedback[:260]}")
                    current_error_count = sum(
                        1 for d in (verify_result.diagnostics or []) if (getattr(d, "level", "") or "") == "error"
                    )
                    if run_state.best_error_count is None or current_error_count < run_state.best_error_count:
                        run_state.best_error_count = current_error_count
                        run_state.no_progress_retries = 0
                    else:
                        run_state.no_progress_retries += 1
                    self.logger.info(
                        f"[PROGRESS] {test_source_name}:{func_name} errors={current_error_count} best={run_state.best_error_count} no_progress={run_state.no_progress_retries}/{self.no_progress_regen_retries}"
                    )
                    run_state.last_detailed_compile_feedback = self._format_verify_diagnostics_for_debug(
                        verify_result,
                        focus_modules=focus_modules,
                    )
                    if run_state.last_detailed_compile_feedback:
                        self.logger.info(
                            f"[VERIFY-DETAIL] {test_source_name}:{func_name}\n{run_state.last_detailed_compile_feedback}"
                        )

                    if self._is_structural_syntax_failure(run_state.last_feedback):
                        committed_extra = (run_state.committed_archive or {}).get(source_name, {}).get("extra", "")
                        run_state.working_archive.setdefault(source_name, {})["extra"] = committed_extra
                        self.logger.info(
                            f"[ROLLBACK-EXTRA] {test_source_name}:{func_name} structural syntax error -> reset module extra"
                        )

                    if self._is_test_source(source_name) and self._is_unresolved_symbol_failure(run_state.last_diagnostic_codes, run_state.last_feedback):
                        alias_archive, alias_info = self._auto_alias_missing_test_values(
                            candidate_results,
                            source_name,
                            include_files,
                            run_state.last_feedback,
                        )
                        if alias_archive is not None:
                            self.logger.info(
                                f"[AUTO-ALIAS] {test_source_name}:{func_name} {alias_info}"
                            )
                            run_state.working_archive = alias_archive
                            if run_state.verify_invocations >= self.max_verify_invocations_per_func:
                                run_state.request_stop(
                                    "verify_budget",
                                    f"verify 调用次数达到上限({self.max_verify_invocations_per_func})，提前停止自动别名修复。"
                                )
                                self.logger.info(
                                    f"[EARLY-STOP] {test_source_name}:{func_name} {run_state.last_feedback}"
                                )
                                break
                            alias_verify, alias_used_verify, alias_stage, alias_scope = self._verify_archive_with_strategy(
                                archive=alias_archive,
                                source_name=source_name,
                                include_files=include_files,
                                crate_name=f"verify_{normalize_rust_module_name(test_source_name)}_alias",
                                remaining_budget=max(0, self.max_verify_invocations_per_func - run_state.verify_invocations),
                                log_label=f"{test_source_name}:{func_name}:alias",
                            )
                            if alias_verify is None:
                                run_state.request_stop(
                                    "verify_budget",
                                    f"verify 调用次数达到上限({self.max_verify_invocations_per_func})，提前停止自动别名修复。"
                                )
                                self.logger.info(
                                    f"[EARLY-STOP] {test_source_name}:{func_name} {run_state.last_feedback}"
                                )
                                break
                            run_state.add_verify_invocations(alias_used_verify)
                            run_state.last_verify_result = alias_verify
                            run_state.last_verify_scope = list(alias_scope)
                            self.logger.info(
                                f"[VERIFY-AUTO-ALIAS] {test_source_name}:{func_name} success={alias_verify.success} diagnostics={len(alias_verify.diagnostics)} stage={alias_stage} cache_hit={int(getattr(alias_verify, 'cache_hit', False))} used_verify={alias_used_verify}"
                            )
                            if alias_verify.success:
                                self._commit_verified_translation_and_check_runtime_tests(
                                    accepted_archive=alias_archive,
                                    include_files=include_files,
                                    results=results,
                                    all_error_funcs_content=all_error_funcs_content,
                                    once_retry_count_dict=once_retry_count_dict,
                                    source_name=source_name,
                                    test_source_name=test_source_name,
                                    func_name=func_name,
                                    retry_count=retry_idx,
                                    verify_invocations=run_state.verify_invocations,
                                    func_start_time=func_start_time,
                                    success_log_label="PASS-AUTO-ALIAS",
                                    runtime_failure_log_label="PASS-AUTO-ALIAS-BUT-TEST-FAIL",
                                    success_detail=f"retries={retry_idx} regenerations={regenerate_idx}",
                                )
                                return

                            run_state.last_feedback = alias_verify.summarize_for_llm(max_items=25, focus_modules=focus_modules)
                            run_state.last_diagnostic_codes = self._extract_diagnostic_codes(alias_verify)
                            run_state.last_detailed_compile_feedback = self._format_verify_diagnostics_for_debug(
                                alias_verify,
                                focus_modules=focus_modules,
                            )
                            self.logger.info(
                                f"[VERIFY-FAIL-AUTO-ALIAS] {test_source_name}:{func_name} {run_state.last_feedback[:260]}"
                            )
                        elif alias_info:
                            self.logger.info(
                                f"[AUTO-ALIAS-SKIP] {test_source_name}:{func_name} {alias_info}"
                            )

                        if self._is_unresolved_symbol_failure(run_state.last_diagnostic_codes, run_state.last_feedback):
                            placeholder_archive, placeholder_info = self._auto_inject_missing_test_value_placeholders(
                                run_state.working_archive,
                                source_name,
                                include_files,
                                run_state.last_feedback,
                            )
                            if placeholder_archive is not None:
                                self.logger.info(
                                    f"[AUTO-PLACEHOLDER] {test_source_name}:{func_name} {placeholder_info}"
                                )
                                run_state.working_archive = placeholder_archive
                                if run_state.verify_invocations >= self.max_verify_invocations_per_func:
                                    run_state.request_stop(
                                        "verify_budget",
                                        f"verify 调用次数达到上限({self.max_verify_invocations_per_func})，提前停止占位符修复。"
                                    )
                                    self.logger.info(
                                        f"[EARLY-STOP] {test_source_name}:{func_name} {run_state.last_feedback}"
                                    )
                                    break
                                placeholder_verify, placeholder_used_verify, placeholder_stage, placeholder_scope = self._verify_archive_with_strategy(
                                    archive=placeholder_archive,
                                    source_name=source_name,
                                    include_files=include_files,
                                    crate_name=f"verify_{normalize_rust_module_name(test_source_name)}_placeholder",
                                    remaining_budget=max(0, self.max_verify_invocations_per_func - run_state.verify_invocations),
                                    log_label=f"{test_source_name}:{func_name}:placeholder",
                                )
                                if placeholder_verify is None:
                                    run_state.request_stop(
                                        "verify_budget",
                                        f"verify 调用次数达到上限({self.max_verify_invocations_per_func})，提前停止占位符修复。"
                                    )
                                    self.logger.info(
                                        f"[EARLY-STOP] {test_source_name}:{func_name} {run_state.last_feedback}"
                                    )
                                    break
                                run_state.add_verify_invocations(placeholder_used_verify)
                                run_state.last_verify_result = placeholder_verify
                                run_state.last_verify_scope = list(placeholder_scope)
                                self.logger.info(
                                    f"[VERIFY-AUTO-PLACEHOLDER] {test_source_name}:{func_name} success={placeholder_verify.success} diagnostics={len(placeholder_verify.diagnostics)} stage={placeholder_stage} cache_hit={int(getattr(placeholder_verify, 'cache_hit', False))} used_verify={placeholder_used_verify}"
                                )
                                if placeholder_verify.success:
                                    self._commit_verified_translation_and_check_runtime_tests(
                                        accepted_archive=placeholder_archive,
                                        include_files=include_files,
                                        results=results,
                                        all_error_funcs_content=all_error_funcs_content,
                                        once_retry_count_dict=once_retry_count_dict,
                                        source_name=source_name,
                                        test_source_name=test_source_name,
                                        func_name=func_name,
                                        retry_count=retry_idx,
                                        verify_invocations=run_state.verify_invocations,
                                        func_start_time=func_start_time,
                                        success_log_label="PASS-AUTO-PLACEHOLDER",
                                        runtime_failure_log_label="PASS-AUTO-PLACEHOLDER-BUT-TEST-FAIL",
                                        success_detail=f"retries={retry_idx} regenerations={regenerate_idx}",
                                    )
                                    return

                                run_state.last_feedback = placeholder_verify.summarize_for_llm(max_items=25, focus_modules=focus_modules)
                                run_state.last_diagnostic_codes = self._extract_diagnostic_codes(placeholder_verify)
                                run_state.last_detailed_compile_feedback = self._format_verify_diagnostics_for_debug(
                                    placeholder_verify,
                                    focus_modules=focus_modules,
                                )
                                self.logger.info(
                                    f"[VERIFY-FAIL-AUTO-PLACEHOLDER] {test_source_name}:{func_name} {run_state.last_feedback[:260]}"
                                )
                            elif placeholder_info:
                                self.logger.info(
                                    f"[AUTO-PLACEHOLDER-SKIP] {test_source_name}:{func_name} {placeholder_info}"
                                )

                    if self._is_test_source(source_name) and self._is_missing_constructor_failure(run_state.last_feedback):
                        ctor_archive, ctor_info = self._auto_inject_missing_new_constructor(
                            run_state.working_archive,
                            source_name,
                            run_state.last_feedback,
                        )
                        if ctor_archive is not None:
                            self.logger.info(
                                f"[AUTO-CTOR] {test_source_name}:{func_name} {ctor_info}"
                            )
                            run_state.working_archive = ctor_archive
                            if run_state.verify_invocations >= self.max_verify_invocations_per_func:
                                run_state.request_stop(
                                    "verify_budget",
                                    f"verify 调用次数达到上限({self.max_verify_invocations_per_func})，提前停止构造器修复。"
                                )
                                self.logger.info(
                                    f"[EARLY-STOP] {test_source_name}:{func_name} {run_state.last_feedback}"
                                )
                                break
                            ctor_verify, ctor_used_verify, ctor_stage, ctor_scope = self._verify_archive_with_strategy(
                                archive=ctor_archive,
                                source_name=source_name,
                                include_files=include_files,
                                crate_name=f"verify_{normalize_rust_module_name(test_source_name)}_ctor",
                                remaining_budget=max(0, self.max_verify_invocations_per_func - run_state.verify_invocations),
                                log_label=f"{test_source_name}:{func_name}:ctor",
                            )
                            if ctor_verify is None:
                                run_state.request_stop(
                                    "verify_budget",
                                    f"verify 调用次数达到上限({self.max_verify_invocations_per_func})，提前停止构造器修复。"
                                )
                                self.logger.info(
                                    f"[EARLY-STOP] {test_source_name}:{func_name} {run_state.last_feedback}"
                                )
                                break
                            run_state.add_verify_invocations(ctor_used_verify)
                            run_state.last_verify_result = ctor_verify
                            run_state.last_verify_scope = list(ctor_scope)
                            self.logger.info(
                                f"[VERIFY-AUTO-CTOR] {test_source_name}:{func_name} success={ctor_verify.success} diagnostics={len(ctor_verify.diagnostics)} stage={ctor_stage} cache_hit={int(getattr(ctor_verify, 'cache_hit', False))} used_verify={ctor_used_verify}"
                            )
                            if ctor_verify.success:
                                self._commit_verified_translation_and_check_runtime_tests(
                                    accepted_archive=ctor_archive,
                                    include_files=include_files,
                                    results=results,
                                    all_error_funcs_content=all_error_funcs_content,
                                    once_retry_count_dict=once_retry_count_dict,
                                    source_name=source_name,
                                    test_source_name=test_source_name,
                                    func_name=func_name,
                                    retry_count=retry_idx,
                                    verify_invocations=run_state.verify_invocations,
                                    func_start_time=func_start_time,
                                    success_log_label="PASS-AUTO-CTOR",
                                    runtime_failure_log_label="PASS-AUTO-CTOR-BUT-TEST-FAIL",
                                    success_detail=f"retries={retry_idx} regenerations={regenerate_idx}",
                                )
                                return

                            run_state.last_feedback = ctor_verify.summarize_for_llm(max_items=25, focus_modules=focus_modules)
                            run_state.last_diagnostic_codes = self._extract_diagnostic_codes(ctor_verify)
                            run_state.last_detailed_compile_feedback = self._format_verify_diagnostics_for_debug(
                                ctor_verify,
                                focus_modules=focus_modules,
                            )
                            self.logger.info(
                                f"[VERIFY-FAIL-AUTO-CTOR] {test_source_name}:{func_name} {run_state.last_feedback[:260]}"
                            )
                        elif ctor_info:
                            self.logger.info(
                                f"[AUTO-CTOR-SKIP] {test_source_name}:{func_name} {ctor_info}"
                            )

                    if (
                        self.enable_cc_mini_agent_fallback
                        and self.swe_fast_fallback_on_unresolved_symbol
                        and (retry_idx + 1) >= self.unresolved_symbol_handoff_retries
                        and self._is_unresolved_symbol_failure(run_state.last_diagnostic_codes, run_state.last_feedback)
                    ):
                        run_state.request_stop(
                            "early_fallback",
                            "检测到重复未解析符号错误(E0422/E0425/E0433)，提前转交 CC-MINI fallback: "
                            + run_state.last_feedback[:200]
                        )
                        self.logger.info(
                            f"[EARLY-FALLBACK] {test_source_name}:{func_name} {run_state.last_feedback}"
                        )
                        break

                    signature = self._normalize_feedback_signature(run_state.last_feedback)
                    if signature and signature == run_state.last_verify_signature:
                        run_state.stagnant_verify_count += 1
                    else:
                        run_state.last_verify_signature = signature
                        run_state.stagnant_verify_count = 1

                    if signature:
                        run_state.repeat_signature_count[signature] += 1
                        self.logger.info(
                            f"[DIAG-SIGNATURE] {test_source_name}:{func_name} signature={signature[:220]} stagnant={run_state.stagnant_verify_count} repeat={run_state.repeat_signature_count[signature]}"
                        )
                        if run_state.repeat_signature_count[signature] >= max_global_stagnant:
                            run_state.last_feedback = (
                                f"重复诊断达到 {run_state.repeat_signature_count[signature]} 次，提前进入下一轮再生成: {signature[:200]}"
                            )
                            # Give regeneration a fresh chance instead of hard-stopping the function.
                            run_state.repeat_signature_count.clear()
                            self.logger.info(
                                f"[EARLY-REGEN-DIAG] {test_source_name}:{func_name} {run_state.last_feedback}"
                            )
                            break

                    if run_state.stagnant_verify_count >= self.max_stagnant_retries:
                        self.logger.info(
                            f"[EARLY-REGEN] {test_source_name}:{func_name} repeated same diagnostics {run_state.stagnant_verify_count} times"
                        )
                        break

                    if run_state.no_progress_retries >= self.no_progress_regen_retries:
                        self.logger.info(
                            f"[EARLY-REGEN-NOPROGRESS] {test_source_name}:{func_name} no progress for {run_state.no_progress_retries} retries"
                        )
                        break

                increment_retry_count()
                if retry_idx == max_retries - 1:
                    break

                prompt_archive = candidate_results if merge_error is None else run_state.working_archive
                required_editable_functions = self._collect_required_editable_functions(
                    run_state.last_verify_result,
                    prompt_archive,
                    run_state.last_verify_scope or run_state.active_verify_include_files,
                    func_name,
                )
                next_round_editable_candidates = self._collect_next_round_editable_candidates(
                    test_source_name,
                    required_editable_functions + run_state.editable_functions,
                    prompt_archive,
                    include_files,
                )
                run_state.editable_functions = self._reconcile_editable_functions(
                    run_state.editable_functions,
                    required=required_editable_functions,
                    add_names=[],
                    remove_names=[],
                    archive=prompt_archive,
                    include_files=include_files,
                    pinned_names={func_name},
                    next_round_candidate_names=next_round_editable_candidates,
                )
                run_state.last_template = self._build_editable_fix_template(
                    prompt_archive,
                    run_state.editable_functions,
                    include_files,
                    source_name,
                    diagnostic_codes=run_state.last_diagnostic_codes,
                )
                readonly_dependency_hints = self._build_readonly_dependency_signature_hints(
                    test_source_name,
                    run_state.editable_functions,
                    prompt_archive,
                    include_files,
                    source_name,
                )
                trajectory = get_trajectory(run_state.last_template, clean_response, run_state.last_feedback, self.llm_model)
                trajectory_memory.add(trajectory)

                model_compile_feedback = self._compose_model_compile_feedback(
                    run_state.last_feedback,
                    run_state.last_detailed_compile_feedback,
                )
                detail_for_model = self._strip_cargo_check_raw(run_state.last_detailed_compile_feedback)
                self.logger.info(
                    f"[MODEL-FEEDBACK] {test_source_name}:{func_name} summary_chars={len(run_state.last_feedback)} detail_chars={len(detail_for_model)} mixed_chars={len(model_compile_feedback)}"
                )

                fix_prompt = self._build_fix_prompt(
                    template_code=run_state.last_template,
                    compile_feedback=model_compile_feedback,
                    prompt_ctx=prompt_ctx,
                    diagnostic_codes=run_state.last_diagnostic_codes,
                    editable_functions=run_state.editable_functions,
                    readonly_dependency_hints=readonly_dependency_hints,
                )
                if cycle_stub_note:
                    fix_prompt += "\n\n" + cycle_stub_note + "\n"
                trajectory_context = self._clip_text(trajectory_memory.get_context(), 900).strip()
                if trajectory_context:
                    fix_prompt += (
                        "\n以下是你最近失败尝试的轨迹，请避免重复：\n"
                        f"{trajectory_context}\n"
                    )

                fix_llm_timeout = self._compute_llm_timeout(func_start_time)
                if fix_llm_timeout < self.min_llm_timeout_seconds:
                    run_state.mark_timeout(
                        f"函数处理超时: {func_name} 剩余预算不足，放弃继续修复（remaining={self._remaining_func_seconds(func_start_time):.1f}s）"
                    )
                    self.logger.warning(f"[FUNC-TIMEOUT] {test_source_name}:{func_name} {run_state.last_feedback}")
                    break

                # Keep one verify slot for the next retry's actual commit check.
                fix_picker_verify_budget = max(
                    0,
                    self.max_verify_invocations_per_func - run_state.verify_invocations - 1,
                )
                fix_temperature = min(0.02 * (retry_idx + 1), 0.2)
                response, fix_chat_id, fix_candidate_verify_used = self._generate_candidates_and_pick_best(
                    prompt=fix_prompt,
                    llm_model=self.llm_model,
                    timeout_seconds=fix_llm_timeout,
                    base_temperature=fix_temperature,
                    candidate_count=self.fix_multi_candidate_count,
                    test_source_name=test_source_name,
                    source_name=source_name,
                    func_name=func_name,
                    include_files=include_files,
                    verify_include_files=run_state.active_verify_include_files,
                    base_archive=run_state.working_archive,
                    remaining_verify_budget=fix_picker_verify_budget,
                    stage="fix",
                    allowed_function_names=set(run_state.editable_functions),
                )
                run_state.response_stage = "fix"
                run_state.add_verify_invocations(fix_candidate_verify_used)
                self.logger.info(
                    f"[LLM-FIX-RESP] {test_source_name}:{func_name} chat_id={fix_chat_id} timeout={fix_llm_timeout}s response_chars={len(response) if response else 0} candidate_verify_used={fix_candidate_verify_used}"
                )
                run_state.response_allowed_functions = set(run_state.editable_functions)
                normalized_fix_response = remove_markdown_code_block(response)
                normalized_fix_response, handoff_reason = self._extract_swe_handoff_directive(
                    normalized_fix_response
                )
                stripped_fix_response, editable_add_names, editable_remove_names = self._extract_editable_function_directives(
                    normalized_fix_response
                )
                if stripped_fix_response:
                    response = stripped_fix_response
                else:
                    response = normalized_fix_response
                if editable_add_names or editable_remove_names:
                    next_round_editable_candidates = self._collect_next_round_editable_candidates(
                        test_source_name,
                        run_state.editable_functions,
                        run_state.working_archive,
                        include_files,
                    )
                    run_state.editable_functions = self._reconcile_editable_functions(
                        run_state.editable_functions,
                        required=[func_name],
                        add_names=editable_add_names,
                        remove_names=editable_remove_names,
                        archive=run_state.working_archive,
                        include_files=include_files,
                        pinned_names={func_name},
                        next_round_candidate_names=next_round_editable_candidates,
                    )
                    self.logger.info(
                        f"[EDITABLE-FNS] {test_source_name}:{func_name} after-llm add={editable_add_names} remove={editable_remove_names} current={run_state.editable_functions}"
                    )

                if handoff_reason:
                    reason_text = self._clip_text(handoff_reason, 260)
                    if (
                        self.enable_cc_mini_agent_fallback
                        and run_state.last_verify_result is not None
                        and not run_state.last_verify_result.success
                    ):
                        run_state.request_stop(
                            "early_fallback",
                            "repair 阶段模型主动请求转交 CC-MINI: " + reason_text,
                        )
                        self.logger.info(
                            f"[LLM-HANDOFF-CC-MINI] {test_source_name}:{func_name} {reason_text}"
                        )
                        break
                    self.logger.info(
                        f"[LLM-HANDOFF-CC-MINI-IGNORED] {test_source_name}:{func_name} {reason_text}"
                    )

                if response == "上下文长度超过限制":
                    break
                if self._is_llm_transport_error(response):
                    self.logger.warning(
                        f"[LLM-ERROR] {test_source_name}:{func_name} fix stage failed, switch to regeneration"
                    )
                    break

            if run_state.timeout_reached:
                break

            early_fallback_stop = run_state.forced_stop and run_state.forced_stop_reason == "early_fallback"

            if (
                self.enable_swe_regen_assist
                and self.enable_cc_mini_agent_fallback
                and run_state.last_verify_result is not None
                and not run_state.last_verify_result.success
                and not early_fallback_stop
            ):
                assist_archive, assist_msg, assist_note = self._attempt_cc_mini_agent_regen_assist(
                    test_source_name=test_source_name,
                    source_name=source_name,
                    func_name=func_name,
                    include_files=include_files,
                    base_archive=run_state.working_archive,
                    verify_result=run_state.last_verify_result,
                    summary_feedback=run_state.last_feedback,
                    detailed_feedback=run_state.last_detailed_compile_feedback,
                )
                if assist_msg:
                    self.logger.info(
                        f"[CC-MINI-REGEN-ASSIST] {test_source_name}:{func_name} {assist_msg}"
                    )
                if assist_archive is not None:
                    self._commit_verified_translation_and_check_runtime_tests(
                        accepted_archive=assist_archive,
                        include_files=include_files,
                        results=results,
                        all_error_funcs_content=all_error_funcs_content,
                        once_retry_count_dict=once_retry_count_dict,
                        source_name=source_name,
                        test_source_name=test_source_name,
                        func_name=func_name,
                        retry_count=max_retries,
                        verify_invocations=run_state.verify_invocations,
                        func_start_time=func_start_time,
                        success_log_label="PASS-CC-MINI-REGEN-ASSIST",
                        runtime_failure_log_label="PASS-CC-MINI-REGEN-ASSIST-BUT-TEST-FAIL",
                    )
                    return
                if assist_note:
                    run_state.record_swe_note(assist_note, self.swe_regen_assist_max_notes)
                    self.logger.info(
                        f"[CC-MINI-REGEN-NOTE] {test_source_name}:{func_name} notes={len(run_state.swe_regen_notes)}"
                    )

            # EARLY-FALLBACK: try one CC-MINI fallback before moving to next regeneration.
            # On failure, persist a concise note so next regeneration can avoid repeating it.
            if (
                early_fallback_stop
                and regenerate_idx < max_regenerations - 1
                and self.enable_cc_mini_agent_fallback
                and run_state.last_verify_result is not None
                and not run_state.last_verify_result.success
            ):
                fallback_archive, fallback_msg = self._attempt_cc_mini_agent_fallback(
                    test_source_name=test_source_name,
                    source_name=source_name,
                    func_name=func_name,
                    include_files=include_files,
                    base_archive=run_state.working_archive,
                    verify_result=run_state.last_verify_result,
                )
                if fallback_archive is not None:
                    self._commit_verified_translation_and_check_runtime_tests(
                        accepted_archive=fallback_archive,
                        include_files=include_files,
                        results=results,
                        all_error_funcs_content=all_error_funcs_content,
                        once_retry_count_dict=once_retry_count_dict,
                        source_name=source_name,
                        test_source_name=test_source_name,
                        func_name=func_name,
                        retry_count=max_retries,
                        verify_invocations=run_state.verify_invocations,
                        func_start_time=func_start_time,
                        success_log_label="CC-MINI-FALLBACK-PASS",
                        runtime_failure_log_label="CC-MINI-FALLBACK-PASS-BUT-TEST-FAIL",
                        success_detail=fallback_msg,
                        swe_feedback=fallback_msg,
                    )
                    return

                run_state.last_swe_feedback = fallback_msg
                self.logger.info(
                    f"[CC-MINI-FALLBACK-FAIL] {test_source_name}:{func_name} {fallback_msg}"
                )
                fallback_note = self._clip_text(
                    "CC-MINI fallback 失败，下一轮请避免同类策略:\n"
                    + (fallback_msg or ""),
                    self.swe_regen_assist_note_max_chars,
                ).strip()
                if fallback_note:
                    run_state.record_swe_note(fallback_note, self.swe_regen_assist_max_notes)
                    self.logger.info(
                        f"[CC-MINI-REGEN-NOTE] {test_source_name}:{func_name} notes={len(run_state.swe_regen_notes)}"
                    )

                # Consume this early-stop and continue to regeneration path below.
                run_state.clear_stop()
                self.logger.info(
                    f"[EARLY-FALLBACK-NEXT-REGEN] {test_source_name}:{func_name} fallback failed, skip current regen and continue"
                )

            if run_state.forced_stop:
                break

            increment_regenerate_count()
            if regenerate_idx == max_regenerations - 1:
                break

            # Regeneration starts a fresh attempt from committed state.
            run_state.working_archive = copy.deepcopy(run_state.committed_archive)

            regen_model = self.llm_model
            if self.params.get("enable_multi_models") and regenerate_idx == 0:
                regen_model = "zhipu"

            regen_llm_timeout = self._compute_llm_timeout(func_start_time)
            if regen_llm_timeout < self.min_llm_timeout_seconds:
                run_state.mark_timeout(
                    f"函数处理超时: {func_name} 剩余预算不足，放弃再生成（remaining={self._remaining_func_seconds(func_start_time):.1f}s）"
                )
                self.logger.warning(f"[FUNC-TIMEOUT] {test_source_name}:{func_name} {run_state.last_feedback}")
                break

            regen_temperature = min(0.1 * (regenerate_idx + 1), 0.3)
            regen_prompt = self._compose_regen_prompt_with_swe_notes(
                prompt_ctx.prompt,
                run_state.swe_regen_notes,
            )
            if cycle_stub_note:
                regen_prompt += "\n\n" + cycle_stub_note + "\n"
            run_state.active_verify_include_files = self._collect_archive_verify_sources(
                run_state.working_archive,
                source_name,
                include_files,
            )
            response, regen_chat_id, regen_verify_used = self._generate_candidates_and_pick_best(
                prompt=regen_prompt,
                llm_model=regen_model,
                timeout_seconds=regen_llm_timeout,
                base_temperature=regen_temperature,
                candidate_count=self.multi_candidate_count,
                test_source_name=test_source_name,
                    source_name=source_name,
                    func_name=func_name,
                    include_files=include_files,
                    verify_include_files=run_state.active_verify_include_files,
                    base_archive=run_state.working_archive,
                    remaining_verify_budget=max(0, self.max_verify_invocations_per_func - run_state.verify_invocations),
                    stage="regen",
                )
            run_state.response_stage = "regen"
            run_state.add_verify_invocations(regen_verify_used)
            run_state.response_allowed_functions = None
            run_state.editable_functions = [func_name]
            self.logger.info(
                f"[LLM-REGEN-RESP] {test_source_name}:{func_name} chat_id={regen_chat_id} regen_model={regen_model} timeout={regen_llm_timeout}s response_chars={len(response) if response else 0} candidate_verify_used={regen_verify_used}"
            )
            if response == "上下文长度超过限制":
                break
            if self._is_llm_transport_error(response):
                self.logger.warning(
                    f"[LLM-ERROR] {test_source_name}:{func_name} regeneration failed: {(response or '').strip()[:180]}"
                )
                continue

        if (
            self.enable_cc_mini_agent_fallback
            and run_state.last_verify_result is not None
            and not run_state.last_verify_result.success
        ):
            fallback_archive, fallback_msg = self._attempt_cc_mini_agent_fallback(
                test_source_name=test_source_name,
                source_name=source_name,
                func_name=func_name,
                include_files=include_files,
                base_archive=run_state.working_archive,
                verify_result=run_state.last_verify_result,
            )
            if fallback_archive is not None:
                self._commit_verified_translation_and_check_runtime_tests(
                    accepted_archive=fallback_archive,
                    include_files=include_files,
                    results=results,
                    all_error_funcs_content=all_error_funcs_content,
                    once_retry_count_dict=once_retry_count_dict,
                    source_name=source_name,
                    test_source_name=test_source_name,
                    func_name=func_name,
                    retry_count=max_retries,
                    verify_invocations=run_state.verify_invocations,
                    func_start_time=func_start_time,
                    success_log_label="CC-MINI-FALLBACK-PASS",
                    runtime_failure_log_label="CC-MINI-FALLBACK-PASS-BUT-TEST-FAIL",
                    success_detail=fallback_msg,
                    swe_feedback=fallback_msg,
                )
                return
            run_state.last_swe_feedback = fallback_msg
            self.logger.info(
                f"[CC-MINI-FALLBACK-FAIL] {test_source_name}:{func_name} {fallback_msg}"
            )

        run_state.retry_count = max_retries
        self.record_final_failure(run_state)
