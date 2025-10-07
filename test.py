import atexit
import json
import os
import shlex
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple, TypedDict

from langgraph.graph import END, StateGraph  # type: ignore
from pydantic import BaseModel, Field
from pydantic import ConfigDict  # type: ignore
from llm.template_parser.template_parser import TemplateParser
from llm.llm import LLM
from llm.rag import build_csv_mapping_collection, search_knowledge_base
from analyzer.analyzer import Analyzer
from analyzer.config import get_project_root, load_rust_output_dir


class RustItem(BaseModel):
    """单个 Rust 元素（name + 完整源码）。"""

    # 生成的 Rust 元素名称（例如类型/结构体/函数/常量名）
    name: str = Field(..., description="Rust 元素名（类型/结构体/函数/常量等）")
    # 该元素的完整 Rust 源码
    code: str = Field(..., description="该元素的完整 Rust 源码")

    # 在 Pydantic v2 中为 JSON Schema 添加模型级描述
    try:
        model_config = ConfigDict(json_schema_extra={
            "description": "RustItem：单个 Rust 元素，包含名称与完整源码。"
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


TYPE_MAPPING_CSV = "c_to_rust_type_mapping.csv"
TYPE_MAPPING_COLLECTION = "c_to_rust_type_mapping"
TYPE_MAPPING_KEY_FIELDS = ["Type", "C 类型", "C 示例"]
TYPE_MAPPING_TOP_K = 6
TYPE_MAPPING_RERANK_TOP_N = 3
MAX_CHARS_PER_TRANSLATION = 1000

FUNCTION_SYMBOL_TYPES: Set[str] = {"functions"}
NON_FUNCTION_SYMBOL_TYPES: Set[str] = {"structs", "typedefs", "macros", "variables", "enums"}

_ANALYZER: Optional[Analyzer] = None
_PROJECT_ROOT: Optional[Path] = None
_RUST_SRC_ROOT: Optional[Path] = None
_C_TO_RUST_MAP: Optional[Dict[str, Path]] = None
_DEST_FILE_SYMBOLS: Dict[Path, OrderedDict[str, str]] = {}
_SWE_AGENT_INSTANCE: Optional["SWEAgent"] = None


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
        max_iterations=20,
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


def _run_swe_agent_compile(dest_paths: Set[Path]) -> None:
    if not dest_paths:
        return

    agent = _get_swe_agent_instance()
    if agent is None:
        return

    try:
        rust_output_dir = load_rust_output_dir()
    except Exception as exc:
        print(f"无法定位 Rust 输出目录，跳过编译：{exc}")
        return

    cargo_toml = rust_output_dir / "Cargo.toml"
    if not cargo_toml.exists():
        print(f"未找到 Cargo.toml: {cargo_toml}")
        return

    compile_cmd_parts = ["RUSTFLAGS=-Awarnings", "cargo", "check", "--manifest-path", str(cargo_toml)]
    compile_cmd = " ".join(shlex.quote(part) for part in compile_cmd_parts)

    try:
        result = agent.toolset.run_command(compile_cmd)
    except Exception as exc:
        print(f"SWE Agent 执行编译命令失败: {exc}")
        return

    if (result or {}).get("returncode", 0) == 0:
        rel_list = _format_relative_paths(dest_paths)
        print(f"SWE Agent 编译通过: {compile_cmd} -> {', '.join(rel_list)}")
        return

    error_output = f"{result.get('stderr', '').strip()}\n{result.get('stdout', '').strip()}".strip()
    if not error_output:
        error_output = "编译失败但没有提供错误输出。"

    error_lines = error_output.splitlines()
    truncated_error = "\n".join(error_lines[:200])

    rel_paths = _format_relative_paths(dest_paths)
    task_description = (
        "自动转译后的 Rust 文件编译失败，请修复所有编译错误并确保 cargo check 通过。\n"
        f"涉及文件：{', '.join(rel_paths)}\n"
        f"编译命令使用run_command工具：{compile_cmd}\n"
        "错误输出：\n"
        f"{truncated_error}"
    )

    try:
        agent.run_task(
            task_description,
            acceptance_criteria=[
                "cargo check 成功", "保留已有功能", "仅修改必要文件"
            ]
        )
    except Exception as exc:
        print(f"SWE Agent 尝试修复编译错误失败: {exc}")
        return

    try:
        rerun = agent.toolset.run_command(compile_cmd)
    except Exception as exc:
        print(f"SWE Agent 复验编译命令失败: {exc}")
        return

    if (rerun or {}).get("returncode", 0) == 0:
        rel_list = _format_relative_paths(dest_paths)
        print(f"SWE Agent 修复后编译通过: {', '.join(rel_list)}")
    else:
        print("SWE Agent 修复后仍未通过编译，请手动检查。")
        raise RuntimeError("SWE Agent 修复后仍未通过编译，请手动检查。")


def _persist_batch_to_rust(batch: Dict[str, Any], items: List[Dict[str, Any]], mapping_c2r: Dict[str, Optional[str]]) -> Set[Path]:
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

    batch_files_raw = batch.get("files", [])
    fallback_files: List[Path] = []
    if isinstance(batch_files_raw, list):
        for file_entry in batch_files_raw:
            rel = _resolve_relative_c_path(str(file_entry))
            if rel is not None:
                fallback_files.append(rel)

    fallback_destinations: Set[Path] = set()
    for rel_path in fallback_files:
        target_rel = _map_c_path_to_rust_relative(rel_path)
        if target_rel is not None:
            fallback_destinations.add(target_rel)

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
            dest_path = src_root / target_rel
            cleaned_code = code.strip()
            if not cleaned_code:
                continue
            dest_segments.setdefault(dest_path, {})[rust_name] = cleaned_code

    if not dest_segments:
        return set()

    written_paths: Set[Path] = set()

    for dest_path, segments in dest_segments.items():
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            symbol_map = _DEST_FILE_SYMBOLS.setdefault(dest_path, OrderedDict())

            updated = False
            for rust_name, cleaned_code in segments.items():
                existing_code = symbol_map.get(rust_name)
                if existing_code == cleaned_code:
                    continue
                symbol_map[rust_name] = cleaned_code
                updated = True

            if not symbol_map or not updated:
                continue

            content_pieces = [segment.rstrip() for segment in symbol_map.values() if segment.strip()]
            if not content_pieces:
                continue

            final_text = "\n\n".join(content_pieces).rstrip() + "\n"
            dest_path.write_text(final_text, encoding="utf-8")
            written_paths.add(dest_path)
        except Exception as exc:
            print(f"写入 Rust 文件失败: {dest_path}: {exc}")
    return written_paths


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
        content = symbol.get("content", "")
        if not isinstance(content, str) or not content.strip():
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


def gather_dependency_context(
    symbols: List[Dict[str, Any]],
    current_mapping: Dict[str, Optional[str]],
    rust_defs: Dict[str, str],
    depth: int = 1,
) -> List[str]:
    if not symbols or not current_mapping or not rust_defs:
        return []

    try:
        analyzer = get_analyzer()
    except Exception:
        return []

    context_blocks: List[str] = []
    seen_pairs: set[Tuple[str, str]] = set()
    seen_dep_keys: set[str] = set()

    for symbol in symbols:
        name = symbol.get("name") or symbol.get("symbol") or symbol.get("id")
        sym_type = symbol.get("type")
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

    return context_blocks


def build_batch_prompt(
    batch,
    mapping_entries: Optional[List[str]] = None,
    dependency_entries: Optional[List[str]] = None,
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
        items.append({
            "idx": i,
            "c_name": c_name,
            "content": s["content"],
        })
    c_inputs = json.dumps(items, ensure_ascii=False, indent=2)
    instr = (
        "你是一名资深的 C -> Rust 转译器。请将下面列表中的每个 C 符号独立、安全地转为 Rust。\n"
        "要求：\n"
        "- 使用纯 Rust 特性，不使用 unsafe 代码；\n"
        "- 用 mut 关键字声明可变变量；\n"
        "- 不使用任何 `c_void`、`*mut`、`*const` 指针，任何类似CString这种ffi操作的类型；\n"
        "- 返回最优结果，不做解释；\n"
        "- 避免使用 Box<dyn Any>；\n"
        "- 如为宏/常量，优先转为 const/静态或等价的安全形式；\n"
        "- 如为类型/结构体/函数签名，给出 idiomatic 的 Rust 定义（尽量使用所有权/借用）；\n"
        "- 如果类型为函数声明，给出完整函数签名，包括参数和返回值类型；函数主体使用 unimplemented!() 占位；\n"
        "- 仅输出我指定的 JSON 结果，不要多余说明；\n"
        "- 不要使用任何面向对象的特性；如果 C 语言是全局函数，转换成的 Rust 也保持全局函数，不要使用 impl 封装；\n"
        "- 类型转换建议，请严格按照以下要求执行，以避免类型不匹配：\n"
        "  - int, char, unsigned int, unsigned char, float, double, enum, bool 等基本类型转换为 i32, i8, u32, u8, f32, f64、对应枚举或 bool；\n"
        "  - char* 字符串或 void* 字符串类型转换为 Rust 的 String；\n"
        "  - 一维动态数组优先转换为 Rust的切片操作；\n"
        "  - 忽略任何typedef 或者没有定义的结构体，将其转换为空\n"
        "输出对象必须包含键：items, mapping_c2r。\n"
        "- items: [{name, code}]\n"
        "- mapping_c2r: {c_name: rust_name | null}\n"
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

    return instr


def _translate_symbols(
    chunk_batch: Dict[str, Any],
    dependency_entries: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Optional[str]]]:
    """调用 LLM 转译一个子批次的符号集合。"""
    llm = LLM(logger=True)
    parser = TemplateParser("{batch:json:RustBatch}", model_map={"RustBatch": RustBatch})
    # mapping_entries = retrieve_type_mapping_context(chunk_batch)
    mapping_entries: Optional[List[str]] = None
    prompt = build_batch_prompt(chunk_batch, mapping_entries, dependency_entries)
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
        content = symbol.get("content", "")
        if not isinstance(content, str):
            content = str(content)
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

    chunks = _chunk_symbols_by_chars(symbols, MAX_CHARS_PER_TRANSLATION)
    if len(chunks) <= 1:
        dependency_entries = gather_dependency_context(symbols, base_mapping, base_rust_defs)
        items, mapping_c2r = _translate_symbols(batch, dependency_entries)
        _log_chunk_output(batch, 1, items, mapping_c2r)
        return items, mapping_c2r

    aggregated_items: List[Dict[str, Any]] = []
    aggregated_mapping: Dict[str, Optional[str]] = {}

    current_mapping = dict(base_mapping)
    current_rust_defs = dict(base_rust_defs)

    for chunk_index, chunk in enumerate(chunks, start=1):
        sub_batch = dict(batch)
        sub_batch["symbols"] = chunk
        dependency_entries = gather_dependency_context(chunk, current_mapping, current_rust_defs)
        items, mapping_c2r = _translate_symbols(sub_batch, dependency_entries)
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
        existing_mapping = dict(state.get("mapping_c2r", {}))
        existing_items = state.get("items", []) or []
        rust_defs = {
            item.get("name"): item.get("code")
            for item in existing_items
            if isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("code"), str)
        }

        items, mapping_c2r = translate_batch(batch, existing_mapping, rust_defs)
        written_paths = _persist_batch_to_rust(batch, items, mapping_c2r)
        _run_swe_agent_compile(written_paths)

        aggregated_items = list(state.get("items", []))
        aggregated_items.extend(items)

        aggregated_mapping = dict(state.get("mapping_c2r", {}))
        aggregated_mapping.update(mapping_c2r)

        history = list(state.get("history", []))

        history.append(
            {
                "batch_id": batch.get("batch_id"),
                "items": items,
                "mapping_c2r": mapping_c2r,
            }
        )

        return {
            "remaining_batches": rest,
            "items": aggregated_items,
            "mapping_c2r": aggregated_mapping,
            "history": history,
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


if __name__ == "__main__":
    main()