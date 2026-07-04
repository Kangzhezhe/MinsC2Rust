"""Cargo project export helpers for translated Rust archives.

The translation pipeline verifies snippets frequently, but CC-MINI fallback and
runtime test checks need a real Cargo project layout. This module owns that
materialization step and keeps it separate from the scheduling/LLM loop.
"""

import os
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from utils import normalize_rust_module_name


class CargoProjectWriter:
    """Write a Rust library archive into a Cargo project directory."""

    def __init__(self, verifier: Any = None):
        self.verifier = verifier

    def write_library_project(
        self,
        *,
        crate_name: str,
        output_project_path: str,
        module_sources: Dict[str, str],
    ) -> Tuple[bool, str]:
        src_dir = os.path.join(output_project_path, "src")
        os.makedirs(src_dir, exist_ok=True)

        # CargoVerifier knows how to include project-level dependency overrides.
        # Use it when available, otherwise fall back to a self-contained crate.
        if hasattr(self.verifier, "_write_cargo_project"):
            self.verifier._write_cargo_project(
                crate_name=crate_name,
                src_dir=src_dir,
                module_sources=module_sources,
            )
            return True, f"exported {len(module_sources)} modules via verifier"

        cargo_toml = os.path.join(output_project_path, "Cargo.toml")
        with open(cargo_toml, "w", encoding="utf-8") as f:
            f.write(
                "[package]\n"
                f"name = \"{crate_name}\"\n"
                "version = \"0.1.0\"\n"
                "edition = \"2021\"\n\n"
                "[lib]\n"
                "path = \"src/lib.rs\"\n\n"
                "[dependencies]\n"
                "libc = \"0.2\"\n"
            )

        lib_lines = ["#![allow(warnings)]"]
        for module_name in sorted(module_sources.keys()):
            lib_lines.append(f"pub mod {module_name};")
            module_path = os.path.join(src_dir, f"{module_name}.rs")
            with open(module_path, "w", encoding="utf-8") as mf:
                mf.write((module_sources[module_name] or "") + "\n")

        with open(os.path.join(src_dir, "lib.rs"), "w", encoding="utf-8") as f:
            f.write("\n".join(lib_lines) + "\n")

        return True, f"exported {len(module_sources)} modules via fallback writer"


class RustProjectExporter:
    """Export archive buckets into temporary Cargo projects."""

    def __init__(
        self,
        *,
        module_source_renderer: Any = None,
        cargo_project_writer: Any = None,
        test_source_classifier: Optional[Callable[[str], bool]] = None,
        verifier: Any = None,
    ):
        self._module_source_renderer = module_source_renderer
        self._cargo_project_writer = cargo_project_writer
        self._test_source_classifier = test_source_classifier
        self.verifier = verifier

    def export_archive_to_project(
        self,
        archive: Dict[str, Dict[str, str]],
        include_files: List[str],
        output_project_path: str,
        crate_name: str = "translation_export",
    ) -> Tuple[bool, str]:
        """Write selected non-test archive modules as a Cargo library project."""
        if not isinstance(archive, dict):
            return False, "archive is not a dict"

        export_sources = [name for name in include_files if name in archive]
        if not export_sources:
            return False, "no exportable source found"

        module_sources, _ = self._render_module_sources(archive, export_sources)
        if not module_sources:
            return False, "no module sources produced"

        writer = self._library_project_writer()
        return writer.write_library_project(
            crate_name=crate_name,
            output_project_path=output_project_path,
            module_sources=module_sources,
        )

    def export_archive_tests_to_project(
        self,
        archive: Dict[str, Dict[str, str]],
        include_test_files: List[str],
        output_project_path: str,
        crate_name: str,
    ) -> Tuple[bool, str]:
        """Write translated test modules under `tests/` for `cargo test`."""
        if not isinstance(archive, dict):
            return False, "archive is not a dict"

        test_sources = [
            name
            for name in include_test_files
            if name in archive and self._is_exportable_test_source(name)
        ]
        if not test_sources:
            return False, "no exportable test source found"

        module_sources, _ = self._render_module_sources(archive, test_sources)
        if not module_sources:
            return False, "no test module sources produced"

        tests_dir = os.path.join(output_project_path, "tests")
        os.makedirs(tests_dir, exist_ok=True)

        rendered = 0
        for source_name in test_sources:
            module_name = normalize_rust_module_name(source_name)
            module_text = (module_sources.get(module_name) or "").strip()
            if not module_text:
                continue

            normalized_lines: List[str] = []
            has_timeout_import = False
            for raw in module_text.splitlines():
                stripped = raw.strip()
                if stripped == "#![allow(warnings)]":
                    continue
                line = raw.replace("use crate::", f"use {crate_name}::")
                line = line.replace("crate::", f"{crate_name}::")
                if line.strip().startswith("use ntest::timeout"):
                    has_timeout_import = True
                normalized_lines.append(line)

            annotated_lines: List[str] = []
            prev_nonempty = ""
            for line in normalized_lines:
                stripped = line.strip()
                is_test_fn = stripped.startswith("pub fn test_") or stripped.startswith("fn test_")
                if is_test_fn and prev_nonempty != "#[test]":
                    annotated_lines.append("#[test]")
                annotated_lines.append(line)
                if stripped:
                    prev_nonempty = stripped

            test_body = "\n".join(annotated_lines).strip()
            if not test_body:
                continue

            if not has_timeout_import and "#[timeout(" in test_body:
                test_body = "use ntest::timeout;\n\n" + test_body

            rendered_text = f"{test_body}\n"
            test_path = os.path.join(tests_dir, f"{module_name}.rs")
            with open(test_path, "w", encoding="utf-8") as tf:
                tf.write(rendered_text)
            rendered += 1

        if rendered == 0:
            return False, "no non-empty tests rendered"
        return True, f"exported {rendered} test modules"

    def _render_module_sources(
        self,
        archive: Dict[str, Dict[str, str]],
        include_files: List[str],
    ) -> Tuple[Dict[str, str], Any]:
        """Render source buckets through the injected renderer or legacy seam."""
        if self._module_source_renderer is not None:
            return self._module_source_renderer.build_module_sources(archive, include_files)
        if hasattr(self, "_build_module_sources"):
            return self._build_module_sources(archive, include_files)
        return {}, ["module source renderer is not configured"]

    def _library_project_writer(self) -> Any:
        if self._cargo_project_writer is not None:
            return self._cargo_project_writer
        return CargoProjectWriter(verifier=getattr(self, "verifier", None))

    def _is_exportable_test_source(self, source_name: str) -> bool:
        if self._test_source_classifier is not None:
            return bool(self._test_source_classifier(source_name))
        if hasattr(self, "_is_test_source"):
            return bool(self._is_test_source(source_name))
        normalized = str(source_name or "").replace("\\", "/").lower()
        return normalized.startswith("tests/") or normalized.endswith("_test") or "/tests/" in normalized
