import sys
import os
import json
import re
from collections import defaultdict
import clang.cindex
from clang.cindex import Config, Index, CursorKind, TypeKind

# 尝试配置 libclang 路径
# 优先查找常见的 libclang.so 路径，或者依赖系统配置
potential_paths = [
    '/usr/lib/libclang.so',
    '/usr/lib/llvm-14/lib/libclang.so.1',
    '/usr/lib/llvm-14/lib/libclang.so',
    '/usr/lib64/libclang.so',
]

libclang_found = False
# 如果已经设置了就不再设置
if not Config.library_file:
    for path in potential_paths:
        if os.path.exists(path):
            Config.set_library_file(path)
            libclang_found = True
            break

if not libclang_found:
    # 尝试让 python 自动寻找，或者如果不设置也能工作（依赖 LD_LIBRARY_PATH）
    try:
        # 简单的测试一下
        Index.create()
    except Exception:
        # 如果还是不行，打印警告
        print("Warning: Could not find libclang.so. Please ensure clang is installed or set LD_LIBRARY_PATH.")

try:
    from ctags_parse import extract_info_from_c_file
except ImportError:
    # 如果找不到模块，提供默认实现以避免崩溃
    def extract_info_from_c_file(filename):
        return ""

try:
    from utils import delete_file_if_exists
except ImportError:
    def delete_file_if_exists(filename):
        if os.path.exists(filename):
            os.remove(filename)

current_dir = os.path.dirname(os.path.abspath(__file__))

def get_node_name(node):
    """获取节点的名称 (spelling)"""
    return node.spelling

def get_node_location(node):
    """获取节点的起始和结束行号 (1-based)"""
    return node.extent.start.line, node.extent.end.line


def _safe_cursor_kind(node):
    try:
        return node.kind
    except ValueError:
        return None


def _safe_children(node):
    try:
        return list(node.get_children())
    except ValueError:
        return []


def _resolve_call_expr_name(node):
    """Resolve the callee name from a call expression or wrapper node."""
    spelling = getattr(node, 'spelling', '')
    if spelling:
        return spelling

    referenced = getattr(node, 'referenced', None)
    if referenced is not None:
        ref_spelling = getattr(referenced, 'spelling', '')
        if ref_spelling:
            return ref_spelling

    for child in _safe_children(node):
        resolved = _resolve_call_expr_name(child)
        if resolved:
            return resolved

    return ""

class FunctionCallVisitor:
    def __init__(self):
        self.function_calls = defaultdict(list)
        self.current_function = None

    def visit(self, node):
        kind = _safe_cursor_kind(node)
        if kind == CursorKind.FUNCTION_DECL and node.is_definition():
            old_func = self.current_function
            self.current_function = node.spelling
            # 遍历函数体
            self.visit_children(node)
            self.current_function = old_func
        elif self.current_function:
            if kind == CursorKind.CALL_EXPR:
                callee_name = _resolve_call_expr_name(node)
                if callee_name:
                    self.function_calls[self.current_function].append(callee_name)
            
            # 继续遍历子节点
            self.visit_children(node)
        else:
            # 在函数外，继续找函数定义
            self.visit_children(node)

    def visit_children(self, node):
        for child in _safe_children(node):
            self.visit(child)

class FunctionDefVisitor:
    def __init__(self):
        self.functions = set()

    def visit(self, node):
        kind = _safe_cursor_kind(node)
        if kind == CursorKind.FUNCTION_DECL and node.is_definition():
            self.functions.add(node.spelling)
        
        # 继续遍历查找
        for child in _safe_children(node):
            self.visit(child)

def parse_c_file(filename):
    """
    使用 clang.cindex 解析 C 文件
    返回 TranslationUnit 的 cursor (root node)
    """
    index = Index.create()
    # 可以在这里添加 args，例如 include 路径
    args = [] 
    
    try:
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return None
            
        tu = index.parse(filename, args=args)
        return tu.cursor
    except Exception as e:
        print(f"解析错误: {e}")
        return None

