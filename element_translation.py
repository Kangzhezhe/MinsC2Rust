import atexit
from functools import partial
import json
import os
import re
import shlex
from collections import OrderedDict, defaultdict
from pathlib import Path
import subprocess
from typing import TYPE_CHECKING, Any, DefaultDict, Dict, List, Optional, Set, Tuple, TypedDict

from langgraph.graph import END, StateGraph  # type: ignore
from pydantic import BaseModel, Field
from pydantic import ConfigDict  # type: ignore
from llm.template_parser.template_parser import TemplateParser
from llm.llm import LLM
from llm.rag import build_csv_mapping_collection, search_knowledge_base
from analyzer.analyzer import Analyzer
from analyzer.config import get_project_root, load_rust_output_dir
from analyzer.symbol_model import SymbolModel, normalize_symbol_type


class RustItem(BaseModel):
    """单个 Rust 元素（name + 完整源码 + 备注）。"""

    name: str = Field(..., description="Rust 元素名（类型/结构体/函数/常量等）")
    code: str = Field(..., description="该元素的完整 Rust 源码")
    note: Optional[str] = Field(..., description="一句话描述该元素对应的转换/映射/删除说明，比如：为什么要转换/映射/删除。")

    try:
        model_config = ConfigDict(json_schema_extra={
            "description": "RustItem：单个 Rust 元素，包含名称、源码与处理说明。"
        })
    except Exception:
        pass


class RustBatch(BaseModel):
    """批量转译结果：items + C→Rust（单值或 null）。"""

    items: List[RustItem] = Field(..., description="生成的 Rust 元素列表")
    # c_to_rust: 每个输入的 C 符号名 -> 由其转译得到的 Rust 符号名（一个或无，对无对应请用 null）
    mapping_c2r: Dict[str, Optional[str]] = Field(
    ..., description="C 名 → Rust 名；无对应为 null"
    )

    try:
        model_config = ConfigDict(json_schema_extra={
            "description": "RustBatch：批处理转译结果，含 items 与 mapping_c2r（C→Rust 单值/null）。"
        })
    except Exception:
        pass


class BatchState(TypedDict, total=False):
    remaining_batches: List[Dict[str, Any]]
    items: List[Dict[str, Any]]
    mapping_c2r: Dict[str, Optional[str]]
    history: List[Dict[str, Any]]
    error: str
    translated_symbols: List[str]


TYPE_MAPPING_CSV = "data/c_to_rust_type_mapping.csv"
TYPE_MAPPING_COLLECTION = "c_to_rust_type_mapping"
TYPE_MAPPING_KEY_FIELDS = ["Type", "C 类型", "C 示例"]
TYPE_MAPPING_TOP_K = 6
TYPE_MAPPING_RERANK_TOP_N = 3
MAX_CHARS_PER_TRANSLATION = 3000
COMPILE_MAX_RETRIES = 3
AUTO_DEPENDENCY_EXPANSION_LIMIT = 64

FUNCTION_SYMBOL_TYPES: Set[str] = {"functions"}
NON_FUNCTION_SYMBOL_TYPES: Set[str] = {"structs", "typedefs", "macros", "variables", "enums"}

def _symbol_primary_text(symbol: Dict[str, Any]) -> str:
    return symbol.get("full_declaration", "")


def _symbol_unique_key(symbol: Dict[str, Any]) -> Optional[str]:
    name = symbol.get("name") or symbol.get("symbol") or symbol.get("id")
    if not name:
        return None

    sym_type = normalize_symbol_type(symbol.get("type")) or ""
    file_path = (
        symbol.get("file_path")
        or symbol.get("file")
        or symbol.get("source_file")
        or symbol.get("path")
    )
    file_path_norm = _normalize_c_key(str(file_path)) if file_path else ""

    return "|".join([name, sym_type, file_path_norm])

_ANALYZER: Optional[Analyzer] = None
_PROJECT_ROOT: Optional[Path] = None
_RUST_SRC_ROOT: Optional[Path] = None
_C_TO_RUST_MAP: Optional[Dict[str, Path]] = None
_DEST_FILE_SYMBOLS: Dict[Path, OrderedDict[str, str]] = {}
_DEST_EXPECTED_SOURCES: Dict[Path, Set[str]] = {}
_DEST_COMPLETED_SOURCES: DefaultDict[Path, Set[str]] = defaultdict(set)
_DEST_FLUSHED_DESTS: Set[Path] = set()
_SWE_AGENT_INSTANCE: Optional["SWEAgent"] = None
_RUST_FILE_CACHE: Dict[Path, str] = {}

MAPPING_C2R_FILENAME = "mapping_c2r.json"


if TYPE_CHECKING:  # pragma: no cover - 仅用于类型检查
    from llm.swe_agent import SWEAgent


def _close_swe_agent_instance() -> None:
    global _SWE_AGENT_INSTANCE
    agent = _SWE_AGENT_INSTANCE
    if agent is None:
        return
    try:
        agent.close()
    except Exception:
        pass
    _SWE_AGENT_INSTANCE = None


atexit.register(_close_swe_agent_instance)


def _get_project_root_cached() -> Optional[Path]:
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        try:
            _PROJECT_ROOT = get_project_root()
        except Exception:
            return None
    return _PROJECT_ROOT


def _get_rust_src_root() -> Optional[Path]:
    global _RUST_SRC_ROOT
    if _RUST_SRC_ROOT is None:
        try:
            rust_root = load_rust_output_dir()
        except Exception:
            return None
        _RUST_SRC_ROOT = rust_root / "src"
        _RUST_SRC_ROOT.mkdir(parents=True, exist_ok=True)
    return _RUST_SRC_ROOT


