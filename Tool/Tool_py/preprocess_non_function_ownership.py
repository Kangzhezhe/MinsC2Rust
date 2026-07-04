import argparse
import ast
import json
import os
import re
import shlex
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from parse_config import configure_llm_env, read_config

try:
    from clang import cindex
except Exception:
    cindex = None


STYLE_PROFILE_ID = "rust_safe_idiomatic_unified_v1"


@dataclass
class SourceExtraContext:
    source_name: str
    source_kind: str
    json_path: str
    decl_map: Dict[str, str]
    extract_info: str


def _clip_text(text: str, max_chars: int) -> str:
    raw = str(text or "")
    if len(raw) <= max_chars:
        return raw
    return raw[: max_chars - 14] + "\n...(truncated)"


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}
    return data


def _parse_extra_field(extra_text: str) -> Tuple[Dict[str, str], str]:
    raw = str(extra_text or "").strip()
    if not raw:
        return {}, ""

    head = raw
    tail = ""
    if " extract_info:" in raw:
        head, tail = raw.split(" extract_info:", 1)

    head = head.strip()
    tail = tail.strip()

    decl_map: Dict[str, str] = {}
    if head:
        try:
            parsed = ast.literal_eval(head)
            if isinstance(parsed, dict):
                for k, v in parsed.items():
                    if isinstance(k, str):
                        decl_map[k] = str(v)
        except Exception:
            decl_map = {}

    return decl_map, tail


def _collect_contexts(tmp_dir: str, only_sources: Optional[set] = None) -> List[SourceExtraContext]:
    contexts: List[SourceExtraContext] = []
    roots = [
        ("src", os.path.join(tmp_dir, "src_json")),
        ("test", os.path.join(tmp_dir, "test_json")),
    ]

    for source_kind, root in roots:
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(root, name)
            data = _load_json(path)
            extra_raw = str(data.get("extra", "") or "")
            decl_map, extract_info = _parse_extra_field(extra_raw)
            if not decl_map:
                continue
            source_name = os.path.splitext(name)[0]
            if only_sources is not None and source_name not in only_sources:
                continue
            contexts.append(
                SourceExtraContext(
                    source_name=source_name,
                    source_kind=source_kind,
                    json_path=path,
                    decl_map=decl_map,
                    extract_info=extract_info,
                )
            )

    return contexts


def _resolve_path_from_config(config_path: str, raw_path: str) -> str:
    path = str(raw_path or "").strip()
    if not path:
        return ""
    if os.path.isabs(path):
        return os.path.abspath(path)

    cfg_dir = os.path.abspath(os.path.dirname(config_path))
    tool_py_root = os.path.abspath(os.path.join(cfg_dir, os.pardir))
    candidates = [
        os.path.abspath(path),
        os.path.abspath(os.path.join(tool_py_root, path)),
        os.path.abspath(os.path.join(cfg_dir, path)),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[1]


def _derive_default_workspace_root(candidates: List[str]) -> str:
    existing = [os.path.abspath(p) for p in candidates if p and os.path.exists(p)]
    if not existing:
        return os.path.abspath(os.getcwd())
    if len(existing) == 1:
        only = existing[0]
        return only if os.path.isdir(only) else os.path.dirname(only)
    try:
        root = os.path.commonpath(existing)
    except Exception:
        root = os.path.dirname(existing[0])
    if os.path.isfile(root):
        root = os.path.dirname(root)
    return os.path.abspath(root)


def _extract_struct_field_decls(decl: str) -> List[Tuple[str, str]]:
    text = str(decl or "")
    m = re.search(r"\{(.*)\}", text, flags=re.DOTALL)
    if not m:
        return []
    body = m.group(1)
    items: List[Tuple[str, str]] = []
    for raw in body.split(";"):
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"/\*.*?\*/", "", line)
        line = re.sub(r"//.*$", "", line).strip()
        if not line:
            continue
        m_name = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[[^\]]*\])?$", line)
        if not m_name:
            continue
        items.append((m_name.group(1), line))
    return items