def get_all_function_cursors(root_cursor):
    """获取所有函数定义的 cursor"""
    funcs = []
    # 直接遍历顶层声明即可，通常函数不在嵌套中
    for node in _safe_children(root_cursor):
        if _safe_cursor_kind(node) == CursorKind.FUNCTION_DECL and node.is_definition():
            funcs.append(node)
    return funcs


def _expand_requested_functions(requested_funcs, func_map, function_calls):
    """Expand requested functions with same-file direct/indirect callees."""
    expanded = []
    seen = set()
    queue = []

    for func_name in requested_funcs:
        if func_name in func_map and func_name not in seen:
            seen.add(func_name)
            expanded.append(func_name)
            queue.append(func_name)

    while queue:
        current = queue.pop(0)
        for callee in function_calls.get(current, []):
            if callee not in func_map or callee in seen:
                continue
            seen.add(callee)
            expanded.append(callee)
            queue.append(callee)

    return expanded


def _sanitize_extra_content(extra_text):
    """Remove low-signal preprocessed noise from non-function content."""
    text = re.sub(r"/\*.*?\*/", "", extra_text, flags=re.DOTALL)
    cleaned_lines = []
    pending_blank = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if not pending_blank:
                cleaned_lines.append("")
                pending_blank = True
            continue

        pending_blank = False
        if stripped.startswith("#line"):
            continue
        if stripped.startswith("#include <"):
            continue
        cleaned_lines.append(line.rstrip())

    cleaned = "\n".join(cleaned_lines).strip()
    if len(cleaned) > 10000:
        cleaned = cleaned[:10000].rstrip() + "\n/* extra truncated */"
    return cleaned

