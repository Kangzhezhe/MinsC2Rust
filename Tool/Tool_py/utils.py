import ast
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from collections import deque
from dataclasses import dataclass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, "func_result")))


def _is_ident_char(ch):
    return ch.isalnum() or ch == "_"


def _iter_identifiers(text):
    buf = []
    out = []
    for ch in text:
        if _is_ident_char(ch):
            buf.append(ch)
        elif buf:
            out.append("".join(buf))
            buf = []
    if buf:
        out.append("".join(buf))
    return out


def _collapse_whitespace(text):
    return " ".join((text or "").split())


def _extract_fn_name_from_signature_line(line):
    tokens = _iter_identifiers(line)
    if not tokens:
        return ""

    i = 0
    if i < len(tokens) and tokens[i] == "pub":
        i += 1

    while i < len(tokens):
        token = tokens[i]
        if token in {"async", "unsafe", "const"}:
            i += 1
            continue
        if token == "extern":
            i += 1
            if i < len(tokens) and tokens[i] != "fn":
                i += 1
            continue
        if token == "fn":
            if i + 1 < len(tokens):
                name = tokens[i + 1]
                return name if name.isidentifier() else ""
            return ""
        return ""
    return ""


def _extract_error_codes(stderr):
    codes = set()
    text = stderr or ""
    marker = "error["
    i = 0
    while True:
        start = text.find(marker, i)
        if start == -1:
            break
        end = text.find("]", start + len(marker))
        if end == -1:
            break
        code = text[start + len(marker) : end].strip()
        if code:
            codes.add(f"error[{code}]")
        i = end + 1
    return codes


def _replace_timeout_attrs(content, new_timeout):
    text = content or ""
    target = "#[timeout("
    i = 0
    out = []
    while i < len(text):
        start = text.find(target, i)
        if start == -1:
            out.append(text[i:])
            break
        out.append(text[i:start])
        j = start + len(target)
        k = j
        while k < len(text) and text[k].isdigit():
            k += 1
        if k > j and k + 1 < len(text) and text[k] == ")" and text[k + 1] == "]":
            out.append(f"#[timeout({new_timeout})]")
            i = k + 2
            continue
        out.append(text[start : start + len(target)])
        i = start + len(target)
    return "".join(out)


def find_elements(list1, list2):
    """
    在两个列表中查找交集元素。

    参数:
        list1 (list): 第一个列表。
        list2 (list): 第二个列表。

    返回:
        list: 包含两个列表中共有元素的列表。
    """
    set2 = set(list2)
    return [element for element in list1 if element in set2]

def extract_rust_code(text):
    if not text:
        return None
    start = text.find("```rust")
    if start == -1:
        return None
    content_start = start + len("```rust")
    end = text.find("```", content_start)
    if end == -1:
        return None
    block = text[content_start:end].strip()
    if block:
        return block
    return None


def normalize_rust_module_name(source_name):
    """Convert arbitrary source names to valid Rust module names."""
    normalized_chars = []
    for ch in source_name:
        if ch.isalnum() or ch == "_":
            normalized_chars.append(ch)
        else:
            normalized_chars.append("_")
    normalized = "".join(normalized_chars)
    if not normalized:
        normalized = "module"
    if normalized[0].isdigit():
        normalized = f"m_{normalized}"
    return normalized


@dataclass
class RustFunctionSpan:
    name: str
    start: int
    end: int
    code: str


@dataclass
class RustSplitResult:
    non_function_content: str
    function_content_dict: dict
    output_content: str
    ast_ok: bool
    fallback_used: bool
    diagnostic: str = ""


_AST_SPLIT_CACHE = {}
_AST_SPLIT_CACHE_LOCK = threading.Lock()
_RUST_AST_BIN = None
_RUST_AST_BIN_LOCK = threading.Lock()


def _normalize_non_function_item_key(item_type, item_name, code_block):
    kind = _collapse_whitespace(item_type or "")
    name = _collapse_whitespace(item_name or "")
    code = _collapse_whitespace(code_block or "")

    if kind == "Use":
        return f"Use:{code}"
    if kind and name:
        return f"{kind}:{name}:{code}"
    if kind:
        return f"{kind}:{code}"
    return code


