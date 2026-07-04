"""Candidate selection for multi-sample LLM translation responses.

The pipeline asks the model for multiple candidate translations and cheaply
scores them before committing one response back into the worker loop. This
module keeps that policy independent from `TranslationPipeline`: callers inject
the LLM boundary, archive merge/render operations, verifier, and scoring rules.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from utils import normalize_rust_module_name, remove_markdown_code_block


class LlmCandidateSelector:
    """Pick the best response from multiple LLM candidates.

    Dependencies are injected as callables so tests can cover candidate
    selection behavior with deterministic fakes instead of subclassing the full
    translation pipeline.
    """

    def __init__(
        self,
        *,
        call_llm_logged: Callable[..., Tuple[str, str, Dict[str, int]]],
        apply_response_to_archive: Callable[..., Tuple[Optional[Dict[str, Dict[str, str]]], str]],
        build_module_sources: Callable[[Dict[str, Dict[str, str]], List[str]], Tuple[Dict[str, str], Any]],
        verifier: Any,
        score_verify_result: Callable[[Any], Tuple[int, str]],
        score_rust_style_penalty: Callable[[str], Tuple[int, str]],
        find_forbidden_c_pointer_tokens: Callable[[str], List[str]],
        is_llm_transport_error: Callable[[str], bool],
        logger: Any,
        temperature_step: float,
        max_temperature: float,
        hard_reject_c_pointers: bool,
    ):
        self._call_llm_logged = call_llm_logged
        self._apply_response_to_archive = apply_response_to_archive
        self._build_module_sources = build_module_sources
        self._verifier = verifier
        self._score_verify_result = score_verify_result
        self._score_rust_style_penalty = score_rust_style_penalty
        self._find_forbidden_c_pointer_tokens = find_forbidden_c_pointer_tokens
        self._is_llm_transport_error = is_llm_transport_error
        self._logger = logger
        self._temperature_step = float(temperature_step)
        self._max_temperature = float(max_temperature)
        self._hard_reject_c_pointers = bool(hard_reject_c_pointers)

    def select(
        self,
        *,
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
        """Return `(response, chat_id, verify_invocations_used)` for the best candidate."""
        enforce_forbidden_tokens = self._hard_reject_c_pointers and str(stage).lower() in {"initial", "regen"}
        first_response, first_chat_id, _ = self._call_llm_logged(
            prompt=prompt,
            llm_model=llm_model,
            timeout_seconds=timeout_seconds,
            temperature=base_temperature,
            test_source_name=test_source_name,
            source_name=source_name,
            func_name=func_name,
            stage=stage,
            candidate_index=1,
            candidate_count=candidate_count,
        )
        if candidate_count <= 1:
            return first_response, first_chat_id, 0
        if first_response == "上下文长度超过限制":
            return first_response, first_chat_id, 0

        used_verify = 0
        best_response = first_response
        best_chat_id = first_chat_id
        best_score = 999999999

        responses: List[Tuple[int, str, float, str]] = [(1, first_response, base_temperature, first_chat_id)]
        for idx in range(2, candidate_count + 1):
            temperature = min(
                base_temperature + self._temperature_step * float(idx - 1),
                self._max_temperature,
            )
            response, chat_id, _ = self._call_llm_logged(
                prompt=prompt,
                llm_model=llm_model,
                timeout_seconds=timeout_seconds,
                temperature=temperature,
                test_source_name=test_source_name,
                source_name=source_name,
                func_name=func_name,
                stage=stage,
                candidate_index=idx,
                candidate_count=candidate_count,
            )
            responses.append((idx, response, temperature, chat_id))

        for idx, response, temperature, chat_id in responses:
            if response == "上下文长度超过限制":
                self._info(
                    f"[CANDIDATE-SCORE] {test_source_name}:{func_name} cand={idx}/{candidate_count} "
                    f"chat_id={chat_id} temp={temperature:.2f} context-limit"
                )
                continue
            if self._is_llm_transport_error(response):
                score = 950000
                best_response, best_chat_id, best_score = self._keep_if_better(
                    score,
                    best_score,
                    response,
                    chat_id,
                    best_response,
                    best_chat_id,
                )
                self._info(
                    f"[CANDIDATE-SCORE] {test_source_name}:{func_name} cand={idx}/{candidate_count} "
                    f"chat_id={chat_id} temp={temperature:.2f} score={score} transport-error"
                )
                continue

            clean_response = remove_markdown_code_block(response)
            style_penalty, style_reason = self._score_rust_style_penalty(clean_response)
            if enforce_forbidden_tokens:
                forbidden_hits = self._find_forbidden_c_pointer_tokens(clean_response)
                if forbidden_hits:
                    score = 800000 + style_penalty
                    best_response, best_chat_id, best_score = self._keep_if_better(
                        score,
                        best_score,
                        response,
                        chat_id,
                        best_response,
                        best_chat_id,
                    )
                    self._info(
                        f"[CANDIDATE-SCORE] {test_source_name}:{func_name} cand={idx}/{candidate_count} "
                        f"chat_id={chat_id} temp={temperature:.2f} score={score} "
                        f"forbidden-ptr tokens={','.join(forbidden_hits)}"
                    )
                    continue

            candidate_results, merge_error = self._apply_response_to_archive(
                clean_response,
                func_name,
                source_name,
                include_files,
                base_archive,
                allowed_function_names=allowed_function_names,
                enforce_forbidden_tokens=enforce_forbidden_tokens,
            )
            if merge_error:
                score = 700000 + style_penalty
                best_response, best_chat_id, best_score = self._keep_if_better(
                    score,
                    best_score,
                    response,
                    chat_id,
                    best_response,
                    best_chat_id,
                )
                self._info(
                    f"[CANDIDATE-SCORE] {test_source_name}:{func_name} cand={idx}/{candidate_count} "
                    f"chat_id={chat_id} temp={temperature:.2f} score={score} parse-fail {style_reason}"
                )
                continue

            if used_verify >= max(0, remaining_verify_budget):
                score = 500000 + style_penalty
                best_response, best_chat_id, best_score = self._keep_if_better(
                    score,
                    best_score,
                    response,
                    chat_id,
                    best_response,
                    best_chat_id,
                )
                self._info(
                    f"[CANDIDATE-SCORE] {test_source_name}:{func_name} cand={idx}/{candidate_count} "
                    f"chat_id={chat_id} temp={temperature:.2f} score={score} no-verify-budget {style_reason}"
                )
                continue

            module_sources, _ = self._build_module_sources(candidate_results, verify_include_files)
            verify_result = self._verifier.verify_modules(
                module_sources=module_sources,
                crate_name=f"verify_{normalize_rust_module_name(test_source_name)}_cand_{idx}",
            )
            used_verify += 1
            compile_score, reason = self._score_verify_result(verify_result)
            score = compile_score + style_penalty
            best_response, best_chat_id, best_score = self._keep_if_better(
                score,
                best_score,
                response,
                chat_id,
                best_response,
                best_chat_id,
            )
            self._info(
                f"[CANDIDATE-SCORE] {test_source_name}:{func_name} cand={idx}/{candidate_count} "
                f"chat_id={chat_id} temp={temperature:.2f} score={score} compile_score={compile_score} "
                f"style_penalty={style_penalty} {reason} {style_reason}"
            )
            if getattr(verify_result, "success", False) and style_penalty == 0:
                break

        self._info(
            f"[CANDIDATE-PICK] {test_source_name}:{func_name} chat_id={best_chat_id} "
            f"picked_score={best_score} verify_used={used_verify}/{max(0, remaining_verify_budget)}"
        )
        return best_response, best_chat_id, used_verify

    @staticmethod
    def _keep_if_better(
        score: int,
        best_score: int,
        response: str,
        chat_id: str,
        best_response: str,
        best_chat_id: str,
    ) -> Tuple[str, str, int]:
        if score < best_score:
            return response, chat_id, score
        return best_response, best_chat_id, best_score

    def _info(self, message: str) -> None:
        if hasattr(self._logger, "info"):
            self._logger.info(message)
