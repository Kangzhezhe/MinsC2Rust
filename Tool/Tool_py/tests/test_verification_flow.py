import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.verification_flow import VerificationFlow


def _verification_flow():
    flow = VerificationFlow()
    flow._clip_text = lambda text, max_chars: str(text or "") if len(str(text or "")) <= max_chars else str(text or "")[:max_chars]
    return flow


class VerificationFlowTest(unittest.TestCase):
    def test_strip_cargo_check_raw_keeps_model_relevant_prefix(self):
        detail = "first useful line\n[cargo-check-raw]\nraw cargo noise"

        self.assertEqual(VerificationFlow._strip_cargo_check_raw(detail), "first useful line")

    def test_score_single_diagnostic_prioritizes_timeouts(self):
        timeout_diag = SimpleNamespace(code="TIMEOUT", message="", rendered="")
        missing_value_diag = SimpleNamespace(code="E0425", message="cannot find value", rendered="")

        self.assertGreater(
            VerificationFlow._score_single_diagnostic(timeout_diag),
            VerificationFlow._score_single_diagnostic(missing_value_diag),
        )

    def test_format_verify_diagnostics_filters_focus_modules_and_keeps_raw_output(self):
        verify_result = SimpleNamespace(
            diagnostics=[
                SimpleNamespace(
                    module="target_mod",
                    level="error",
                    code="E0425",
                    line=7,
                    column=9,
                    message="cannot find value",
                    rendered="rendered target",
                ),
                SimpleNamespace(
                    module="other_mod",
                    level="error",
                    code="E0308",
                    line=1,
                    column=1,
                    message="mismatched types",
                    rendered="rendered other",
                ),
            ],
            raw_output="raw cargo output",
            summarize_for_llm=lambda max_items=12: "summary",
        )

        formatted = _verification_flow()._format_verify_diagnostics_for_debug(
            verify_result,
            focus_modules={"target_mod"},
        )

        self.assertIn("[error] E0425 target_mod:7:9 cannot find value", formatted)
        self.assertIn("rendered target", formatted)
        self.assertIn("[cargo-check-raw]", formatted)
        self.assertIn("raw cargo output", formatted)
        self.assertNotIn("other_mod", formatted)

    def test_bucket_has_translated_content_checks_extra_and_functions(self):
        self.assertFalse(VerificationFlow._bucket_has_translated_content({}))
        self.assertFalse(VerificationFlow._bucket_has_translated_content({"extra": "  ", "foo": ""}))
        self.assertTrue(VerificationFlow._bucket_has_translated_content({"extra": "pub const X: usize = 1;"}))
        self.assertTrue(VerificationFlow._bucket_has_translated_content({"foo": "pub fn foo() {}"}))

    def test_collect_verify_scope_sources_follows_includes_and_direct_callees(self):
        class DataManager:
            include_dict = {"src_a": ["src_b"], "src_b": []}

            def get_source_name_by_func_name(self, name, respect_scope=False):
                return {"child": "src_c"}.get(name, "")

        harness = _verification_flow()
        harness.owner_scoped_verify = True
        harness.data_manager = DataManager()
        harness.funcs_childs = {"src_a": {"root": ["child"]}}
        harness._is_test_source = lambda source_name: source_name.startswith("tests/")

        scope = harness._collect_verify_scope_sources(
            source_name="src_a",
            include_files=["src_a", "src_b", "src_c", "tests/foo_test"],
        )

        self.assertEqual(scope, ["src_a", "src_b", "src_c"])


if __name__ == "__main__":
    unittest.main()
