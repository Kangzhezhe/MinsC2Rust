import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.run_report import CommandResult, generate_translation_report


class RunReportTest(unittest.TestCase):
    def _write_sample_output(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "checkpoint.json").write_text(
            json.dumps(
                {
                    "total_retry_count": 2,
                    "total_regenerate_count": 1,
                    "total_error_count": 0,
                    "ast_split_success_count": 7,
                    "ast_split_failure_count": 1,
                    "ast_fallback_used_count": 1,
                    "roundtrip_verify_success_count": 3,
                    "roundtrip_verify_failure_count": 0,
                }
            ),
            encoding="utf-8",
        )
        (output_dir / "results.json").write_text(
            json.dumps({"arraylist": {"arraylist_new": "pub fn arraylist_new() {}\n"}}),
            encoding="utf-8",
        )
        (output_dir / "pending_accepted.json").write_text("{}", encoding="utf-8")
        (output_dir / "all_error_funcs_content.json").write_text("{}", encoding="utf-8")
        (output_dir / "runtime_status.json").write_text(
            json.dumps(
                {
                    "arraylist": {
                        "arraylist_new": {
                            "status": "runtime_passed",
                            "elapsed_seconds": 1.5,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        (output_dir / "source_runtime_status.json").write_text(
            json.dumps({"arraylist": {"status": "runtime_ok", "failed_functions": 0}}),
            encoding="utf-8",
        )
        (output_dir / "repair_records.json").write_text(
            json.dumps(
                {
                    "test-arraylist": [
                        {
                            "attempt": 1,
                            "trigger": "runtime_repair",
                            "failure_kind": "cargo_test",
                            "modified_files": ["test-arraylist"],
                            "acceptance_command": "runtime_test_runner",
                            "returncode": 0,
                            "backfill_status": "merged",
                            "summary": "runtime cargo test passed via CC-MINI",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (output_dir / "cost.csv").write_text(
            "scope,source_name,elapsed_seconds,input_tokens,output_tokens,total_tokens\n"
            "global,ALL,12.5,100,200,300\n"
            "module,arraylist,3.0,10,20,30\n",
            encoding="utf-8",
        )
        (output_dir / "app.log").write_text(
            "[RUNTIME-CHECK-MODE] mode=source_complete enabled=1\n"
            "[PASS] arraylist:arraylist_new verify_invocations=1 elapsed=1.5s "
            "retries=0 regenerations=0 runtime=non-test source\n"
            "[TEST-RUNTIME-CC-MINI-FAIL] test-arraylist:test_x attempt=1/2 detail=failed\n"
            "Total time: 00:00:12, retries=2, regenerations=1, errors=0\n",
            encoding="utf-8",
        )
        (output_dir / "run.log").write_text(
            "Tool error: BashTool.execute() got an unexpected keyword argument 'description'\n"
            "</|DSML|parameter>\n"
            "token sk_test_should_be_redacted user@example.com\n",
            encoding="utf-8",
        )
        verify_project = output_dir / "verify_project"
        verify_project.mkdir()
        (verify_project / "Cargo.toml").write_text("[package]\nname='x'\nversion='0.1.0'\n", encoding="utf-8")

    def test_generate_report_writes_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "Output"
            self._write_sample_output(output_dir)

            def fake_runner(command, cwd, timeout):
                self.assertEqual(command, ["cargo", "test", "--quiet"])
                self.assertEqual(cwd, output_dir / "verify_project")
                return CommandResult(command="cargo test --quiet", returncode=0, stdout="ok", stderr="", elapsed_seconds=0.2)

            report = generate_translation_report(output_dir, verify=True, command_runner=fake_runner)

            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["verification"]["cargo_test"]["returncode"], 0)
            self.assertEqual(report["state"]["result_functions"], 1)
            self.assertEqual(report["state"]["pending_functions"], 0)
            self.assertEqual(report["state"]["error_functions"], 0)
            self.assertEqual(report["state"]["source_runtime_status_counts"], {"runtime_ok": 1})
            self.assertEqual(report["runtime_check"]["mode"], "source_complete")
            self.assertTrue(report["runtime_check"]["enabled"])
            self.assertTrue(report["state"]["reconciliation"]["ok"])
            self.assertEqual(report["repairs"]["total"], 1)
            self.assertEqual(report["quality_guards"]["ast_fallback_used_count"], 1)
            self.assertEqual(report["quality_guards"]["roundtrip_verify_success_count"], 3)
            self.assertEqual(report["log_markers"]["run.log"]["Tool error"], 1)
            self.assertEqual(report["log_markers"]["app.log"]["TEST-RUNTIME-CC-MINI-FAIL"], 1)

            report_json = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
            report_md = (output_dir / "report.md").read_text(encoding="utf-8")
            self.assertEqual(report_json["status"], "passed")
            self.assertIn("# Translation Run Report", report_md)
            self.assertIn("## Quality Guards", report_md)
            self.assertIn("cargo test", report_md)
            self.assertNotIn("sk_test_should_be_redacted", report_md)
            self.assertNotIn("user@example.com", report_md)

    def test_failed_cargo_test_marks_report_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "Output"
            self._write_sample_output(output_dir)

            def fake_runner(command, cwd, timeout):
                return CommandResult(
                    command="cargo test --quiet",
                    returncode=101,
                    stdout="fail",
                    stderr="error: test failed",
                    elapsed_seconds=0.2,
                )

            report = generate_translation_report(output_dir, verify=True, command_runner=fake_runner)

            self.assertEqual(report["status"], "failed")
            self.assertFalse(report["verification"]["cargo_test"]["ok"])
            self.assertIn("error: test failed", report["verification"]["cargo_test"]["stderr_tail"])

    def test_verification_report_filters_cargo_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "Output"
            self._write_sample_output(output_dir)
            stderr = (
                "warning: variable does not need to be mutable\n"
                "  --> tests/test_arraylist.rs:325:9\n"
                "   |\n"
                "325 |     let mut arraylist_ref = value;\n"
                "   |         ----^^^^^^^^^^^^^\n"
                "   |\n"
                "   = note: #[warn(unused_mut)] on by default\n"
                "\n"
            )

            def fake_runner(command, cwd, timeout):
                return CommandResult(
                    command="cargo test --quiet",
                    returncode=0,
                    stdout="ok",
                    stderr=stderr,
                    elapsed_seconds=0.2,
                )

            report = generate_translation_report(output_dir, verify=True, command_runner=fake_runner)

            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["verification"]["cargo_test"]["stderr_tail"], "")
            self.assertNotIn("cargo test stderr tail", (output_dir / "report.md").read_text(encoding="utf-8"))

    def test_failed_verification_report_keeps_errors_after_filtering_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "Output"
            self._write_sample_output(output_dir)
            stderr = (
                "warning: unused variable: `x`\n"
                "  --> tests/test_arraylist.rs:1:1\n"
                "   |\n"
                "   = note: #[warn(unused_variables)] on by default\n"
                "\n"
                "error: test failed, to rerun pass `--test test_arraylist`\n"
            )

            def fake_runner(command, cwd, timeout):
                return CommandResult(
                    command="cargo test --quiet",
                    returncode=101,
                    stdout="fail",
                    stderr=stderr,
                    elapsed_seconds=0.2,
                )

            report = generate_translation_report(output_dir, verify=True, command_runner=fake_runner)

            self.assertEqual(report["status"], "failed")
            self.assertIn("error: test failed", report["verification"]["cargo_test"]["stderr_tail"])
            self.assertNotIn("warning:", report["verification"]["cargo_test"]["stderr_tail"])

    def test_generate_report_reads_new_subdirectory_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "Output"
            self._write_sample_output(output_dir)
            for subdir in ("state", "metrics", "logs"):
                (output_dir / subdir).mkdir(exist_ok=True)
            for name in [
                "pending_accepted.json",
                "runtime_status.json",
                "source_runtime_status.json",
                "repair_records.json",
            ]:
                (output_dir / "state" / name).write_text((output_dir / name).read_text(encoding="utf-8"), encoding="utf-8")
                (output_dir / name).unlink()
            (output_dir / "metrics" / "cost.csv").write_text((output_dir / "cost.csv").read_text(encoding="utf-8"), encoding="utf-8")
            (output_dir / "cost.csv").unlink()
            (output_dir / "logs" / "run.log").write_text((output_dir / "run.log").read_text(encoding="utf-8"), encoding="utf-8")
            (output_dir / "run.log").unlink()

            report = generate_translation_report(output_dir, verify=False)

            self.assertEqual(report["state"]["runtime_status_counts"], {"runtime_passed": 1})
            self.assertEqual(report["repairs"]["total"], 1)
            self.assertEqual(report["cost"]["global"]["total_tokens"], 300)
            self.assertEqual(report["log_markers"]["run.log"]["Tool error"], 1)
            self.assertIn("/state/runtime_status.json", report["artifacts"]["runtime_status.json"])
            self.assertIn("/metrics/cost.csv", report["artifacts"]["cost.csv"])
            self.assertIn("/logs/run.log", report["artifacts"]["run.log"])


if __name__ == "__main__":
    unittest.main()
