"""Function scheduling and dependency-cycle handling for translation.

This module owns ready-queue ordering, strict dependency blocking, and the
cycle-probe placeholder flow. It calls back into `TranslationPipeline.process_func`
for the actual translation attempt, so algorithm behavior stays unchanged while
the orchestration code is easier to read.
"""

import random
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from pipeline.stats import increment_dynamic_dependency_add_count
from utils import is_rust_snippet_brace_balanced

try:
    from tqdm import tqdm
except ModuleNotFoundError:
    class _TqdmFallback:
        def __init__(self, iterable=None, total=None, desc=None):
            self.iterable = iterable if iterable is not None else range(int(total or 0))

        def __iter__(self):
            return iter(self.iterable)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_postfix(self, **kwargs):
            return None

        def update(self, n=1):
            return None

    def tqdm(iterable=None, total=None, desc=None):
        return _TqdmFallback(iterable=iterable, total=total, desc=desc)


class TranslationScheduler:
    """Schedule functions in dependency order and handle cycle probes."""

    _cycle_placeholder_marker = "__CYCLE_PLACEHOLDER__"

    @classmethod
    def _is_cycle_placeholder_function(cls, snippet: str) -> bool:
        text = str(snippet or "")
        if not text.strip():
            return False
        lowered = text.lower()
        marker = cls._cycle_placeholder_marker.lower()
        return marker in lowered or "unimplemented!(" in lowered or "todo!(" in lowered

    @staticmethod
    def _find_blocked_cycle_group(
        next_pending: List[Tuple[str, int]],
        blocked_map: Dict[str, List[str]],
        anchor_func: str,
    ) -> List[str]:
        pending_names = [name for name, _ in next_pending]
        pending_set = set(pending_names)
        if anchor_func not in pending_set:
            return []

        adj: Dict[str, List[str]] = {}
        for name in pending_names:
            deps = [dep for dep in blocked_map.get(name, []) if dep in pending_set]
            # Preserve order while de-duplicating.
            seen: Set[str] = set()
            uniq: List[str] = []
            for dep in deps:
                if dep in seen:
                    continue
                seen.add(dep)
                uniq.append(dep)
            adj[name] = uniq

        index = 0
        indices: Dict[str, int] = {}
        lowlink: Dict[str, int] = {}
        stack: List[str] = []
        on_stack: Set[str] = set()
        components: List[List[str]] = []

        def strong_connect(v: str) -> None:
            nonlocal index
            indices[v] = index
            lowlink[v] = index
            index += 1
            stack.append(v)
            on_stack.add(v)

            for w in adj.get(v, []):
                if w not in indices:
                    strong_connect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], indices[w])

            if lowlink[v] == indices[v]:
                component: List[str] = []
                while stack:
                    w = stack.pop()
                    on_stack.discard(w)
                    component.append(w)
                    if w == v:
                        break
                components.append(component)

        for name in pending_names:
            if name not in indices:
                strong_connect(name)

        for comp in components:
            if anchor_func not in comp:
                continue
            if len(comp) > 1:
                ordered = [name for name in pending_names if name in set(comp)]
                return ordered
            only = comp[0]
            if only in adj.get(only, []):
                return [only]
            break

        # Fallback: anchor + blocked peers in current pending queue.
        fallback = [anchor_func]
        for dep in adj.get(anchor_func, []):
            if dep != anchor_func and dep not in fallback:
                fallback.append(dep)
        return fallback

    def _build_cycle_stub_prompt_note(
        self,
        test_source_name: str,
        source_name: str,
        cycle_peers: List[str],
        results: Dict[str, Dict[str, str]],
    ) -> str:
        peers = [name for name in cycle_peers if name]
        if not peers:
            return ""

        placeholder_body = (
            f"// {self._cycle_placeholder_marker}\\n"
            'unimplemented!("cycle placeholder")'
        )

        lines: List[str] = [
            "\n\n环依赖处理指令（高优先级）：",
            "当前函数处于循环依赖打破流程。请在本轮除目标函数外，为下列环内函数补齐最小占位实现：",
            f"占位函数体统一使用 `{placeholder_body}`。",
            "这些占位函数必须保留正确函数名和参数/返回类型签名，后续轮次会逐个补全真实主体。",
            f"cycle_source={test_source_name}",
        ]

        for peer in peers:
            owner = self.data_manager.get_source_name_by_func_name(
                peer,
                preferred_source=source_name,
                respect_scope=True,
            )
            existing = results.get(owner or "", {}).get(peer, "") if owner else ""
            signature = self._extract_function_signature(existing)
            if signature:
                lines.append(f"- {peer}: {signature} {{ {placeholder_body} }}")
            else:
                lines.append(f"- {peer}: 若当前无 Rust 签名，请根据对应 C 函数生成签名，并使用占位函数体")

        return "\n".join(lines).strip()

    def _refresh_cycle_placeholder_state(
        self,
        test_source_name: str,
        results: Dict[str, Dict[str, str]],
        focus_funcs: Optional[Set[str]] = None,
    ) -> None:
        active = self._cycle_placeholder_active.setdefault(test_source_name, set())
        candidates: Set[str] = set(active)
        if focus_funcs:
            candidates.update(focus_funcs)

        for func_name in list(candidates):
            owner = self.data_manager.get_source_name_by_func_name(
                func_name,
                preferred_source=test_source_name,
                respect_scope=False,
            )
            snippet = results.get(owner or "", {}).get(func_name, "") if owner else ""
            if self._is_cycle_placeholder_function(snippet):
                active.add(func_name)
            else:
                active.discard(func_name)

        if not active and test_source_name in self._cycle_placeholder_active:
            del self._cycle_placeholder_active[test_source_name]

    def _same_cycle_group(self, test_source_name: str, lhs: str, rhs: str) -> bool:
        group_map = self._cycle_group_members.get(test_source_name, {})
        lhs_group = group_map.get(lhs)
        return bool(lhs_group and rhs in lhs_group)

    @staticmethod
    def _set_tqdm_total(pbar, total: int) -> None:
        if hasattr(pbar, "total"):
            try:
                pbar.total = int(total)
                refresh = getattr(pbar, "refresh", None)
                if callable(refresh):
                    refresh()
            except Exception:
                pass

    def _has_valid_existing_function(
        self,
        func_name: str,
        owner_source: str,
        results: Dict[str, Dict[str, str]],
    ) -> bool:
        snippet = results.get(owner_source or "", {}).get(func_name, "")
        return (
            bool(str(snippet or "").strip())
            and is_rust_snippet_brace_balanced(snippet)
            and not self._is_cycle_placeholder_function(snippet)
        )

    @staticmethod
    def _clear_function_error_record(
        all_error_funcs_content: Dict[str, Dict[str, str]],
        source_name: str,
        func_name: str,
    ) -> bool:
        source_errors = all_error_funcs_content.get(source_name, {})
        if func_name not in source_errors:
            return False
        del source_errors[func_name]
        if not source_errors and source_name in all_error_funcs_content:
            del all_error_funcs_content[source_name]
        return True

    def _resolve_dynamic_dependency_owner(
        self,
        test_source_name: str,
        child: str,
    ) -> str:
        owner_source = self.data_manager.get_source_name_by_func_name(
            child,
            preferred_source=test_source_name,
            respect_scope=True,
        ) or ""
        if not owner_source:
            return ""
        if self._is_excluded_source_name(owner_source):
            return ""
        return owner_source

    @staticmethod
    def _has_failure_record_for_func(
        func_name: str,
        all_error_funcs_content: Dict[str, Dict[str, str]],
    ) -> bool:
        for source_errors in all_error_funcs_content.values():
            if func_name in source_errors:
                return True
        return False

    def _sort_ready_candidates_root_first(
        self,
        test_source_name: str,
        ready: List[Tuple[str, int]],
        all_error_funcs_content: Dict[str, Dict[str, str]],
    ) -> List[Tuple[str, int]]:
        funcs_child = self.funcs_childs.get(test_source_name, {}) or {}
        parent_counts: Dict[str, int] = defaultdict(int)
        for parent, children in funcs_child.items():
            if not isinstance(children, list):
                continue
            for child in children:
                if not child or child == parent:
                    continue
                parent_counts[child] += 1

        def score(item: Tuple[str, int]) -> Tuple[int, int, int, int]:
            func_name, depth = item
            has_history_fail = 1 if self._has_failure_record_for_func(func_name, all_error_funcs_content) else 0
            parent_count = parent_counts.get(func_name, 0)
            child_count = len(funcs_child.get(func_name, []) or [])
            return (has_history_fail, parent_count, child_count, -depth)

        return sorted(ready, key=score, reverse=True)

    def process_test_source(
        self,
        test_source_name: str,
        funcs_depth,
        results: Dict[str, Dict[str, str]],
        all_error_funcs_content: Dict[str, Dict[str, str]],
        once_retry_count_dict: Dict[str, Dict[str, int]],
    ) -> None:
        self._mark_module_start(test_source_name)
        # test-uncovered_* sources are virtual buckets generated by callgraph.
        # They may not have a standalone json file, but should still drive
        # translation of uncovered dependency-module functions.
        if test_source_name not in self.source_names and not test_source_name.startswith("test-uncovered_"):
            return

        self.data_manager.get_include_indices(test_source_name)
        iterable = list(funcs_depth.items())

        if self.ablation_random_order:
            random_items = list(iterable)
            source_seed = self.ablation_random_seed + sum(
                (idx + 1) * ord(ch) for idx, ch in enumerate(test_source_name)
            )
            rng = random.Random(source_seed)
            rng.shuffle(random_items)
            self.logger.info(
                "[RANDOM-ORDER][FUNC] %s seed=%d order=%s"
                % (
                    test_source_name,
                    source_seed,
                    ",".join(name for name, _ in random_items[:12]),
                )
            )

            with tqdm(total=len(random_items), desc=test_source_name) as pbar:
                for func_name, depth in random_items:
                    pbar.set_postfix(func_name=func_name)
                    self.process_func(
                        test_source_name=test_source_name,
                        func_name=func_name,
                        depth=depth,
                        results=results,
                        all_error_funcs_content=all_error_funcs_content,
                        once_retry_count_dict=once_retry_count_dict,
                    )
                    pbar.update(1)
                    if self.checkpoint_hook:
                        self.checkpoint_hook()
            source_runtime_check = getattr(self, "_run_source_runtime_check_after_completion", None)
            if source_runtime_check:
                source_runtime_check(
                    test_source_name=test_source_name,
                    results=results,
                    all_error_funcs_content=all_error_funcs_content,
                )
            return

        pending = list(iterable)
        scheduled_funcs: Set[str] = {name for name, _ in pending}
        source_completed = not pending
        deferred_logged: Set[str] = set()
        cycle_probe_attempts = 0
        probed_funcs: Set[str] = set()
        round_idx = 0
        source_cycle_probe_budget = max(
            self.max_cycle_probe_attempts_per_source,
            len(pending),
        )

        with tqdm(total=len(iterable), desc=test_source_name) as pbar:
            while pending:
                self._refresh_cycle_placeholder_state(
                    test_source_name=test_source_name,
                    results=results,
                )
                round_idx += 1
                progressed = False
                next_pending: List[Tuple[str, int]] = []
                ready: List[Tuple[str, int]] = []
                blocked_map: Dict[str, List[str]] = {}
                dynamic_pending: List[Tuple[str, int]] = []

                for func_name, depth in pending:
                    unmet = self._collect_unfinished_direct_callees(
                        test_source_name=test_source_name,
                        func_name=func_name,
                        results=results,
                        all_error_funcs_content=all_error_funcs_content,
                    )

                    if unmet:
                        unresolved: List[str] = []
                        for child in unmet:
                            owner_source = self._resolve_dynamic_dependency_owner(
                                test_source_name,
                                child,
                            )
                            if not owner_source:
                                unresolved.append(child)
                                continue
                            if child not in scheduled_funcs:
                                scheduled_funcs.add(child)
                                child_depth = max(0, depth + 1)
                                dynamic_pending.append((child, child_depth))
                                self.logger.info(
                                    "[DYNAMIC-DEPS-ADD] "
                                    f"source={test_source_name} parent={func_name} "
                                    f"child={child} owner={owner_source}"
                                )
                                increment_dynamic_dependency_add_count()
                            unresolved.append(child)

                        if not unresolved:
                            ready.append((func_name, depth))
                            continue

                        next_pending.append((func_name, depth))
                        blocked_map[func_name] = list(unresolved)
                        if func_name not in deferred_logged:
                            self.logger.info(
                                f"[DEFER] {test_source_name}:{func_name} waiting_on={','.join(unresolved[:6])}"
                            )
                            deferred_logged.add(func_name)
                        continue

                    ready.append((func_name, depth))

                if self.root_cause_first and len(ready) > 1:
                    ready = self._sort_ready_candidates_root_first(
                        test_source_name=test_source_name,
                        ready=ready,
                        all_error_funcs_content=all_error_funcs_content,
                    )
                    self.logger.info(
                        f"[ROOT-FIRST] {test_source_name} round={round_idx} order={','.join(name for name, _ in ready[:8])}"
                    )

                processed_count = 0
                for func_name, depth in ready:
                    pbar.set_postfix(func_name=func_name)
                    self.process_func(
                        test_source_name=test_source_name,
                        func_name=func_name,
                        depth=depth,
                        results=results,
                        all_error_funcs_content=all_error_funcs_content,
                        once_retry_count_dict=once_retry_count_dict,
                    )
                    pbar.update(1)
                    progressed = True
                    processed_count += 1
                    if self.checkpoint_hook:
                        self.checkpoint_hook()

                if self.source_round_summary_enabled:
                    self.logger.info(
                        "[SOURCE-ROUND] %s round=%d pending=%d ready=%d processed=%d blocked=%d"
                        % (
                            test_source_name,
                            round_idx,
                            len(pending),
                            len(ready),
                            processed_count,
                            len(next_pending),
                        )
                    )

                if not next_pending:
                    source_completed = True
                    break

                if dynamic_pending:
                    pending = dynamic_pending + next_pending
                    source_cycle_probe_budget = max(
                        source_cycle_probe_budget,
                        len(scheduled_funcs),
                    )
                    self._set_tqdm_total(pbar, len(scheduled_funcs))
                    continue

                if progressed:
                    pending = next_pending
                    continue

                if (
                    self.dependency_cycle_probe
                    and cycle_probe_attempts < source_cycle_probe_budget
                    and next_pending
                ):
                    cycle_probe_budget = source_cycle_probe_budget
                    probe_candidates = [
                        item
                        for item in next_pending
                        if item[0] not in probed_funcs
                    ]
                    if self._is_test_source(test_source_name):
                        filtered_probe_candidates: List[Tuple[str, int]] = []
                        for cand_name, cand_depth in probe_candidates:
                            cand_owner = self.data_manager.get_source_name_by_func_name(
                                cand_name,
                                preferred_source=test_source_name,
                                respect_scope=True,
                            ) or ""
                            if self._is_test_source(cand_owner):
                                continue
                            filtered_probe_candidates.append((cand_name, cand_depth))
                        probe_candidates = filtered_probe_candidates
                    non_existing_probe_candidates: List[Tuple[str, int]] = []
                    for cand_name, cand_depth in probe_candidates:
                        cand_owner = self.data_manager.get_source_name_by_func_name(
                            cand_name,
                            preferred_source=test_source_name,
                            respect_scope=True,
                        ) or self.data_manager.get_source_name_by_func_name(
                            cand_name,
                            preferred_source=test_source_name,
                            respect_scope=False,
                        ) or ""
                        if cand_owner and self._has_valid_existing_function(
                            cand_name,
                            cand_owner,
                            results,
                        ):
                            self.logger.info(
                                f"[CYCLE-PROBE-SKIP-EXISTING] {test_source_name}:{cand_name}"
                            )
                            continue
                        non_existing_probe_candidates.append((cand_name, cand_depth))
                    probe_candidates = non_existing_probe_candidates
                    if probe_candidates:
                        probe_func, probe_depth = min(
                            probe_candidates,
                            key=lambda item: (
                                len(blocked_map.get(item[0], [])),
                                item[1],
                            ),
                        )
                        cycle_group = self._find_blocked_cycle_group(
                            next_pending=next_pending,
                            blocked_map=blocked_map,
                            anchor_func=probe_func,
                        )
                        if cycle_group:
                            cycle_set = set(cycle_group)
                            group_map = self._cycle_group_members.setdefault(test_source_name, {})
                            for cycle_name in cycle_set:
                                group_map[cycle_name] = set(cycle_set)
                        cycle_peers = [name for name in cycle_group if name != probe_func]
                        if cycle_peers:
                            self._cycle_probe_stub_plan[(test_source_name, probe_func)] = cycle_peers

                        cycle_probe_attempts += 1
                        probed_funcs.add(probe_func)
                        unmet = blocked_map.get(probe_func, [])
                        self.logger.warning(
                            f"[CYCLE-PROBE] {test_source_name} attempt={cycle_probe_attempts}/{cycle_probe_budget} func={probe_func} unmet={','.join(unmet[:6])}"
                        )
                        if cycle_peers:
                            self.logger.warning(
                                f"[CYCLE-STUB-PLAN] {test_source_name} probe={probe_func} peers={','.join(cycle_peers[:8])}"
                            )

                        pbar.set_postfix(func_name=probe_func)
                        self.process_func(
                            test_source_name=test_source_name,
                            func_name=probe_func,
                            depth=probe_depth,
                            results=results,
                            all_error_funcs_content=all_error_funcs_content,
                            once_retry_count_dict=once_retry_count_dict,
                        )
                        pbar.update(1)
                        if self.checkpoint_hook:
                            self.checkpoint_hook()
                        self._refresh_cycle_placeholder_state(
                            test_source_name=test_source_name,
                            results=results,
                            focus_funcs=set(cycle_group),
                        )

                        pending = [item for item in next_pending if item[0] != probe_func]
                        continue

                if not self.blocked_fast_fail:
                    self.logger.error(
                        f"[BLOCKED-DEPS-DEFERRED] {test_source_name} unresolved_round={len(next_pending)}"
                    )
                    break

                # Strict dependency gate: callers must wait until direct callees are done.
                blocked_labels: List[str] = []
                for blocked_func, _ in next_pending:
                    owner_source = self.data_manager.get_source_name_by_func_name(
                        blocked_func,
                        preferred_source=test_source_name,
                    ) or test_source_name
                    if self._has_valid_existing_function(blocked_func, owner_source, results):
                        if self._clear_function_error_record(
                            all_error_funcs_content,
                            owner_source,
                            blocked_func,
                        ):
                            self.logger.info(
                                f"[CLEAR-STALE-ERROR] {owner_source}:{blocked_func} valid checkpoint function"
                            )
                        self.logger.info(
                            f"[BLOCKED-DEPS-SKIP-EXISTING] {test_source_name}:{blocked_func}"
                        )
                        continue
                    unmet = blocked_map.get(blocked_func, [])
                    all_error_funcs_content.setdefault(owner_source, {})[blocked_func] = (
                        "// 依赖函数未完成，严格调度阻塞: " + ", ".join(unmet[:8])
                    )
                    blocked_labels.append(f"{blocked_func}<-{','.join(unmet[:4])}")

                if blocked_labels:
                    self.logger.error(
                        f"[BLOCKED-DEPS] {test_source_name} unresolved={'; '.join(blocked_labels[:8])}"
                    )
                if self.checkpoint_hook:
                    self.checkpoint_hook()
                break

        if source_completed:
            source_runtime_check = getattr(self, "_run_source_runtime_check_after_completion", None)
            if source_runtime_check:
                source_runtime_check(
                    test_source_name=test_source_name,
                    results=results,
                    all_error_funcs_content=all_error_funcs_content,
                )

    def _is_function_translation_complete(
        self,
        func_name: str,
        results: Dict[str, Dict[str, str]],
        all_error_funcs_content: Dict[str, Dict[str, str]],
        owner_source: str = "",
        test_source_name: str = "",
    ) -> bool:
        if not owner_source:
            owner_source = self.data_manager.get_source_name_by_func_name(
                func_name,
                respect_scope=False,
            )
        if not owner_source:
            return True
        source_bucket = results.get(owner_source, {})
        snippet = source_bucket.get(func_name, "")
        if not snippet.strip() or not is_rust_snippet_brace_balanced(snippet):
            return False
        if self._is_cycle_placeholder_function(snippet):
            return False

        if test_source_name:
            group_map = self._cycle_group_members.get(test_source_name, {})
            cycle_group = group_map.get(func_name)
            if cycle_group:
                for peer_name in cycle_group:
                    peer_owner = self.data_manager.get_source_name_by_func_name(
                        peer_name,
                        preferred_source=test_source_name,
                        respect_scope=False,
                    )
                    if not peer_owner:
                        continue
                    peer_snippet = results.get(peer_owner, {}).get(peer_name, "")
                    if self._is_cycle_placeholder_function(peer_snippet):
                        return False

        if func_name in all_error_funcs_content.get(owner_source, {}):
            if self._has_valid_existing_function(func_name, owner_source, results):
                self._clear_function_error_record(
                    all_error_funcs_content,
                    owner_source,
                    func_name,
                )
                return True
            return False
        return True

    def _is_excluded_source_name(self, source_name: str) -> bool:
        name = str(source_name or "").strip()
        if not name:
            return False
        if name in self.excluded_sources:
            return True
        if name.startswith("test-uncovered_"):
            base = name.replace("test-uncovered_", "", 1)
            return base in self.excluded_sources or f"test-{base}" in self.excluded_sources
        return False

    def _collect_unfinished_direct_callees(
        self,
        test_source_name: str,
        func_name: str,
        results: Dict[str, Dict[str, str]],
        all_error_funcs_content: Dict[str, Dict[str, str]],
    ) -> List[str]:
        funcs_child = self.funcs_childs.get(test_source_name, {}) or {}
        children = list(funcs_child.get(func_name, []) or [])
        if self.heuristic_test_dep_extraction and self._is_test_source(test_source_name):
            for hinted in self._extract_direct_callees_from_c_body(test_source_name, func_name):
                if hinted and hinted not in children:
                    children.append(hinted)
        if not children:
            return []

        unfinished: List[str] = []
        for child in children:
            if not child or child == func_name:
                continue
            if child in self.excluded_function_names:
                continue

            owner_source = self.data_manager.get_source_name_by_func_name(
                child,
                preferred_source=test_source_name,
                respect_scope=True,
            )
            if not owner_source and child in self.data_manager.all_pointer_funcs:
                # Keep function-pointer dependency coverage: if a child is recognized
                # as pointer-derived, allow cross-scope owner resolution as fallback.
                owner_source = self.data_manager.get_source_name_by_func_name(
                    child,
                    preferred_source=test_source_name,
                    respect_scope=False,
                )
            if not owner_source:
                # External/runtime symbol not in translation corpus should not block scheduling.
                continue
            if self._is_excluded_source_name(owner_source):
                # Excluded dependency source should not block scheduling.
                continue

            if not self._is_function_translation_complete(
                func_name=child,
                results=results,
                all_error_funcs_content=all_error_funcs_content,
                owner_source=owner_source,
                test_source_name=test_source_name,
            ):
                active_placeholders = self._cycle_placeholder_active.get(test_source_name, set())
                child_snippet = results.get(owner_source, {}).get(child, "")
                if (
                    child in active_placeholders
                    and self._is_cycle_placeholder_function(child_snippet)
                    and self._same_cycle_group(test_source_name, func_name, child)
                ):
                    # During cycle-breaking, placeholder stubs can temporarily unblock peers.
                    continue
                unfinished.append(child)

        return unfinished
