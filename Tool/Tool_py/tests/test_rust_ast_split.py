import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from utils import split_rust_code_structural


class RustAstSplitTest(unittest.TestCase):
    def test_ast_split_handles_common_top_level_rust_items(self):
        code = "\n".join(
            [
                "extern crate libc;",
                "use crate::foo::{",
                "    bar,",
                "    baz,",
                "};",
                "pub const LIMIT: usize = 8;",
                "pub static mut COUNT: i32 = 0;",
                "pub type Size = usize;",
                "#[derive(Clone)]",
                "pub struct Node { pub value: i32 }",
                "pub enum Kind { A, B }",
                "pub union Bits { pub i: i32, pub u: u32 }",
                "pub trait Named { fn name(&self) -> &'static str; }",
                "impl Node { pub fn new(value: i32) -> Self { Self { value } } }",
                "macro_rules! make_zero { () => { 0 }; }",
                "pub fn run() -> i32 {",
                "    unsafe { COUNT += 1; }",
                "    LIMIT as i32",
                "}",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertFalse(split.fallback_used)
        self.assertEqual(set(split.function_content_dict), {"run"})
        self.assertIn("use crate::foo::{", split.non_function_content)
        self.assertIn("bar", split.non_function_content)
        self.assertIn("pub struct Node", split.non_function_content)
        self.assertIn("pub union Bits", split.non_function_content)
        self.assertIn("impl Node", split.non_function_content)
        self.assertIn("macro_rules! make_zero", split.non_function_content)

    def test_ast_split_handles_import_and_function_matrix(self):
        code = "\n".join(
            [
                "#![allow(dead_code)]",
                "pub use crate::prelude::*;",
                "use crate::foo::Bar as RenamedBar;",
                "use crate::glob::*;",
                "#[cfg(feature = \"std\")]",
                "use crate::std_impl::{",
                "    Alpha,",
                "    Beta as RenamedBeta,",
                "};",
                "pub fn plain() {}",
                "#[test]",
                "#[should_panic]",
                "pub fn test_case() { panic!(\"expected\") }",
                "#[allow(clippy::needless_return)]",
                "pub async fn async_fn() -> i32 { 1 }",
                "pub unsafe fn unsafe_fn(ptr: *const i32) -> i32 { unsafe { *ptr } }",
                "pub const fn const_fn(value: usize) -> usize { value + 1 }",
                "#[no_mangle]",
                "pub extern \"C\" fn extern_fn(value: i32) -> i32 { value }",
                "pub fn generic_where<T, E>(value: T) -> Result<T, E>",
                "where",
                "    T: Clone,",
                "    E: Default,",
                "{",
                "    Ok(value.clone())",
                "}",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertFalse(split.fallback_used)
        self.assertEqual(
            set(split.function_content_dict),
            {
                "plain",
                "test_case",
                "async_fn",
                "unsafe_fn",
                "const_fn",
                "extern_fn",
                "generic_where",
            },
        )
        self.assertIn("#![allow(dead_code)]", split.non_function_content)
        self.assertIn("pub use crate::prelude::*;", split.non_function_content)
        self.assertIn("Bar as RenamedBar", split.non_function_content)
        self.assertIn("use crate::glob::*;", split.non_function_content)
        self.assertIn("#[cfg(feature = \"std\")]", split.non_function_content)
        self.assertIn("Beta as RenamedBeta", split.non_function_content)
        self.assertIn("#[test]", split.function_content_dict["test_case"])
        self.assertIn("#[should_panic]", split.function_content_dict["test_case"])
        self.assertIn("#[allow(clippy::needless_return)]", split.function_content_dict["async_fn"])
        self.assertIn("where", split.function_content_dict["generic_where"])

    def test_ast_split_preserves_cfg_duplicate_function_variants(self):
        code = "\n".join(
            [
                "#[cfg(unix)]",
                "pub fn platform_value() -> i32 { 1 }",
                "#[cfg(windows)]",
                "pub fn platform_value() -> i32 { 2 }",
                "pub fn caller() -> i32 { platform_value() }",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"platform_value", "caller"})
        self.assertEqual(split.output_content.count("pub fn platform_value"), 2)
        self.assertIn("#[cfg(unix)]", split.output_content)
        self.assertIn("#[cfg(windows)]", split.output_content)

    def test_ast_split_preserves_multiple_impl_blocks_for_same_type(self):
        code = "\n".join(
            [
                "pub struct Node { value: i32 }",
                "impl Node {",
                "    pub fn new(value: i32) -> Self { Self { value } }",
                "}",
                "impl Node {",
                "    pub fn value(&self) -> i32 { self.value }",
                "}",
                "pub struct Wrapper<T> { value: T }",
                "impl<T> Wrapper<T> {",
                "    pub fn new(value: T) -> Self { Self { value } }",
                "}",
                "impl<T> Wrapper<T>",
                "where",
                "    T: Clone,",
                "{",
                "    pub fn cloned(&self) -> T { self.value.clone() }",
                "}",
                "pub fn use_node(node: &Node) -> i32 { node.value() }",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"use_node"})
        self.assertEqual(split.output_content.count("impl Node"), 2)
        self.assertIn("pub fn new(value: i32)", split.output_content)
        self.assertIn("pub fn value(&self)", split.output_content)
        self.assertEqual(split.output_content.count("impl<T> Wrapper<T>"), 2)
        self.assertIn("pub fn cloned(&self)", split.output_content)

    def test_ast_split_preserves_cfg_duplicate_non_function_items(self):
        code = "\n".join(
            [
                "#[cfg(unix)]",
                "pub struct Platform { unix: bool }",
                "#[cfg(windows)]",
                "pub struct Platform { windows: bool }",
                "#[cfg(feature = \"a\")]",
                "macro_rules! platform_macro { () => { 1 }; }",
                "#[cfg(feature = \"b\")]",
                "macro_rules! platform_macro { () => { 2 }; }",
                "pub fn use_platform() {}",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"use_platform"})
        self.assertEqual(split.output_content.count("pub struct Platform"), 2)
        self.assertEqual(split.output_content.count("macro_rules! platform_macro"), 2)
        self.assertIn("#[cfg(unix)]", split.output_content)
        self.assertIn("#[cfg(windows)]", split.output_content)

    def test_ast_split_keeps_nested_module_as_extra(self):
        code = "\n".join(
            [
                "pub mod nested {",
                "    pub fn hidden() -> i32 { 1 }",
                "}",
                "pub fn visible() -> i32 { nested::hidden() }",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"visible"})
        self.assertIn("pub mod nested", split.non_function_content)
        self.assertIn("pub fn hidden()", split.non_function_content)

    def test_ast_split_preserves_doc_comments_and_cfg_attr(self):
        code = "\n".join(
            [
                "//! module level docs",
                "#![cfg_attr(test, allow(unused_imports))]",
                "/// struct docs",
                "#[cfg_attr(feature = \"debug\", derive(Debug))]",
                "pub struct Documented {",
                "    pub value: i32,",
                "}",
                "/// function docs",
                "#[cfg_attr(feature = \"inline\", inline)]",
                "pub fn documented_fn() -> i32 {",
                "    1",
                "}",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"documented_fn"})
        self.assertIn("//! module level docs", split.output_content)
        self.assertIn("#![cfg_attr(test, allow(unused_imports))]", split.output_content)
        self.assertIn("/// struct docs", split.non_function_content)
        self.assertIn("#[cfg_attr(feature = \"debug\", derive(Debug))]", split.non_function_content)
        self.assertIn("/// function docs", split.function_content_dict["documented_fn"])
        self.assertIn("#[cfg_attr(feature = \"inline\", inline)]", split.function_content_dict["documented_fn"])

    def test_ast_split_preserves_extern_block_as_extra(self):
        code = "\n".join(
            [
                "extern \"C\" {",
                "    pub fn malloc(size: usize) -> *mut u8;",
                "    pub static errno: i32;",
                "}",
                "pub fn wrapper() -> i32 { 0 }",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"wrapper"})
        self.assertIn("extern \"C\"", split.output_content)
        self.assertIn("pub fn malloc", split.output_content)
        self.assertIn("pub static errno", split.output_content)

    def test_ast_split_preserves_macro_invocation_items(self):
        code = "\n".join(
            [
                "thread_local! {",
                "    pub static LOCAL_COUNT: std::cell::Cell<u32> = std::cell::Cell::new(0);",
                "}",
                "bitflags! {",
                "    pub struct Flags: u32 {",
                "        const A = 0b0001;",
                "    }",
                "}",
                "pub fn read_flags() -> u32 { 1 }",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"read_flags"})
        self.assertIn("thread_local!", split.output_content)
        self.assertIn("LOCAL_COUNT", split.output_content)
        self.assertIn("bitflags!", split.output_content)
        self.assertIn("pub struct Flags", split.output_content)

    def test_ast_split_preserves_cfg_duplicate_const_static_type_and_macro_items(self):
        code = "\n".join(
            [
                "#[cfg(unix)]",
                "pub const BUFFER_SIZE: usize = 4096;",
                "#[cfg(windows)]",
                "pub const BUFFER_SIZE: usize = 8192;",
                "#[cfg(unix)]",
                "pub static PLATFORM_NAME: &str = \"unix\";",
                "#[cfg(windows)]",
                "pub static PLATFORM_NAME: &str = \"windows\";",
                "#[cfg(feature = \"a\")]",
                "pub type PlatformWord = u32;",
                "#[cfg(feature = \"b\")]",
                "pub type PlatformWord = u64;",
                "#[cfg(feature = \"a\")]",
                "macro_rules! choose_platform { () => { 1 }; }",
                "#[cfg(feature = \"b\")]",
                "macro_rules! choose_platform { () => { 2 }; }",
                "pub fn platform_word() -> usize { BUFFER_SIZE }",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"platform_word"})
        self.assertEqual(split.output_content.count("pub const BUFFER_SIZE"), 2)
        self.assertEqual(split.output_content.count("pub static PLATFORM_NAME"), 2)
        self.assertEqual(split.output_content.count("pub type PlatformWord"), 2)
        self.assertEqual(split.output_content.count("macro_rules! choose_platform"), 2)

    def test_ast_split_preserves_trait_impl_variants_and_impl_associated_items(self):
        code = "\n".join(
            [
                "pub trait Convert<T> {",
                "    type Error;",
                "    const NAME: &'static str;",
                "    fn convert(value: T) -> Result<Self, Self::Error>",
                "    where",
                "        Self: Sized;",
                "}",
                "pub struct Holder<T> { value: T }",
                "impl<T> Holder<T> {",
                "    pub const KIND: &'static str = \"holder\";",
                "    pub fn new(value: T) -> Self { Self { value } }",
                "}",
                "impl<T> Convert<T> for Holder<T>",
                "where",
                "    T: Clone,",
                "{",
                "    type Error = ();",
                "    const NAME: &'static str = \"holder\";",
                "    fn convert(value: T) -> Result<Self, Self::Error> { Ok(Self { value }) }",
                "}",
                "pub fn free_fn() {}",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"free_fn"})
        self.assertIn("pub trait Convert", split.non_function_content)
        self.assertIn("pub const KIND", split.non_function_content)
        self.assertIn("impl<T> Convert<T> for Holder<T>", split.non_function_content)
        self.assertIn("fn convert(value: T)", split.non_function_content)

    def test_ast_split_keeps_cfg_test_module_functions_nested(self):
        code = "\n".join(
            [
                "pub fn exported() -> i32 { 1 }",
                "#[cfg(test)]",
                "mod tests {",
                "    #[test]",
                "    fn inner_test() {",
                "        assert_eq!(super::exported(), 1);",
                "    }",
                "}",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"exported"})
        self.assertNotIn("inner_test", split.function_content_dict)
        self.assertIn("mod tests", split.non_function_content)
        self.assertIn("fn inner_test()", split.non_function_content)

    def test_ast_split_handles_raw_identifiers(self):
        code = "\n".join(
            [
                "pub struct r#match { pub r#type: i32 }",
                "pub fn r#type(value: r#match) -> i32 {",
                "    value.r#type",
                "}",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"r#type"})
        self.assertIn("pub struct r#match", split.non_function_content)
        self.assertIn("value.r#type", split.function_content_dict["r#type"])

    def test_ast_split_handles_multiline_signature_const_generics_and_unsafe_extern(self):
        code = "\n".join(
            [
                "#[inline]",
                "pub fn borrow_array<'a, T, const N: usize>(",
                "    value: &'a [T; N],",
                ") -> &'a [T; N]",
                "where",
                "    T: Clone,",
                "{",
                "    value",
                "}",
                "#[no_mangle]",
                "pub unsafe extern \"C\" fn ffi_value(",
                "    value: i32,",
                ") -> i32 {",
                "    value",
                "}",
            ]
        )

        split = split_rust_code_structural(code)

        self.assertTrue(split.ast_ok, split.diagnostic)
        self.assertEqual(set(split.function_content_dict), {"borrow_array", "ffi_value"})
        self.assertIn("const N: usize", split.function_content_dict["borrow_array"])
        self.assertIn("where", split.function_content_dict["borrow_array"])
        self.assertIn("pub unsafe extern \"C\" fn ffi_value", split.function_content_dict["ffi_value"])


if __name__ == "__main__":
    unittest.main()
