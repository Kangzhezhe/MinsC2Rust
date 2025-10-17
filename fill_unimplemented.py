import difflib
import json
import os
import re
import subprocess
import tempfile
import textwrap
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field
try:  # Pydantic v2
    from pydantic import RootModel
except ImportError:  # Pydantic v1 fallback
    RootModel = None  # type: ignore

from analyzer.symbol_model import normalize_symbol_type
from llm.llm import LLM
from llm.template_parser.template_parser import TemplateParser
from collections import deque

from analyzer.config import load_rust_output_dir

from test import (
    FUNCTION_SYMBOL_TYPES,
    NON_FUNCTION_SYMBOL_TYPES,
    RustBatch,
    _format_relative_paths,
    _get_swe_agent_instance,
    _map_c_path_to_rust_relative,
    _normalize_c_key,
    _resolve_relative_c_path,
    get_analyzer,
)

FILL_PROMPT_TEMPLATE = (
    "你是一名资深的 C -> Rust 转译器。请将下面列表中的每个 C 函数体定义精准、安全地实现为 Rust 函数体。\n"
    "要求：\n"
    "- 保留原有函数声明/签名完全不变（包括 pub、extern、参数、返回类型、属性等），只实现函数体；\n"
    "- 输出目标函数的完整 Rust 定义文本，从函数签名起首行开始，直到函数体闭合的右大括号与换行结束。\n"
    "- 使用纯 Rust 安全惯用特性，不要使用 unsafe；\n"
    "- 函数体内不得保留 unimplemented!()，需要写出完整逻辑；\n"
    "- 仅修改函数体，不新增或删除任何函数、结构体、宏定义，也不调整可见性；\n"
    "- 尽量沿用现有标准库或已有依赖定义，实现与原 C 语义一致的行为；\n"
    "- 如果 C 宏可以用标准库宏/函数，优先复用（如 assert -> assert!）；\n"
    "- 不要添加 impl、trait 等面向对象封装；\n"
    "- 对于函数指针字段始终用 (hash_table.hash_func)(...)、(hash_table.equal_func)(...) 形式调用；\n"
    "- 如果决定使用 clone 方案，为那些需要复制的自定义结构派生 Clone 特征；或实现 Copy 特征。\n"
    "- 对于迭代器设计，推荐不直接持有 owned Box 的克隆，而是使用索引或引用的方式来避免大量克隆/复杂的借用问题；\n"
    "- 输出 JSON，对象包含 items, mapping_c2r；\n"
    "- items: [{{name, code, note}}]，mapping_c2r: {{c_name: rust_name | null}};\n"
    "- note 简要说明 translate/map/delete 的原因，可留空；\n"
    "- items.name 必须与 mapping_c2r 的值一致；\n"
    "输入 items（idx/c_name/content）：\n{items_json}"
)

FUNCTION_STUB_PATTERN = "unimplemented!()"

RUST_AST_PROJECT_DIR = Path(__file__).resolve().parent / "rust_ast_project"
_LLM_FIX_PAYLOAD_HISTORY: Set[str] = set()


class FixTargetsModel(BaseModel):
    files: Dict[str, List[str]] = Field(default_factory=dict)


if RootModel is not None:

    class FixResultModel(RootModel[Dict[str, Dict[str, Any]]]):  # type: ignore[type-arg]
        def to_dict(self) -> Dict[str, Dict[str, Any]]:
            return self.root

    class FixResultListModel(RootModel[List[Dict[str, Dict[str, Any]]]]):  # type: ignore[type-arg]
        def to_list(self) -> List[Dict[str, Dict[str, Any]]]:
            return self.root


else:

    class FixResultModel(BaseModel):
        __root__: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

        def to_dict(self) -> Dict[str, Dict[str, Any]]:
            return self.__root__

    class FixResultListModel(BaseModel):
        __root__: List[Dict[str, Dict[str, Any]]] = Field(default_factory=list)

        def to_list(self) -> List[Dict[str, Dict[str, Any]]]:
            return list(self.__root__)


class CandidateEvaluationModel(BaseModel):
    score: float = 0.0
    reason: str = ""


class Memory:
    def __init__(self, max_size=3, memory_type="Reflection"):
        self.mem = deque(maxlen=max_size)  # 限制记忆长度
        self.memory_type = memory_type
    
    def add(self, item):
        self.mem.append(item)
    
    def get_context(self):
        return "\n".join([f"# {self.memory_type} {i+1}: {r}" for i, r in enumerate(self.mem)])
    
    def clear(self):
        self.mem.clear()

    def get_latest(self, n=1):
        latest_items = list(self.mem)[-n:] if self.mem else []
        return "\n".join([f"# {self.memory_type} {len(self.mem) - len(latest_items) + i + 1}: {r}" for i, r in enumerate(latest_items)])



TRAJECTORY_MEMORY = Memory(max_size=5, memory_type="历史改错")


def gather_dependency_context_from_project(
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
            # rust_code = rust_defs.get(rust_name)
            rust_code = _run_rust_symbol_extractor(load_rust_output_dir(), rust_name)
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
            max_size=5000,
        )
        if isinstance(summary_result, str):
            summary_text = summary_result
    except Exception:
        summary_text = ""

    return context_blocks, summary_text


def _collect_dependency_locations_for_symbol(
    symbol: Dict[str, Any],
    current_mapping: Dict[str, Optional[str]],
) -> List[str]:
    locations: List[str] = []
    try:
        analyzer = get_analyzer()
    except Exception:
        return locations

    name = symbol.get("name") or symbol.get("symbol") or symbol.get("id")
    sym_type = normalize_symbol_type(symbol.get("type"))
    file_path = symbol.get("file_path")
    if not (name and sym_type and file_path):
        return locations

    try:
        refs = analyzer.find_symbols_by_name(name, symbol_type=sym_type, file_path=file_path)
    except Exception:
        refs = []
    if not refs:
        return locations
    sym_ref = refs[0]

    try:
        func_nodes, _ = analyzer.get_dependencies(
            sym_ref,
            depth=1,
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

    try:
        project_root = load_rust_output_dir()
    except Exception:
        project_root = None

    if not project_root:
        return locations

    seen: Set[str] = set()

    for dep in func_nodes + non_func_nodes:
        c_name = dep.name
        rust_name = current_mapping.get(c_name)
        if not rust_name:
            continue
        try:
            matches = _run_rust_symbol_extractor(project_root, rust_name)
        except Exception:
            matches = []

        if not matches:
            entry = f"{rust_name} -> (未找到源码位置)"
            if entry not in seen:
                seen.add(entry)
                locations.append(entry)
            continue

        for match in matches:
            file_rel = match.get("file")
            start_line = match.get("start_line")
            end_line = match.get("end_line")
            if isinstance(file_rel, str) and isinstance(start_line, int) and isinstance(end_line, int):
                entry = f"{rust_name} -> {file_rel}:{start_line}-{end_line}"
            elif isinstance(file_rel, str):
                entry = f"{rust_name} -> {file_rel}"
            else:
                entry = rust_name
            if entry not in seen:
                seen.add(entry)
                locations.append(entry)

    return locations

def _build_fill_prompt(
    symbols: List[Dict[str, Any]],
    dependency_entries: Optional[List[str]],
    dependency_summary: Optional[str],
    rust_placeholders: Optional[List[str]] = None,
) -> str:
    payload = []
    for idx, sym in enumerate(symbols):
        c_name = sym.get("name") or sym.get("symbol") or sym.get("id") or f"item_{idx}"
        content = sym.get("full_definition","")
        if content is None:
            continue
        payload.append({
            "idx": idx,
            "c_name": c_name,
            "content": content,
        })
    base_prompt = FILL_PROMPT_TEMPLATE.format(items_json=json.dumps(payload, ensure_ascii=False, indent=2))

    if dependency_entries:
        base_prompt += (
            "\n\n以下是已完成转译的相关依赖 Rust 定义，请直接复用或保持兼容，不要重复声明：\n"
            + "\n\n".join(dependency_entries)
        )

    if dependency_summary:
        base_prompt += "\n\n【依赖摘要】\n" + dependency_summary

    if rust_placeholders:
        base_prompt += (
            "\n\n以下是当前 Rust 工程中的占位定义，请保留签名并实现函数体：\n"
            + "\n\n".join(rust_placeholders)
        )

    return base_prompt


def _run_rust_symbol_extractor(project_root: Path, symbol: str) -> List[Dict[str, Any]]:

    if not RUST_AST_PROJECT_DIR.exists():
        raise RuntimeError(f"Rust AST 项目不存在: {RUST_AST_PROJECT_DIR}")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        cmd = [
            "cargo",
            "run",
            "--quiet",
            "--",
            str(project_root),
            symbol,
            str(tmp_path),
        ]
        subprocess.run(cmd, cwd=RUST_AST_PROJECT_DIR, check=True)
        with tmp_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"提取 Rust 符号 {symbol} 失败: {exc}") from exc
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    matches = payload.get("matches", []) if isinstance(payload, dict) else []
    return matches

