"""Main orchestration loop for C-to-Rust function translation.

This file coordinates scheduling, LLM calls, verification, retry accounting,
and checkpoint-compatible result updates. Heavy helper domains live in sibling
modules with clearer names:

* `rust_archive.py`: merge/render the persistent Rust translation archive.
* `prompt_builder.py`: assemble initial and repair prompts.
* `rust_project_export.py`: materialize archive buckets as Cargo projects.
* `cc_mini_fallback.py`: CC-MINI assisted fallback and runtime repair.
"""

import csv
import hashlib
import json
import os
import re
import sys
import time
from collections import defaultdict
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from cargo_verifier import CargoVerifier
from data_manager import DataManager
from models.llm_model import generate_response
from pipeline.prompt_builder import PromptBuilder
from pipeline.auto_repair import AutoRepairActions
from pipeline.cc_mini_runtime import CcMiniRuntimeAgentAdapter
from pipeline.function_worker import FunctionTranslationWorker
from pipeline.llm_candidate_selector import LlmCandidateSelector
from pipeline.translation_scheduler import TranslationScheduler
from pipeline.verification_flow import VerificationFlow
from pipeline.rust_archive import RustArchiveBuilder
from pipeline.rust_project_export import RustProjectExporter
from pipeline.cc_mini_fallback import CcMiniFallbackCoordinator
from pipeline.output_layout import artifact_path, logs_dir
from pipeline.stats import PipelineStats, apply_pipeline_stats, current_pipeline_stats


def _current_pipeline_stats() -> PipelineStats:
    return current_pipeline_stats()


def _apply_pipeline_stats(stats: PipelineStats) -> None:
    apply_pipeline_stats(stats)


