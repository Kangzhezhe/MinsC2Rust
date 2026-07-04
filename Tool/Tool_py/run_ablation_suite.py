#!/usr/bin/env python3
import argparse
import csv
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

from parse_config import read_config


ABLATION_FLAGS = {
    "ablation_no_context": "0",
    "ablation_no_constraints": "0",
    "ablation_disable_feedback_loop": "0",
    "ablation_random_order": "0",
}

VARIANT_MAP: Dict[str, Dict[str, str]] = {
    "full": {},
    "no_context": {"ablation_no_context": "1"},
    "no_constraints": {"ablation_no_constraints": "1"},
    "no_feedback": {"ablation_disable_feedback_loop": "1"},
    "random_order": {"ablation_random_order": "1"},
}

PYTHON_BIN = sys.executable or "python3"
FAST_ABLATION_MAX_RETRIES = 6
FAST_ABLATION_MAX_REGENERATIONS = 2


def _resolve_path(raw: str, work_dir: Path) -> Path:
    p = Path(str(raw).strip())
    if p.is_absolute():
        return p
    return (work_dir / p).resolve()


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


def _normalize_variants(raw: str) -> List[str]:
    parts = [x.strip() for x in str(raw or "").split(",") if x.strip()]
    if not parts:
        return ["full", "no_context", "no_constraints", "no_feedback", "random_order"]

    normalized = []
    for item in parts:
        if item not in VARIANT_MAP:
            raise ValueError(
                f"Unknown variant '{item}'. Valid variants: {', '.join(sorted(VARIANT_MAP.keys()))}"
            )
        normalized.append(item)
    return normalized


def _prepare_variant_config(
    base_config_path: Path,
    work_dir: Path,
    variants_root: Path,
    variant: str,
    max_retries: int,
    max_regenerations: int,
) -> Tuple[Path, Path, Path]:
    cfg = read_config(str(base_config_path))
    cfg.remove_section("Config")

    if "Paths" not in cfg:
        raise ValueError(f"Invalid config: missing [Paths], file={base_config_path}")
    if "Params" not in cfg:
        cfg["Params"] = {}

    base_output_dir = _resolve_path(cfg["Paths"].get("output_dir", "./Output"), work_dir)
    benchmark_root = base_output_dir.parent
    variant_root = benchmark_root / "ablation" / variant
    output_dir = variant_root / "Output"
    tmp_dir = variant_root / "tmp"
    func_result_dir = variant_root / "func_result"

    cfg["Paths"]["output_dir"] = str(output_dir)
    cfg["Paths"]["tmp_dir"] = str(tmp_dir)
    cfg["Paths"]["func_result_dir"] = str(func_result_dir)

    for key in ["src_dir", "test_dir", "compile_commands_path"]:
        if key in cfg["Paths"]:
            cfg["Paths"][key] = str(_resolve_path(cfg["Paths"][key], work_dir))

    for flag_key, default_val in ABLATION_FLAGS.items():
        cfg["Params"][flag_key] = default_val
    # Ablation suite defaults to smaller retry/regen limits for faster convergence.
    cfg["Params"]["max_retries"] = str(max(1, int(max_retries)))
    cfg["Params"]["max_regenerations"] = str(max(1, int(max_regenerations)))
    cfg["Params"]["export_verify_project"] = "1"

    for k, v in VARIANT_MAP[variant].items():
        cfg["Params"][k] = v

    generated_dir = variants_root / "generated_configs"
    generated_dir.mkdir(parents=True, exist_ok=True)
    generated_cfg_path = generated_dir / f"{variant}.ini"
    with generated_cfg_path.open("w", encoding="utf-8") as f:
        cfg.write(f)

    return generated_cfg_path, variant_root, output_dir