def _format_placeholder_entry(match: Dict[str, Any]) -> str:
    file = match.get("file", "未知文件")
    start = match.get("start_line")
    end = match.get("end_line")
    code = match.get("code", "")
    location = f"{file}:{start}-{end}" if isinstance(start, int) and isinstance(end, int) else file
    return f"- {location}\n```rust\n{code.strip()}\n```"


def _run_cargo_check_once() -> Tuple[bool, str]:
    try:
        rust_output_dir = load_rust_output_dir()
    except Exception as exc:
        return False, f"无法定位 Rust 输出目录：{exc}"

    if rust_output_dir is None:
        return False, "Rust 输出目录未配置。"

    cargo_toml = rust_output_dir / "Cargo.toml"
    if not cargo_toml.exists():
        return False, f"未找到 Cargo.toml: {cargo_toml}"

    env = os.environ.copy()
    rustflags = env.get("RUSTFLAGS", "").strip()
    extra_flag = "-Awarnings"
    if rustflags:
        if extra_flag not in rustflags.split():
            rustflags = f"{rustflags} {extra_flag}".strip()
    else:
        rustflags = extra_flag
    env["RUSTFLAGS"] = rustflags

    cmd = [
        "cargo",
        "check",
        "--manifest-path",
        str(cargo_toml),
    ]

    proc = subprocess.run(
        cmd,
        cwd=rust_output_dir,
        capture_output=True,
        text=True,
        env=env,
    )

    succeeded = proc.returncode == 0
    output_parts = [part.strip() for part in (proc.stdout, proc.stderr) if part]
    output = "\n".join(part for part in output_parts if part)
    return succeeded, output


