#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path
from typing import Dict, List


DEFAULT_VARIANTS = ["full", "no_context", "no_constraints", "no_feedback", "random_order"]


def _read_overall_value(csv_path: Path, column: str) -> str:
    if not csv_path.exists():
        return ""

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fallback = ""
        for row in reader:
            if row.get("Source", "") == "Overall":
                return str(row.get(column, "") or "").strip()
            fallback = str(row.get(column, "") or "").strip()
        return fallback


def _read_overall_int(csv_path: Path, column: str) -> int:
    raw = _read_overall_value(csv_path, column)
    if raw == "":
        return -1
    try:
        return int(raw)
    except ValueError:
        try:
            return int(float(raw))
        except ValueError:
            return -1


def _read_existing_summary(summary_path: Path) -> Dict[str, Dict[str, str]]:
    if not summary_path.exists():
        return {}

    with summary_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {str(row.get("variant", "")).strip(): row for row in reader}


def recompute_ablation_summary(ablation_root: Path, variants: List[str]) -> Path:
    summary_path = ablation_root / "ablation_summary.csv"
    existing_map = _read_existing_summary(summary_path)

    rows = []
    for variant in variants:
        output_dir = ablation_root / variant / "Output"
        compile_csv = output_dir / "compile_pass_rate.csv"
        once_csv = output_dir / "once_pass_rates.csv"
        safety_csv = output_dir / "safety.csv"
        config_path = ablation_root / "generated_configs" / f"{variant}.ini"

        compile_with_test = _read_overall_value(compile_csv, "Pass Rate (with test)")
        compile_without_test = _read_overall_value(compile_csv, "Pass Rate (without test)")
        once_pass = _read_overall_value(once_csv, "Pass Rate")
        safe_loc = _read_overall_value(safety_csv, "Safe Loc")
        safe_ref = _read_overall_value(safety_csv, "Safe Ref")

        compile_total_wo_test = _read_overall_int(compile_csv, "Total count (without test)")
        once_total = _read_overall_int(once_csv, "Total Count")

        existing = existing_map.get(variant, {})
        duration_sec = str(existing.get("duration_sec", "") or "")

        status = "ok"
        error = ""

        if not compile_csv.exists() or not once_csv.exists():
            status = "failed"
            missing = []
            if not compile_csv.exists():
                missing.append("compile_pass_rate.csv")
            if not once_csv.exists():
                missing.append("once_pass_rates.csv")
            error = "missing metrics files: " + ", ".join(missing)
        elif compile_total_wo_test == 0 or once_total == 0:
            status = "failed"
            reasons = []
            if compile_total_wo_test == 0:
                reasons.append("compile total(without test)=0")
            if once_total == 0:
                reasons.append("once-pass total=0")
            error = "invalid metrics: " + ", ".join(reasons)

        row = {
            "variant": variant,
            "status": status,
            "duration_sec": duration_sec,
            "compile_with_test": compile_with_test,
            "compile_without_test": compile_without_test,
            "once_pass": once_pass,
            "safe_loc": safe_loc,
            "safe_ref": safe_ref,
            "output_dir": str(output_dir),
            "config_path": str(config_path),
            "error": error,
        }
        rows.append(row)

    with summary_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "variant",
            "status",
            "duration_sec",
            "compile_with_test",
            "compile_without_test",
            "once_pass",
            "safe_loc",
            "safe_ref",
            "output_dir",
            "config_path",
            "error",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return summary_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute ablation_summary.csv from existing variant outputs")
    parser.add_argument(
        "--ablation-root",
        required=True,
        help="Path to ablation root directory, e.g. Output/c_algorithm/ablation",
    )
    parser.add_argument(
        "--variants",
        default=",".join(DEFAULT_VARIANTS),
        help="Comma-separated variants to include",
    )
    args = parser.parse_args()

    ablation_root = Path(args.ablation_root).expanduser().resolve()
    variants = [x.strip() for x in str(args.variants).split(",") if x.strip()]
    summary_path = recompute_ablation_summary(ablation_root, variants)

    print(f"Updated: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
