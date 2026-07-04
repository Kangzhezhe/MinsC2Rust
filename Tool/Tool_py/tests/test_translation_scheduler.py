import sys
import unittest
from pathlib import Path


TOOL_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = TOOL_ROOT / "src"
sys.path.insert(0, str(TOOL_ROOT))
sys.path.insert(0, str(SRC_ROOT))

from pipeline.translation_scheduler import TranslationScheduler


class _DataManager:
    def get_source_name_by_func_name(self, func_name, **kwargs):
        return "src"

    def get_include_indices(self, source_name):
        return []


class _ScopedDataManager:
    def __init__(self, owners):
        self.owners = dict(owners)
        self.all_pointer_funcs = set()

    def get_source_name_by_func_name(self, func_name, **kwargs):
        if kwargs.get("respect_scope"):
            return self.owners.get(func_name, "")
        return self.owners.get(func_name, "")

    def get_include_indices(self, source_name):
        return []


class _SplitScopeDataManager:
    def __init__(self, scoped_owners, global_owners, pointer_funcs=None):
        self.scoped_owners = dict(scoped_owners)
        self.global_owners = dict(global_owners)
        self.all_pointer_funcs = set(pointer_funcs or [])

    def get_source_name_by_func_name(self, func_name, **kwargs):
        if kwargs.get("respect_scope"):
            return self.scoped_owners.get(func_name, "")
        return self.global_owners.get(func_name, "")

    def get_include_indices(self, source_name):
        return []


class _Logger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(str(message))

    def warning(self, message):
        self.messages.append(str(message))

    def error(self, message):
        self.messages.append(str(message))


def _base_process_scheduler():
    scheduler = TranslationScheduler()
    scheduler.source_names = ["test_src", "src"]
    scheduler.data_manager = _ScopedDataManager({"root": "test_src", "leaf": "src"})
    scheduler.funcs_childs = {"test_src": {"root": ["leaf"]}}
    scheduler.logger = _Logger()
    scheduler.ablation_random_order = False
    scheduler.ablation_random_seed = 0
    scheduler.root_cause_first = False
    scheduler.source_round_summary_enabled = True
    scheduler.dependency_cycle_probe = False
    scheduler.max_cycle_probe_attempts_per_source = 3
    scheduler.blocked_fast_fail = True
    scheduler.heuristic_test_dep_extraction = False
    scheduler.excluded_sources = set()
    scheduler.excluded_function_names = set()
    scheduler._cycle_group_members = {}
    scheduler._cycle_placeholder_active = {}
    scheduler._cycle_probe_stub_plan = {}
    scheduler.checkpoint_hook = None
    scheduler._mark_module_start = lambda source_name: None
    scheduler._is_test_source = lambda source_name: str(source_name).startswith("test")
    scheduler._extract_direct_callees_from_c_body = lambda test_source_name, func_name: []
    scheduler.processed = []

    def process_func(**kwargs):
        func_name = kwargs["func_name"]
        scheduler.processed.append(func_name)
        owner = scheduler.data_manager.get_source_name_by_func_name(
            func_name,
            preferred_source=kwargs["test_source_name"],
            respect_scope=True,
        )
        if owner:
            kwargs["results"].setdefault(owner, {})[func_name] = f"pub fn {func_name}() {{}}"

    scheduler.process_func = process_func
    return scheduler


def _scheduler():
    scheduler = TranslationScheduler()
    scheduler.funcs_childs = {
        "test_src": {
            "root": ["leaf_a", "leaf_b"],
            "leaf_a": [],
            "leaf_b": [],
        }
    }
    scheduler.data_manager = _DataManager()
    scheduler._cycle_group_members = {}
    return scheduler