def _truncate_text(text: str, limit: int = 6000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...（内容已截断）"


def _normalize_compile_output_signature(output: str) -> str:
    if not output:
        return ""
    normalized_lines: List[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        normalized_lines.append(stripped)
    return "\n".join(normalized_lines)


def _summarize_candidate_changes(candidate: Dict[str, Dict[str, Any]]) -> str:
    entries: List[str] = []
    for file_rel, payload in candidate.items():
        if not isinstance(file_rel, str) or not isinstance(payload, dict):
            continue
        symbols = [name for name in payload.keys() if isinstance(name, str) and name != "extra"]
        notes: List[str] = []
        if symbols:
            notes.append("符号: " + ", ".join(symbols))
        extra = payload.get("extra")
        if isinstance(extra, list) and extra:
            notes.append("调整导入")
        entry = file_rel
        if notes:
            entry += " (" + "; ".join(notes) + ")"
        entries.append(entry)
    return "; ".join(entries) if entries else "无显著变更"


def _generate_candidate_diff_summary(
    original_payload: Dict[str, Dict[str, Any]],
    candidate_payload: Dict[str, Dict[str, Any]],
    metadata: Dict[str, Dict[str, Any]],
    max_chars: int = 1800,
) -> str:
    diff_sections: List[str] = []
    for file_rel, file_changes in candidate_payload.items():
        if not isinstance(file_rel, str) or not isinstance(file_changes, dict):
            continue

        orig_entries = original_payload.get(file_rel, {})
        if not isinstance(orig_entries, dict):
            orig_entries = {}

        meta_entry = metadata.get(file_rel, {})
        symbol_snippets = {}
        if isinstance(meta_entry, dict):
            symbol_snippets = meta_entry.get("symbol_snippets", {}) or {}
            if not isinstance(symbol_snippets, dict):
                symbol_snippets = {}

        for symbol, new_code in file_changes.items():
            if symbol == "extra":
                continue
            if not isinstance(symbol, str) or not isinstance(new_code, str):
                continue

            old_code = ""
            old_value = orig_entries.get(symbol)
            if isinstance(old_value, str):
                old_code = old_value
            elif isinstance(symbol_snippets, dict):
                fallback = symbol_snippets.get(symbol)
                if isinstance(fallback, str):
                    old_code = fallback

            if old_code == new_code:
                continue

            diff_iter = difflib.unified_diff(
                old_code.splitlines(),
                new_code.splitlines(),
                fromfile=f"{file_rel}:{symbol}:before",
                tofile=f"{file_rel}:{symbol}:after",
                lineterm="",
            )
            diff_text = "\n".join(diff_iter).strip()
            if diff_text:
                diff_sections.append(diff_text)

        extra_value = file_changes.get("extra")
        if isinstance(extra_value, list):
            orig_extra_raw = orig_entries.get("extra") if isinstance(orig_entries, dict) else None
            orig_extra_list = [item for item in orig_extra_raw if isinstance(item, str)] if isinstance(orig_extra_raw, list) else []
            new_extra_text = "\n".join(item for item in extra_value if isinstance(item, str))
            orig_extra_text = "\n".join(orig_extra_list)
            if new_extra_text != orig_extra_text:
                diff_iter = difflib.unified_diff(
                    orig_extra_text.splitlines(),
                    new_extra_text.splitlines(),
                    fromfile=f"{file_rel}:extra:before",
                    tofile=f"{file_rel}:extra:after",
                    lineterm="",
                )
                diff_text = "\n".join(diff_iter).strip()
                if diff_text:
                    diff_sections.append(diff_text)

    if not diff_sections:
        return ""

    combined = "\n\n".join(diff_sections)
    return _truncate_text(combined, max_chars)


def _format_symbol_diff_for_history(
    file_rel: str,
    symbol: str,
    old_code: str,
    new_code: str,
    max_lines: int = 40,
) -> Optional[str]:
    if old_code == new_code:
        return None

    diff_lines: List[str] = []
    for line in difflib.ndiff(old_code.splitlines(), new_code.splitlines()):
        if not line:
            continue
        if line[0] in {"+", "-"}:
            diff_lines.append(line[:1] + " " + line[2:])
        elif line.startswith("? "):
            continue
    if not diff_lines:
        return None

    if len(diff_lines) > max_lines:
        truncated = diff_lines[:max_lines]
        truncated.append("... (diff truncated)")
        diff_lines = truncated

    header = f"{file_rel}::{symbol}"
    body = "\n".join(diff_lines)
    return f"{header}\n{body}"


def _build_history_entry(
    attempt_no: int,
    original_payload: Dict[str, Dict[str, Any]],
    candidate_payload: Dict[str, Dict[str, Any]],
    metadata: Dict[str, Dict[str, Any]],
    compile_output: str,
    success: bool,
    baseline_compile_output: Optional[str] = None,
) -> str:
    change_summary = _summarize_candidate_changes(candidate_payload)
    diff_summary = _generate_candidate_diff_summary(original_payload, candidate_payload, metadata)
    status_text = "成功" if success else "失败"

    symbol_summaries: List[str] = []

    for file_rel, file_changes in candidate_payload.items():
        if not isinstance(file_rel, str) or not isinstance(file_changes, dict):
            continue

        orig_entries = original_payload.get(file_rel, {}) if isinstance(original_payload, dict) else {}
        if not isinstance(orig_entries, dict):
            orig_entries = {}

        meta_entry = metadata.get(file_rel, {}) if isinstance(metadata, dict) else {}
        symbol_snippets = meta_entry.get("symbol_snippets", {}) if isinstance(meta_entry, dict) else {}
        if not isinstance(symbol_snippets, dict):
            symbol_snippets = {}

        for symbol, new_code in file_changes.items():
            if symbol == "extra" or not isinstance(symbol, str) or not isinstance(new_code, str):
                continue
            old_code = ""
            old_value = orig_entries.get(symbol)
            if isinstance(old_value, str):
                old_code = old_value
            else:
                fallback = symbol_snippets.get(symbol)
                if isinstance(fallback, str):
                    old_code = fallback

            formatted = _format_symbol_diff_for_history(file_rel, symbol, old_code, new_code)
            if formatted:
                symbol_summaries.append(formatted)

        extra_value = file_changes.get("extra")
        if isinstance(extra_value, list):
            orig_extra_raw = orig_entries.get("extra") if isinstance(orig_entries, dict) else None
            orig_extra_list = [item for item in orig_extra_raw if isinstance(item, str)] if isinstance(orig_extra_raw, list) else []
            new_extra_text = "\n".join(item for item in extra_value if isinstance(item, str))
            orig_extra_text = "\n".join(orig_extra_list)
            formatted = _format_symbol_diff_for_history(file_rel, "导入语句", orig_extra_text, new_extra_text)
            if formatted:
                symbol_summaries.append(formatted)

    raw_history_context = None
    if symbol_summaries or diff_summary:
        diff_block = diff_summary or "\n\n".join(symbol_summaries)
        baseline_excerpt = _truncate_text((baseline_compile_output or "").strip(), 1000)
        current_excerpt = _truncate_text((compile_output or "").strip(), 1200)
        history_summary_prompt = textwrap.dedent(
            f"""
            你是一个代码诊断专家。请阅读改前编译报错、代码改动以及改后编译结果，生成两段简洁的总结：
            1. 修改摘要：说明针对哪些报错（引用改前日志关键信息）做了哪些代码改动，涉及的函数/导入及调整方向。
            2. 结果判读：若仍失败，请分析主要报错并说明与改前报错的差异；若已成功，请确认 cargo check 通过并概述与改前报错相比的改善。

            ### 改前编译错误
            {baseline_excerpt or '无'}

            ### 代码差异
            {diff_block}

            ### 改后编译输出
            {current_excerpt or '无'}

            输出格式示例：
            "修改摘要: ...\n失败原因: ..." 或 "修改摘要: ...\n结果: cargo check 已通过"。
            """
        ).strip()
        try:
            llm = LLM(logger=False)
            raw_history_context = llm.call(history_summary_prompt, parser=None, max_retry=2)
        except Exception:
            raw_history_context = None

    lines: List[str] = [
        f"尝试 {attempt_no}: {status_text}",
        f"改动摘要: {change_summary or '无'}",
    ]

    if raw_history_context:
        lines.append(str(raw_history_context).strip())
    else:
        if baseline_compile_output:
            baseline_trimmed = _truncate_text((baseline_compile_output or "").strip(), 1500)
            lines.append("改前编译错误摘要:\n" + (baseline_trimmed or "无输出"))

        if symbol_summaries:
            change_block = "\n\n".join(symbol_summaries)
            lines.append("本轮改动细节:\n" + _truncate_text(change_block, 1800))
        elif diff_summary:
            lines.append("代码差异:\n" + diff_summary)

        if success:
            lines.append("结果: cargo check 已通过")
            if compile_output:
                lines.append("改后编译输出:\n" + _truncate_text((compile_output or "").strip(), 600))
        else:
            trimmed_error = _truncate_text((compile_output or "").strip(), 1500)
            lines.append("改后编译错误摘要:\n" + (trimmed_error or "无输出"))

    return "\n".join(lines).strip()


def _evaluate_candidate_progress(
    llm: LLM,
    baseline_output: str,
    candidate_output: str,
    candidate_payload: Dict[str, Dict[str, Any]],
    history_context: str,
) -> Tuple[float, str]:
    if not baseline_output or not candidate_output:
        return 0.0, ""

    baseline_excerpt = _truncate_text(baseline_output, 4000)
    candidate_excerpt = _truncate_text(candidate_output, 4000)
    change_summary = _summarize_candidate_changes(candidate_payload)

    prompt = textwrap.dedent(
        f"""
        你是一名资深的 Rust 构建工程师。现在有两份 `cargo check` 编译错误日志：

        - 基准错误：
        {baseline_excerpt}

        - 候选错误：
        {candidate_excerpt}

        候选修复涉及的改动概览：{change_summary}

        - 历史改错记录：
        {history_context}

        请判断候选错误是否相较基准错误更接近于通过编译，输出 JSON：{{"score": 浮点数, "reason": "简述判断依据"}}。
        - `score` 取值范围建议在 [-1, 1]，越大表示越有希望继续沿着此方向迭代。
        - 若难以判断，返回 0。
        - 仅输出 JSON，不要添加额外文本。

        - 绝对不允许出现未预期的闭合分隔符，如打破函数的布局的错误，比如 unexpected closing delimiter，这种错误是非常严重的错误，应该给出 -1 的评分。
                - 请参考以下评分细则：
                    * 核心报错数量显著减少，或错误仅剩告警/轻微问题：score 介于 0.5 至 1 之间；若几乎能通过编译，趋近 1。
                    * 报错类型有所改善（如从 borrow 错误降级为简单类型不匹配），记 0 至 0.5；如果只是局部优化或信息不足，可给接近 0 的分数。
                    * 与基准持平（错误完全一致或仅日志顺序不同），记 0并说明原因。
                    * 新增严重错误或原有错误加重，记负分；出现语法破坏、未预期的闭合分隔符等高危问题，分值应低于 -0.5。
        """
    ).strip()

    parser = TemplateParser(
        "{result:json:CandidateEvaluationModel}",
        model_map={"CandidateEvaluationModel": CandidateEvaluationModel},
    )

    try:
        response = llm.call(prompt, parser=parser, max_retry=2)
    except Exception:
        return 0.0, ""

    if not isinstance(response, dict) or not response.get("success"):
        return 0.0, ""

    data = response.get("data", {}).get("result")
    score: float = 0.0
    reason = ""

    if isinstance(data, CandidateEvaluationModel):
        score = float(getattr(data, "score", 0.0) or 0.0)
        reason = str(getattr(data, "reason", "") or "")
    elif isinstance(data, dict):
        score = float(data.get("score", 0.0) or 0.0)
        reason = str(data.get("reason") or data.get("rationale") or "")

    score = max(-1.0, min(1.0, score))
    return score, reason


def _ensure_trailing_newline(text: str) -> str:
    if not text:
        return ""
    stripped = text.rstrip("\n")
    return stripped + "\n"


_ERROR_LOCATION_PATTERN = re.compile(r"-->\s+([^:\s][^:]*):(\d+):(\d+)")


def _parse_error_locations(error_output: str) -> List[Tuple[str, int]]:
    locations: List[Tuple[str, int]] = []
    for match in _ERROR_LOCATION_PATTERN.finditer(error_output):
        file_part, line_str, _col_str = match.groups()
        try:
            line_no = int(line_str)
        except ValueError:
            continue
        locations.append((file_part.strip(), line_no))
    return locations


def _collect_symbols_for_line(symbol_item: Dict[str, Any], line_no: int, results: Set[str]) -> None:
    symbol_name = symbol_item.get("name")
    start_line: Optional[int] = symbol_item.get("start_line")
    end_line: Optional[int] = symbol_item.get("end_line")

    if start_line is None or end_line is None:
        start_line = -1
        end_line = -1

    # Convert from zero-based (common in LSP) to one-based line numbers.
    match_found = False
    if start_line >= 0 and end_line >= 0 and start_line <= end_line:
        # Prefer direct comparison assuming one-based data.
        if start_line <= line_no <= end_line:
            match_found = True
        else:
            # Fall back to treating values as zero-based.
            start_line_1 = start_line + 1
            end_line_1 = end_line + 1
            if start_line_1 <= line_no <= end_line_1:
                start_line = start_line_1
                end_line = end_line_1
                match_found = True

    if match_found:
        if isinstance(symbol_name, str) and symbol_name.strip():
            results.add(symbol_name.strip())

    for child in symbol_item.get("children", []) or []:
        if isinstance(child, dict):
            _collect_symbols_for_line(child, line_no, results)


def _force_symbols_from_error_output(
    agent: Any,
    rust_output_dir: Path,
    error_output: str,
) -> Dict[str, Set[str]]:
    lsp_toolset = getattr(agent, "lsp_toolset", None)
    if lsp_toolset is None or not hasattr(lsp_toolset, "lsp_list_document_symbols"):
        return {}

    forced: Dict[str, Set[str]] = {}
    locations = _parse_error_locations(error_output)
    if not locations:
        return forced

    for file_hint, line_no in locations:
        if line_no <= 0:
            continue

        candidate_path = Path(file_hint)
        if not candidate_path.is_absolute():
            candidate_path = (rust_output_dir / candidate_path).resolve()
        if not candidate_path.exists():
            continue

        try:
            rel_path = candidate_path.relative_to(rust_output_dir)
        except ValueError:
            continue

        try:
            symbols = lsp_toolset.lsp_list_document_symbols(str(candidate_path))['symbols']
        except Exception:
            continue
        if not isinstance(symbols, list):
            continue

        matched: Set[str] = set()
        for item in symbols:
            if not isinstance(item, dict):
                continue
            _collect_symbols_for_line(item, line_no, matched)

        if not matched:
            continue

        rel_key = rel_path.as_posix()
        bucket = forced.setdefault(rel_key, set())
        bucket.update(matched)

    return forced


def _extract_fix_targets(llm: LLM, error_output: str) -> Dict[str, List[str]]:
    if not error_output or not error_output.strip():
        return {}

    agent = _get_swe_agent_instance()
    if agent is None:
        return {}

    tools_to_register: List[Any] = []
    lsp_toolset = getattr(agent, "lsp_toolset", None)
    if lsp_toolset is not None:
        tools_to_register.extend(
            [
                lsp_toolset.lsp_list_document_symbols,
                lsp_toolset.lsp_list_symbol_definitions,
            ]
        )
    toolset = getattr(agent, "toolset", None)
    if toolset is not None:
        tools_to_register.append(toolset.read_file)
    if tools_to_register:
        agent.register_tools(tools_to_register)

    try:
        rust_output_dir = load_rust_output_dir()
    except Exception as exc:
        print(f"无法定位 Rust 输出目录，跳过编译：{exc}")
        return {}

    prompt = textwrap.dedent(
        f"""
        你是一名资深的 Rust 构建工程师（SWE Agent）。请阅读下面的 `cargo check` 编译错误日志，并严格按以下步骤执行：

        1. 解析日志中每条 `--> 路径:行:列`，收集所有报错文件及行号。
        2. 对每个报错行号，必须先调用 `lsp_list_document_symbols` 获得相关文件的候选符号和行号范围
        2. 然后通过`lsp_list_symbol_definitions`（或read_file）获取覆盖该行号的完整函数定义获得完整函数定义代码。
        3. 根据获得的代码上下文，所有 Rust 文件及符号。若无法定位具体符号，返回空数组。
        4. 结合编译报错与获得的上下文，最后输出输出严格的 JSON，获得可能需要修改的文件及符号列表。
        - 文件路径使用相对于工程根目录的相对路径（如 `src/lib.rs`）
        - 不得包含额外文字或注释。

        请确保在确认所有报错位置的上下文后再生成最终 JSON。

        ### 编译错误日志
        {_truncate_text(error_output, 20000)}
        """
    ).strip()

    parser = TemplateParser("{result:json:FixTargetsModel}", model_map={"FixTargetsModel": FixTargetsModel})
    try:
        # response = llm.call(prompt, parser=parser, max_retry=3)
        response = agent.run_task(prompt,
                                    acceptance_criteria=['最后返回json格式的符号列表即可'],
                                   parser=parser, max_retry=3)['final_response']
    except Exception:
        return {}

    if not isinstance(response, dict) or not response.get("success"):
        return {}

    data = response.get("data", {}).get("result")
    if isinstance(data, FixTargetsModel):
        files = data.files
    elif isinstance(data, dict):
        files = data.get("files")
    else:
        files = data
    if not isinstance(files, dict):
        return {}

    normalized: Dict[str, List[str]] = {}
    for path, symbols in files.items():
        if not isinstance(path, str):
            continue
        if isinstance(symbols, list):
            filtered = [sym.strip() for sym in symbols if isinstance(sym, str) and sym.strip()]
        else:
            filtered = []
        if filtered:
            normalized[path.strip()] = filtered

    forced_symbols = _force_symbols_from_error_output(agent, rust_output_dir, error_output)
    if forced_symbols:
        for rel_path, symbol_set in forced_symbols.items():
            bucket = normalized.setdefault(rel_path, [])
            existing: Set[str] = set(bucket)
            for symbol in sorted(symbol_set):
                if symbol in existing:
                    continue
                bucket.append(symbol)
                existing.add(symbol)

    if not normalized:
        return {}

    return _augment_fix_targets_with_dependencies(normalized, rust_output_dir)


def _augment_fix_targets_with_dependencies(
    targets: Dict[str, List[str]],
    rust_output_dir: Path,
) -> Dict[str, List[str]]:
    augmented: Dict[str, List[str]] = {path: list(symbols) for path, symbols in targets.items()}
    existing: Dict[str, Set[str]] = {path: set(symbols) for path, symbols in augmented.items()}

    try:
        analyzer = get_analyzer()
    except Exception:
        return targets

    mapping_path = rust_output_dir / "mapping_c2r.json"
    mapping_c2r: Dict[str, str] = {}
    rust_to_c: Dict[str, Set[str]] = defaultdict(set)
    if mapping_path.exists():
        try:
            with mapping_path.open("r", encoding="utf-8") as fh:
                mapping_payload = json.load(fh) or {}
            raw_mapping = mapping_payload.get("mapping_c2r", {})
            if isinstance(raw_mapping, dict):
                for c_name, rust_name in raw_mapping.items():
                    if isinstance(c_name, str) and isinstance(rust_name, str):
                        mapping_c2r[c_name] = rust_name
                        rust_to_c[rust_name].add(c_name)
        except Exception:
            pass

    if not mapping_c2r:
        return targets

    visited: Set[Tuple[str, str]] = set()

    for file_rel, symbol_list in list(augmented.items()):
        original_symbols = list(symbol_list)
        for rust_symbol in original_symbols:
            dependency_entries = _collect_rust_dependencies_for_symbol(
                analyzer,
                rust_symbol,
                mapping_c2r,
                rust_to_c,
                rust_output_dir,
            )
            for dep_file, dep_symbol in dependency_entries:
                if not dep_symbol:
                    continue
                pair_key = (dep_file or file_rel, dep_symbol)
                if pair_key in visited:
                    continue
                visited.add(pair_key)
                target_file = dep_file or file_rel
                bucket = augmented.setdefault(target_file, [])
                bucket_seen = existing.setdefault(target_file, set())
                if dep_symbol not in bucket_seen:
                    bucket.append(dep_symbol)
                    bucket_seen.add(dep_symbol)

    return {path: symbols for path, symbols in augmented.items() if symbols}


def _collect_rust_dependencies_for_symbol(
    analyzer: Any,
    rust_symbol: str,
    mapping_c2r: Dict[str, str],
    rust_to_c: Dict[str, Set[str]],
    project_root: Path,
) -> List[Tuple[Optional[str], str]]:
    c_candidates = rust_to_c.get(rust_symbol, set())
    if not c_candidates:
        return []

    dependency_entries: List[Tuple[Optional[str], str]] = []
    seen_dep_keys: Set[str] = set()
    seen_pairs: Set[Tuple[str, str]] = set()

    for c_name in c_candidates:
        try:
            refs = analyzer.find_symbols_by_name(c_name)
        except Exception:
            continue
        if not refs:
            continue
        sym_ref = refs[0]

        try:
            func_nodes, _ = analyzer.get_dependencies(
                sym_ref,
                depth=1,
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

            dep_c_name = dep.name
            rust_dep_name = mapping_c2r.get(dep_c_name)
            if not isinstance(rust_dep_name, str):
                continue

            pair = (dep_c_name, rust_dep_name)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            try:
                matches = _run_rust_symbol_extractor(project_root, rust_dep_name)
            except Exception:
                matches = []

            added_file = False
            for match in matches or []:
                file_rel = match.get("file")
                if isinstance(file_rel, str):
                    dependency_entries.append((file_rel, rust_dep_name))
                    added_file = True
            if not added_file:
                dependency_entries.append((None, rust_dep_name))

    return dependency_entries


def _fallback_find_symbol_span(content: str, symbol: str) -> Optional[Tuple[int, int]]:
    lines = content.splitlines()
    pattern = re.compile(rf"\bfn\s+{re.escape(symbol)}\b")
    for idx, line in enumerate(lines):
        if not pattern.search(line):
            continue
        start_line = idx + 1
        depth = 0
        started = False
        for j in range(idx, len(lines)):
            current = lines[j]
            open_count = current.count("{")
            close_count = current.count("}")
            if open_count:
                started = True
            depth += open_count
            depth -= close_count
            if started and depth <= 0:
                end_line = j + 1
                return start_line, end_line
        break
    return None


def _resolve_symbol_span(project_root: Path, file_rel: str, symbol: str, content: str) -> Optional[Tuple[int, int]]:
    try:
        matches = _run_rust_symbol_extractor(project_root, symbol)
    except Exception:
        matches = []

    for match in matches:
        match_file = match.get("file")
        if match_file != file_rel:
            continue
        start_line = match.get("start_line")
        end_line = match.get("end_line")
        if isinstance(start_line, int) and isinstance(end_line, int) and start_line > 0 and end_line >= start_line:
            return start_line, end_line

    return _fallback_find_symbol_span(content, symbol)


def _build_segments_from_spans(
    lines: List[str],
    spans: List[Tuple[int, int, str]],
) -> Tuple[List[str], List[str], Dict[str, str]]:
    segments: List[str] = []
    symbol_order: List[str] = []
    symbol_snippets: Dict[str, str] = {}

    cursor = 0
    sorted_spans = sorted(spans, key=lambda item: item[0])

    for start_line, end_line, symbol in sorted_spans:
        start_idx = max(min(start_line - 1, len(lines)), 0)
        end_idx = max(min(end_line, len(lines)), start_idx)
        segments.append("".join(lines[cursor:start_idx]))
        snippet = "".join(lines[start_idx:end_idx])
        symbol_snippets[symbol] = _ensure_trailing_newline(snippet)
        symbol_order.append(symbol)
        cursor = end_idx

    segments.append("".join(lines[cursor:]))
    return segments, symbol_order, symbol_snippets


_USE_STMT_PATTERN = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?use\s")


def _extract_use_blocks_from_text(text: str) -> Tuple[str, List[str]]:
    lines = text.splitlines(keepends=True)
    use_blocks: List[str] = []
    residual_lines: List[str] = []
    idx = 0

    while idx < len(lines):
        line = lines[idx]
        if _USE_STMT_PATTERN.match(line):
            block_lines: List[str] = []

            # Include immediately preceding attributes without blank lines.
            attr_buffer: List[str] = []
            while residual_lines:
                candidate = residual_lines[-1]
                if candidate.strip() == "":
                    break
                if candidate.lstrip().startswith("#["):
                    attr_buffer.insert(0, residual_lines.pop())
                else:
                    break

            block_lines.extend(attr_buffer)
            block_lines.append(line)

            brace_balance = line.count("{") - line.count("}")
            semicolon_seen = ";" in line
            idx += 1

            while idx < len(lines) and (brace_balance > 0 or not semicolon_seen):
                continuation = lines[idx]
                block_lines.append(continuation)
                brace_balance += continuation.count("{") - continuation.count("}")
                if ";" in continuation:
                    semicolon_seen = True
                idx += 1

            use_blocks.append("".join(block_lines))
        else:
            residual_lines.append(line)
            idx += 1

    residual_text = "".join(residual_lines)
    return residual_text, use_blocks


def _split_segments_and_uses(
    segments: List[str],
) -> Tuple[List[str], List[str], List[int]]:
    trimmed_segments: List[str] = []
    use_statements: List[str] = []
    use_segment_indices: List[int] = []

    for idx, segment in enumerate(segments):
        residual, uses = _extract_use_blocks_from_text(segment)
        trimmed_segments.append(residual)
        for use_text in uses:
            use_statements.append(use_text)
            use_segment_indices.append(idx)

    return trimmed_segments, use_statements, use_segment_indices


def _build_fix_payload(
    project_root: Path,
    targets: Dict[str, List[str]],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    payload: Dict[str, Dict[str, Any]] = {}
    metadata: Dict[str, Dict[str, Any]] = {}

    request_queue: deque[Tuple[str, str, str]] = deque()
    seen_requests: Set[Tuple[str, str]] = set()
    resolved_spans: Dict[str, List[Tuple[int, int, str]]] = defaultdict(list)
    unresolved_reported: Set[Tuple[str, str]] = set()

    for file_rel, symbols in targets.items():
        if not isinstance(file_rel, str) or not symbols:
            continue
        normalized = [sym.strip() for sym in symbols if isinstance(sym, str) and sym.strip()]
        for symbol in normalized:
            request_queue.append((file_rel, symbol, file_rel))

    while request_queue:
        file_rel, symbol, origin_file = request_queue.popleft()
        request_key = (file_rel, symbol)
        if request_key in seen_requests:
            continue
        seen_requests.add(request_key)

        dest_path = (project_root / file_rel).resolve()
        try:
            dest_path.relative_to(project_root)
        except ValueError:
            print(f"提示: 文件路径越界，已忽略 {file_rel}")
            continue

        content = ""
        lines: List[str] = []
        file_readable = False
        if dest_path.exists():
            try:
                content = dest_path.read_text(encoding="utf-8")
                lines = content.splitlines(keepends=True)
                file_readable = True
            except OSError as exc:
                print(f"提示: 读取 {file_rel} 失败，原因: {exc}")

        span: Optional[Tuple[int, int]] = None
        if file_readable:
            span = _resolve_symbol_span(project_root, file_rel, symbol, content)

        if span is not None:
            resolved_spans[file_rel].append((span[0], span[1], symbol))
            continue

        added_any = False
        try:
            matches = _run_rust_symbol_extractor(project_root, symbol)
        except Exception:
            matches = []

        for match in matches or []:
            alt_file = match.get("file")
            start_line = match.get("start_line")
            end_line = match.get("end_line")
            if not isinstance(alt_file, str):
                continue
            alt_file = alt_file.strip()
            if not alt_file:
                continue

            if (
                alt_file == file_rel
                and file_readable
                and isinstance(start_line, int)
                and isinstance(end_line, int)
            ):
                resolved_spans[file_rel].append((start_line, end_line, symbol))
                added_any = True
                break

            request_queue.append((alt_file, symbol, origin_file))
            added_any = True

        if added_any:
            continue

        warning_key = (origin_file, symbol)
        if warning_key in unresolved_reported:
            continue
        unresolved_reported.add(warning_key)
        print(f"提示: 未在工作区中找到符号 {symbol}（原始文件: {origin_file}）")
        # 从 targets 中删除未找到的符号
        if origin_file in targets and symbol in targets[origin_file]:
            targets[origin_file].remove(symbol)
            if not targets[origin_file]:
                del targets[origin_file]

    for file_rel, spans in resolved_spans.items():
        if not spans:
            continue

        dest_path = (project_root / file_rel).resolve()
        try:
            dest_path.relative_to(project_root)
        except ValueError:
            print(f"提示: 文件路径越界，已忽略 {file_rel}")
            continue

        if not dest_path.exists():
            print(f"提示: 跳过不存在的文件 {file_rel}")
            continue

        try:
            content = dest_path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"提示: 读取 {file_rel} 失败，原因: {exc}")
            continue

        lines = content.splitlines(keepends=True)

        unique_spans: List[Tuple[int, int, str]] = []
        seen_symbols: Set[str] = set()
        for start_line, end_line, symbol in sorted(spans, key=lambda item: item[0]):
            if not isinstance(start_line, int) or not isinstance(end_line, int):
                continue
            if start_line <= 0 or end_line < start_line:
                continue
            if symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            unique_spans.append((start_line, end_line, symbol))

        if not unique_spans:
            continue

        segments, symbol_order, symbol_snippets = _build_segments_from_spans(lines, unique_spans)
        trimmed_segments, use_statements, use_segment_indices = _split_segments_and_uses(segments)

        file_payload: Dict[str, Any] = {symbol: code for symbol, code in symbol_snippets.items()}
        file_payload["extra"] = list(use_statements)
        payload[file_rel] = file_payload

        metadata[file_rel] = {
            "segments": list(trimmed_segments),
            "order": list(symbol_order),
            "symbol_snippets": dict(symbol_snippets),
            "use_segment_indices": list(use_segment_indices),
        }

    return payload, metadata


def _request_compile_fixes(
    llm: LLM,
    error_output: str,
    payload: Dict[str, Dict[str, Any]],
    history_context: Optional[str] = None,
) -> List[Dict[str, Dict[str, Any]]]:
    if not payload:
        return []

    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)
    history_section = ""
    if history_context:
        history_block = textwrap.dedent(
            f"""
            ### 历史修复轨迹
            以下是最近几轮改错的摘要，请不要重复相同的思路，尝试新的修复策略：
            {history_context}
            """
        ).strip()
        history_section = "\n\n" + history_block
    prompt = textwrap.dedent(
        f"""
        你是一名经验丰富的 Rust 修复工程师。请依据编译错误以及给定的文件内容，仔细分析错误的原因，对代码编译报错修复以通过 `cargo check`。

        - 输入数据以 {{文件路径: {{符号: 代码, "extra": 片段数组}}}} 的形式提供。
        - `extra` 仅包含该文件中的 `use` / `pub use` 导入语句（含原始换行），顺序与源码一致。
        - 若导入带有紧邻的属性（如 `#[cfg]`），属性与导入会作为同一个数组元素提供。
        - 如需修改某个符号，请在对应键下提供更新后的完整代码。
        - 若需调整导入语句，可在 `extra` 数组中增删或编辑对应字符串；如未改动请省略该字段。
        - 仅返回确实发生改动的文件；若文件整体未改动，请不要在结果中出现该文件。
        - 对于保留的文件，仅返回发生改动的符号键；符号代码与输入一致时请省略该键。
        - `extra` 与输入完全一致时请省略该键，以减小输出体积。

        - 输出必须是 JSON 数组，数组的每个元素为一个候选修复可能，一个候选可能包含多个文件的修改，形如 {{文件路径: {{符号: 更新后的代码, "extra": 片段数组}}}}。
        - 给出尽量多的修复候选操作，从而提高成功率，至少给出 1 个候选，推荐 2 个以上；
        - 保持现有的缩进与风格，不要引入无关改动。

        ### 当前编译错误
        {_truncate_text(error_output, 20000)}

        {history_section}

        ### 当前文件内容
        {payload_json}
        """
    ).strip()

    parser = TemplateParser(
        "{result:json:FixResultListModel}",
        model_map={"FixResultListModel": FixResultListModel, "FixResultModel": FixResultModel},
    )
    try:
        response = llm.call(prompt, parser=parser, max_retry=3)
    except Exception:
        return []

    if not isinstance(response, dict) or not response.get("success"):
        return []

    data = response.get("data", {}).get("result")
    candidates: List[Any]
    if isinstance(data, FixResultListModel):
        candidates = data.to_list()
    elif isinstance(data, FixResultModel):
        candidates = [data.to_dict()]
    elif isinstance(data, list):
        candidates = data
    elif isinstance(data, dict):
        candidates = [data]
    else:
        candidates = []

    normalized: List[Dict[str, Dict[str, Any]]] = []
    seen: Set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        filtered_candidate: Dict[str, Dict[str, Any]] = {}
        for file_rel, file_payload in candidate.items():
            if not isinstance(file_rel, str) or not isinstance(file_payload, dict):
                continue
            filtered_file: Dict[str, Any] = {}
            for symbol_name, value in file_payload.items():
                if symbol_name == "extra":
                    if isinstance(value, list):
                        filtered_file["extra"] = [item for item in value if isinstance(item, str)]
                    continue
                if isinstance(symbol_name, str) and isinstance(value, str):
                    filtered_file[symbol_name] = value
            if not filtered_file:
                continue
            filtered_candidate[file_rel.strip()] = filtered_file
        try:
            marker = json.dumps(filtered_candidate, sort_keys=True, ensure_ascii=False)
        except TypeError:
            marker = None
        if filtered_candidate and marker not in seen:
            normalized.append(filtered_candidate)
            if marker is not None:
                seen.add(marker)

    return normalized


def _apply_fix_payload(
    project_root: Path,
    metadata: Dict[str, Dict[str, Any]],
    original_payload: Dict[str, Dict[str, Any]],
    updated_payload: Dict[str, Dict[str, Any]],
) -> None:
    for file_rel, meta in metadata.items():
        dest_path = (project_root / file_rel).resolve()
        try:
            dest_path.relative_to(project_root)
        except ValueError:
            print(f"提示: 写入目标越界，已忽略 {file_rel}")
            continue
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        original_entries = original_payload.get(file_rel, {}) if isinstance(original_payload, dict) else {}
        updated_entries = updated_payload.get(file_rel, {}) if isinstance(updated_payload, dict) else {}

        segments = meta.get("segments")
        order = meta.get("order")
        symbol_snippets = meta.get("symbol_snippets", {})
        use_segment_indices = meta.get("use_segment_indices", [])
        original_extra = original_entries.get("extra", []) if isinstance(original_entries, dict) else []

        if not isinstance(segments, list) or not isinstance(order, list):
            print(f"提示: 无法恢复 {file_rel} 的片段结构，跳过写回。")
            continue
        if len(segments) != len(order) + 1:
            print(f"提示: {file_rel} 片段结构异常，跳过写回。")
            continue

        if isinstance(updated_entries, dict) and isinstance(updated_entries.get("extra"), list):
            target_extra = updated_entries["extra"]
        else:
            target_extra = original_extra if isinstance(original_extra, list) else []

        base_indices = use_segment_indices if use_segment_indices else [0]
        default_indices = [base_indices[min(idx, len(base_indices) - 1)] for idx in range(len(target_extra))]

        uses_by_segment: Dict[int, List[str]] = {}
        seen_use_text: Dict[int, Set[str]] = {}
        for use_text, seg_idx in zip(target_extra, default_indices):
            if not isinstance(seg_idx, int) or seg_idx < 0 or seg_idx >= len(segments):
                seg_idx = 0
            text = use_text if isinstance(use_text, str) else ""
            if text and not text.endswith("\n"):
                text += "\n"
            normalized = text.strip()
            bucket = uses_by_segment.setdefault(seg_idx, [])
            seen_bucket = seen_use_text.setdefault(seg_idx, set())
            if normalized and normalized in seen_bucket:
                continue
            if normalized:
                seen_bucket.add(normalized)
            bucket.append(text)

        final_parts: List[str] = []
        for idx in range(len(order) + 1):
            segment_text = segments[idx] if isinstance(segments[idx], str) else ""
            final_parts.append(segment_text)

            for use_text in uses_by_segment.get(idx, []):
                final_parts.append(use_text)

            if idx >= len(order):
                continue

            symbol = order[idx]
            replacement = None
            if isinstance(updated_entries, dict):
                replacement = updated_entries.get(symbol)
            if not isinstance(replacement, str) or not replacement.strip():
                replacement = symbol_snippets.get(symbol)
            if not isinstance(replacement, str):
                replacement = original_entries.get(symbol)
            if not isinstance(replacement, str):
                replacement = ""
            final_parts.append(_ensure_trailing_newline(replacement))

        final_content = "".join(final_parts)
        if not final_content.endswith("\n"):
            final_content += "\n"

        try:
            dest_path.write_text(final_content, encoding="utf-8")
        except OSError as exc:
            print(f"提示: 写入 {file_rel} 失败，原因: {exc}")


def _snapshot_file_contents(
    project_root: Path,
    metadata: Dict[str, Dict[str, Any]],
) -> Dict[str, Optional[str]]:
    snapshots: Dict[str, Optional[str]] = {}
    for file_rel in metadata.keys():
        dest_path = (project_root / file_rel).resolve()
        try:
            dest_path.relative_to(project_root)
        except ValueError:
            continue
        if dest_path.exists():
            try:
                snapshots[file_rel] = dest_path.read_text(encoding="utf-8")
            except OSError:
                snapshots[file_rel] = None
        else:
            snapshots[file_rel] = None
    return snapshots


def _restore_file_contents(
    project_root: Path,
    snapshots: Dict[str, Optional[str]],
) -> None:
    for file_rel, content in snapshots.items():
        dest_path = (project_root / file_rel).resolve()
        try:
            dest_path.relative_to(project_root)
        except ValueError:
            continue
        if content is None:
            continue
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            dest_path.write_text(content, encoding="utf-8")
        except OSError:
            pass


def _attempt_llm_compile_fix(project_root: Path, error_output: str) -> bool:
    llm = LLM(logger=True)
    targets = _extract_fix_targets(llm, error_output)
    print(f"LLM 识别到需要修复的符号: {targets}")
    if not targets:
        attempt_no = len(TRAJECTORY_MEMORY.mem) + 1
        error_excerpt = _truncate_text((error_output or "").strip(), 1500)
        note_lines = [
            f"尝试 {attempt_no}: 失败",
            "改动摘要: 无",
            "编译错误摘要:",
            error_excerpt or "无输出",
            "附注: LLM 未能识别需要修改的文件或符号。",
        ]
        TRAJECTORY_MEMORY.add("\n".join(note_lines).strip())
        print("提示: LLM 未能识别需要修改的文件或符号。")
        return False

    payload, metadata = _build_fix_payload(project_root, targets)
    if not payload:
        attempt_no = len(TRAJECTORY_MEMORY.mem) + 1
        note_lines = [
            f"尝试 {attempt_no}: 失败",
            "改动摘要: 无",
            "编译错误摘要:",
            "无法构建自动修复所需的上下文。",
        ]
        TRAJECTORY_MEMORY.add("\n".join(note_lines).strip())
        print("提示: 无法构建自动修复所需的上下文。")
        return False

    history_context = TRAJECTORY_MEMORY.get_latest(3)
    candidates = _request_compile_fixes(llm, error_output, payload, history_context=history_context)
    if not candidates:
        attempt_no = len(TRAJECTORY_MEMORY.mem) + 1
        error_excerpt = _truncate_text((error_output or "").strip(), 1500)
        note_lines = [
            f"尝试 {attempt_no}: 失败",
            "改动摘要: 无",
            "编译错误摘要:",
            error_excerpt or "无输出",
            "附注: LLM 未返回有效的修复结果。",
        ]
        TRAJECTORY_MEMORY.add("\n".join(note_lines).strip())
        print("提示: LLM 未返回有效的修复结果。")
        return False

    candidate_markers: List[Optional[str]] = []
    filtered_candidates: List[Dict[str, Dict[str, Any]]] = []
    for candidate in candidates:
        try:
            marker = json.dumps(candidate, sort_keys=True, ensure_ascii=False)
        except TypeError:
            marker = None
        if marker and marker in _LLM_FIX_PAYLOAD_HISTORY:
            continue
        filtered_candidates.append(candidate)
        candidate_markers.append(marker)

    if not filtered_candidates:
        attempt_no = len(TRAJECTORY_MEMORY.mem) + 1
        error_excerpt = _truncate_text((error_output or "").strip(), 1500)
        note_lines = [
            f"尝试 {attempt_no}: 失败",
            "改动摘要: 无",
            "编译错误摘要:",
            error_excerpt or "无输出",
            "附注: 候选修复均与历史重复，未执行新的 cargo check。",
        ]
        TRAJECTORY_MEMORY.add("\n".join(note_lines).strip())
        print("提示: 候选修复均与历史重复，跳过。")
        return False

    candidates = filtered_candidates
    print(f"LLM 提供了 {len(candidates)} 个修复候选。")

    snapshots = _snapshot_file_contents(project_root, metadata)

    baseline_output = error_output or ""
    baseline_error_len = len(baseline_output)
    evaluation_cache: Dict[str, Tuple[float, str]] = {}
    best_index = -1
    best_payload: Optional[Dict[str, Dict[str, Any]]] = None
    best_output = ""
    best_success = False
    best_score: float = float("-inf")

    for idx, candidate in enumerate(candidates):
        _restore_file_contents(project_root, snapshots)
        _apply_fix_payload(project_root, metadata, payload, candidate)

        # 新增验证步骤：检查目标符号是否仍能被提取
        skip_candidate = False
        for file_rel, symbols in targets.items():
            for symbol in symbols:
                try:
                    matches = _run_rust_symbol_extractor(project_root, symbol)
                    if not matches:
                        print(f"候选 {idx + 1} 跳过：符号 {symbol} 提取失败。")
                        skip_candidate = True
                        break
                except Exception as e:
                    print(f"候选 {idx + 1} 跳过：符号 {symbol} 提取异常：{e}")
                    skip_candidate = True
                    break
            if skip_candidate:
                break
        if skip_candidate:
            continue

        compile_ok, output = _run_cargo_check_once()
        error_len = 0 if compile_ok else len(output)
        candidate_signature = _normalize_compile_output_signature(output)
        status = "通过" if compile_ok else "失败"
        print(f"候选 {idx + 1}/{len(candidates)} cargo check {status}，错误长度 {error_len}。")
        if output and not compile_ok:
            print(_truncate_text(output, 2000))

        candidate_score = 0.0
        evaluation_reason = ""
        if compile_ok:
            candidate_score = 1.0
            evaluation_reason = "cargo check 已通过"
        elif baseline_output and output:
            cache_key = f"{candidate_signature}|{_summarize_candidate_changes(candidate)}"
            if cache_key in evaluation_cache:
                candidate_score, evaluation_reason = evaluation_cache[cache_key]
            else:
                candidate_score, evaluation_reason = _evaluate_candidate_progress(
                    llm,
                    baseline_output,
                    output,
                    candidate,
                    history_context
                )
                evaluation_cache[cache_key] = (candidate_score, evaluation_reason)

        if evaluation_reason:
            print(f"候选 {idx + 1} LLM 评估得分 {candidate_score:.2f}：{evaluation_reason}")

        update_best = False
        if compile_ok and not best_success:
            update_best = True
        elif compile_ok and best_success:
            if candidate_score > best_score + 1e-6:
                update_best = True
        elif not best_success:
            if best_payload is None or candidate_score > best_score + 1e-6:
                update_best = True

        if update_best:
            best_index = idx
            best_payload = candidate
            best_output = output
            best_success = compile_ok
            best_score = candidate_score

    _restore_file_contents(project_root, snapshots)

    if best_payload is None:
        print("提示: 所有候选修复均无效，已恢复原始内容。")
        return False

    if 0 <= best_index < len(candidate_markers):
        marker = candidate_markers[best_index]
        if marker:
            _LLM_FIX_PAYLOAD_HISTORY.add(marker)

    print(f"应用最佳候选 {best_index + 1}/{len(candidates)}，cargo check {'通过' if best_success else '仍未通过'}。")

    _apply_fix_payload(project_root, metadata, payload, best_payload)

    attempt_no = len(TRAJECTORY_MEMORY.mem) + 1
    history_entry = _build_history_entry(
        attempt_no,
        payload,
        best_payload,
        metadata,
        best_output,
        best_success,
        baseline_output,
    )
    TRAJECTORY_MEMORY.add(history_entry)

    return best_success


def _compile_after_translation(
    dest_paths: Set[Path],
    failing_symbol: Optional[str] = None,
) -> bool:
    # Compile immediately after filling a function to catch regressions early.
    _ = failing_symbol  # 保留参数以兼容调用方，当前流程不区分具体符号
    TRAJECTORY_MEMORY.clear()
    max_fix_rounds = 30

    for round_idx in range(max_fix_rounds + 1):
        compile_ok, raw_output = _run_cargo_check_once()
        if compile_ok:
            if round_idx > 0:
                rel_list = _format_relative_paths(dest_paths)
                print(f"cargo check 修复完成: {', '.join(rel_list)}")
            return True

        if not raw_output:
            print("cargo check 失败，但没有任何输出，无法自动修复。")
            return False

        error_lines = raw_output.splitlines()
        truncated = "\n".join(error_lines[-80:])
        print("cargo check 失败，启动 LLM 自动修复：")
        print(truncated)

        try:
            project_root = load_rust_output_dir()
        except Exception as exc:
            print(f"提示: 无法定位 Rust 输出目录，自动修复中止：{exc}")
            return False

        fix_ok = _attempt_llm_compile_fix(project_root, raw_output)

    print("达到最大自动修复次数，仍未通过编译。")
    return False


def _replace_with_span(dest_path: Path, start_line: int, end_line: int, new_code: str) -> bool:
    if start_line <= 0 or end_line <= 0 or end_line < start_line:
        return False

    if not dest_path.exists():
        return False

    content = dest_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    max_index = len(lines)
    start_idx = min(max(start_line - 1, 0), max_index)
    end_idx = min(max(end_line, start_idx), max_index)
    new_code_lines = new_code.rstrip("\n").splitlines()

    updated_lines = lines[:start_idx] + new_code_lines + lines[end_idx:]
    dest_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    return True


def _translate_symbol(
    symbol: Dict[str, Any],
    current_mapping: Dict[str, Optional[str]],
    rust_defs: Dict[str, str],
    target_rust_names: List[str],
) -> Tuple[List[Dict[str, Any]], Dict[str, Optional[str]], Dict[str, List[Dict[str, Any]]]]:
    llm = LLM(logger=True)
    parser = TemplateParser("{batch:json:RustBatch}", model_map={"RustBatch": RustBatch})

    dependency_entries, dependency_summary = gather_dependency_context_from_project([symbol], current_mapping, rust_defs)
    project_root = load_rust_output_dir()
    rust_placeholders_map: Dict[str, List[Dict[str, Any]]] = {}
    placeholder_texts: List[str] = []

    for rust_name in target_rust_names:
        if not rust_name:
            continue
        matches = _run_rust_symbol_extractor(project_root, rust_name)
        if matches:
            rust_placeholders_map[rust_name] = matches
            placeholder_texts.extend(_format_placeholder_entry(match) for match in matches)

    prompt = _build_fill_prompt([symbol], dependency_entries, dependency_summary, placeholder_texts)
    result = llm.call(prompt, parser=parser, max_retry=5)
    if not isinstance(result, dict) or not result.get("success"):
        raise RuntimeError(f"LLM 解析失败: {result}")
    data = result["data"]["batch"]
    return data["items"], data.get("mapping_c2r", {}), rust_placeholders_map


def _collect_dest_paths(symbol: Dict[str, Any]) -> List[Path]:
    file_path = symbol.get("file_path")
    if not file_path:
        return []
    rel_path = _resolve_relative_c_path(str(file_path))
    if rel_path is None:
        return []
    target_rel = _map_c_path_to_rust_relative(rel_path)
    if target_rel is None:
        return []
    rust_root = load_rust_output_dir() / "src"
    return [rust_root / target_rel]


def _replace_function(dest_path: Path, rust_name: str, new_code: str) -> bool:
    if FUNCTION_STUB_PATTERN not in new_code:
        new_code_text = new_code.strip() + "\n"
    else:
        new_code_text = new_code

    content = dest_path.read_text(encoding="utf-8")
    stub_regex = re.compile(
        rf"pub\s+fn\s+{re.escape(rust_name)}\b[\s\S]*?\{{\s*{FUNCTION_STUB_PATTERN}\s*;?\s*\}}",
        re.MULTILINE,
    )
    if not stub_regex.search(content):
        return False
    updated = stub_regex.sub(new_code_text.rstrip(), content, count=1)
    dest_path.write_text(updated if updated.endswith("\n") else updated + "\n", encoding="utf-8")
    return True


def _has_unimplemented_stub(project_root: Path, rust_name: str, dest_paths: List[Path]) -> bool:
    try:
        matches = _run_rust_symbol_extractor(project_root, rust_name)
    except Exception:
        matches = []

    for match in matches:
        code = match.get("code")
        if isinstance(code, str) and FUNCTION_STUB_PATTERN in code:
            return True

    if matches:
        return False

    for dest_path in dest_paths:
        if not dest_path.exists():
            continue
        try:
            content = dest_path.read_text(encoding="utf-8")
        except OSError:
            continue
        if FUNCTION_STUB_PATTERN in content:
            return True

    return False


def _load_batches() -> List[Dict[str, Any]]:
    with open("analyzer/output/file_batches.json", "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("batches", [])


def _load_mapping_sequence() -> Tuple[List[Tuple[str, Optional[str]]], Dict[str, Optional[str]]]:
    rust_output_dir = load_rust_output_dir()
    mapping_path = rust_output_dir / "mapping_c2r.json"
    if not mapping_path.exists():
        return [], {}

    with mapping_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh) or {}

    raw_mapping = payload.get("mapping_c2r", {})
    if not isinstance(raw_mapping, dict):
        return [], {}

    sequence: List[Tuple[str, Optional[str]]] = []
    mapping: Dict[str, Optional[str]] = {}
    for c_name, rust_name in raw_mapping.items():
        if not isinstance(c_name, str):
            continue
        resolved = rust_name if isinstance(rust_name, str) else None
        mapping[c_name] = resolved
        mapping[_normalize_c_key(c_name)] = resolved
        sequence.append((c_name, resolved))

    return sequence, mapping


def _build_symbol_lookup(batches: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for batch in batches:
        for symbol in batch.get("symbols", []):
            c_name = symbol.get("name") or symbol.get("symbol") or symbol.get("id")
            if not isinstance(c_name, str) or not c_name:
                continue
            lookup.setdefault(c_name, symbol)
            lookup.setdefault(_normalize_c_key(c_name), symbol)
    return lookup

def main() -> None:
    project_root = load_rust_output_dir()
    rust_root = project_root / "src"
    rust_root.mkdir(parents=True, exist_ok=True)

    batches = _load_batches()
    symbol_lookup = _build_symbol_lookup(batches)

    sequence, loaded_mapping = _load_mapping_sequence()
    mapping: Dict[str, Optional[str]] = dict(loaded_mapping)
    rust_defs: Dict[str, str] = {}
    translated_rust: Set[str] = set()

    tasks: List[Dict[str, Any]] = []
    for c_name, rust_name in sequence:
        if not rust_name:
            continue
        symbol = symbol_lookup.get(c_name) or symbol_lookup.get(_normalize_c_key(c_name))
        if not symbol:
            continue
        if symbol.get("type") != "functions":
            continue
        dest_paths = _collect_dest_paths(symbol)
        tasks.append(
            {
                "c_name": c_name,
                "rust_name": rust_name,
                "symbol": symbol,
                "dest_paths": dest_paths,
            }
        )

    for idx, task in enumerate(tasks):
        c_name = task["c_name"]
        rust_name = task["rust_name"]
        symbol = task["symbol"]
        dest_paths = task["dest_paths"]

        existing_paths = [path for path in dest_paths if path.exists()]
        has_stub = _has_unimplemented_stub(project_root, rust_name, existing_paths)
        if existing_paths and not has_stub:
            print(f"跳过 {rust_name}，未检测到 unimplemented!() 存根。")
            translated_rust.add(rust_name)
        else:
            items, mapping_c2r, rust_placeholders = _translate_symbol(
                symbol,
                mapping,
                rust_defs,
                [rust_name],
            )
            effective_mapping = dict(mapping)
            for mapped_c, mapped_rust in mapping_c2r.items():
                if not mapped_c or mapped_rust is None:
                    continue
                mapping[mapped_c] = mapped_rust
                mapping[_normalize_c_key(mapped_c)] = mapped_rust
                effective_mapping[mapped_c] = mapped_rust
                effective_mapping[_normalize_c_key(mapped_c)] = mapped_rust

            name_to_code = {
                item.get("name"): item.get("code")
                for item in items
                if isinstance(item.get("name"), str) and isinstance(item.get("code"), str)
            }

            for rust_symbol, rust_code in name_to_code.items():
                if rust_code is None:
                    continue
                if rust_symbol in translated_rust:
                    continue
                replaced_any = False
                updated_paths: Set[Path] = set()
                placeholder_matches = rust_placeholders.get(rust_symbol, [])
                for placeholder in placeholder_matches:
                    file_rel = placeholder.get("file")
                    start_line = placeholder.get("start_line")
                    end_line = placeholder.get("end_line")
                    if not isinstance(file_rel, str) or not isinstance(start_line, int) or not isinstance(end_line, int):
                        continue
                    dest_path = project_root / file_rel
                    replaced = _replace_with_span(dest_path, start_line, end_line, rust_code)
                    if replaced:
                        rust_defs[rust_symbol] = rust_code
                        translated_rust.add(rust_symbol)
                        updated_paths.add(dest_path)
                        replaced_any = True
                        break

                if not replaced_any:
                    for dest_path in dest_paths:
                        if not dest_path.exists():
                            continue
                        replaced = _replace_function(dest_path, rust_symbol, rust_code)
                        if replaced:
                            rust_defs[rust_symbol] = rust_code
                            translated_rust.add(rust_symbol)
                            updated_paths.add(dest_path)
                            replaced_any = True
                            break

                if replaced_any:
                    if not updated_paths:
                        updated_paths.update(task["dest_paths"])

                    compile_ok = _compile_after_translation(
                        updated_paths,
                        failing_symbol=rust_symbol,
                    )
                    if not compile_ok:
                        raise RuntimeError(f"{rust_symbol} 编译失败，已尝试自动修复。")
                else:
                    dest_paths = task["dest_paths"]
                    target_hint = dest_paths[0].as_posix() if dest_paths else "未知"
                    print(f"未找到 {rust_symbol} 的 unimplemented!() 存根，文件：{target_hint}")

    print("填充完成。再次运行 cargo check 验证编译结果。")


if __name__ == "__main__":
    main()
