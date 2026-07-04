import json
import subprocess
import os
import re
import tempfile


def _strip_c_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    return text


def _normalize_definition(text, max_len=1200):
    if not text:
        return ""
    text = _strip_c_comments(text)
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip() + " /* truncated */"
    return text


def _should_keep_symbol(name, definition):
    if not name or not definition:
        return False
    # Drop low-signal implementation internals from system headers.
    if name.startswith("__"):
        return False
    return True


def _store_symbol(target_dict, name, definition):
    normalized = _normalize_definition(definition)
    if _should_keep_symbol(name, normalized):
        target_dict[name] = normalized

def generate_ctags(c_file, tags_file='tags.json'):
    # 如果标签文件已经存在，删除它
    if os.path.exists(tags_file):
        os.remove(tags_file)
    
    # 生成 ctags 标签文件
    subprocess.run([
        'ctags',
        '--c-kinds=+pxd',
        '--fields=+S',
        '--extras=+q',
        '--output-format=json',
        '-f',
        tags_file,
        c_file,
    ], check=True)

def find_matching_brace(content, start_pos):
    stack = []
    for i, char in enumerate(content[start_pos:], start=start_pos):
        if char == '{':
            stack.append(char)
        elif char == '}':
            if stack:
                stack.pop()
            if not stack:
                return i
    return -1

def find_struct(content, pattern):
    # ctags patterns may contain escaped delimiters; always treat as text prefix.
    text = (pattern or "").strip()
    if not text:
        return None

    if '{' in text:
        text = text.split('{', 1)[0].rstrip()
    regex = re.escape(text) + r'\s*{'

    try:
        match = re.search(regex, content)
    except re.error:
        return None
    if match:
        start_pos = match.end() - 1
        end_pos = find_matching_brace(content, start_pos)
        if end_pos != -1:
            struct_def = content[match.start():end_pos + 1]
            return struct_def + ';'
    return None


def _normalize_ctags_pattern(raw_pattern):
    pattern = (raw_pattern or "").strip()
    if not pattern:
        return ""

    # ctags JSON usually wraps regex in /.../ or /^...$/
    if pattern.startswith('/^'):
        pattern = pattern[2:]
    elif pattern.startswith('/'):
        pattern = pattern[1:]

    if pattern.endswith('$/'):
        pattern = pattern[:-2]
    elif pattern.endswith('/'):
        pattern = pattern[:-1]

    # Unescape ctags delimiter and common escaped metacharacters to plain text.
    pattern = pattern.replace(r'\/', '/')
    pattern = pattern.replace(r'\{', '{').replace(r'\}', '}')
    pattern = pattern.replace(r'\(', '(').replace(r'\)', ')')
    pattern = pattern.replace(r'\[', '[').replace(r'\]', ']')
    pattern = pattern.replace(r'\*', '*').replace(r'\+', '+').replace(r'\?', '?')
    pattern = pattern.replace(r'\.', '.')
    return pattern


def parse_ctags_json(filename, c_file):
    structs = {}
    globals = {}
    macros = {}
    typedefs = {}
    enums = {}

    if not os.path.exists(filename):
        return structs, globals, macros, typedefs, enums

    with open(c_file, 'r') as f:
        content = f.read()

    with open(filename, 'r') as f:
        for line in f:
            try:
                tag = json.loads(line)
            except json.JSONDecodeError:
                continue
            if 'kind' not in tag:
                continue
            pattern = _normalize_ctags_pattern(tag.get('pattern', ''))
            variable_name = tag.get('name', '')
            
            if tag['kind'] == 'struct':
                struct_def = find_struct(content,pattern)
                if struct_def:
                    _store_symbol(structs, variable_name, struct_def)
            elif tag['kind'] == 'variable':
                if pattern.endswith(';'):
                    _store_symbol(globals, variable_name, pattern)
                else:
                    match = re.search(re.escape(pattern) + r'[^;]*;', content)
                    if match:
                        _store_symbol(globals, variable_name, match.group(0))
            elif tag['kind'] == 'macro':
                match = re.search(re.escape(pattern) + r'.*', content)
                if match:
                    _store_symbol(macros, variable_name, match.group(0))
            elif tag['kind'] == 'typedef':
                if pattern.endswith(';'):
                    _store_symbol(typedefs, variable_name, pattern)
                else:
                    match = re.search(re.escape(pattern) + r'[^;]*;', content)
                    if match:
                        _store_symbol(typedefs, variable_name, match.group(0))
            elif tag['kind'] == 'enum':
                    matches = re.findall(re.escape(pattern) + r'[^;]*;', content)
                    for match in matches:
                        _store_symbol(enums, variable_name, match)

    return structs, globals, macros, typedefs, enums

def extract_info_from_c_file(c_file):
    fd, tags_file = tempfile.mkstemp(prefix='ctags_', suffix='.json')
    os.close(fd)

    try:
        generate_ctags(c_file, tags_file)
        structs, globals, macros, typedefs, enums = parse_ctags_json(tags_file, c_file)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""
    finally:
        if os.path.exists(tags_file):
            os.remove(tags_file)

    merged = {**structs, **globals, **macros, **typedefs, **enums}
    merged = {k: merged[k] for k in sorted(merged.keys())}
    return repr(merged).encode("ascii", "ignore").decode("ascii")
    # return f"Names: {variable_names}\n\nGlobals: {globals}\n\nMacros: {macros}\n\nEnums: {enums} \n\n"

if __name__ == '__main__':
    # 示例用法
    c_file = '/home/mins01/Test_decompose/tmp/src/set.c'
    
    # 提取信息
    result = extract_info_from_c_file(c_file)
    
    # 打印结果
    print(result)