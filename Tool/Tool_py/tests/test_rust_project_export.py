import sys
import tempfile
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.rust_archive import RustArchiveBuilder
from pipeline.rust_project_export import RustProjectExporter


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
    builder.verifier = object()
    builder.enable_dependency_import_guessing = False
    builder._collect_source_dependency_sources = lambda source_name, include_file_set: []
    return builder


def _project_exporter():
    builder = _archive_builder()
    exporter = RustProjectExporter()
    exporter._build_module_sources = builder._build_module_sources
    exporter._is_test_source = RustArchiveBuilder._is_test_source
    exporter.verifier = object()
    return exporter


class RustProjectExporterTest(unittest.TestCase):
    def test_export_archive_to_project_uses_injected_renderer_and_writer(self):
        class Renderer:
            def __init__(self):
                self.calls = []

            def build_module_sources(self, archive, include_files):
                self.calls.append((archive, list(include_files)))
                return {"src_foo": "pub fn foo() -> i32 { 1 }"}, []

        class Writer:
            def __init__(self):
                self.calls = []

            def write_library_project(self, crate_name, output_project_path, module_sources):
                self.calls.append((crate_name, output_project_path, dict(module_sources)))
                return True, "writer exported"

        renderer = Renderer()
        writer = Writer()
        exporter = RustProjectExporter(module_source_renderer=renderer, cargo_project_writer=writer)

        with tempfile.TemporaryDirectory() as tmp:
            ok, msg = exporter.export_archive_to_project(
                archive={"src/foo": {"foo": "ignored by fake renderer"}},
                include_files=["src/foo"],
                output_project_path=tmp,
                crate_name="verify_project",
            )

        self.assertTrue(ok, msg)
        self.assertEqual(msg, "writer exported")
        self.assertEqual(renderer.calls, [({"src/foo": {"foo": "ignored by fake renderer"}}, ["src/foo"])])
        self.assertEqual(writer.calls, [("verify_project", tmp, {"src_foo": "pub fn foo() -> i32 { 1 }"})])

    def test_export_archive_tests_to_project_uses_injected_renderer(self):
        class Renderer:
            def build_module_sources(self, archive, include_files):
                return {"tests_foo_test": "fn test_case() { crate::foo::helper(); }"}, []

        exporter = RustProjectExporter(
            module_source_renderer=Renderer(),
            test_source_classifier=lambda source_name: source_name.startswith("tests/"),
        )

        with tempfile.TemporaryDirectory() as tmp:
            ok, msg = exporter.export_archive_tests_to_project(
                archive={"tests/foo_test": {"test_case": "ignored by fake renderer"}},
                include_test_files=["tests/foo_test"],
                output_project_path=tmp,
                crate_name="verify_project",
            )

            self.assertTrue(ok, msg)
            test_text = (Path(tmp) / "tests" / "tests_foo_test.rs").read_text()

        self.assertIn("#[test]\nfn test_case()", test_text)
        self.assertIn("verify_project::foo::helper()", test_text)

    def test_export_archive_to_project_writes_cargo_library(self):
        archive = {
            "src/foo": {
                "extra": "pub struct Item { pub value: i32 }",
                "helper": "fn helper() -> i32 { 1 }",
            }
        }

        with tempfile.TemporaryDirectory() as tmp:
            ok, msg = _project_exporter().export_archive_to_project(
                archive=archive,
                include_files=["src/foo"],
                output_project_path=tmp,
                crate_name="verify_project",
            )

            self.assertTrue(ok, msg)
            self.assertIn("via fallback writer", msg)
            self.assertTrue((Path(tmp) / "Cargo.toml").is_file())
            self.assertIn("pub mod src_foo;", (Path(tmp) / "src" / "lib.rs").read_text())
            module_text = (Path(tmp) / "src" / "src_foo.rs").read_text()
            self.assertIn("pub struct Item", module_text)
            self.assertIn("pub fn helper() -> i32", module_text)

    def test_export_archive_tests_to_project_rewrites_crate_paths_and_adds_test_attr(self):
        archive = {
            "tests/foo_test": {
                "extra": "use crate::foo::helper;",
                "test_case": "fn test_case() { helper(); }",
            }
        }

        with tempfile.TemporaryDirectory() as tmp:
            ok, msg = _project_exporter().export_archive_tests_to_project(
                archive=archive,
                include_test_files=["tests/foo_test"],
                output_project_path=tmp,
                crate_name="verify_project",
            )

            self.assertTrue(ok, msg)
            test_text = (Path(tmp) / "tests" / "tests_foo_test.rs").read_text()
            self.assertIn("use verify_project::foo::helper;", test_text)
            self.assertIn("#[test]\npub fn test_case()", test_text)


if __name__ == "__main__":
    unittest.main()
