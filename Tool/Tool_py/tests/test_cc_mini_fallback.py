import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.cc_mini_fallback import CcMiniFallbackCoordinator
from pipeline.rust_archive import RustArchiveBuilder
from pipeline.stats import PipelineStats, apply_pipeline_stats, current_pipeline_stats


class _Logger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(str(message))


class _Verifier:
    dependency_overrides = {}


class _DataManager:
    include_dict = {}

    def get_decl_owner(self, symbol):
        return ""

    def get_source_name_by_func_name(self, name, respect_scope=False):
        return ""


class _RuntimeFailingToolset:
    def run_command(self, command):
        return {"returncode": 101, "stdout": "still failing", "stderr": ""}


class _RuntimeFailingAgent:
    def __init__(self, name):
        self.name = name
        self.toolset = _RuntimeFailingToolset()
        self.tools = {}

    def register_tools(self, tools):
        self.tools = {getattr(tool, "__name__", str(idx)): tool for idx, tool in enumerate(tools)}

    def run_task(self, task, acceptance_criteria=None, extra_notes=""):
        return {
            "success": False,
            "final_response": f"{self.name} failed",
            "tool_calls": [
                {
                    "name": "run_command",
                    "args": {"command": "cargo test --quiet"},
                    "result": {"returncode": 101, "stdout": "still failing", "stderr": ""},
                }
            ],
        }


def _archive_builder():
    builder = RustArchiveBuilder()
    builder.source_names = ["src/foo"]
    builder.funcs_childs = {}
    builder.data_manager = _DataManager()
    builder.logger = _Logger()
    builder.enable_dependency_import_guessing = False
    builder._collect_source_dependency_sources = lambda source_name, include_file_set: []
    return builder


def _fallback_coordinator():
    builder = _archive_builder()
    coordinator = CcMiniFallbackCoordinator()
    coordinator.source_names = ["src/foo"]
    coordinator.funcs_childs = {}
    coordinator.data_manager = _DataManager()
    coordinator.enable_dependency_import_guessing = False
    coordinator.logger = _Logger()
    coordinator.verifier = _Verifier()
    coordinator.project_dependency_overrides = {}
    coordinator.swe_regen_assist_max_notes = 3
    coordinator._clip_text = lambda text, max_chars: str(text or "") if len(str(text or "")) <= max_chars else str(text or "")[:max_chars]
    coordinator._collect_source_dependency_sources = lambda source_name, include_file_set: []
    coordinator._dedupe_use_statements = RustArchiveBuilder._dedupe_use_statements
    coordinator._ensure_public_function = RustArchiveBuilder._ensure_public_function
    coordinator._is_test_source = RustArchiveBuilder._is_test_source
    coordinator._preserve_owned_declaration_blocks = builder._preserve_owned_declaration_blocks
    coordinator._sanitize_non_function_content = RustArchiveBuilder._sanitize_non_function_content
    coordinator._trim_to_function_definition = RustArchiveBuilder._trim_to_function_definition
    return coordinator


