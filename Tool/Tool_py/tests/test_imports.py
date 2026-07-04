import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))


class ImportCompatibilityTest(unittest.TestCase):
    def test_translation_pipeline_imports_from_new_module(self):
        from pipeline.translation_pipeline import TranslationPipeline, _current_pipeline_stats

        self.assertEqual(TranslationPipeline.__name__, "TranslationPipeline")
        self.assertEqual(_current_pipeline_stats().total_retry_count, 0)

    def test_translation_pipeline_uses_composition_instead_of_mixin_inheritance(self):
        from pipeline.auto_repair import AutoRepairActions
        from pipeline.cc_mini_fallback import CcMiniFallbackCoordinator
        from pipeline.function_worker import FunctionTranslationWorker
        from pipeline.prompt_builder import PromptBuilder
        from pipeline.rust_archive import RustArchiveBuilder
        from pipeline.rust_project_export import RustProjectExporter
        from pipeline.translation_pipeline import TranslationPipeline
        import pipeline.translation_pipeline as translation_pipeline_module
        from pipeline.translation_scheduler import TranslationScheduler
        from pipeline.verification_flow import VerificationFlow

        forbidden_bases = {
            AutoRepairActions,
            CcMiniFallbackCoordinator,
            FunctionTranslationWorker,
            PromptBuilder,
            RustArchiveBuilder,
            RustProjectExporter,
            TranslationScheduler,
            VerificationFlow,
        }

        self.assertTrue(forbidden_bases.isdisjoint(set(TranslationPipeline.__mro__[1:])))
        self.assertTrue(hasattr(TranslationPipeline, "process_func"))
        self.assertTrue(hasattr(TranslationPipeline, "process_test_source"))
        self.assertTrue(hasattr(TranslationPipeline, "sync_archive_imports"))
        self.assertFalse(
            any(name.startswith("_Bound") for name in vars(translation_pipeline_module))
        )

    def test_clear_support_module_names_import(self):
        from pipeline.cc_mini_runtime import CcMiniCommandToolset, CcMiniRuntimeAgentAdapter
        from pipeline.cc_mini_fallback import CcMiniFallbackCoordinator
        from pipeline.auto_repair import AutoRepairActions
        from pipeline.function_worker import FunctionTranslationWorker
        from pipeline.rust_archive import RustArchiveBuilder
        from pipeline.rust_project_export import RustProjectExporter
        from pipeline.translation_scheduler import TranslationScheduler
        from pipeline.verification_flow import VerificationFlow

        self.assertTrue(hasattr(RustArchiveBuilder, "_apply_response_to_archive"))
        self.assertTrue(hasattr(RustProjectExporter, "export_archive_to_project"))
        self.assertTrue(hasattr(CcMiniFallbackCoordinator, "_attempt_cc_mini_agent_fallback"))
        self.assertTrue(hasattr(CcMiniCommandToolset, "run_rust_debug_script"))
        self.assertTrue(hasattr(CcMiniRuntimeAgentAdapter, "run_task"))
        self.assertTrue(hasattr(TranslationScheduler, "process_test_source"))
        self.assertTrue(hasattr(AutoRepairActions, "_auto_alias_missing_test_values"))
        self.assertTrue(hasattr(VerificationFlow, "_verify_archive_with_strategy"))
        self.assertTrue(hasattr(FunctionTranslationWorker, "process_func"))


if __name__ == "__main__":
    unittest.main()
