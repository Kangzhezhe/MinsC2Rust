"""Checkpoint load/save helpers with legacy file compatibility."""

import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, DefaultDict, Dict, List, Optional

from .output_layout import artifact_path, ensure_output_subdirs, resolve_existing_artifact
from .stats import PipelineStats
from utils import is_rust_snippet_brace_balanced


@dataclass
class CheckpointState:
    """Runtime state reconstructed from old checkpoint/result JSON files."""

    results: DefaultDict[str, Dict[str, str]] = field(default_factory=lambda: defaultdict(dict))
    once_retry_count_dict: DefaultDict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(dict))
    all_error_funcs_content: DefaultDict[str, Dict[str, str]] = field(default_factory=lambda: defaultdict(dict))
    pending_accepted: DefaultDict[str, Dict[str, str]] = field(default_factory=lambda: defaultdict(dict))
    runtime_status: DefaultDict[str, Dict[str, Dict[str, Any]]] = field(default_factory=lambda: defaultdict(dict))
    source_runtime_status: DefaultDict[str, Dict[str, Any]] = field(default_factory=lambda: defaultdict(dict))
    source_runtime_pass_cache: Dict[str, Any] = field(default_factory=dict)
    repair_records: DefaultDict[str, List[Dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    dependency_overrides: Dict[str, str] = field(default_factory=dict)
    stats: PipelineStats = field(default_factory=PipelineStats)


def _current_error_record_count(all_error_funcs_content) -> int:
    return sum(
        len(funcs)
        for funcs in (all_error_funcs_content or {}).values()
        if isinstance(funcs, dict)
    )


def reconcile_error_records_with_results(results, all_error_funcs_content) -> int:
    """Remove error records for functions that now have valid result snippets."""
    removed = 0
    if not isinstance(results, dict) or not isinstance(all_error_funcs_content, dict):
        return removed

    for source_name in list(all_error_funcs_content.keys()):
        source_errors = all_error_funcs_content.get(source_name)
        if not isinstance(source_errors, dict):
            continue
        source_results = results.get(source_name, {})
        if not isinstance(source_results, dict):
            continue
        for func_name in list(source_errors.keys()):
            if func_name == "extra":
                continue
            snippet = str(source_results.get(func_name, "") or "")
            if snippet.strip() and is_rust_snippet_brace_balanced(snippet):
                del source_errors[func_name]
                removed += 1
        if not source_errors:
            del all_error_funcs_content[source_name]

    return removed


def _checkpoint_stats_with_reconciled_errors(
    stats: Optional[PipelineStats],
    all_error_funcs_content,
) -> PipelineStats:
    checkpoint_stats = stats or PipelineStats()
    return PipelineStats(
        total_retry_count=checkpoint_stats.total_retry_count,
        total_regenerate_count=checkpoint_stats.total_regenerate_count,
        total_error_count=_current_error_record_count(all_error_funcs_content),
        total_input_tokens=checkpoint_stats.total_input_tokens,
        total_output_tokens=checkpoint_stats.total_output_tokens,
        total_tokens=checkpoint_stats.total_tokens,
        ast_split_success_count=checkpoint_stats.ast_split_success_count,
        ast_split_failure_count=checkpoint_stats.ast_split_failure_count,
        ast_fallback_used_count=checkpoint_stats.ast_fallback_used_count,
        roundtrip_verify_success_count=checkpoint_stats.roundtrip_verify_success_count,
        roundtrip_verify_failure_count=checkpoint_stats.roundtrip_verify_failure_count,
        dynamic_dependency_add_count=checkpoint_stats.dynamic_dependency_add_count,
    )


def save_checkpoint(
    results,
    once_retry_count_dict,
    all_error_funcs_content,
    output_dir,
    *,
    stats: Optional[PipelineStats] = None,
    dependency_overrides: Optional[Dict[str, str]] = None,
    pending_accepted: Optional[Dict[str, Dict[str, str]]] = None,
    runtime_status: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None,
    source_runtime_status: Optional[Dict[str, Dict[str, Any]]] = None,
    source_runtime_pass_cache: Optional[Dict[str, Any]] = None,
    repair_records: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> None:
    """Persist pipeline state using the legacy multi-file checkpoint layout."""
    os.makedirs(output_dir, exist_ok=True)
    ensure_output_subdirs(output_dir)
    reconcile_error_records_with_results(results, all_error_funcs_content)
    checkpoint_stats = _checkpoint_stats_with_reconciled_errors(stats, all_error_funcs_content)

    with open(os.path.join(output_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    with open(os.path.join(output_dir, "all_error_funcs_content.json"), "w", encoding="utf-8") as f:
        json.dump(all_error_funcs_content, f, indent=4, ensure_ascii=False)

    with open(os.path.join(output_dir, "checkpoint.json"), "w", encoding="utf-8") as f:
        json.dump(checkpoint_stats.to_checkpoint_dict(), f, indent=4, ensure_ascii=False)

    with open(artifact_path(output_dir, "once_retry_count_dict.json"), "w", encoding="utf-8") as f:
        json.dump(once_retry_count_dict, f, indent=4, ensure_ascii=False)
    with open(artifact_path(output_dir, "dependency_overrides.json"), "w", encoding="utf-8") as f:
        json.dump(dict(dependency_overrides or {}), f, indent=4, ensure_ascii=False)

    with open(artifact_path(output_dir, "pending_accepted.json"), "w", encoding="utf-8") as f:
        json.dump(pending_accepted or {}, f, indent=4, ensure_ascii=False)
    with open(artifact_path(output_dir, "runtime_status.json"), "w", encoding="utf-8") as f:
        json.dump(runtime_status or {}, f, indent=4, ensure_ascii=False)
    with open(artifact_path(output_dir, "source_runtime_status.json"), "w", encoding="utf-8") as f:
        json.dump(source_runtime_status or {}, f, indent=4, ensure_ascii=False)
    with open(artifact_path(output_dir, "source_runtime_pass_cache.json"), "w", encoding="utf-8") as f:
        json.dump(source_runtime_pass_cache or {}, f, indent=4, ensure_ascii=False)
    with open(artifact_path(output_dir, "repair_records.json"), "w", encoding="utf-8") as f:
        json.dump(repair_records or {}, f, indent=4, ensure_ascii=False)


def load_checkpoint(output_dir) -> CheckpointState:
    """Load all known checkpoint files while tolerating missing old fields."""
    state = CheckpointState()

    results_path = os.path.join(output_dir, "results.json")
    retry_path = resolve_existing_artifact(output_dir, "once_retry_count_dict.json")
    error_path = os.path.join(output_dir, "all_error_funcs_content.json")
    checkpoint_path = os.path.join(output_dir, "checkpoint.json")
    dependency_path = resolve_existing_artifact(output_dir, "dependency_overrides.json")
    pending_path = resolve_existing_artifact(output_dir, "pending_accepted.json")
    runtime_status_path = resolve_existing_artifact(output_dir, "runtime_status.json")
    source_runtime_status_path = resolve_existing_artifact(output_dir, "source_runtime_status.json")
    source_runtime_pass_cache_path = resolve_existing_artifact(output_dir, "source_runtime_pass_cache.json")
    repair_records_path = resolve_existing_artifact(output_dir, "repair_records.json")

    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            for k, v in loaded.items():
                state.results[k] = v

    if os.path.exists(retry_path):
        with open(retry_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            for k, v in loaded.items():
                state.once_retry_count_dict[k] = v

    if os.path.exists(error_path):
        with open(error_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            for k, v in loaded.items():
                state.all_error_funcs_content[k] = v

    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            state.stats = PipelineStats.from_checkpoint(json.load(f))

    if os.path.exists(dependency_path):
        with open(dependency_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                state.dependency_overrides = {
                    str(k): str(v)
                    for k, v in loaded.items()
                    if str(k).strip() and str(k).strip() != "libc"
                }

    if os.path.exists(pending_path):
        with open(pending_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                for k, v in loaded.items():
                    state.pending_accepted[k] = v if isinstance(v, dict) else {}

    if os.path.exists(runtime_status_path):
        with open(runtime_status_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                for k, v in loaded.items():
                    state.runtime_status[k] = v if isinstance(v, dict) else {}

    if os.path.exists(source_runtime_status_path):
        with open(source_runtime_status_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                for k, v in loaded.items():
                    state.source_runtime_status[k] = v if isinstance(v, dict) else {}

    if os.path.exists(source_runtime_pass_cache_path):
        with open(source_runtime_pass_cache_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                state.source_runtime_pass_cache = loaded

    if os.path.exists(repair_records_path):
        with open(repair_records_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                for k, v in loaded.items():
                    state.repair_records[k] = v if isinstance(v, list) else []

    return state