def _dedupe_non_function_items_from_ast(item_spans):
    ordered_blocks = []
    index_by_key = {}

    for item_type, item_name, start_line, code_block in item_spans:
        _ = start_line
        block = (code_block or "").strip()
        if not block:
            continue
        key = _normalize_non_function_item_key(item_type, item_name, block)
        if not key:
            continue
        if key in index_by_key:
            ordered_blocks[index_by_key[key]] = block
        else:
            index_by_key[key] = len(ordered_blocks)
            ordered_blocks.append(block)

    return "\n\n".join(block for block in ordered_blocks if block).strip()


def _rust_ast_project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, "rust_ast_project"))


def _resolve_rust_ast_binary():
    env_bin = os.getenv("RUST_AST_BIN", "").strip()
    if env_bin and os.path.exists(env_bin):
        return env_bin

    root = _rust_ast_project_root()
    candidates = [
        os.path.join(root, "target", "release", "test_project"),
        os.path.join(root, "target", "debug", "test_project"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    try:
        subprocess.run(
            ["cargo", "build", "--manifest-path", os.path.join(root, "Cargo.toml"), "--quiet"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
    except Exception:
        return ""

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return ""


def _get_rust_ast_binary():
    global _RUST_AST_BIN
    if _RUST_AST_BIN:
        return _RUST_AST_BIN

    with _RUST_AST_BIN_LOCK:
        if _RUST_AST_BIN:
            return _RUST_AST_BIN
        _RUST_AST_BIN = _resolve_rust_ast_binary()
        return _RUST_AST_BIN


def _split_rust_code_with_syn_ast(code, tmp_dir=None):
    """Split Rust code by top-level item spans reported by syn parser."""
    parser_bin = _get_rust_ast_binary()
    if not parser_bin:
        return None

    cleaned = remove_markdown_code_block(code)
    digest = hashlib.sha256(cleaned.encode("utf-8", errors="ignore")).hexdigest()

    with _AST_SPLIT_CACHE_LOCK:
        cached = _AST_SPLIT_CACHE.get(digest)
        if cached is not None:
            return cached

    work_dir = None
    created_tmp = False
    try:
        if tmp_dir:
            work_dir = os.path.abspath(tmp_dir)
            os.makedirs(work_dir, exist_ok=True)
        else:
            work_dir = tempfile.mkdtemp(prefix="rust_ast_split_")
            created_tmp = True

        src_path = os.path.join(work_dir, f"ast_input_{digest[:12]}.rs")
        out_path = os.path.join(work_dir, f"ast_defs_{digest[:12]}.json")

        with open(src_path, "w", encoding="utf-8") as f:
            f.write(cleaned)

        proc = subprocess.run(
            [parser_bin, src_path, out_path],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0 or not os.path.exists(out_path):
            return None

        with open(out_path, "r", encoding="utf-8") as f:
            defs = json.load(f)

        lines = cleaned.splitlines(keepends=True)
        total_lines = len(lines)
        if total_lines == 0:
            result = ("", {}, "")
            with _AST_SPLIT_CACHE_LOCK:
                _AST_SPLIT_CACHE[digest] = result
            return result

        function_spans = []
        non_function_spans = []
        seen_function_names = set()
        covered_all = [False] * total_lines
        for item in defs:
            item_type = item.get("type", "")
            name = item.get("name", "")
            try:
                start_line = int(item.get("start_line", 0))
                end_line = int(item.get("end_line", 0))
            except Exception:
                continue
            if start_line <= 0 or end_line <= 0:
                continue
            start_line = max(1, min(start_line, total_lines))
            end_line = max(start_line, min(end_line, total_lines))

            code_block = "".join(lines[start_line - 1:end_line]).strip()
            if not code_block:
                continue

            for idx in range(start_line - 1, end_line):
                covered_all[idx] = True

            if item_type == "Function":
                if not name:
                    continue
                if name in seen_function_names:
                    # `results.json` stores functions by name, so duplicate
                    # cfg-gated variants cannot both be represented in the
                    # function map. Preserve later variants in extra text so
                    # round-trip export does not silently lose valid Rust.
                    non_function_spans.append(("FunctionDuplicate", name, start_line, code_block))
                    continue
                seen_function_names.add(name)
                function_spans.append((name, start_line, end_line, code_block))
            else:
                non_function_spans.append((item_type, name, start_line, code_block))

        if not function_spans and not non_function_spans:
            return None

        dedup = {}
        for name, start_line, end_line, code_block in function_spans:
            dedup[name] = (start_line, code_block)

        ordered_names = sorted(dedup.keys(), key=lambda n: dedup[n][0])
        function_content_dict = {name: dedup[name][1] for name in ordered_names}

        non_function_content = _dedupe_non_function_items_from_ast(
            sorted(non_function_spans, key=lambda item: item[2])
        )
        leftover_text = "".join(
            line for idx, line in enumerate(lines) if not covered_all[idx]
        ).strip()
        if leftover_text:
            if non_function_content:
                non_function_content = f"{leftover_text}\n\n{non_function_content}".strip()
            else:
                non_function_content = leftover_text
        if non_function_content:
            non_function_content += "\n"

        output_content = non_function_content + "\n".join(function_content_dict.values())
        result = (non_function_content, function_content_dict, output_content)

        with _AST_SPLIT_CACHE_LOCK:
            # Keep cache bounded for long-running pipelines.
            if len(_AST_SPLIT_CACHE) > 2048:
                _AST_SPLIT_CACHE.clear()
            _AST_SPLIT_CACHE[digest] = result
        return result
    except Exception:
        return None
    finally:
        if created_tmp and work_dir and os.path.exists(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)


def dedupe_non_function_content(non_function_content, tmp_dir=None):
    text = (non_function_content or "").strip()
    if not text:
        return ""

    ast_split = _split_rust_code_with_syn_ast(text, tmp_dir=tmp_dir)
    if ast_split is not None:
        normalized = (ast_split[0] or "").strip()
        if normalized:
            return normalized + "\n"
        return ""

    return text + "\n"


def _mask_non_code_regions(text):
    """
    Replace chars in comments/strings/chars with spaces while preserving length.
    This allows lexical scans on executable/code-only regions.
    """
    chars = list(text)
    i = 0
    n = len(chars)
    state = "code"
    block_depth = 0

    while i < n:
        c = chars[i]
        nxt = chars[i + 1] if i + 1 < n else ""

        if state == "code":
            if c == "/" and nxt == "/":
                chars[i] = " "
                chars[i + 1] = " "
                i += 2
                state = "line_comment"
                continue
            if c == "/" and nxt == "*":
                chars[i] = " "
                chars[i + 1] = " "
                i += 2
                state = "block_comment"
                block_depth = 1
                continue
            if c == '"':
                chars[i] = " "
                i += 1
                state = "string"
                continue
            if c == "'":
                # Rust lifetime markers like `'a` / `'static` are not char literals.
                # Keep them in code stream so function signatures are not truncated.
                after = chars[i + 1] if i + 1 < n else ""
                after2 = chars[i + 2] if i + 2 < n else ""
                if (after.isalpha() or after == "_") and after2 != "'":
                    i += 1
                    continue
                chars[i] = " "
                i += 1
                state = "char"
                continue
            i += 1
            continue

        if state == "line_comment":
            if c != "\n":
                chars[i] = " "
            else:
                state = "code"
            i += 1
            continue

        if state == "block_comment":
            if c == "/" and nxt == "*":
                chars[i] = " "
                chars[i + 1] = " "
                block_depth += 1
                i += 2
                continue
            if c == "*" and nxt == "/":
                chars[i] = " "
                chars[i + 1] = " "
                block_depth -= 1
                i += 2
                if block_depth == 0:
                    state = "code"
                continue
            if c != "\n":
                chars[i] = " "
            i += 1
            continue

        if state == "string":
            if c == "\\":
                chars[i] = " "
                if i + 1 < n:
                    chars[i + 1] = " "
                i += 2
                continue
            chars[i] = " " if c != "\n" else "\n"
            if c == '"':
                state = "code"
            i += 1
            continue

        if state == "char":
            if c == "\\":
                chars[i] = " "
                if i + 1 < n:
                    chars[i + 1] = " "
                i += 2
                continue
            chars[i] = " " if c != "\n" else "\n"
            if c == "'":
                state = "code"
            i += 1
            continue

    return "".join(chars)


def _find_matching_brace(masked, open_index):
    depth = 0
    for idx in range(open_index, len(masked)):
        ch = masked[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return idx
    return -1


def _compute_brace_depth(masked):
    """
    Compute brace nesting depth at each character index.
    depth_at[i] is the depth before reading masked[i].
    """
    depth_at = [0] * (len(masked) + 1)
    depth = 0
    for idx, ch in enumerate(masked):
        depth_at[idx] = depth
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(depth - 1, 0)
    depth_at[len(masked)] = depth
    return depth_at


def is_rust_snippet_brace_balanced(code):
    """Return True when braces are balanced outside comments/strings."""
    masked = _mask_non_code_regions(remove_markdown_code_block(code))
    depth = 0
    for ch in masked:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def extract_rust_functions(code):
    """
    Extract Rust function definitions from source text using brace matching.
    Returns last occurrence for duplicated function names.
    """
    cleaned = remove_markdown_code_block(code)
    masked = _mask_non_code_regions(cleaned)
    brace_depth_at = _compute_brace_depth(masked)
    spans = []

    line_start = 0
    while line_start < len(masked):
        line_end = masked.find("\n", line_start)
        if line_end == -1:
            line_end = len(masked)
        raw_line = masked[line_start:line_end]
        stripped = raw_line.lstrip()

        if not stripped:
            line_start = line_end + 1
            continue

        # Keep only top-level functions to avoid extracting nested local fns.
        if brace_depth_at[line_start] != 0:
            line_start = line_end + 1
            continue

        name = _extract_fn_name_from_signature_line(stripped)
        if not name:
            line_start = line_end + 1
            continue

        search_start = line_start
        open_brace = masked.find("{", search_start)
        if open_brace == -1:
            line_start = line_end + 1
            continue

        semicolon = masked.find(";", search_start, open_brace)
        if semicolon != -1:
            # Declaration / signature only.
            line_start = line_end + 1
            continue

        close_brace = _find_matching_brace(masked, open_brace)
        if close_brace == -1:
            line_start = line_end + 1
            continue

        prior_newline = cleaned.rfind("\n", 0, line_start)
        start_idx = 0 if prior_newline == -1 else prior_newline + 1
        end_idx = close_brace + 1
        fn_code = cleaned[start_idx:end_idx].strip()
        spans.append(RustFunctionSpan(name=name, start=start_idx, end=end_idx, code=fn_code))

        line_start = line_end + 1

    # Keep last definition if duplicated.
    fn_dict = {}
    dedup_spans = {}
    for span in spans:
        fn_dict[span.name] = span.code
        dedup_spans[span.name] = span

    ordered_names = sorted(dedup_spans.keys(), key=lambda name: dedup_spans[name].start)
    ordered_spans = [dedup_spans[name] for name in ordered_names]
    return fn_dict, ordered_spans


def extract_non_function_content(code, spans):
    cleaned = remove_markdown_code_block(code)
    if not spans:
        return cleaned.strip()

    fragments = []
    cursor = 0
    for span in sorted(spans, key=lambda item: item.start):
        if span.start > cursor:
            fragments.append(cleaned[cursor:span.start])
        cursor = max(cursor, span.end)
    if cursor < len(cleaned):
        fragments.append(cleaned[cursor:])
    return "\n".join(fragment.strip("\n") for fragment in fragments if fragment.strip()).strip()

def extract_related_items(source_str, target_str,names_list,not_found = False,exlude_str = ""):
    """
    从 source_str 中提取关键字，并在 target_str 中查找包含这些关键字的相关子串。

    参数:
        source_str (str): 包含关键字的源字符串。
        target_str (str): 需要匹配关键字的目标字典

    返回:
        list: 包含所有相关子串的列表（去重）。
    """
    try:
        converted_dict = ast.literal_eval(target_str)
    except (SyntaxError, ValueError):
        print("Error: Invalid string format for conversion.")
        converted_dict = {}

    not_found_keywords = ['not found', 'in this scope', 'not bound', 'cannot find', 'undeclared', 'undefined','error[E0425]','error[E0408]']
    
    for keyword in not_found_keywords:
        if keyword in source_str:
            not_found = True
            break

    if  not_found:
        not_found_vars = _iter_identifiers(source_str)
        keywords = {var for var in not_found_vars if var in names_list}

        excluded_vars = _iter_identifiers(exlude_str)
        excluded_keywords = {var for var in excluded_vars if var in names_list}

        filtered_keywords = [k for k in names_list if k in keywords and k not in excluded_keywords]
        if not filtered_keywords:
            return ""

        # Expand declaration context as a syntax-driven dependency closure.
        # No name-shape heuristics are used; relationships come from declaration text only.
        decl_keys = {k for k in converted_dict.keys() if isinstance(k, str)}
        decl_refs = {k: set() for k in decl_keys}

        for key, decl_text in converted_dict.items():
            if key not in decl_refs:
                continue
            text = decl_text if isinstance(decl_text, str) else ""

            # Direct textual references to other known declaration symbols.
            for token in _iter_identifiers(text):
                if token in decl_keys and token != key:
                    decl_refs[key].add(token)

            # Explicit typedef tag/alias coupling, e.g.:
            # typedef struct Tag Alias;
            for raw_line in text.splitlines():
                line_tokens = _iter_identifiers(raw_line)
                if len(line_tokens) < 4:
                    continue
                if line_tokens[0] != "typedef":
                    continue
                if line_tokens[1] not in {"struct", "enum", "union"}:
                    continue

                tag_name = line_tokens[2]
                alias_name = line_tokens[3]
                if tag_name in decl_keys and alias_name in decl_keys:
                    decl_refs[tag_name].add(alias_name)
                    decl_refs[alias_name].add(tag_name)

        selected_keys = set()
        pending = list(filtered_keywords)

        while pending:
            keyword = pending.pop(0)
            if keyword in selected_keys:
                continue
            if keyword not in converted_dict:
                continue
            if keyword in excluded_keywords:
                continue

            selected_keys.add(keyword)
            for dep in decl_refs.get(keyword, set()):
                if dep not in selected_keys and dep not in excluded_keywords:
                    pending.append(dep)

        # Keep output deterministic and close to names_list priority.
        key_rank = {name: idx for idx, name in enumerate(names_list)}
        ordered_keys = sorted(selected_keys, key=lambda x: (key_rank.get(x, 10**9), x))

        related_items = []
        seen_values = set()
        for key in ordered_keys:
            value = converted_dict.get(key, "")
            if not value or value in seen_values:
                continue
            seen_values.add(value)
            related_items.append(value)

        return "\n".join(related_items)

    else:    
        return ""

def decompose_project(data_manager, tmp_dir, ouput_dir):
    pass

def compile_all_files(all_files, results_copy, tmp_dir, data_manager):
    compile_error2 = ''
    for file in all_files:
        all_child_files = [file]
        data_manager.get_all_source(file, all_child_files)
        if not data_manager.has_test:
            all_child_files = all_files

        all_function_lines = '\n'.join(
            value
            for file, source in results_copy.items()
            if file in all_child_files
            for key, value in source.items()
            if key != 'extra'
        )

        if 'fn main()' not in all_function_lines:
            all_function_lines += '\nfn main(){}'
        output_content = all_function_lines

        for source in all_child_files:
            if 'extra' in results_copy.get(source, []):
                output_content = results_copy[source]['extra'] + '\n' + output_content

        with open(os.path.join(tmp_dir, 'test_source.rs'), 'w') as f:
            f.write(output_content)

        
        compile_error2 = run_command(f"rustc -Awarnings {os.path.join(tmp_dir, 'test_source.rs')}")

        delete_file_if_exists('test_source')
        if compile_error2:
            break

    return compile_error2

def has_generic_parameters(function_str):
    if not function_str:
        return False
    head = function_str.split("{", 1)[0]
    fn_idx = head.find("pub fn")
    if fn_idx == -1:
        return False
    paren_idx = head.find("(", fn_idx)
    if paren_idx == -1:
        return False
    lt_idx = head.find("<", fn_idx, paren_idx)
    if lt_idx == -1:
        return False
    gt_idx = head.find(">", lt_idx, paren_idx)
    return gt_idx != -1

def cleanup(tmp_dir):
    rm_tmp_dir = os.path.abspath(tmp_dir)
    def handler(sig, frame):
        print("Caught signal, cleaning up...")
        if os.path.exists(rm_tmp_dir):
            shutil.rmtree(rm_tmp_dir)
        sys.exit(0)
    return handler

def debug(*args, **kwargs):
    if 'DEBUG' in os.environ:
        print(*args, **kwargs)

def update_nested_dict(original, updates):
    for key, sub_dict in updates.items():
        if key in original:
            original[key].update(sub_dict)
        else:
            original[key] = sub_dict

def run_command(command,check=True):
    try:
        result = subprocess.run(command, shell=True, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # print("Command output:", result.stdout)
        # print("Command error (if any):", result.stderr)
        return result.stdout
    except subprocess.CalledProcessError as e:
        # print(f"Command '{command}' failed with error: {e.stderr}")
        return e.stderr

def filter_toolchain_errors(compile_error):
    if not compile_error:
        return ""
    kept = []
    for line in compile_error.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(":::"):
            continue
        if stripped.startswith("help:"):
            continue
        kept.append(line)
    return "\n".join(kept)

def run_command_rustc(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Command output:", result.stdout)
        print("Command error (if any):", result.stderr)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command '{command}' failed with error: {e.stderr}")
        explanations = explain_errors(e.stderr)
        print(explanations)
        return e.stderr + explanations

def explain_errors(stderr, max_length=1000):
    explanations = ""
    # 提取错误代码
    error_codes = _extract_error_codes(stderr)
    for error_code in error_codes:
        code = error_code.strip("error[]")
        explain_command = f"rustc --explain {code}"
        try:
            result = subprocess.run(explain_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            explanation = result.stdout
            # 截断解释内容
            if len(explanation) > max_length:
                explanation = explanation[:max_length] + '... [truncated]'
            explanations += f"\nExplanation for {error_code}:\n{explanation}"
        except subprocess.CalledProcessError as e:
            explanations += f"\nFailed to explain error '{error_code}': {e.stderr}"
    return explanations


def remove_markdown_code_block(text):
    if not text:
        return text
    lines = []
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            continue
        lines.append(line.replace("```", ""))
    return "".join(lines)

def traverse_dir(dir_path, header_files, source_files):
    for root, _, files in os.walk(dir_path):
        for file in files:
            path = os.path.join(root, file)
            if file.endswith(".h"):
                with open(path, 'r') as f:
                    header_files[file] = f.read()
            elif file.endswith(".c"):
                with open(path, 'r') as f:
                    source_files[file] = f.read()

def get_filename(filepath):
    """
    获取文件名并去除后缀
    :param filepath: 文件路径
    :return: 去除后缀的文件名
    """
    filename = os.path.basename(filepath)
    filename_without_extension = os.path.splitext(filename)[0]
    return filename_without_extension


def get_functions_by_line_numbers(definitions, line_numbers):
    function_names = set()
    for line in line_numbers:
        line = int(line)
        for func in definitions:
            if func['start_line'] <= line <= func['end_line']:
                function_names.add(func['name'])
    return function_names


def remove_comments_and_whitespace(text):
    if not text:
        return ""
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if ch == "/" and nxt == "/":
            i += 2
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        if ch not in {" ", "\n", "\t", "\r"}:
            out.append(ch)
        i += 1
    return "".join(out)


def get_output_content(non_function_content, function_content_dict):
    output_content = non_function_content + '\n' + '\n'.join(function_content_dict.values())
    return output_content

def parse_and_deduplicate_errors(error_str):
    if not error_str:
        return ""

    error_dict = {}
    current_header = ""
    for line in error_str.splitlines():
        stripped = line.strip()
        if stripped.startswith("error[") and "]:" in stripped:
            current_header = stripped
            if current_header not in error_dict:
                error_dict[current_header] = ""
            continue
        if current_header:
            if error_dict[current_header]:
                error_dict[current_header] += "\n"
            error_dict[current_header] += line

    unique_errors = [header for header in error_dict.keys()]
    return "\n\n".join(unique_errors)

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


def _split_rust_code_with_lexical_fallback(all_function_lines):
    function_content_dict, spans = extract_rust_functions(all_function_lines)
    non_function_content = extract_non_function_content(all_function_lines, spans)
    if non_function_content:
        non_function_content += "\n"
    output_content = non_function_content + "\n".join(function_content_dict.values())
    return non_function_content, function_content_dict, output_content


def split_rust_code_structural(all_function_lines, tmp_dir=None):
    """
    Split Rust source into non-function content and function map with metadata.

    The legacy `deduplicate_code` API returns only the split tuple. This richer
    API lets writeback paths distinguish a successful syn AST split from the
    heuristic fallback, so they can avoid extra lossy sanitization and count
    fallback use in reports.
    """
    ast_split = _split_rust_code_with_syn_ast(all_function_lines, tmp_dir=tmp_dir)
    if ast_split is not None:
        non_function_content, function_content_dict, output_content = ast_split
        return RustSplitResult(
            non_function_content=non_function_content,
            function_content_dict=function_content_dict,
            output_content=output_content,
            ast_ok=True,
            fallback_used=False,
        )

    non_function_content, function_content_dict, output_content = _split_rust_code_with_lexical_fallback(
        all_function_lines
    )
    return RustSplitResult(
        non_function_content=non_function_content,
        function_content_dict=function_content_dict,
        output_content=output_content,
        ast_ok=False,
        fallback_used=True,
        diagnostic="syn AST split failed; used lexical fallback",
    )


def deduplicate_code(all_function_lines, tmp_dir=None):
    """
    Split Rust source into non-function content and function map.
    Prefer syn AST parser for structural robustness; fallback to lexer split on parser failure.
    """
    split = split_rust_code_structural(all_function_lines, tmp_dir=tmp_dir)
    return split.non_function_content, split.function_content_dict, split.output_content

def clean_and_validate_json(output):
    if output is None:
        return None

    # 去除不可见字符
    output = "".join(ch for ch in str(output) if (32 <= ord(ch) < 127) or ch in {"\n", "\t", " "})
    output = _collapse_whitespace(output)

    # 将单引号替换为双引号
    output = output.replace("'", '"')

    try:
        json_obj = json.loads(output)
        return json_obj
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(output)
            if isinstance(parsed, (dict, list, tuple, str, int, float, bool)) or parsed is None:
                return parsed
        except Exception:
            return None
    return None


def delete_file_if_exists(file_path):
    """
    如果文件存在则删除文件。

    参数:
    file_path (str): 要删除的文件路径。
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
    except Exception as e:
        print(f"An error occurred while trying to delete the file {file_path}: {e}")

def update_test_timeout(file_path, new_timeout):
    if os.path.isdir(file_path):
        for root, _, files in os.walk(file_path):
            for file in files:
                file_full_path = os.path.join(root, file)
                update_test_timeout_in_file(file_full_path, new_timeout)
    else:
        update_test_timeout_in_file(file_path, new_timeout)

def update_test_timeout_in_file(file_path, new_timeout):
    with open(file_path, 'r') as file:
        content = file.read()

    updated_content = _replace_timeout_attrs(content, new_timeout)

    with open(file_path, 'w') as file:
        file.write(updated_content)

    # print(f"Updated timeouts in {file_path} to {new_timeout} milliseconds.")