def _get_swe_agent_instance() -> Optional["SWEAgent"]:
    global _SWE_AGENT_INSTANCE
    if _SWE_AGENT_INSTANCE is not None:
        return _SWE_AGENT_INSTANCE

    try:
        from llm.swe_agent import SWEAgent  # 延迟导入以避免初始化开销
    except Exception as exc:  # pragma: no cover - 防御性处理
        print(f"导入 SWEAgent 失败: {exc}")
        return None

    try:
        rust_root = load_rust_output_dir()
    except Exception as exc:
        print(f"无法定位 Rust 输出目录，跳过 SWE Agent 初始化: {exc}")
        return None

    if rust_root is None:
        print("load_rust_output_dir 返回 None，跳过 SWE Agent 初始化")
        return None

    try:
        rust_root.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        print(f"创建 Rust 输出目录失败: {exc}")
        return None

    try:
        _SWE_AGENT_INSTANCE = SWEAgent(workspace_root=str(rust_root),logger=True,
        max_iterations=50,
        command_timeout=90,
        memory_strategy={"name": "summary", "token_trigger_max_tokens": 3000},
        )
    except Exception as exc:
        print(f"初始化 SWEAgent 失败: {exc}")
        return None

    return _SWE_AGENT_INSTANCE


def _resolve_relative_c_path(path_value: str) -> Optional[Path]:
    if not path_value:
        return None
    raw_path = Path(path_value)
    if raw_path.is_absolute():
        project_root = _get_project_root_cached()
        if project_root is None:
            return Path(raw_path.name)
        try:
            relative = raw_path.relative_to(project_root)
        except ValueError:
            relative = Path(os.path.relpath(raw_path, project_root))
        return Path(*relative.parts)
    return Path(*raw_path.parts)