class TranslationPipeline:
    """Coordinate translation while preserving legacy result/checkpoint formats."""

    COST_CSV_COLUMNS = [
        "scope",
        "source_name",
        "elapsed_seconds",
        "input_tokens",
        "output_tokens",
        "total_tokens",
    ]
    _cc_mini_agent_import_attempted = False
    _cc_mini_agent_import_error = ""
    _cc_mini_agent_class = None
    _cc_mini_options_class = None
    _cycle_placeholder_marker = "__CYCLE_PLACEHOLDER__"

    def __init__(
        self,
        data_manager: DataManager,
        source_names: List[str],
        funcs_childs: Dict[str, Dict[str, List[str]]],
        logger,
        llm_model: str,
        verifier: CargoVerifier,
        params: Dict[str, int],
        checkpoint_hook=None,
        ownership_suggestions: Optional[Dict[str, List[str]]] = None,
        excluded_sources: Optional[Set[str]] = None,
        output_dir: str = "",
        pending_accepted: Optional[Dict[str, Dict[str, str]]] = None,
        runtime_status: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None,
        source_runtime_status: Optional[Dict[str, Dict[str, Any]]] = None,
        source_runtime_pass_cache: Optional[Dict[str, Any]] = None,
        repair_records: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ):
        self.data_manager = data_manager
        self.source_names = source_names
        self.funcs_childs = funcs_childs
        self.logger = logger
        self.llm_model = llm_model
        self.verifier = verifier
        self.params = params
        self.ownership_suggestions = ownership_suggestions or {}
        self.excluded_sources: Set[str] = {str(x).strip() for x in (excluded_sources or set()) if str(x).strip()}
        self.llm_timeout_seconds = int(params.get("llm_timeout_seconds", 180))
        self.max_stagnant_retries = int(params.get("max_stagnant_retries", 5))
        self.max_func_seconds = int(params.get("max_func_seconds", 1000))
        self.min_func_time_reserve_seconds = int(params.get("min_func_time_reserve_seconds", 15))
        self.min_llm_timeout_seconds = int(params.get("min_llm_timeout_seconds", 12))
        self.max_verify_invocations_per_func = int(params.get("max_verify_invocations_per_func", 18))
        self.multi_candidate_count = max(1, int(params.get("multi_candidate_count", 2)))
        self.fix_multi_candidate_count = max(
            1,
            int(params.get("fix_multi_candidate_count", self.multi_candidate_count)),
        )
        self.multi_candidate_temperature_step = float(params.get("multi_candidate_temperature_step", 0.08))
        self.multi_candidate_max_temperature = float(params.get("multi_candidate_max_temperature", 0.35))
        self.model_feedback_detail_max_chars = int(params.get("model_feedback_detail_max_chars", 2200))
        self.style_penalty_ffi_c_void = int(params.get("style_penalty_ffi_c_void", 180))
        self.style_penalty_raw_ptr = int(params.get("style_penalty_raw_ptr", 24))
        self.style_penalty_unsafe = int(params.get("style_penalty_unsafe", 42))
        self.hard_reject_c_pointers = bool(int(params.get("hard_reject_c_pointers", 1)))
        self.ablation_no_context = bool(int(params.get("ablation_no_context", 0)))
        self.ablation_no_constraints = bool(int(params.get("ablation_no_constraints", 0)))
        self.ablation_disable_feedback_loop = bool(int(params.get("ablation_disable_feedback_loop", 0)))
        self.ablation_random_order = bool(int(params.get("ablation_random_order", 0)))
        self.ablation_random_seed = int(params.get("ablation_random_seed", 20260314))
        self.export_verify_project = bool(int(params.get("export_verify_project", 1)))
        if self.ablation_no_constraints:
            # No-constraints ablation should not keep style penalties as hidden constraints.
            self.style_penalty_ffi_c_void = 0
            self.style_penalty_raw_ptr = 0
            self.style_penalty_unsafe = 0
            self.hard_reject_c_pointers = False
        self.enable_dependency_import_guessing = bool(int(params.get("enable_dependency_import_guessing", 0)))
        self.fix_editable_function_limit = max(1, int(params.get("fix_editable_function_limit", 4)))
        self.fix_readonly_dependency_limit = max(1, int(params.get("fix_readonly_dependency_limit", 12)))
        self.verify_scope_mode = str(params.get("verify_scope_mode", "archive")).strip().lower()
        self.verify_full_archive = bool(int(params.get("verify_full_archive", 1)))
        self.owner_scoped_verify = bool(int(params.get("owner_scoped_verify", 1)))
        self.root_cause_first = bool(int(params.get("root_cause_first", 1)))
        self.blocked_fast_fail = bool(int(params.get("blocked_fast_fail", 1)))
        self.source_round_summary_enabled = bool(int(params.get("source_round_summary_enabled", 1)))
        self.no_progress_regen_retries = max(1, int(params.get("no_progress_regen_retries", 4)))
        self.parse_fail_handoff_retries = max(1, int(params.get("parse_fail_handoff_retries", 2)))
        self.unresolved_symbol_handoff_retries = max(
            1,
            int(params.get("unresolved_symbol_handoff_retries", 4)),
        )
        self.dependency_cycle_probe = bool(int(params.get("dependency_cycle_probe", 1)))
        self.max_cycle_probe_attempts_per_source = max(
            0,
            int(params.get("max_cycle_probe_attempts_per_source", 3)),
        )
        self.heuristic_test_dep_extraction = bool(int(params.get("heuristic_test_dep_extraction", 1)))
        excluded_functions_raw = str(
            params.get("excluded_functions", "extra,run_test,run_tests")
        )
        self.excluded_function_names: Set[str] = {
            item.strip() for item in excluded_functions_raw.split(",") if item.strip()
        }
        # 0: retry functions in all_error_funcs_content; 1: skip them
        self.skip_failed_functions = bool(int(params.get("skip_failed_functions", 0)))
        self.enable_cc_mini_agent_fallback = bool(
            int(
                params.get(
                    "enable_cc_mini_agent_fallback",
                    params.get("enable_swe_agent_fallback", 0),
                )
            )
        )
        self.enable_swe_regen_assist = bool(
            int(params.get("enable_swe_regen_assist", int(self.enable_cc_mini_agent_fallback)))
        )
        self.swe_regen_assist_max_notes = max(1, int(params.get("swe_regen_assist_max_notes", 3)))
        self.swe_regen_assist_note_max_chars = int(params.get("swe_regen_assist_note_max_chars", 900))
        self.swe_fast_fallback_on_unresolved_symbol = bool(
            int(params.get("swe_fast_fallback_on_unresolved_symbol", 1))
        )
        self.swe_prompt_strict_target_scope = bool(int(params.get("swe_prompt_strict_target_scope", 0)))
        self.cc_mini_agent_max_iterations = int(
            params.get("cc_mini_agent_max_iterations", params.get("swe_agent_max_iterations", 50))
        )
        self.cc_mini_agent_command_timeout = int(
            params.get("cc_mini_agent_command_timeout", params.get("swe_agent_command_timeout", 90))
        )
        self.cc_mini_max_call_attempts = max(
            1,
            int(params.get("cc_mini_max_call_attempts", params.get("swe_max_call_attempts", 2))),
        )
        self.cc_mini_config_path = str(params.get("cc_mini_config", "")).strip()
        if not self.cc_mini_config_path:
            self.cc_mini_config_path = self._derive_cc_mini_default_config_path()
        runtime_mode_raw = str(params.get("test_runtime_check_mode", "") or "").strip().lower()
        legacy_runtime_enabled = bool(int(params.get("test_runtime_check_enabled", 0)))
        if runtime_mode_raw:
            runtime_mode = runtime_mode_raw
        else:
            runtime_mode = "function" if legacy_runtime_enabled else "off"
        if runtime_mode not in {"off", "function", "source_complete"}:
            self.logger.warning(
                f"[RUNTIME-CHECK-MODE-INVALID] mode={runtime_mode} fallback=function"
            )
            runtime_mode = "function"
        self.test_runtime_check_mode = runtime_mode
        self.test_runtime_check_enabled = runtime_mode != "off"
        self.test_runtime_check_timeout_seconds = max(30, int(params.get("test_runtime_check_timeout_seconds", 300)))
        self.test_runtime_swe_max_attempts = max(1, int(params.get("test_runtime_swe_max_attempts", 2)))
        self._cc_mini_agent_instances: Dict[str, Any] = {}
        self._cc_mini_agent_instance_seq = 0
        self._cc_mini_agent_warned = False
        self.project_dependency_overrides: Dict[str, str] = {}
        if hasattr(self.verifier, "dependency_overrides"):
            self.verifier.dependency_overrides = dict(self.project_dependency_overrides)
        self.chat_log_path = self._derive_chat_log_path()
        self.run_log_path = self._derive_run_log_path()
        self.output_dir = output_dir or ""
        self.pending_accepted: Dict[str, Dict[str, str]] = pending_accepted if pending_accepted is not None else defaultdict(dict)
        self.runtime_status: Dict[str, Dict[str, Dict[str, Any]]] = runtime_status if runtime_status is not None else defaultdict(dict)
        self.source_runtime_status: Dict[str, Dict[str, Any]] = source_runtime_status if source_runtime_status is not None else defaultdict(dict)
        self.source_runtime_pass_cache: Dict[str, Any] = source_runtime_pass_cache if source_runtime_pass_cache is not None else {}
        self.repair_records: Dict[str, List[Dict[str, Any]]] = repair_records if repair_records is not None else defaultdict(list)
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0
        self.module_costs: Dict[str, Dict[str, float]] = {}
        self.module_start_times: Dict[str, float] = {}
        self._chat_log_lock = Lock()
        self._chat_counter = 0
        self.checkpoint_hook = checkpoint_hook
        self._heuristic_direct_callee_cache: Dict[Tuple[str, str], List[str]] = {}
        self._cycle_probe_stub_plan: Dict[Tuple[str, str], List[str]] = {}
        self._cycle_placeholder_active: Dict[str, Set[str]] = defaultdict(set)
        self._cycle_group_members: Dict[str, Dict[str, Set[str]]] = defaultdict(dict)
        if self.ablation_no_context:
            # No-context ablation should measure prompt-context impact only.
            # Disable CC-MINI assistance to avoid external recovery path interference.
            self.enable_cc_mini_agent_fallback = False
            self.enable_swe_regen_assist = False
            self.swe_fast_fallback_on_unresolved_symbol = False

        if self.ablation_disable_feedback_loop:
            # Feedback-loop ablation should isolate single-pass transpilation behavior.
            self.enable_cc_mini_agent_fallback = False
            self.enable_swe_regen_assist = False
            self.swe_fast_fallback_on_unresolved_symbol = False

        self.logger.info(
            "[ABLATION] no_context=%d no_constraints=%d no_feedback_loop=%d random_order=%d seed=%d"
            % (
                int(self.ablation_no_context),
                int(self.ablation_no_constraints),
                int(self.ablation_disable_feedback_loop),
                int(self.ablation_random_order),
                int(self.ablation_random_seed),
            )
        )
        self.logger.info(
            f"[RUNTIME-CHECK-MODE] mode={self.test_runtime_check_mode} enabled={int(self.test_runtime_check_enabled)}"
        )
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Create concrete modules and inject only the dependencies they use.

        This replaces the old adapter fallback that exposed the entire pipeline
        namespace to every helper. The lists below are intentionally explicit:
        adding a cross-module dependency now requires a visible edit here.
        """
        self.auto_repair = AutoRepairActions()
        self.scheduler = TranslationScheduler()
        self.verification_flow = VerificationFlow()
        self.prompt_builder = PromptBuilder()
        self.archive_builder = RustArchiveBuilder()
        self.project_exporter = RustProjectExporter(
            module_source_renderer=self.archive_builder._renderer(),
            test_source_classifier=self.archive_builder._is_test_source,
            verifier=self.verifier,
        )
        self.cc_mini_fallback = CcMiniFallbackCoordinator()
        self.function_worker = FunctionTranslationWorker(logger=self.logger)
        self.candidate_selector = None

        self._wire_archive_builder()
        self._wire_prompt_builder()
        self._wire_verification_flow()
        self._wire_auto_repair()
        self._wire_scheduler()
        self._wire_project_exporter()
        self._wire_cc_mini_fallback()
        self._wire_candidate_selector()
        self._wire_function_worker()
        self._wire_pipeline_compatibility_methods()

    def _copy_attrs(self, target: object, names: List[str]) -> None:
        for name in names:
            setattr(target, name, getattr(self, name))

    @staticmethod
    def _bind_methods(target: object, mapping: Dict[str, Any]) -> None:
        for name, method in mapping.items():
            setattr(target, name, method)

    def _wire_archive_builder(self) -> None:
        self._copy_attrs(
            self.archive_builder,
            [
                "data_manager",
                "source_names",
                "funcs_childs",
                "logger",
                "params",
                "enable_dependency_import_guessing",
            ],
        )
        self._bind_methods(
            self.archive_builder,
            {
                "_collect_source_dependency_sources": self.prompt_builder._collect_source_dependency_sources,
                "_extract_editable_function_directives": self.prompt_builder._extract_editable_function_directives,
                "_find_forbidden_c_pointer_tokens": self._find_forbidden_c_pointer_tokens,
                "_is_cycle_placeholder_function": self.scheduler._is_cycle_placeholder_function,
            },
        )

    def _wire_prompt_builder(self) -> None:
        self._copy_attrs(
            self.prompt_builder,
            [
                "data_manager",
                "source_names",
                "funcs_childs",
                "ownership_suggestions",
                "params",
                "ablation_no_context",
                "ablation_no_constraints",
                "fix_editable_function_limit",
                "fix_readonly_dependency_limit",
            ],
        )
        self._bind_methods(
            self.prompt_builder,
            {
                "_build_module_sources": self.archive_builder._build_module_sources,
                "_clip_text": self._clip_text,
                "_collect_source_dependency_sources": self.prompt_builder._collect_source_dependency_sources,
                "_extract_decl_symbol_from_block": self.archive_builder._extract_decl_symbol_from_block,
                "_extract_diagnostic_codes": self.prompt_builder._extract_diagnostic_codes,
                "_extract_function_signature": self.prompt_builder._extract_function_signature,
                "_is_excluded_source_name": self.scheduler._is_excluded_source_name,
                "_is_test_source": self.archive_builder._is_test_source,
                "_iter_identifiers": self.archive_builder._iter_identifiers,
                "_split_extra_blocks": self.archive_builder._split_extra_blocks,
            },
        )

    def _wire_verification_flow(self) -> None:
        self._copy_attrs(
            self.verification_flow,
            [
                "data_manager",
                "source_names",
                "funcs_childs",
                "logger",
                "verifier",
                "model_feedback_detail_max_chars",
                "owner_scoped_verify",
                "verify_full_archive",
                "verify_scope_mode",
            ],
        )
        self._bind_methods(
            self.verification_flow,
            {
                "_build_module_sources": self.archive_builder._build_module_sources,
                "_clip_text": self._clip_text,
                "_is_test_source": self.archive_builder._is_test_source,
            },
        )

    def _wire_auto_repair(self) -> None:
        self._bind_methods(
            self.auto_repair,
            {
                "_build_module_sources": self.archive_builder._build_module_sources,
                "_extract_missing_named_entities": self.prompt_builder._extract_missing_named_entities,
                "_merge_extra": self.archive_builder._merge_extra,
            },
        )

    def _wire_scheduler(self) -> None:
        self._copy_attrs(
            self.scheduler,
            [
                "data_manager",
                "source_names",
                "funcs_childs",
                "logger",
                "excluded_sources",
                "excluded_function_names",
                "checkpoint_hook",
                "ablation_random_order",
                "ablation_random_seed",
                "blocked_fast_fail",
                "root_cause_first",
                "source_round_summary_enabled",
                "dependency_cycle_probe",
                "max_cycle_probe_attempts_per_source",
                "heuristic_test_dep_extraction",
                "_cycle_probe_stub_plan",
                "_cycle_placeholder_active",
                "_cycle_group_members",
            ],
        )
        self._bind_methods(
            self.scheduler,
            {
                "_extract_direct_callees_from_c_body": self._extract_direct_callees_from_c_body,
                "_extract_function_signature": self.prompt_builder._extract_function_signature,
                "_is_test_source": self.archive_builder._is_test_source,
                "_mark_module_start": self._mark_module_start,
                "_run_source_runtime_check_after_completion": self._run_source_runtime_check_after_completion,
                "process_func": self.process_func,
            },
        )

    def _wire_project_exporter(self) -> None:
        self.project_exporter.verifier = self.verifier

    def _wire_cc_mini_fallback(self) -> None:
        self._copy_attrs(
            self.cc_mini_fallback,
            [
                "logger",
                "verifier",
                "enable_cc_mini_agent_fallback",
                "test_runtime_check_enabled",
                "test_runtime_check_mode",
                "test_runtime_check_timeout_seconds",
                "test_runtime_swe_max_attempts",
                "swe_regen_assist_max_notes",
                "swe_regen_assist_note_max_chars",
                "project_dependency_overrides",
            ],
        )
        self._bind_methods(
            self.cc_mini_fallback,
            {
                "_build_module_sources": self.archive_builder._build_module_sources,
                "_build_swe_strategy_notes": self.prompt_builder._build_swe_strategy_notes,
                "_clip_text": self._clip_text,
                "_collect_archive_verify_sources": self.verification_flow._collect_archive_verify_sources,
                "_collect_swe_prompt_diagnostic_codes": self.prompt_builder._collect_swe_prompt_diagnostic_codes,
                "_compose_model_compile_feedback": self.verification_flow._compose_model_compile_feedback,
                "_dedupe_use_statements": self.archive_builder._dedupe_use_statements,
                "_ensure_public_function": self.archive_builder._ensure_public_function,
                "_format_verify_diagnostics_for_debug": self.verification_flow._format_verify_diagnostics_for_debug,
                "_get_cc_mini_agent_instance": self._get_cc_mini_agent_instance,
                "_is_test_source": self.archive_builder._is_test_source,
                "_preserve_owned_declaration_blocks": self.archive_builder._preserve_owned_declaration_blocks,
                "_sanitize_non_function_content": self.archive_builder._sanitize_non_function_content,
                "_strip_cargo_check_raw": self.verification_flow._strip_cargo_check_raw,
                "_trim_to_function_definition": self.archive_builder._trim_to_function_definition,
                "export_archive_tests_to_project": self.export_archive_tests_to_project,
                "export_archive_to_project": self.export_archive_to_project,
            },
        )

    def _wire_candidate_selector(self) -> None:
        self.candidate_selector = LlmCandidateSelector(
            call_llm_logged=self._call_llm_logged,
            apply_response_to_archive=self.archive_builder._apply_response_to_archive,
            build_module_sources=self.archive_builder._build_module_sources,
            verifier=self.verifier,
            score_verify_result=self.verification_flow._score_verify_result,
            score_rust_style_penalty=self._score_rust_style_penalty,
            find_forbidden_c_pointer_tokens=self._find_forbidden_c_pointer_tokens,
            is_llm_transport_error=self._is_llm_transport_error,
            logger=self.logger,
            temperature_step=self.multi_candidate_temperature_step,
            max_temperature=self.multi_candidate_max_temperature,
            hard_reject_c_pointers=self.hard_reject_c_pointers,
        )

    def _wire_function_worker(self) -> None:
        self._copy_attrs(
            self.function_worker,
            [
                "data_manager",
                "source_names",
                "funcs_childs",
                "logger",
                "llm_model",
                "params",
                "excluded_function_names",
                "skip_failed_functions",
                "ablation_disable_feedback_loop",
                "hard_reject_c_pointers",
                "max_func_seconds",
                "min_llm_timeout_seconds",
                "max_verify_invocations_per_func",
                "multi_candidate_count",
                "fix_multi_candidate_count",
                "no_progress_regen_retries",
                "max_stagnant_retries",
                "parse_fail_handoff_retries",
                "unresolved_symbol_handoff_retries",
                "enable_cc_mini_agent_fallback",
                "enable_swe_regen_assist",
                "swe_fast_fallback_on_unresolved_symbol",
                "swe_regen_assist_max_notes",
                "swe_regen_assist_note_max_chars",
                "verify_full_archive",
                "pending_accepted",
                "runtime_status",
                "source_runtime_status",
                "repair_records",
                "_cycle_probe_stub_plan",
                "_cycle_placeholder_active",
                "_cycle_placeholder_marker",
            ],
        )
        self._bind_methods(
            self.function_worker,
            {
                "_apply_response_to_archive": self.archive_builder._apply_response_to_archive,
                "_attempt_cc_mini_agent_fallback": self.cc_mini_fallback._attempt_cc_mini_agent_fallback,
                "_attempt_cc_mini_agent_regen_assist": self.cc_mini_fallback._attempt_cc_mini_agent_regen_assist,
                "_auto_alias_missing_test_values": self.auto_repair._auto_alias_missing_test_values,
                "_auto_inject_missing_new_constructor": self.auto_repair._auto_inject_missing_new_constructor,
                "_auto_inject_missing_test_value_placeholders": self.auto_repair._auto_inject_missing_test_value_placeholders,
                "_build_cycle_stub_prompt_note": self.scheduler._build_cycle_stub_prompt_note,
                "_build_editable_fix_template": self.prompt_builder._build_editable_fix_template,
                "_build_fix_prompt": self.prompt_builder._build_fix_prompt,
                "_build_failure_record": self.verification_flow._build_failure_record,
                "_build_initial_prompt_context": self.prompt_builder._build_initial_prompt_context,
                "_build_readonly_dependency_signature_hints": self.prompt_builder._build_readonly_dependency_signature_hints,
                "_call_llm_logged": self._call_llm_logged,
                "_clip_text": self._clip_text,
                "_collect_archive_verify_sources": self.verification_flow._collect_archive_verify_sources,
                "_collect_next_round_editable_candidates": self.prompt_builder._collect_next_round_editable_candidates,
                "_collect_required_editable_functions": self.prompt_builder._collect_required_editable_functions,
                "_collect_unfinished_direct_callees": self.scheduler._collect_unfinished_direct_callees,
                "_compose_model_compile_feedback": self.verification_flow._compose_model_compile_feedback,
                "_compose_regen_prompt_with_swe_notes": self.cc_mini_fallback._compose_regen_prompt_with_swe_notes,
                "_compute_llm_timeout": self._compute_llm_timeout,
                "_extract_diagnostic_codes": self.prompt_builder._extract_diagnostic_codes,
                "_extract_editable_function_directives": self.prompt_builder._extract_editable_function_directives,
                "_extract_swe_handoff_directive": self.prompt_builder._extract_swe_handoff_directive,
                "_fallback_model_name": self._fallback_model_name,
                "_find_forbidden_c_pointer_tokens": self._find_forbidden_c_pointer_tokens,
                "_format_verify_diagnostics_for_debug": self.verification_flow._format_verify_diagnostics_for_debug,
                "_generate_candidates_and_pick_best": self._generate_candidates_and_pick_best,
                "_is_cycle_placeholder_function": self.scheduler._is_cycle_placeholder_function,
                "_is_excluded_source_name": self.scheduler._is_excluded_source_name,
                "_is_llm_transport_error": self._is_llm_transport_error,
                "_is_malformed_target_output_failure": self.prompt_builder._is_malformed_target_output_failure,
                "_is_missing_constructor_failure": self.auto_repair._is_missing_constructor_failure,
                "_is_structural_syntax_failure": self._is_structural_syntax_failure,
                "_is_test_source": self.archive_builder._is_test_source,
                "_is_unresolved_symbol_failure": self.prompt_builder._is_unresolved_symbol_failure,
                "_is_verify_timeout": self._is_verify_timeout,
                "_normalize_feedback_signature": self.prompt_builder._normalize_feedback_signature,
                "_reconcile_editable_functions": self.prompt_builder._reconcile_editable_functions,
                "_refresh_cycle_placeholder_state": self.scheduler._refresh_cycle_placeholder_state,
                "_remaining_func_seconds": self._remaining_func_seconds,
                "_resolve_verify_scopes": self.verification_flow._resolve_verify_scopes,
                "_run_test_module_with_optional_swe_repair": self.cc_mini_fallback._run_test_module_with_optional_swe_repair,
                "_strip_cargo_check_raw": self.verification_flow._strip_cargo_check_raw,
                "_verify_archive_with_strategy": self.verification_flow._verify_archive_with_strategy,
            },
        )

    def _wire_pipeline_compatibility_methods(self) -> None:
        """Keep existing internal call sites working without namespace fallback."""
        self._apply_response_to_archive = self.archive_builder._apply_response_to_archive
        self._build_module_sources = self.archive_builder._build_module_sources
        self._is_ident_char = self.archive_builder._is_ident_char
        self._score_verify_result = self.verification_flow._score_verify_result

    def process_func(
        self,
        test_source_name: str,
        func_name: str,
        depth: int,
        results: Dict[str, Dict[str, str]],
        all_error_funcs_content: Dict[str, Dict[str, str]],
        once_retry_count_dict: Dict[str, Dict[str, int]],
    ) -> None:
        self.function_worker.process_func(
            test_source_name=test_source_name,
            func_name=func_name,
            depth=depth,
            results=results,
            all_error_funcs_content=all_error_funcs_content,
            once_retry_count_dict=once_retry_count_dict,
        )

    def _fingerprint_source_runtime_archive(
        self,
        archive: Dict[str, Dict[str, str]],
        include_files: List[str],
    ) -> str:
        export_sources = sorted(
            name for name in (archive or {}).keys() if not self.archive_builder._is_test_source(name)
        )
        test_sources = sorted(
            name for name in (archive or {}).keys() if self.archive_builder._is_test_source(name)
        )
        render_sources = export_sources + test_sources
        module_sources, module_to_source = self.archive_builder._build_module_sources(archive, render_sources)
        payload = {
            "version": 1,
            "mode": "source_complete",
            "command": "cargo test --quiet",
            "crate_name": "verify_project",
            "export_sources": export_sources,
            "test_sources": test_sources,
            "dependency_overrides": dict(sorted(self.project_dependency_overrides.items())),
            "modules": [
                {
                    "module": module_name,
                    "source_name": module_to_source.get(module_name, ""),
                    "text": module_sources[module_name],
                }
                for module_name in sorted(module_sources)
            ],
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    def _source_runtime_pass_cache_hit(self, fingerprint: str) -> bool:
        cache = self.source_runtime_pass_cache if isinstance(self.source_runtime_pass_cache, dict) else {}
        if cache.get("version") != 2:
            return False
        cache.pop("last_pass", None)
        passes = cache.get("passes")
        if not isinstance(passes, dict):
            return False
        entry = passes.get(fingerprint)
        if not isinstance(entry, dict):
            return False
        return (
            entry.get("fingerprint") == fingerprint
            and entry.get("mode") == "source_complete"
            and entry.get("command") == "cargo test --quiet"
        )

    def _record_source_runtime_pass_cache(
        self,
        *,
        fingerprint: str,
        test_source_name: str,
        include_files: List[str],
        message: str,
    ) -> None:
        cache = self.source_runtime_pass_cache if isinstance(self.source_runtime_pass_cache, dict) else {}
        if cache.get("version") != 2 or not isinstance(cache.get("passes"), dict):
            cache.clear()
            cache.update({"version": 2, "passes": {}})
        cache.pop("last_pass", None)
        cache["passes"][fingerprint] = {
            "fingerprint": fingerprint,
            "command": "cargo test --quiet",
            "mode": "source_complete",
            "include_files": sorted(str(x) for x in include_files),
            "passed_by_source": test_source_name,
            "message": str(message or ""),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        if cache is not self.source_runtime_pass_cache:
            self.source_runtime_pass_cache.clear()
            self.source_runtime_pass_cache.update(cache)

    def _run_source_runtime_check_after_completion(
        self,
        *,
        test_source_name: str,
        results: Dict[str, Dict[str, str]],
        all_error_funcs_content: Dict[str, Dict[str, str]],
    ) -> None:
        if not self.test_runtime_check_enabled or self.test_runtime_check_mode != "source_complete":
            return
        if not self.archive_builder._is_test_source(test_source_name):
            return

        include_files = list(getattr(self.data_manager, "all_include_files", []) or [])
        if test_source_name not in include_files:
            include_files.append(test_source_name)

        compile_error_sources = [
            src
            for src in include_files
            if isinstance(all_error_funcs_content.get(src), dict)
            and all_error_funcs_content.get(src)
        ]
        if compile_error_sources:
            message = "source runtime check skipped: compile errors in " + ",".join(compile_error_sources[:8])
            self.runtime_status.setdefault(test_source_name, {})["__source_complete__"] = {
                "status": "source_runtime_skipped_compile_errors",
                "test_source": test_source_name,
                "message": message,
            }
            self.source_runtime_status[test_source_name] = {
                "status": "source_runtime_skipped_compile_errors",
                "failed": 0,
                "passed": 0,
                "message": message,
            }
            self.logger.info(f"[SOURCE-RUNTIME-SKIP] {test_source_name} reason={message}")
            if self.checkpoint_hook:
                self.checkpoint_hook()
            return

        runtime_before = FunctionTranslationWorker._build_runtime_test_archive(
            results,
            {},
            include_files,
        )
        runtime_fingerprint = self._fingerprint_source_runtime_archive(runtime_before, include_files)
        if self._source_runtime_pass_cache_hit(runtime_fingerprint):
            message = "source runtime full cargo test skipped: cached pass for unchanged project"
            self.runtime_status.setdefault(test_source_name, {})["__source_complete__"] = {
                "status": "source_runtime_passed_cached",
                "test_source": test_source_name,
                "message": message,
                "fingerprint": runtime_fingerprint,
            }
            self.source_runtime_status[test_source_name] = {
                "status": "source_runtime_ok",
                "failed": 0,
                "passed": 1,
                "message": message,
                "cached": 1,
                "fingerprint": runtime_fingerprint,
            }
            self.logger.info(
                f"[SOURCE-RUNTIME-SKIP-CACHED-PASS] {test_source_name} fingerprint={runtime_fingerprint}"
            )
            if self.checkpoint_hook:
                self.checkpoint_hook()
            return
        self.logger.info(
            f"[SOURCE-RUNTIME-REQ] {test_source_name} mode=source_complete include={len(include_files)}"
        )
        ok, message, runtime_archive = self.cc_mini_fallback._run_source_module_with_optional_swe_repair(
            test_source_name=test_source_name,
            source_name=test_source_name,
            include_files=include_files,
            archive=runtime_before,
        )
        status = "source_runtime_passed" if ok else "source_runtime_failed"
        self.runtime_status.setdefault(test_source_name, {})["__source_complete__"] = {
            "status": status,
            "test_source": test_source_name,
            "message": message,
        }
        self.source_runtime_status[test_source_name] = {
            "status": "source_runtime_ok" if ok else "source_runtime_failed",
            "failed": 0 if ok else 1,
            "passed": 1 if ok else 0,
            "message": message,
        }

        if ok and runtime_archive:
            full_runtime_files = list(runtime_archive.keys())
            FunctionTranslationWorker._merge_runtime_archive_results(
                runtime_archive=runtime_archive,
                include_files=full_runtime_files,
                results=results,
                all_error_funcs_content=all_error_funcs_content,
            )
            FunctionTranslationWorker._clear_pending_for_archive(
                archive=runtime_archive,
                include_files=full_runtime_files,
                pending_accepted=self.pending_accepted,
            )
            FunctionTranslationWorker._record_runtime_repair(
                repair_records=self.repair_records,
                source_name=test_source_name,
                runtime_before=runtime_before,
                runtime_after=runtime_archive,
                include_files=full_runtime_files,
                message=message,
            )
            runtime_fingerprint = self._fingerprint_source_runtime_archive(runtime_archive, full_runtime_files)

        if ok:
            self._record_source_runtime_pass_cache(
                fingerprint=runtime_fingerprint,
                test_source_name=test_source_name,
                include_files=list(runtime_archive.keys()) if runtime_archive else include_files,
                message=message,
            )

        log_tag = "[SOURCE-RUNTIME-PASS]" if ok else "[SOURCE-RUNTIME-FAIL]"
        self.logger.info(f"{log_tag} {test_source_name} detail={str(message or '')[:260]}")
        if self.checkpoint_hook:
            self.checkpoint_hook()

    def process_test_source(
        self,
        test_source_name: str,
        funcs_depth: Dict[str, int],
        results: Dict[str, Dict[str, str]],
        all_error_funcs_content: Dict[str, Dict[str, str]],
        once_retry_count_dict: Dict[str, Dict[str, int]],
    ) -> None:
        self.scheduler.process_test_source(
            test_source_name=test_source_name,
            funcs_depth=funcs_depth,
            results=results,
            all_error_funcs_content=all_error_funcs_content,
            once_retry_count_dict=once_retry_count_dict,
        )

    def sync_archive_imports(
        self,
        archive: Dict[str, Dict[str, str]],
        include_files: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, str]]:
        return self.archive_builder.sync_archive_imports(archive, include_files=include_files)

    def export_archive_to_project(
        self,
        archive: Dict[str, Dict[str, str]],
        include_files: List[str],
        output_project_path: str,
        crate_name: str = "translation_export",
    ) -> Tuple[bool, str]:
        return self.project_exporter.export_archive_to_project(
            archive=archive,
            include_files=include_files,
            output_project_path=output_project_path,
            crate_name=crate_name,
        )

    def export_archive_tests_to_project(
        self,
        archive: Dict[str, Dict[str, str]],
        include_test_files: List[str],
        output_project_path: str,
        crate_name: str = "translation_export",
    ) -> Tuple[bool, str]:
        return self.project_exporter.export_archive_tests_to_project(
            archive=archive,
            include_test_files=include_test_files,
            output_project_path=output_project_path,
            crate_name=crate_name,
        )

    def _is_test_source(self, source_name: str) -> bool:
        return self.archive_builder._is_test_source(source_name)

    def _sync_dependency_overrides_to_verifier(self) -> None:
        self.cc_mini_fallback._sync_dependency_overrides_to_verifier()

    def _remaining_func_seconds(self, func_start_time: float) -> float:
        return float(self.max_func_seconds) - (time.time() - func_start_time)

    def _compute_llm_timeout(self, func_start_time: float) -> int:
        remaining = self._remaining_func_seconds(func_start_time)
        budget = int(remaining - self.min_func_time_reserve_seconds)
        return max(0, min(self.llm_timeout_seconds, budget))

    @staticmethod
    def _is_llm_transport_error(response: str) -> bool:
        text = (response or "").strip()
        if not text:
            return True
        return (
            text.startswith("请求超时:")
            or text.startswith("请求出错:")
            or text.startswith("不支持的模型:")
        )

    @staticmethod
    def _is_verify_timeout(verify_result) -> bool:
        if verify_result is None:
            return False
        if int(getattr(verify_result, "returncode", 0) or 0) == 124:
            return True
        for diag in getattr(verify_result, "diagnostics", []) or []:
            if (getattr(diag, "code", "") or "").strip().upper() == "TIMEOUT":
                return True
        return False

    def _fallback_model_name(self) -> str:
        if self.llm_model != "qwen":
            return "qwen"
        return "qwen"

    @staticmethod
    def _is_structural_syntax_failure(feedback: str) -> bool:
        text = (feedback or "").lower()
        return (
            "unexpected closing delimiter" in text
            or "unmatched angle bracket" in text
            or "unclosed delimiter" in text
        )

    @staticmethod
    def _clip_text(text: str, max_chars: int) -> str:
        raw = str(text or "")
        if len(raw) <= max_chars:
            return raw
        return raw[: max_chars - 14] + "\n...(truncated)"

    def _derive_chat_log_path(self) -> str:
        log_file_path = getattr(self.logger, "log_file_path", "") or ""
        if log_file_path:
            output_dir = os.path.dirname(log_file_path)
            logs_dir(output_dir).mkdir(parents=True, exist_ok=True)
            return str(artifact_path(output_dir, "llm_chat.log"))
        return os.path.abspath("llm_chat.log")

    def _derive_run_log_path(self) -> str:
        log_file_path = getattr(self.logger, "log_file_path", "") or ""
        if log_file_path:
            output_dir = os.path.dirname(log_file_path)
            logs_dir(output_dir).mkdir(parents=True, exist_ok=True)
            return str(artifact_path(output_dir, "run.log"))
        return os.path.abspath("run.log")

    @staticmethod
    def _cc_mini_candidate_roots() -> List[str]:
        """Return repository roots that may contain local cc_mini sources.

        CC-MINI is intentionally kept as a local source checkout instead of a
        package dependency.  The pipeline can run from Tool/, Tool/Tool_py/, or
        tests, so fallback discovery must be explicit and shared by both config
        lookup and Python import setup.
        """
        roots: List[str] = []

        def add_root(root: str) -> None:
            normalized = os.path.abspath(os.path.expanduser(str(root or "")))
            if normalized and normalized not in roots:
                roots.append(normalized)

        env_cc_mini_path = os.environ.get("CC_MINI_PATH", "").strip()
        if env_cc_mini_path:
            env_path = os.path.abspath(os.path.expanduser(env_cc_mini_path))
            # Accept either /path/to/cc_mini or /path/to/repo_root.
            if os.path.basename(env_path) == "cc_mini":
                add_root(os.path.dirname(env_path))
            else:
                add_root(env_path)

        here = os.path.abspath(os.path.dirname(__file__))
        for levels_up in (3, 2, 4, 5):
            add_root(os.path.join(here, *([os.pardir] * levels_up)))
        add_root(os.getcwd())
        return roots

    @classmethod
    def _derive_cc_mini_default_config_path(cls) -> str:
        env_config = os.environ.get("CC_MINI_CONFIG", "").strip()
        if env_config:
            cfg = os.path.abspath(os.path.expanduser(env_config))
            if os.path.isfile(cfg):
                return cfg

        for root in cls._cc_mini_candidate_roots():
            cfg = os.path.join(root, ".cc-mini.toml")
            if os.path.isfile(cfg):
                return cfg
        return ""

    def _next_chat_id(self) -> str:
        self._chat_counter += 1
        return f"chat_{self._chat_counter:06d}"

    def _accumulate_token_usage(self, source_name: str, usage: Dict[str, Any]) -> None:
        usage = usage or {}
        in_tokens = int(usage.get("prompt_tokens", 0) or 0)
        out_tokens = int(usage.get("completion_tokens", 0) or 0)
        total = int(usage.get("total_tokens", 0) or 0)
        if total <= 0:
            total = in_tokens + out_tokens

        self.total_input_tokens += in_tokens
        self.total_output_tokens += out_tokens
        self.total_tokens += total

        bucket = self.module_costs.setdefault(
            source_name,
            {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "elapsed_seconds": 0.0,
            },
        )
        bucket["input_tokens"] += in_tokens
        bucket["output_tokens"] += out_tokens
        bucket["total_tokens"] += total

    def _mark_module_start(self, source_name: str) -> None:
        if source_name and source_name not in self.module_start_times:
            self.module_start_times[source_name] = time.time()

    def _mark_module_end(self, source_name: str) -> None:
        if not source_name:
            return
        start = self.module_start_times.pop(source_name, None)
        if start is None:
            return
        elapsed = max(0.0, time.time() - start)
        bucket = self.module_costs.setdefault(
            source_name,
            {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "elapsed_seconds": 0.0,
            },
        )
        bucket["elapsed_seconds"] += elapsed

    def write_cost_csv(self, output_dir: Optional[str] = None, global_elapsed_seconds: Optional[float] = None) -> str:
        out_dir = output_dir or self.output_dir
        if not out_dir:
            return ""
        csv_path = artifact_path(out_dir, "cost.csv")
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        rows: List[Dict[str, Any]] = []
        rows.append(
            {
                "scope": "global",
                "source_name": "ALL",
                "elapsed_seconds": (
                    f"{float(global_elapsed_seconds):.3f}" if global_elapsed_seconds is not None else ""
                ),
                "input_tokens": int(self.total_input_tokens),
                "output_tokens": int(self.total_output_tokens),
                "total_tokens": int(self.total_tokens),
            }
        )
        for source_name in sorted(self.module_costs.keys()):
            bucket = self.module_costs[source_name]
            rows.append(
                {
                    "scope": "module",
                    "source_name": source_name,
                    "elapsed_seconds": f"{float(bucket.get('elapsed_seconds', 0.0) or 0.0):.3f}",
                    "input_tokens": int(bucket.get("input_tokens", 0) or 0),
                    "output_tokens": int(bucket.get("output_tokens", 0) or 0),
                    "total_tokens": int(bucket.get("total_tokens", 0) or 0),
                }
            )

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.COST_CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        return csv_path

    def _append_chat_log(
        self,
        *,
        chat_id: str,
        stage: str,
        test_source_name: str,
        source_name: str,
        func_name: str,
        llm_model: str,
        temperature: float,
        timeout_seconds: int,
        response_format: str,
        prompt: str,
        response: str,
        elapsed_seconds: float,
        candidate_index: int = 1,
        candidate_count: int = 1,
    ) -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        payload = [
            f"===== {chat_id} =====",
            (
                f"timestamp={timestamp} stage={stage} test_source={test_source_name} "
                f"source={source_name} func={func_name} model={llm_model} temp={temperature:.2f} "
                f"timeout={timeout_seconds}s response_format={response_format} "
                f"candidate={candidate_index}/{candidate_count} prompt_chars={len(prompt or '')} "
                f"response_chars={len(response or '')} elapsed={elapsed_seconds:.2f}s"
            ),
            "[PROMPT]",
            str(prompt or ""),
            "[RESPONSE]",
            str(response or ""),
            f"===== END {chat_id} =====",
            "",
        ]
        with self._chat_log_lock:
            with open(self.chat_log_path, "a", encoding="utf-8") as chat_log:
                chat_log.write("\n".join(payload))

    def _call_llm_logged(
        self,
        *,
        prompt: str,
        llm_model: str,
        timeout_seconds: int,
        temperature: float,
        test_source_name: str,
        source_name: str,
        func_name: str,
        stage: str,
        candidate_index: int = 1,
        candidate_count: int = 1,
        response_format: str = "text",
    ) -> Tuple[str, str, Dict[str, int]]:
        chat_id = self._next_chat_id()
        self.logger.info(
            f"[LLM-CALL] {test_source_name}:{func_name} stage={stage} chat_id={chat_id} model={llm_model} "
            f"temp={temperature:.2f} timeout={timeout_seconds}s candidate={candidate_index}/{candidate_count} "
            f"prompt_chars={len(prompt or '')}"
        )
        llm_start = time.time()
        response_payload = generate_response(
            prompt,
            llm_model,
            temperature=temperature,
            response_format=response_format,
            timeout_seconds=timeout_seconds,
            return_usage=True,
        )
        if isinstance(response_payload, dict):
            response = str(response_payload.get("content", "") or "")
            usage = response_payload.get("usage", {}) or {}
        else:
            response = str(response_payload or "")
            usage = {}
        usage_dict = {
            "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
        }
        self._accumulate_token_usage(source_name, usage_dict)
        elapsed_seconds = time.time() - llm_start
        self._append_chat_log(
            chat_id=chat_id,
            stage=stage,
            test_source_name=test_source_name,
            source_name=source_name,
            func_name=func_name,
            llm_model=llm_model,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
            response_format=response_format,
            prompt=prompt,
            response=response,
            elapsed_seconds=elapsed_seconds,
            candidate_index=candidate_index,
            candidate_count=candidate_count,
        )
        self.logger.info(
            f"[LLM-CALL-RESP] {test_source_name}:{func_name} stage={stage} chat_id={chat_id} elapsed={elapsed_seconds:.1f}s "
            f"response_chars={len(response) if response else 0}"
        )
        return response, chat_id, usage_dict


    @staticmethod
    def _find_forbidden_c_pointer_tokens(text: str) -> List[str]:
        source = str(text or "")
        if not source:
            return []

        patterns = (
            (r"(?:^|[^A-Za-z0-9_])(?:libc|std::ffi|core::ffi|ffi)::c_void\b", "c_void(any namespace)"),
            (r"\bvoid\s*\*", "void*"),
        )
        hits: List[str] = []
        for pattern, label in patterns:
            if re.search(pattern, source):
                hits.append(label)
        return hits

    def _score_rust_style_penalty(self, text: str) -> Tuple[int, str]:
        source = str(text or "")
        ffi_hits = source.count("ffi::c_void")
        raw_mut_hits = source.count("*mut ")
        raw_const_hits = source.count("*const ")
        unsafe_hits = source.count("unsafe {") + source.count(" unsafe ")

        score = 0
        score += ffi_hits * self.style_penalty_ffi_c_void
        score += (raw_mut_hits + raw_const_hits) * self.style_penalty_raw_ptr
        score += unsafe_hits * self.style_penalty_unsafe

        if score <= 0:
            return 0, "style=clean"
        reason = (
            f"style ffi_c_void={ffi_hits} raw_ptr={raw_mut_hits + raw_const_hits} "
            f"unsafe={unsafe_hits}"
        )
        return score, reason

    def _generate_candidates_and_pick_best(
        self,
        prompt: str,
        llm_model: str,
        timeout_seconds: int,
        base_temperature: float,
        candidate_count: int,
        test_source_name: str,
        source_name: str,
        func_name: str,
        include_files: List[str],
        verify_include_files: List[str],
        base_archive: Dict[str, Dict[str, str]],
        remaining_verify_budget: int,
        stage: str,
        allowed_function_names: Optional[Set[str]] = None,
    ) -> Tuple[str, str, int]:
        return self.candidate_selector.select(
            prompt=prompt,
            llm_model=llm_model,
            timeout_seconds=timeout_seconds,
            base_temperature=base_temperature,
            candidate_count=candidate_count,
            test_source_name=test_source_name,
            source_name=source_name,
            func_name=func_name,
            include_files=include_files,
            verify_include_files=verify_include_files,
            base_archive=base_archive,
            remaining_verify_budget=remaining_verify_budget,
            stage=stage,
            allowed_function_names=allowed_function_names,
        )


    def close(self) -> None:
        for workspace, agent in list(self._cc_mini_agent_instances.items()):
            try:
                agent.close()
            except Exception as exc:
                self.logger.info(f"[CC-MINI-FALLBACK-CLOSE-FAIL] workspace={workspace} err={exc}")
        self._cc_mini_agent_instances.clear()

    @classmethod
    def _load_cc_mini_agent_class(cls):
        if cls._cc_mini_agent_import_attempted:
            return cls._cc_mini_agent_class

        cls._cc_mini_agent_import_attempted = True

        repo_root = ""
        for root in cls._cc_mini_candidate_roots():
            if os.path.exists(os.path.join(root, "cc_mini", "__init__.py")):
                repo_root = root
                break

        if not repo_root:
            cls._cc_mini_agent_import_error = "cannot locate cc_mini/__init__.py"
            return None

        try:
            if repo_root not in sys.path:
                sys.path.insert(0, repo_root)
            from cc_mini import CCMini, CCMiniOptions

            cls._cc_mini_agent_class = CCMini
            cls._cc_mini_options_class = CCMiniOptions
            return cls._cc_mini_agent_class
        except Exception as exc:
            cls._cc_mini_agent_import_error = str(exc)
            cls._cc_mini_agent_class = None
            cls._cc_mini_options_class = None
            return None

    def _get_cc_mini_agent_instance(self, workspace_root: str):
        if not self.enable_cc_mini_agent_fallback:
            return None

        workspace_root = os.path.abspath(workspace_root)

        cc_mini_agent_cls = self._load_cc_mini_agent_class()
        if cc_mini_agent_cls is None:
            if not self._cc_mini_agent_warned:
                self.logger.info(
                    f"[CC-MINI-FALLBACK-DISABLED] import failed: {self._cc_mini_agent_import_error}"
                )
                self._cc_mini_agent_warned = True
            return None

        if not self.cc_mini_config_path or not os.path.isfile(self.cc_mini_config_path):
            missing_path = self.cc_mini_config_path or "(empty)"
            self.logger.info(
                f"[CC-MINI-FALLBACK-DISABLED] missing config file: {missing_path}. Please provide cc_mini_config or place .cc-mini.toml in repo root."
            )
            return None

        cc_mini_memory_dir = self._get_cc_mini_memory_dir()

        cc_mini_options: Dict[str, Any] = {}
        cc_mini_options_cls = self.__class__._cc_mini_options_class
        if cc_mini_options_cls is not None:
            try:
                option_kwargs: Dict[str, Any] = {
                    "auto_approve": True,
                    "config": self.cc_mini_config_path,
                    "compact_log_path": self.run_log_path or None,
                }
                if cc_mini_memory_dir:
                    os.makedirs(cc_mini_memory_dir, exist_ok=True)
                    option_kwargs["memory_dir"] = cc_mini_memory_dir
                cc_mini_options["options"] = cc_mini_options_cls(**option_kwargs)
                self.logger.info(f"[CC-MINI-CONFIG] {self.cc_mini_config_path}")
                if cc_mini_memory_dir:
                    self.logger.info(f"[CC-MINI-MEMORY-DIR] {cc_mini_memory_dir}")
            except Exception as exc:
                self.logger.info(
                    f"[CC-MINI-FALLBACK-OPTION-WARN] workspace={workspace_root} err={exc}"
                )

        try:
            agent = CcMiniRuntimeAgentAdapter(
                cc_mini_cls=cc_mini_agent_cls,
                workspace_root=workspace_root,
                cc_mini_options=cc_mini_options,
                command_timeout=self.cc_mini_agent_command_timeout,
                run_log_path=self.run_log_path,
                max_call_attempts=self.cc_mini_max_call_attempts,
            )
        except Exception as exc:
            self.logger.info(
                f"[CC-MINI-FALLBACK-DISABLED] init failed workspace={workspace_root} err={exc}"
            )
            return None

        self._cc_mini_agent_instance_seq += 1
        instance_key = f"{workspace_root}#{self._cc_mini_agent_instance_seq}"
        self._cc_mini_agent_instances[instance_key] = agent
        self.logger.info(
            f"[CC-MINI-FALLBACK-READY] workspace={workspace_root} isolated=1 instance={self._cc_mini_agent_instance_seq}"
        )
        return agent

    def _get_cc_mini_memory_dir(self) -> str:
        output_dir = str(self.output_dir or "").strip()
        if not output_dir:
            return ""
        return os.path.join(os.path.abspath(output_dir), "state", "cc_mini_memory")

    def _extract_direct_callees_from_c_body(
        self,
        test_source_name: str,
        func_name: str,
    ) -> List[str]:
        cache_key = (test_source_name, func_name)
        cached = self._heuristic_direct_callee_cache.get(cache_key)
        if cached is not None:
            return list(cached)

        source_context = ""
        if test_source_name in self.source_names:
            source_idx = self.source_names.index(test_source_name)
            source_bucket = self.data_manager.data[source_idx] if 0 <= source_idx < len(self.data_manager.data) else {}
            source_context = (source_bucket.get(func_name, "") or "")

        if not source_context:
            # Prefer current include scope to avoid same-name function cross-source contamination.
            source_context, _, _ = self.data_manager.get_content(func_name, respect_scope=True)

        if not source_context:
            # Final fallback when include scope cannot resolve the function body.
            source_context, _, _ = self.data_manager.get_content(func_name, respect_scope=False)

        if not source_context:
            self._heuristic_direct_callee_cache[cache_key] = []
            return []

        skip_tokens = {
            "if",
            "for",
            "while",
            "switch",
            "return",
            "sizeof",
            "alignof",
            "typeof",
            "assert",
        }
        known_functions = set(getattr(self.data_manager, "func_to_indices", {}).keys())
        hinted: List[str] = []
        seen: Set[str] = set()
        text = source_context
        n = len(text)
        i = 0

        while i < n:
            ch = text[i]
            if not (ch == "_" or ch.isalpha()):
                i += 1
                continue

            start = i
            i += 1
            while i < n and self._is_ident_char(text[i]):
                i += 1
            ident = text[start:i]

            j = i
            while j < n and text[j].isspace():
                j += 1

            if j < n and text[j] == "(":
                if (
                    ident not in skip_tokens
                    and ident != func_name
                    and ident in known_functions
                    and ident not in seen
                ):
                    hinted.append(ident)
                    seen.add(ident)

            i = max(i, j)

        self._heuristic_direct_callee_cache[cache_key] = list(hinted)
        return hinted