class TranslationSchedulerTest(unittest.TestCase):
    def test_find_blocked_cycle_group_returns_ordered_cycle_members(self):
        group = TranslationScheduler._find_blocked_cycle_group(
            next_pending=[("a", 1), ("b", 2), ("c", 3), ("d", 4)],
            blocked_map={
                "a": ["b"],
                "b": ["c"],
                "c": ["a"],
                "d": ["a"],
            },
            anchor_func="b",
        )

        self.assertEqual(group, ["a", "b", "c"])

    def test_find_blocked_cycle_group_returns_self_cycle(self):
        group = TranslationScheduler._find_blocked_cycle_group(
            next_pending=[("a", 1)],
            blocked_map={"a": ["a"]},
            anchor_func="a",
        )

        self.assertEqual(group, ["a"])

    def test_has_failure_record_for_func_searches_all_sources(self):
        self.assertTrue(
            TranslationScheduler._has_failure_record_for_func(
                "target",
                {
                    "source_a": {"other": "err"},
                    "source_b": {"target": "err"},
                },
            )
        )
        self.assertFalse(
            TranslationScheduler._has_failure_record_for_func(
                "missing",
                {"source_a": {"other": "err"}},
            )
        )

    def test_sort_ready_candidates_prioritizes_functions_with_more_callers(self):
        ordered = _scheduler()._sort_ready_candidates_root_first(
            test_source_name="test_src",
            ready=[("leaf_a", 1), ("root", 2), ("leaf_b", 1)],
            all_error_funcs_content={},
        )

        self.assertEqual([name for name, _ in ordered], ["leaf_a", "leaf_b", "root"])

    def test_function_translation_complete_rejects_unbalanced_snippet(self):
        scheduler = _scheduler()

        self.assertFalse(
            scheduler._is_function_translation_complete(
                func_name="root",
                owner_source="src",
                results={"src": {"root": "pub fn root() {"}},
                all_error_funcs_content={},
            )
        )

    def test_same_cycle_group_returns_true_for_group_members(self):
        scheduler = _scheduler()
        scheduler._cycle_group_members = {"test_src": {"a": {"a", "b"}}}

        self.assertTrue(scheduler._same_cycle_group("test_src", "a", "b"))
        self.assertFalse(scheduler._same_cycle_group("test_src", "a", "c"))

    def test_process_source_dynamically_adds_missing_scoped_dependency(self):
        scheduler = _base_process_scheduler()
        results = {}
        errors = {}

        scheduler.process_test_source(
            test_source_name="test_src",
            funcs_depth={"root": 0},
            results=results,
            all_error_funcs_content=errors,
            once_retry_count_dict={},
        )

        self.assertEqual(scheduler.processed, ["leaf", "root"])
        self.assertNotIn("root", errors.get("test_src", {}))
        self.assertTrue(
            any("[DYNAMIC-DEPS-ADD]" in message for message in scheduler.logger.messages),
            scheduler.logger.messages,
        )

    def test_process_source_dynamically_adds_dependency_from_heuristic_callee(self):
        scheduler = _base_process_scheduler()
        scheduler.funcs_childs = {"test_src": {"root": []}}
        scheduler.heuristic_test_dep_extraction = True
        scheduler._extract_direct_callees_from_c_body = lambda test_source_name, func_name: ["leaf"]
        results = {}
        errors = {}

        scheduler.process_test_source(
            test_source_name="test_src",
            funcs_depth={"root": 0},
            results=results,
            all_error_funcs_content=errors,
            once_retry_count_dict={},
        )

        self.assertEqual(scheduler.processed, ["leaf", "root"])
        self.assertIn("leaf", results.get("src", {}))
        self.assertNotIn("root", errors.get("test_src", {}))

    def test_process_source_does_not_add_out_of_scope_dependency(self):
        scheduler = _base_process_scheduler()
        scheduler.data_manager = _ScopedDataManager({"root": "test_src"})
        results = {}
        errors = {}

        scheduler.process_test_source(
            test_source_name="test_src",
            funcs_depth={"root": 0},
            results=results,
            all_error_funcs_content=errors,
            once_retry_count_dict={},
        )

        self.assertEqual(scheduler.processed, ["root"])
        self.assertEqual(errors, {})

    def test_stale_error_for_valid_result_does_not_block_dependency(self):
        scheduler = _base_process_scheduler()
        results = {"src": {"leaf": "pub fn leaf() {}\n"}}
        errors = {"src": {"leaf": "// stale failure"}}

        scheduler.process_test_source(
            test_source_name="test_src",
            funcs_depth={"root": 0},
            results=results,
            all_error_funcs_content=errors,
            once_retry_count_dict={},
        )

        self.assertEqual(scheduler.processed, ["root"])
        self.assertNotIn("src", errors)
        self.assertNotIn("root", errors.get("test_src", {}))

    def test_blocked_fast_fail_does_not_write_error_for_valid_existing_function(self):
        scheduler = _base_process_scheduler()
        scheduler.data_manager = _ScopedDataManager({"a": "src", "b": "src"})
        scheduler.funcs_childs = {"test_src": {"a": ["b"], "b": ["a"]}}
        scheduler.dependency_cycle_probe = True
        scheduler.max_cycle_probe_attempts_per_source = 1
        scheduler.processed = []
        scheduler.process_func = lambda **kwargs: scheduler.processed.append(kwargs["func_name"])
        results = {"src": {"a": "pub fn a() {}\n"}}
        errors = {"src": {"a": "// stale blocked failure"}}

        scheduler.process_test_source(
            test_source_name="test_src",
            funcs_depth={"a": 0, "b": 0},
            results=results,
            all_error_funcs_content=errors,
            once_retry_count_dict={},
        )

        self.assertNotIn("a", errors.get("src", {}))
        self.assertTrue(
            any("[BLOCKED-DEPS-SKIP-EXISTING] test_src:a" in message for message in scheduler.logger.messages),
            scheduler.logger.messages,
        )

    def test_unresolved_dependency_without_dynamic_owner_stays_blocked(self):
        scheduler = _base_process_scheduler()
        scheduler.data_manager = _SplitScopeDataManager(
            scoped_owners={"root": "test_src"},
            global_owners={"root": "test_src", "leaf": "src"},
            pointer_funcs={"leaf"},
        )
        scheduler.funcs_childs = {"test_src": {"root": ["leaf"]}}
        scheduler.processed = []
        results = {}
        errors = {}

        scheduler.process_test_source(
            test_source_name="test_src",
            funcs_depth={"root": 0},
            results=results,
            all_error_funcs_content=errors,
            once_retry_count_dict={},
        )

        self.assertEqual(scheduler.processed, [])
        self.assertIn("root", errors.get("test_src", {}))
        self.assertIn("leaf", errors["test_src"]["root"])

    def test_cycle_probe_budget_is_fixed_for_source(self):
        scheduler = _base_process_scheduler()
        scheduler.data_manager = _ScopedDataManager({"a": "src", "b": "src", "c": "src"})
        scheduler.funcs_childs = {"test_src": {"a": ["b"], "b": ["a"], "c": ["a"]}}
        scheduler.dependency_cycle_probe = True
        scheduler.max_cycle_probe_attempts_per_source = 1
        scheduler.processed = []

        def process_func(**kwargs):
            scheduler.processed.append(kwargs["func_name"])

        scheduler.process_func = process_func

        scheduler.process_test_source(
            test_source_name="test_src",
            funcs_depth={"a": 0, "b": 0, "c": 0},
            results={},
            all_error_funcs_content={},
            once_retry_count_dict={},
        )

        probe_messages = [
            message for message in scheduler.logger.messages
            if "[CYCLE-PROBE]" in message
        ]
        self.assertEqual(len(probe_messages), 3, probe_messages)

    def test_cycle_probe_skips_valid_existing_candidates(self):
        scheduler = _base_process_scheduler()
        scheduler.data_manager = _ScopedDataManager({"a": "src", "b": "src", "c": "src"})
        scheduler.funcs_childs = {"test_src": {"a": ["b"], "b": ["c"], "c": ["b"]}}
        scheduler.dependency_cycle_probe = True
        scheduler.max_cycle_probe_attempts_per_source = 2
        scheduler.processed = []

        def process_func(**kwargs):
            scheduler.processed.append(kwargs["func_name"])

        scheduler.process_func = process_func
        results = {"src": {"a": "pub fn a() {}"}}

        scheduler.process_test_source(
            test_source_name="test_src",
            funcs_depth={"a": 0, "b": 0, "c": 0},
            results=results,
            all_error_funcs_content={},
            once_retry_count_dict={},
        )

        self.assertTrue(
            any("[CYCLE-PROBE-SKIP-EXISTING] test_src:a" in message for message in scheduler.logger.messages),
            scheduler.logger.messages,
        )
        probe_messages = [
            message for message in scheduler.logger.messages
            if "[CYCLE-PROBE]" in message
        ]
        self.assertTrue(probe_messages, scheduler.logger.messages)
        self.assertIn("func=b", probe_messages[0])
        self.assertTrue(
            scheduler._is_function_translation_complete(
                func_name="root",
                owner_source="src",
                results={"src": {"root": "pub fn root() {}"}},
                all_error_funcs_content={},
            )
        )


if __name__ == "__main__":
    unittest.main()
