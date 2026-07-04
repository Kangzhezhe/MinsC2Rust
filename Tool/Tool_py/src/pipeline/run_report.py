import csv
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .output_layout import artifact_path, ensure_output_subdirs, resolve_existing_artifact


DEFAULT_LOG_MARKERS = [
    "PASS-BUT-TEST-FAIL",
    "TEST-RUNTIME-CC-MINI-FAIL",
    "Tool error",
    "unexpected keyword",
    "No tools called",
    "empty completion",
    "tool_parser",
    "DSML",
    "@pram",
    "missing 3 required",
    "timed out",
    "TimeoutError",
]


@dataclass(frozen=True)
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    elapsed_seconds: float


def generate_translation_report(
    output_dir: os.PathLike[str] | str,
    *,
    verify: bool = True,
    command_runner: Optional[Callable[[List[str], Path, int], CommandResult]] = None,
    verification_timeout_seconds: int = 300,
) -> Dict[str, Any]:
    """Generate report.json and report.md for one translation run output dir."""
    output_path = _resolve_output_dir(Path(output_dir))
    output_path.mkdir(parents=True, exist_ok=True)
    ensure_output_subdirs(output_path)

    checkpoint = _read_json(output_path / "checkpoint.json", {})
    results = _read_json(output_path / "results.json", {})
    pending = _read_json(resolve_existing_artifact(output_path, "pending_accepted.json"), {})
    errors = _read_json(output_path / "all_error_funcs_content.json", {})
    runtime_status = _read_json(resolve_existing_artifact(output_path, "runtime_status.json"), {})
    source_runtime_status = _read_json(resolve_existing_artifact(output_path, "source_runtime_status.json"), {})
    repair_records = _read_json(resolve_existing_artifact(output_path, "repair_records.json"), {})

    app_log_text = _read_text(output_path / "app.log")
    run_log_text = _read_text(resolve_existing_artifact(output_path, "run.log"))
    final_log_summary = _parse_final_summary(app_log_text)
    runtime_check_summary = _parse_runtime_check_summary(app_log_text)
    pass_entries = _parse_pass_entries(app_log_text)
    cost_summary = _parse_cost_csv(resolve_existing_artifact(output_path, "cost.csv"))
    verification = _run_verification(
        output_path,
        verify=verify,
        command_runner=command_runner,
        timeout_seconds=verification_timeout_seconds,
    )

    state_summary = _build_state_summary(
        checkpoint=checkpoint,
        results=results,
        pending=pending,
        errors=errors,
        runtime_status=runtime_status,
        source_runtime_status=source_runtime_status,
    )
    repairs_summary = _build_repairs_summary(repair_records)
    quality_guards = _build_quality_guard_summary(checkpoint)
    marker_summary = {
        "app.log": _count_markers(app_log_text),
        "run.log": _count_markers(run_log_text),
    }
    hotspots = _build_hotspots(pass_entries, repair_records)

    cargo_test = verification.get("cargo_test", {})
    status = "passed" if cargo_test.get("ok") is True else "failed"
    if cargo_test.get("status") == "skipped":
        status = "not_verified"

    generated_at = datetime.now(timezone.utc).isoformat()
    report = {
        "generated_at": generated_at,
        "status": status,
        "output_dir": str(output_path),
        "summary": {
            "total_time": final_log_summary.get("total_time", ""),
            "retries": _coalesce_int(final_log_summary.get("retries"), checkpoint.get("total_retry_count")),
            "regenerations": _coalesce_int(
                final_log_summary.get("regenerations"),
                checkpoint.get("total_regenerate_count"),
            ),
            "errors": _coalesce_int(final_log_summary.get("errors"), checkpoint.get("total_error_count")),
            "dynamic_dependency_adds": _coalesce_int(
                None,
                checkpoint.get("dynamic_dependency_add_count"),
            ),
            "result_functions": state_summary["result_functions"],
            "pending_functions": state_summary["pending_functions"],
            "error_functions": state_summary["error_functions"],
            "repair_records": repairs_summary["total"],
        },
        "verification": verification,
        "runtime_check": runtime_check_summary,
        "state": state_summary,
        "quality_guards": quality_guards,
        "cost": cost_summary,
        "hotspots": hotspots,
        "repairs": repairs_summary,
        "log_markers": marker_summary,
        "artifacts": _build_artifacts(output_path),
    }

    _write_json(output_path / "report.json", report)
    (output_path / "report.md").write_text(_render_markdown(report), encoding="utf-8")
    return report