def _normalize_c_key(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def _load_c_to_rust_map() -> Dict[str, Path]:
    global _C_TO_RUST_MAP
    if _C_TO_RUST_MAP is not None:
        return _C_TO_RUST_MAP

    mapping: Dict[str, Path] = {}
    try:
        rust_output_dir = load_rust_output_dir()
    except Exception:
        _C_TO_RUST_MAP = mapping
        return mapping

    mapping_path = rust_output_dir / "c_to_rust_mapping.json"
    if mapping_path.exists():
        try:
            with mapping_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            c_to_rust = data.get("c_to_rust", {})
            if isinstance(c_to_rust, dict):
                for raw_c, raw_rust in c_to_rust.items():
                    if not isinstance(raw_c, str) or not isinstance(raw_rust, str):
                        continue
                    norm_c = _normalize_c_key(raw_c)
                    rust_rel = Path(raw_rust)
                    if rust_rel.is_absolute():
                        try:
                            rust_rel = rust_rel.relative_to(rust_output_dir / "src")
                        except ValueError:
                            try:
                                rust_rel = rust_rel.relative_to(rust_output_dir)
                            except ValueError:
                                pass
                    mapping[norm_c] = rust_rel
        except Exception as exc:
            print(f"读取 c_to_rust_mapping.json 失败: {exc}")

    _C_TO_RUST_MAP = mapping
    return mapping


def _map_c_to_rust_via_mapping(rel_path: Path) -> Optional[Path]:
    mapping = _load_c_to_rust_map()
    if not mapping:
        return None
    candidates = {
        _normalize_c_key(rel_path.as_posix()),
        _normalize_c_key(str(rel_path)),
    }
    for candidate in candidates:
        if candidate in mapping:
            return mapping[candidate]
    return None


def _map_c_path_to_rust_relative(rel_path: Path) -> Optional[Path]:
    mapped = _map_c_to_rust_via_mapping(rel_path)
    if mapped is not None:
        return mapped

    suffix = rel_path.suffix.lower()
    if suffix == ".c":
        new_name = f"{rel_path.stem}_c.rs"
    elif suffix == ".h":
        new_name = f"{rel_path.stem}_h.rs"
    else:
        return None
    return rel_path.with_name(new_name)


def _candidate_dest_paths_for_c_file(file_path: str) -> List[Path]:
    rel_path = _resolve_relative_c_path(file_path)
    if rel_path is None:
        return []
    target_rel = _map_c_path_to_rust_relative(rel_path)
    if target_rel is None:
        return []
    src_root = _get_rust_src_root()
    if src_root is None:
        return []
    return [src_root / target_rel]


def _read_rust_file_cached(path: Path) -> Optional[str]:
    cached = _RUST_FILE_CACHE.get(path)
    if cached is not None:
        return cached
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    _RUST_FILE_CACHE[path] = text
    return text


def _extract_rust_item_from_text(rust_name: str, content: str) -> Optional[str]:
    if not content.strip():
        return None
    pattern = re.compile(
        rf"(?ms)(^pub(?:\([^\n]+\))?(?:\s+\w+)*\s+(?:struct|enum|fn|type|const|static)\s+{re.escape(rust_name)}\b[\s\S]*?)(?=^pub(?:\([^\n]+\))?(?:\s+\w+)*\s+(?:struct|enum|fn|type|const|static)\s+\w|\Z)"
    )
    match = pattern.search(content)
    if match:
        return match.group(1).strip()

    # Fallback: locate first occurrence of the symbol name following a pub item and grab a window of lines.
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        if "pub" in line and rust_name in line:
            start = max(idx - 2, 0)
            end = min(idx + 60, len(lines))
            snippet = "\n".join(lines[start:end]).strip()
            if snippet:
                return snippet
    return None


def _load_rust_code_for_dependency(dep, rust_name: str, rust_defs: Dict[str, str]) -> Optional[str]:
    candidate_paths = _candidate_dest_paths_for_c_file(dep.file_path)
    for path in candidate_paths:
        text = _read_rust_file_cached(path)
        if text is None:
            continue
        snippet = _extract_rust_item_from_text(rust_name, text)
        if snippet:
            rust_defs[rust_name] = snippet
            return snippet
    for path in candidate_paths:
        text = _read_rust_file_cached(path)
        if text is None:
            continue
        trimmed = text.strip()
        if trimmed:
            # limit to avoid oversized context
            rust_defs[rust_name] = trimmed[:8000]
            return rust_defs[rust_name]
    return None


def _get_expected_sources_for_dest(dest_path: Path, target_rel: Path) -> Set[str]:
    expected = _DEST_EXPECTED_SOURCES.get(dest_path)
    if expected is not None:
        return expected

    mapping = _load_c_to_rust_map()
    expected = {
        c_norm for c_norm, rust_rel in mapping.items()
        if rust_rel == target_rel
    }
    _DEST_EXPECTED_SOURCES[dest_path] = expected
    return expected


def _format_relative_paths(paths: Set[Path]) -> List[str]:
    project_root = _get_project_root_cached()
    formatted: List[str] = []
    for path in sorted(paths):
        if project_root is not None:
            try:
                formatted.append(str(path.relative_to(project_root)))
                continue
            except ValueError:
                pass
        formatted.append(path.as_posix())
    return formatted


def _verify_compile_success(context, agent: "SWEAgent", compile_cmd: str, dest_paths: Set[Path]) -> Tuple[bool, Optional[str]]:
    try:
        rerun = agent.toolset.run_command(compile_cmd)
    except Exception as exc:
        return False, f"复验命令异常: {exc}"

    if (rerun or {}).get("returncode", 0) == 0:
        rel_list = _format_relative_paths(dest_paths)
        return True, "编译通过"
    return False, "复验失败，错误信息：" + (rerun.get("stderr", "").strip() or rerun.get("stdout", "").strip() or "无错误输出")

def _run_swe_agent_compile(dest_paths: Set[Path]) -> None:
    if not dest_paths:
        return True

    agent = _get_swe_agent_instance()
    if agent is None:
        return False

    try:
        rust_output_dir = load_rust_output_dir()
    except Exception as exc:
        print(f"无法定位 Rust 输出目录，跳过编译：{exc}")
        return False

    cargo_toml = rust_output_dir / "Cargo.toml"
    if not cargo_toml.exists():
        print(f"未找到 Cargo.toml: {cargo_toml}")
        return False

    compile_cmd_parts = ["RUSTFLAGS=-Awarnings", "cargo", "check", "--manifest-path", str(cargo_toml)]
    compile_cmd = " ".join(shlex.quote(part) for part in compile_cmd_parts)

    try:
        result = agent.toolset.run_command(compile_cmd)
    except Exception as exc:
        print(f"SWE Agent 执行编译命令失败: {exc}")
        return False

    if (result or {}).get("returncode", 0) == 0:
        rel_list = _format_relative_paths(dest_paths)
        print(f"SWE Agent 编译通过: {compile_cmd} -> {', '.join(rel_list)}")
        return True

    error_output = f"{result.get('stderr', '').strip()}\n{result.get('stdout', '').strip()}".strip()
    if not error_output:
        error_output = "编译失败但没有提供错误输出。"

    error_lines = error_output.splitlines()
    truncated_error = "\n".join(error_lines[:200])

    rel_paths = _format_relative_paths(dest_paths)
    cargo_toml_display = _format_relative_paths({cargo_toml})[0] if cargo_toml else str(cargo_toml)

    task_description = (
        "自动转译后的 Rust 文件编译失败，请修复所有编译错误并确保 cargo check 通过。仅修改必要文件，保留原有功能\n"
        f"涉及文件：{', '.join(rel_paths)}\n"
        f"编译命令使用run_command工具：{compile_cmd}\n"
        f"Cargo.toml 位置：{cargo_toml_display}\n"
        "模块导入提示：库入口文件位于 src/lib.rs，可查看其中的模块声明来确定需要 use 或 pub use 的模块路径，use语句放到文件的开头；但是不要修改src/lib.rs文件\n"
        "若需查找现有符号或实现，可使用 LSP 搜索工具（如提供的 symbol_definitions/symbol_usage 能力）来定位定义与引用；\n"
        "如需新增第三方依赖，可调用 run_command 执行 cargo add 或其他下载命令。"
    )

    review_cb = partial(_verify_compile_success, agent=agent, compile_cmd=compile_cmd, dest_paths=dest_paths)

    try:
        agent.run_task(
            task_description,
            acceptance_criteria=[
                f"最后一次调用一定是：检查编译错误使用run_command工具：{compile_cmd}cargo check 成功"
            ],
            review_condition=review_cb,
        )
    except Exception as exc:
        print(f"SWE Agent 尝试修复编译错误失败: {exc}")
        return False

    try:
        rerun = agent.toolset.run_command(compile_cmd)
    except Exception as exc:
        print(f"SWE Agent 复验编译命令失败: {exc}")
        return False

    if (rerun or {}).get("returncode", 0) == 0:
        rel_list = _format_relative_paths(dest_paths)
        print(f"SWE Agent 修复后编译通过: {', '.join(rel_list)}")
        return True
    else:
        print("SWE Agent 修复后仍未通过编译，请手动检查。")
        return False
        # raise RuntimeError("SWE Agent 修复后仍未通过编译，请手动检查。")


def _snapshot_rust_files(file_paths: Set[Path]) -> Dict[Path, Optional[str]]:
    snapshots: Dict[Path, Optional[str]] = {}
    for path in sorted(file_paths):
        try:
            if path.exists():
                snapshots[path] = path.read_text(encoding="utf-8")
            else:
                snapshots[path] = None
        except Exception as exc:
            print(f"记录快照失败: {path}: {exc}")
            snapshots[path] = None
    return snapshots


def _restore_rust_files(snapshots: Dict[Path, Optional[str]]) -> None:
    for path, content in snapshots.items():
        try:
            if content is None:
                if path.exists():
                    path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except Exception as exc:
            print(f"恢复快照失败: {path}: {exc}")


def _persist_batch_to_rust(
    batch: Dict[str, Any],
    items: List[Dict[str, Any]],
    mapping_c2r: Dict[str, Optional[str]],
    full_mapping: Dict[str, Optional[str]],
) -> Set[Path]:
    src_root = _get_rust_src_root()
    if src_root is None:
        return set()

    symbol_files: Dict[str, Set[Path]] = {}
    for sym in batch.get("symbols", []):
        c_name = sym.get("name") or sym.get("symbol") or sym.get("id")
        file_path = sym.get("file_path")
        rel_path = _resolve_relative_c_path(file_path) if file_path else None
        if not c_name or rel_path is None:
            continue
        symbol_files.setdefault(c_name, set()).add(rel_path)

    symbol_destinations: Dict[str, Set[Path]] = {}
    for c_name, rel_paths in symbol_files.items():
        dests: Set[Path] = set()
        for rel_path in rel_paths:
            target_rel = _map_c_path_to_rust_relative(rel_path)
            if target_rel is not None:
                dests.add(target_rel)
        if dests:
            symbol_destinations[c_name] = dests

    rust_to_destinations: Dict[str, Set[Path]] = {}
    for c_name, rust_name in (mapping_c2r or {}).items():
        if not rust_name:
            continue
        dests = symbol_destinations.get(c_name)
        if not dests:
            continue
        rust_to_destinations.setdefault(rust_name, set()).update(dests)

    fallback_files: Set[Path] = set()
    batch_files_raw = batch.get("files", [])
    if isinstance(batch_files_raw, list):
        for file_entry in batch_files_raw:
            rel = _resolve_relative_c_path(str(file_entry))
            if rel is not None:
                fallback_files.add(rel)

    for rel_paths in symbol_files.values():
        fallback_files.update(rel_paths)

    sources_by_dest_rel: DefaultDict[Path, Set[str]] = defaultdict(set)
    for rel_path in fallback_files:
        target_rel = _map_c_path_to_rust_relative(rel_path)
        if target_rel is None:
            continue
        sources_by_dest_rel[target_rel].add(_normalize_c_key(rel_path.as_posix()))

    fallback_destinations: Set[Path] = set(sources_by_dest_rel.keys())
    if not fallback_destinations and symbol_destinations:
        for dests in symbol_destinations.values():
            fallback_destinations.update(dests)

    dest_segments: Dict[Path, Dict[str, str]] = {}
    for item in items:
        code = item.get("code")
        if not isinstance(code, str) or not code.strip():
            continue
        rust_name = item.get("name")
        if not isinstance(rust_name, str) or not rust_name.strip():
            continue
        target_rels = rust_to_destinations.get(rust_name) or fallback_destinations
        if not target_rels:
            continue
        for target_rel in target_rels:
            cleaned_code = code.strip()
            if not cleaned_code:
                continue
            dest_segments.setdefault(target_rel, {})[rust_name] = cleaned_code

    affected_target_rels: Set[Path] = set(dest_segments.keys()) | set(sources_by_dest_rel.keys())
    if not affected_target_rels:
        return set()

    updated_dest_paths: Set[Path] = set()
    for target_rel, segments in dest_segments.items():
        dest_path = src_root / target_rel
        symbol_map = _DEST_FILE_SYMBOLS.setdefault(dest_path, OrderedDict())
        updated = False
        for rust_name, cleaned_code in segments.items():
            existing_code = symbol_map.get(rust_name)
            if existing_code == cleaned_code:
                continue
            symbol_map[rust_name] = cleaned_code
            updated = True
        if updated:
            updated_dest_paths.add(dest_path)

    for target_rel, source_norms in sources_by_dest_rel.items():
        dest_path = src_root / target_rel
        _DEST_COMPLETED_SOURCES[dest_path].update(source_norms)

    written_paths: Set[Path] = set()

    for target_rel in affected_target_rels:
        dest_path = src_root / target_rel
        symbol_map = _DEST_FILE_SYMBOLS.get(dest_path)
        if not symbol_map:
            continue
        expected_sources = _get_expected_sources_for_dest(dest_path, target_rel)
        completed_sources = _DEST_COMPLETED_SOURCES.get(dest_path, set())
        ready = not expected_sources or expected_sources.issubset(completed_sources)
        if not ready:
            continue
        should_flush = dest_path in updated_dest_paths or dest_path not in _DEST_FLUSHED_DESTS
        if not should_flush:
            continue
        content_pieces = [segment.rstrip() for segment in symbol_map.values() if segment.strip()]
        if not content_pieces:
            continue
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            body_text = "\n\n".join(content_pieces).rstrip()
            final_text = body_text + "\n"
            dest_path.write_text(final_text, encoding="utf-8")
            written_paths.add(dest_path)
            _DEST_FLUSHED_DESTS.add(dest_path)
        except Exception as exc:
            print(f"写入 Rust 文件失败: {dest_path}: {exc}")
    return written_paths


def _persist_mapping_c2r(mapping: Dict[str, Optional[str]]) -> None:
    try:
        rust_output_dir = load_rust_output_dir()
    except Exception as exc:
        print(f"无法定位 Rust 输出目录，跳过映射保存：{exc}")
        return

    if rust_output_dir is None:
        return

    target_path = rust_output_dir / MAPPING_C2R_FILENAME

    try:
        payload = {"mapping_c2r": mapping}
        target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"写入 mapping_c2r 失败: {exc}")


