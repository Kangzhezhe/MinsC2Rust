#!/usr/bin/env python3

import copy
from pprint import pprint
import re
import subprocess
import glob
from clang.cindex import Config, CursorKind, Index, CompilationDatabase
from collections import OrderedDict, defaultdict, deque
import sys
import json
import os
from utils import find_elements

try:
    import yaml
except ImportError:
    yaml = None

try:
    import graphviz
except ImportError:
    graphviz = None


def _configure_libclang():
    if Config.library_file:
        return

    env_candidates = []
    for env_key in ("LIBCLANG_PATH", "LIBCLANG_FILE"):
        value = os.environ.get(env_key, "").strip()
        if not value:
            continue
        if os.path.isdir(value):
            env_candidates.extend(
                [
                    os.path.join(value, "libclang.so"),
                    os.path.join(value, "libclang.so.1"),
                ]
            )
        else:
            env_candidates.append(value)

    candidate_paths = env_candidates + [
        "/usr/lib/libclang.so",
        "/usr/lib/libclang.so.1",
        "/usr/lib/libclang.so.21.1",
        "/usr/lib/libclang.so.21.1.8",
        "/usr/lib64/libclang.so",
        "/usr/lib/llvm-14/lib/libclang.so.1",
        "/usr/lib/llvm-14/lib/libclang.so",
    ]

    candidate_paths.extend(sorted(glob.glob("/usr/lib*/libclang.so*")))
    candidate_paths.extend(sorted(glob.glob("/usr/lib/llvm-*/lib/libclang.so*")))

    seen = set()
    for path in candidate_paths:
        if not path or path in seen:
            continue
        seen.add(path)
        if not os.path.exists(path):
            continue
        try:
            Config.set_library_file(path)
            return
        except Exception:
            continue


_configure_libclang()

"""
Dumps a callgraph of a function in a codebase
usage: callgraph.py file.cpp|compile_commands.json [-x exclude-list] [extra clang args...]
The easiest way to generate the file compile_commands.json for any make based
compilation chain is to use Bear and recompile with `bear make`.

When running the python script, after parsing all the codebase, you are
prompted to type in the function's name for which you wan to obtain the
callgraph
"""

CALLGRAPH = defaultdict(list)
CALLGRAPH_SEEN = defaultdict(set)
DIRECT_CALLGRAPH = defaultdict(set)
REFERENCEGRAPH = defaultdict(set)
FULLNAMES = defaultdict(set)
FILE_FUNCTIONS = defaultdict(set)
DEFINED_SIGNATURES = set()

FUNCTION_CURSOR_KINDS = {
    CursorKind.FUNCTION_DECL,
    CursorKind.CXX_METHOD,
    CursorKind.FUNCTION_TEMPLATE,
}

REFERENCE_CURSOR_KINDS = {
    CursorKind.DECL_REF_EXPR,
    CursorKind.MEMBER_REF_EXPR,
    CursorKind.UNEXPOSED_EXPR,
}


def _safe_kind(cursor):
    try:
        return cursor.kind
    except ValueError:
        return None


def _safe_children(cursor):
    try:
        return list(cursor.get_children())
    except ValueError:
        return []


def get_diag_info(diag):
    return {
        'severity': diag.severity,
        'location': diag.location,
        'spelling': diag.spelling,
        'ranges': list(diag.ranges),
        'fixits': list(diag.fixits)
    }


def fully_qualified(c):
    if c is None:
        return ''
    elif isinstance(c, str):
        return c
    elif _safe_kind(c) == CursorKind.TRANSLATION_UNIT:
        return ''
    else:
        res = fully_qualified(c.semantic_parent)
        if res != '':
            return res + '::' + c.spelling
        return c.spelling


def fully_qualified_pretty(c):
    if c is None:
        return ''
    elif isinstance(c, str):
        return c
    elif _safe_kind(c) == CursorKind.TRANSLATION_UNIT:
        return ''
    else:
        res = fully_qualified(c.semantic_parent)
        if res != '':
            return res + '::' + c.displayname
        return c.displayname


def _signature_suffix(signature):
    if not signature:
        return ''
    token = str(signature).strip()
    if '::' in token:
        return token.split('::')[-1].strip()
    return token


def _signature_file_path(signature):
    token = str(signature or '').strip()
    if '::' not in token:
        return ''
    return token.rsplit('::', 1)[0]


def _is_test_signature(signature):
    path = _signature_file_path(signature).lower()
    return '/test/' in path or '/tests/' in path


def _choose_best_definition(signature, candidates):
    unique_candidates = []
    seen = set()
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)

    if not unique_candidates:
        return ''
    if len(unique_candidates) == 1:
        return unique_candidates[0]

    signature_is_test = _is_test_signature(signature)

    def rank(candidate):
        candidate_is_test = _is_test_signature(candidate)
        return (
            1 if candidate_is_test and not signature_is_test else 0,
            0 if (signature_is_test and not candidate_is_test) else 1,
            len(CALLGRAPH.get(candidate, [])),
            candidate,
        )

    return sorted(unique_candidates, key=rank)[0]