def _run_subprocess(cmd: List[str], cwd: Path, env: Dict[str, str]) -> Tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _run_variant(
    variant: str,
    cfg_path: Path,
    variant_root: Path,
    output_dir: Path,
    work_dir: Path,
    target_sources: str,
) -> Dict[str, str]:
    start = time.time()
    result = {
        "variant": variant,
        "status": "failed",
        "duration_sec": "0",
        "compile_with_test": "",
        "compile_without_test": "",
        "once_pass": "",
        "safe_loc": "",
        "safe_ref": "",
        "output_dir": str(output_dir),
        "config_path": str(cfg_path),
        "error": "",
    }

    if variant_root.exists():
        shutil.rmtree(variant_root, ignore_errors=True)
    variant_root.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    if target_sources:
        env["TARGET_TEST_SOURCES"] = target_sources

    logs: List[str] = []

    # makejson.py writes directly into func_result_dir; ensure all runtime dirs exist.
    cfg = read_config(str(cfg_path))
    variant_output_dir = _resolve_path(cfg["Paths"].get("output_dir", str(output_dir)), work_dir)
    variant_tmp_dir = _resolve_path(cfg["Paths"].get("tmp_dir", str(variant_root / "tmp")), work_dir)
    variant_func_result_dir = _resolve_path(
        cfg["Paths"].get("func_result_dir", str(variant_root / "func_result")),
        work_dir,
    )
    variant_output_dir.mkdir(parents=True, exist_ok=True)
    variant_tmp_dir.mkdir(parents=True, exist_ok=True)
    variant_func_result_dir.mkdir(parents=True, exist_ok=True)

    rc, out, err = _run_subprocess([PYTHON_BIN, "makejson.py", str(cfg_path)], cwd=work_dir, env=env)
    logs.append("[makejson stdout]\n" + out)
    logs.append("[makejson stderr]\n" + err)
    if rc != 0:
        result["error"] = f"makejson failed with exit code {rc}"
        result["duration_sec"] = f"{time.time() - start:.1f}"
        (output_dir / "run.log").parent.mkdir(parents=True, exist_ok=True)
        (output_dir / "run.log").write_text("\n\n".join(logs), encoding="utf-8")
        return result

    rc, out, err = _run_subprocess([PYTHON_BIN, "src/main.py", str(cfg_path)], cwd=work_dir, env=env)
    logs.append("[main stdout]\n" + out)
    logs.append("[main stderr]\n" + err)
    (output_dir / "run.log").parent.mkdir(parents=True, exist_ok=True)
    (output_dir / "run.log").write_text("\n\n".join(logs), encoding="utf-8")

    if rc != 0:
        result["error"] = f"main.py failed with exit code {rc}"
        result["duration_sec"] = f"{time.time() - start:.1f}"
        return result

    compile_csv = output_dir / "compile_pass_rate.csv"
    once_csv = output_dir / "once_pass_rates.csv"

    result["compile_with_test"] = _read_overall_value(compile_csv, "Pass Rate (with test)")
    result["compile_without_test"] = _read_overall_value(compile_csv, "Pass Rate (without test)")
    result["once_pass"] = _read_overall_value(once_csv, "Pass Rate")

    compile_total_wo_test = _read_overall_int(compile_csv, "Total count (without test)")
    once_total = _read_overall_int(once_csv, "Total Count")
    if compile_total_wo_test == 0 or once_total == 0:
        reasons: List[str] = []
        if compile_total_wo_test == 0:
            reasons.append("compile total(without test)=0")
        if once_total == 0:
            reasons.append("once-pass total=0")
        result["error"] = "invalid metrics: " + ", ".join(reasons)
        result["duration_sec"] = f"{time.time() - start:.1f}"
        return result

    verify_src_dir = output_dir / "verify_project" / "src"
    if verify_src_dir.exists() and any(verify_src_dir.glob("*.rs")):
        safety_csv = output_dir / "safety.csv"
        rc_s, out_s, err_s = _run_subprocess(
            [PYTHON_BIN, "test_unsafe.py", str(verify_src_dir), str(safety_csv)],
            cwd=work_dir,
            env=env,
        )
        with (output_dir / "safety.log").open("w", encoding="utf-8") as f:
            f.write("[safety stdout]\n" + out_s + "\n\n[safety stderr]\n" + err_s)
        if rc_s == 0:
            result["safe_loc"] = _read_overall_value(safety_csv, "Safe Loc")
            result["safe_ref"] = _read_overall_value(safety_csv, "Safe Ref")

    result["status"] = "ok"
    result["duration_sec"] = f"{time.time() - start:.1f}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MinsC2Rust ablation variants in parallel")
    parser.add_argument(
        "--base-config",
        required=True,
        help="Path to base ini config, e.g. configs/config_c_algorithm.ini",
    )
    parser.add_argument(
        "--variants",
        default="full,no_context,no_constraints,no_feedback,random_order",
        help="Comma-separated variant names",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=2,
        help="Max number of variants to run in parallel",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=FAST_ABLATION_MAX_RETRIES,
        help="Override Params.max_retries for ablation runs (smaller is faster)",
    )
    parser.add_argument(
        "--max-regenerations",
        type=int,
        default=FAST_ABLATION_MAX_REGENERATIONS,
        help="Override Params.max_regenerations for ablation runs (smaller is faster)",
    )
    parser.add_argument(
        "--target-sources",
        default="",
        help="Optional TARGET_TEST_SOURCES override, comma-separated",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    work_dir = script_path.parent.resolve()

    base_config_path = Path(args.base_config).expanduser().resolve()
    if not base_config_path.exists():
        print(f"Base config not found: {base_config_path}")
        return 1

    variants = _normalize_variants(args.variants)

    base_cfg = read_config(str(base_config_path))
    if "Paths" not in base_cfg:
        print(f"Invalid config: missing [Paths], file={base_config_path}")
        return 1

    base_output_dir = _resolve_path(base_cfg["Paths"].get("output_dir", "./Output"), work_dir)
    variants_root = base_output_dir.parent / "ablation"
    variants_root.mkdir(parents=True, exist_ok=True)

    tasks: List[Tuple[str, Path, Path, Path]] = []
    for variant in variants:
        cfg_path, variant_root, output_dir = _prepare_variant_config(
            base_config_path=base_config_path,
            work_dir=work_dir,
            variants_root=variants_root,
            variant=variant,
            max_retries=args.max_retries,
            max_regenerations=args.max_regenerations,
        )
        tasks.append((variant, cfg_path, variant_root, output_dir))

    print(
        "Ablation fast settings: "
        f"max_retries={max(1, int(args.max_retries))}, "
        f"max_regenerations={max(1, int(args.max_regenerations))}"
    )

    results: List[Dict[str, str]] = []
    max_workers = max(1, int(args.parallel))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _run_variant,
                variant,
                cfg_path,
                variant_root,
                output_dir,
                work_dir,
                args.target_sources.strip(),
            ): variant
            for variant, cfg_path, variant_root, output_dir in tasks
        }
        for future in as_completed(future_map):
            results.append(future.result())

    results.sort(key=lambda x: x.get("variant", ""))

    summary_path = variants_root / "ablation_summary.csv"
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
        writer.writerows(results)

    print(f"Ablation summary saved to: {summary_path}")
    for row in results:
        msg = (
            f"[{row['variant']}] status={row['status']} "
            f"compile_with_test={row['compile_with_test']} "
            f"compile={row['compile_without_test']} once={row['once_pass']} "
            f"safe_loc={row['safe_loc']} safe_ref={row['safe_ref']}"
        )
        if row.get("status") != "ok" and row.get("error"):
            msg += f" error={row['error']}"
        print(msg)

    failed = [r for r in results if r.get("status") != "ok"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