def _parse_mapping_doc(doc: str) -> Optional[Tuple[Dict[str, str], Dict[str, str]]]:
    try:
        payload = json.loads(doc)
    except (json.JSONDecodeError, TypeError):
        return None

    key_part = payload.get("key") or {}
    value_part = payload.get("value") or {}

    if not key_part and not value_part:
        return None

    return (
        {k: str(v) for k, v in key_part.items() if v is not None},
        {k: str(v) for k, v in value_part.items() if v is not None},
    )



def retrieve_type_mapping_context(batch) -> List[str]:
    mappings: List[str] = []
    seen_docs: set[str] = set()
    seen_keys: set[Tuple[Tuple[str, str], ...]] = set()

    for symbol in batch.get("symbols", []):
        content = _symbol_primary_text(symbol)
        if not content.strip():
            continue

        docs = search_knowledge_base(
            content.strip(),
            collection_name=TYPE_MAPPING_COLLECTION,
            top_k=TYPE_MAPPING_TOP_K,
            use_rerank=True,
            rerank_top_n=TYPE_MAPPING_RERANK_TOP_N,
        )

        for doc in docs:
            if doc in seen_docs:
                continue
            parsed = _parse_mapping_doc(doc)
            if not parsed:
                continue
            key_part, value_part = parsed
            key_signature = tuple(sorted(key_part.items()))
            if key_signature in seen_keys:
                continue

            seen_docs.add(doc)
            seen_keys.add(key_signature)
            formatted = parsed
            if formatted:
                mappings.append(formatted)

    return mappings


