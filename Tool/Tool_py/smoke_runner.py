"""Utilities for repeatable Tool_py smoke validation.

This module deliberately keeps the expensive parts of the real smoke test
outside unit tests. The pure functions here cover the behavior that is easy to
regress during refactoring: deriving a reference-aligned config, comparing
output directories, and keeping the exported Cargo project validation contract
stable.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from parse_config import read_config


CARGO_EXPORT_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("cargo", "check", "--quiet"),
    ("cargo", "build", "--quiet"),
    ("cargo", "test", "--quiet", "--no-run"),
    ("cargo", "test", "--quiet"),
)

REFERENCE_ALIGNED_INCLUDE_FILES = frozenset({"alloc-testing", "test-alloc-testing"})


@dataclass(frozen=True)
class DerivedSmokeConfig:
    """Paths produced by a derived real-smoke config."""

    config_path: Path
    tmp_dir: Path
    output_dir: Path


@dataclass(frozen=True)
class SmokeOutputSummary:
    """Small, stable summary of a Tool_py output directory."""

    output_dir: Path
    checkpoint_stats: Mapping[str, int]
    result_counts: Mapping[str, int]
    result_sources: frozenset[str]
    error_count: int
    compile_overall_with_test: float
    compile_overall_without_test: float
    once_overall: float


@dataclass(frozen=True)
class SmokeComparison:
    """Comparison result for current smoke output against a reference output."""

    ok: bool
    issues: tuple[str, ...]
    current: SmokeOutputSummary
    reference: SmokeOutputSummary
    result_count_deltas: Mapping[str, tuple[int, int]]


@dataclass(frozen=True)
class CargoCommandResult:
    """Result for one exported-project Cargo validation command."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class SmokeCommandResult:
    """Result for one command in the real-smoke orchestration."""

    command: tuple[str, ...]
    cwd: Path
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ReferenceAlignedSmokeRunResult:
    """End-to-end result for the reference-aligned arraylist smoke runner."""

    ok: bool
    issues: tuple[str, ...]
    config: DerivedSmokeConfig
    command_results: tuple[SmokeCommandResult, ...]
    comparison: SmokeComparison | None
    cargo_results: tuple[CargoCommandResult, ...]


def write_reference_aligned_arraylist_config(
    *,
    base_config_path: Path,
    destination_config_path: Path,
    output_root: Path,
) -> DerivedSmokeConfig:
    """Create an arraylist smoke config that writes to a fixed output root.

    The committed/default config may exclude `alloc-testing` and
    `test-alloc-testing` for faster iteration. The reference output includes
    them, so a reference-aligned smoke config must remove only those exclusions
    while preserving other intentional excludes such as framework helpers.
    """

    config = read_config(str(base_config_path))
    config.remove_section("Config")

    tmp_dir = output_root / "tmp"
    output_dir = output_root / "Output"
    if "Paths" not in config:
        config["Paths"] = {}
    config["Paths"]["tmp_dir"] = str(tmp_dir)
    config["Paths"]["output_dir"] = str(output_dir)

    if "ExcludeFiles" not in config:
        config["ExcludeFiles"] = {}
    excluded_files = _split_csv(config["ExcludeFiles"].get("files", ""))
    config["ExcludeFiles"]["files"] = ", ".join(
        item for item in excluded_files if item not in REFERENCE_ALIGNED_INCLUDE_FILES
    )

    destination_config_path.parent.mkdir(parents=True, exist_ok=True)
    with destination_config_path.open("w", encoding="utf-8") as f:
        config.write(f)

    return DerivedSmokeConfig(
        config_path=destination_config_path,
        tmp_dir=tmp_dir,
        output_dir=output_dir,
    )


def compare_smoke_outputs(current_output_dir: Path, reference_output_dir: Path) -> SmokeComparison:
    """Compare current smoke output with the preserved reference output.

    Function count deltas are reported but do not fail the comparison by
    themselves. This matches the current acceptance rule for `test-arraylist`:
    source coverage, compile/test results, and checkpoint error counts matter
    more than exact helper-test function counts.
    """

    current = _load_smoke_output_summary(current_output_dir)
    reference = _load_smoke_output_summary(reference_output_dir)

    issues: list[str] = []
    if current.result_sources != reference.result_sources:
        missing = sorted(reference.result_sources - current.result_sources)
        extra = sorted(current.result_sources - reference.result_sources)
        issues.append(f"source set differs: missing={missing}, extra={extra}")

    if current.error_count > reference.error_count:
        issues.append(
            f"checkpoint errors regressed: current={current.error_count}, reference={reference.error_count}"
        )

    if current.compile_overall_with_test < reference.compile_overall_with_test:
        issues.append(
            "compile pass rate with tests regressed: "
            f"current={current.compile_overall_with_test:.2f}, "
            f"reference={reference.compile_overall_with_test:.2f}"
        )

    if current.compile_overall_without_test < reference.compile_overall_without_test:
        issues.append(
            "compile pass rate without tests regressed: "
            f"current={current.compile_overall_without_test:.2f}, "
            f"reference={reference.compile_overall_without_test:.2f}"
        )

    if current.once_overall < reference.once_overall:
        issues.append(
            f"once pass rate regressed: current={current.once_overall:.2f}, reference={reference.once_overall:.2f}"
        )

    return SmokeComparison(
        ok=not issues,
        issues=tuple(issues),
        current=current,
        reference=reference,
        result_count_deltas=_result_count_deltas(current.result_counts, reference.result_counts),
    )


