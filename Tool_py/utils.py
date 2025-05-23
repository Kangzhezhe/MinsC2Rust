import json
import os
import subprocess
import re
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir,'func_result')))
from extract_rust_func import extract_rust
import shutil

import signal
import ast


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
    # 使用正则表达式匹配 ```rust 和 ``` 之间的内容
    match = re.search(r"```rust(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()  # 提取并去除首尾空白
    return None

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
        not_found_vars = re.findall( r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', source_str)
        keywords = {var for var in not_found_vars  if var in names_list}

        excluded_vars = re.findall( r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', exlude_str)
        excluded_keywords = {var for var in excluded_vars  if var in names_list}

        filtered_keywords = keywords - excluded_keywords
        # 在 target_str 中查找包含这些关键字的所有子串
        related_items = set()
        for keyword in filtered_keywords:
            # matches = re.findall(rf"'[^']*\b{keyword}\b[^']*'", target_str)
            related_items.add(converted_dict.get(keyword, ''))

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
            if key != 'extra' and key != 'main'
        )

        if 'fn main()' not in all_function_lines:
            all_function_lines += '\nfn main(){}'
        output_content = all_function_lines

        for source in all_child_files:
            if 'extra' in results_copy.get(source, []):
                output_content = results_copy[source]['extra'] + '\n' + output_content

        with open(os.path.join(tmp_dir, 'test_source.rs'), 'w') as f:
            f.write(output_content)

        
        compile_error2 = run_command(f'rustc -Awarnings {os.path.join(tmp_dir, 'test_source.rs')}')

        delete_file_if_exists('test_source')
        if compile_error2:
            break

    return compile_error2

def has_generic_parameters(function_str):
    # 改进的正则表达式，支持泛型参数和函数体
    pattern = r"pub\s+fn\s+\w+\s*<[^>]*>\s*"
    match = re.search(pattern, function_str)
    return bool(match)

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
    # 使用正则表达式过滤掉工具链的错误信息及其具体内容
    filtered_error = re.sub(r'(?m)^   ::: .*\n(?:.*\n)*', '', compile_error)
    # filtered_error = re.sub(r'(?m)^    = note: .*\n(?:.*\n)*', '', filtered_error)
    filtered_error = re.sub(r'(?m)^help: .*\n(?:.*\n)*', '', filtered_error)
    return filtered_error

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
    error_codes = set(re.findall(r"error\[\w+\]", stderr))
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
    # 创建正则表达式来匹配代码块标记
    text = re.sub(r"```.*?\n", "", text)
    # 去除剩余的代码块结束标记
    text = re.sub(r"```", "", text)
    return text

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
    # 去除注释
    text = re.sub(r'//.*?\n', '', text)
    # 去除空格和换行符
    return text.replace(" ", "").replace("\n", "")


def get_output_content(non_function_content, function_content_dict):
    output_content = non_function_content + '\n' + '\n'.join(function_content_dict.values())
    return output_content

def parse_and_deduplicate_errors(error_str):
    # 使用正则表达式匹配错误类型和具体报错内容
    error_pattern = re.compile(r"(error\[[E\d]+\]: .+?)(?=\nerror\[|$)", re.DOTALL)
    matches = error_pattern.findall(error_str)

    # 将错误信息转换为字典形式
    error_dict = {}
    for match in matches:
        error_type = match.split('\n')[0]
        error_content = match[len(error_type):].strip()
        if error_type not in error_dict:
            error_dict[error_type] = error_content

    # 对错误类型进行去重，并生成去重后的字符串
    unique_errors = []
    for error_type, error_content in error_dict.items():
        unique_errors.append(f"{error_type}\n{error_content}")

    return '\n\n'.join(unique_errors)


from collections import deque

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


def deduplicate_code(all_function_lines,tmp_dir):
    with open(os.path.join(tmp_dir,'test_source.rs'), 'w') as f:
        f.write(all_function_lines)

    json_file_path = os.path.join(tmp_dir,'definitions.json')


    run_command(f"cd ../rust_ast_project/ && cargo run {os.path.join(tmp_dir,'test_source.rs')} {json_file_path}")

    source_file_path = os.path.join(tmp_dir,'test_source.rs')
    output_file_path = os.path.join(tmp_dir,'processed_file.rs')
    non_function_content, function_content_dict= extract_rust(json_file_path, source_file_path, output_file_path)
    non_function_content = ''.join(non_function_content)
    non_function_content += '\n'

    output_content = non_function_content + '\n'+'\n'.join(function_content_dict.values())
    return non_function_content, function_content_dict,output_content

def clean_and_validate_json(output):
    # 去除不可见字符
    output = re.sub(r'[\x00-\x1F\x7F]', '', output)

    # 使用正则表达式去除多余的空格和换行符
    output = re.sub(r'\s+', ' ', output).strip()

    # 将单引号替换为双引号
    output = output.replace("'", '"')

    # 尝试修复常见的 JSON 格式问题
    # 确保 key 和 value 是用双引号括起来的
    output = re.sub(r'(\w+)\s*:\s*([^",{}\[\]]+)', r'"\1": "\2"', output)

    try:
        json_obj = json.loads(output)
        return json_obj
    except json.JSONDecodeError:
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

    updated_content = re.sub(r'#\[timeout\(\d+\)\]', f'#[timeout({new_timeout})]', content)

    with open(file_path, 'w') as file:
        file.write(updated_content)

    # print(f"Updated timeouts in {file_path} to {new_timeout} milliseconds.")