def _resolve_to_definition_signature(signature):
    token = str(signature or '').strip()
    if not token:
        return ''

    if token in DEFINED_SIGNATURES:
        return token

    suffix = _signature_suffix(token)
    func_name = extract_function_names(token)

    exact_candidates = [candidate for candidate in DEFINED_SIGNATURES if _signature_suffix(candidate) == suffix]
    if exact_candidates:
        return _choose_best_definition(token, exact_candidates)

    if func_name:
        name_candidates = [candidate for candidate in DEFINED_SIGNATURES if extract_function_names(candidate) == func_name]
        if name_candidates:
            return _choose_best_definition(token, name_candidates)

    return token


def canonicalize_callgraph_edges():
    canonical_callgraph = defaultdict(list)
    canonical_seen = defaultdict(set)
    canonical_direct = defaultdict(set)
    canonical_reference = defaultdict(set)

    all_callers = set(CALLGRAPH.keys()) | set(DIRECT_CALLGRAPH.keys()) | set(REFERENCEGRAPH.keys())

    for caller in all_callers:
        canonical_caller = _resolve_to_definition_signature(caller)

        for callee in CALLGRAPH.get(caller, []):
            canonical_callee = _resolve_to_definition_signature(callee)
            if not canonical_callee or canonical_callee == canonical_caller:
                continue
            if canonical_callee in canonical_seen[canonical_caller]:
                continue
            canonical_seen[canonical_caller].add(canonical_callee)
            canonical_callgraph[canonical_caller].append(canonical_callee)

        for callee in DIRECT_CALLGRAPH.get(caller, set()):
            canonical_callee = _resolve_to_definition_signature(callee)
            if canonical_callee and canonical_callee != canonical_caller:
                canonical_direct[canonical_caller].add(canonical_callee)

        for callee in REFERENCEGRAPH.get(caller, set()):
            canonical_callee = _resolve_to_definition_signature(callee)
            if canonical_callee and canonical_callee != canonical_caller:
                canonical_reference[canonical_caller].add(canonical_callee)

    CALLGRAPH.clear()
    CALLGRAPH.update(canonical_callgraph)
    CALLGRAPH_SEEN.clear()
    CALLGRAPH_SEEN.update(canonical_seen)
    DIRECT_CALLGRAPH.clear()
    DIRECT_CALLGRAPH.update(canonical_direct)
    REFERENCEGRAPH.clear()
    REFERENCEGRAPH.update(canonical_reference)


def is_excluded(node, xfiles, xprefs):
    if not node.extent.start.file:
        return False

    for xf in xfiles:
        if node.extent.start.file.name.startswith(xf):
            return True

    fqp = fully_qualified_pretty(node)

    for xp in xprefs:
        if fqp.startswith(xp):
            return True

    return False


def _is_function_cursor(node):
    return _safe_kind(node) in FUNCTION_CURSOR_KINDS


def _add_callgraph_edge(cur_fun, callee, edge_kind="call"):
    caller_name = fully_qualified_pretty(cur_fun)
    callee_name = fully_qualified_pretty(callee)
    if not caller_name or not callee_name or caller_name == callee_name:
        return

    if edge_kind == "call":
        DIRECT_CALLGRAPH[caller_name].add(callee_name)
    elif edge_kind == "reference":
        REFERENCEGRAPH[caller_name].add(callee_name)

    if callee_name in CALLGRAPH_SEEN[caller_name]:
        return
    CALLGRAPH_SEEN[caller_name].add(callee_name)
    CALLGRAPH[caller_name].append(callee_name)


def _record_function_reference(cur_fun, node, xfiles, xprefs, edge_kind="call"):
    if cur_fun is None:
        return
    referenced = getattr(node, 'referenced', None)
    if referenced is None:
        return
    if not _is_function_cursor(referenced):
        return
    if is_excluded(referenced, xfiles, xprefs):
        return
    _add_callgraph_edge(cur_fun, referenced, edge_kind=edge_kind)


def show_info(node, xfiles, xprefs, cur_fun=None, suppress_reference_capture=False):
    kind = _safe_kind(node)
    if kind is None:
        for c in _safe_children(node):
            show_info(c, xfiles, xprefs, cur_fun, suppress_reference_capture=suppress_reference_capture)
        return

    if kind == CursorKind.FUNCTION_TEMPLATE:
        if not is_excluded(node, xfiles, xprefs):
            # 检查是否是函数定义（不是声明）
            if node.is_definition():
                cur_fun = node
                DEFINED_SIGNATURES.add(fully_qualified_pretty(cur_fun))
                FULLNAMES[fully_qualified(cur_fun)].add(
                    fully_qualified_pretty(cur_fun))
                FILE_FUNCTIONS[node.location.file.name].add(fully_qualified_pretty(cur_fun))

    if kind == CursorKind.CXX_METHOD or kind == CursorKind.FUNCTION_DECL:
        if not is_excluded(node, xfiles, xprefs):
            # 检查是否是函数定义（不是声明）
            if node.is_definition():
                cur_fun = node
                DEFINED_SIGNATURES.add(fully_qualified_pretty(cur_fun))
                FULLNAMES[fully_qualified(cur_fun)].add(
                    fully_qualified_pretty(cur_fun))
                FILE_FUNCTIONS[node.location.file.name].add(fully_qualified_pretty(cur_fun))

    if kind == CursorKind.CALL_EXPR:
        _record_function_reference(cur_fun, node, xfiles, xprefs, edge_kind="call")

        children = _safe_children(node)
        for idx, c in enumerate(children):
            show_info(
                c,
                xfiles,
                xprefs,
                cur_fun,
                suppress_reference_capture=(idx == 0),
            )
        return

    if kind in REFERENCE_CURSOR_KINDS and not suppress_reference_capture:
        _record_function_reference(cur_fun, node, xfiles, xprefs, edge_kind="reference")

    for c in _safe_children(node):
        show_info(c, xfiles, xprefs, cur_fun)