class CcMiniFallbackCoordinatorTest(unittest.TestCase):
    def setUp(self):
        apply_pipeline_stats(PipelineStats())

    def tearDown(self):
        apply_pipeline_stats(PipelineStats())

    def test_acceptance_command_normalization_is_owned_by_coordinator(self):
        self.assertEqual(
            CcMiniFallbackCoordinator._collapse_whitespace(" cargo   check\n--tests\t--quiet "),
            "cargo check --tests --quiet",
        )

    def test_parse_dependency_overrides_ignores_libc_and_non_dependency_sections(self):
        cargo_toml = "\n".join(
            [
                "[package]",
                'name = "verify_project"',
                "",
                "[dependencies]",
                'libc = "0.2"',
                'regex = "1"',
                'serde = { version = "1", features = ["derive"] }',
                "",
                "[dev-dependencies]",
                'tempfile = "3"',
            ]
        )

        overrides = CcMiniFallbackCoordinator._parse_dependency_overrides_from_cargo_toml(cargo_toml)

        self.assertEqual(
            overrides,
            {
                "regex": '"1"',
                "serde": '{ version = "1", features = ["derive"] }',
            },
        )

    def test_update_dependency_overrides_syncs_verifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            cargo_path = Path(tmp) / "Cargo.toml"
            cargo_path.write_text(
                "\n".join(
                    [
                        "[dependencies]",
                        'regex = "1"',
                        'rand = "0.8"',
                    ]
                ),
                encoding="utf-8",
            )
            harness = _fallback_coordinator()

            changed = harness._update_dependency_overrides_from_cargo_toml(str(cargo_path), "unit-test")

            self.assertEqual(changed, 2)
            self.assertEqual(harness.project_dependency_overrides, {"regex": '"1"', "rand": '"0.8"'})
            self.assertEqual(harness.verifier.dependency_overrides, harness.project_dependency_overrides)
            self.assertTrue(any("[DEPENDENCY-OVERRIDE]" in msg for msg in harness.logger.messages))

    def test_validate_acceptance_command_accepts_exact_success(self):
        ok, message = _fallback_coordinator()._validate_swe_acceptance_command(
            {
                "tool_calls": [
                    {
                        "name": "run_command",
                        "args": {"command": "cargo check --tests --quiet"},
                        "result": {"returncode": 0, "stdout": "", "stderr": ""},
                    }
                ]
            },
            "cargo check --tests --quiet",
        )

        self.assertTrue(ok)
        self.assertEqual(message, "")

    def test_validate_acceptance_command_uses_requested_command_instead_of_hardcoded_cargo_check(self):
        ok, message = _fallback_coordinator()._validate_swe_acceptance_command(
            {
                "tool_calls": [
                    {
                        "name": "run_command",
                        "args": {"command": "cargo test --quiet"},
                        "result": {"returncode": 0, "stdout": "", "stderr": ""},
                    }
                ]
            },
            "cargo test --quiet",
        )

        self.assertTrue(ok, message)

    def test_validate_acceptance_command_rejects_wrapped_or_failing_commands(self):
        harness = _fallback_coordinator()

        wrapped_ok, wrapped_message = harness._validate_swe_acceptance_command(
            {
                "tool_calls": [
                    {
                        "name": "run_command",
                        "args": {"command": "bash -lc 'cargo check --tests --quiet'"},
                        "result": {"returncode": 0, "stdout": "", "stderr": ""},
                    }
                ]
            },
            "cargo check --tests --quiet",
        )
        exact_fail_ok, exact_fail_message = harness._validate_swe_acceptance_command(
            {
                "tool_calls": [
                    {
                        "name": "run_command",
                        "args": {"command": "cargo check --tests --quiet"},
                        "result": {"returncode": 101, "stdout": "", "stderr": "error[E0425]: missing"},
                    }
                ]
            },
            "cargo check --tests --quiet",
        )

        self.assertFalse(wrapped_ok)
        self.assertIn("包装命令", wrapped_message)
        self.assertFalse(exact_fail_ok)
        self.assertIn("返回码非 0", exact_fail_message)

    def test_validate_acceptance_command_rejects_zero_returncode_with_error_output(self):
        ok, message = _fallback_coordinator()._validate_swe_acceptance_command(
            {
                "tool_calls": [
                    {
                        "name": "run_command",
                        "args": {"command": "cargo check --tests --quiet"},
                        "result": {"returncode": 0, "stdout": "", "stderr": "error[E0308]: mismatched"},
                    }
                ]
            },
            "cargo check --tests --quiet",
        )

        self.assertFalse(ok)
        self.assertIn("编译错误标记", message)

    def test_summarize_tool_output_prefers_stderr_then_stdout_and_limits_lines(self):
        summary = CcMiniFallbackCoordinator._summarize_tool_output(
            {
                "stderr": "err1\nerr2\nerr3",
                "stdout": "out1\nout2",
            },
            max_lines=4,
        )

        self.assertEqual(summary, "err1\nerr2\nerr3\nout1")

    def test_rebuild_bucket_from_module_text_preserves_previous_valid_functions(self):
        harness = _fallback_coordinator()
        module_text = "\n".join(
            [
                "pub struct Item { pub value: i32 }",
                "",
                "pub fn target() -> i32 { 2 }",
            ]
        )

        bucket, error = harness._rebuild_bucket_from_module_text(
            source_name="src/foo",
            module_text=module_text,
            required_func="target",
            previous_bucket={"helper": "pub fn helper() -> i32 { 1 }\n"},
        )

        self.assertEqual(error, "")
        self.assertIn("pub struct Item", bucket["extra"])
        self.assertIn("pub fn target() -> i32", bucket["target"])
        self.assertIn("pub fn helper() -> i32", bucket["helper"])
        self.assertTrue(any("[REBUILD-PRESERVE-FN]" in msg for msg in harness.logger.messages))

    def test_rebuild_bucket_skips_previous_function_with_duplicate_rust_fn_name(self):
        harness = _fallback_coordinator()
        module_text = "\n".join(
            [
                "pub fn is_valid_binn_header() -> bool {",
                "    true",
                "}",
            ]
        )

        bucket, error = harness._rebuild_bucket_from_module_text(
            source_name="binn",
            module_text=module_text,
            required_func="is_valid_binn_header",
            previous_bucket={
                "IsValidBinnHeader": "pub fn is_valid_binn_header() -> bool { false }\n",
                "helper": "pub fn helper() -> i32 { 1 }\n",
            },
        )

        self.assertEqual(error, "")
        self.assertIn("is_valid_binn_header", bucket)
        self.assertNotIn("IsValidBinnHeader", bucket)
        self.assertIn("helper", bucket)
        self.assertTrue(
            any("[REBUILD-PRESERVE-SKIP-DUP] binn skipped=IsValidBinnHeader" in msg for msg in harness.logger.messages),
            harness.logger.messages,
        )

    def test_rebuild_bucket_from_module_text_preserves_multiline_grouped_imports(self):
        harness = _fallback_coordinator()
        module_text = "\n".join(
            [
                "use crate::alloc_testing::{",
                "    alloc_test_calloc,",
                "    alloc_test_free,",
                "    alloc_test_malloc,",
                "};",
                "",
                "pub fn test_malloc_free() {",
                "    let block = alloc_test_malloc(8).unwrap();",
                "    alloc_test_free(block);",
                "}",
            ]
        )

        bucket, error = harness._rebuild_bucket_from_module_text(
            source_name="test-alloc-testing",
            module_text=module_text,
            required_func="test_malloc_free",
            previous_bucket={},
        )

        self.assertEqual(error, "")
        self.assertIn("alloc_test_malloc", bucket["extra"])
        self.assertIn("alloc_test_free", bucket["extra"])
        self.assertNotIn("use crate::alloc_testing::{\n};", bucket["extra"])

    def test_rebuild_bucket_reports_missing_required_function(self):
        bucket, error = _fallback_coordinator()._rebuild_bucket_from_module_text(
            source_name="src/foo",
            module_text="pub fn other() {}\n",
            required_func="target",
        )

        self.assertEqual(bucket, {})
        self.assertIn("缺少目标函数 target", error)

    def test_runtime_repair_attempts_use_isolated_cc_mini_agents(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = _fallback_coordinator()
            harness.test_runtime_check_enabled = True
            harness.test_runtime_check_mode = "function"
            harness.test_runtime_check_timeout_seconds = 30
            harness.test_runtime_swe_max_attempts = 2
            harness.enable_cc_mini_agent_fallback = True
            harness.verifier = SimpleNamespace(base_tmp_dir=tmp, dependency_overrides={})
            harness._is_test_source = lambda source_name: source_name.startswith("test-")
            harness._ensure_swe_runtime_debug_tool = lambda agent: None
            harness.export_archive_to_project = lambda **kwargs: (True, "")

            def export_tests_to_project(**kwargs):
                output_project_path = Path(kwargs["output_project_path"])
                tests_dir = output_project_path / "tests"
                tests_dir.mkdir(parents=True, exist_ok=True)
                (tests_dir / "test_foo.rs").write_text("pub fn test_foo() {}\n", encoding="utf-8")
                return True, ""

            harness.export_archive_tests_to_project = export_tests_to_project
            agents = []

            def new_agent(workspace):
                agent = _RuntimeFailingAgent(f"agent-{len(agents) + 1}")
                agents.append(agent)
                return agent

            harness._get_cc_mini_agent_instance = new_agent
            proc = SimpleNamespace(returncode=101, stderr="failed", stdout="")
            archive = {
                "foo": {"foo": "pub fn foo() {}\n"},
                "test-foo": {"test_foo": "pub fn test_foo() {}\n"},
            }

            with mock.patch("pipeline.cc_mini_fallback.subprocess.run", return_value=proc):
                ok, detail, candidate = harness._run_test_module_with_optional_swe_repair(
                    test_source_name="test-foo",
                    source_name="test-foo",
                    func_name="test_foo",
                    include_files=["foo", "test-foo"],
                    archive=archive,
                )

            self.assertFalse(ok)
            self.assertIsNone(candidate)
            self.assertIn("runtime cargo test failed after CC-MINI attempts", detail)
            self.assertEqual([agent.name for agent in agents], ["agent-1", "agent-2"])

    def test_runtime_roundtrip_archive_rejects_failed_cargo_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = _fallback_coordinator()
            harness.verifier = SimpleNamespace(base_tmp_dir=tmp, dependency_overrides={})
            harness.test_runtime_check_timeout_seconds = 30
            harness.export_archive_to_project = mock.Mock(return_value=(True, "src exported"))
            harness.export_archive_tests_to_project = mock.Mock(return_value=(True, "tests exported"))
            proc = SimpleNamespace(returncode=101, stderr="error[E0432]: unresolved import", stdout="")

            with mock.patch("pipeline.cc_mini_fallback.subprocess.run", return_value=proc):
                ok, detail = harness._verify_runtime_roundtrip_archive(
                    archive={
                        "foo": {"foo": "pub fn foo() {}\n"},
                        "test-foo": {"test_foo": "pub fn test_foo() {}\n"},
                    },
                    export_sources=["foo"],
                    test_sources=["test-foo"],
                    crate_name="verify_project",
                    label="test-foo:test_foo",
                )

            self.assertFalse(ok)
            self.assertIn("round-trip cargo test failed", detail)
            self.assertEqual(current_pipeline_stats().roundtrip_verify_failure_count, 1)

    def test_source_complete_mode_defers_function_runtime_check(self):
        harness = _fallback_coordinator()
        harness.test_runtime_check_enabled = True
        harness.test_runtime_check_mode = "source_complete"
        harness._is_test_source = lambda source_name: source_name.startswith("test-")
        harness.export_archive_to_project = mock.Mock()
        archive = {
            "foo": {"foo": "pub fn foo() {}\n"},
            "test-foo": {"test_foo": "pub fn test_foo() {}\n"},
        }

        ok, detail, candidate = harness._run_test_module_with_optional_swe_repair(
            test_source_name="test-foo",
            source_name="test-foo",
            func_name="test_foo",
            include_files=["foo", "test-foo"],
            archive=archive,
        )

        self.assertTrue(ok)
        self.assertIsNone(candidate)
        self.assertIn("deferred", detail)
        harness.export_archive_to_project.assert_not_called()


if __name__ == "__main__":
    unittest.main()
