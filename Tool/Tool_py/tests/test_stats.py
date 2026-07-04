import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.stats import (
    PipelineStats,
    apply_pipeline_stats,
    current_pipeline_stats,
    increment_dynamic_dependency_add_count,
    increment_roundtrip_verify_failure_count,
    increment_roundtrip_verify_success_count,
    increment_error_count,
    increment_regenerate_count,
    increment_retry_count,
    record_ast_split_result,
    set_error_count,
)


class PipelineStatsRuntimeTest(unittest.TestCase):
    def setUp(self):
        apply_pipeline_stats(PipelineStats())

    def tearDown(self):
        apply_pipeline_stats(PipelineStats())

    def test_runtime_stats_round_trip_and_increment(self):
        apply_pipeline_stats(
            PipelineStats(
                total_retry_count=2,
                total_regenerate_count=3,
                total_error_count=4,
                ast_split_success_count=5,
                ast_split_failure_count=6,
                ast_fallback_used_count=7,
                roundtrip_verify_success_count=8,
                roundtrip_verify_failure_count=9,
                dynamic_dependency_add_count=10,
            )
        )

        increment_retry_count()
        increment_regenerate_count(2)
        increment_error_count(3)
        record_ast_split_result(ast_ok=True)
        record_ast_split_result(ast_ok=False, fallback_used=True)
        increment_roundtrip_verify_success_count()
        increment_roundtrip_verify_failure_count(2)
        increment_dynamic_dependency_add_count(3)
        stats = current_pipeline_stats()

        self.assertEqual(stats.total_retry_count, 3)
        self.assertEqual(stats.total_regenerate_count, 5)
        self.assertEqual(stats.total_error_count, 7)
        self.assertEqual(stats.ast_split_success_count, 6)
        self.assertEqual(stats.ast_split_failure_count, 7)
        self.assertEqual(stats.ast_fallback_used_count, 8)
        self.assertEqual(stats.roundtrip_verify_success_count, 9)
        self.assertEqual(stats.roundtrip_verify_failure_count, 11)
        self.assertEqual(stats.dynamic_dependency_add_count, 13)
        self.assertEqual(
            stats.to_checkpoint_dict(),
            {
                "total_retry_count": 3,
                "total_regenerate_count": 5,
                "total_error_count": 7,
                "ast_split_success_count": 6,
                "ast_split_failure_count": 7,
                "ast_fallback_used_count": 8,
                "roundtrip_verify_success_count": 9,
                "roundtrip_verify_failure_count": 11,
                "dynamic_dependency_add_count": 13,
            },
        )

    def test_current_pipeline_stats_returns_snapshot(self):
        snapshot = current_pipeline_stats()
        snapshot.total_error_count = 99

        self.assertEqual(current_pipeline_stats().total_error_count, 0)

    def test_set_error_count_reconciles_runtime_counter(self):
        increment_error_count(5)

        set_error_count(2)

        self.assertEqual(current_pipeline_stats().total_error_count, 2)


if __name__ == "__main__":
    unittest.main()