def build_reference_dependency_map():
    dependencies = defaultdict(list)

    for caller_func_signature, referenced_funcs in REFERENCEGRAPH.items():
        caller_name = extract_function_names(caller_func_signature)
        if not caller_name:
            continue

        direct_calls = DIRECT_CALLGRAPH.get(caller_func_signature, set())
        seen = set()
        for callee_signature in referenced_funcs:
            if callee_signature in direct_calls:
                continue
            callee_name = extract_function_names(callee_signature)
            if not callee_name or callee_name == caller_name or callee_name in seen:
                continue
            seen.add(callee_name)
            dependencies[caller_name].append(callee_name)

    return dependencies


def pretty_print(n):
    if isinstance(n, str):
        return n
    v = ''
    if n.is_virtual_method():
        v = ' virtual'
    if n.is_pure_virtual_method():
        v = ' = 0'
    return fully_qualified_pretty(n) + v

def generate_dot(fun_name, so_far, depth=0, dot=None):
    if graphviz is None:
        raise RuntimeError("graphviz is required to generate call graph dot output")
    if dot is None:
        dot = graphviz.Digraph(comment='Call Graph')
    if depth >= 15:
        dot.node('too_deep', '...<too deep>...')
        return dot
    if fun_name in CALLGRAPH:
        for f in CALLGRAPH[fun_name]:
            if pretty_print(f) in so_far:
                continue
            so_far.append(pretty_print(f))
            # print('  ' * (depth + 1) + pretty_print(f))
            dot.node(pretty_print(f), pretty_print(f))
            dot.edge(fun_name, pretty_print(f))
            if fully_qualified_pretty(f) in CALLGRAPH:
                generate_dot(fully_qualified_pretty(f), list(), depth + 1, dot)
            else:
                generate_dot(fully_qualified(f), list(), depth + 1, dot)
    return dot





def read_compile_commands(filename):
    if filename.endswith('.json'):
        with open(filename) as compdb:
            return json.load(compdb)
    else:
        return [{'command': '', 'file': filename}]




def read_args(args):
    db = None
    clang_args = []
    excluded_prefixes = []
    excluded_paths = []
    config_filename = None
    lookup = None
    i = 0
    while i < len(args):
        if args[i] == '-x':
            i += 1
            excluded_prefixes += args[i].split(',')
        elif args[i] == '-p':
            i += 1
            excluded_paths += args[i].split(',')
        elif args[i] == '--cfg':
            i += 1
            config_filename = args[i]
        elif args[i] == '--lookup':
            i += 1
            lookup = args[i]
        # elif args[i][0] == '-':
        #     clang_args.append(args[i])
        else:
            db = args[i]
        i += 1

    if len(excluded_paths) == 0:
        excluded_paths.append('/usr')
    return {
        'db': db,
        'clang_args': clang_args,
        'excluded_prefixes': excluded_prefixes,
        'excluded_paths': excluded_paths,
        'config_filename': config_filename,
        'lookup': lookup,
        'ask': (lookup is None)
    }

def load_config_file(cfg):
    if cfg['config_filename']:
        if yaml is None:
            raise RuntimeError("PyYAML is required when --cfg is used")
        with open(cfg['config_filename'], 'r') as yamlfile:
            data = yaml.load(yamlfile, Loader=yaml.FullLoader)
            cfg['clang_args'] += data['clang_args']
            cfg['excluded_prefixes'] += data['excluded_prefixes']
            cfg['excluded_paths'] += data['excluded_paths']


def keep_arg(x) -> bool:
    keep_this = x.startswith('-I') or x.startswith('-std=') or x.startswith('-D')
    return keep_this


def get_system_include_paths():
    cmd = ['gcc', '-E', '-Wp,-v', '-']
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    _, stderr = proc.communicate(input=b'')
    lines = stderr.decode().splitlines()
    start = False
    paths = []
    for line in lines:
        if line.strip() == '#include <...> search starts here:':
            start = True
            continue
        if line.strip() == 'End of search list.':
            break
        if start:
            paths.append(line.strip())
    return paths

def analyze_source_files(cfg):
    print('reading source files...')
    system_include_paths = get_system_include_paths()
    system_include_paths = ['-I' + path for path in system_include_paths]
    for cmd in read_compile_commands(cfg['db']):
        source_file = cmd.get('file', '')
        # This pipeline targets C projects; skip C++ compile units to avoid TU load failures.
        if not source_file.endswith('.c'):
            continue

        index = Index.create()

        c = system_include_paths + [
            x for x in cmd.get('command','').split()
            if keep_arg(x)
        ] + cfg['clang_args']
        try:
            tu = index.parse(source_file, c)
        except Exception as exc:
            print(f"[WARN] skip translation unit parse failure: {source_file} ({exc})")
            continue
        print(source_file)
        if not tu:
            print("unable to load input")

        for d in tu.diagnostics:
            if d.severity > 3:
                print(' '.join(c))
                pprint(('diags', list(map(get_diag_info, tu.diagnostics))))
                exit(1)
                return
        show_info(tu.cursor, cfg['excluded_paths'], cfg['excluded_prefixes'])