def _resolve_output_dir(path: Path) -> Path:
    if path.name == "Output":
        return path
    nested = path / "Output"
    if nested.exists():
        return nested
    return path


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _run_verification(
    output_path: Path,
    *,
    verify: bool,
    command_runner: Optional[Callable[[List[str], Path, int], CommandResult]],
    timeout_seconds: int,
) -> Dict[str, Any]:
    verify_project = output_path / "verify_project"
    result = {
        "verify_project": str(verify_project),
        "cargo_test": {
            "status": "skipped",
            "ok": None,
            "reason": "",
            "command": "cargo test --quiet",
            "returncode": None,
            "elapsed_seconds": 0.0,
            "stdout_tail": "",
            "stderr_tail": "",
        },
    }
    if not verify:
        result["cargo_test"]["reason"] = "verification disabled"
        return result
    if not (verify_project / "Cargo.toml").exists():
        result["cargo_test"]["reason"] = "verify_project Cargo.toml not found"
        return result

    runner = command_runner or _default_command_runner
    try:
        cmd_result = runner(["cargo", "test", "--quiet"], verify_project, timeout_seconds)
    except Exception as exc:
        result["cargo_test"].update(
            {
                "status": "error",
                "ok": False,
                "reason": _sanitize_text(str(exc), limit=500),
            }
        )
        return result

    result["cargo_test"].update(
        {
            "status": "completed",
            "ok": cmd_result.returncode == 0,
            "command": cmd_result.command,
            "returncode": cmd_result.returncode,
            "elapsed_seconds": round(cmd_result.elapsed_seconds, 3),
            "stdout_tail": _sanitize_text(_tail(cmd_result.stdout), limit=4000),
            "stderr_tail": _sanitize_text(_tail(_filter_cargo_stderr_for_report(cmd_result.stderr)), limit=4000),
        }
    )
    return result


def _default_command_runner(command: List[str], cwd: Path, timeout: int) -> CommandResult:
    start = time.time()
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return CommandResult(
        command=" ".join(command),
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        elapsed_seconds=time.time() - start,
    )


def _parse_final_summary(app_log_text: str) -> Dict[str, Any]:
    pattern = re.compile(
        r"Total time:\s*(?P<total_time>\d+:\d+:\d+),\s*"
        r"retries=(?P<retries>\d+),\s*"
        r"regenerations=(?P<regenerations>\d+),\s*"
        r"errors=(?P<errors>\d+)"
    )
    matches = list(pattern.finditer(app_log_text))
    if not matches:
        return {}
    match = matches[-1]
    return {
        "total_time": match.group("total_time"),
        "retries": int(match.group("retries")),
        "regenerations": int(match.group("regenerations")),
        "errors": int(match.group("errors")),
    }


def _parse_runtime_check_summary(app_log_text: str) -> Dict[str, Any]:
    pattern = re.compile(
        r"\[RUNTIME-CHECK-MODE\]\s+mode=(?P<mode>[^\s]+)\s+enabled=(?P<enabled>[01])"
    )
    matches = list(pattern.finditer(app_log_text or ""))
    if not matches:
        return {"mode": "unknown", "enabled": None}
    match = matches[-1]
    return {
        "mode": match.group("mode"),
        "enabled": bool(int(match.group("enabled"))),
    }