def get_analyzer() -> Analyzer:
    global _ANALYZER
    if _ANALYZER is None:
        _ANALYZER = Analyzer()
    return _ANALYZER


def _mapping_has_resolved_target(mapping: Dict[str, Optional[str]], name: Optional[str]) -> bool:
    if not name:
        return False
    direct = mapping.get(name)
    if isinstance(direct, str) and direct.strip():
        return True
    normalized = _normalize_c_key(name)
    resolved = mapping.get(normalized)
    return isinstance(resolved, str) and resolved.strip()


def _get_symbol_ref_for_symbol(analyzer: Analyzer, symbol: Dict[str, Any]):
    name = symbol.get("name") or symbol.get("symbol") or symbol.get("id")
    sym_type = normalize_symbol_type(symbol.get("type"))
    file_path = symbol.get("file_path")
    if not (name and sym_type and file_path):
        return None
    try:
        refs = analyzer.find_symbols_by_name(name, symbol_type=sym_type, file_path=file_path)
    except Exception:
        return None
    return refs[0] if refs else None


def _materialize_symbol_from_ref(analyzer: Analyzer, sym_ref) -> Optional[Dict[str, Any]]:
    file_data = analyzer.analysis_data.get(sym_ref.file_path) if hasattr(analyzer, "analysis_data") else None
    candidate: Optional[Dict[str, Any]] = None
    entries = []
    if isinstance(file_data, dict):
        entries = file_data.get(sym_ref.type, []) or []
        for entry in entries:
            entry_name = entry.get("name") or entry.get("text")
            if entry_name != sym_ref.name:
                continue
            entry_start = entry.get("start_line")
            if entry_start and sym_ref.start_line and entry_start != sym_ref.start_line:
                continue
            candidate = entry
            break
        if candidate is None:
            for entry in entries:
                entry_name = entry.get("name") or entry.get("text")
                if entry_name == sym_ref.name:
                    candidate = entry
                    break

    if candidate is None:
        definition = analyzer.extract_definition_text(sym_ref)
        if not definition.strip():
            return None
        return {
            "name": sym_ref.name,
            "type": sym_ref.type,
            "file_path": sym_ref.file_path,
            "full_definition": definition,
            "full_declaration": "",
        }

    symbol_data = dict(candidate)
    symbol_data["name"] = sym_ref.name
    symbol_data["type"] = sym_ref.type
    symbol_data["file_path"] = sym_ref.file_path

    if not symbol_data.get("full_definition"):
        definition = analyzer.extract_definition_text(sym_ref)
        if definition.strip():
            symbol_data["full_definition"] = definition

    if not symbol_data.get("full_declaration"):
        placeholder_decl = symbol_data.get("declaration") or symbol_data.get("text") or ""
        symbol_data["full_declaration"] = placeholder_decl

    return symbol_data


def _expand_symbols_with_missing_dependencies(
    symbols: List[Dict[str, Any]],
    current_mapping: Dict[str, Optional[str]],
) -> Tuple[List[Dict[str, Any]], int]:
    if not symbols:
        return symbols, 0

    try:
        analyzer = get_analyzer()
    except Exception:
        return symbols, 0

    expanded: List[Dict[str, Any]] = list(symbols)
    added = 0
    visited_keys: Set[str] = set()
    pending_refs: List = []

    for symbol in expanded:
        sym_ref = _get_symbol_ref_for_symbol(analyzer, symbol)
        if sym_ref is None:
            continue
        key = sym_ref.key()
        if key in visited_keys:
            continue
        visited_keys.add(key)
        pending_refs.append(sym_ref)

    while pending_refs:
        current_ref = pending_refs.pop(0)

        try:
            func_nodes, _ = analyzer.get_dependencies(
                current_ref,
                depth=1,
                direction="out",
                symbol_types=FUNCTION_SYMBOL_TYPES,
            )
        except Exception:
            func_nodes = []

        try:
            non_func_nodes, _ = analyzer.get_dependencies(
                current_ref,
                depth=None,
                direction="out",
                symbol_types=NON_FUNCTION_SYMBOL_TYPES,
            )
        except Exception:
            non_func_nodes = []

        for dep in func_nodes + non_func_nodes:
            dep_key = dep.key()
            if dep_key in visited_keys:
                continue
            visited_keys.add(dep_key)

            if _mapping_has_resolved_target(current_mapping, dep.name):
                continue

            dep_symbol = _materialize_symbol_from_ref(analyzer, dep)
            if dep_symbol is None:
                continue

            expanded.append(dep_symbol)
            pending_refs.append(dep)
            added += 1

            if added >= AUTO_DEPENDENCY_EXPANSION_LIMIT:
                return expanded, added

    return expanded, added


