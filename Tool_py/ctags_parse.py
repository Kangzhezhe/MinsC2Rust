import json
import subprocess
import os
import re

def generate_ctags(c_file, tags_file='tags.json'):
    # 如果标签文件已经存在，删除它
    if os.path.exists(tags_file):
        os.remove(tags_file)
    
    # 生成 ctags 标签文件
    subprocess.run(['ctags', '-R', '--c-kinds=+pxd', '--fields=+S', '--extras=+q', '--output-format=json', '-f', tags_file, c_file], check=True)

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
    match = re.search(re.escape(pattern), content)
    if match:
        start_pos = match.end() - 1
        end_pos = find_matching_brace(content, start_pos)
        if end_pos != -1:
            struct_def = content[match.start():end_pos + 1]
            return struct_def
    return None


def parse_ctags_json(filename, c_file):
    structs = set()
    globals = set()
    macros = set()
    typedefs = set()
    enums = set()
    variable_names = set()

    with open(c_file, 'r') as f:
        content = f.read()

    with open(filename, 'r') as f:
        for line in f:
            tag = json.loads(line)
            if 'kind' not in tag:
                continue
            pattern = tag.get('pattern', '').strip('/^$/')
            if tag['kind']  in ['struct', 'variable', 'macro', 'typedef', 'enum']:
                variable_names.add(tag.get('name', ''))

            if tag['kind'] == 'struct':
                struct_def = find_struct(content,pattern)
                if struct_def:
                    structs.add(struct_def)
            elif tag['kind'] == 'variable':
                if pattern.endswith(';'):
                    globals.add(pattern)
                else:
                    match = re.search(re.escape(pattern) + r'[^;]*;', content)
                    if match:
                        globals.add(match.group(0))
            elif tag['kind'] == 'macro':
                match = re.search(re.escape(pattern) + r'.*', content)
                if match:
                    macros.add(match.group(0))
            elif tag['kind'] == 'typedef':
                if pattern.endswith(';'):
                    typedefs.add(pattern)
                else:
                    match = re.search(re.escape(pattern) + r'[^;]*;', content)
                    if match:
                        typedefs.add(match.group(0))
            elif tag['kind'] == 'enum':
                    matches = re.findall(re.escape(pattern) + r'[^;]*;', content)
                    for match in matches:
                        enums.add(match)

    return list(structs), list(globals), list(macros), list(typedefs),list(enums), list(variable_names)

def extract_info_from_c_file(c_file):
    tags_file = 'tags.json'
    generate_ctags(c_file, tags_file)
    structs, globals, macros, typedefs,enums ,variable_names= parse_ctags_json(tags_file, c_file)
    if os.path.exists(tags_file):
        os.remove(tags_file)
    return f"Names: {variable_names}\n\nStructs: {structs}\n\nGlobals: {globals}\n\nMacros: {macros}\n\nTypedefs: {typedefs}\n\nEnums: {enums} \n\n"
    # return f"Names: {variable_names}\n\nGlobals: {globals}\n\nMacros: {macros}\n\nEnums: {enums} \n\n"

if __name__ == '__main__':
    # 示例用法
    c_file = '/home/mins01//binn/src/binn.c'
    
    # 提取信息
    result = extract_info_from_c_file(c_file)
    
    # 打印结果
    print(result)