def _parse_pass_entries(app_log_text: str) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    pattern = re.compile(
        r"\[PASS\]\s+(?P<source>[^:\s]+):(?P<func>[^\s]+).*?"
        r"elapsed=(?P<elapsed>[0-9.]+)s.*?"
        r"retries=(?P<retries>\d+).*?"
        r"regenerations=(?P<regenerations>\d+).*?"
        r"runtime=(?P<runtime>.*)$"
    )
    for line in app_log_text.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        entries.append(
            {
                "source": match.group("source"),
                "function": match.group("func"),
                "elapsed_seconds": float(match.group("elapsed")),
                "retries": int(match.group("retries")),
                "regenerations": int(match.group("regenerations")),
                "runtime": _sanitize_text(match.group("runtime"), limit=300),
            }
        )
    return entries


def _parse_cost_csv(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"global": {}, "modules": []}
    global_row: Dict[str, Any] = {}
    modules: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                parsed = {
                    "scope": row.get("scope", ""),
                    "source_name": row.get("source_name", ""),
                    "elapsed_seconds": _parse_float(row.get("elapsed_seconds")),
                    "input_tokens": _parse_int(row.get("input_tokens")),
                    "output_tokens": _parse_int(row.get("output_tokens")),
                    "total_tokens": _parse_int(row.get("total_tokens")),
                }
                if parsed["scope"] == "global":
                    global_row = parsed
                elif parsed["scope"] == "module":
                    modules.append(parsed)
    except Exception:
        return {"global": {}, "modules": []}
    modules.sort(key=lambda row: row.get("elapsed_seconds") or 0.0, reverse=True)
    return {"global": global_row, "modules": modules}


def _build_state_summary(
    *,
    checkpoint: Dict[str, Any],
    results: Dict[str, Any],
    pending: Dict[str, Any],
    errors: Dict[str, Any],
    runtime_status: Dict[str, Any],
    source_runtime_status: Dict[str, Any],
) -> Dict[str, Any]:
    result_functions = _count_nested_dict_items(results)
    pending_functions = _count_nested_dict_items(pending)
    error_functions = _count_nested_dict_items(errors)
    runtime_counts: Dict[str, int] = {}
    for funcs in runtime_status.values():
        if not isinstance(funcs, dict):
            continue
        for status in funcs.values():
            if not isinstance(status, dict):
                continue
            key = str(status.get("status", "unknown"))
            runtime_counts[key] = runtime_counts.get(key, 0) + 1

    source_statuses = {
        source: status.get("status", "unknown")
        for source, status in source_runtime_status.items()
        if isinstance(status, dict)
    }
    source_runtime_counts: Dict[str, int] = {}
    for status in source_runtime_status.values():
        if not isinstance(status, dict):
            continue
        key = str(status.get("status", "unknown"))
        source_runtime_counts[key] = source_runtime_counts.get(key, 0) + 1
    issues: List[str] = []
    checkpoint_errors = checkpoint.get("total_error_count")
    if isinstance(checkpoint_errors, int) and checkpoint_errors != error_functions:
        issues.append(f"checkpoint.total_error_count={checkpoint_errors} but error_functions={error_functions}")
    conflicts = sorted(
        f"{source}:{func}"
        for source, funcs in errors.items()
        if isinstance(funcs, dict)
        for func in funcs.keys()
        if isinstance(results.get(source), dict) and func in results[source]
    )
    if conflicts:
        issues.append("functions appear in both results and errors: " + ", ".join(conflicts[:20]))
    if pending_functions:
        issues.append(f"pending_accepted has {pending_functions} functions")

    return {
        "result_functions": result_functions,
        "pending_functions": pending_functions,
        "error_functions": error_functions,
        "runtime_status_counts": runtime_counts,
        "source_runtime_status_counts": source_runtime_counts,
        "source_statuses": source_statuses,
        "reconciliation": {
            "ok": not issues,
            "issues": issues,
        },
    }


