import atexit
import asyncio
import json
import os
import random
import sys
import time
from typing import Dict, List, Optional, Set, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from cargo_verifier import CargoVerifier
from clang_callgraph import clang_callgraph
from data_manager import DataManager
from logger import logger_init
from merge_c_h import process_compile_commands, process_files
from metrics import (
    calculate_compile_pass_rates,
    calculate_retry_pass_rates,
    configure_metric_excluded_functions,
)
from models.llm_model import generate_response
from pipeline.checkpoint import load_checkpoint, save_checkpoint
from pipeline.run_report import generate_translation_report
from pipeline.translation_pipeline import (
    TranslationPipeline,
    _apply_pipeline_stats,
    _current_pipeline_stats,
)
from pipeline.stats import set_error_count
from parse_config import read_config, setup_project_directories


def active_error_count(all_error_funcs_content) -> int:
    return sum(
        len(funcs)
        for funcs in (all_error_funcs_content or {}).values()
        if isinstance(funcs, dict)
    )


def resolve_source_paths(tmp_dir: str, excluded_files: List[str]) -> Tuple[List[str], List[str], List[str], List[str]]:
    test_json_dir = os.path.join(tmp_dir, "test_json")
    src_json_dir = os.path.join(tmp_dir, "src_json")

    test_paths = [os.path.join(test_json_dir, f) for f in os.listdir(test_json_dir)]
    src_paths = [os.path.join(src_json_dir, f) for f in os.listdir(src_json_dir)]

    test_names = [os.path.splitext(os.path.basename(f))[0] for f in test_paths]
    src_names = [os.path.splitext(os.path.basename(f))[0] for f in src_paths]

    source_paths = test_paths + src_paths
    source_names = [os.path.splitext(os.path.basename(p))[0] for p in source_paths]
    return source_paths, source_names, src_names, test_names