def _resolve_struct_decl(symbol: str, decl: str, decl_map: Dict[str, str]) -> Tuple[str, bool]:
    text = str(decl or "")
    if "struct" in text and "{" in text:
        return text, True

    m_alias = re.match(r"\s*typedef\s+struct\s+([A-Za-z_][A-Za-z0-9_]*)\s+" + re.escape(symbol) + r"\s*;", text)
    if m_alias:
        body_name = m_alias.group(1)
        body_decl = str(decl_map.get(body_name, "") or "")
        if body_decl and "struct" in body_decl and "{" in body_decl:
            return body_decl, True

    return text, False


def _iter_cursor_tree(root: "cindex.Cursor") -> List["cindex.Cursor"]:
    stack = [root]
    result: List["cindex.Cursor"] = []
    while stack:
        node = stack.pop()
        result.append(node)
        stack.extend(list(node.get_children()))
    return result


def _callee_name_from_call(node: "cindex.Cursor") -> str:
    name = (node.spelling or "").strip()
    if name:
        return name
    for child in node.get_children():
        if child.spelling:
            return child.spelling
    return ""


def _field_name_from_expr(node: "cindex.Cursor") -> str:
    if node.kind == cindex.CursorKind.MEMBER_REF_EXPR:
        return (node.spelling or "").strip()
    for child in node.get_children():
        name = _field_name_from_expr(child)
        if name:
            return name
    return ""


def _tokens_contain(cursor: "cindex.Cursor", target: str) -> bool:
    try:
        for tok in cursor.get_tokens():
            if tok.spelling == target:
                return True
    except Exception:
        return False
    return False


def _scan_c_file_for_ownership_hints(path: str, clang_args: Optional[List[str]] = None) -> Dict[str, Dict[str, int]]:
    hints: Dict[str, Dict[str, int]] = {}
    if cindex is None:
        return hints

    args = ["-x", "c", "-std=c11"]
    if clang_args:
        args = clang_args + args

    try:
        index = cindex.Index.create()
        tu = index.parse(
            path,
            args=args,
            options=0,
        )
    except Exception:
        return hints

    for node in _iter_cursor_tree(tu.cursor):
        if node.kind == cindex.CursorKind.MEMBER_REF_EXPR:
            field = (node.spelling or "").strip()
            if field:
                entry = hints.setdefault(field, {})
                entry["total_refs"] = entry.get("total_refs", 0) + 1

        if node.kind == cindex.CursorKind.CALL_EXPR:
            callee = _callee_name_from_call(node)
            if callee == "free":
                for child in node.get_children():
                    field = _field_name_from_expr(child)
                    if field:
                        entry = hints.setdefault(field, {})
                        entry["freed"] = entry.get("freed", 0) + 1
                        break

        if node.kind == cindex.CursorKind.BINARY_OPERATOR:
            children = list(node.get_children())
            if len(children) < 2:
                continue
            lhs, rhs = children[0], children[1]
            field = _field_name_from_expr(lhs)
            if not field:
                continue
            entry = hints.setdefault(field, {})
            entry["assigned"] = entry.get("assigned", 0) + 1

            rhs_callee = ""
            for child in _iter_cursor_tree(rhs):
                if child.kind == cindex.CursorKind.CALL_EXPR:
                    rhs_callee = _callee_name_from_call(child)
                    if rhs_callee:
                        break

            if rhs_callee in {"malloc", "calloc", "realloc"}:
                entry["allocated"] = entry.get("allocated", 0) + 1
                continue

            if _tokens_contain(rhs, "NULL"):
                entry["nulled"] = entry.get("nulled", 0) + 1
                continue

            entry["borrowed_assign"] = entry.get("borrowed_assign", 0) + 1

    return hints


