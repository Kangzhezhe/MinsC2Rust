import sys
import unittest
from pathlib import Path


TOOL_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = TOOL_ROOT / "src"
sys.path.insert(0, str(TOOL_ROOT))
sys.path.insert(0, str(SRC_ROOT))

from pipeline.function_worker import (
    FunctionRunState,
    FunctionTranslationWorker,
    RuntimeTestResult,
)
from pipeline.stats import PipelineStats, apply_pipeline_stats, current_pipeline_stats


class _NullLogger:
    def info(self, message):
        return None

    def warning(self, message):
        return None


class _RuntimeTestRunner:
    """Boundary fake for runtime cargo-test checks."""

    def __init__(self, result):
        self.result = result
        self.requests = []

    def run(self, request):
        self.requests.append(request)
        return self.result


class _FailureRecordBuilder:
    """Boundary fake for converting runtime failures into checkpoint records."""

    def build(self, **kwargs):
        return (
            "summary={summary}; detail={detail}; swe={swe}; template={template}"
        ).format(
            summary=kwargs["summary_feedback"],
            detail=kwargs["detailed_compile_feedback"],
            swe=kwargs.get("swe_feedback", ""),
            template=kwargs["template_code"],
        )


class _VerifyResult:
    def __init__(self, success, message="roundtrip failed"):
        self.success = success
        self.message = message

    def summarize_for_llm(self, **kwargs):
        return self.message


class _ProcessDataManager:
    include_files_indices = [0]
    all_include_files = ["src_a"]

    def get_content(self, func_name):
        return "int foo(void) { return 0; }", "", 0


def _make_state(
    results=None,
    errors=None,
    retry_counts=None,
    pending=None,
    runtime_status=None,
    source_runtime_status=None,
    repair_records=None,
):
    return FunctionRunState(
        test_source_name="tests/foo_test",
        source_name="src_a",
        func_name="foo",
        include_files=["src_a", "src_b"],
        results=results if results is not None else {},
        all_error_funcs_content=errors if errors is not None else {},
        once_retry_count_dict=retry_counts if retry_counts is not None else {},
        pending_accepted=pending if pending is not None else {},
        runtime_status=runtime_status if runtime_status is not None else {},
        source_runtime_status=source_runtime_status if source_runtime_status is not None else {},
        repair_records=repair_records if repair_records is not None else {},
        retry_count=4,
        verify_invocations=2,
        func_start_time=0.0,
        last_template="pub fn foo() { todo!() }\n",
        last_feedback="cannot find value `bar`",
        last_detailed_compile_feedback="error[E0425]: cannot find value `bar`",
        last_swe_feedback="cc-mini unavailable",
    )


