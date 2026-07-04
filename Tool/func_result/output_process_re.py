import re
import json
import os

# 正则表达式模式，用于匹配函数名和文件名的基础部分
pattern_func = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*\(.*\)$')
pattern_file = re.compile(r'^(.+)\.\w+$')

def extract_function_names(func):
    if not isinstance(func, str):
        return None

    token = func.strip()
    # Drop fully-qualified prefixes, keep the last symbol segment.
    if '::' in token:
        token = token.split('::')[-1]

    match = pattern_func.match(token)
    if match:
        return match.group(1)

    # Fallback: keep bare identifier if already normalized.
    bare = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)$', token)
    if bare:
        return bare.group(1)
    return None

def process_file_func_name(json_path, processed_json_path):
    # json.load 加载数据
    with open(json_path, 'r') as file:
        data = json.load(file)

    # 处理数据
    processed_data = {}
    for entry in data:
        for file, functions in entry.items():
            # 使用正则表达式处理文件名
            file_name = os.path.basename(file)
            match_file = pattern_file.match(file_name)
            base_filename = match_file.group(1) if match_file else os.path.splitext(file_name)[0]
            # 使用正则表达式处理函数名
            processed_functions = []
            for func in functions:
                name = extract_function_names(func)
                if name:
                    processed_functions.append(name)
            # 将处理过的文件名和函数名添加到新的字典中
            processed_data[base_filename] = processed_functions
    result = []
    result.append(processed_data)
    # json.dump 将数据写入文件
    with open(processed_json_path, 'w') as json_file:
        json.dump(result, json_file, indent=4)