def gather_dependency_context(
    symbols: List[Dict[str, Any]],
    current_mapping: Dict[str, Optional[str]],
    rust_defs: Dict[str, str],
    depth: int = 1,

) -> Tuple[List[str], str]:
    if not symbols:
        return [], ""

    try:
        analyzer = get_analyzer()
    except Exception:
        return [], ""

    context_blocks: List[str] = []
    seen_pairs: set[Tuple[str, str]] = set()
    seen_dep_keys: set[str] = set()

    for symbol in symbols:
        name = symbol.get("name") or symbol.get("symbol") or symbol.get("id")
        sym_type = normalize_symbol_type(symbol.get("type"))
        file_path = symbol.get("file_path")
        if not (name and sym_type and file_path):
            continue

        try:
            refs = analyzer.find_symbols_by_name(name, symbol_type=sym_type, file_path=file_path)
        except Exception:
            continue
        if not refs:
            continue
        sym_ref = refs[0]

        try:
            func_nodes, _ = analyzer.get_dependencies(
                sym_ref,
                depth=depth,
                direction="out",
                symbol_types=FUNCTION_SYMBOL_TYPES,
            )
        except Exception:
            func_nodes = []

        try:
            non_func_nodes, _ = analyzer.get_dependencies(
                sym_ref,
                depth=None,
                direction="out",
                symbol_types=NON_FUNCTION_SYMBOL_TYPES,
            )
        except Exception:
            non_func_nodes = []

        nodes = func_nodes + non_func_nodes

        for dep in nodes:
            if dep.key() == sym_ref.key():
                continue
            if dep.key() in seen_dep_keys:
                continue
            seen_dep_keys.add(dep.key())
            c_name = dep.name
            rust_name = current_mapping.get(c_name)
            if not rust_name:
                continue
            rust_code = rust_defs.get(rust_name)
            if not rust_code:
                continue
            pair = (c_name, rust_name)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            context_blocks.append(f"// {c_name} -> {rust_name}\n{rust_code}\n")

    summary_text = ""
    try:
        summary_result = analyzer.get_batch_dependency_contexts(
            symbols,
            depth=depth,
            summary=True,
            max_size=10000,
        )
        if isinstance(summary_result, str):
            summary_text = summary_result
    except Exception:
        summary_text = ""

    return context_blocks, summary_text


def build_batch_prompt(
    batch,
    mapping_entries: Optional[List[str]] = None,
    dependency_entries: Optional[List[str]] = None,
    dependency_summary: Optional[str] = None,
):
    """构造单次调用包含整个 batch 的提示词。"""
    items = []
    for i, s in enumerate(batch["symbols"]):
        c_name = (
            s.get("name")
            or s.get("symbol")
            or s.get("id")
            or f"item_{i}"
        )
        content = _symbol_primary_text(s)
        items.append({
            "idx": i,
            "c_name": c_name,
            "content": content,
        })
    c_inputs = json.dumps(items, ensure_ascii=False, indent=2)
    instr = (
        "你是一名资深的 C -> Rust 转译器。请将下面列表中的每个 C 符号独立、安全地转为 Rust。\n"
        "要求：\n"
        "- 使用纯 Rust 安全惯用特性，不使用 unsafe 代码；\n"
        "- 用 mut 关键字声明可变变量；\n"
        "- 避免使用任何 `c_void`、`*mut`、`*const` 、`Box<dyn Any>`指针，任何ffi操作的类型；泛型用途的万能指针或结构体内部万能指针变量使用Rust的泛型<T>，智能指针，泛型结构体替代，确保内存安全和所有权管理\n"
        "- 评估并改进数据结构及所有权/借用模型；避免不必要的 clone/Box，可引入 Rc/RefCell/Weak(弱引用防止循环引用，管理父子关系) 等模式；\n"
        "- 如为类型/结构体/函数签名，给出 idiomatic 的 Rust 定义（尽量使用所有权/借用）；\n"
        "- 结构体所有成员使用pub关键字，所有函数，结构体，枚举，全局变量，全局类型定义声明成pub，允许外部访问，生成的所有的rust函数定义前面加pub关键字, 不要出现非pub的函数定义\n"
        "- 所有定义前加 pub；不得出现 impl/trait/class 等封装\n"
        "- 如果类型为函数声明，给出完整函数签名，包括参数和返回值类型；函数主体必须使用 unimplemented!() 占位；比如：pub fn foo() -> i32 {\n    unimplemented!()\n"
        "- 仅输出我指定的 JSON 结果，不要多余说明；\n"
        "- 不要使用任何面向对象的特性；如果 C 语言是全局函数，转换成的 Rust 也保持全局函数，不要使用 impl 封装；\n"
        "- 类型转换建议，请严格按照以下要求执行，以避免类型不匹配：\n"
        "  - int, char, unsigned int, unsigned char, float, double, enum, bool 等基本类型转换为 i32, i8, u32, u8, f32, f64、对应枚举或 bool；\n"
        "  - 对于 void * 等万能指针如果作为泛型用途，则使用泛型 T类型替代。\n"
        "  - C语言字符串或类型转换为 Rust 的 String；\n"
        "  - 一维动态数组优先转换为 Rust的切片操作；\n"
        "  - 不要用带有生命周期参数的泛型类型；\n"
        "  - 匿名结构体/联合体，转换为具名结构体/联合体；\n"
        "- 如果 C 宏可以直接使用标准库中的既有宏或函数，请优先复用（例如 assert 对应 Rust 的 assert! 宏）；\n"
    "输出对象必须包含键：items, mapping_c2r。\n"
    "- items: [{name, code, note}]\n"
        "- mapping_c2r: {c_name: rust_name | null}\n"
    "允许的处理方式仅限 translate(生成新Rust实现)、map(复用已有实现，映射到已经转换完成的Rust符号) 与 delete(删除无意义符号，比如头文件宏，无意义的宏定义，为null表示删除，注意：有数据的常量不要删除)。\n"
    "note 字段为字符串，简单明确指明上述哪一种处理并给出原因，无额外说明可留空；\n"
    "规则：安全 Rust；不要多余说明；items.name 必须与 mapping_c2r 的值一致；"
        f"输入 items（idx/c_name/content）：\n{c_inputs}"
    )

    if mapping_entries:
        mapping_text = "\n\n".join(mapping_entries)
        instr += (
            "\n\n以下为已知的 C→Rust 类型映射，请参考这些映射进行转译，"
            "如映射中的 Rust 表达与默认推断冲突，以映射为准：\n"
            f"{mapping_text}"
        )

    if dependency_entries:
        dependency_text = "\n\n".join(dependency_entries)
        instr += (
            "\n\n以下是已完成转译的相关依赖 Rust 定义，直接复用或作为约束，不要重复定义：\n"
            f"{dependency_text}"
        )

    if dependency_summary:
        instr += (
            "\n\n【依赖上下文摘要】\n"
            f"{dependency_summary}"
        )

    return instr