def print_callgraph(fun):
    if fun in CALLGRAPH:
        # print(fun)
        dot = generate_dot(fun, list())
        # dot.render('callgraph', format='png', cleanup=True)
    else:
        print('matching:')
        # for f, ff in FULLNAMES.items():
        #     if f.startswith(fun):
        #         for fff in ff:
        #             print(fff)

def func_match(fun):
    fs = []
    for f, ff in FULLNAMES.items():
        canonical_f = extract_function_names(f) or f
        if f == fun or canonical_f == fun:
            for fff in ff:
                fs.append(fff)
    return fs

def ask_and_print_callgraph():
    while True:
        fun = input('> ')
        if not fun:
            break
        print_callgraph(fun)


def get_c_filenames(directory):
    # 创建一个空列表来保存文件名
    c_filenames = []

    # 遍历给定目录中的所有文件和子目录
    for filename in os.listdir(directory):
        # 检查文件是否是.c文件
        if filename.endswith('.c'):
            # 去掉.c后缀并添加到列表中
            c_filenames.append(os.path.splitext(filename)[0])
            # c_filenames = [s.replace("-","_") for s in c_filenames]
    print(c_filenames)
    return c_filenames

def get_c_filepaths(directory_path, is_test=False):
    c_filepaths = []
    for root, dirs, files in os.walk(directory_path):
        abs_root = os.path.abspath(root)
        path_parts = abs_root.split(os.sep)
        if 'Output' in path_parts or 'build' in path_parts or ('test' in path_parts and not is_test):
            continue

        for filename in files:
            if filename.endswith('.c') and (filename.startswith('test-') is False or is_test):
                # 使用 os.path.abspath 获取绝对路径
                abs_path = os.path.abspath(os.path.join(root, filename))
                c_filepaths.append(abs_path)
    
    # 添加没有对应.c文件的.h文件
    # 首先收集所有.c文件的基础名称
    c_basenames = set()
    for filepath in c_filepaths:
        basename = os.path.splitext(os.path.basename(filepath))[0]
        c_basenames.add(basename)
    
    # 检查所有.h文件，添加没有对应.c文件的
    additional_h_files = []
    for root, dirs, files in os.walk(directory_path):
        abs_root = os.path.abspath(root)
        path_parts = abs_root.split(os.sep)
        if 'Output' in path_parts or 'build' in path_parts or ('test' in path_parts and not is_test):
            continue
            
        for filename in files:
            if filename.endswith('.h'):
                h_basename = os.path.splitext(filename)[0]
                # 检查是否有对应的.c文件
                if h_basename not in c_basenames:
                    abs_path = os.path.abspath(os.path.join(root, filename))
                    additional_h_files.append(abs_path)
    
    # 将独立的.h文件添加到结果中
    c_filepaths.extend(additional_h_files)
    
    return c_filepaths

def get_path_suffix(file_path, depth=2):
    """获取路径的最后depth个层级"""
    parts = file_path.split('/')
    if len(parts) >= depth:
        return '/'.join(parts[-depth:])
    return file_path


def get_c_functions_name(c_path, unprocess_path, compile_commands_path, is_test=False):
    #找到文件夹下的所有的.c文件
    # filenames = get_c_filenames("/home/mins01/project/c-algorithms/src")
    # #将文件的所有函数合成json格式
    cfg = read_args(sys.argv)
    cfg['db'] = compile_commands_path
    load_config_file(cfg)
    analyze_source_files(cfg)
    if c_path != '':
        filepaths = get_c_filepaths(c_path, is_test)
    else:
        filepaths = {f['file'] for f in read_compile_commands(cfg['db'])}

    print("FILE_FUNCTIONS: ", FILE_FUNCTIONS)
    print("filepaths: ", filepaths)
    
    results = []
    collected_functions = set()
    
    # 构建文件基础名到路径的映射
    filepath_basename_map = {}
    for file in filepaths:
        basename = os.path.splitext(os.path.basename(file))[0]
        filepath_basename_map[basename] = file
    
    for file in filepaths:
        # functions_list = list(FILE_FUNCTIONS.get(file, []))
        # 使用路径的最后两个层级作为键
        file_key = get_path_suffix(file, 2)
        functions_list = list(FILE_FUNCTIONS.get(file, []))
        
        # 如果直接匹配失败，尝试在FILE_FUNCTIONS中查找匹配的路径
        if not functions_list:
            for full_path in FILE_FUNCTIONS.keys():
                if get_path_suffix(full_path, 2) == file_key:
                    functions_list = list(FILE_FUNCTIONS.get(full_path, []))
                    break


        # 检查是否有对应的.h文件中的函数定义
        basename = os.path.splitext(os.path.basename(file))[0]
        
        # 查找对应的.h文件
        for h_file, h_functions in FILE_FUNCTIONS.items():
            h_basename = os.path.splitext(os.path.basename(h_file))[0]
            
            # 如果.h文件的基础名与.c文件相同
            if h_basename == basename and h_file.endswith('.h'):
                # 将.h文件中的函数添加到.c文件的函数列表中
                h_functions_list = list(h_functions)
                
                # 去重：只添加.c文件中没有的函数
                for h_func in h_functions_list:
                    if h_func not in functions_list:
                        functions_list.append(h_func)
                        # print(f"添加来自 {os.path.basename(h_file)} 的函数 '{h_func}' 到 {os.path.basename(file)}")
        
        if functions_list:  # 只添加有函数的文件
            results.append({os.path.basename(file): functions_list})
            collected_functions.update(functions_list)
    
    # 指定要保存的文件名
    # 使用 json.dump 将数据写入文件
    with open(unprocess_path, 'w') as json_file:
        json.dump(results, json_file, indent=4)

