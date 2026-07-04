"""Small value object for pipeline counters stored in checkpoints."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class PipelineStats:
    """Counters that used to live as module globals in `main.py`."""

    total_retry_count: int = 0
    total_regenerate_count: int = 0
    total_error_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    ast_split_success_count: int = 0
    ast_split_failure_count: int = 0
    ast_fallback_used_count: int = 0
    roundtrip_verify_success_count: int = 0
    roundtrip_verify_failure_count: int = 0
    dynamic_dependency_add_count: int = 0

    @classmethod
    def from_checkpoint(cls, checkpoint: Dict[str, Any]) -> "PipelineStats":
        checkpoint = checkpoint or {}
        return cls(
            total_retry_count=int(checkpoint.get("total_retry_count", 0) or 0),
            total_regenerate_count=int(checkpoint.get("total_regenerate_count", 0) or 0),
            total_error_count=int(checkpoint.get("total_error_count", 0) or 0),
            ast_split_success_count=int(checkpoint.get("ast_split_success_count", 0) or 0),
            ast_split_failure_count=int(checkpoint.get("ast_split_failure_count", 0) or 0),
            ast_fallback_used_count=int(checkpoint.get("ast_fallback_used_count", 0) or 0),
            roundtrip_verify_success_count=int(checkpoint.get("roundtrip_verify_success_count", 0) or 0),
            roundtrip_verify_failure_count=int(checkpoint.get("roundtrip_verify_failure_count", 0) or 0),
            dynamic_dependency_add_count=int(checkpoint.get("dynamic_dependency_add_count", 0) or 0),
        )

    def to_checkpoint_dict(self) -> Dict[str, int]:
        return {
            "total_retry_count": int(self.total_retry_count),
            "total_regenerate_count": int(self.total_regenerate_count),
            "total_error_count": int(self.total_error_count),
            "ast_split_success_count": int(self.ast_split_success_count),
            "ast_split_failure_count": int(self.ast_split_failure_count),
            "ast_fallback_used_count": int(self.ast_fallback_used_count),
            "roundtrip_verify_success_count": int(self.roundtrip_verify_success_count),
            "roundtrip_verify_failure_count": int(self.roundtrip_verify_failure_count),
            "dynamic_dependency_add_count": int(self.dynamic_dependency_add_count),
        }


_runtime_stats = PipelineStats()


def current_pipeline_stats() -> PipelineStats:
    """Return a snapshot of counters used by legacy checkpoint files."""
    return PipelineStats(
        total_retry_count=_runtime_stats.total_retry_count,
        total_regenerate_count=_runtime_stats.total_regenerate_count,
        total_error_count=_runtime_stats.total_error_count,
        total_input_tokens=_runtime_stats.total_input_tokens,
        total_output_tokens=_runtime_stats.total_output_tokens,
        total_tokens=_runtime_stats.total_tokens,
        ast_split_success_count=_runtime_stats.ast_split_success_count,
        ast_split_failure_count=_runtime_stats.ast_split_failure_count,
        ast_fallback_used_count=_runtime_stats.ast_fallback_used_count,
        roundtrip_verify_success_count=_runtime_stats.roundtrip_verify_success_count,
        roundtrip_verify_failure_count=_runtime_stats.roundtrip_verify_failure_count,
        dynamic_dependency_add_count=_runtime_stats.dynamic_dependency_add_count,
    )


def apply_pipeline_stats(stats: PipelineStats) -> None:
    """Replace runtime counters from a loaded checkpoint."""
    _runtime_stats.total_retry_count = int(getattr(stats, "total_retry_count", 0) or 0)
    _runtime_stats.total_regenerate_count = int(getattr(stats, "total_regenerate_count", 0) or 0)
    _runtime_stats.total_error_count = int(getattr(stats, "total_error_count", 0) or 0)
    _runtime_stats.total_input_tokens = int(getattr(stats, "total_input_tokens", 0) or 0)
    _runtime_stats.total_output_tokens = int(getattr(stats, "total_output_tokens", 0) or 0)
    _runtime_stats.total_tokens = int(getattr(stats, "total_tokens", 0) or 0)
    _runtime_stats.ast_split_success_count = int(getattr(stats, "ast_split_success_count", 0) or 0)
    _runtime_stats.ast_split_failure_count = int(getattr(stats, "ast_split_failure_count", 0) or 0)
    _runtime_stats.ast_fallback_used_count = int(getattr(stats, "ast_fallback_used_count", 0) or 0)
    _runtime_stats.roundtrip_verify_success_count = int(getattr(stats, "roundtrip_verify_success_count", 0) or 0)
    _runtime_stats.roundtrip_verify_failure_count = int(getattr(stats, "roundtrip_verify_failure_count", 0) or 0)
    _runtime_stats.dynamic_dependency_add_count = int(getattr(stats, "dynamic_dependency_add_count", 0) or 0)


def increment_retry_count(amount: int = 1) -> None:
    _runtime_stats.total_retry_count += int(amount or 0)


def increment_regenerate_count(amount: int = 1) -> None:
    _runtime_stats.total_regenerate_count += int(amount or 0)


def increment_error_count(amount: int = 1) -> None:
    _runtime_stats.total_error_count += int(amount or 0)


def set_error_count(count: int) -> None:
    _runtime_stats.total_error_count = max(0, int(count or 0))


def record_ast_split_result(ast_ok: bool, fallback_used: bool = False) -> None:
    if ast_ok:
        _runtime_stats.ast_split_success_count += 1
    else:
        _runtime_stats.ast_split_failure_count += 1
    if fallback_used:
        _runtime_stats.ast_fallback_used_count += 1


def increment_roundtrip_verify_success_count(amount: int = 1) -> None:
    _runtime_stats.roundtrip_verify_success_count += int(amount or 0)


def increment_roundtrip_verify_failure_count(amount: int = 1) -> None:
    _runtime_stats.roundtrip_verify_failure_count += int(amount or 0)


def increment_dynamic_dependency_add_count(amount: int = 1) -> None:
    _runtime_stats.dynamic_dependency_add_count += int(amount or 0)
