import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.prompt_builder import PromptBuilder, PromptContext
from pipeline.rust_archive import RustArchiveBuilder


class MinimalPromptDataManager:
    all_pointer_funcs = []
    include_dict = {}
    all_include_files = []

    def __init__(self):
        self.data = [{"extra": "typedef int Item;\nstruct ArrayList;"}]

    def get_direct_child_functions(self, _func_name, _funcs_child):
        return []

    def get_content(self, func_name, **_kwargs):
        return f"int {func_name}(void) {{ return 1; }}", "", 0

    def get_source_name_by_func_name(self, _func_name, **_kwargs):
        return "arraylist"


class PromptBuilderTest(unittest.TestCase):
    def test_render_prompt_code_block_skips_empty_content(self):
        self.assertEqual(PromptBuilder._render_prompt_code_block("rust", "  "), "")
        self.assertEqual(
            PromptBuilder._render_prompt_code_block("rust", "fn main() {}"),
            "```rust\nfn main() {}\n```",
        )

    def test_extract_error_codes_from_text_deduplicates_codes(self):
        codes = PromptBuilder._extract_error_codes_from_text("error E0425; then E0425 and E0308")

        self.assertEqual(codes, {"E0425", "E0308"})

    def test_prompt_context_defaults_optional_hints(self):
        ctx = PromptContext(
            prompt="p",
            source_name="s",
            child_context="c",
            names_list=[],
            before_details="",
            pointer_functions=[],
        )

        self.assertEqual(ctx.bootstrap_decls, "")
        self.assertEqual(ctx.dependency_rust_hints, "")

    def test_initial_prompt_no_context_golden(self):
        builder = PromptBuilder()
        builder.data_manager = MinimalPromptDataManager()
        builder.source_names = ["arraylist"]
        builder.ablation_no_context = True
        builder.ablation_no_constraints = True
        builder.params = {}
        builder.ownership_suggestions = {}
        builder._is_excluded_source_name = lambda _source_name: False
        expected = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "prompt_golden"
            / "initial_no_context_prompt.txt"
        ).read_text(encoding="utf-8")

        ctx = builder._build_initial_prompt_context(
            "arraylist_new",
            "arraylist",
            results={},
            funcs_child={},
        )

        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.prompt, expected)
        self.assertIn("typedef int Item;", ctx.bootstrap_decls)

    def test_extract_editable_function_directives_removes_control_comments(self):
        code, add_names, remove_names = PromptBuilder._extract_editable_function_directives(
            "\n".join(
                [
                    "// editable_functions_add: helper, helper, invalid-name",
                    "// editable_functions_remove: old_helper; another_old",
                    "pub fn target() {}",
                ]
            )
        )

        self.assertEqual(code, "pub fn target() {}\n")
        self.assertEqual(add_names, ["helper"])
        self.assertEqual(remove_names, ["old_helper", "another_old"])

    def test_extract_swe_handoff_directive_keeps_code_and_returns_reason(self):
        code, reason = PromptBuilder._extract_swe_handoff_directive(
            "// handoff_to_swe: needs coordinated signature change\npub fn target() {}\n"
        )

        self.assertEqual(code, "pub fn target() {}\n")
        self.assertEqual(reason, "needs coordinated signature change")

    def test_extract_function_signature_from_multiline_function(self):
        signature = PromptBuilder._extract_function_signature(
            "pub fn add(a: i32, b: i32) -> i32 {\n    a + b\n}\n"
        )

        self.assertEqual(signature, "pub fn add(a: i32, b: i32) -> i32;")

    def test_build_prompt_non_function_snippet_deduplicates_imports(self):
        builder = PromptBuilder()
        builder._split_extra_blocks = RustArchiveBuilder._split_extra_blocks
        builder._extract_decl_symbol_from_block = RustArchiveBuilder._extract_decl_symbol_from_block

        snippet = builder._build_prompt_non_function_snippet(
            "use crate::arraylist::ArrayList;\nuse crate::arraylist::ArrayList;\npub const LIMIT: usize = 2;"
        )

        self.assertEqual(snippet.count("ArrayList"), 1)
        self.assertIn("pub const LIMIT", snippet)

    def test_diagnostics_require_type_bodies_for_field_and_borrow_errors(self):
        self.assertTrue(PromptBuilder._diagnostics_require_type_bodies({"E0560"}))
        self.assertTrue(PromptBuilder._diagnostics_require_type_bodies({"E0507"}))
        self.assertFalse(PromptBuilder._diagnostics_require_type_bodies({"E0425"}))

    def test_normalize_feedback_signature_removes_source_locations(self):
        sig = PromptBuilder._normalize_feedback_signature(
            "foo:12:3 error[E0425] bar:7 cannot find value"
        )

        self.assertEqual(sig, "<loc> error[E0425] <loc> cannot find value")

    def test_extract_missing_named_entities_deduplicates_valid_identifiers(self):
        names = PromptBuilder._extract_missing_named_entities(
            "cannot find value `limit` in this scope; cannot find value `bad-name`; cannot find value `limit`",
            "value",
        )

        self.assertEqual(names, ["limit"])

    def test_extract_hint_lines_for_symbols_groups_by_source_and_case_variants(self):
        hints = "\n".join(
            [
                "[C 声明 file=a.c source=a]",
                "int LIMIT_VALUE;",
                "int unrelated;",
                "[C 声明 file=b.c source=b]",
                "struct Node;",
            ]
        )

        selected = PromptBuilder._extract_hint_lines_for_symbols(
            hints,
            ["limit-value", "Node"],
        )

        self.assertIn("[C 声明 file=a.c source=a]\n- int LIMIT_VALUE;", selected)
        self.assertIn("[C 声明 file=b.c source=b]\n- struct Node;", selected)
        self.assertNotIn("unrelated", selected)

    def test_build_module_function_spans_and_find_function_for_line(self):
        spans = PromptBuilder._build_module_function_spans(
            "\n".join(
                [
                    "pub fn first() {",
                    "    let x = 1;",
                    "}",
                    "",
                    "fn second() {",
                    "}",
                ]
            )
        )

        self.assertEqual([name for name, _, _ in spans], ["first", "second"])
        self.assertEqual(PromptBuilder._find_function_for_line(spans, 2), "first")
        self.assertEqual(PromptBuilder._find_function_for_line(spans, 5), "second")
        self.assertEqual(PromptBuilder._find_function_for_line(spans, 99), "")


if __name__ == "__main__":
    unittest.main()
