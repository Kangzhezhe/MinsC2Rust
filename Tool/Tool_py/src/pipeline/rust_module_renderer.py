"""Render checkpoint-compatible Rust archives into Cargo module sources."""

from typing import Any, Dict, List, Tuple

from utils import normalize_rust_module_name


class RustModuleSourceRenderer:
    """Build Rust module text from archive buckets.

    The renderer owns the archive-to-module rendering policy. It receives the
    broader archive tool object explicitly so the old helper functions can be
    reused while `RustArchiveBuilder` stops being responsible for every detail.
    """

    def __init__(self, archive_tools: Any):
        self.archive_tools = archive_tools

    def build_source_template(self, archive: Dict[str, Dict[str, str]], source_name: str) -> str:
        content = archive.get(source_name, {})
        ordered = []
        if content.get("extra"):
            ordered.append(content["extra"])
        for key, value in content.items():
            if key == "extra":
                continue
            ordered.append(value)
        return "\n\n".join(ordered)

    def build_module_sources(
        self,
        archive: Dict[str, Dict[str, str]],
        include_files: List[str],
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Render selected archive buckets into Rust module source strings."""
        tools = self.archive_tools
        module_sources: Dict[str, str] = {}
        module_to_source: Dict[str, str] = {}
        include_file_set = set(include_files)

        for source_name in include_files:
            module_name = normalize_rust_module_name(source_name)
            module_to_source[module_name] = source_name
            is_test_source = tools._is_test_source(source_name)
            per_source = archive.get(source_name, {})
            extra_content = per_source.get("extra", "").strip()
            if is_test_source:
                extra_content = tools._sanitize_non_function_content(extra_content)

            chunks = []
            fn_body_chunks = []
            for fn_name, fn_code in per_source.items():
                if fn_name == "extra":
                    continue
                normalized_fn = fn_code.strip()
                trimmed_fn = tools._trim_to_function_definition(normalized_fn)
                normalized_fn = trimmed_fn.strip() if trimmed_fn else ""
                if not normalized_fn:
                    continue
                if (not is_test_source) or fn_name.startswith("test_"):
                    normalized_fn = tools._ensure_public_function(normalized_fn + "\n").strip()
                fn_body_chunks.append(normalized_fn)

            body_chunks = []
            if extra_content:
                body_chunks.append(extra_content)
            body_chunks.extend(fn_body_chunks)

            current_body = "\n\n".join(body_chunks)
            dep_sources = tools._collect_source_dependency_sources(source_name, include_file_set)
            dep_exports_by_module = {
                normalize_rust_module_name(dep): tools._extract_export_names(dep, archive.get(dep, {}))
                for dep in dep_sources
            }
            hinted_dep_modules = (
                {normalize_rust_module_name(dep) for dep in dep_sources}
                if tools.enable_dependency_import_guessing
                else None
            )
            cleaned_extra, removed_shadowed = tools._prune_shadowed_extra(
                extra_content,
                dep_exports_by_module,
                hinted_dep_modules=hinted_dep_modules,
            )
            if cleaned_extra != extra_content:
                extra_content = cleaned_extra
                rebuilt_chunks: List[str] = []
                if extra_content:
                    rebuilt_chunks.append(extra_content)
                rebuilt_chunks.extend(fn_body_chunks)
                current_body = "\n\n".join(rebuilt_chunks)
                if removed_shadowed:
                    tools.logger.info(
                        f"[SHADOW-PRUNE] {source_name} removed={','.join(removed_shadowed[:8])}"
                    )

            std_imports = tools._build_std_imports(current_body)
            if std_imports:
                chunks.append("\n".join(std_imports))

            if dep_sources and tools.enable_dependency_import_guessing:
                dep_imports = tools._build_dependency_imports(current_body, archive, dep_sources)
                if dep_imports:
                    chunks.append("\n".join(dep_imports))

            if extra_content:
                chunks.append(extra_content)
            for fn_name, fn_code in per_source.items():
                if fn_name == "extra":
                    continue
                normalized_fn = fn_code.strip()
                trimmed_fn = tools._trim_to_function_definition(normalized_fn)
                normalized_fn = trimmed_fn.strip() if trimmed_fn else ""
                if not normalized_fn:
                    continue
                if (not is_test_source) or fn_name.startswith("test_"):
                    normalized_fn = tools._ensure_public_function(normalized_fn + "\n").strip()
                chunks.append(normalized_fn)

            if not chunks:
                chunks = ["// empty module"]

            module_text = "\n\n".join(chunks) + "\n"
            if is_test_source or module_name.startswith("test_"):
                module_text = tools._cleanup_test_module_text(module_text, module_name=module_name)
            module_text = tools._drop_self_module_use_imports(module_text, module_name)
            module_text = tools._dedupe_use_statements(module_text)
            module_sources[module_name] = module_text

        return module_sources, module_to_source