def _translate_symbols(
    chunk_batch: Dict[str, Any],
    dependency_entries: Optional[List[str]] = None,
    dependency_summary: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Optional[str]]]:
    """调用 LLM 转译一个子批次的符号集合。"""
    llm = LLM(logger=True)
    parser = TemplateParser("{batch:json:RustBatch}", model_map={"RustBatch": RustBatch})
    # mapping_entries = retrieve_type_mapping_context(chunk_batch)
    mapping_entries: Optional[List[str]] = None
    prompt = build_batch_prompt(chunk_batch, mapping_entries, dependency_entries, dependency_summary)
    result = llm.call(prompt, parser=parser, max_retry=5)
    if not isinstance(result, dict) or not result.get("success"):
        raise RuntimeError(f"LLM 解析失败: {result}")
    data = result["data"]["batch"]
    return data["items"], data.get("mapping_c2r", {})


def _log_chunk_output(
    batch: Dict[str, Any],
    chunk_index: int,
    items: List[Dict[str, Any]],
    mapping_c2r: Dict[str, Optional[str]],
) -> None:
    batch_id = batch.get("batch_id", "?")
    item_names = [item.get("name") for item in items if isinstance(item, dict)]
    names_str = ", ".join(name for name in item_names if isinstance(name, str) and name.strip()) or "无"
    mapping_total = len(mapping_c2r or {})
    print(f"[batch {batch_id} chunk {chunk_index}] items: {names_str}; mappings: {mapping_total}")
    pretty = json.dumps({"items": items, "mapping_c2r": mapping_c2r}, ensure_ascii=False, indent=2)
    print(pretty)


def _chunk_symbols_by_chars(symbols: List[Dict[str, Any]], max_chars: int) -> List[List[Dict[str, Any]]]:
    """根据字符总数将符号拆分为多个块。"""
    if not symbols:
        return []

    chunks: List[List[Dict[str, Any]]] = []
    current_chunk: List[Dict[str, Any]] = []
    current_chars = 0

    for symbol in symbols:
        content = _symbol_primary_text(symbol)
        symbol_chars = len(content)

        if current_chunk and current_chars + symbol_chars > max_chars:
            chunks.append(current_chunk)
            current_chunk = []
            current_chars = 0

        current_chunk.append(symbol)
        current_chars += symbol_chars

        if symbol_chars >= max_chars and len(current_chunk) == 1:
            chunks.append(current_chunk)
            current_chunk = []
            current_chars = 0

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def translate_batch(
    batch: Dict[str, Any],
    known_mapping: Optional[Dict[str, Optional[str]]] = None,
    known_rust_defs: Optional[Dict[str, str]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Optional[str]]]:
    """对一个 batch 内的所有符号进行转译，按字符阈值拆分处理。"""
    symbols = list(batch.get("symbols", []))
    if not symbols:
        return [], {}

    base_mapping = dict(known_mapping or {})
    base_rust_defs = dict(known_rust_defs or {})

    # 过滤
    pending_symbols: List[Dict[str, Any]] = []
    skipped = 0
    for symbol in symbols:
        c_name = (
            symbol.get("name")
            or symbol.get("symbol")
            or symbol.get("id")
        )
        if symbol.get("type") == "functions" and symbol.get("full_definition") == "":
            skipped += 1
            continue
        pending_symbols.append(symbol)

    if not pending_symbols:
        if skipped:
            print(f"[translate_batch] skipped {skipped} symbols already mapped; nothing to do.")
        return [], {}

    if skipped:
        print(f"[translate_batch] skipped {skipped} symbols already present in mapping.")

    pending_symbols, auto_added = _expand_symbols_with_missing_dependencies(pending_symbols, base_mapping)
    if auto_added:
        print(f"[translate_batch] automatically appended {auto_added} dependency symbol(s) to current batch.")
    batch["symbols"] = pending_symbols

    # pending_symbols = symbols
    pending_symbols_names = [
        s.get("name") or s.get("symbol") or s.get("id") or f"item_{i}"
        for i, s in enumerate(pending_symbols)
    ]

    print(f"-------------- [translate_batch] translating symbols {pending_symbols_names}...")

    chunks = _chunk_symbols_by_chars(pending_symbols, MAX_CHARS_PER_TRANSLATION)
    if len(chunks) <= 1:
        sub_batch = dict(batch)
        sub_batch["symbols"] = pending_symbols
        dependency_entries, dependency_summary = gather_dependency_context(pending_symbols, base_mapping, base_rust_defs)
        items, mapping_c2r = _translate_symbols(sub_batch, dependency_entries, dependency_summary)
        _log_chunk_output(batch, 1, items, mapping_c2r)
        return items, mapping_c2r

    aggregated_items: List[Dict[str, Any]] = []
    aggregated_mapping: Dict[str, Optional[str]] = {}

    current_mapping = dict(base_mapping)
    current_rust_defs = dict(base_rust_defs)

    for chunk_index, chunk in enumerate(chunks, start=1):
        sub_batch = dict(batch)
        sub_batch["symbols"] = chunk
        dependency_entries, dependency_summary = gather_dependency_context(chunk, current_mapping, current_rust_defs)
        items, mapping_c2r = _translate_symbols(sub_batch, dependency_entries, dependency_summary)
        _log_chunk_output(batch, chunk_index, items, mapping_c2r)
        aggregated_items.extend(items)
        aggregated_mapping.update(mapping_c2r)

        # 更新已知映射和 Rust 定义，供后续 chunk 使用
        for c_name, rust_name in mapping_c2r.items():
            current_mapping[c_name] = rust_name
        for item in items:
            rust_name = item.get("name")
            rust_code = item.get("code")
            if isinstance(rust_name, str) and isinstance(rust_code, str):
                current_rust_defs[rust_name] = rust_code

    return aggregated_items, aggregated_mapping