async def main():
    if len(sys.argv) != 2:
        print("Usage: python src/main.py <config_path>")
        sys.exit(1)

    config_path = sys.argv[1]
    cfg = read_config(config_path)
    tmp_dir, output_dir, output_project_path, compile_commands_path, params, excluded_files = setup_project_directories(cfg)
    normalized_compile_commands_path = os.path.join(tmp_dir, "compile_commands.normalized.json")
    compile_commands = process_compile_commands(compile_commands_path, write_back=False)
    with open(normalized_compile_commands_path, "w", encoding="utf-8") as f:
        json.dump(compile_commands, f, indent=4)

    llm_model = params.get('model', 'qwen')
    configure_metric_excluded_functions(params)

    include_dict, all_file_paths = process_files(normalized_compile_commands_path, tmp_dir)
    source_paths, source_names, src_names, test_names = resolve_source_paths(tmp_dir, excluded_files)

    has_test = cfg["Paths"].get("test_dir", "") != ""
    if not has_test:
        for test_name in test_names:
            include_dict[test_name] = src_names

    sorted_funcs_depth, funcs_childs, include_dict, include_dict_without_fn_pointer, all_pointer_funcs = clang_callgraph(
        normalized_compile_commands_path,
        include_dict,
        all_file_paths,
        has_test=has_test,
    )

    logger = logger_init(os.path.join(output_dir, "app.log"))
    data_manager = DataManager(
        source_paths,
        include_dict=include_dict,
        all_pointer_funcs=all_pointer_funcs,
        include_dict_without_fn_pointer=include_dict_without_fn_pointer,
        has_test=has_test,
    )

    ownership_index_path = os.path.join(output_dir, "ownership_non_function_index.json")
    ownership_suggestions: Dict[str, List[str]] = {}
    if os.path.exists(ownership_index_path):
        try:
            with open(ownership_index_path, "r", encoding="utf-8") as f:
                ownership_payload = json.load(f)
            suggestions = ownership_payload.get("suggestions", {}) if isinstance(ownership_payload, dict) else {}
            if isinstance(suggestions, dict):
                for key, value in suggestions.items():
                    if not isinstance(value, str):
                        continue
                    if "::" in key:
                        ownership_suggestions[key] = [value]
                    else:
                        ownership_suggestions[f"{key}::*"] = [value]
        except Exception:
            ownership_suggestions = {}

    checkpoint_state = load_checkpoint(output_dir)
    results = checkpoint_state.results
    once_retry_count_dict = checkpoint_state.once_retry_count_dict
    all_error_funcs_content = checkpoint_state.all_error_funcs_content
    dependency_overrides = checkpoint_state.dependency_overrides
    pending_accepted = checkpoint_state.pending_accepted
    runtime_status = checkpoint_state.runtime_status
    source_runtime_status = checkpoint_state.source_runtime_status
    source_runtime_pass_cache = checkpoint_state.source_runtime_pass_cache
    repair_records = checkpoint_state.repair_records
    _apply_pipeline_stats(checkpoint_state.stats)
    keep_sandbox_on_failure = bool(int(params.get("keep_sandbox_on_failure", 0)))
    verify_timeout_seconds = int(params.get("verify_timeout_seconds", 60))
    verify_cache_enabled = bool(int(params.get("verify_cache_enabled", 1)))
    verifier = CargoVerifier(
        base_tmp_dir=tmp_dir,
        keep_sandbox_on_failure=keep_sandbox_on_failure,
        verify_timeout_seconds=verify_timeout_seconds,
        verify_cache_enabled=verify_cache_enabled,
    )
    verifier.dependency_overrides = dict(dependency_overrides)

    def checkpoint_hook():
        pipeline.sync_archive_imports(results)
        set_error_count(active_error_count(all_error_funcs_content))
        save_checkpoint(
            results,
            once_retry_count_dict,
            all_error_funcs_content,
            output_dir,
            stats=_current_pipeline_stats(),
            dependency_overrides=pipeline.project_dependency_overrides,
            pending_accepted=pending_accepted,
            runtime_status=runtime_status,
            source_runtime_status=source_runtime_status,
            source_runtime_pass_cache=source_runtime_pass_cache,
            repair_records=repair_records,
        )

    pipeline = TranslationPipeline(
        data_manager=data_manager,
        source_names=source_names,
        funcs_childs=funcs_childs,
        logger=logger,
        llm_model=llm_model,
        verifier=verifier,
        params=params,
        checkpoint_hook=checkpoint_hook,
        ownership_suggestions=ownership_suggestions,
        excluded_sources=set(excluded_files),
        output_dir=output_dir,
        pending_accepted=pending_accepted,
        runtime_status=runtime_status,
        source_runtime_status=source_runtime_status,
        source_runtime_pass_cache=source_runtime_pass_cache,
        repair_records=repair_records,
    )
    pipeline.project_dependency_overrides = dict(dependency_overrides)
    pipeline._sync_dependency_overrides_to_verifier()
    atexit.register(pipeline.close)

    start_time = time.time()
    elapsed_time: Optional[float] = None
    try:
        target_sources_env = os.getenv("TARGET_TEST_SOURCES", "").strip()
        target_sources = {
            x.strip() for x in target_sources_env.split(",") if x.strip()
        }
        excluded_source_set = set(excluded_files)

        def _is_excluded_target_source(source_name: str) -> bool:
            if source_name in excluded_source_set:
                return True
            if source_name.startswith("test-uncovered_"):
                base_source = source_name.replace("test-uncovered_", "", 1)
                if base_source in excluded_source_set:
                    return True
                if f"test-{base_source}" in excluded_source_set:
                    return True
            return False

        default_target_sources = {
            name for name in sorted_funcs_depth.keys() if not _is_excluded_target_source(name)
        }
        filtered_test_names = [name for name in test_names if name not in excluded_source_set]

        ordered_sources = list(sorted_funcs_depth.items())
        if target_sources:
            active_target_sources = {
                name for name in target_sources if not _is_excluded_target_source(name)
            }
            dropped_target_sources = sorted(target_sources - active_target_sources)
            if dropped_target_sources:
                logger.info(
                    "[TARGET-SOURCES] drop excluded targets: "
                    + ",".join(dropped_target_sources)
                )
        else:
            active_target_sources = default_target_sources

        ordered_sources = [
            (name, depth)
            for name, depth in ordered_sources
            if name in active_target_sources and not _is_excluded_target_source(name)
        ]
        if target_sources:
            logger.info(f"[TARGET-SOURCES] only process: {sorted(active_target_sources)}")
        else:
            logger.info(
                "[TARGET-SOURCES] skip top-level excluded modules: "
                + ",".join(sorted(excluded_source_set))
            )

        if pipeline.ablation_random_order:
            rng = random.Random(pipeline.ablation_random_seed)
            rng.shuffle(ordered_sources)
            logger.info(
                "[SOURCE-ORDER] random order seed=%d order=%s"
                % (
                    pipeline.ablation_random_seed,
                    ",".join(name for name, _ in ordered_sources[:20]),
                )
            )
        else:
            # Dependency-first scheduling across modules: translate providers before callers.
            source_name_set = {name for name, _ in ordered_sources}
            dep_depth_cache: Dict[str, int] = {}
            dep_depth_visiting: Set[str] = set()

            def _dependency_depth(source_name: str) -> int:
                cached = dep_depth_cache.get(source_name)
                if cached is not None:
                    return cached
                if source_name in dep_depth_visiting:
                    return 0

                dep_depth_visiting.add(source_name)
                max_depth = 0
                for dep in include_dict.get(source_name, []) or []:
                    if dep not in source_name_set or dep == source_name:
                        continue
                    max_depth = max(max_depth, _dependency_depth(dep) + 1)
                dep_depth_visiting.remove(source_name)
                dep_depth_cache[source_name] = max_depth
                return max_depth

            # Keep convergence signal (historical failures), but only inside the same dependency layer.
            ordered_sources.sort(
                key=lambda kv: (
                    _dependency_depth(kv[0]),
                    -len(all_error_funcs_content.get(kv[0], {})),
                ),
            )
            logger.info(
                "[SOURCE-ORDER] dependency-first order="
                + ",".join(
                    f"{name}(d={_dependency_depth(name)},err={len(all_error_funcs_content.get(name, {}))})"
                    for name, _ in ordered_sources[:20]
                )
            )

        for test_source_name, funcs_depth in ordered_sources:
            pipeline.process_test_source(
                test_source_name=test_source_name,
                funcs_depth=funcs_depth,
                results=results,
                all_error_funcs_content=all_error_funcs_content,
                once_retry_count_dict=once_retry_count_dict,
            )
            pipeline._mark_module_end(test_source_name)
            pipeline.sync_archive_imports(results)
            set_error_count(active_error_count(all_error_funcs_content))
            save_checkpoint(
                results,
                once_retry_count_dict,
                all_error_funcs_content,
                output_dir,
                stats=_current_pipeline_stats(),
                dependency_overrides=pipeline.project_dependency_overrides,
                pending_accepted=pending_accepted,
                runtime_status=runtime_status,
                source_runtime_status=source_runtime_status,
                source_runtime_pass_cache=source_runtime_pass_cache,
                repair_records=repair_records,
            )

        if pipeline.export_verify_project:
            export_sources = [name for name in src_names if name in results]
            test_sources = [name for name in results.keys() if pipeline._is_test_source(name)]
            if not export_sources:
                export_sources = [
                    name for name in results.keys() if not pipeline._is_test_source(name)
                ]
            export_root = os.path.join(output_dir, "verify_project")
            ok, msg = pipeline.export_archive_to_project(
                archive=results,
                include_files=export_sources,
                output_project_path=export_root,
                crate_name="verify_project",
            )
            if ok:
                if test_sources:
                    test_ok, test_msg = pipeline.export_archive_tests_to_project(
                        archive=results,
                        include_test_files=test_sources,
                        output_project_path=export_root,
                        crate_name="verify_project",
                    )
                    if test_ok:
                        logger.info(f"[EXPORT-PROJECT-TESTS] root={export_root} {test_msg}")
                    else:
                        logger.warning(f"[EXPORT-PROJECT-TESTS-SKIP] {test_msg}")
                logger.info(f"[EXPORT-PROJECT] root={export_root} {msg}")
            else:
                logger.warning(f"[EXPORT-PROJECT-SKIP] {msg}")

        elapsed_time = time.time() - start_time
        set_error_count(active_error_count(all_error_funcs_content))
        h, rem = divmod(elapsed_time, 3600)
        m, s = divmod(rem, 60)
        logger.info(
            "Total time: %02d:%02d:%02d, retries=%d, regenerations=%d, errors=%d"
            % (
                int(h),
                int(m),
                int(s),
                _current_pipeline_stats().total_retry_count,
                _current_pipeline_stats().total_regenerate_count,
                _current_pipeline_stats().total_error_count,
            )
        )
        logger.info(
            f"Verify cache: enabled={int(verify_cache_enabled)} hits={getattr(verifier, 'cache_hits', 0)} misses={getattr(verifier, 'cache_misses', 0)}"
        )
        cost_csv_path = pipeline.write_cost_csv(output_dir, global_elapsed_seconds=elapsed_time)
        if cost_csv_path:
            logger.info(f"[COST-CSV] saved to {cost_csv_path}")

        calculate_compile_pass_rates(
            output_dir,
            results,
            sorted_funcs_depth,
            data_manager,
            list(active_target_sources),
        )
        calculate_retry_pass_rates(
            output_dir,
            results,
            include_dict,
            once_retry_count_dict,
            list(active_target_sources),
        )
        try:
            generate_run_report = bool(int(params.get("generate_run_report", 1)))
            report_verify_cargo_test = bool(int(params.get("report_verify_cargo_test", 1)))
        except Exception:
            generate_run_report = True
            report_verify_cargo_test = True
        if generate_run_report:
            try:
                report = generate_translation_report(
                    output_dir,
                    verify=report_verify_cargo_test,
                )
                logger.info(
                    "[RUN-REPORT] status=%s report_json=%s report_md=%s"
                    % (
                        report.get("status"),
                        report.get("artifacts", {}).get("report.json"),
                        report.get("artifacts", {}).get("report.md"),
                    )
                )
            except Exception as exc:
                logger.warning(f"[RUN-REPORT-FAIL] {exc}")
    finally:
        try:
            pipeline.write_cost_csv(output_dir, global_elapsed_seconds=elapsed_time)
        except Exception:
            pass
        pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())
