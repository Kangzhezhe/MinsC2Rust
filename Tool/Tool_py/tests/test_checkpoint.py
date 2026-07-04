import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.checkpoint import load_checkpoint, save_checkpoint
from pipeline.stats import PipelineStats


class CheckpointCompatibilityTest(unittest.TestCase):
    def test_loads_legacy_arraylist_checkpoint_fixture(self):
        fixture_dir = Path(__file__).resolve().parent / "fixtures" / "legacy_arraylist_checkpoint"

        state = load_checkpoint(fixture_dir)

        self.assertEqual(state.stats.total_retry_count, 23)
        self.assertEqual(state.stats.total_regenerate_count, 0)
        self.assertEqual(state.stats.total_error_count, 2)
        self.assertEqual(
            set(state.results),
            {"alloc-testing", "test-alloc-testing", "arraylist", "compare-int", "test-arraylist"},
        )
        self.assertEqual(
            {source: len(funcs) for source, funcs in state.results.items()},
            {
                "alloc-testing": 11,
                "test-alloc-testing": 6,
                "arraylist": 13,
                "compare-int": 2,
                "test-arraylist": 11,
            },
        )
        self.assertEqual(
            set(state.all_error_funcs_content["test-arraylist"]),
            {"test_arraylist_remove", "test_arraylist_insert"},
        )
        self.assertEqual(state.dependency_overrides, {})

    def test_load_missing_files_returns_empty_legacy_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = load_checkpoint(tmp)

            self.assertEqual(dict(state.results), {})
            self.assertEqual(dict(state.once_retry_count_dict), {})
            self.assertEqual(dict(state.all_error_funcs_content), {})
            self.assertEqual(dict(state.pending_accepted), {})
            self.assertEqual(dict(state.runtime_status), {})
            self.assertEqual(dict(state.source_runtime_status), {})
            self.assertEqual(dict(state.source_runtime_pass_cache), {})
            self.assertEqual(dict(state.repair_records), {})
            self.assertEqual(state.dependency_overrides, {})
            self.assertEqual(state.stats.to_checkpoint_dict(), {
                "total_retry_count": 0,
                "total_regenerate_count": 0,
                "total_error_count": 0,
                "ast_split_success_count": 0,
                "ast_split_failure_count": 0,
                "ast_fallback_used_count": 0,
                "roundtrip_verify_success_count": 0,
                "roundtrip_verify_failure_count": 0,
                "dynamic_dependency_add_count": 0,
            })

            state.results["source"]["func"] = "pub fn func() {}\n"
            self.assertEqual(state.results["source"]["func"], "pub fn func() {}\n")

    def test_load_and_save_keeps_legacy_checkpoint_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            (output_dir / "results.json").write_text(
                json.dumps({"arraylist": {"extra": "pub type Size = usize;\n", "new": "pub fn new() {}\n"}}),
                encoding="utf-8",
            )
            (output_dir / "once_retry_count_dict.json").write_text(
                json.dumps({"arraylist": {"new": 2}}),
                encoding="utf-8",
            )
            (output_dir / "all_error_funcs_content.json").write_text(
                json.dumps({"arraylist": {"push": "// failed"}}),
                encoding="utf-8",
            )
            (output_dir / "checkpoint.json").write_text(
                json.dumps(
                    {
                        "total_retry_count": 3,
                        "total_regenerate_count": 4,
                        "total_error_count": 5,
                    }
                ),
                encoding="utf-8",
            )
            (output_dir / "dependency_overrides.json").write_text(
                json.dumps({"libc": "\"0.2\"", "regex": "\"1\""}),
                encoding="utf-8",
            )

            state = load_checkpoint(output_dir)
            self.assertEqual(state.results["arraylist"]["new"], "pub fn new() {}\n")
            self.assertEqual(state.once_retry_count_dict["arraylist"]["new"], 2)
            self.assertEqual(state.all_error_funcs_content["arraylist"]["push"], "// failed")
            self.assertEqual(state.stats.total_retry_count, 3)
            self.assertEqual(state.stats.total_regenerate_count, 4)
            self.assertEqual(state.stats.total_error_count, 5)
            self.assertEqual(state.dependency_overrides, {"regex": "\"1\""})

            save_checkpoint(
                state.results,
                state.once_retry_count_dict,
                state.all_error_funcs_content,
                output_dir,
                stats=PipelineStats(
                    total_retry_count=6,
                    total_regenerate_count=7,
                    total_error_count=8,
                    ast_split_success_count=9,
                    ast_split_failure_count=10,
                    ast_fallback_used_count=11,
                    roundtrip_verify_success_count=12,
                    roundtrip_verify_failure_count=13,
                    dynamic_dependency_add_count=14,
                ),
                dependency_overrides=state.dependency_overrides,
            )

            saved_checkpoint = json.loads((output_dir / "checkpoint.json").read_text(encoding="utf-8"))
            self.assertEqual(
                saved_checkpoint,
                {
                    "total_retry_count": 6,
                    "total_regenerate_count": 7,
                    "total_error_count": 1,
                    "ast_split_success_count": 9,
                    "ast_split_failure_count": 10,
                    "ast_fallback_used_count": 11,
                    "roundtrip_verify_success_count": 12,
                    "roundtrip_verify_failure_count": 13,
                    "dynamic_dependency_add_count": 14,
                },
            )
            self.assertIn("arraylist", json.loads((output_dir / "results.json").read_text(encoding="utf-8")))

    def test_save_checkpoint_writes_all_legacy_files_even_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            save_checkpoint({}, {}, {}, output_dir)

            expected_top_level = {
                "results.json",
                "all_error_funcs_content.json",
                "checkpoint.json",
                "state",
                "metrics",
                "logs",
            }
            self.assertEqual(
                {path.name for path in output_dir.iterdir()},
                expected_top_level,
            )
            expected_state_files = {
                "once_retry_count_dict.json",
                "dependency_overrides.json",
                "pending_accepted.json",
                "runtime_status.json",
                "source_runtime_status.json",
                "source_runtime_pass_cache.json",
                "repair_records.json",
            }
            self.assertEqual(
                {path.name for path in (output_dir / "state").iterdir()},
                expected_state_files,
            )
            self.assertEqual(
                json.loads((output_dir / "checkpoint.json").read_text(encoding="utf-8")),
                {
                    "total_retry_count": 0,
                    "total_regenerate_count": 0,
                    "total_error_count": 0,
                    "ast_split_success_count": 0,
                    "ast_split_failure_count": 0,
                    "ast_fallback_used_count": 0,
                    "roundtrip_verify_success_count": 0,
                    "roundtrip_verify_failure_count": 0,
                    "dynamic_dependency_add_count": 0,
                },
            )
            self.assertEqual(json.loads((output_dir / "state" / "pending_accepted.json").read_text(encoding="utf-8")), {})
            self.assertEqual(json.loads((output_dir / "state" / "runtime_status.json").read_text(encoding="utf-8")), {})
            self.assertEqual(json.loads((output_dir / "state" / "source_runtime_status.json").read_text(encoding="utf-8")), {})
            self.assertEqual(json.loads((output_dir / "state" / "source_runtime_pass_cache.json").read_text(encoding="utf-8")), {})
            self.assertEqual(json.loads((output_dir / "state" / "repair_records.json").read_text(encoding="utf-8")), {})

    def test_save_checkpoint_removes_error_records_for_valid_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            results = {
                "src": {
                    "ok": "pub fn ok() {}\n",
                    "bad": "pub fn bad() {\n",
                }
            }
            errors = {
                "src": {
                    "ok": "// stale blocked failure",
                    "bad": "// real failure",
                }
            }

            save_checkpoint(results, {}, errors, output_dir)

            saved_errors = json.loads(
                (output_dir / "all_error_funcs_content.json").read_text(encoding="utf-8")
            )
            saved_checkpoint = json.loads(
                (output_dir / "checkpoint.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved_errors, {"src": {"bad": "// real failure"}})
            self.assertEqual(saved_checkpoint["total_error_count"], 1)

    def test_load_and_save_sidecar_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            pending = {"src_a": {"foo": "pub fn foo() {}\n"}}
            runtime_status = {
                "src_a": {
                    "foo": {
                        "status": "runtime_failed",
                        "test_source": "test-src_a",
                        "message": "cargo test failed",
                    }
                }
            }
            source_runtime_status = {"src_a": {"status": "has_runtime_failures", "failed": 1}}
            source_runtime_pass_cache = {
                "version": 2,
                "passes": {
                    "sha256:abc": {
                        "fingerprint": "sha256:abc",
                        "command": "cargo test --quiet",
                        "mode": "source_complete",
                        "passed_by_source": "test-src_a",
                    }
                },
            }
            repair_records = {
                "src_a": [
                    {
                        "attempt": 1,
                        "trigger": "runtime_failure",
                        "failure_kind": "cargo_test",
                        "modified_files": ["src_a"],
                        "acceptance_command": "cargo test --quiet",
                        "returncode": 0,
                        "backfill_status": "merged",
                        "archive_hash_before": "before",
                        "archive_hash_after": "after",
                        "summary": "cc-mini repaired src_a",
                    }
                ]
            }

            save_checkpoint(
                {},
                {},
                {},
                output_dir,
                pending_accepted=pending,
                runtime_status=runtime_status,
                source_runtime_status=source_runtime_status,
                source_runtime_pass_cache=source_runtime_pass_cache,
                repair_records=repair_records,
            )

            state = load_checkpoint(output_dir)
            self.assertEqual(state.pending_accepted["src_a"]["foo"], "pub fn foo() {}\n")
            self.assertEqual(state.runtime_status["src_a"]["foo"]["status"], "runtime_failed")
            self.assertEqual(state.source_runtime_status["src_a"]["failed"], 1)
            self.assertEqual(
                state.source_runtime_pass_cache["passes"]["sha256:abc"]["fingerprint"],
                "sha256:abc",
            )
            self.assertEqual(state.repair_records["src_a"][0]["backfill_status"], "merged")


if __name__ == "__main__":
    unittest.main()