class FunctionTranslationWorkerTest(unittest.TestCase):
    def setUp(self):
        apply_pipeline_stats(PipelineStats())

    def tearDown(self):
        apply_pipeline_stats(PipelineStats())

    def test_commit_accepted_translation_persists_included_runtime_repairs(self):
        runtime_runner = _RuntimeTestRunner(
            RuntimeTestResult(
                ok=True,
                message="runtime ok",
                archive={
                    "src_a": {"foo": "pub fn foo() { runtime_fix(); }\n"},
                    "src_b": {"bar": "pub fn bar() {}\n"},
                    "src_c": {"baz": "pub fn baz() {}\n"},
                },
            )
        )
        failure_builder = _FailureRecordBuilder()
        worker = FunctionTranslationWorker(
            runtime_test_runner=runtime_runner,
            failure_record_builder=failure_builder,
            logger=_NullLogger(),
        )
        results = {"src_a": {"foo": "old"}}
        errors = {
            "src_a": {"foo": "previous failure"},
            "src_b": {
                "bar": "stale runtime failure repaired by the runtime archive",
                "other": "keep me",
            },
        }
        retry_counts = {}
        state = _make_state(results=results, errors=errors, retry_counts=retry_counts)

        ok = worker.commit_accepted_translation(
            state=state,
            accepted_archive={
                "src_a": {"foo": "pub fn foo() {}\n"},
                "src_b": {"bar": "pub fn bar() {}\n"},
                "src_c": {"baz": "pub fn baz() {}\n"},
            },
            success_log_label="PASS-LABEL",
            runtime_failure_log_label="FAIL-LABEL",
        )

        self.assertTrue(ok)
        self.assertEqual(results["src_a"]["foo"], "pub fn foo() { runtime_fix(); }\n")
        self.assertEqual(results["src_b"]["bar"], "pub fn bar() {}\n")
        self.assertNotIn("src_c", results)
        self.assertEqual(errors, {"src_b": {"other": "keep me"}})
        self.assertEqual(retry_counts, {"src_a": {"foo": 4}})
        self.assertEqual(current_pipeline_stats().total_error_count, 0)

    def test_process_func_clears_stale_error_when_valid_checkpoint_exists(self):
        worker = FunctionTranslationWorker(
            runtime_test_runner=_RuntimeTestRunner(RuntimeTestResult(ok=True, message="unused")),
            failure_record_builder=_FailureRecordBuilder(),
            logger=_NullLogger(),
        )
        worker.funcs_childs = {"tests/foo_test": {"foo": []}}
        worker.data_manager = _ProcessDataManager()
        worker.source_names = ["src_a"]
        worker.excluded_function_names = set()
        worker.excluded_sources = set()
        worker.skip_failed_functions = False
        worker.hard_reject_c_pointers = False
        worker._is_test_source = lambda source_name: str(source_name).startswith("tests/")
        worker._is_excluded_source_name = lambda source_name: False
        worker._is_cycle_placeholder_function = lambda code: False
        worker._find_forbidden_c_pointer_tokens = lambda code: []
        worker._collect_unfinished_direct_callees = lambda **kwargs: []
        worker._build_initial_prompt_context = lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("valid checkpoint should skip prompt build")
        )
        results = {"src_a": {"foo": "pub fn foo() -> i32 { 0 }\n"}}
        errors = {"src_a": {"foo": "stale failure"}}

        worker.process_func(
            test_source_name="tests/foo_test",
            func_name="foo",
            depth=0,
            results=results,
            all_error_funcs_content=errors,
            once_retry_count_dict={},
        )

        self.assertEqual(errors, {})

    def test_commit_accepted_translation_quarantines_runtime_failure_without_polluting_results(self):
        runtime_runner = _RuntimeTestRunner(RuntimeTestResult(ok=False, message="cargo test failed", archive=None))
        failure_builder = _FailureRecordBuilder()
        worker = FunctionTranslationWorker(
            runtime_test_runner=runtime_runner,
            failure_record_builder=failure_builder,
            logger=_NullLogger(),
        )
        results = {"src_a": {"old": "pub fn old() {}\n"}}
        errors = {}
        retry_counts = {}
        pending = {}
        runtime_status = {}
        state = _make_state(
            results=results,
            errors=errors,
            retry_counts=retry_counts,
            pending=pending,
            runtime_status=runtime_status,
        )

        ok = worker.commit_accepted_translation(
            state=state,
            accepted_archive={"src_a": {"foo": "pub fn foo() {}\n"}},
            success_log_label="PASS-LABEL",
            runtime_failure_log_label="FAIL-LABEL",
            swe_feedback="fallback note",
        )

        self.assertFalse(ok)
        self.assertEqual(results, {"src_a": {"old": "pub fn old() {}\n"}})
        self.assertEqual(runtime_runner.requests[0].archive["src_a"]["foo"], "pub fn foo() {}\n")
        self.assertEqual(pending, {"src_a": {"foo": "pub fn foo() {}\n"}})
        self.assertEqual(
            runtime_status,
            {
                "src_a": {
                    "foo": {
                        "status": "runtime_failed",
                        "test_source": "tests/foo_test",
                        "message": "cargo test failed",
                    }
                }
            },
        )
        self.assertEqual(retry_counts, {"src_a": {"foo": 4}})
        self.assertEqual(current_pipeline_stats().total_error_count, 1)
        self.assertEqual(
            errors,
            {
                "src_a": {
                    "foo": (
                        "summary=cargo check 通过，但 cargo test 未通过; "
                        "detail=cargo test failed; swe=fallback note; "
                        "template=pub fn foo() {}\n"
                    )
                }
            },
        )

    def test_commit_accepted_translation_rejects_roundtrip_compile_failure(self):
        runtime_runner = _RuntimeTestRunner(RuntimeTestResult(ok=True, message="runtime ok", archive=None))
        worker = FunctionTranslationWorker(
            runtime_test_runner=runtime_runner,
            failure_record_builder=_FailureRecordBuilder(),
            logger=_NullLogger(),
        )
        verify_calls = []

        def fake_verify(**kwargs):
            verify_calls.append(kwargs)
            return _VerifyResult(False, "missing import after rebuild"), 1, "primary", kwargs["include_files"]

        worker._verify_archive_with_strategy = fake_verify
        results = {"src_a": {"old": "pub fn old() {}\n"}}
        errors = {}
        pending = {}
        runtime_status = {}
        state = _make_state(
            results=results,
            errors=errors,
            pending=pending,
            runtime_status=runtime_status,
        )

        ok = worker.commit_accepted_translation(
            state=state,
            accepted_archive={"src_a": {"foo": "pub fn foo() {}\n"}},
            success_log_label="PASS-LABEL",
            runtime_failure_log_label="FAIL-LABEL",
        )

        self.assertFalse(ok)
        self.assertEqual(len(verify_calls), 1)
        self.assertEqual(results, {"src_a": {"old": "pub fn old() {}\n"}})
        self.assertEqual(pending, {"src_a": {"foo": "pub fn foo() {}\n"}})
        self.assertEqual(runtime_status["src_a"]["foo"]["status"], "roundtrip_compile_failed")
        self.assertIn("round-trip cargo check failed", errors["src_a"]["foo"])
        stats = current_pipeline_stats()
        self.assertEqual(stats.roundtrip_verify_failure_count, 1)
        self.assertEqual(stats.total_error_count, 1)

    def test_commit_accepted_translation_records_source_complete_runtime_deferred(self):
        runtime_runner = _RuntimeTestRunner(
            RuntimeTestResult(
                ok=True,
                message="runtime test check deferred to source completion",
                archive=None,
            )
        )
        worker = FunctionTranslationWorker(
            runtime_test_runner=runtime_runner,
            failure_record_builder=_FailureRecordBuilder(),
            logger=_NullLogger(),
        )
        results = {}
        errors = {}
        pending = {}
        runtime_status = {}
        source_runtime_status = {}
        state = _make_state(
            results=results,
            errors=errors,
            pending=pending,
            runtime_status=runtime_status,
            source_runtime_status=source_runtime_status,
        )

        ok = worker.commit_accepted_translation(
            state=state,
            accepted_archive={"src_a": {"foo": "pub fn foo() {}\n"}},
            success_log_label="PASS-LABEL",
            runtime_failure_log_label="FAIL-LABEL",
        )

        self.assertTrue(ok)
        self.assertEqual(results, {"src_a": {"foo": "pub fn foo() {}\n"}})
        self.assertEqual(pending, {})
        self.assertEqual(
            runtime_status["src_a"]["foo"]["status"],
            "runtime_deferred_source_complete",
        )
        self.assertEqual(
            source_runtime_status["src_a"]["status"],
            "runtime_deferred_source_complete",
        )

    def test_record_final_failure_writes_checkpoint_error_from_run_state(self):
        worker = FunctionTranslationWorker(
            runtime_test_runner=_RuntimeTestRunner(RuntimeTestResult(ok=True, message="unused")),
            failure_record_builder=_FailureRecordBuilder(),
            logger=_NullLogger(),
        )
        errors = {}
        state = _make_state(results={}, errors=errors, retry_counts={})

        worker.record_final_failure(state)

        self.assertEqual(current_pipeline_stats().total_error_count, 1)
        self.assertEqual(
            errors,
            {
                "src_a": {
                    "foo": (
                        "summary=cannot find value `bar`; "
                        "detail=error[E0425]: cannot find value `bar`; "
                        "swe=cc-mini unavailable; "
                        "template=pub fn foo() { todo!() }\n"
                    )
                }
            },
        )

    def test_function_run_state_tracks_verify_feedback_and_stop_reason(self):
        state = _make_state()

        state.add_verify_invocations(2)
        state.record_verify_feedback(
            summary_feedback="cannot find value",
            detailed_feedback="error[E0425]",
            diagnostic_codes={"E0425"},
            verify_result=object(),
            verify_scope=["src_a"],
        )
        state.request_stop("early_fallback", feedback="handoff to cc-mini")
        state.record_swe_note("first", max_notes=2)
        state.record_swe_note("second", max_notes=2)
        state.record_swe_note("third", max_notes=2)

        self.assertEqual(state.verify_invocations, 4)
        self.assertEqual(state.last_feedback, "handoff to cc-mini")
        self.assertEqual(state.last_detailed_compile_feedback, "error[E0425]")
        self.assertEqual(state.last_diagnostic_codes, {"E0425"})
        self.assertEqual(state.last_verify_scope, ["src_a"])
        self.assertTrue(state.forced_stop)
        self.assertEqual(state.forced_stop_reason, "early_fallback")
        self.assertEqual(state.swe_regen_notes, ["second", "third"])


if __name__ == "__main__":
    unittest.main()
