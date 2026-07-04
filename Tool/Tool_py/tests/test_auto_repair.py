import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.auto_repair import AutoRepairActions
from pipeline.prompt_builder import PromptBuilder
from pipeline.rust_archive import RustArchiveBuilder


class _Logger:
    def info(self, *args, **kwargs):
        return None


class _DataManager:
    include_dict = {}

    def get_decl_owner(self, symbol):
        return ""

    def get_source_name_by_func_name(self, name, respect_scope=False):
        return ""


def _archive_builder():
    builder = RustArchiveBuilder()
    builder.source_names = []
    builder.funcs_childs = {}
    builder.data_manager = _DataManager()
    builder.logger = _Logger()
    builder.enable_dependency_import_guessing = False
    builder._collect_source_dependency_sources = lambda source_name, include_file_set: []
    return builder


def _auto_repair_actions():
    builder = _archive_builder()
    actions = AutoRepairActions()
    actions.source_names = []
    actions.funcs_childs = {}
    actions.data_manager = _DataManager()
    actions.logger = _Logger()
    actions.enable_dependency_import_guessing = False
    actions._build_module_sources = builder._build_module_sources
    actions._extract_missing_named_entities = PromptBuilder._extract_missing_named_entities
    actions._merge_extra = RustArchiveBuilder._merge_extra
    return actions


class AutoRepairActionsTest(unittest.TestCase):
    def test_collect_declared_identifiers_only_top_level_values(self):
        declared = AutoRepairActions._collect_declared_identifiers(
            {
                "extra": "\n".join(
                    [
                        "pub const LIMIT: usize = 4;",
                        "fn helper() {",
                        "    const INNER: usize = 1;",
                        "}",
                        "static mut GLOBAL_COUNT: i32 = 0;",
                    ]
                )
            }
        )

        self.assertEqual(declared, {"LIMIT", "GLOBAL_COUNT"})

    def test_extract_missing_new_structs_normalizes_paths(self):
        structs = AutoRepairActions._extract_missing_new_structs(
            "no function or associated item named `new` found for struct `crate::node::Node`"
        )

        self.assertEqual(structs, ["Node"])

    def test_auto_alias_missing_test_values_adds_case_alias(self):
        archive = {
            "tests/foo_test": {
                "extra": "pub const LIMIT: usize = 3;",
                "test_case": "fn test_case() { assert_eq!(limit, LIMIT); }",
            }
        }

        updated, message = _auto_repair_actions()._auto_alias_missing_test_values(
            archive=archive,
            source_name="tests/foo_test",
            include_files=["tests/foo_test"],
            feedback="error[E0425]: cannot find value `limit` in this scope",
        )

        self.assertIsNotNone(updated)
        self.assertIn("use self::LIMIT as limit;", updated["tests/foo_test"]["extra"])
        self.assertEqual(message, "use self::LIMIT as limit;")

    def test_impl_contains_method_detects_method_inside_matching_impl_block(self):
        text = "\n".join(
            [
                "impl Node {",
                "    pub fn new() -> Self { Node {} }",
                "}",
                "impl Other { pub fn new() -> Self { Other {} } }",
            ]
        )

        self.assertTrue(AutoRepairActions._impl_contains_method(text, "Node", "new"))
        self.assertFalse(AutoRepairActions._impl_contains_method(text, "Node", "missing"))


if __name__ == "__main__":
    unittest.main()
