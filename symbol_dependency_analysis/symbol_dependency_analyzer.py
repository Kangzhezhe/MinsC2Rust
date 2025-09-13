#!/usr/bin/env python3
"""
C代码符号依赖关系分析器
基于tree-sitter AST和c_project_analysis.json构建符号依赖图
"""

import json
import os
import tree_sitter_c as ts_c
from tree_sitter import Language, Parser, Node
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import re
from pathlib import Path

class SymbolType(Enum):
    """符号类型枚举"""
    FUNCTION = "functions"
    STRUCT = "structs"
    TYPEDEF = "typedefs"
    VARIABLE = "variables"
    MACRO = "macros"
    ENUM = "enums"

class DependencyType(Enum):
    """依赖类型枚举"""
    FUNCTION_CALL = "function_call"      # 函数调用
    TYPE_REFERENCE = "type_reference"    # 类型引用
    VARIABLE_USE = "variable_use"        # 变量使用
    MACRO_USE = "macro_use"              # 宏使用
    ENUM_USE = "enum_use"                # 枚举使用
    STRUCT_MEMBER = "struct_member"      # 结构体成员访问

@dataclass
class Symbol:
    """符号信息"""
    name: str
    symbol_type: SymbolType
    file_path: str
    start_line: int = 0
    end_line: int = 0
    definition: str = ""
    
    def __hash__(self):
        return hash((self.name, self.symbol_type.value, self.file_path))
    
    def __eq__(self, other):
        if not isinstance(other, Symbol):
            return False
        return (self.name == other.name and 
                self.symbol_type == other.symbol_type and 
                self.file_path == other.file_path)

@dataclass
class Dependency:
    """依赖关系"""
    source_symbol: Symbol
    target_symbol: Symbol
    dependency_type: DependencyType
    location: Tuple[int, int] = (0, 0)  # (start_line, end_line)
    context: str = ""  # 依赖发生的上下文代码

@dataclass
class SymbolDependencyGraph:
    """符号依赖图"""
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    dependencies: List[Dependency] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        self._dependency_set: Set[str] = set()  # 用于检测重复依赖
    
    def add_symbol(self, symbol: Symbol):
        """添加符号"""
        key = f"{symbol.name}:{symbol.symbol_type.value}:{symbol.file_path}"
        self.symbols[key] = symbol
    
    def add_dependency(self, dependency: Dependency):
        """添加依赖关系（自动去重）"""
        # 创建依赖关系的唯一标识（不包括具体的符号实例和位置）
        dep_signature = (
            dependency.source_symbol.name,
            dependency.source_symbol.symbol_type.value,
            dependency.source_symbol.file_path,
            dependency.target_symbol.name,
            dependency.target_symbol.symbol_type.value,
            dependency.target_symbol.file_path,
            dependency.dependency_type.value
        )
        
        # 只添加不重复的依赖关系
        dep_key = str(dep_signature)
        if not hasattr(self, '_dependency_set'):
            self._dependency_set = set()
            
        if dep_key not in self._dependency_set:
            self.dependencies.append(dependency)
            self._dependency_set.add(dep_key)
            return True  # 成功添加
        return False  # 重复，未添加
    
    def get_symbol_dependencies(self, symbol_name: str, symbol_type: SymbolType = None) -> List[Dependency]:
        """获取指定符号的所有依赖"""
        dependencies = []
        for dep in self.dependencies:
            if dep.source_symbol.name == symbol_name:
                if symbol_type is None or dep.source_symbol.symbol_type == symbol_type:
                    dependencies.append(dep)
        return dependencies
    
    def get_symbols_by_type(self, symbol_type: SymbolType) -> List[Symbol]:
        """根据类型获取符号"""
        return [symbol for symbol in self.symbols.values() 
                if symbol.symbol_type == symbol_type]
    
    def get_symbol_dependents(self, symbol_name: str, symbol_type: SymbolType = None) -> List[Dependency]:
        """获取依赖指定符号的所有依赖关系（被依赖）"""
        dependents = []
        for dep in self.dependencies:
            if dep.target_symbol.name == symbol_name:
                if symbol_type is None or dep.target_symbol.symbol_type == symbol_type:
                    dependents.append(dep)
        return dependents
    
    def get_all_related_symbols(self, symbol_name: str, max_depth: int = 2) -> Set[str]:
        """获取与指定符号相关的所有符号（包括依赖和被依赖）"""
        related = set()
        to_visit = [(symbol_name, 0)]
        visited = set()
        
        while to_visit:
            current_symbol, depth = to_visit.pop(0)
            if current_symbol in visited or depth > max_depth:
                continue
            
            visited.add(current_symbol)
            related.add(current_symbol)
            
            if depth < max_depth:
                # 添加依赖的符号
                deps = self.get_symbol_dependencies(current_symbol)
                for dep in deps:
                    if dep.target_symbol.name not in visited:
                        to_visit.append((dep.target_symbol.name, depth + 1))
                
                # 添加被依赖的符号
                dependents = self.get_symbol_dependents(current_symbol)
                for dep in dependents:
                    if dep.source_symbol.name not in visited:
                        to_visit.append((dep.source_symbol.name, depth + 1))
        
        return related

