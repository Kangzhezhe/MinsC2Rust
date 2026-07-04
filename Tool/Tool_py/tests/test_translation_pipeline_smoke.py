import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.translation_pipeline import TranslationPipeline
from pipeline.function_worker import FunctionRunState


class _Logger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(str(message))

    def warning(self, message):
        self.messages.append(str(message))

    def error(self, message):
        self.messages.append(str(message))


class _DataManager:
    include_files_indices = {0}
    all_include_files = ["src"]
    all_pointer_funcs = set()
    include_dict = {}
    data = [{"foo": "int foo(void) { return 1; }"}]

    def get_content(self, func_name, respect_scope=True):
        return self.data[0].get(func_name, ""), "", 0

    def get_decl_owner(self, symbol):
        return ""


class _Verifier:
    pass


class _FakeCcMiniOptions:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class _FakeCcMiniAgent:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.engine = type("_Engine", (), {"tools": []})()


class TranslationPipelineSmokeTest(unittest.TestCase):
    def test_static_error_classifiers_keep_retry_policy_stable(self):
        self.assertTrue(TranslationPipeline._is_llm_transport_error("请求超时: model endpoint did not answer"))
        self.assertFalse(TranslationPipeline._is_llm_transport_error("error[E0425]: cannot find value"))
        self.assertTrue(TranslationPipeline._is_structural_syntax_failure("unclosed delimiter in generated module"))
        self.assertFalse(TranslationPipeline._is_structural_syntax_failure("cannot find value `x`"))
        self.assertEqual(
            TranslationPipeline._find_forbidden_c_pointer_tokens("let p: *mut libc::c_void; let q: void *;"),
            ["c_void(any namespace)", "void*"],
        )

    def test_process_func_preserves_valid_existing_checkpoint_without_llm(self):
        logger = _Logger()
        with tempfile.TemporaryDirectory() as tmp:
            pipeline = TranslationPipeline(
                data_manager=_DataManager(),
                source_names=["src"],
                funcs_childs={"test_src": {"foo": []}},
                logger=logger,
                llm_model="openai",
                verifier=_Verifier(),
                params={"max_retries": 3, "max_regenerations": 2},
                output_dir=tmp,
            )
            results = {"src": {"foo": "pub fn foo() -> i32 { 1 }"}}
            errors = {"src": {"foo": "historical failure"}}
            retry_counts = {}

            pipeline.process_func(
                test_source_name="test_src",
                func_name="foo",
                depth=0,
                results=results,
                all_error_funcs_content=errors,
                once_retry_count_dict=retry_counts,
            )

            self.assertEqual(results, {"src": {"foo": "pub fn foo() -> i32 { 1 }"}})
            self.assertEqual(errors, {})
            self.assertEqual(retry_counts, {})
            self.assertTrue(
                any("[CLEAR-STALE-ERROR] src:foo" in message for message in logger.messages),
                logger.messages,
            )

    def test_pipeline_components_do_not_fallback_to_global_pipeline_namespace(self):
        logger = _Logger()
        with tempfile.TemporaryDirectory() as tmp:
            pipeline = TranslationPipeline(
                data_manager=_DataManager(),
                source_names=["src"],
                funcs_childs={"test_src": {"foo": []}},
                logger=logger,
                llm_model="openai",
                verifier=_Verifier(),
                params={"max_retries": 3, "max_regenerations": 2},
                output_dir=tmp,
            )

            self.assertNotEqual(type(pipeline.function_worker).__name__, "_PipelineComponentAdapter")
            self.assertFalse(hasattr(pipeline.function_worker, "_merge_extra"))
            self.assertFalse(hasattr(TranslationPipeline, "__getattr__"))

    def test_pipeline_wired_function_worker_records_final_failure(self):
        logger = _Logger()
        with tempfile.TemporaryDirectory() as tmp:
            pipeline = TranslationPipeline(
                data_manager=_DataManager(),
                source_names=["src"],
                funcs_childs={"test_src": {"foo": []}},
                logger=logger,
                llm_model="openai",
                verifier=_Verifier(),
                params={"max_retries": 3, "max_regenerations": 2},
                output_dir=tmp,
            )
            errors = {}
            state = FunctionRunState(
                test_source_name="test_src",
                source_name="src",
                func_name="foo",
                include_files=["src"],
                results={},
                all_error_funcs_content=errors,
                once_retry_count_dict={},
                last_template="pub fn foo() {}\n",
                last_feedback="LLM failed",
                last_detailed_compile_feedback="transport error",
            )

            pipeline.function_worker.record_final_failure(state)

            self.assertIn("foo", errors["src"])
            self.assertIn("LLM failed", errors["src"]["foo"])
            self.assertIn("transport error", errors["src"]["foo"])

    def test_cc_mini_default_config_can_come_from_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".cc-mini.toml"
            config_path.write_text("model = 'test'\n", encoding="utf-8")

            with mock.patch.dict(os.environ, {"CC_MINI_CONFIG": str(config_path)}, clear=False):
                self.assertEqual(
                    TranslationPipeline._derive_cc_mini_default_config_path(),
                    str(config_path),
                )

    def test_cc_mini_agent_instances_are_isolated_per_request(self):
        logger = _Logger()
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".cc-mini.toml"
            config_path.write_text("model = 'test'\n", encoding="utf-8")
            pipeline = TranslationPipeline(
                data_manager=_DataManager(),
                source_names=["src"],
                funcs_childs={"test_src": {"foo": []}},
                logger=logger,
                llm_model="openai",
                verifier=_Verifier(),
                params={
                    "enable_cc_mini_agent_fallback": 1,
                    "cc_mini_config": str(config_path),
                },
                output_dir=tmp,
            )

            with mock.patch.object(TranslationPipeline, "_cc_mini_agent_class", _FakeCcMiniAgent), \
                 mock.patch.object(TranslationPipeline, "_cc_mini_options_class", _FakeCcMiniOptions), \
                 mock.patch.object(TranslationPipeline, "_cc_mini_agent_import_attempted", True), \
                 mock.patch.object(TranslationPipeline, "_cc_mini_agent_import_error", ""):
                first = pipeline._get_cc_mini_agent_instance(tmp)
                second = pipeline._get_cc_mini_agent_instance(tmp)

            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            self.assertIsNot(first, second)
            self.assertEqual(len(pipeline._cc_mini_agent_instances), 2)
            self.assertTrue(any("isolated=1" in msg for msg in logger.messages))

    def test_cc_mini_memory_dir_is_scoped_to_current_run_output(self):
        logger = _Logger()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "Output"
            output_dir.mkdir()
            config_path = Path(tmp) / ".cc-mini.toml"
            config_path.write_text("model = 'test'\n", encoding="utf-8")
            pipeline = TranslationPipeline(
                data_manager=_DataManager(),
                source_names=["src"],
                funcs_childs={"test_src": {"foo": []}},
                logger=logger,
                llm_model="openai",
                verifier=_Verifier(),
                params={
                    "enable_cc_mini_agent_fallback": 1,
                    "cc_mini_config": str(config_path),
                },
                output_dir=str(output_dir),
            )

            with mock.patch.object(TranslationPipeline, "_cc_mini_agent_class", _FakeCcMiniAgent), \
                 mock.patch.object(TranslationPipeline, "_cc_mini_options_class", _FakeCcMiniOptions), \
                 mock.patch.object(TranslationPipeline, "_cc_mini_agent_import_attempted", True), \
                 mock.patch.object(TranslationPipeline, "_cc_mini_agent_import_error", ""):
                agent = pipeline._get_cc_mini_agent_instance(tmp)

            expected = output_dir / "state" / "cc_mini_memory"
            self.assertIsNotNone(agent)
            cc_mini_options = agent._agent.kwargs["options"]
            self.assertEqual(cc_mini_options.kwargs["memory_dir"], str(expected))
            self.assertTrue(expected.is_dir())

    def test_source_complete_runtime_check_merges_repaired_archive(self):
        logger = _Logger()
        with tempfile.TemporaryDirectory() as tmp:
            data_manager = _DataManager()
            data_manager.all_include_files = ["src", "test_src"]
            pipeline = TranslationPipeline(
                data_manager=data_manager,
                source_names=["src", "test_src"],
                funcs_childs={"test_src": {"test_foo": []}},
                logger=logger,
                llm_model="openai",
                verifier=_Verifier(),
                params={
                    "test_runtime_check_enabled": 1,
                    "test_runtime_check_mode": "source_complete",
                },
                output_dir=tmp,
            )
            results = {
                "src": {"foo": "pub fn foo() -> i32 { 1 }\n"},
                "test_src": {"test_foo": "#[test]\npub fn test_foo() { assert_eq!(1, 1); }\n"},
                "shared": {"helper": "pub fn helper() -> i32 { 1 }\n"},
                "test_other": {"test_other": "#[test]\npub fn test_other() {}\n"},
            }
            errors = {
                "shared": {
                    "helper": "stale helper failure",
                    "still_failed": "do not clear unrelated failed function",
                }
            }
            repaired = {
                "src": {"foo": "pub fn foo() -> i32 { 2 }\n"},
                "test_src": {
                    "test_foo": "#[test]\npub fn test_foo() { assert_eq!(2, 2); }\n",
                    "test_bar": "#[test]\npub fn test_bar() {}\n",
                },
                "shared": {"helper": "pub fn helper() -> i32 { 2 }\n"},
                "test_other": {"test_other": "#[test]\npub fn test_other() { assert!(true); }\n"},
            }
            calls = []

            def fake_source_runtime(**kwargs):
                calls.append(kwargs)
                return True, "runtime cargo test passed via CC-MINI", repaired

            pipeline.cc_mini_fallback._run_source_module_with_optional_swe_repair = fake_source_runtime

            pipeline._run_source_runtime_check_after_completion(
                test_source_name="test_src",
                results=results,
                all_error_funcs_content=errors,
            )

            self.assertEqual(len(calls), 1)
            self.assertEqual(results["src"]["foo"], "pub fn foo() -> i32 { 2 }\n")
            self.assertIn("test_bar", results["test_src"])
            self.assertEqual(results["shared"]["helper"], "pub fn helper() -> i32 { 2 }\n")
            self.assertEqual(
                results["test_other"]["test_other"],
                "#[test]\npub fn test_other() { assert!(true); }\n",
            )
            self.assertEqual(errors, {"shared": {"still_failed": "do not clear unrelated failed function"}})
            self.assertEqual(
                pipeline.source_runtime_status["test_src"]["status"],
                "source_runtime_ok",
            )
            self.assertEqual(
                pipeline.runtime_status["test_src"]["__source_complete__"]["status"],
                "source_runtime_passed",
            )
            self.assertEqual(
                pipeline.repair_records["test_src"][0]["modified_files"],
                ["src", "test_src", "shared", "test_other"],
            )

    def test_source_complete_runtime_check_skips_when_full_project_pass_cache_matches(self):
        logger = _Logger()
        with tempfile.TemporaryDirectory() as tmp:
            data_manager = _DataManager()
            data_manager.all_include_files = ["src", "test_src"]
            pipeline = TranslationPipeline(
                data_manager=data_manager,
                source_names=["src", "test_src"],
                funcs_childs={"test_src": {"test_foo": []}},
                logger=logger,
                llm_model="openai",
                verifier=_Verifier(),
                params={
                    "test_runtime_check_enabled": 1,
                    "test_runtime_check_mode": "source_complete",
                },
                output_dir=tmp,
                source_runtime_pass_cache={},
            )
            results = {
                "src": {"foo": "pub fn foo() -> i32 { 1 }\n"},
                "test_src": {"test_foo": "#[test]\npub fn test_foo() { assert_eq!(1, 1); }\n"},
            }
            errors = {}
            runtime_archive = pipeline.function_worker._build_runtime_test_archive(
                results,
                {},
                ["src", "test_src"],
            )
            fingerprint = pipeline._fingerprint_source_runtime_archive(
                runtime_archive,
                ["src", "test_src"],
            )
            pipeline.source_runtime_pass_cache.update(
                {
                    "version": 2,
                    "passes": {
                        fingerprint: {
                            "fingerprint": fingerprint,
                            "command": "cargo test --quiet",
                            "mode": "source_complete",
                            "passed_by_source": "test_src",
                        }
                    },
                }
            )

            def fail_if_called(**kwargs):
                raise AssertionError("source runtime repair should be skipped on cache hit")

            pipeline.cc_mini_fallback._run_source_module_with_optional_swe_repair = fail_if_called

            pipeline._run_source_runtime_check_after_completion(
                test_source_name="test_src",
                results=results,
                all_error_funcs_content=errors,
            )

            self.assertEqual(
                pipeline.source_runtime_status["test_src"]["status"],
                "source_runtime_ok",
            )
            self.assertEqual(
                pipeline.runtime_status["test_src"]["__source_complete__"]["status"],
                "source_runtime_passed_cached",
            )
            self.assertTrue(any("[SOURCE-RUNTIME-SKIP-CACHED-PASS]" in msg for msg in logger.messages))

    def test_source_runtime_fingerprint_ignores_source_specific_include_scope(self):
        logger = _Logger()
        with tempfile.TemporaryDirectory() as tmp:
            data_manager = _DataManager()
            data_manager.all_include_files = ["src", "test_src"]
            pipeline = TranslationPipeline(
                data_manager=data_manager,
                source_names=["src", "test_src"],
                funcs_childs={"test_src": {"test_foo": []}},
                logger=logger,
                llm_model="openai",
                verifier=_Verifier(),
                params={
                    "test_runtime_check_enabled": 1,
                    "test_runtime_check_mode": "source_complete",
                },
                output_dir=tmp,
            )
            archive = {
                "src": {"foo": "pub fn foo() -> i32 { 1 }\n"},
                "test_src": {"test_foo": "#[test]\npub fn test_foo() { assert_eq!(1, 1); }\n"},
            }

            self.assertEqual(
                pipeline._fingerprint_source_runtime_archive(archive, ["src", "test_src"]),
                pipeline._fingerprint_source_runtime_archive(archive, ["src"]),
            )

    def test_source_complete_runtime_check_reruns_when_pass_cache_fingerprint_changes(self):
        logger = _Logger()
        with tempfile.TemporaryDirectory() as tmp:
            data_manager = _DataManager()
            data_manager.all_include_files = ["src", "test_src"]
            pipeline = TranslationPipeline(
                data_manager=data_manager,
                source_names=["src", "test_src"],
                funcs_childs={"test_src": {"test_foo": []}},
                logger=logger,
                llm_model="openai",
                verifier=_Verifier(),
                params={
                    "test_runtime_check_enabled": 1,
                    "test_runtime_check_mode": "source_complete",
                },
                output_dir=tmp,
                source_runtime_pass_cache={
                    "version": 2,
                    "passes": {
                        "sha256:stale": {
                            "fingerprint": "sha256:stale",
                            "command": "cargo test --quiet",
                            "mode": "source_complete",
                            "passed_by_source": "test_src",
                        }
                    }
                },
            )
            results = {
                "src": {"foo": "pub fn foo() -> i32 { 1 }\n"},
                "test_src": {"test_foo": "#[test]\npub fn test_foo() { assert_eq!(1, 1); }\n"},
            }
            errors = {}
            calls = []

            def fake_source_runtime(**kwargs):
                calls.append(kwargs)
                return True, "cargo test passed", None

            pipeline.cc_mini_fallback._run_source_module_with_optional_swe_repair = fake_source_runtime

            pipeline._run_source_runtime_check_after_completion(
                test_source_name="test_src",
                results=results,
                all_error_funcs_content=errors,
            )

            self.assertEqual(len(calls), 1)
            self.assertEqual(pipeline.source_runtime_pass_cache["version"], 2)
            self.assertIn("sha256:stale", pipeline.source_runtime_pass_cache["passes"])
            self.assertEqual(len(pipeline.source_runtime_pass_cache["passes"]), 2)
            new_entries = [
                entry
                for key, entry in pipeline.source_runtime_pass_cache["passes"].items()
                if key != "sha256:stale"
            ]
            self.assertEqual(len(new_entries), 1)
            self.assertEqual(new_entries[0]["passed_by_source"], "test_src")

    def test_source_complete_runtime_check_ignores_legacy_last_pass_cache(self):
        logger = _Logger()
        with tempfile.TemporaryDirectory() as tmp:
            data_manager = _DataManager()
            data_manager.all_include_files = ["src", "test_src"]
            pipeline = TranslationPipeline(
                data_manager=data_manager,
                source_names=["src", "test_src"],
                funcs_childs={"test_src": {"test_foo": []}},
                logger=logger,
                llm_model="openai",
                verifier=_Verifier(),
                params={
                    "test_runtime_check_enabled": 1,
                    "test_runtime_check_mode": "source_complete",
                },
                output_dir=tmp,
                source_runtime_pass_cache={},
            )
            results = {
                "src": {"foo": "pub fn foo() -> i32 { 1 }\n"},
                "test_src": {"test_foo": "#[test]\npub fn test_foo() { assert_eq!(1, 1); }\n"},
            }
            runtime_archive = pipeline.function_worker._build_runtime_test_archive(
                results,
                {},
                ["src", "test_src"],
            )
            fingerprint = pipeline._fingerprint_source_runtime_archive(
                runtime_archive,
                ["src", "test_src"],
            )
            pipeline.source_runtime_pass_cache["last_pass"] = {
                "fingerprint": fingerprint,
                "command": "cargo test --quiet",
                "mode": "source_complete",
                "passed_by_source": "test_src",
            }
            calls = []

            def fake_source_runtime(**kwargs):
                calls.append(kwargs)
                return True, "cargo test passed", None

            pipeline.cc_mini_fallback._run_source_module_with_optional_swe_repair = fake_source_runtime

            pipeline._run_source_runtime_check_after_completion(
                test_source_name="test_src",
                results=results,
                all_error_funcs_content={},
            )

            self.assertEqual(len(calls), 1)
            self.assertNotIn("last_pass", pipeline.source_runtime_pass_cache)
            self.assertEqual(pipeline.source_runtime_pass_cache["version"], 2)

    def test_cc_mini_loader_accepts_environment_package_path(self):
        old_sys_path = list(sys.path)
        old_module = sys.modules.pop("cc_mini", None)
        old_cache = (
            TranslationPipeline._cc_mini_agent_import_attempted,
            TranslationPipeline._cc_mini_agent_import_error,
            TranslationPipeline._cc_mini_agent_class,
            TranslationPipeline._cc_mini_options_class,
        )
        TranslationPipeline._cc_mini_agent_import_attempted = False
        TranslationPipeline._cc_mini_agent_import_error = ""
        TranslationPipeline._cc_mini_agent_class = None
        TranslationPipeline._cc_mini_options_class = None

        try:
            with tempfile.TemporaryDirectory() as tmp:
                package_dir = Path(tmp) / "cc_mini"
                package_dir.mkdir()
                (package_dir / "__init__.py").write_text(
                    "class CCMini:\n"
                    "    pass\n\n"
                    "class CCMiniOptions:\n"
                    "    pass\n",
                    encoding="utf-8",
                )

                with mock.patch.dict(os.environ, {"CC_MINI_PATH": str(package_dir)}, clear=False):
                    cc_mini_cls = TranslationPipeline._load_cc_mini_agent_class()

                self.assertIsNotNone(cc_mini_cls)
                self.assertEqual(cc_mini_cls.__name__, "CCMini")
                self.assertEqual(TranslationPipeline._cc_mini_agent_import_error, "")
        finally:
            sys.path[:] = old_sys_path
            sys.modules.pop("cc_mini", None)
            if old_module is not None:
                sys.modules["cc_mini"] = old_module
            (
                TranslationPipeline._cc_mini_agent_import_attempted,
                TranslationPipeline._cc_mini_agent_import_error,
                TranslationPipeline._cc_mini_agent_class,
                TranslationPipeline._cc_mini_options_class,
            ) = old_cache


if __name__ == "__main__":
    unittest.main()
