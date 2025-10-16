#!/usr/bin/env python3
"""Generate a Rust project skeleton mirroring the C project structure.

The script reads `analyzer_config.yaml` to determine:
- `project_root`: the root of the original C project.
- `rust_output`: the destination directory to place the Rust skeleton.

Deterministic fallback behaviour:
- Each `.c` file becomes `<name>_c.rs` in the same relative path under `src/`.
- Each `.h` file becomes `<name>_h.rs` in the same relative path under `src/`.
- File contents are empty placeholders for now.
- A minimal Cargo project (Cargo.toml, Cargo.lock, src/lib.rs) is created.

Extended mode (`--use-llm`, default):
- Build lightweight summaries for each C/H 文件 based on analyzer outputs.
- Ask the project LLM to propose grouped Rust modules并生成 C→Rust 映射。
- Persist the mapping to `c_to_rust_mapping.json` inside the Rust output dir.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from pydantic import BaseModel, Field

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from analyzer.config import get_output_dir, get_project_root, load_rust_output_dir
from llm.llm import LLM
from llm.template_parser.template_parser import TemplateParser

C_EXTENSIONS = {".c"}
HEADER_EXTENSIONS = {".h"}

def _target_relative_path(rel_path: Path) -> Path | None:
    suffix = rel_path.suffix.lower()
    stem = rel_path.stem

    if suffix in C_EXTENSIONS:
        new_name = f"{stem}_c.rs"
    elif suffix in HEADER_EXTENSIONS:
        new_name = f"{stem}_h.rs"
    else:
        return None

    return rel_path.with_name(new_name)


def _collect_source_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in (C_EXTENSIONS | HEADER_EXTENSIONS):
            yield path


def _write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


_ANALYSIS_CACHE: Optional[Dict[str, Any]] = None


def _load_analysis_data() -> Dict[str, Any]:
    global _ANALYSIS_CACHE
    if _ANALYSIS_CACHE is not None:
        return _ANALYSIS_CACHE

    try:
        analysis_dir = get_output_dir()
    except Exception:
        analysis_dir = None

    if analysis_dir is None:
        _ANALYSIS_CACHE = {}
        return _ANALYSIS_CACHE

    analysis_path = Path(analysis_dir) / "c_project_analysis.json"
    if not analysis_path.exists():
        _ANALYSIS_CACHE = {}
        return _ANALYSIS_CACHE

    try:
        with analysis_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            data = {}
    except Exception as exc:
        print(f"读取分析输出失败: {exc}")
        data = {}

    _ANALYSIS_CACHE = data
    return _ANALYSIS_CACHE


SUMMARY_KEYS = [
    ("functions", "函数"),
    ("structs", "结构体"),
    ("typedefs", "类型别名"),
    ("macros", "宏"),
    ("variables", "变量"),
    ("enums", "枚举"),
]


def _summarize_file(rel_path: Path, project_root: Path, analysis_data: Dict[str, Any]) -> str:
    candidates = {
        rel_path.as_posix(),
        str(rel_path),
        rel_path.as_posix().lstrip("./"),
    }
    abs_path = (project_root / rel_path).as_posix()
    candidates.add(abs_path)

    file_data: Optional[Dict[str, Any]] = None
    for key in candidates:
        if key in analysis_data:
            file_data = analysis_data[key]
            break

    if not file_data:
        return "分析数据缺失"

    if not file_data.get("parse_success", True):
        return "解析失败或未成功提取符号"

    summaries: List[str] = []
    for cat_key, cat_label in SUMMARY_KEYS:
        items = file_data.get(cat_key) or []
        if not items:
            continue

        if cat_key == "functions":
            definitions: List[str] = []
            declarations: List[str] = []
            others: List[str] = []
            for entry in items:
                name = entry.get("name") or entry.get("full_declaration") or entry.get("full_definition")
                if not name:
                    continue
                entry_type = (entry.get("type") or "").lower()
                if entry_type == "function_definition":
                    if name not in definitions:
                        definitions.append(name)
                elif entry_type == "function_declaration":
                    if name not in declarations:
                        declarations.append(name)
                else:
                    if name not in others:
                        others.append(name)

            fragments: List[str] = []
            if definitions:
                snippet = ", ".join(definitions[:5])
                if len(definitions) > 5:
                    snippet += ", ..."
                fragments.append(f"定义: {snippet}")
            if declarations:
                snippet = ", ".join(declarations[:5])
                if len(declarations) > 5:
                    snippet += ", ..."
                fragments.append(f"声明: {snippet}")
            if others:
                snippet = ", ".join(others[:5])
                if len(others) > 5:
                    snippet += ", ..."
                fragments.append(f"未知: {snippet}")
            if not fragments:
                continue
            summaries.append(f"{cat_label}: {'；'.join(fragments)}")
            continue

        names: List[str] = []
        for entry in items:
            name = entry.get("name") or entry.get("full_declaration") or entry.get("full_definition")
            if not name:
                continue
            if name not in names:
                names.append(name)
        if not names:
            continue
        snippet = ", ".join(names[:5])
        if len(names) > 5:
            snippet += ", ..."
        summaries.append(f"{cat_label}: {snippet}")

    if not summaries:
        return "未识别出可列举的符号"

    return "；".join(summaries)


def _build_file_summaries(rel_sources: Sequence[Path], project_root: Path) -> Dict[str, str]:
    if not rel_sources:
        return {}

    analysis_data = _load_analysis_data()

    def worker(path: Path) -> tuple[str, str]:
        summary = _summarize_file(path, project_root, analysis_data)
        return path.as_posix(), summary

    max_workers = min(8, len(rel_sources)) or 1

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(worker, rel_sources))

    return {path: summary for path, summary in results}


class RustModuleSkeleton(BaseModel):
    rust_file: str = Field(..., description="Rust 源文件（相对 src/ 的路径，包含 .rs）")
    sources: List[str] = Field(..., description="归入该模块的 C/H 文件相对路径")
    description: Optional[str] = Field(None, description="模块职责简述")


class RustSkeletonPlan(BaseModel):
    modules: List[RustModuleSkeleton] = Field(..., description="全部 Rust 模块规划")


def _sanitize_module_name(raw: str) -> str:
    name = raw.replace("-", "_").replace(".", "_")
    if name and name[0].isdigit():
        name = f"m_{name}"
    return name


def _format_lib_rs_content(module_paths: Iterable[Path]) -> str:
    lines = [
        "// Auto-generated module declarations.\n",
    ]
    unique_paths = sorted({Path(p) for p in module_paths})
    for rel_path in unique_paths:
        module_name = _sanitize_module_name("_".join(rel_path.with_suffix("").parts))
        inline_path = rel_path.as_posix()
        lines.append(f"#[path = \"{inline_path}\"]\n")
        lines.append(f"pub mod {module_name};\n\n")
    if len(lines) == 1:
        lines.append("// No source files discovered.\n")
    return "".join(lines)


def _generate_cargo_files(project_dir: Path, package_name: str) -> None:
    cargo_toml = project_dir / "Cargo.toml"
    cargo_lock = project_dir / "Cargo.lock"
    src_dir = project_dir / "src"
    lib_rs = src_dir / "lib.rs"

    src_dir.mkdir(parents=True, exist_ok=True)

    cargo_toml_content = f"""[package]