class SymbolDependencyAnalyzer:
    """符号依赖关系分析器"""
    
    def __init__(self, analysis_json_path: str):
        """初始化分析器"""
        self.analysis_json_path = analysis_json_path
        self.C_LANGUAGE = Language(ts_c.language())
        self.parser = Parser(self.C_LANGUAGE)
        
        # 加载分析结果
        with open(analysis_json_path, 'r', encoding='utf-8') as f:
            self.analysis_data = json.load(f)
        
        # 初始化依赖图
        self.dependency_graph = SymbolDependencyGraph()
        
        # 符号注册表：存储所有已知符号
        self.symbol_registry: Dict[str, List[Symbol]] = {}
        
        # C语言关键字和内置类型，需要排除
        self.c_keywords = {
            'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
            'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
            'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
            'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while',
            # C99/C11 keywords
            'inline', 'restrict', '_Bool', '_Complex', '_Imaginary',
            # Common types
            'size_t', 'ssize_t', 'ptrdiff_t', 'NULL'
        }
        
        # 内置函数，需要排除
        self.builtin_functions = {
            'malloc', 'free', 'calloc', 'realloc', 'printf', 'scanf', 'strlen',
            'strcpy', 'strcmp', 'strncmp', 'strcat', 'memcpy', 'memset', 'memcmp'
        }
    
    def build_symbol_registry(self):
        """构建符号注册表"""
        print("构建符号注册表...")
        
        for file_path, file_data in self.analysis_data.items():
            if not file_data.get('parse_success', False):
                continue
            
            # 注册各种类型的符号
            for symbol_type in SymbolType:
                symbol_list = file_data.get(symbol_type.value, [])
                for symbol_data in symbol_list:
                    symbol = self._create_symbol_from_data(symbol_data, symbol_type, file_path)
                    if symbol:
                        self.dependency_graph.add_symbol(symbol)
                        
                        # 添加到注册表
                        if symbol.name not in self.symbol_registry:
                            self.symbol_registry[symbol.name] = []
                        self.symbol_registry[symbol.name].append(symbol)
        
        print(f"符号注册表构建完成：共注册 {len(self.symbol_registry)} 个符号名称")
    
    def _create_symbol_from_data(self, symbol_data: dict, symbol_type: SymbolType, file_path: str) -> Optional[Symbol]:
        """从JSON数据创建Symbol对象"""
        name = symbol_data.get('name', '')
        if not name or name in self.c_keywords:
            return None
        
        symbol = Symbol(
            name=name,
            symbol_type=symbol_type,
            file_path=file_path,
            start_line=symbol_data.get('start_line', 0),
            end_line=symbol_data.get('end_line', 0),
            definition=symbol_data.get('full_definition', '') or symbol_data.get('text', '')
        )
        
        return symbol
    
    def is_valid_symbol_reference(self, name: str, context_node: Node = None) -> bool:
        """判断一个名称是否是有效的符号引用"""
        if not name or name in self.c_keywords or name in self.builtin_functions:
            return False
        
        # 检查是否是数字或字符串字面量
        if name.isdigit() or (name.startswith('"') and name.endswith('"')):
            return False
        
        # 检查是否在符号注册表中
        return name in self.symbol_registry
    
    def extract_dependencies_from_text(self, text: str, source_symbol: Symbol) -> List[Dependency]:
        """从文本中提取依赖关系"""
        dependencies = []
        
        # 使用tree-sitter解析代码片段
        try:
            tree = self.parser.parse(bytes(text, "utf8"))
            root_node = tree.root_node
            dependencies.extend(self._extract_dependencies_from_ast(root_node, text, source_symbol))
        except Exception as e:
            print(f"解析代码片段失败 {source_symbol.name}: {e}")
            # 回退到简单的文本匹配
            dependencies.extend(self._extract_dependencies_by_pattern(text, source_symbol))
        
        return dependencies
    
    def _extract_dependencies_from_ast(self, node: Node, text: str, source_symbol: Symbol) -> List[Dependency]:
        """基于AST提取依赖关系"""
        dependencies = []
        local_variables = set()  # 存储局部变量名
        
        def collect_local_variables(node: Node):
            """收集局部变量声明"""
            if node.type == 'declaration':
                declarator = node.child_by_field_name('declarator')
                if declarator:
                    if declarator.type == 'identifier':
                        var_name = text[declarator.start_byte:declarator.end_byte]
                        local_variables.add(var_name)
                    elif declarator.type == 'init_declarator':
                        declarator_node = declarator.child_by_field_name('declarator')
                        if declarator_node and declarator_node.type == 'identifier':
                            var_name = text[declarator_node.start_byte:declarator_node.end_byte]
                            local_variables.add(var_name)
            
            # 参数声明
            elif node.type == 'parameter_declaration':
                declarator = node.child_by_field_name('declarator')
                if declarator and declarator.type == 'identifier':
                    var_name = text[declarator.start_byte:declarator.end_byte]
                    local_variables.add(var_name)
            
            # 递归收集
            for child in node.children:
                collect_local_variables(child)
        
        def traverse_node(node: Node):
            # 函数调用
            if node.type == 'call_expression':
                func_node = node.child_by_field_name('function')
                if func_node:
                    if func_node.type == 'identifier':
                        func_name = text[func_node.start_byte:func_node.end_byte]
                        if self.is_valid_symbol_reference(func_name) and func_name not in local_variables:
                            dependencies.extend(self._create_dependencies_for_name(
                                func_name, source_symbol, DependencyType.FUNCTION_CALL, func_node
                            ))
                    elif func_node.type == 'field_expression':
                        # 处理结构体成员函数调用 obj.func()
                        field_node = func_node.child_by_field_name('field')
                        if field_node and field_node.type == 'field_identifier':
                            field_name = text[field_node.start_byte:field_node.end_byte]
                            if self.is_valid_symbol_reference(field_name):
                                dependencies.extend(self._create_dependencies_for_name(
                                    field_name, source_symbol, DependencyType.FUNCTION_CALL, field_node
                                ))
            
            # 类型声明和转换
            elif node.type in ['type_identifier', 'struct_specifier', 'union_specifier', 'enum_specifier']:
                if node.type == 'type_identifier':
                    type_name = text[node.start_byte:node.end_byte]
                    if self.is_valid_symbol_reference(type_name):
                        dependencies.extend(self._create_dependencies_for_name(
                            type_name, source_symbol, DependencyType.TYPE_REFERENCE, node
                        ))
                else:
                    # struct/union/enum 关键字后的标识符
                    name_node = node.child_by_field_name('name')
                    if name_node and name_node.type == 'type_identifier':
                        type_name = text[name_node.start_byte:name_node.end_byte]
                        if self.is_valid_symbol_reference(type_name):
                            dependencies.extend(self._create_dependencies_for_name(
                                type_name, source_symbol, DependencyType.TYPE_REFERENCE, name_node
                            ))
            
            # 字段访问 obj.field
            elif node.type == 'field_expression':
                field_node = node.child_by_field_name('field')
                if field_node and field_node.type == 'field_identifier':
                    field_name = text[field_node.start_byte:field_node.end_byte]
                    if self.is_valid_symbol_reference(field_name):
                        dependencies.extend(self._create_dependencies_for_name(
                            field_name, source_symbol, DependencyType.STRUCT_MEMBER, field_node
                        ))
            
            # 预处理指令 (宏使用)
            elif node.type == 'preproc_defined' or node.type == 'preproc_call':
                if node.type == 'preproc_call':
                    directive_node = node.child_by_field_name('directive')
                    if directive_node and directive_node.type == 'preproc_directive':
                        directive_name = text[directive_node.start_byte:directive_node.end_byte]
                        if self.is_valid_symbol_reference(directive_name):
                            dependencies.extend(self._create_dependencies_for_name(
                                directive_name, source_symbol, DependencyType.MACRO_USE, directive_node
                            ))
            
            # sizeof 表达式
            elif node.type == 'sizeof_expression':
                type_node = node.child_by_field_name('type')
                if type_node:
                    if type_node.type == 'type_identifier':
                        type_name = text[type_node.start_byte:type_node.end_byte]
                        if self.is_valid_symbol_reference(type_name):
                            dependencies.extend(self._create_dependencies_for_name(
                                type_name, source_symbol, DependencyType.TYPE_REFERENCE, type_node
                            ))
                    elif type_node.type == 'parenthesized_expression':
                        inner_node = type_node.children[1] if len(type_node.children) > 1 else None
                        if inner_node and inner_node.type == 'type_identifier':
                            type_name = text[inner_node.start_byte:inner_node.end_byte]
                            if self.is_valid_symbol_reference(type_name):
                                dependencies.extend(self._create_dependencies_for_name(
                                    type_name, source_symbol, DependencyType.TYPE_REFERENCE, inner_node
                                ))
            
            # 标识符引用（最通用的情况）
            elif node.type == 'identifier':
                identifier = text[node.start_byte:node.end_byte]
                if (self.is_valid_symbol_reference(identifier) and 
                    identifier not in local_variables and 
                    not self._is_in_declaration_context(node)):
                    # 根据上下文确定依赖类型
                    dep_type = self._infer_dependency_type(node, text)
                    dependencies.extend(self._create_dependencies_for_name(
                        identifier, source_symbol, dep_type, node
                    ))
            
            # 递归遍历子节点
            for child in node.children:
                traverse_node(child)
        
        # 首先收集所有局部变量
        collect_local_variables(node)
        
        # 然后遍历查找依赖
        traverse_node(node)
        return dependencies
    
    def _infer_dependency_type(self, node: Node, text: str) -> DependencyType:
        """根据AST节点上下文推断依赖类型"""
        identifier = text[node.start_byte:node.end_byte]
        parent = node.parent
        
        if not parent:
            return DependencyType.VARIABLE_USE
        
        # 首先检查是否是已知的宏
        if self._is_likely_macro(identifier):
            return DependencyType.MACRO_USE
        
        # 函数调用
        if parent.type == 'call_expression' and parent.child_by_field_name('function') == node:
            return DependencyType.FUNCTION_CALL
        
        # 类型声明或转换
        if parent.type in ['type_identifier', 'primitive_type', 'cast_expression', 
                          'struct_specifier', 'union_specifier', 'enum_specifier']:
            return DependencyType.TYPE_REFERENCE
        
        # 结构体成员访问
        if parent.type in ['field_expression', 'field_identifier']:
            return DependencyType.STRUCT_MEMBER
        
        # 宏使用 - 检查是否在宏调用中
        if self._is_in_macro_context(node):
            return DependencyType.MACRO_USE
        
        # 检查是否在符号注册表中确定类型
        if identifier in self.symbol_registry:
            for symbol in self.symbol_registry[identifier]:
                if symbol.symbol_type == SymbolType.FUNCTION:
                    return DependencyType.FUNCTION_CALL
                elif symbol.symbol_type == SymbolType.MACRO:
                    return DependencyType.MACRO_USE
                elif symbol.symbol_type in [SymbolType.STRUCT, SymbolType.TYPEDEF]:
                    return DependencyType.TYPE_REFERENCE
                elif symbol.symbol_type == SymbolType.ENUM:
                    return DependencyType.ENUM_USE
        
        # 默认为变量使用
        return DependencyType.VARIABLE_USE
    
    def _is_in_declaration_context(self, node: Node) -> bool:
        """检查节点是否在变量声明上下文中"""
        parent = node.parent
        while parent:
            if parent.type in ['declaration', 'parameter_declaration', 'init_declarator']:
                return True
            parent = parent.parent
        return False
    
    def _is_in_macro_context(self, node: Node) -> bool:
        """检查节点是否在宏使用上下文中"""
        # 检查是否在预处理指令中
        parent = node.parent
        while parent:
            if parent.type in ['preproc_call', 'preproc_defined', 'preproc_ifdef', 'preproc_ifndef']:
                return True
            parent = parent.parent
        return False
    
    def _is_likely_macro(self, name: str) -> bool:
        """基于命名模式判断是否可能是宏"""
        if not name:
            return False
        
        # 检查是否在符号注册表中被标记为宏
        if name in self.symbol_registry:
            for symbol in self.symbol_registry[name]:
                if symbol.symbol_type == SymbolType.MACRO:
                    return True
        
        # 启发式规则：
        # 1. 全大写字母加下划线
        if name.isupper() and '_' in name:
            return True
        
        # 2. 以常见宏前缀开头
        macro_prefixes = ['BINN_', 'API', 'MAX_', 'MIN_', '__', '_']
        for prefix in macro_prefixes:
            if name.startswith(prefix):
                return True
        
        return False
    
    def _extract_dependencies_by_pattern(self, text: str, source_symbol: Symbol) -> List[Dependency]:
        """基于模式匹配提取依赖关系（回退方法）"""
        dependencies = []
        
        # 简单的标识符匹配
        identifier_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.finditer(identifier_pattern, text)
        
        for match in matches:
            identifier = match.group(1)
            if self.is_valid_symbol_reference(identifier):
                dependencies.extend(self._create_dependencies_for_name(
                    identifier, source_symbol, DependencyType.VARIABLE_USE, None
                ))
        
        return dependencies
    
    def _create_dependencies_for_name(self, name: str, source_symbol: Symbol, 
                                     dep_type: DependencyType, node: Node = None) -> List[Dependency]:
        """为给定名称创建依赖关系"""
        dependencies = []
        
        if name in self.symbol_registry:
            for target_symbol in self.symbol_registry[name]:
                # 避免自依赖
                if target_symbol != source_symbol:
                    dependency = Dependency(
                        source_symbol=source_symbol,
                        target_symbol=target_symbol,
                        dependency_type=dep_type,
                        location=(node.start_point[0] + 1, node.end_point[0] + 1) if node else (0, 0)
                    )
                    dependencies.append(dependency)
        
        return dependencies
    
    def analyze_all_dependencies(self):
        """分析所有符号的依赖关系"""
        print("开始分析符号依赖关系...")
        
        total_symbols = len(self.dependency_graph.symbols)
        analyzed_count = 0
        error_count = 0
        total_found_deps = 0
        total_added_deps = 0
        
        for symbol in self.dependency_graph.symbols.values():
            try:
                # 提取该符号定义中的依赖
                if symbol.definition:
                    dependencies = self.extract_dependencies_from_text(symbol.definition, symbol)
                    total_found_deps += len(dependencies)
                    
                    for dep in dependencies:
                        if self.dependency_graph.add_dependency(dep):
                            total_added_deps += 1
                
                analyzed_count += 1
                
                # 显示进度
                if analyzed_count % 50 == 0 or analyzed_count == total_symbols:
                    progress = (analyzed_count / total_symbols) * 100
                    duplicate_rate = ((total_found_deps - total_added_deps) / max(total_found_deps, 1)) * 100
                    print(f"进度: {analyzed_count}/{total_symbols} ({progress:.1f}%) - "
                          f"发现: {total_found_deps}, 添加: {total_added_deps}, 重复率: {duplicate_rate:.1f}% - 错误: {error_count}")
                    
            except Exception as e:
                error_count += 1
                print(f"分析符号 {symbol.name} 时出错: {e}")
                continue
        
        print(f"依赖关系分析完成：")
        print(f"  ✅ 成功分析: {analyzed_count - error_count}/{total_symbols} 个符号")
        print(f"  ❌ 分析错误: {error_count} 个符号")
        print(f"  📊 发现依赖: {total_found_deps} 个")
        print(f"  📊 实际添加: {total_added_deps} 个")
        print(f"  🔄 去重数量: {total_found_deps - total_added_deps} 个")
        print(f"  📈 去重率: {((total_found_deps - total_added_deps) / max(total_found_deps, 1)) * 100:.1f}%")
    
    def export_dependencies_to_json(self, output_path: str):
        """导出依赖关系到JSON文件"""
        try:
            export_data = {
                'metadata': {
                    'total_symbols': len(self.dependency_graph.symbols),
                    'total_dependencies': len(self.dependency_graph.dependencies),
                    'statistics': self.get_dependency_statistics()
                },
                'symbols': {},
                'dependencies': []
            }
            
            # 导出符号信息
            for symbol in self.dependency_graph.symbols.values():
                key = f"{symbol.name}:{symbol.symbol_type.value}:{symbol.file_path}"
                export_data['symbols'][key] = {
                    'name': symbol.name,
                    'type': symbol.symbol_type.value,
                    'file_path': symbol.file_path,
                    'start_line': symbol.start_line,
                    'end_line': symbol.end_line
                }
            
            # 导出依赖关系
            for dep in self.dependency_graph.dependencies:
                export_data['dependencies'].append({
                    'source': {
                        'name': dep.source_symbol.name,
                        'type': dep.source_symbol.symbol_type.value,
                        'file': dep.source_symbol.file_path
                    },
                    'target': {
                        'name': dep.target_symbol.name,
                        'type': dep.target_symbol.symbol_type.value,
                        'file': dep.target_symbol.file_path
                    },
                    'dependency_type': dep.dependency_type.value,
                    'location': dep.location,
                    'context': dep.context
                })
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 依赖关系已导出到: {output_path}")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
    
    def generate_dependency_report(self) -> str:
        """生成依赖关系报告"""
        stats = self.get_dependency_statistics()
        
        report = []
        report.append("=" * 60)
        report.append("           C项目符号依赖关系分析报告")
        report.append("=" * 60)
        report.append("")
        
        # 总体统计
        report.append("📊 总体统计:")
        report.append(f"  符号总数: {stats['total_symbols']}")
        report.append(f"  依赖总数: {stats['total_dependencies']}")
        report.append("")
        
        # 按类型统计符号
        report.append("📋 符号分布:")
        for symbol_type, count in stats['symbols_by_type'].items():
            report.append(f"  {symbol_type}: {count}")
        report.append("")
        
        # 按类型统计依赖
        report.append("🔗 依赖分布:")
        for dep_type, count in stats['dependencies_by_type'].items():
            report.append(f"  {dep_type}: {count}")
        report.append("")
        
        # Top 10 最多依赖的符号
        symbol_dep_count = {}
        for dep in self.dependency_graph.dependencies:
            source_name = dep.source_symbol.name
            symbol_dep_count[source_name] = symbol_dep_count.get(source_name, 0) + 1
        
        top_symbols = sorted(symbol_dep_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        report.append("🔝 依赖最多的符号 (Top 10):")
        for i, (symbol_name, dep_count) in enumerate(top_symbols, 1):
            report.append(f"  {i:2d}. {symbol_name}: {dep_count} 个依赖")
        report.append("")
        
        # Top 10 被依赖最多的符号
        target_dep_count = {}
        for dep in self.dependency_graph.dependencies:
            target_name = dep.target_symbol.name
            target_dep_count[target_name] = target_dep_count.get(target_name, 0) + 1
        
        top_targets = sorted(target_dep_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        report.append("🎯 被依赖最多的符号 (Top 10):")
        for i, (symbol_name, dep_count) in enumerate(top_targets, 1):
            report.append(f"  {i:2d}. {symbol_name}: 被 {dep_count} 个符号依赖")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def get_dependency_statistics(self) -> Dict:
        """获取依赖关系统计信息"""
        stats = {
            'total_symbols': len(self.dependency_graph.symbols),
            'total_dependencies': len(self.dependency_graph.dependencies),
            'symbols_by_type': {},
            'dependencies_by_type': {}
        }
        
        # 按类型统计符号
        for symbol in self.dependency_graph.symbols.values():
            symbol_type = symbol.symbol_type.value
            stats['symbols_by_type'][symbol_type] = stats['symbols_by_type'].get(symbol_type, 0) + 1
        
        # 按类型统计依赖
        for dep in self.dependency_graph.dependencies:
            dep_type = dep.dependency_type.value
            stats['dependencies_by_type'][dep_type] = stats['dependencies_by_type'].get(dep_type, 0) + 1
        
        return stats

def main():
    """主函数 - 演示完整功能"""
    import time
    start_time = time.time()
    
    analyzer = SymbolDependencyAnalyzer('../c_project_analysis.json')
    
    print("=== 符号依赖关系分析器 ===")
    print("第二阶段：完整的依赖关系分析")
    print()
    
    # 构建符号注册表
    print("1️⃣ 构建符号注册表...")
    analyzer.build_symbol_registry()
    
    # 分析依赖关系
    print("\n2️⃣ 分析符号依赖关系...")
    analyzer.analyze_all_dependencies()
    
    # 生成报告
    print("\n3️⃣ 生成分析报告...")
    report = analyzer.generate_dependency_report()
    print(report)
    
    # 导出结果
    print("\n4️⃣ 导出分析结果...")
    analyzer.export_dependencies_to_json('symbol_dependencies.json')
    
    # 性能统计
    end_time = time.time()
    print(f"\n⏱️ 总用时: {end_time - start_time:.2f} 秒")

if __name__ == "__main__":
    main()