def _load_compile_commands(path: str) -> Dict[str, List[str]]:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    mapping: Dict[str, List[str]] = {}
    if isinstance(data, list):
        for entry in data:
            if not isinstance(entry, dict):
                continue
            file_path = str(entry.get("file", "") or "").strip()
            directory = str(entry.get("directory", "") or "").strip()
            if not file_path:
                continue
            if not os.path.isabs(file_path) and directory:
                file_path = os.path.abspath(os.path.join(directory, file_path))
            if not file_path:
                continue
            command = entry.get("command") or entry.get("arguments")
            args: List[str] = []
            if isinstance(command, str):
                args = shlex.split(command)
            elif isinstance(command, list):
                args = [str(x) for x in command]
            args = [a for a in args if a not in {"clang", "cc", "gcc"}]
            mapping[file_path] = args
    return mapping


def _resolve_compile_args(
    compile_commands: Dict[str, List[str]],
    file_path: str,
) -> List[str]:
    if file_path in compile_commands:
        return compile_commands[file_path]
    basename = os.path.basename(file_path)
    if basename:
        for key, args in compile_commands.items():
            if os.path.basename(key) == basename:
                return args
    rel_path = ""
    for root in ["/app", "/root"]:
        if file_path.startswith(root):
            rel_path = file_path[len(root) :]
            break
    if rel_path:
        for key, args in compile_commands.items():
            if key.endswith(rel_path):
                return args
    return []


def _collect_c_ownership_hints(
    roots: List[str],
    compile_commands_path: str,
) -> Dict[str, Dict[str, int]]:
    merged: Dict[str, Dict[str, int]] = {}
    compile_commands = _load_compile_commands(compile_commands_path)
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            for fname in filenames:
                if not fname.endswith((".c", ".h")):
                    continue
                fpath = os.path.join(dirpath, fname)
                args = _resolve_compile_args(compile_commands, fpath)
                hints = _scan_c_file_for_ownership_hints(fpath, args)
                for field, stats in hints.items():
                    bucket = merged.setdefault(field, {})
                    for key, value in stats.items():
                        bucket[key] = bucket.get(key, 0) + value
    return merged


def _build_context_ownership_hints(
    contexts: List[SourceExtraContext],
    c_src_dir: str,
    c_test_dir: str,
    compile_commands_path: str,
) -> Dict[str, Dict[str, Dict[str, str]]]:
    field_stats = _collect_c_ownership_hints([c_src_dir, c_test_dir], compile_commands_path)
    if not field_stats:
        return {}

    context_hints: Dict[str, Dict[str, Dict[str, str]]] = {}
    for ctx in contexts:
        module_hints: Dict[str, Dict[str, str]] = {}
        for symbol, decl in ctx.decl_map.items():
            struct_decl, struct_like = _resolve_struct_decl(symbol, decl, ctx.decl_map)
            if not struct_like:
                continue
            field_hints: Dict[str, str] = {}
            for field, _line in _extract_struct_field_decls(struct_decl):
                stats = field_stats.get(field)
                if not stats:
                    continue
                parts = []
                for key in [
                    "allocated",
                    "freed",
                    "nulled",
                    "assigned",
                    "borrowed_assign",
                    "total_refs",
                ]:
                    if stats.get(key):
                        parts.append(f"{key}={stats[key]}")
                if parts:
                    field_hints[field] = ", ".join(parts)
            if field_hints:
                module_hints[symbol] = field_hints
        if module_hints:
            context_hints[ctx.source_name] = module_hints
    return context_hints