name = \"{package_name}\"
version = \"0.1.0\"
edition = \"2021\"

[dependencies]
"""
    _write_file(cargo_toml, cargo_toml_content)

    if not cargo_lock.exists():
        cargo_lock.touch()

    if not lib_rs.exists():
        _write_file(lib_rs)


def _request_llm_plan(
    rel_sources: Sequence[Path],
    summaries: Dict[str, str],
) -> Optional[RustSkeletonPlan]:
    if not rel_sources:
        return None

    file_entries: List[str] = []
    for rel_path in rel_sources:
        key = rel_path.as_posix()
        summary = summaries.get(key) or "无摘要"
        file_entries.append(f"- {key}\n  摘要: {summary}")

    file_list_text = "\n".join(file_entries)
    prompt = (
        "我们正在把一个 C 工程迁移到 Rust。下面列出所有 C 源文件与头文件的相对路径：\n"
        f"{file_list_text}\n\n"
        "请根据这些文件规划 Rust 项目的模块拆分。要求：\n"
        "1. 输出必须满足 RustSkeletonPlan 的 JSON Schema。\n"
        "2. modules 中每一项包含 rust_file（以 src/ 或 test/ 开头，如果是测试文件则放入 test/，扩展名 .rs）、sources（必须从上方列表中取值）、description（简短说明即可，可引用摘要信息）。\n"
        "3. 可以将匹配的 .c 与 .h 合并到同一个 Rust 文件，也可以按目录聚合，但不要遗漏任何来源文件。\n"
        "4. 模块的划分与描述应优先参考给定摘要，而不是仅凭文件名。\n"
        "5. 输出 JSON 时不要添加除必要转义以外的多余文本或注释。\n"
    )

    llm = LLM(logger=True)
    parser = TemplateParser(
        "{plan:json:RustSkeletonPlan}",
        model_map={
            "RustSkeletonPlan": RustSkeletonPlan,
            "RustModuleSkeleton": RustModuleSkeleton,
        },
    )

    try:
        result = llm.call(prompt, parser=parser, max_retry=4)
    except Exception as exc:  # pragma: no cover - LLM 可能暂不可用
        print(f"LLM 规划失败（调用异常）: {exc}")
        return None

    if not isinstance(result, dict) or not result.get("success"):
        print(f"LLM 规划失败（解析错误）: {result}")
        return None

    try:
        plan_data = result["data"]["plan"]
        return RustSkeletonPlan.model_validate(plan_data)
    except Exception as exc:  # pragma: no cover
        print(f"LLM 规划结果不符合模型: {exc}")
        return None


def _build_default_plan(
    rel_sources: Sequence[Path],
    summaries: Dict[str, str],
) -> RustSkeletonPlan:
    modules: List[RustModuleSkeleton] = []
    for rel_path in rel_sources:
        target_rel = _target_relative_path(rel_path)
        if target_rel is None:
            continue
        key = rel_path.as_posix()
        summary = summaries.get(key)
        description = summary or f"自动生成占位：来自 {key}"
        if summary and len(summary) > 200:
            description = summary[:197] + "..."
        modules.append(
            RustModuleSkeleton(
                rust_file=target_rel.as_posix(),
                sources=[rel_path.as_posix()],
                description=description,
            )
        )
    return RustSkeletonPlan(modules=modules)


def _materialize_plan(
    rust_output_dir: Path,
    plan: RustSkeletonPlan,
    summaries: Dict[str, str],
) -> List[Path]:
    src_root = rust_output_dir / "src"
    src_root.mkdir(parents=True, exist_ok=True)

    created_files: List[Path] = []
    module_paths: List[Path] = []
    c_to_rust: dict[str, str] = {}

    for module in plan.modules:
        rust_rel = Path(module.rust_file)
        if rust_rel.is_absolute():
            rust_rel = Path(*rust_rel.parts[1:])
        if rust_rel.suffix != ".rs":
            rust_rel = rust_rel.with_suffix(".rs")
        dest_path = src_root / rust_rel

        placeholder_lines = [
            "// Auto-generated placeholder.\n",
        ]
        if module.description:
            placeholder_lines.append(f"// {module.description}\n")
        if module.sources:
            placeholder_lines.append("// Sources:\n")
            placeholder_lines.extend(f"// - {source}\n" for source in module.sources)
            for source in module.sources:
                summary = summaries.get(source)
        placeholder_lines.append("// TODO: 填写转译后的 Rust 实现。\n")
        _write_file(dest_path, "".join(placeholder_lines))

        created_files.append(dest_path)
        module_paths.append(rust_rel)

        for source in module.sources:
            c_to_rust[source] = rust_rel.as_posix()

    lib_content = _format_lib_rs_content(module_paths)
    _write_file(src_root / "lib.rs", lib_content)

    mapping_payload = {
        "modules": [module.model_dump() for module in plan.modules],
        "c_to_rust": c_to_rust,
        "summaries": {source: summaries.get(source) for source in c_to_rust},
    }
    mapping_path = rust_output_dir / "c_to_rust_mapping.json"
    _write_file(mapping_path, json.dumps(mapping_payload, ensure_ascii=False, indent=2))

    return created_files


def build_rust_skeleton(use_llm: bool = True) -> Path:
    project_root = get_project_root()
    rust_output_dir = load_rust_output_dir()

    if rust_output_dir.exists():
        shutil.rmtree(rust_output_dir)
    rust_output_dir.mkdir(parents=True, exist_ok=True)

    package_name = project_root.name.replace("-", "_")
    _generate_cargo_files(rust_output_dir, package_name)

    rel_sources = [path.relative_to(project_root) for path in _collect_source_files(project_root)]
    summaries = _build_file_summaries(rel_sources, project_root)

    plan: Optional[RustSkeletonPlan] = None
    if use_llm:
        plan = _request_llm_plan(rel_sources, summaries)
        if plan is None:
            print("LLM 规划失败，回退到默认规则。")

    if plan is None:
        plan = _build_default_plan(rel_sources, summaries)

    created_files = _materialize_plan(rust_output_dir, plan, summaries)

    print(f"生成 Rust 项目: {rust_output_dir}")
    print(f"创建 {len(created_files)} 个占位文件")
    return rust_output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Rust skeleton for the C project")
    parser.add_argument(
        "--use-llm",
        dest="use_llm",
        action="store_true",
        default=True,
        help="调用 LLM 规划 Rust 文件结构（默认开启）",
    )
    parser.add_argument(
        "--no-llm",
        dest="use_llm",
        action="store_false",
        help="禁用 LLM，使用简单映射规则",
    )
    args = parser.parse_args()
    build_rust_skeleton(use_llm=args.use_llm)
