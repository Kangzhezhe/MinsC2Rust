#!/usr/bin/env python3
"""
演示Tree-sitter解析整个C工程的所有.c和.h文件
"""

import os
import glob
import tree_sitter_c as ts_c
from tree_sitter import Language, Parser
from pathlib import Path
import json
import sys

try:  # 兼容脚本直接执行与模块导入
    from config import get_project_root, to_relative_path
except ImportError:  # pragma: no cover
    from .config import get_project_root, to_relative_path

class CProjectAnalyzer:
    def __init__(self):
        """初始化C工程分析器"""
        self.C_LANGUAGE = Language(ts_c.language())
        self.parser = Parser(self.C_LANGUAGE)
        self.analysis_results = {}
        self.project_root = get_project_root()
    
    def find_c_files(self, project_path):
        """查找项目中所有的C和H文件"""
        c_files = []
        h_files = []
        project_str = str(project_path)
        
        # 递归查找所有.c文件
        c_pattern = os.path.join(project_str, "**", "*.c")
        c_files.extend(glob.glob(c_pattern, recursive=True))
        
        # 递归查找所有.h文件
        h_pattern = os.path.join(project_str, "**", "*.h")
        h_files.extend(glob.glob(h_pattern, recursive=True))
        
        return c_files, h_files
    
    def parse_single_file(self, file_path):
        """解析单个C/H文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 解析文件
            tree = self.parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node
            
            # 提取语法元素
            functions = self.extract_functions(root_node, content, root_node)
            structs = self.extract_structs(root_node, content, root_node)
            includes = self.extract_includes(root_node, content)
            variables = self.extract_global_variables(root_node, content, root_node)
            typedefs = self.extract_typedefs(root_node, content, root_node)
            macros = self.extract_macros(root_node, content, root_node)
            enums = self.extract_enums(root_node, content, root_node)
            
            # 创建初始数据
            raw_data = {
                'functions': functions,
                'structs': structs,
                'includes': includes,
                'variables': variables,
                'typedefs': typedefs,
                'macros': macros,
                'enums': enums
            }
            
            # 应用通用去重逻辑
            deduplicated_data = self.deduplicate_elements(raw_data)
            
            rel_path = to_relative_path(file_path)

            return {
                'file_path': rel_path,
                'parse_success': True,
                'functions': deduplicated_data['functions'],
                'structs': deduplicated_data['structs'],
                'includes': includes,  # includes不需要去重
                'variables': deduplicated_data['variables'],
                'typedefs': deduplicated_data['typedefs'],
                'macros': deduplicated_data['macros'],
                'enums': deduplicated_data['enums'],
                'total_nodes': self.count_nodes(root_node),
                'file_size': len(content)
            }
            
        except Exception as e:
            return {
                'file_path': to_relative_path(file_path),
                'parse_success': False,
                'error': str(e)
            }
    
    def deduplicate_elements(self, file_data):
        """
        通用去重方法：基于start_byte和end_byte的包含关系去重
        如果元素A完全包含元素B，则移除被包含的元素B
        """
        all_elements = []
        
        # 收集所有元素，添加类型标记
        for element_type in ['functions', 'structs', 'typedefs', 'variables', 'macros', 'enums']:
            if element_type in file_data:
                for element in file_data[element_type]:
                    if 'start_byte' in element and 'end_byte' in element:
                        element_with_type = element.copy()
                        element_with_type['_element_type'] = element_type
                        all_elements.append(element_with_type)
        
        # 按start_byte排序
        all_elements.sort(key=lambda x: x['start_byte'])
        
        # 去重：移除被完全包含的元素
        filtered_elements = []
        for i, current in enumerate(all_elements):
            is_contained = False
            
            # 检查是否被其他元素完全包含
            for j, other in enumerate(all_elements):
                if i != j:
                    # other完全包含current
                    if (other['start_byte'] <= current['start_byte'] and 
                        other['end_byte'] >= current['end_byte'] and
                        (other['start_byte'] != current['start_byte'] or 
                         other['end_byte'] != current['end_byte'])):
                        is_contained = True
                        break
            
            if not is_contained:
                filtered_elements.append(current)
        
        # 重新分组到各个类型
        result = {}
        for element_type in ['functions', 'structs', 'typedefs', 'variables', 'macros', 'enums']:
            result[element_type] = []
            for element in filtered_elements:
                if element.get('_element_type') == element_type:
                    # 移除临时的类型标记
                    clean_element = {k: v for k, v in element.items() if k != '_element_type'}
                    result[element_type].append(clean_element)
        
        return result
    
    def extract_functions(self, node, content, root_node):
        """提取函数定义和声明"""
        functions = []
        
        def traverse(node):
            if node.type == 'function_definition':
                func_info = self.parse_function(node, content, root_node)
                if func_info:
                    functions.append(func_info)
            elif node.type == 'declaration':
                # 检查是否是函数声明（包括指针返回类型）
                has_function_declarator = False
                for child in node.children:
                    if child.type == 'function_declarator':
                        has_function_declarator = True
                        break
                    elif child.type == 'pointer_declarator':
                        # 检查指针声明中是否包含函数声明
                        def check_pointer_declarator(ptr_node):
                            for subchild in ptr_node.children:
                                if subchild.type == 'function_declarator':
                                    return True
                                elif subchild.type == 'pointer_declarator':
                                    if check_pointer_declarator(subchild):
                                        return True
                            return False
                        if check_pointer_declarator(child):
                            has_function_declarator = True
                            break
                
                if has_function_declarator:
                    func_info = self.parse_function_declaration(node, content, root_node)
                    if func_info:
                        functions.append(func_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return functions
    
    def correct_byte_offset(self, node, content, original_func_name=None):
        """修正Tree-sitter的字节偏移错误"""
        try:
            # 获取Tree-sitter报告的位置
            ts_start = node.start_byte
            ts_end = node.end_byte
            
            # 先尝试从修正后的内容中提取函数名
            corrected_func_name = self.extract_function_name_from_content(ts_start, ts_end, content)
            
            if corrected_func_name:
                # 使用提取到的函数名来查找正确的位置
                search_func_name = corrected_func_name
            elif original_func_name:
                # 使用原始函数名
                search_func_name = original_func_name
            else:
                # 都没有，返回原始位置
                return ts_start, ts_end
            
            # 在原始内容中搜索正确的函数位置
            func_name_positions = []
            start_pos = 0
            while True:
                pos = content.find(search_func_name, start_pos)
                if pos == -1:
                    break
                func_name_positions.append(pos)
                start_pos = pos + 1
            
            if not func_name_positions:
                return ts_start, ts_end
            
            # 找到最接近Tree-sitter报告位置的函数名
            best_func_pos = min(func_name_positions, key=lambda x: abs(x - ts_start))
            
            # 从函数名位置向前搜索，找到函数定义的真正开始
            lines_before = content[:best_func_pos].split('\n')
            current_line_start = len('\n'.join(lines_before[:-1])) + (1 if len(lines_before) > 1 else 0)
            current_line = lines_before[-1] if lines_before else ""
            
            # 检查函数名前面是否有其他tokens（返回类型等）
            prefix = current_line[:best_func_pos - current_line_start]
            tokens = prefix.strip().split()
            
            if tokens:
                # 当前行有返回类型或修饰符，从行开始算
                corrected_start = current_line_start
            else:
                # 当前行只有函数名，检查上一行是否有返回类型
                if len(lines_before) >= 2:
                    prev_line = lines_before[-2].strip()
                    if prev_line and not prev_line.endswith(';') and not prev_line.startswith('//') and not prev_line.startswith('/*'):
                        # 上一行可能是返回类型，从上一行开始
                        prev_line_start = len('\n'.join(lines_before[:-2])) + (1 if len(lines_before) > 2 else 0)
                        corrected_start = prev_line_start
                    else:
                        corrected_start = current_line_start
                else:
                    corrected_start = current_line_start
            
            # 对于函数定义，结束位置通常是正确的
            corrected_end = ts_end
            
            return corrected_start, corrected_end
            
        except Exception:
            # 出错时使用原始位置
            return node.start_byte, node.end_byte
    
    def extract_function_name_from_content(self, start_byte, end_byte, content):
        """从指定字节范围中提取函数名"""
        try:
            section_content = content[start_byte:end_byte]
            
            # 使用正则表达式匹配函数名
            import re
            
            # 匹配函数定义的模式
            patterns = [
                r'(?:static\s+)?(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*\{',  # 完整模式：[static] 返回类型 函数名(参数){
                r'\b(\w+)\s*\([^)]*\)\s*\{',  # 简单模式：函数名(参数){
            ]
            
            for pattern in patterns:
                match = re.search(pattern, section_content)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception:
            return None

    def parse_function(self, node, content, root_node):
        """解析函数定义"""
        try:
            # 首先修正字节偏移
            corrected_start, corrected_end = self.correct_byte_offset(node, content)
            
            # 从修正后的内容中提取函数名
            func_name = self.extract_function_name_from_content(corrected_start, corrected_end, content)
            
            # 如果没有提取到函数名，尝试使用Tree-sitter的结果作为备选
            if not func_name:
                def find_function_info(child_node):
                    nonlocal func_name
                    if child_node.type == 'function_declarator':
                        for subchild in child_node.children:
                            if subchild.type == 'identifier':
                                func_name = content[subchild.start_byte:subchild.end_byte]
                                break
                    elif child_node.type == 'pointer_declarator':
                        for subchild in child_node.children:
                            find_function_info(subchild)
                
                for child in node.children:
                    if child.type == 'function_declarator':
                        find_function_info(child)
                    elif child.type == 'pointer_declarator':
                        find_function_info(child)
            
            if not func_name:
                return None
            
            # 提取其他信息
            return_type = None
            parameters = []
            
            def find_function_info(child_node):
                nonlocal parameters
                if child_node.type == 'function_declarator':
                    for subchild in child_node.children:
                        if subchild.type == 'parameter_list':
                            parameters = self.parse_parameters(subchild, content)
                elif child_node.type == 'pointer_declarator':
                    for subchild in child_node.children:
                        find_function_info(subchild)
            
            for child in node.children:
                if child.type == 'primitive_type' or child.type == 'type_identifier':
                    return_type = content[child.start_byte:child.end_byte].strip()
                elif child.type == 'function_declarator':
                    find_function_info(child)
                elif child.type == 'pointer_declarator':
                    find_function_info(child)
            
            # 提取完整的函数定义内容（使用修正后的位置）
            full_definition = content[corrected_start:corrected_end]
            
            # 提取函数签名（不包括函数体）
            signature = self.extract_function_signature_corrected(corrected_start, corrected_end, content)
            
            # 提取前置注释
            comment = self.extract_preceding_comment(node, root_node, content)
            
            result = {
                'name': func_name,
                'type': 'definition',
                # 'return_type': return_type if return_type else '',
                # 'parameters': parameters,
                'start_line': node.start_point[0] + 1,
                'end_line': node.end_point[0] + 1,
                'start_byte': corrected_start,
                'end_byte': corrected_end,
                'signature': signature,
                'full_definition': full_definition,
                'comment': comment if comment else ''
            }
                
            return result
        except:
            pass
        return None
    
    def extract_function_signature_corrected(self, start_byte, end_byte, content):
        """使用修正后的字节位置提取函数签名"""
        try:
            full_text = content[start_byte:end_byte]
            
            # 查找函数体的开始位置（第一个 { ）
            brace_pos = full_text.find('{')
            if brace_pos >= 0:
                # 函数签名是从开始到第一个大括号之前
                signature = full_text[:brace_pos].strip()
                return signature
            
            # 如果没有找到大括号，可能是声明，返回整个内容
            return full_text.strip()
        except:
            return content[start_byte:end_byte].strip()

    def parse_function_declaration(self, node, content, root_node):
        """解析函数声明"""
        try:
            # 首先修正字节偏移
            corrected_start, corrected_end = self.correct_byte_offset(node, content)
            
            # 从修正后的内容中提取函数名
            func_name = self.extract_function_name_from_content(corrected_start, corrected_end, content)
            
            # 如果没有提取到函数名，尝试使用Tree-sitter的结果作为备选
            if not func_name:
                def find_function_info(child_node):
                    nonlocal func_name
                    if child_node.type == 'function_declarator':
                        for subchild in child_node.children:
                            if subchild.type == 'identifier':
                                func_name = content[subchild.start_byte:subchild.end_byte]
                                break
                    elif child_node.type == 'pointer_declarator':
                        for subchild in child_node.children:
                            find_function_info(subchild)
                
                for child in node.children:
                    if child.type == 'function_declarator':
                        find_function_info(child)
                    elif child.type == 'pointer_declarator':
                        find_function_info(child)
            
            if not func_name:
                return None
            
            # 提取其他信息
            return_type = None
            parameters = []
            
            def find_function_info(child_node):
                nonlocal parameters
                if child_node.type == 'function_declarator':
                    for subchild in child_node.children:
                        if subchild.type == 'parameter_list':
                            parameters = self.parse_parameters(subchild, content)
                elif child_node.type == 'pointer_declarator':
                    for subchild in child_node.children:
                        find_function_info(subchild)
            
            for child in node.children:
                if child.type == 'primitive_type' or child.type == 'type_identifier':
                    return_type = content[child.start_byte:child.end_byte].strip()
                elif child.type == 'function_declarator':
                    find_function_info(child)
                elif child.type == 'pointer_declarator':
                    find_function_info(child)
            
            # 提取完整的函数声明内容（使用修正后的位置）
            full_declaration = content[corrected_start:corrected_end].strip()
            
            # 提取前置注释
            comment = self.extract_preceding_comment(node, root_node, content)
            
            result = {
                'name': func_name,
                'type': 'declaration',
                # 'return_type': return_type if return_type else '',
                # 'parameters': parameters,
                'start_line': node.start_point[0] + 1,
                'end_line': node.end_point[0] + 1,
                'start_byte': corrected_start,
                'end_byte': corrected_end,
                'full_declaration': full_declaration,
                'comment': comment if comment else ''
            }
                
            return result
        except:
            pass
        return None
    
    def parse_parameters(self, param_node, content):
        """解析函数参数"""
        parameters = []
        for child in param_node.children:
            if child.type == 'parameter_declaration':
                param_text = content[child.start_byte:child.end_byte].strip()
                if param_text and param_text != ',':
                    parameters.append(param_text)
        return parameters
    
    def extract_function_signature(self, node, content):
        """提取函数签名（不包括函数体）"""
        try:
            # 查找函数体的开始位置
            for child in node.children:
                if child.type == 'compound_statement':
                    # 函数签名是从函数开始到函数体开始之前
                    signature_end = child.start_byte
                    signature = content[node.start_byte:signature_end].strip()
                    return signature
            # 如果没有找到函数体，返回整个节点内容
            return content[node.start_byte:node.end_byte].strip()
        except:
            return content[node.start_byte:node.end_byte].strip()
    
    def extract_structs(self, node, content, root_node):
        """提取结构体定义"""
        structs = []
        
        def traverse(node):
            if node.type == 'struct_specifier':
                struct_name = None
                for child in node.children:
                    if child.type == 'type_identifier':
                        struct_name = content[child.start_byte:child.end_byte]
                        break
                
                if struct_name:
                    # 提取完整的结构体定义
                    full_definition = content[node.start_byte:node.end_byte]
                    
                    # 提取结构体字段
                    fields = self.extract_struct_fields(node, content)
                    
                    # 提取前置注释
                    comment = self.extract_preceding_comment(node, root_node, content)
                    
                    struct_info = {
                        'name': struct_name,
                        'start_line': node.start_point[0] + 1,
                        'end_line': node.end_point[0] + 1,
                        'start_byte': node.start_byte,
                        'end_byte': node.end_byte,
                        'full_definition': full_definition,
                        'fields': fields,
                        'comment': comment if comment else ''
                    }
                        
                    structs.append(struct_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return structs
    
    def extract_struct_fields(self, struct_node, content):
        """提取结构体字段"""
        fields = []
        
        def traverse(node):
            if node.type == 'field_declaration':
                field_text = content[node.start_byte:node.end_byte].strip()
                if field_text:
                    fields.append({
                        'text': field_text,
                        'line': node.start_point[0] + 1,
                        'start_line': node.start_point[0] + 1,
                        'end_line': node.end_point[0] + 1,
                        'start_byte': node.start_byte,
                        'end_byte': node.end_byte
                    })
            
            for child in node.children:
                traverse(child)
        
        traverse(struct_node)
        return fields
    
    def extract_includes(self, node, content):
        """提取预处理包含指令"""
        includes = []
        
        def traverse(node):
            if node.type == 'preproc_include':
                include_text = content[node.start_byte:node.end_byte].strip()
                includes.append({
                    'text': include_text,
                    'line': node.start_point[0] + 1,
                    'start_line': node.start_point[0] + 1,
                    'end_line': node.end_point[0] + 1,
                    'start_byte': node.start_byte,
                    'end_byte': node.end_byte
                })
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return includes
    
    def extract_global_variables(self, node, content, root_node):
        """提取全局变量声明，包括静态常量和计算型变量"""
        variables = []
        
        def is_function_declaration(text):
            """更精确地判断是否为函数声明"""
            # 简单的启发式规则：
            # 1. 如果包含 = 号，很可能是变量赋值
            if '=' in text:
                return False
            
            # 2. 如果有括号但没有等号，且括号前有标识符，可能是函数
            if '(' in text and ')' in text:
                paren_pos = text.find('(')
                before_paren = text[:paren_pos].strip()
                
                # 检查括号前最后一个token是否像函数名
                if before_paren:
                    tokens = before_paren.split()
                    if len(tokens) > 0:
                        last_token = tokens[-1].rstrip('*')  # 移除指针星号
                        # 如果最后一个token是有效的标识符，且整行不包含赋值
                        if last_token.replace('_', '').isalnum() and last_token[0].isalpha():
                            # 检查括号后是否直接跟分号（函数声明）
                            after_paren = text[text.rfind(')') + 1:].strip()
                            if after_paren == ';' or after_paren.startswith(';'):
                                return True
            
            return False
        
        def traverse(node):
            if (node.type == 'declaration' and 
                node.parent and node.parent.type == 'translation_unit'):
                # 这是一个顶级声明
                var_text = content[node.start_byte:node.end_byte].strip()
                if (var_text and 
                    not var_text.startswith('typedef') and
                    not is_function_declaration(var_text)):
                    
                    # 提取前置注释
                    comment = self.extract_preceding_comment(node, root_node, content)
                    
                    var_info = {
                        'text': var_text,
                        'line': node.start_point[0] + 1,
                        'start_line': node.start_point[0] + 1,
                        'end_line': node.end_point[0] + 1,
                        'start_byte': node.start_byte,
                        'end_byte': node.end_byte,
                        'comment': comment if comment else ''
                    }
                        
                    variables.append(var_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return variables
    
    def extract_typedefs(self, node, content, root_node):
        """提取typedef定义"""
        typedefs = []
        
        def traverse(node):
            if node.type == 'type_definition':
                # 提取完整的typedef定义
                typedef_text = content[node.start_byte:node.end_byte].strip()
                if typedef_text:
                    # 尝试提取typedef的名称
                    typedef_name = self.extract_typedef_name(node, content)
                    
                    # 提取前置注释
                    comment = self.extract_preceding_comment(node, root_node, content)
                    
                    typedef_info = {
                        'text': typedef_text,
                        'name': typedef_name if typedef_name else '',
                        'line': node.start_point[0] + 1,
                        'start_line': node.start_point[0] + 1,
                        'end_line': node.end_point[0] + 1,
                        'start_byte': node.start_byte,
                        'end_byte': node.end_byte,
                        'comment': comment if comment else ''
                    }
                        
                    typedefs.append(typedef_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return typedefs
    
    def extract_typedef_name(self, typedef_node, content):
        """提取typedef的名称"""
        try:
            # 对于函数指针typedef，需要特殊处理
            # 例如: typedef unsigned int (*BloomFilterHashFunc)(BloomFilterValue data);
            # 真正的typedef名称是括号中的标识符
            
            # 首先检查是否是函数指针typedef
            typedef_text = content[typedef_node.start_byte:typedef_node.end_byte]
            if '(*' in typedef_text and ')(' in typedef_text:
                # 这是函数指针typedef，提取括号中的名称
                import re
                # 匹配 (*名称) 模式
                match = re.search(r'\(\s*\*\s*(\w+)\s*\)', typedef_text)
                if match:
                    return match.group(1)
            
            # 对于普通typedef，查找所有标识符
            identifiers = []
            type_identifiers = []
            
            def find_identifiers(node):
                if node.type == 'identifier':
                    identifiers.append(content[node.start_byte:node.end_byte])
                elif node.type == 'type_identifier':
                    type_identifiers.append(content[node.start_byte:node.end_byte])
                for child in node.children:
                    find_identifiers(child)
            
            find_identifiers(typedef_node)
            
            # 对于普通typedef，typedef名称通常是最后一个identifier或type_identifier
            # 优先使用identifier（新定义的类型名），然后使用type_identifier
            if identifiers:
                return identifiers[-1]
            elif type_identifiers:
                return type_identifiers[-1]
            else:
                return None
        except:
            return None
    
    def extract_macros(self, node, content, root_node):
        """提取宏定义 (#define)"""
        macros = []
        
        def traverse(node):
            if node.type == 'preproc_def':
                # 提取完整的宏定义
                macro_text = content[node.start_byte:node.end_byte].strip()
                if macro_text:
                    # 提取宏名称
                    macro_name = self.extract_macro_name(node, content)
                    
                    # 提取前置注释
                    comment = self.extract_preceding_comment(node, root_node, content)
                    
                    macro_info = {
                        'text': macro_text,
                        'name': macro_name if macro_name else '',
                        'line': node.start_point[0] + 1,
                        'start_line': node.start_point[0] + 1,
                        'end_line': node.end_point[0] + 1,
                        'start_byte': node.start_byte,
                        'end_byte': node.end_byte,
                        'comment': comment if comment else ''
                    }
                        
                    macros.append(macro_info)
            # 也检查其他可能的预处理器节点类型
            elif node.type in ['preproc_function_def', 'preproc_call']:
                macro_text = content[node.start_byte:node.end_byte].strip()
                if macro_text.startswith('#define'):
                    # 提取宏名称
                    macro_name = self.extract_macro_name(node, content)
                    
                    # 提取前置注释
                    comment = self.extract_preceding_comment(node, root_node, content)
                    
                    macro_info = {
                        'text': macro_text,
                        'name': macro_name if macro_name else '',
                        'line': node.start_point[0] + 1,
                        'start_line': node.start_point[0] + 1,
                        'end_line': node.end_point[0] + 1,
                        'start_byte': node.start_byte,
                        'end_byte': node.end_byte,
                        'comment': comment if comment else ''
                    }
                        
                    macros.append(macro_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        
        return macros
    
    def extract_macro_name(self, macro_node, content):
        """提取宏定义的名称"""
        try:
            # 宏的名称是#define后的第一个identifier
            for child in macro_node.children:
                if child.type == 'identifier':
                    return content[child.start_byte:child.end_byte]
            return None
        except:
            return None
    
    def extract_enums(self, node, content, root_node):
        """提取枚举定义"""
        enums = []
        
        def traverse(node):
            if node.type == 'enum_specifier':
                enum_info = self.parse_enum(node, content, root_node)
                if enum_info:
                    enums.append(enum_info)
            
            for child in node.children:
                traverse(child)
        
        traverse(node)
        return enums
    
    def parse_enum(self, node, content, root_node):
        """解析枚举定义"""
        try:
            enum_name = None
            enumerators = []
            
            for child in node.children:
                if child.type == 'type_identifier':
                    enum_name = content[child.start_byte:child.end_byte]
                elif child.type == 'enumerator_list':
                    for enumerator_child in child.children:
                        if enumerator_child.type == 'enumerator':
                            enumerator_text = content[enumerator_child.start_byte:enumerator_child.end_byte]
                            enumerators.append(enumerator_text.strip())
            
            # 提取完整的枚举定义
            full_definition = content[node.start_byte:node.end_byte]
            
            # 提取前置注释
            comment = self.extract_preceding_comment(node, root_node, content)
            
            result = {
                'name': enum_name if enum_name else 'anonymous',
                'enumerators': enumerators,
                'start_line': node.start_point[0] + 1,
                'end_line': node.end_point[0] + 1,
                'start_byte': node.start_byte,
                'end_byte': node.end_byte,
                'full_definition': full_definition,
                'comment': comment if comment else ''
            }
                
            return result
        except:
            pass
        return None
    
    def extract_preceding_comment(self, target_node, root_node, content):
        """使用Tree-sitter提取目标节点前面的注释"""
        try:
            # 收集所有注释节点
            comment_nodes = []
            
            def collect_comments(node):
                if node.type == 'comment':
                    comment_nodes.append(node)
                for child in node.children:
                    collect_comments(child)
            
            collect_comments(root_node)
            
            # 找到目标节点前面最近的注释
            target_start_line = target_node.start_point[0]
            preceding_comments = []
            
            for comment in comment_nodes:
                comment_end_line = comment.end_point[0]
                # 注释必须在目标节点之前，且距离不能太远（最多3行空行）
                if comment_end_line < target_start_line and (target_start_line - comment_end_line) <= 3:
                    preceding_comments.append(comment)
            
            if not preceding_comments:
                return None
            
            # 按行号排序，取最接近的连续注释块
            preceding_comments.sort(key=lambda x: x.start_point[0])
            
            # 找到最后一个连续的注释块
            final_comments = []
            if preceding_comments:
                # 从最后一个注释开始，向前查找连续的注释
                last_comment = preceding_comments[-1]
                final_comments.append(last_comment)
                
                for i in range(len(preceding_comments) - 2, -1, -1):
                    current_comment = preceding_comments[i]
                    # 如果当前注释和下一个注释之间只有很少行数（<=2），认为是连续的
                    if (final_comments[0].start_point[0] - current_comment.end_point[0]) <= 2:
                        final_comments.insert(0, current_comment)
                    else:
                        break
            
            # 提取注释内容并清理
            if final_comments:
                comment_texts = []
                for comment in final_comments:
                    comment_text = content[comment.start_byte:comment.end_byte]
                    # 清理注释标记
                    if comment_text.startswith('//'):
                        clean_text = comment_text[2:].strip()
                    elif comment_text.startswith('/*') and comment_text.endswith('*/'):
                        clean_text = comment_text[2:-2].strip()
                    else:
                        clean_text = comment_text.strip()
                    
                    if clean_text:
                        comment_texts.append(clean_text)
                
                return ' '.join(comment_texts) if comment_texts else None
            
            return None
            
        except Exception:
            return None
    
    def count_nodes(self, node):
        """统计AST节点数量"""
        count = 1
        for child in node.children:
            count += self.count_nodes(child)
        return count
    
    def analyze_project(self, project_path=None):
        """分析整个C工程"""
        if project_path is None:
            project_path = self.project_root
        project_path = Path(project_path).resolve()

        print(f"🔍 开始分析C工程: {project_path}")
        print("=" * 60)
        
        # 查找所有C和H文件
        c_files, h_files = self.find_c_files(project_path)
        all_files = c_files + h_files
        
        print(f"📁 发现文件:")
        print(f"   • C文件: {len(c_files)}个")
        print(f"   • H文件: {len(h_files)}个")
        print(f"   • 总计: {len(all_files)}个")
        print()
        
        if not all_files:
            print("❌ 未找到任何C/H文件")
            return
        
        # 逐个解析文件
        print("🔄 正在解析文件...")
        successful_parses = 0
        total_functions = 0
        total_structs = 0
        total_typedefs = 0
        total_macros = 0
        total_enums = 0
        
        for i, file_path in enumerate(all_files):
            rel_for_display = to_relative_path(file_path)
            print(f"   [{i+1:3d}/{len(all_files)}] {rel_for_display}")

            result = self.parse_single_file(file_path)
            self.analysis_results[result['file_path']] = result
            
            if result['parse_success']:
                successful_parses += 1
                total_functions += len(result['functions'])
                total_structs += len(result['structs'])
                total_typedefs += len(result['typedefs'])
                total_macros += len(result['macros'])
                total_enums += len(result['enums'])
        
        print()
        print("📊 分析结果统计:")
        print(f"   • 成功解析: {successful_parses}/{len(all_files)} 文件")
        print(f"   • 总函数数: {total_functions}")
        print(f"   • 总结构体: {total_structs}")
        print(f"   • 总typedef: {total_typedefs}")
        print(f"   • 总宏定义: {total_macros}")
        print(f"   • 总枚举: {total_enums}")
        print()

        # 显示详细结果
        self.display_detailed_results(project_path)
    
    def display_detailed_results(self, project_path):
        """显示详细的分析结果"""
        print("📋 详细分析结果:")
        print("-" * 60)
        
        for file_path, result in self.analysis_results.items():
            relative_path = file_path
            
            if result['parse_success']:
                print(f"\n📄 {relative_path}")
                print(f"   • 函数: {len(result['functions'])}个")
                print(f"   • 结构体: {len(result['structs'])}个")
                print(f"   • typedef: {len(result['typedefs'])}个")
                print(f"   • 包含指令: {len(result['includes'])}个")
                print(f"   • AST节点: {result['total_nodes']}个")
                
                # 显示函数列表
                if result['functions']:
                    print("   📝 函数列表:")
                    for func in result['functions'][:5]:  # 只显示前5个
                        print(f"      - {func['name']}() [{func['type']}]")
                    if len(result['functions']) > 5:
                        print(f"      ... 还有{len(result['functions'])-5}个函数")
                
                # 显示结构体列表
                if result['structs']:
                    print("   📦 结构体列表:")
                    for struct in result['structs']:
                        print(f"      - struct {struct['name']}")
                
                # 显示typedef列表
                if result['typedefs']:
                    print("   🏷️  typedef列表:")
                    for typedef in result['typedefs'][:3]:  # 只显示前3个
                        name = typedef['name'] if typedef['name'] else '?'
                        print(f"      - {name}")
                    if len(result['typedefs']) > 3:
                        print(f"      ... 还有{len(result['typedefs'])-3}个typedef")
            else:
                print(f"\n❌ {relative_path} - 解析失败: {result['error']}")
        
        print("\n✅ C工程分析完成!")
    
    def save_results(self, output_file):
        """保存分析结果到JSON文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        print(f"💾 分析结果已保存到: {output_file}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='C项目分析器')
    parser.add_argument('project_path', nargs='?', default=None,
                        help='要分析的C项目路径（默认读取配置文件）')
    parser.add_argument('-o', '--output', default="output/c_project_analysis.json",
                       help='输出JSON文件路径')
    parser.add_argument('--debug', action='store_true',
                       help='启用调试模式')
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = CProjectAnalyzer()
    
    if args.project_path:
        project_path = Path(args.project_path).resolve()
        if not project_path.exists():
            print(f"❌ 工程路径不存在: {project_path}")
            print("请提供正确的C工程路径")
            return
    else:
        project_path = analyzer.project_root

    print(f"🔍 开始分析项目: {project_path}")
    analyzer.analyze_project(project_path)

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path(__file__).resolve().parent / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    analyzer.save_results(str(output_path))

if __name__ == "__main__":
    main()