# 针对src/test文件
def content_extract(func_json_path, read_c_path, save_json_path):
    if not os.path.exists(func_json_path):
        print(f"Error: {func_json_path} does not exist.")
        return

    with open(func_json_path, "r") as f:
        data = json.load(f)
    
    for item in data:
        for file_name, funcs in item.items():
            # 判断文件类型并确定路径
            if file_name.startswith('test-'):
                # 测试文件
                filename = f"{read_c_path.replace('/src', '/test')}/{file_name}.c"
                output_json_path = save_json_path.replace('src_json', 'test_json')
            else:
                # 源文件
                filename = f"{read_c_path.replace('/test', '/src')}/{file_name}.c"
                output_json_path = save_json_path.replace('test_json', 'src_json')
            
            if not os.path.exists(filename):
                print(f"Warning: File {filename} not found, skipping.")
                continue

            # 解析文件
            root_cursor = parse_c_file(filename)
            if not root_cursor:
                continue

            result = {}
            all_function_lines = set()
            
            # 读取文件内容用于行提取
            with open(filename, 'r', errors='replace') as file:
                file_lines = file.readlines()

            # 找到所有函数定义
            all_funcs = get_all_function_cursors(root_cursor)
            func_map = {f.spelling: f for f in all_funcs}
            call_visitor = FunctionCallVisitor()
            call_visitor.visit(root_cursor)
            requested_funcs = _expand_requested_functions(funcs, func_map, call_visitor.function_calls)
            
            # 获取指定函数的上下文
            for func_signature in requested_funcs:
                if func_signature in func_map:
                    node = func_map[func_signature]
                    start_line, end_line = get_node_location(node)
                    
                    if start_line and end_line:
                        # 检查末尾如果是 '}' 且未包含，修正一下 (虽然 clang 通常是准确的)
                        # Clang extent end line is inclusive of the closing brace usually.
                        # Do nothing special unless needed.
                        
                        # 提取内容
                        extracted_lines = file_lines[start_line-1 : end_line]
                        content = "".join(extracted_lines)
                        
                        # 更新已处理行集合
                        all_function_lines.update(range(start_line, end_line + 1))
                        
                        # 存入结果
                        result[func_signature] = content

            # 计算extra字段 (所有未被函数覆盖的行)
            extra_content = []
            for i, line in enumerate(file_lines, start=1):
                if i not in all_function_lines:
                    extra_content.append(line)
            
            # 原始代码直接拼接，不做后续处理
            result["extra"] = _sanitize_extra_content("".join(extra_content))
            
            details = extract_info_from_c_file(filename)
            result["extra"] = f"{details} extract_info: [{result['extra']}]"
            
            # 写入最终 JSON
            os.makedirs(output_json_path, exist_ok=True)
            output_file = f'{output_json_path}/{file_name}.json'
            with open(output_file, 'w') as json_file:
                json.dump(result, json_file, indent=4)
            
            # 更新 data 对象中的 funcs 列表
            # 原代码逻辑: data[0][file_name]... 这里 item 就是 data 中的元素
            # 原代码似乎总是修改 data[0]，但循环是 for item in data。这是一个潜在的 bug/feature。
            # 为了保持一致性，我们修改当前的 item。
            # 实际上原代码: data[0][file_name] = ... if item is data[0]...
            # 我们直接修改 item 更有道理。
            # 但是为了完全兼容原代码行为:
            # 原代码: for item in data: ... data[0][file_name] ...
            # 如果 data 有多项，原代码可能会出错。这里我们还是修改 data 本身。
            # 假设 funcs 是 item[file_name] 得到的值
            item[file_name] = [key for key in result.keys() if key != 'extra']

    with open(func_json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

class FileScopeFunctionPointerVisitor:
    def __init__(self, defined_functions):
        self.defined_functions = defined_functions
        self.global_function_pointers = defaultdict(list)
        self.current_function = None
        self.excluded_functions = set()
        
    def visit(self, node):
        kind = _safe_cursor_kind(node)
        if kind == CursorKind.FUNCTION_DECL and node.is_definition():
            self.current_function = node.spelling
            self.visit_body(node)
            self.current_function = None
        else:
            for child in _safe_children(node):
                self.visit(child)

    def visit_body(self, node):
        # 递归寻找引用
        stack = [node]
        while stack:
            curr = stack.pop()
            curr_kind = _safe_cursor_kind(curr)
            if curr_kind is None:
                continue
            
            # 如果是引用
            if curr_kind == CursorKind.DECL_REF_EXPR:
                ref_name = curr.spelling
                if (ref_name in self.defined_functions and 
                    ref_name != self.current_function and 
                    ref_name not in self.excluded_functions):
                    self.global_function_pointers[self.current_function].append(ref_name)
            
            # 添加子节点
            children = _safe_children(curr)
            stack.extend(children)

def get_global_function_pointer_dependencies(filenames):
    """
    获取函数体内部的全局函数指针依赖（未在函数体内定义，但出现在当前文件内定义的函数）。
    """
    dependencies = defaultdict(list)

    for file in filenames:
        if not os.path.exists(file):
            continue
            
        root_cursor = parse_c_file(file)
        if not root_cursor:
            continue

        # 获取定义的函数
        fd_visitor = FunctionDefVisitor()
        fd_visitor.visit(root_cursor)
        defined_functions = fd_visitor.functions

        # 获取函数体内对这些函数的引用
        fc_visitor = FileScopeFunctionPointerVisitor(defined_functions)
        fc_visitor.visit(root_cursor)

        # 获取函数调用
        fnc_visitor = FunctionCallVisitor()
        fnc_visitor.visit(root_cursor)

        for func_name, pointers in fc_visitor.global_function_pointers.items():
            # 过滤掉直接调用的函数
            called_funcs = set(fnc_visitor.function_calls.get(func_name, []))
            
            # 指针 = 所有引用 - 直接调用
            filtered_pointers = [pointer for pointer in pointers if pointer not in called_funcs]
            
            if filtered_pointers:
                # 再次去重
                dependencies[func_name] = list(set(filtered_pointers))

    return dependencies


if __name__ == "__main__":
    # 简单的CLI测试
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        print(f"Testing parsing on {test_file}")
        if os.path.exists(test_file):
            root = parse_c_file(test_file)
            if root:
                print("Parse successful")
                funcs = get_all_function_cursors(root)
                print(f"Found {len(funcs)} functions: {[f.spelling for f in funcs]}")
        else:
            print("File not found")
