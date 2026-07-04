#!/usr/bin/env python3
import argparse
import ast
import json
import os
from collections import defaultdict

from clang_callgraph import clang_callgraph
from merge_c_h import process_compile_commands, process_files
from metrics import calculate_compile_pass_rates, calculate_retry_pass_rates
from parse_config import read_config, setup_project_directories
from src.data_manager import DataManager


def _write_normalized_compile_commands(compile_commands_path: str, tmp_dir: str) -> str:
    os.makedirs(tmp_dir, exist_ok=True)
    normalized_path = os.path.join(tmp_dir, "compile_commands.normalized.json")
    compile_commands = process_compile_commands(compile_commands_path, write_back=False)
    with open(normalized_path, "w", encoding="utf-8") as f:
        json.dump(compile_commands, f, indent=4)
    return normalized_path


def _extract_target_sources_from_app_log(output_dir: str):
    app_log_path = os.path.join(output_dir, "app.log")
    if not os.path.exists(app_log_path):
        return []

    try:
        with open(app_log_path, "r", encoding="utf-8") as f:
            for line in f:
                marker = "[TARGET-SOURCES] only process:"
                if marker not in line:
                    continue
                raw = line.split(marker, 1)[1].strip()
                if not raw:
                    return []
                parsed = ast.literal_eval(raw)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
                return []
    except Exception:
        return []

    return []


def recompute_for_config(config_path: str) -> None:
    cfg = read_config(config_path)
    tmp_dir, output_dir, _output_project_path, compile_commands_path, _params, excluded_files = setup_project_directories(cfg)

    normalized_compile_commands_path = _write_normalized_compile_commands(compile_commands_path, tmp_dir)
    include_dict, all_file_paths = process_files(normalized_compile_commands_path, tmp_dir)

    test_json_dir = os.path.join(tmp_dir, "test_json")
    src_json_dir = os.path.join(tmp_dir, "src_json")
    test_path = [os.path.join(test_json_dir, f) for f in os.listdir(test_json_dir)]
    src_path = [os.path.join(src_json_dir, f) for f in os.listdir(src_json_dir)]

    test_names = [os.path.splitext(os.path.basename(f))[0] for f in test_path]
    src_names = [os.path.splitext(os.path.basename(f))[0] for f in src_path]

    source_path = list(test_path)
    source_path.extend(src_path)

    has_test = (cfg["Paths"].get("test_dir", "") != "")
    if not has_test:
        for test_name in test_names:
            include_dict[test_name] = src_names

    sorted_funcs_depth, _funcs_childs, include_dict, include_dict_without_fn_pointer, all_pointer_funcs = clang_callgraph(
        normalized_compile_commands_path,
        include_dict,
        all_file_paths,
        has_test=has_test,
    )

    uncovered_test_names = []
    for key in include_dict.keys():
        if key.startswith("test-uncovered_"):
            source_file = key.replace("test-uncovered_", "")
            if source_file not in excluded_files:
                uncovered_test_names.append(key)
    test_names.extend(uncovered_test_names)

    if not has_test:
        for test_name in test_names:
            include_dict[test_name] = src_names

    data_manager = DataManager(source_path, include_dict, all_pointer_funcs, include_dict_without_fn_pointer, has_test=has_test)

    results = defaultdict(dict)
    once_retry_count_dict = defaultdict(dict)

    results_path = os.path.join(output_dir, "results.json")
    retry_path = os.path.join(output_dir, "once_retry_count_dict.json")

    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            results = json.load(f)

    if os.path.exists(retry_path):
        with open(retry_path, "r", encoding="utf-8") as f:
            once_retry_count_dict = json.load(f)

    active_test_names = _extract_target_sources_from_app_log(output_dir)
    if not active_test_names:
        active_test_names = [name for name in test_names if name not in set(excluded_files)]

    print(f"Active targets for metrics: {active_test_names}")

    calculate_compile_pass_rates(
        output_dir,
        results,
        sorted_funcs_depth,
        data_manager,
        active_test_names,
    )
    calculate_retry_pass_rates(
        output_dir,
        results,
        include_dict,
        once_retry_count_dict,
        active_test_names,
    )

    print(f"Updated: {os.path.join(output_dir, 'compile_pass_rate.csv')}")
    print(f"Updated: {os.path.join(output_dir, 'once_pass_rates.csv')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute compile/once metrics from existing outputs")
    parser.add_argument("configs", nargs="+", help="One or more .ini config paths")
    args = parser.parse_args()

    for config_path in args.configs:
        print(f"=== Recompute metrics: {config_path} ===")
        recompute_for_config(config_path)

    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
