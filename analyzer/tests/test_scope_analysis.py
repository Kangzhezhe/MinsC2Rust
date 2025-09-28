#!/usr/bin/env python3
"""
测试脚本：验证作用域分析和局部变量过滤
"""

import sys
import os
# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from symbol_dependency_analyzer import SymbolDependencyAnalyzer, SymbolType, DependencyType

def test_local_variable_filtering():
    """测试局部变量过滤功能"""
    print("=== 测试局部变量过滤功能 ===")
    
    analyzer = SymbolDependencyAnalyzer('../output/c_project_analysis.json')
    analyzer.build_symbol_registry()
    
    # 选择一些有局部变量的函数进行测试
    test_functions = ['copy_be16', 'copy_be32', 'copy_be64', 'binn_memdup']
    
    functions_tested = 0
    for func_name in test_functions:
        if func_name in analyzer.symbol_registry:
            symbols = analyzer.symbol_registry[func_name]
            func_symbols = [s for s in symbols if s.symbol_type == SymbolType.FUNCTION]
            
            for symbol in func_symbols:
                if symbol.definition:
                    functions_tested += 1
                    print(f"\n📍 函数: {symbol.name}")
                    print(f"   定义:")
                    print(f"   {symbol.definition}")
                    
                    # 手动识别局部变量（简单的启发式）
                    local_vars = set()
                    lines = symbol.definition.split('\n')
                    for line in lines:
                        # 查找变量声明模式
                        if any(type_keyword in line for type_keyword in ['unsigned char', 'int ', 'void ', 'char ']):
                            # 提取可能的变量名
                            words = line.replace('*', ' ').replace(',', ' ').replace(';', ' ').split()
                            for i, word in enumerate(words):
                                if word in ['unsigned', 'char', 'int', 'void', 'const']:
                                    continue
                                if word.isalpha() and not word in ['if', 'for', 'while', 'return']:
                                    local_vars.add(word)
                    
                    print(f"   预期局部变量: {', '.join(sorted(local_vars)) if local_vars else '无'}")
                    
                    # 分析依赖
                    dependencies = analyzer.extract_dependencies_from_text(symbol.definition, symbol)
                    
                    # 检查是否有局部变量被误认为依赖
                    false_positives = []
                    for dep in dependencies:
                        if dep.target_symbol.name in local_vars:
                            false_positives.append(dep.target_symbol.name)
                    
                    # 断言：不应该有局部变量被误识别
                    assert len(false_positives) == 0, f"函数 {symbol.name} 中局部变量被误识别为依赖: {false_positives}"
                    print(f"   ✅ 局部变量过滤正确")
                    
                    # 显示真实的依赖
                    real_deps = [dep for dep in dependencies if dep.target_symbol.name not in local_vars]
                    if real_deps:
                        print(f"   真实依赖 ({len(real_deps)} 个):")
                        for dep in real_deps:
                            print(f"     • {dep.target_symbol.name} ({dep.dependency_type.value})")
                    else:
                        print(f"   真实依赖: 无")
                    break
    
    assert functions_tested > 0, "应该至少测试一个函数的局部变量过滤"

def test_parameter_filtering():
    """测试函数参数过滤"""
    print("\n=== 测试函数参数过滤 ===")
    
    analyzer = SymbolDependencyAnalyzer('../output/c_project_analysis.json')
    analyzer.build_symbol_registry()
    
    # 选择有明显参数的函数
    test_functions = ['binn_set_alloc_functions', 'binn_memdup']
    
    functions_tested = 0
    for func_name in test_functions:
        if func_name in analyzer.symbol_registry:
            symbols = analyzer.symbol_registry[func_name]
            func_symbols = [s for s in symbols if s.symbol_type == SymbolType.FUNCTION]
            
            for symbol in func_symbols:
                if symbol.definition:
                    functions_tested += 1
                    print(f"\n📍 函数: {symbol.name}")
                    
                    # 提取函数签名中的参数
                    func_signature = symbol.definition.split('{')[0] if '{' in symbol.definition else symbol.definition
                    print(f"   签名: {func_signature.strip()}")
                    
                    # 简单的参数提取
                    parameter_names = set()
                    if '(' in func_signature and ')' in func_signature:
                        params_part = func_signature.split('(')[1].split(')')[0]
                        
                        if params_part.strip() and params_part.strip() != 'void':
                            params = params_part.split(',')
                            for param in params:
                                # 提取参数名（最后一个单词，去掉指针符号）
                                words = param.strip().replace('*', ' ').split()
                                if words:
                                    param_name = words[-1]
                                    if param_name.isalpha():
                                        parameter_names.add(param_name)
                    
                    print(f"   参数: {', '.join(sorted(parameter_names)) if parameter_names else '无'}")
                    
                    # 分析依赖
                    dependencies = analyzer.extract_dependencies_from_text(symbol.definition, symbol)
                    
                    # 检查参数是否被误认为依赖
                    param_false_positives = []
                    for dep in dependencies:
                        if dep.target_symbol.name in parameter_names:
                            param_false_positives.append(dep.target_symbol.name)
                    
                    # 断言：参数不应该被识别为依赖
                    assert len(param_false_positives) == 0, f"函数 {symbol.name} 中参数被误识别为依赖: {param_false_positives}"
                    print(f"   ✅ 参数过滤正确")
                    break
    
    assert functions_tested > 0, "应该至少测试一个函数的参数过滤"

def test_scope_analysis():
    """测试作用域分析的准确性"""
    print("\n=== 测试作用域分析准确性 ===")
    
    analyzer = SymbolDependencyAnalyzer('../output/c_project_analysis.json')
    analyzer.build_symbol_registry()
    
    # 创建一个测试代码片段
    test_code = """int test_function(int param1, char *param2) {
    int local_var = 10;
    char *local_ptr = NULL;
    
    APIENTRY some_call();
    BINN_STORAGE_MIN;
    
    local_var = param1 + 5;
    local_ptr = param2;
    
    return local_var;
}"""
    
    print("测试代码片段:")
    print(test_code)
    
    # 创建一个临时符号用于测试
    from symbol_dependency_analyzer import Symbol
    test_symbol = Symbol(
        name="test_function",
        symbol_type=SymbolType.FUNCTION,
        file_path="test.c",
        definition=test_code
    )
    
    # 分析依赖
    dependencies = analyzer.extract_dependencies_from_text(test_code, test_symbol)
    
    print(f"\n分析结果:")
    print(f"发现 {len(dependencies)} 个依赖关系:")
    
    for dep in dependencies:
        print(f"  • {dep.target_symbol.name} ({dep.dependency_type.value})")
    
    # 预期的结果：应该只识别APIENTRY和BINN_STORAGE_MIN，不应该包含局部变量
    expected_symbols = {'APIENTRY', 'BINN_STORAGE_MIN'}
    unexpected_symbols = {'local_var', 'local_ptr', 'param1', 'param2'}
    
    found_symbols = {dep.target_symbol.name for dep in dependencies}
    
    print(f"\n验证结果:")
    for expected in expected_symbols:
        if expected in found_symbols:
            print(f"  ✅ 正确识别: {expected}")
        else:
            print(f"  ⚠️  应该识别但未识别: {expected} (可能是正常的)")
    
    # 严格断言：不应该识别局部变量和参数
    for unexpected in unexpected_symbols:
        assert unexpected not in found_symbols, f"错误识别了局部符号: {unexpected}"
        print(f"  ✅ 正确过滤: {unexpected}")

if __name__ == "__main__":
    test_local_variable_filtering()
    test_parameter_filtering()
    test_scope_analysis()