def _build_repairs_summary(repair_records: Dict[str, Any]) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    by_source: Dict[str, int] = {}
    for source, source_records in repair_records.items():
        if not isinstance(source_records, list):
            continue
        by_source[source] = len(source_records)
        for record in source_records:
            if not isinstance(record, dict):
                continue
            records.append(
                {
                    "source": source,
                    "attempt": record.get("attempt"),
                    "trigger": _sanitize_text(str(record.get("trigger", "")), limit=120),
                    "failure_kind": _sanitize_text(str(record.get("failure_kind", "")), limit=120),
                    "modified_files": record.get("modified_files", []),
                    "acceptance_command": _sanitize_text(str(record.get("acceptance_command", "")), limit=200),
                    "returncode": record.get("returncode"),
                    "backfill_status": _sanitize_text(str(record.get("backfill_status", "")), limit=120),
                    "summary": _sanitize_text(str(record.get("summary", "")), limit=500),
                }
            )
    return {
        "total": len(records),
        "by_source": by_source,
        "records": records,
    }


def _build_quality_guard_summary(checkpoint: Dict[str, Any]) -> Dict[str, int]:
    return {
        "ast_split_success_count": _coalesce_int(checkpoint.get("ast_split_success_count")),
        "ast_split_failure_count": _coalesce_int(checkpoint.get("ast_split_failure_count")),
        "ast_fallback_used_count": _coalesce_int(checkpoint.get("ast_fallback_used_count")),
        "roundtrip_verify_success_count": _coalesce_int(checkpoint.get("roundtrip_verify_success_count")),
        "roundtrip_verify_failure_count": _coalesce_int(checkpoint.get("roundtrip_verify_failure_count")),
    }


def _build_hotspots(pass_entries: List[Dict[str, Any]], repair_records: Dict[str, Any]) -> Dict[str, Any]:
    slowest = sorted(pass_entries, key=lambda item: item.get("elapsed_seconds", 0.0), reverse=True)[:10]
    retry_heavy = sorted(
        [entry for entry in pass_entries if entry.get("retries", 0) > 0],
        key=lambda item: (item.get("retries", 0), item.get("elapsed_seconds", 0.0)),
        reverse=True,
    )[:10]
    cc_mini_sources = [
        {"source": source, "repair_records": len(records)}
        for source, records in repair_records.items()
        if isinstance(records, list) and records
    ]
    cc_mini_sources.sort(key=lambda item: item["repair_records"], reverse=True)
    return {
        "slowest_functions": slowest,
        "retry_heavy_functions": retry_heavy,
        "cc_mini_repair_sources": cc_mini_sources,
    }


def _count_markers(text: str) -> Dict[str, int]:
    return {marker: text.count(marker) for marker in DEFAULT_LOG_MARKERS}


def _build_artifacts(output_path: Path) -> Dict[str, str]:
    artifact_names = [
        "report.json",
        "report.md",
        "app.log",
        "run.log",
        "cost.csv",
        "checkpoint.json",
        "results.json",
        "pending_accepted.json",
        "runtime_status.json",
        "source_runtime_status.json",
        "source_runtime_pass_cache.json",
        "repair_records.json",
        "all_error_funcs_content.json",
    ]
    artifacts = {
        name: str(resolve_existing_artifact(output_path, name))
        for name in artifact_names
        if resolve_existing_artifact(output_path, name).exists() or name in {"report.json", "report.md"}
    }
    verify_project = output_path / "verify_project"
    if verify_project.exists():
        artifacts["verify_project"] = str(verify_project)
    return artifacts


