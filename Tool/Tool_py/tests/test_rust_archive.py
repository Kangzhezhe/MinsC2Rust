import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.rust_archive import RustArchiveBuilder
from pipeline.stats import PipelineStats, apply_pipeline_stats


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
    builder.params = {}
    builder.enable_dependency_import_guessing = False
    builder._collect_source_dependency_sources = lambda source_name, include_file_set: []
    builder._extract_editable_function_directives = lambda response: (response, None, None)
    builder._find_forbidden_c_pointer_tokens = lambda response: []
    builder._is_cycle_placeholder_function = lambda code: False
    return builder


class RustArchiveBuilderTest(unittest.TestCase):
    def setUp(self):
        apply_pipeline_stats(PipelineStats())

    def tearDown(self):
        apply_pipeline_stats(PipelineStats())

    def test_build_module_sources_uses_injected_renderer_seam(self):
        class Renderer:
            def build_module_sources(self, archive, include_files):
                return {"custom": "pub fn rendered() {}\n"}, {"custom": include_files[0]}

        builder = RustArchiveBuilder(module_source_renderer=Renderer())

        module_sources, module_to_source = builder._build_module_sources(
            {"src/foo": {"helper": "fn helper() {}"}},
            ["src/foo"],
        )

        self.assertEqual(module_sources, {"custom": "pub fn rendered() {}\n"})
        self.assertEqual(module_to_source, {"custom": "src/foo"})

    def test_merge_extra_replaces_same_symbol_declaration(self):
        existing = "pub type Item = i32;\n\npub struct Node { pub value: i32 }\n"
        incoming = "pub type Item = usize;\n"

        merged = RustArchiveBuilder._merge_extra(existing, incoming)

        self.assertIn("pub type Item = usize;", merged)
        self.assertNotIn("pub type Item = i32;", merged)
        self.assertIn("pub struct Node", merged)

    def test_dedupe_use_statements_groups_imports(self):
        source = "\n".join(
            [
                "use crate::arraylist::ArrayList;",
                "use crate::arraylist::arraylist_new;",
                "use crate::arraylist::{ArrayList};",
                "pub fn test_case() {}",
            ]
        )

        deduped = RustArchiveBuilder._dedupe_use_statements(source)

        self.assertEqual(deduped.count("use crate::arraylist::"), 1)
        self.assertIn("ArrayList", deduped)
        self.assertIn("arraylist_new", deduped)
        self.assertIn("pub fn test_case() {}", deduped)

    def test_dedupe_use_statements_merges_multiline_grouped_imports(self):
        source = "\n".join(
            [
                "use crate::alloc_testing::{",
                "    alloc_test_free,",
                "    alloc_test_malloc,",
                "};",
                "use crate::alloc_testing::{alloc_test_calloc, alloc_test_free};",
                "use crate::alloc_testing::alloc_test_set_limit;",
                "pub fn test_case() {}",
            ]
        )

        deduped = RustArchiveBuilder._dedupe_use_statements(source)

        self.assertEqual(deduped.count("use crate::alloc_testing::"), 1)
        self.assertEqual(deduped.count("alloc_test_free"), 1)
        self.assertIn("alloc_test_calloc", deduped)
        self.assertIn("alloc_test_malloc", deduped)
        self.assertIn("alloc_test_set_limit", deduped)

    def test_merge_extra_dedupes_multiline_grouped_imports(self):
        existing = "\n".join(
            [
                "use crate::alloc_testing::{",
                "    alloc_test_free,",
                "    alloc_test_malloc,",
                "};",
            ]
        )
        incoming = "use crate::alloc_testing::{alloc_test_calloc, alloc_test_free};\n"

        merged = RustArchiveBuilder._merge_extra(existing, incoming)

        self.assertEqual(merged.count("use crate::alloc_testing::"), 1)
        self.assertEqual(merged.count("alloc_test_free"), 1)
        self.assertIn("alloc_test_calloc", merged)
        self.assertIn("alloc_test_malloc", merged)

    def test_sanitize_non_function_content_preserves_multiline_grouped_use(self):
        source = "\n".join(
            [
                "use crate::alloc_testing::{",
                "    alloc_test_free,",
                "    alloc_test_malloc,",
                "};",
            ]
        )

        sanitized = RustArchiveBuilder._sanitize_non_function_content(source)

        self.assertIn("alloc_test_free", sanitized)
        self.assertIn("alloc_test_malloc", sanitized)
        self.assertNotEqual(sanitized, "use crate::alloc_testing::{\n};")

    def test_ensure_public_function_promotes_plain_function(self):
        promoted = RustArchiveBuilder._ensure_public_function("fn helper() {}\n")

        self.assertEqual(promoted, "pub fn helper() {}\n")

    def test_collect_response_local_helpers_follows_identifier_references(self):
        helpers = RustArchiveBuilder._collect_response_local_helpers(
            "root",
            {
                "root": "pub fn root() { child(); }",
                "child": "pub fn child() { leaf(); }",
                "leaf": "pub fn leaf() {}",
                "unused": "pub fn unused() {}",
            },
        )

        self.assertEqual(helpers, {"child", "leaf"})

    def test_apply_response_to_archive_accepts_balanced_target_function(self):
        result, error = _archive_builder()._apply_response_to_archive(
            response_code="pub fn foo() -> i32 { 1 }",
            func_name="foo",
            source_name="src/foo",
            include_files=["src/foo"],
            base_archive={},
        )

        self.assertEqual(error, "")
        self.assertIn("foo", result["src/foo"])
        self.assertIn("pub fn foo() -> i32", result["src/foo"]["foo"])

    def test_apply_response_to_archive_preserves_multiline_test_import_extra(self):
        response = "\n".join(
            [
                "use crate::alloc_testing::{",
                "    alloc_test_calloc,",
                "    alloc_test_free,",
                "    alloc_test_malloc,",
                "};",
                "",
                "pub fn test_malloc_free() {",
                "    let block = alloc_test_malloc(8).unwrap();",
                "    alloc_test_free(block);",
                "}",
            ]
        )

        result, error = _archive_builder()._apply_response_to_archive(
            response_code=response,
            func_name="test_malloc_free",
            source_name="test-alloc-testing",
            include_files=["alloc-testing", "test-alloc-testing"],
            base_archive={},
        )

        self.assertEqual(error, "")
        self.assertIn("alloc_test_malloc", result["test-alloc-testing"]["extra"])
        self.assertIn("alloc_test_free", result["test-alloc-testing"]["extra"])
        self.assertNotIn("use crate::alloc_testing::{\n};", result["test-alloc-testing"]["extra"])

    def test_build_module_sources_promotes_functions_and_maps_module_names(self):
        archive = {
            "src/foo-bar": {
                "extra": "pub struct Item { pub value: i32 }",
                "helper": "fn helper() -> i32 { 1 }",
            }
        }

        module_sources, module_to_source = _archive_builder()._build_module_sources(
            archive,
            ["src/foo-bar"],
        )

        self.assertEqual(module_to_source, {"src_foo_bar": "src/foo-bar"})
        self.assertIn("pub struct Item", module_sources["src_foo_bar"])
        self.assertIn("pub fn helper() -> i32", module_sources["src_foo_bar"])

    def test_build_module_sources_cleans_test_modules(self):
        archive = {
            "tests/foo_test": {
                "extra": "\n".join(
                    [
                        "use crate::foo::helper;",
                        "random prose that should not become Rust",
                        "pub const LIMIT: usize = 3;",
                    ]
                ),
                "test_case": "fn test_case() { assert_eq!(LIMIT, 3); }",
                "helper": "fn helper() {}",
            }
        }

        module_sources, _ = _archive_builder()._build_module_sources(
            archive,
            ["tests/foo_test"],
        )
        rendered = module_sources["tests_foo_test"]

        self.assertIn("pub const LIMIT", rendered)
        self.assertIn("pub fn test_case()", rendered)
        self.assertNotIn("random prose", rendered)
        self.assertIn("fn helper()", rendered)
        self.assertNotIn("pub fn helper()", rendered)

    def test_prune_shadowed_extra_removes_declarations_owned_by_dependency(self):
        extra = "\n".join(
            [
                "use crate::dep::{Node, Size};",
                "#[derive(Clone)]",
                "pub struct Node { pub value: i32 }",
                "pub type Size = usize;",
                "pub const LOCAL: usize = 1;",
            ]
        )

        cleaned, removed = RustArchiveBuilder._prune_shadowed_extra(
            extra,
            {"dep": {"Node", "Size"}},
        )

        self.assertEqual(removed, ["Node", "Size"])
        self.assertIn("use crate::dep::{Node, Size};", cleaned)
        self.assertIn("pub const LOCAL", cleaned)
        self.assertNotIn("pub struct Node", cleaned)
        self.assertNotIn("pub type Size", cleaned)
        self.assertNotIn("#[derive(Clone)]", cleaned)

    def test_drop_self_module_use_imports_only_removes_current_module_imports(self):
        module_text = "\n".join(
            [
                "use crate::src_foo::helper;",
                "use crate::other::value;",
                "pub fn target() {}",
            ]
        )

        cleaned = RustArchiveBuilder._drop_self_module_use_imports(module_text, "src_foo")

        self.assertNotIn("use crate::src_foo::helper;", cleaned)
        self.assertIn("use crate::other::value;", cleaned)
        self.assertIn("pub fn target() {}", cleaned)

    def test_collect_response_local_helpers_for_multiple_roots(self):
        helpers = RustArchiveBuilder._collect_response_local_helpers_for_roots(
            ["root_a", "root_b"],
            {
                "root_a": "pub fn root_a() { shared(); only_a(); }",
                "root_b": "pub fn root_b() { shared(); }",
                "shared": "pub fn shared() {}",
                "only_a": "pub fn only_a() {}",
                "unused": "pub fn unused() {}",
            },
        )

        self.assertEqual(helpers, {"shared", "only_a"})


if __name__ == "__main__":
    unittest.main()
