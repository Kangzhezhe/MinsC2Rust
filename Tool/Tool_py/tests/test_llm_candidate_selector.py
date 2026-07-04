import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.llm_candidate_selector import LlmCandidateSelector


class _Logger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(str(message))


class _VerifyResult:
    success = True
    diagnostics = []


class _Verifier:
    def __init__(self):
        self.calls = []

    def verify_modules(self, module_sources, crate_name):
        self.calls.append((dict(module_sources), crate_name))
        return _VerifyResult()


class LlmCandidateSelectorTest(unittest.TestCase):
    def test_selects_verified_candidate_over_parse_failure(self):
        responses = [
            ("fn foo() { bad", "chat-1", {}),
            ("pub fn foo() -> i32 { 1 }", "chat-2", {}),
        ]

        def call_llm_logged(**kwargs):
            return responses.pop(0)

        def apply_response_to_archive(response, func_name, source_name, include_files, base_archive, **kwargs):
            if "bad" in response:
                return None, "parse failed"
            return {"src/foo": {"foo": response}}, ""

        def build_module_sources(archive, include_files):
            return {"src_foo": archive["src/foo"]["foo"]}, []

        verifier = _Verifier()
        selector = LlmCandidateSelector(
            call_llm_logged=call_llm_logged,
            apply_response_to_archive=apply_response_to_archive,
            build_module_sources=build_module_sources,
            verifier=verifier,
            score_verify_result=lambda verify_result: (0, "success"),
            score_rust_style_penalty=lambda text: (0, "style=clean"),
            find_forbidden_c_pointer_tokens=lambda text: [],
            is_llm_transport_error=lambda text: False,
            logger=_Logger(),
            temperature_step=0.1,
            max_temperature=0.3,
            hard_reject_c_pointers=True,
        )

        response, chat_id, verify_used = selector.select(
            prompt="translate foo",
            llm_model="fake-model",
            timeout_seconds=5,
            base_temperature=0.0,
            candidate_count=2,
            test_source_name="tests/foo",
            source_name="src/foo",
            func_name="foo",
            include_files=["src/foo"],
            verify_include_files=["src/foo"],
            base_archive={},
            remaining_verify_budget=2,
            stage="initial",
        )

        self.assertEqual(response, "pub fn foo() -> i32 { 1 }")
        self.assertEqual(chat_id, "chat-2")
        self.assertEqual(verify_used, 1)
        self.assertEqual(len(verifier.calls), 1)
        self.assertEqual(verifier.calls[0][0], {"src_foo": "pub fn foo() -> i32 { 1 }"})


if __name__ == "__main__":
    unittest.main()