def _render_markdown(report: Dict[str, Any]) -> str:
    summary = report["summary"]
    cargo_test = report["verification"]["cargo_test"]
    state = report["state"]
    cost = report["cost"]
    repairs = report["repairs"]
    hotspots = report["hotspots"]
    markers = report["log_markers"]
    artifacts = report["artifacts"]
    runtime_check = report.get("runtime_check", {})
    quality_guards = report.get("quality_guards", {})

    lines = [
        "# Translation Run Report",
        "",
        "## Summary",
        "",
        f"- status: `{report['status']}`",
        f"- total time: `{summary.get('total_time') or ''}`",
        f"- retries: `{summary.get('retries')}`",
        f"- regenerations: `{summary.get('regenerations')}`",
        f"- errors: `{summary.get('errors')}`",
        f"- dynamic dependency adds: `{summary.get('dynamic_dependency_adds')}`",
        f"- result functions: `{summary.get('result_functions')}`",
        f"- pending functions: `{summary.get('pending_functions')}`",
        f"- error functions: `{summary.get('error_functions')}`",
        f"- repair records: `{summary.get('repair_records')}`",
        f"- runtime check mode: `{runtime_check.get('mode')}`",
        f"- runtime check enabled: `{runtime_check.get('enabled')}`",
        "",
        "## Quality Guards",
        "",
        f"- AST split success: `{quality_guards.get('ast_split_success_count', 0)}`",
        f"- AST split failure: `{quality_guards.get('ast_split_failure_count', 0)}`",
        f"- AST fallback used: `{quality_guards.get('ast_fallback_used_count', 0)}`",
        f"- round-trip verify success: `{quality_guards.get('roundtrip_verify_success_count', 0)}`",
        f"- round-trip verify failure: `{quality_guards.get('roundtrip_verify_failure_count', 0)}`",
        "",
        "## Verification",
        "",
        f"- command: `{cargo_test.get('command')}`",
        f"- status: `{cargo_test.get('status')}`",
        f"- ok: `{cargo_test.get('ok')}`",
        f"- returncode: `{cargo_test.get('returncode')}`",
        f"- elapsed seconds: `{cargo_test.get('elapsed_seconds')}`",
    ]
    if cargo_test.get("reason"):
        lines.append(f"- reason: `{cargo_test.get('reason')}`")
    if cargo_test.get("stderr_tail"):
        lines.extend(["", "### cargo test stderr tail", "", "```text", cargo_test["stderr_tail"], "```"])
    if cargo_test.get("stdout_tail"):
        lines.extend(["", "### cargo test stdout tail", "", "```text", cargo_test["stdout_tail"], "```"])

    lines.extend(
        [
            "",
            "## State Reconciliation",
            "",
            f"- ok: `{state['reconciliation']['ok']}`",
            f"- pending functions: `{state['pending_functions']}`",
            f"- error functions: `{state['error_functions']}`",
            "",
            "### Runtime Status Counts",
            "",
            "| status | count |",
            "| --- | ---: |",
        ]
    )
    for key, value in sorted(state["runtime_status_counts"].items()):
        lines.append(f"| `{key}` | {value} |")
    if not state["runtime_status_counts"]:
        lines.append("| none | 0 |")

    lines.extend(["", "### Source Runtime Status Counts", "", "| status | count |", "| --- | ---: |"])
    for key, value in sorted(state.get("source_runtime_status_counts", {}).items()):
        lines.append(f"| `{key}` | {value} |")
    if not state.get("source_runtime_status_counts"):
        lines.append("| none | 0 |")

    lines.extend(["", "### Source Statuses", "", "| source | status |", "| --- | --- |"])
    for source, status in sorted(state["source_statuses"].items()):
        lines.append(f"| `{source}` | `{status}` |")
    if not state["source_statuses"]:
        lines.append("| none | none |")

    if state["reconciliation"]["issues"]:
        lines.extend(["", "### Reconciliation Issues", ""])
        for issue in state["reconciliation"]["issues"]:
            lines.append(f"- {_sanitize_text(issue, limit=500)}")

    lines.extend(["", "## Cost", ""])
    global_cost = cost.get("global") or {}
    if global_cost:
        lines.extend(
            [
                f"- elapsed seconds: `{global_cost.get('elapsed_seconds')}`",
                f"- input tokens: `{global_cost.get('input_tokens')}`",
                f"- output tokens: `{global_cost.get('output_tokens')}`",
                f"- total tokens: `{global_cost.get('total_tokens')}`",
            ]
        )
    else:
        lines.append("- no cost.csv summary found")

    lines.extend(["", "### Module Cost", "", "| source | elapsed | input | output | total |", "| --- | ---: | ---: | ---: | ---: |"])
    for row in (cost.get("modules") or [])[:20]:
        lines.append(
            f"| `{row.get('source_name')}` | {row.get('elapsed_seconds')} | {row.get('input_tokens')} | {row.get('output_tokens')} | {row.get('total_tokens')} |"
        )
    if not cost.get("modules"):
        lines.append("| none | 0 | 0 | 0 | 0 |")

    lines.extend(["", "## Function Hotspots", "", "### Slowest Functions", "", "| source | function | elapsed | runtime |", "| --- | --- | ---: | --- |"])
    for entry in hotspots["slowest_functions"]:
        lines.append(
            f"| `{entry['source']}` | `{entry['function']}` | {entry['elapsed_seconds']} | `{entry['runtime']}` |"
        )
    if not hotspots["slowest_functions"]:
        lines.append("| none | none | 0 | none |")

    lines.extend(["", "### Retry Heavy Functions", "", "| source | function | retries | elapsed |", "| --- | --- | ---: | ---: |"])
    for entry in hotspots["retry_heavy_functions"]:
        lines.append(
            f"| `{entry['source']}` | `{entry['function']}` | {entry['retries']} | {entry['elapsed_seconds']} |"
        )
    if not hotspots["retry_heavy_functions"]:
        lines.append("| none | none | 0 | 0 |")

    lines.extend(["", "## Runtime / CC-MINI Repairs", "", f"- total repair records: `{repairs['total']}`", "", "| source | attempt | trigger | failure | backfill | summary |", "| --- | ---: | --- | --- | --- | --- |"])
    for record in repairs["records"][:30]:
        lines.append(
            f"| `{record['source']}` | {record.get('attempt')} | `{record.get('trigger')}` | `{record.get('failure_kind')}` | `{record.get('backfill_status')}` | {record.get('summary')} |"
        )
    if not repairs["records"]:
        lines.append("| none | 0 | none | none | none | none |")

    lines.extend(["", "## Instability Markers", ""])
    for log_name, counts in markers.items():
        lines.extend(["", f"### {log_name}", "", "| marker | count |", "| --- | ---: |"])
        for marker, count in counts.items():
            lines.append(f"| `{marker}` | {count} |")

    lines.extend(["", "## Artifacts", "", "| artifact | path |", "| --- | --- |"])
    for name, path in sorted(artifacts.items()):
        lines.append(f"| `{name}` | `{path}` |")

    return "\n".join(lines) + "\n"