def _extract_json_from_agent_response(text: str) -> Dict[str, Any]:
    raw = str(text or "")
    if not raw.strip():
        return {}

    for begin, end in [
        ("[SAFE_SUGGESTIONS_BEGIN]", "[SAFE_SUGGESTIONS_END]"),
        ("[OWNERSHIP_PLAN_BEGIN]", "[OWNERSHIP_PLAN_END]"),
    ]:
        marker = re.search(
            re.escape(begin) + r"(.*?)" + re.escape(end),
            raw,
            flags=re.DOTALL,
        )
        if marker:
            block = marker.group(1).strip()
            try:
                parsed = json.loads(block)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}

    fence = re.search(r"```json\s*(.*?)```", raw, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        block = fence.group(1).strip()
        try:
            parsed = json.loads(block)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _normalize_agent_items(
    parsed: Dict[str, Any],
    ctx: SourceExtraContext,
) -> Tuple[Dict[str, str], List[str]]:
    raw_items = parsed.get("items")
    if not isinstance(raw_items, list):
        raw_items = parsed.get("symbols")
    if not isinstance(raw_items, list):
        raw_items = []

    normalized: Dict[str, str] = {}
    logs: List[str] = []

    for item in raw_items:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol", "") or "").strip()
        if not symbol or symbol not in ctx.decl_map:
            continue

        decl = ctx.decl_map.get(symbol, "")
        struct_decl, struct_like = _resolve_struct_decl(symbol, decl, ctx.decl_map)
        kind = str(item.get("kind", "") or "").strip().lower()
        is_struct = kind == "struct" or struct_like

        safe_text = str(item.get("safe_text", "") or "").strip()
        if not safe_text:
            logs.append(f"missing safe_text for {ctx.source_name}::{symbol}")
            continue

        text_lines: List[str] = [safe_text]
        reason = str(item.get("reason", "") or "").strip()
        if reason:
            text_lines.append(f"理由: {reason}")

        if is_struct:
            field_decls = _extract_struct_field_decls(struct_decl)
            field_suggestions = item.get("field_suggestions", {})
            field_map: Dict[str, Any] = field_suggestions if isinstance(field_suggestions, dict) else {}
            if field_decls:
                missing_fields = []
                field_lines: List[str] = []
                for fname, _field_decl in field_decls:
                    entry = field_map.get(fname, "")
                    fmsg = ""
                    if isinstance(entry, dict):
                        ownership = str(entry.get("ownership", "") or "").strip()
                        nullable = entry.get("nullable")
                        rust_type = str(entry.get("rust_type", "") or "").strip()
                        reason_text = str(entry.get("reason", "") or "").strip()
                        parts = []
                        if rust_type:
                            parts.append(rust_type)
                        if ownership:
                            parts.append(f"ownership={ownership}")
                        if nullable is not None:
                            parts.append(f"nullable={nullable}")
                        if reason_text:
                            parts.append(f"reason={reason_text}")
                        fmsg = "; ".join(parts)
                    else:
                        fmsg = str(entry or "").strip()
                    if not fmsg:
                        missing_fields.append(fname)
                        continue
                    field_lines.append(f"- {fname}: {fmsg}")
                if missing_fields:
                    logs.append(
                        f"missing field_suggestions for {ctx.source_name}::{symbol}: {', '.join(missing_fields[:8])}"
                    )
                    continue
                if field_lines:
                    text_lines.append("字段级建议:")
                    text_lines.extend(field_lines)
            else:
                logs.append(f"struct {ctx.source_name}::{symbol} has no parsed fields")

        key = f"{ctx.source_name}::{symbol}"
        normalized[key] = "\n".join(line for line in text_lines if line.strip()).strip()

    return normalized, logs


def _load_swe_agent_class() -> Optional[type]:
    current_dir = os.path.abspath(os.path.dirname(__file__))
    candidate_roots = [
        os.path.abspath(os.path.join(current_dir, "..", "..", "MinsC2Rust_V2")),
        os.path.abspath(os.path.join(current_dir, "..", "..", "..", "MinsC2Rust_V2")),
        os.path.abspath(os.path.join(current_dir, "..", "MinsC2Rust_V2")),
    ]

    v2_root = ""
    for root in candidate_roots:
        if os.path.exists(os.path.join(root, "llm", "swe_agent.py")):
            v2_root = root
            break

    if not v2_root:
        return None

    if v2_root not in sys.path:
        sys.path.insert(0, v2_root)
    try:
        from llm.swe_agent import SWEAgent

        return SWEAgent
    except Exception:
        return None


def _analyze_with_agent(
    ctx: SourceExtraContext,
    agent: Any,
    max_decl_chars: int,
    use_tools: bool,
    c_src_dir: str,
    c_test_dir: str,
    require_tools: bool,
    pointer_only: bool,
    ownership_hints: Optional[Dict[str, Dict[str, str]]] = None,
) -> Tuple[Dict[str, str], List[str], str]:
    decl_preview = json.dumps(ctx.decl_map, ensure_ascii=False, indent=2)
    hints_text = ""
    if ownership_hints:
        hints_text = _clip_text(json.dumps(ownership_hints, ensure_ascii=False, indent=2), 2400)
    task_description = "".join(
        [
            "请基于 C 非函数声明做所有权与安全类型映射分析，并给出可执行的指针转换建议。\n",
            f"源文件标识: {ctx.source_name} ({ctx.source_kind})\n",
            f"对应 json: {ctx.json_path}\n",
            f"真实 C 源目录: {c_src_dir}\n",
            f"真实 C 测试目录: {c_test_dir}\n",
            "输入声明(字典 key 即后续索引 key 的 symbol):\n",
            _clip_text(decl_preview, max_decl_chars),
            "\n\n补充 extract_info:\n",
            _clip_text(ctx.extract_info, 2800),
            "\n\n补充 ownership_hints (from C scan):\n",
            (hints_text if hints_text else "<none>"),
            "\n\n安全类型规则(必须遵守):\n",
            "- 输出必须使用纯 Rust 安全特性：Box/Rc/Arc/Weak/Option/RefCell/Vec，不得出现 raw pointer/NonNull。\n",
            "- 所有权模型必须一致：若出现 Weak，则对应拥有者必须是 Rc；不得混用 Box + Weak。\n",
            "- 可空语义必须用 Option 包裹；树/图结构优先使用 Rc<RefCell<T>> + Weak 处理父指针。\n",
            "- void* 优先映射为泛型参数（如 K/V/T）；若无法泛化，使用 Box<dyn Any> 或 Rc<dyn Any>。\n",
            "- borrowed 语义优先用 Rc/Arc 的克隆或 &T（若可表达生命周期）。\n",
            "- 全局可变状态必须使用 Atomic* 或 Mutex/RwLock 封装，禁止裸 static mut。\n",
            "\n\n输出要求:\n",
            ("- 仅分析指针相关元素（含函数指针、void*别名、含指针字段的结构体）。\n" if pointer_only else ""),
            "0) 若 use_tools=True：必须先调用工具读取真实 C 目录中的至少一个 .c/.h 文件，再输出结果。\n",
            "1) 必须返回 [SAFE_SUGGESTIONS_BEGIN] 与 [SAFE_SUGGESTIONS_END] 包裹的 JSON。\n",
            "2) JSON 格式为 {\"items\":[...]}。\n",
            "3) items 每项必须至少包含 symbol, kind, safe_text。\n",
            "4) 如果 kind=struct，必须额外包含 field_suggestions 对象，且覆盖该结构体每个字段。\n",
            "   field_suggestions 可用结构化对象：{field:{ownership, nullable, rust_type, reason}}，也可用纯文本。\n",
            "4) 仅分析 non-function 元素，禁止输出函数实现代码。\n",
            "5) 严禁输出 shell 命令或解释过程文本；只能输出指定标记块。\n",
        ]
    )

    run_task_result: Any = {}
    run_task_result = agent.run_task(
        task_description,
        acceptance_criteria=[
            "必须输出标记块 [SAFE_SUGGESTIONS_BEGIN]...[SAFE_SUGGESTIONS_END]",
            "JSON 里的 symbol 仅来自输入声明字典 key",
            "输出只包含 non-function 的安全建议文本",
            "结构体必须提供每个字段的文本建议",
            "不要输出函数代码，不要输出命令文本",
        ],
        extra_notes="目标是供后续函数转译阶段做 key 索引，不要返回函数代码。",
        use_tools=use_tools,
    )

    final_response = ""
    tool_calls: List[Dict[str, Any]] = []
    if isinstance(run_task_result, dict):
        final_response = str(run_task_result.get("final_response", "") or "")
        raw_tool_calls = run_task_result.get("tool_calls", [])
        if isinstance(raw_tool_calls, list):
            tool_calls = raw_tool_calls

    parsed = _extract_json_from_agent_response(final_response)
    normalized, normalize_logs = _normalize_agent_items(parsed, ctx)
    summary = f"tool_calls={len(tool_calls)}"
    if require_tools and use_tools and len(tool_calls) == 0:
        return {}, normalize_logs, summary + " require_tools=1 but no tools invoked"

    if normalized:
        return normalized, normalize_logs, summary

    if use_tools and tool_calls:
        concise_tool_calls: List[Dict[str, Any]] = []
        for call in tool_calls[:8]:
            concise_tool_calls.append(
                {
                    "name": str(call.get("name", "") or ""),
                    "args": call.get("args", {}) if isinstance(call.get("args", {}), dict) else {},
                }
            )

        synth_prompt = "".join(
            [
                "你已经完成工具取证，现在只做结果整理。\n",
                "禁止调用任何工具，禁止输出解释文字。\n",
                "只输出 [SAFE_SUGGESTIONS_BEGIN]...[SAFE_SUGGESTIONS_END] 包裹的 JSON。\n",
                "JSON 顶层为 {\"items\":[...]}，且 symbol 必须来自输入声明 key。\n",
                "items 每项仅保留 symbol/kind/safe_text；若 kind=struct，必须带 field_suggestions(每个字段都有)。\n",
                "输入声明 key:\n",
                _clip_text(json.dumps(list(ctx.decl_map.keys()), ensure_ascii=False), 1200),
                "\n\n输入声明字典:\n",
                _clip_text(decl_preview, max_decl_chars),
                "\n\n阶段1工具调用摘要:\n",
                _clip_text(json.dumps(concise_tool_calls, ensure_ascii=False, indent=2), 2200),
                "\n\n阶段1回复(仅供参考):\n",
                _clip_text(final_response, 2600),
            ]
        )

        synth_result = agent.run_task(
            synth_prompt,
            acceptance_criteria=[
                "必须输出标记块 [SAFE_SUGGESTIONS_BEGIN]...[SAFE_SUGGESTIONS_END]",
                "仅输出 JSON，不输出额外文本",
            ],
            extra_notes="本轮只做结构化整理，不要工具调用。",
            use_tools=False,
        )

        synth_resp = ""
        if isinstance(synth_result, dict):
            synth_resp = str(synth_result.get("final_response", "") or "")
        synth_parsed = _extract_json_from_agent_response(synth_resp)
        synth_norm, synth_logs = _normalize_agent_items(synth_parsed, ctx)
        normalize_logs.extend(synth_logs)
        if synth_norm:
            return synth_norm, normalize_logs, summary + " synth=1"

    return {}, normalize_logs, summary + " parsed_items=0"


def _empty_guidance() -> Dict[str, Any]:
    return {
        "summary": "",
        "rules": [],
        "style_contract": {},
        "stats": {},
    }


def build_ownership_index(
    contexts: List[SourceExtraContext],
    use_agent: bool,
    workspace_root: str,
    max_iterations: int,
    command_timeout: int,
    max_decl_chars: int,
    agent_use_tools: bool,
    c_src_dir: str,
    c_test_dir: str,
    compile_commands_path: str,
    require_agent_tools: bool,
    pointer_only: bool,
) -> Dict[str, Any]:
    suggestions: Dict[str, str] = {}
    by_source: Dict[str, List[str]] = {}
    module_guidance: Dict[str, Dict[str, Any]] = {}
    logs: List[str] = []

    agent = None
    if use_agent:
        swe_agent_cls = _load_swe_agent_class()
        if swe_agent_cls is not None:
            try:
                agent = swe_agent_cls(
                    workspace_root=workspace_root,
                    logger=True,
                    max_iterations=max_iterations,
                    command_timeout=command_timeout,
                    memory_strategy={"name": "summary"},
                    enable_lsp_tools=False,
                )
                logs.append(f"[agent] ready workspace={workspace_root}")
            except Exception as exc:
                logs.append(f"[agent] init failed: {exc}")
        else:
            logs.append("[agent] SWEAgent import failed")

    ownership_hints_by_source = _build_context_ownership_hints(
        contexts,
        c_src_dir=c_src_dir,
        c_test_dir=c_test_dir,
        compile_commands_path=compile_commands_path,
    )
    if ownership_hints_by_source:
        logs.append(
            f"[ownership] scanned hints sources={len(ownership_hints_by_source)}"
        )

    for ctx in contexts:
        source_keys = by_source.setdefault(ctx.source_name, [])
        agent_items: Dict[str, str] = {}
        normalize_logs: List[str] = []
        ctx_hints = ownership_hints_by_source.get(ctx.source_name)

        if agent is not None:
            try:
                agent_items, normalize_logs, summary = _analyze_with_agent(
                    ctx,
                    agent,
                    max_decl_chars=max_decl_chars,
                    use_tools=agent_use_tools,
                    c_src_dir=c_src_dir,
                    c_test_dir=c_test_dir,
                    require_tools=require_agent_tools,
                    pointer_only=pointer_only,
                    ownership_hints=ctx_hints,
                )
                logs.append(
                    f"[agent] {ctx.source_name} analyzed symbols={len(agent_items)} {summary}".strip()
                )
            except Exception as exc:
                logs.append(f"[agent] {ctx.source_name} failed: {exc}")

        if normalize_logs:
            logs.extend(f"[normalize] {ctx.source_name} {msg}" for msg in normalize_logs)

        for symbol in ctx.decl_map.keys():
            key = f"{ctx.source_name}::{symbol}"
            item = agent_items.get(key)
            if item is None:
                continue
            suggestions[key] = str(item)
            if key not in source_keys:
                source_keys.append(key)

        module_guidance[ctx.source_name] = _empty_guidance()

    source_keys_count = sum(len(set(keys)) for keys in by_source.values())

    return {
        "meta": {
            "generated_at": int(time.time()),
            "workspace_root": workspace_root,
            "source_count": len(contexts),
            "suggestion_count": len(suggestions),
            "source_keys_count": source_keys_count,
            "module_guidance_count": len(module_guidance),
            "global_guidance_rules": 0,
            "schema_version": 2,
            "agent_enabled": bool(use_agent),
            "agent_active": bool(agent is not None),
            "agent_use_tools": bool(agent_use_tools),
            "require_agent_tools": bool(require_agent_tools),
            "pointer_only": bool(pointer_only),
            "c_src_dir": c_src_dir,
            "c_test_dir": c_test_dir,
        },
        "global_guidance": _empty_guidance(),
        "module_guidance": module_guidance,
        "symbol_suggestions": suggestions,
        "suggestions": suggestions,
        "by_source": by_source,
        "logs": logs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preprocess non-function extra elements into ownership/type-mapping index JSON."
    )
    parser.add_argument("config_path", help="Path to Tool/Tool_py config.ini")
    parser.add_argument(
        "--output",
        default="",
        help="Output file path (default: <output_dir>/ownership_non_function_index.json)",
    )
    parser.add_argument(
        "--workspace-root",
        default="",
        help="Workspace root used by SWEAgent (default: parent of tmp_dir)",
    )
    parser.add_argument("--disable-agent", action="store_true", help="Disable SWEAgent and use heuristic only")
    parser.add_argument(
        "--agent-no-tools",
        action="store_true",
        help="Run agent with use_tools=False for faster/stabler preprocessing",
    )
    parser.add_argument(
        "--allow-no-tool-agent",
        action="store_true",
        help="Do not reject agent result when no tools are invoked in use_tools mode",
    )
    parser.add_argument(
        "--only-sources",
        default="",
        help="Comma-separated source names to preprocess, e.g. bloom-filter,hash-table",
    )
    parser.add_argument(
        "--include-non-pointer",
        action="store_true",
        help="Include non-pointer symbols; default mode only analyzes pointer-related symbols",
    )
    parser.add_argument("--max-iterations", type=int, default=20, help="SWEAgent max iterations")
    parser.add_argument("--command-timeout", type=int, default=90, help="SWEAgent command timeout")
    parser.add_argument(
        "--max-decl-chars",
        type=int,
        default=6000,
        help="Max declaration chars sent to agent per source",
    )
    args = parser.parse_args()

    cfg = read_config(args.config_path)
    configure_llm_env(cfg)

    tmp_dir = _resolve_path_from_config(args.config_path, cfg["Paths"]["tmp_dir"])
    output_dir = _resolve_path_from_config(args.config_path, cfg["Paths"]["output_dir"])
    c_src_dir = _resolve_path_from_config(args.config_path, cfg["Paths"].get("src_dir", ""))
    c_test_dir = _resolve_path_from_config(args.config_path, cfg["Paths"].get("test_dir", ""))
    compile_commands_path = _resolve_path_from_config(
        args.config_path, cfg["Paths"].get("compile_commands_path", "")
    )
    out_path = args.output or os.path.join(output_dir, "ownership_non_function_index.json")

    only_sources = None
    if args.only_sources.strip():
        only_sources = {x.strip() for x in args.only_sources.split(",") if x.strip()}

    contexts = _collect_contexts(tmp_dir, only_sources=only_sources)
    if not contexts:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        empty = {
            "meta": {
                "generated_at": int(time.time()),
                "workspace_root": "",
                "source_count": 0,
                "suggestion_count": 0,
                "source_keys_count": 0,
                "module_guidance_count": 0,
                "global_guidance_rules": 0,
                "schema_version": 2,
                "agent_enabled": not args.disable_agent,
                "agent_active": False,
            },
            "global_guidance": _empty_guidance(),
            "module_guidance": {},
            "symbol_suggestions": {},
            "suggestions": {},
            "by_source": {},
            "logs": ["no extra declarations found in tmp/src_json and tmp/test_json"],
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(empty, f, ensure_ascii=False, indent=2)
        print(f"[ownership-preprocess] wrote empty index: {out_path}")
        return 0

    workspace_root = args.workspace_root or _derive_default_workspace_root(
        [tmp_dir, c_src_dir, c_test_dir]
    )
    result = build_ownership_index(
        contexts=contexts,
        use_agent=not args.disable_agent,
        workspace_root=workspace_root,
        max_iterations=args.max_iterations,
        command_timeout=args.command_timeout,
        max_decl_chars=args.max_decl_chars,
        agent_use_tools=not args.agent_no_tools,
        c_src_dir=c_src_dir,
        c_test_dir=c_test_dir,
        compile_commands_path=compile_commands_path,
        require_agent_tools=not args.allow_no_tool_agent,
        pointer_only=not args.include_non_pointer,
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(
        "[ownership-preprocess] done "
        f"sources={result['meta']['source_count']} "
        f"suggestions={result['meta']['suggestion_count']} "
        f"agent_active={int(result['meta']['agent_active'])} "
        f"output={out_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