def validate_exported_project(
    project_dir: Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> tuple[CargoCommandResult, ...]:
    """Run the standard exported Cargo project validation commands."""

    results: list[CargoCommandResult] = []
    for command in CARGO_EXPORT_VALIDATION_COMMANDS:
        completed = runner(
            command,
            cwd=project_dir,
            text=True,
            capture_output=True,
            check=False,
        )
        result = CargoCommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        results.append(result)
        if result.returncode != 0:
            break
    return tuple(results)


def run_reference_aligned_arraylist_smoke(
    *,
    tool_py_root: Path,
    base_config_path: Path,
    derived_config_path: Path,
    output_root: Path,
    reference_output_dir: Path,
    python_executable: str = sys.executable,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    clean_output: bool = False,
) -> ReferenceAlignedSmokeRunResult:
    """Run the reference-aligned arraylist smoke workflow.

    The expensive command runner is injectable so unit tests can verify the
    orchestration contract without calling real LLM APIs or Cargo. Production
    callers use the default `subprocess.run`.
    """

    tool_py_root = tool_py_root.resolve()
    base_config_path = base_config_path.resolve()
    derived_config_path = derived_config_path.resolve()
    output_root = output_root.resolve()
    reference_output_dir = reference_output_dir.resolve()

    if clean_output and output_root.exists():
        if output_root.is_dir():
            shutil.rmtree(output_root)
        else:
            output_root.unlink()

    config = write_reference_aligned_arraylist_config(
        base_config_path=base_config_path,
        destination_config_path=derived_config_path,
        output_root=output_root,
    )
    command_results: list[SmokeCommandResult] = []
    issues: list[str] = []

    for command in (
        (python_executable, str(tool_py_root / "makejson.py"), str(derived_config_path)),
        (python_executable, str(tool_py_root / "src" / "main.py"), str(derived_config_path)),
    ):
        result = _run_smoke_command(command, cwd=tool_py_root, runner=runner)
        command_results.append(result)
        if result.returncode != 0:
            issues.append(_failed_command_issue(result))
            return ReferenceAlignedSmokeRunResult(
                ok=False,
                issues=tuple(issues),
                config=config,
                command_results=tuple(command_results),
                comparison=None,
                cargo_results=(),
            )

    comparison = compare_smoke_outputs(config.output_dir, reference_output_dir)
    issues.extend(comparison.issues)

    verify_project_dir = config.output_dir / "verify_project"
    if not verify_project_dir.exists():
        issues.append(f"missing exported Cargo project: {verify_project_dir}")
        cargo_results: tuple[CargoCommandResult, ...] = ()
    else:
        cargo_results = validate_exported_project(verify_project_dir, runner=runner)
        for result in cargo_results:
            if result.returncode != 0:
                issues.append(_failed_cargo_issue(result, verify_project_dir))
                break

    return ReferenceAlignedSmokeRunResult(
        ok=not issues,
        issues=tuple(issues),
        config=config,
        command_results=tuple(command_results),
        comparison=comparison,
        cargo_results=cargo_results,
    )


def _load_smoke_output_summary(output_dir: Path) -> SmokeOutputSummary:
    checkpoint = _read_json_object(output_dir / "checkpoint.json")
    results = _read_json_object(output_dir / "results.json")
    _read_json_object(output_dir / "all_error_funcs_content.json")
    compile_overall = _read_overall_row(_resolve_metric_file(output_dir, "compile_pass_rate.csv"))
    once_overall = _read_overall_row(_resolve_metric_file(output_dir, "once_pass_rates.csv"))

    result_counts = {str(source): _result_count(value) for source, value in results.items()}
    checkpoint_error_count = int(checkpoint.get("total_error_count", 0))
    return SmokeOutputSummary(
        output_dir=output_dir,
        checkpoint_stats={
            "total_retry_count": int(checkpoint.get("total_retry_count", 0)),
            "total_regenerate_count": int(checkpoint.get("total_regenerate_count", 0)),
            "total_error_count": checkpoint_error_count,
        },
        result_counts=result_counts,
        result_sources=frozenset(result_counts),
        error_count=checkpoint_error_count,
        compile_overall_with_test=_percent_to_float(compile_overall.get("Pass Rate (with test)", "0")),
        compile_overall_without_test=_percent_to_float(compile_overall.get("Pass Rate (without test)", "0")),
        once_overall=_percent_to_float(once_overall.get("Pass Rate", "0")),
    )


def _run_smoke_command(
    command: tuple[str, ...],
    *,
    cwd: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> SmokeCommandResult:
    completed = runner(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    return SmokeCommandResult(
        command=command,
        cwd=cwd,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _failed_command_issue(result: SmokeCommandResult) -> str:
    detail = (result.stderr or result.stdout).strip()
    command = " ".join(result.command)
    if detail:
        return f"command failed ({result.returncode}): {command}: {detail}"
    return f"command failed ({result.returncode}): {command}"


def _failed_cargo_issue(result: CargoCommandResult, project_dir: Path) -> str:
    detail = (result.stderr or result.stdout).strip()
    command = " ".join(result.command)
    if detail:
        return f"cargo validation failed in {project_dir} ({result.returncode}): {command}: {detail}"
    return f"cargo validation failed in {project_dir} ({result.returncode}): {command}"


def _result_count_deltas(
    current_counts: Mapping[str, int],
    reference_counts: Mapping[str, int],
) -> dict[str, tuple[int, int]]:
    deltas: dict[str, tuple[int, int]] = {}
    for source in sorted(set(current_counts) | set(reference_counts)):
        current = current_counts.get(source, 0)
        reference = reference_counts.get(source, 0)
        if current != reference:
            deltas[source] = (current, reference)
    return deltas


def _read_json_object(path: Path) -> Mapping[str, object]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def _resolve_metric_file(output_dir: Path, filename: str) -> Path:
    """Resolve metrics across the new organized layout and old smoke outputs."""

    preferred = output_dir / "metrics" / filename
    if preferred.exists():
        return preferred
    return output_dir / filename


def _read_overall_row(path: Path) -> Mapping[str, str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("Source") == "Overall":
                return row
    raise ValueError(f"missing Overall row in {path}")


def _result_count(value: object) -> int:
    if isinstance(value, Mapping):
        return len(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value)
    return 1 if value else 0


def _percent_to_float(value: object) -> float:
    text = str(value).strip()
    if text.endswith("%"):
        text = text[:-1]
    return float(text or 0.0)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _comparison_to_dict(comparison: SmokeComparison) -> dict[str, object]:
    data = asdict(comparison)
    data["current"]["output_dir"] = str(comparison.current.output_dir)
    data["current"]["result_sources"] = sorted(comparison.current.result_sources)
    data["reference"]["output_dir"] = str(comparison.reference.output_dir)
    data["reference"]["result_sources"] = sorted(comparison.reference.result_sources)
    return data


def _run_result_to_dict(result: ReferenceAlignedSmokeRunResult) -> dict[str, object]:
    data = asdict(result)
    data["config"]["config_path"] = str(result.config.config_path)
    data["config"]["tmp_dir"] = str(result.config.tmp_dir)
    data["config"]["output_dir"] = str(result.config.output_dir)
    for command_result in data["command_results"]:
        command_result["cwd"] = str(command_result["cwd"])
    if result.comparison is not None:
        data["comparison"] = _comparison_to_dict(result.comparison)
    return data


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tool_py real smoke helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    derive = subparsers.add_parser("derive-arraylist-config")
    derive.add_argument("--base", required=True, type=Path)
    derive.add_argument("--dest", required=True, type=Path)
    derive.add_argument("--output-root", required=True, type=Path)

    compare = subparsers.add_parser("compare")
    compare.add_argument("--current-output", required=True, type=Path)
    compare.add_argument("--reference-output", required=True, type=Path)

    validate = subparsers.add_parser("validate-export")
    validate.add_argument("--project-dir", required=True, type=Path)

    run = subparsers.add_parser("run-arraylist-reference-smoke")
    run.add_argument("--tool-py-root", required=True, type=Path)
    run.add_argument("--base-config", required=True, type=Path)
    run.add_argument("--derived-config", required=True, type=Path)
    run.add_argument("--output-root", required=True, type=Path)
    run.add_argument("--reference-output", required=True, type=Path)
    run.add_argument("--python", default=sys.executable)
    run.add_argument("--clean-output", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "derive-arraylist-config":
        result = write_reference_aligned_arraylist_config(
            base_config_path=args.base,
            destination_config_path=args.dest,
            output_root=args.output_root,
        )
        print(json.dumps({"config_path": str(result.config_path), "tmp_dir": str(result.tmp_dir), "output_dir": str(result.output_dir)}))
        return 0

    if args.command == "compare":
        comparison = compare_smoke_outputs(args.current_output, args.reference_output)
        print(json.dumps(_comparison_to_dict(comparison), ensure_ascii=False, indent=2))
        return 0 if comparison.ok else 1

    if args.command == "validate-export":
        results = validate_exported_project(args.project_dir)
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
        return 0 if all(result.returncode == 0 for result in results) else 1

    if args.command == "run-arraylist-reference-smoke":
        result = run_reference_aligned_arraylist_smoke(
            tool_py_root=args.tool_py_root,
            base_config_path=args.base_config,
            derived_config_path=args.derived_config,
            output_root=args.output_root,
            reference_output_dir=args.reference_output,
            python_executable=args.python,
            clean_output=args.clean_output,
        )
        print(json.dumps(_run_result_to_dict(result), ensure_ascii=False, indent=2))
        return 0 if result.ok else 1

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