def _count_nested_dict_items(data: Any) -> int:
    if not isinstance(data, dict):
        return 0
    return sum(len(value) for value in data.values() if isinstance(value, dict))


def _coalesce_int(*values: Any) -> int:
    for value in values:
        parsed = _parse_int(value)
        if parsed is not None:
            return parsed
    return 0


def _parse_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except Exception:
        return None


def _parse_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _tail(text: str, *, max_lines: int = 80) -> str:
    lines = (text or "").splitlines()
    return "\n".join(lines[-max_lines:])


def _filter_cargo_stderr_for_report(text: str) -> str:
    """Remove Rust warning diagnostics from report stderr while keeping failures."""

    kept: list[str] = []
    skipping_warning = False
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("warning:"):
            skipping_warning = True
            continue
        if skipping_warning:
            if stripped == "":
                skipping_warning = False
            continue
        kept.append(line)

    return "\n".join(kept).strip()


def _sanitize_text(text: str, *, limit: int) -> str:
    sanitized = text or ""
    sanitized = re.sub(r"sk[_-][A-Za-z0-9_\-]{8,}", "[REDACTED_KEY]", sanitized)
    sanitized = re.sub(r"(?i)(api[_-]?key\s*[=:]\s*)['\"]?[^'\"\s]+", r"\1[REDACTED_KEY]", sanitized)
    sanitized = re.sub(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", sanitized)
    if len(sanitized) > limit:
        return sanitized[:limit] + "\n...(truncated)"
    return sanitized


def main(argv: Optional[List[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python -m pipeline.run_report <run_root_or_output_dir> [--no-verify]")
        return 2
    verify = "--no-verify" not in args
    args = [arg for arg in args if arg != "--no-verify"]
    report = generate_translation_report(args[0], verify=verify)
    print(report["artifacts"]["report.json"])
    print(report["artifacts"]["report.md"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