def get_func_depth(fun_name, so_far, depth=0, funcs_depth={}, visited=None):
    if visited is None:
        visited = set()

    # 检查是否已经访问过
    if fun_name in visited:
        return
    
    visited.add(fun_name)
    
    if fun_name in CALLGRAPH:
        for f in CALLGRAPH[fun_name]:
            child_name = pretty_print(f)
            
            # 检查循环引用
            if child_name in so_far:
                continue
                
            so_far.append(child_name)
            print('  ' * (depth + 1) + child_name)
            
            # 更新深度
            if funcs_depth.get(child_name) is None:
                funcs_depth[child_name] = depth + 1
            else:
                if funcs_depth[child_name] < depth + 1:
                    funcs_depth[child_name] = depth + 1
            
            # 递归调用
            if fully_qualified_pretty(f) in CALLGRAPH:
                get_func_depth(fully_qualified_pretty(f), so_far, depth + 1, funcs_depth, visited)
            else:
                get_func_depth(fully_qualified(f), so_far, depth + 1, funcs_depth, visited)
            
            so_far.pop()

pattern_func = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*\(.*\)$')
pattern_file = re.compile(r'^(.+)\.\w+$')

def extract_function_names(func):
    if not isinstance(func, str):
        return None

    token = func.strip()
    if '::' in token:
        token = token.split('::')[-1]

    match = pattern_func.match(token)
    if match:
        return match.group(1)

    bare = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)$', token)
    if bare:
        return bare.group(1)
    return None


