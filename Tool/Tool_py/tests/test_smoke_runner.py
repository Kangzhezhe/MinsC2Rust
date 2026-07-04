import configparser
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOL_PY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_PY_ROOT))

from smoke_runner import (
    CARGO_EXPORT_VALIDATION_COMMANDS,
    compare_smoke_outputs,
    run_reference_aligned_arraylist_smoke,
    write_reference_aligned_arraylist_config,
)
from parse_config import read_config


class SmokeRunnerTest(unittest.TestCase):
    def test_reference_aligned_config_uses_fixed_output_and_includes_alloc_tests(self):
        cfg = configparser.ConfigParser()
        cfg["Paths"] = {
            "src_dir": "../../benchmarks/arraylist/src",
            "test_dir": "../../benchmarks/arraylist/test",
            "tmp_dir": "../../Output/arraylist/tmp",
            "output_dir": "../../Output/arraylist/Output",
            "compile_commands_path": "../../benchmarks/arraylist/build/compile_commands.json",
        }
        cfg["ExcludeFiles"] = {
            "files": "alloc-testing, test-alloc-testing, framework, utf8-decoder",
        }
        cfg["Settings"] = {"model": "openai"}

        with tempfile.TemporaryDirectory() as tmp:
            base_path = Path(tmp) / "base.ini"
            derived_path = Path(tmp) / "derived.ini"
            output_root = Path(tmp) / "arraylist_smoke_current"
            with base_path.open("w", encoding="utf-8") as f:
                cfg.write(f)

            result = write_reference_aligned_arraylist_config(
                base_config_path=base_path,
                destination_config_path=derived_path,
                output_root=output_root,
            )

            derived = configparser.ConfigParser()
            derived.read(derived_path)
            self.assertEqual(result.tmp_dir, output_root / "tmp")
            self.assertEqual(result.output_dir, output_root / "Output")
            self.assertEqual(derived["Paths"]["tmp_dir"], str(output_root / "tmp"))
            self.assertEqual(derived["Paths"]["output_dir"], str(output_root / "Output"))
            self.assertEqual(
                [item.strip() for item in derived["ExcludeFiles"]["files"].split(",") if item.strip()],
                ["framework", "utf8-decoder"],
            )

    def test_reference_aligned_config_resolves_inherited_base_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parent_path = root / "parent.ini"
            child_path = root / "child.ini"
            derived_path = root / "derived.ini"
            output_root = root / "arraylist_smoke_current"

            parent = configparser.ConfigParser()
            parent["Paths"] = {
                "src_dir": "parent-src",
                "test_dir": "parent-test",
                "tmp_dir": "parent-tmp",
                "output_dir": "parent-out",
                "compile_commands_path": "parent-compile-commands.json",
            }
            parent["Params"] = {"cc_mini_max_call_attempts": "3"}
            parent["ExcludeFiles"] = {
                "files": "alloc-testing, test-alloc-testing, framework",
            }
            with parent_path.open("w", encoding="utf-8") as f:
                parent.write(f)

            child_path.write_text(
                """
[Config]
inherits = parent.ini

[Paths]
src_dir = child-src
""".lstrip(),
                encoding="utf-8",
            )

            write_reference_aligned_arraylist_config(
                base_config_path=child_path,
                destination_config_path=derived_path,
                output_root=output_root,
            )

            derived = configparser.ConfigParser()
            derived.read(derived_path)
            self.assertNotIn("Config", derived)
            resolved = read_config(str(derived_path))
            self.assertEqual(resolved["Paths"]["src_dir"], str((child_path.parent / "child-src").resolve()))
            self.assertEqual(resolved["Paths"]["test_dir"], str((parent_path.parent / "parent-test").resolve()))
            self.assertEqual(derived["Params"]["cc_mini_max_call_attempts"], "3")
            self.assertEqual(derived["ExcludeFiles"]["files"], "framework")

    def test_compare_smoke_outputs_accepts_matching_sources_despite_test_function_count_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "current" / "Output"
            reference = root / "reference" / "Output"
            current.mkdir(parents=True)
            reference.mkdir(parents=True)

            self._write_smoke_output(
                current,
                checkpoint={"total_retry_count": 22, "total_regenerate_count": 0, "total_error_count": 0},
                results={
                    "alloc-testing": 11,
                    "test-alloc-testing": 6,
                    "arraylist": 13,
                    "compare-int": 2,
                    "test-arraylist": 13,
                },
                compile_overall=("100.00%", "45", "45", "100.00%", "31", "31"),
                once_overall=("72.34%", "34", "47"),
            )
            self._write_smoke_output(
                reference,
                checkpoint={"total_retry_count": 23, "total_regenerate_count": 0, "total_error_count": 2},
                results={
                    "alloc-testing": 11,
                    "test-alloc-testing": 6,
                    "arraylist": 13,
                    "compare-int": 2,
                    "test-arraylist": 11,
                },
                compile_overall=("97.78%", "44", "45", "100.00%", "31", "31"),
                once_overall=("71.74%", "33", "46"),
            )

            comparison = compare_smoke_outputs(current, reference)

            self.assertTrue(comparison.ok, comparison.issues)
            self.assertEqual(comparison.current.result_sources, comparison.reference.result_sources)
            self.assertEqual(
                comparison.result_count_deltas,
                {"test-arraylist": (13, 11)},
            )
            self.assertEqual(
                CARGO_EXPORT_VALIDATION_COMMANDS,
                (
                    ("cargo", "check", "--quiet"),
                    ("cargo", "build", "--quiet"),
                    ("cargo", "test", "--quiet", "--no-run"),
                    ("cargo", "test", "--quiet"),
                ),
            )

    def test_compare_smoke_outputs_reads_metrics_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "current" / "Output"
            reference = root / "reference" / "Output"
            current.mkdir(parents=True)
            reference.mkdir(parents=True)

            kwargs = {
                "checkpoint": {"total_retry_count": 0, "total_regenerate_count": 0, "total_error_count": 0},
                "results": {"arraylist": 1},
                "compile_overall": ("100.00%", "1", "1", "100.00%", "1", "1"),
                "once_overall": ("100.00%", "1", "1"),
            }
            self._write_smoke_output(current, use_metrics_dir=True, **kwargs)
            self._write_smoke_output(reference, **kwargs)

            comparison = compare_smoke_outputs(current, reference)

            self.assertTrue(comparison.ok, comparison.issues)
            self.assertEqual(comparison.current.compile_overall_with_test, 100.0)
            self.assertEqual(comparison.current.once_overall, 100.0)

    def test_compare_smoke_outputs_uses_checkpoint_error_count_without_double_counting_error_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "current" / "Output"
            reference = root / "reference" / "Output"
            current.mkdir(parents=True)
            reference.mkdir(parents=True)

            self._write_smoke_output(
                current,
                checkpoint={"total_retry_count": 0, "total_regenerate_count": 0, "total_error_count": 0},
                results={"arraylist": 1},
                compile_overall=("100.00%", "1", "1", "100.00%", "1", "1"),
                once_overall=("100.00%", "1", "1"),
            )
            self._write_smoke_output(
                reference,
                checkpoint={"total_retry_count": 0, "total_regenerate_count": 0, "total_error_count": 2},
                results={"arraylist": 1},
                compile_overall=("100.00%", "1", "1", "100.00%", "1", "1"),
                once_overall=("100.00%", "1", "1"),
                errors={"arraylist": {"failed_a": "body", "failed_b": "body"}},
            )

            comparison = compare_smoke_outputs(current, reference)

            self.assertTrue(comparison.ok, comparison.issues)
            self.assertEqual(comparison.reference.error_count, 2)

    def test_reference_aligned_smoke_run_orchestrates_pipeline_and_cargo_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tool_py_root = root / "Tool_py"
            (tool_py_root / "src").mkdir(parents=True)
            base_config_path = root / "base.ini"
            derived_config_path = root / "derived.ini"
            output_root = root / "arraylist_smoke_current"
            reference_output_dir = root / "reference" / "Output"
            reference_output_dir.mkdir(parents=True)
            self._write_base_config(base_config_path)
            self._write_smoke_output(
                reference_output_dir,
                checkpoint={"total_retry_count": 23, "total_regenerate_count": 0, "total_error_count": 2},
                results={"arraylist": 1},
                compile_overall=("97.00%", "97", "100", "100.00%", "100", "100"),
                once_overall=("71.00%", "71", "100"),
                errors={"arraylist": {"failed": "body"}},
            )

            commands = []

            def fake_runner(command, *, cwd, text, capture_output, check):
                commands.append((tuple(str(part) for part in command), Path(cwd)))
                if str(command[1]).endswith("src/main.py"):
                    current_output_dir = output_root / "Output"
                    current_output_dir.mkdir(parents=True)
                    self._write_smoke_output(
                        current_output_dir,
                        checkpoint={"total_retry_count": 1, "total_regenerate_count": 0, "total_error_count": 0},
                        results={"arraylist": 1},
                        compile_overall=("100.00%", "1", "1", "100.00%", "1", "1"),
                        once_overall=("100.00%", "1", "1"),
                    )
                    (current_output_dir / "verify_project").mkdir()
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            result = run_reference_aligned_arraylist_smoke(
                tool_py_root=tool_py_root,
                base_config_path=base_config_path,
                derived_config_path=derived_config_path,
                output_root=output_root,
                reference_output_dir=reference_output_dir,
                python_executable="/fake/python",
                runner=fake_runner,
            )

            self.assertTrue(result.ok, result.issues)
            self.assertTrue(derived_config_path.exists())
            self.assertTrue(result.comparison.ok)
            self.assertEqual(len(result.cargo_results), len(CARGO_EXPORT_VALIDATION_COMMANDS))
            self.assertEqual(
                [command for command, _cwd in commands],
                [
                    ("/fake/python", str(tool_py_root / "makejson.py"), str(derived_config_path)),
                    ("/fake/python", str(tool_py_root / "src" / "main.py"), str(derived_config_path)),
                    *CARGO_EXPORT_VALIDATION_COMMANDS,
                ],
            )

    def test_reference_aligned_smoke_run_resolves_relative_tool_py_root_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_config_path = root / "base.ini"
            derived_config_path = root / "derived.ini"
            output_root = root / "arraylist_smoke_current"
            reference_output_dir = root / "reference" / "Output"
            reference_output_dir.mkdir(parents=True)
            self._write_base_config(base_config_path)
            self._write_smoke_output(
                reference_output_dir,
                checkpoint={"total_retry_count": 0, "total_regenerate_count": 0, "total_error_count": 0},
                results={"arraylist": 1},
                compile_overall=("100.00%", "1", "1", "100.00%", "1", "1"),
                once_overall=("100.00%", "1", "1"),
            )
            commands = []

            def fake_runner(command, *, cwd, text, capture_output, check):
                commands.append((tuple(str(part) for part in command), Path(cwd)))
                if str(command[1]).endswith("src/main.py"):
                    current_output_dir = output_root / "Output"
                    current_output_dir.mkdir(parents=True)
                    self._write_smoke_output(
                        current_output_dir,
                        checkpoint={"total_retry_count": 0, "total_regenerate_count": 0, "total_error_count": 0},
                        results={"arraylist": 1},
                        compile_overall=("100.00%", "1", "1", "100.00%", "1", "1"),
                        once_overall=("100.00%", "1", "1"),
                    )
                    (current_output_dir / "verify_project").mkdir()
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            result = run_reference_aligned_arraylist_smoke(
                tool_py_root=Path("Tool/Tool_py"),
                base_config_path=base_config_path,
                derived_config_path=derived_config_path,
                output_root=output_root,
                reference_output_dir=reference_output_dir,
                python_executable="/fake/python",
                runner=fake_runner,
            )

            self.assertTrue(result.ok, result.issues)
            self.assertEqual(commands[0][0][1], str(Path("Tool/Tool_py/makejson.py").resolve()))
            self.assertEqual(commands[1][0][1], str(Path("Tool/Tool_py/src/main.py").resolve()))
            self.assertEqual(commands[0][1], Path("Tool/Tool_py").resolve())

    def test_reference_aligned_smoke_run_stops_when_makejson_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tool_py_root = root / "Tool_py"
            tool_py_root.mkdir()
            base_config_path = root / "base.ini"
            derived_config_path = root / "derived.ini"
            output_root = root / "arraylist_smoke_current"
            reference_output_dir = root / "reference" / "Output"
            reference_output_dir.mkdir(parents=True)
            self._write_base_config(base_config_path)

            commands = []

            def failing_runner(command, *, cwd, text, capture_output, check):
                commands.append(tuple(str(part) for part in command))
                return subprocess.CompletedProcess(command, 17, stdout="", stderr="makejson failed")

            result = run_reference_aligned_arraylist_smoke(
                tool_py_root=tool_py_root,
                base_config_path=base_config_path,
                derived_config_path=derived_config_path,
                output_root=output_root,
                reference_output_dir=reference_output_dir,
                python_executable="/fake/python",
                runner=failing_runner,
            )

            self.assertFalse(result.ok)
            self.assertIn("makejson failed", result.issues[0])
            self.assertEqual(len(commands), 1)
            self.assertIsNone(result.comparison)
            self.assertEqual(result.cargo_results, ())

    def test_reference_aligned_smoke_run_can_clean_stale_output_before_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tool_py_root = root / "Tool_py"
            (tool_py_root / "src").mkdir(parents=True)
            base_config_path = root / "base.ini"
            derived_config_path = root / "derived.ini"
            output_root = root / "arraylist_smoke_current"
            stale_file = output_root / "Output" / "stale.txt"
            stale_file.parent.mkdir(parents=True)
            stale_file.write_text("old run", encoding="utf-8")
            reference_output_dir = root / "reference" / "Output"
            reference_output_dir.mkdir(parents=True)
            self._write_base_config(base_config_path)
            self._write_smoke_output(
                reference_output_dir,
                checkpoint={"total_retry_count": 0, "total_regenerate_count": 0, "total_error_count": 0},
                results={"arraylist": 1},
                compile_overall=("100.00%", "1", "1", "100.00%", "1", "1"),
                once_overall=("100.00%", "1", "1"),
            )

            def fake_runner(command, *, cwd, text, capture_output, check):
                if str(command[1]).endswith("src/main.py"):
                    self.assertFalse(stale_file.exists())
                    current_output_dir = output_root / "Output"
                    current_output_dir.mkdir(parents=True)
                    self._write_smoke_output(
                        current_output_dir,
                        checkpoint={"total_retry_count": 0, "total_regenerate_count": 0, "total_error_count": 0},
                        results={"arraylist": 1},
                        compile_overall=("100.00%", "1", "1", "100.00%", "1", "1"),
                        once_overall=("100.00%", "1", "1"),
                    )
                    (current_output_dir / "verify_project").mkdir()
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            result = run_reference_aligned_arraylist_smoke(
                tool_py_root=tool_py_root,
                base_config_path=base_config_path,
                derived_config_path=derived_config_path,
                output_root=output_root,
                reference_output_dir=reference_output_dir,
                python_executable="/fake/python",
                runner=fake_runner,
                clean_output=True,
            )

            self.assertTrue(result.ok, result.issues)
            self.assertFalse(stale_file.exists())

    def _write_base_config(self, path):
        cfg = configparser.ConfigParser()
        cfg["Paths"] = {
            "src_dir": "../../benchmarks/arraylist/src",
            "test_dir": "../../benchmarks/arraylist/test",
            "tmp_dir": "../../Output/arraylist/tmp",
            "output_dir": "../../Output/arraylist/Output",
            "compile_commands_path": "../../benchmarks/arraylist/build/compile_commands.json",
        }
        cfg["ExcludeFiles"] = {
            "files": "alloc-testing, test-alloc-testing, framework, utf8-decoder",
        }
        cfg["Settings"] = {"model": "openai"}
        with path.open("w", encoding="utf-8") as f:
            cfg.write(f)

    def _write_smoke_output(
        self,
        output_dir,
        *,
        checkpoint,
        results,
        compile_overall,
        once_overall,
        errors=None,
        use_metrics_dir=False,
    ):
        (output_dir / "checkpoint.json").write_text(json.dumps(checkpoint), encoding="utf-8")
        (output_dir / "all_error_funcs_content.json").write_text(json.dumps(errors or {}), encoding="utf-8")
        (output_dir / "results.json").write_text(
            json.dumps({source: {f"func_{i}": "pub fn f() {}" for i in range(count)} for source, count in results.items()}),
            encoding="utf-8",
        )
        metrics_dir = output_dir / "metrics" if use_metrics_dir else output_dir
        metrics_dir.mkdir(parents=True, exist_ok=True)
        (metrics_dir / "compile_pass_rate.csv").write_text(
            "\n".join(
                [
                    "Source,Pass Rate (with test),Pass count (with test),Total count (with test),Pass Rate (without test),Pass count (without test),Total count (without test)",
                    f"Overall,{','.join(compile_overall)}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (metrics_dir / "once_pass_rates.csv").write_text(
            "\n".join(
                [
                    "Source,Pass Rate,Pass Count,Total Count",
                    f"Overall,{','.join(once_overall)}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