def _translation_node(state: BatchState) -> BatchState:
    remaining = state.get("remaining_batches", [])
    if not remaining:
        return state

    batch = remaining[0]
    rest = remaining[1:]
    try:
        translated_symbols = set(state.get("translated_symbols", []))

        original_symbols = list(batch.get("symbols", []))
        filtered_symbols: List[Dict[str, Any]] = []
        for symbol in original_symbols:
            key = _symbol_unique_key(symbol)
            if key and key in translated_symbols:
                continue
            filtered_symbols.append(symbol)

        if not filtered_symbols:
            history = list(state.get("history", []))
            history.append(
                {
                    "batch_id": batch.get("batch_id"),
                    "items": [],
                    "mapping_c2r": {},
                    "note": "skipped (all symbols already translated)",
                }
            )
            return {
                "remaining_batches": rest,
                "items": list(state.get("items", [])),
                "mapping_c2r": dict(state.get("mapping_c2r", {})),
                "history": history,
                "translated_symbols": sorted(translated_symbols),
            }

        working_batch = dict(batch)
        working_batch["symbols"] = filtered_symbols

        existing_mapping = dict(state.get("mapping_c2r", {}))
        existing_items = state.get("items", []) or []
        rust_defs = {
            item.get("name"): item.get("code")
            for item in existing_items
            if isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("code"), str)
        }

        items, mapping_c2r = translate_batch(working_batch, existing_mapping, rust_defs)

        aggregated_mapping = dict(state.get("mapping_c2r", {}))
        aggregated_mapping.update(mapping_c2r)

        compile_success = False
        written_paths = _persist_batch_to_rust(working_batch, items, mapping_c2r, aggregated_mapping)
        for attempt_index in range(COMPILE_MAX_RETRIES):
            attempt_snapshots = _snapshot_rust_files(written_paths)
            compile_success = _run_swe_agent_compile(written_paths)
            if compile_success:
                break
            _restore_rust_files(attempt_snapshots)
            print("------------------编译未通过，重试中...")
        if not compile_success:
            raise RuntimeError(f"SWE Agent 无法修复编译错误，批次 {batch.get('batch_id')} 失败。")

        aggregated_items = list(state.get("items", []))
        aggregated_items.extend(items)

        history = list(state.get("history", []))

        history.append(
            {
                "batch_id": batch.get("batch_id"),
                "items": items,
                "mapping_c2r": mapping_c2r,
            }
        )

        processed_keys = {
            key
            for key in (
                _symbol_unique_key(symbol)
                for symbol in working_batch.get("symbols", [])
            )
            if key
        }
        translated_symbols.update(processed_keys)

        _persist_mapping_c2r(aggregated_mapping)

        return {
            "remaining_batches": rest,
            "items": aggregated_items,
            "mapping_c2r": aggregated_mapping,
            "history": history,
            "translated_symbols": sorted(translated_symbols),
        }
    except Exception as exc:  # pragma: no cover - 透传异常给上层处理
        return {"error": str(exc)}


def _build_translation_app() -> StateGraph:
    graph = StateGraph(BatchState)
    graph.add_node("translate", _translation_node)
    graph.set_entry_point("translate")
    def _should_continue(state: BatchState) -> str:
        if state.get("error"):
            return "stop"
        if state.get("remaining_batches"):
            return "more"
        return "done"

    graph.add_conditional_edges(
        "translate",
        _should_continue,
        {
            "more": "translate",
            "done": END,
            "stop": END,
        },
    )
    return graph.compile()


TRANSLATION_APP = _build_translation_app()



def main():
    
    cmd = ["python", "clear_rs.py"]
    subprocess.run(cmd, check=True)

    global _C_TO_RUST_MAP, _DEST_FILE_SYMBOLS
    _C_TO_RUST_MAP = None
    _DEST_FILE_SYMBOLS = {}
    _close_swe_agent_instance()

    build_csv_mapping_collection(
        TYPE_MAPPING_CSV,
        key_fields=TYPE_MAPPING_KEY_FIELDS,
        collection_name=TYPE_MAPPING_COLLECTION,
    )

    with open("analyzer/output/file_batches.json", "r", encoding="utf-8") as f:
        batches_payload = json.load(f)

    batch_list = batches_payload.get("batches", [])
    initial_state: BatchState = {
        "remaining_batches": batch_list,
        "items": [],
        "mapping_c2r": {},
        "history": [],
        "translated_symbols": [],
    }

    result_state = TRANSLATION_APP.invoke(initial_state, config={"recursion_limit": 100})

    if "error" in result_state:
        error_message = result_state["error"]
        print(f"批处理失败: {error_message}")
        raise RuntimeError(error_message)

    history = result_state.get("history", [])
    mapping_c2r = result_state.get("mapping_c2r", {})

    for entry in history:
        batch_id = entry.get("batch_id")
        print(f"Batch {batch_id}:")

        print("// 映射表：C -> Rust")
        for c_name, rust_name in entry.get("mapping_c2r", {}).items():
            print(f"// {c_name} -> {rust_name}")

        for item in entry.get("items", []):
            print(f"// {item['name']}\n{item['code']}\n")

    print("// 汇总映射表：C -> Rust")
    for c_name, rust_name in mapping_c2r.items():
        print(f"// {c_name} -> {rust_name}")

    _persist_mapping_c2r(mapping_c2r)

    _close_swe_agent_instance()


if __name__ == "__main__":
    main()