def analyze_function_calls(funcs_childs):
    # 将有向有环图转换为有向无环图，并计算深度
    def remove_cycles(graph):
        visited = set()
        stack = set()
        result = defaultdict(list)
        depth = defaultdict(int)

        def visit(node, current_depth):
            if node in stack:
                return False
            if node in visited:
                return True
            stack.add(node)
            for neighbor in graph.get(node, []):
                if not visit(neighbor, current_depth + 1):
                    continue
                result[node].append(neighbor)
                depth[neighbor] = max(depth[neighbor], current_depth + 1)
            stack.remove(node)
            visited.add(node)
            depth[node] = max(depth[node], current_depth)
            return True

        for node in graph:
            if node not in visited:
                visit(node, 0)

        # 确保所有节点都在结果中，即使它们没有子节点
        for node in graph:
            if node not in result:
                result[node] = []
                depth[node] = 0

        return result, depth

    # 拓扑排序并返回有序字典
    def topological_sort(graph, depth):
        in_degree = defaultdict(int)
        for u in graph:
            for v in graph[u]:
                in_degree[v] += 1

        queue = deque([u for u in graph if in_degree[u] == 0])
        topo_order = []

        while queue:
            u = queue.popleft()
            topo_order.append(u)
            for v in graph[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # 反转结果以确保子函数在前，父函数在后
        topo_order.reverse()

        # 创建有序字典
        ordered_depth = OrderedDict()
        for node in topo_order:
            ordered_depth[node] = depth[node]

        return ordered_depth

    def ensure_ordered_depth(ordered_depth):
        max_depth = float('-inf')
        for key in reversed(ordered_depth):
            if ordered_depth[key] < max_depth:
                ordered_depth[key] = max_depth
            else:
                max_depth = ordered_depth[key]
        return ordered_depth

    # 转换为无环图并计算深度
    dag, depth = remove_cycles(funcs_childs)

    # 进行拓扑排序并返回有序字典
    ordered_depth = topological_sort(dag, depth)

    result = ensure_ordered_depth(ordered_depth)

    return result

def build_module_dependencies_from_callgraph(include_dirs):
    """
    基于函数调用关系构建模块间的依赖关系，作为include_dirs的补充
    遍历每个模块的函数，检查子函数是否在include依赖范围内，不在则添加依赖
    测试模块不作为被依赖项
    """
    # 构建文件名到模块名的映射
    module_functions = defaultdict(set)
    
    for file_path, functions in FILE_FUNCTIONS.items():
        # 提取模块名（去掉路径和扩展名）
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        # 存储每个模块的函数列表
        module_functions[module_name].update(functions)
    
    # 构建函数完整签名到所有可能模块的映射（处理同名同签名函数）
    function_signature_to_modules = defaultdict(list)
    for file_path, functions in FILE_FUNCTIONS.items():
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        for func in functions:
            function_signature_to_modules[func].append(module_name)
    
    # 构建简单的函数名到所有可能模块的映射（处理同名函数）
    function_name_to_modules = defaultdict(list)
    for module, functions in module_functions.items():
        for func in functions:
            func_name = extract_function_names(func)
            if func_name:
                function_name_to_modules[func_name].append(module)
    
    # 获取模块可访问的所有函数（包括通过include间接访问的）
    def get_accessible_functions(module_name):
        accessible_funcs = set()
        visited = set()
        
        def dfs(current_module):
            if current_module in visited:
                return
            visited.add(current_module)
            
            # 添加当前模块的函数
            for func in module_functions.get(current_module, []):
                func_name = extract_function_names(func)
                if func_name:
                    accessible_funcs.add(func_name)
            
            # 递归添加include依赖模块的函数
            for included_module in include_dirs.get(current_module, []):
                dfs(included_module)
        
        dfs(module_name)
        return accessible_funcs
    
    # 为每个模块构建可访问函数集合
    module_accessible_functions = {}
    for module_name in include_dirs.keys():
        module_accessible_functions[module_name] = get_accessible_functions(module_name)
    
    # 基于调用关系构建模块依赖
    enhanced_include_dirs = copy.deepcopy(include_dirs)
    
    # *** 关键修改：遍历CALLGRAPH而不是模块函数 ***
    for caller_func_signature, called_funcs in CALLGRAPH.items():
        # 确定调用者函数所属的模块列表
        caller_modules = function_signature_to_modules.get(caller_func_signature, [])
        if not caller_modules:
            continue
        
        caller_func_name = extract_function_names(caller_func_signature)
        if not caller_func_name:
            continue
        
        # 对每个可能的调用者模块进行处理
        for caller_module in caller_modules:
            if caller_module not in include_dirs:
                continue
                
            # 获取调用者模块可访问的函数
            accessible_funcs = module_accessible_functions.get(caller_module, set())
            
            # 遍历被调用的函数
            for called_func_cursor in called_funcs:
                called_func_name = pretty_print(called_func_cursor)
                called_func_simple = extract_function_names(called_func_name)
                
                if not called_func_simple:
                    continue
                
                # *** 关键修改：检查子函数是否在当前模块的可访问函数范围内 ***
                if called_func_simple in accessible_funcs:
                    # 函数在可访问范围内，不需要添加新的依赖
                    continue
                
                # *** 关键修改：在全局范围内找到子函数对应的模块，考虑同名函数 ***
                target_module = None
                
                # 获取所有可能包含该函数的模块
                possible_modules = function_name_to_modules.get(called_func_simple, [])
                
                # 如果只有一个模块包含该函数，直接使用
                if len(possible_modules) == 1:
                    target_module = possible_modules[0]
                elif len(possible_modules) > 1:
                    # 如果有多个模块包含同名函数，优先选择非测试模块
                    non_test_modules = [m for m in possible_modules if not m.startswith('test-')]
                    if non_test_modules:
                        # 如果有非测试模块，选择第一个非测试模块
                        target_module = non_test_modules[0]
                    else:
                        # 如果都是测试模块，跳过（测试模块不作为被依赖项）
                        continue
                
                if target_module and target_module != caller_module:
                    # 测试模块不作为被依赖项
                    if target_module.startswith('test-'):
                        continue
                    
                    # 添加依赖关系
                    if target_module not in enhanced_include_dirs[caller_module]:
                        enhanced_include_dirs[caller_module].append(target_module)
                        print(f"添加依赖: {caller_module} -> {target_module} (因为函数 {caller_func_name} 调用了 {called_func_simple})")
    
    return enhanced_include_dirs

def process_test_and_uncovered_functions(data, data_src, include_dirs, all_file_paths):
    """
    处理测试函数和未覆盖函数的依赖关系
    
    Args:
        data: 测试文件的函数数据
        data_src: 源文件的函数数据  
        include_dirs: 包含目录依赖关系
        all_file_paths: 所有文件路径列表
        
    Returns:
        tuple: (result_funcs_depth, result_funcs_child, all_pointer_funcs, updated_include_dirs)
    """
    
    def get_all_funcs(source_name, include_dirs, data_src, all_funcs):
        child_source = include_dirs.get(source_name, [])
        for source in child_source:
            # 如果 data_src[source] 的所有元素都已经在 all_funcs 中，则跳过
            if all(func in all_funcs for func in data_src.get(source, [])):
                continue
            
            # 否则，添加新的函数并递归处理
            all_funcs += data_src.get(source, [])
            get_all_funcs(source, include_dirs, data_src, all_funcs)

    def func_avaliabe(func, source_name, include_dirs=include_dirs, data=data, data_src=data_src):
        all_funcs = data.get(source_name, []).copy()
        get_all_funcs(source_name, include_dirs, data_src, all_funcs)
        return func in all_funcs

    def _signature_source_name(signature):
        file_path = _signature_file_path(signature)
        if not file_path:
            return ''
        return os.path.splitext(os.path.basename(file_path))[0]

    reachable_source_cache = {}

    def _collect_reachable_sources(source_name):
        cached = reachable_source_cache.get(source_name)
        if cached is not None:
            return cached

        reachable = {source_name}
        stack = [source_name]
        while stack:
            current = stack.pop()
            for dep in include_dirs.get(current, []) or []:
                if dep in reachable:
                    continue
                reachable.add(dep)
                stack.append(dep)

        reachable_source_cache[source_name] = reachable
        return reachable

    def _pick_seed_matches(func_name, source_name):
        matches = func_match(func_name)
        if not matches:
            return []

        exact_source_matches = [m for m in matches if _signature_source_name(m) == source_name]
        if exact_source_matches:
            return exact_source_matches

        reachable_sources = _collect_reachable_sources(source_name)
        reachable_matches = [m for m in matches if _signature_source_name(m) in reachable_sources]
        if reachable_matches:
            return reachable_matches

        return matches

    result_funcs_depth = {}
    result_funcs_child = {}
    all_file_paths = [os.path.abspath(file) for file in all_file_paths if file.endswith('.c')]
    dependencies = build_reference_dependency_map()

    # 处理测试文件
    for source_name, value in data.items():
        funcs_depth = {}
        funcs_child = defaultdict(set)
        for func in value:
            matchs = _pick_seed_matches(func, source_name)
            for match in matchs:
                if funcs_depth.get(match) is None:
                    funcs_depth[match] = 0
                    get_func_depth(match, [], funcs_depth=funcs_depth)  # 使用空列表而不是 list()

        # 特殊处理 test-utf8-decoder
        if source_name == 'test-utf8-decoder':
            result_funcs_depth[source_name] = {'test_decode_chinese': 0}
            result_funcs_child[source_name] = {'test_decode_chinese': []}
            continue

        for func, depth in funcs_depth.items():
            if extract_function_names(func) and func_avaliabe(extract_function_names(func), source_name):
                funcs_child[func] = set()
                for child in CALLGRAPH[func]:
                    if extract_function_names(pretty_print(child)) and func_avaliabe(extract_function_names(pretty_print(child)), source_name):
                        funcs_child[func].add(pretty_print(child))
        
        funcs_child = {
            extract_function_names(k): [extract_function_names(v) for v in vs if extract_function_names(v)]
            for k, vs in funcs_child.items() if extract_function_names(k)
        }

        for func_name, _ in dependencies.items():
            if func_name in funcs_child:
                funcs_child[func_name] = list(set(funcs_child[func_name]).union(dependencies[func_name]))

        sorted_funcs_depth = analyze_function_calls(funcs_child)
        sorted_funcs_depth = {(k): v for k, v in sorted_funcs_depth.items() if (k) and func_avaliabe((k), source_name)}
        
        result_funcs_depth[source_name] = sorted_funcs_depth
        result_funcs_child[source_name] = funcs_child

    # 处理函数指针
    all_pointer_funcs = set()
    for values in dependencies.values():
        all_pointer_funcs.update(values)

    for pointer in list(all_pointer_funcs): 
        file_cnt = 0
        for k, v in result_funcs_depth.items():
            if pointer in v:
                file_cnt += 1
        if file_cnt <= 1:
            all_pointer_funcs.remove(pointer)

    # 展平函数深度信息
    flattened_sorted_funcs_depth = {}
    for source, funcs in result_funcs_depth.items():
        for func_name, depth in funcs.items():
            if func_name in flattened_sorted_funcs_depth:
                flattened_sorted_funcs_depth[func_name] = max(flattened_sorted_funcs_depth[func_name], depth)
            else:
                flattened_sorted_funcs_depth[func_name] = depth

    # 检查源文件覆盖情况
    print("\n==========================\n")
    for source_name, value in data_src.items():
        union_list = find_elements(value, list(flattened_sorted_funcs_depth.keys()))
        difference = list(set(value) - set(union_list))
        if difference:
            print(f"Warning: Source file {source_name} has uncovered functions: {difference}")
        else:
            print(f"Source file {source_name} all functions are covered by tests")

    print("\n==========================\n")

    # 处理未覆盖的函数
    updated_include_dirs = copy.deepcopy(include_dirs)
    
    for source_name, value in data_src.items():
        union_list = find_elements(value, list(flattened_sorted_funcs_depth.keys()))
        difference = list(set(value) - set(union_list))
        if difference == []:
            continue

        test_source_name = 'test-uncovered_' + source_name

        funcs_depth = {}
        funcs_child = defaultdict(set)
        for func in value:
            matchs = _pick_seed_matches(func, source_name)
            for match in matchs:
                if funcs_depth.get(match) is None:
                    funcs_depth[match] = 0
                    get_func_depth(match, [], funcs_depth=funcs_depth)

        for func, depth in funcs_depth.items():
            if extract_function_names(func) and func_avaliabe(extract_function_names(func), source_name, data=data_src):
                funcs_child[func] = set()
                for child in CALLGRAPH[func]:
                    if extract_function_names(pretty_print(child)) and func_avaliabe(extract_function_names(pretty_print(child)), source_name, data=data_src):
                        funcs_child[func].add(pretty_print(child))
        
        funcs_child = {
            extract_function_names(k): [extract_function_names(v) for v in vs if extract_function_names(v)]
            for k, vs in funcs_child.items() if extract_function_names(k)
        }

        for func_name, _ in dependencies.items():
            if func_name in funcs_child:
                funcs_child[func_name] = list(set(funcs_child[func_name]).union(dependencies[func_name]))

        sorted_funcs_depth = analyze_function_calls(funcs_child)
        sorted_funcs_depth = {(k): v for k, v in sorted_funcs_depth.items() if (k) and func_avaliabe((k), source_name, data=data_src)}
        
        result_funcs_depth[test_source_name] = sorted_funcs_depth
        result_funcs_child[test_source_name] = funcs_child

        if test_source_name not in updated_include_dirs:
            updated_include_dirs[test_source_name] = []

        if source_name not in updated_include_dirs[test_source_name]:
            updated_include_dirs[test_source_name].append(source_name)

    return result_funcs_depth, result_funcs_child, all_pointer_funcs, updated_include_dirs

def clang_callgraph(compile_commands_path ,include_dirs = None,all_file_paths = None,has_test=True):
    CALLGRAPH.clear()
    CALLGRAPH_SEEN.clear()
    DIRECT_CALLGRAPH.clear()
    REFERENCEGRAPH.clear()
    FULLNAMES.clear()
    FILE_FUNCTIONS.clear()
    DEFINED_SIGNATURES.clear()

    if len(sys.argv) < 2:
        print('usage: ' + sys.argv[0] +
              '[extra clang args...]')
        return
    cfg = read_args(sys.argv)
    cfg['db'] = compile_commands_path
    load_config_file(cfg)
    analyze_source_files(cfg)
    canonicalize_callgraph_edges()

    with open('../func_result/new_test_processed.json', 'r') as json_file:
        data = json.load(json_file)[0]

    with open('../func_result/new_src_processed.json', 'r') as json_file:
        data_src = json.load(json_file)[0]


    result_funcs_depth, result_funcs_child, all_pointer_funcs, include_dirs = process_test_and_uncovered_functions(
        data, data_src, include_dirs, all_file_paths
    )

    module_dependencies = build_module_dependencies_from_callgraph(include_dirs)
    if module_dependencies != include_dirs:
        result_funcs_depth, result_funcs_child, all_pointer_funcs, include_dirs = process_test_and_uncovered_functions(
            data, data_src, module_dependencies, all_file_paths
        )

    flattened_funcs_child = {}
    flattened_funcs_child_without_fn_pointer = {}
    for source, funcs in result_funcs_child.items():
        for func_name, children in funcs.items():
            prev_children = set(flattened_funcs_child.get(func_name, []))
            merged_children = sorted(prev_children.union(set(children)))
            flattened_funcs_child[func_name] = merged_children
            flattened_funcs_child_without_fn_pointer[func_name] = [
                child for child in merged_children if child not in all_pointer_funcs
            ]


    if not has_test:
        for file, funcs in data_src.items():
            # 获取当前文件的依赖列表
            current_deps = set(include_dirs.get(file, []))

            # 遍历文件中的每个函数
            for func in funcs:
                # 获取该函数的子函数列表
                child_funcs = flattened_funcs_child.get(func, [])

                # 遍历子函数，找到子函数所在的文件
                for child_func in child_funcs:
                    # 找到子函数所在的文件
                    for other_file, other_funcs in data_src.items():
                        if child_func in other_funcs and other_file not in current_deps and other_file != file:
                            current_deps.add(other_file)

            # 更新 include_dirs 的依赖列表
            include_dirs[file] = list(current_deps)

    

    all_data = data.copy() 
    all_data.update(data_src)
    include_dirs_without_fn_pointer = copy.deepcopy(include_dirs)
    for file,file_childs in include_dirs.items():
        funcs = all_data.get(file, [])
        all_childs = set()
        all_childs_without_fn_pointer = set()
        for func in funcs:
            if func in flattened_funcs_child:
                all_childs.update(flattened_funcs_child[func])
            if func in flattened_funcs_child_without_fn_pointer:
                all_childs_without_fn_pointer.update(flattened_funcs_child_without_fn_pointer[func])
        excluded_childs = set()
        excluded_childs_without_fn_pointer = set()
        for child in file_childs:
            all_funcs = all_data.get(child, [])
            # 特殊处理 uncovered 文件：不排除它们
            if file.startswith('test-uncovered_'):
                # 对于 uncovered 文件，保留所有依赖关系
                continue
            if set(all_funcs).isdisjoint(set(all_childs)):
                excluded_childs.add(child)
            if set(all_funcs).isdisjoint(set(all_childs_without_fn_pointer)):
                excluded_childs_without_fn_pointer.add(child)

        include_dirs[file] = [child for child in file_childs if child not in excluded_childs]
        include_dirs_without_fn_pointer[file] = [child for child in file_childs if child not in excluded_childs_without_fn_pointer]



               
    # if cfg['lookup']:
    #     print_callgraph(cfg['lookup'])
    # if cfg['ask']:
    #     ask_and_print_callgraph()
    # import ipdb; ipdb.set_trace()
    
    return result_funcs_depth,result_funcs_child,include_dirs,include_dirs_without_fn_pointer,all_pointer_funcs
if __name__ == '__main__':
    clang_callgraph()
