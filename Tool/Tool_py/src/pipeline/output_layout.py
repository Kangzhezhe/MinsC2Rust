import os
from pathlib import Path
from typing import Dict


STATE_FILES = {
    "once_retry_count_dict.json",
    "dependency_overrides.json",
    "pending_accepted.json",
    "runtime_status.json",
    "source_runtime_status.json",
    "source_runtime_pass_cache.json",
    "repair_records.json",
}

METRIC_FILES = {
    "cost.csv",
    "compile_pass_rate.csv",
    "once_pass_rates.csv",
    "tests_pass_rates.csv",
    "asserts_count.csv",
    "loc_statistics.csv",
    "safety.csv",
}

LOG_FILES = {
    "run.log",
    "llm_chat.log",
}


def state_dir(output_dir: os.PathLike[str] | str) -> Path:
    return Path(output_dir) / "state"


def metrics_dir(output_dir: os.PathLike[str] | str) -> Path:
    return Path(output_dir) / "metrics"


def logs_dir(output_dir: os.PathLike[str] | str) -> Path:
    return Path(output_dir) / "logs"


def artifact_path(output_dir: os.PathLike[str] | str, filename: str) -> Path:
    base = Path(output_dir)
    if filename in STATE_FILES:
        return state_dir(base) / filename
    if filename in METRIC_FILES:
        return metrics_dir(base) / filename
    if filename in LOG_FILES:
        return logs_dir(base) / filename
    return base / filename


def resolve_existing_artifact(output_dir: os.PathLike[str] | str, filename: str) -> Path:
    preferred = artifact_path(output_dir, filename)
    if preferred.exists():
        return preferred
    return Path(output_dir) / filename


def ensure_output_subdirs(output_dir: os.PathLike[str] | str) -> Dict[str, Path]:
    dirs = {
        "state": state_dir(output_dir),
        "metrics": metrics_dir(output_dir),
        "logs": logs_dir(output_dir),
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs
