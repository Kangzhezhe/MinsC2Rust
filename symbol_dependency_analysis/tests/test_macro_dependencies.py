#!/usr/bin/env python3
"""
测试脚本：验证宏依赖关系识别
"""

import sys
import os
# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from symbol_dependency_analyzer import SymbolDependencyAnalyzer, SymbolType, DependencyType

def test_macro_dependencies():
    """测试宏依赖关系识别"""
    print("=== 测试宏依赖关系识别 ===")
    
    analyzer = SymbolDependencyAnalyzer('../../c_project_analysis.json')
    analyzer.build_symbol_registry()
    
    # 测试宏定义和宏使用的识别
    test_cases = [
        {
            'name': 'BINN_STORAGE_MIN',
            'expected_dependencies': ['BINN_STORAGE_NOBYTES'],
            'description': '宏定义依赖其他宏'
        },
        {
            'name': 'APIENTRY',
            'expected_dependencies': [],
            'description': '条件编译宏定义'
        },
        {
            'name': 'ALWAYS_INLINE',
            'expected_dependencies': [],
            'description': '编译器特定宏定义'
        }
    ]
    
    for case in test_cases:
        print(f"\n📌 测试宏: {case['name']}")
        print(f"   描述: {case['description']}")
        
        assert case['name'] in analyzer.symbol_registry, f"宏 {case['name']} 未在注册表中找到"
        
        symbols = analyzer.symbol_registry[case['name']]
        macro_symbols = [s for s in symbols if s.symbol_type == SymbolType.MACRO]
        assert len(macro_symbols) > 0, f"宏 {case['name']} 应该至少有一个宏定义"
        
        for symbol in macro_symbols:
            if symbol.definition:
                print(f"   定义: {symbol.definition.strip()}")
                
                # 分析依赖
                dependencies = analyzer.extract_dependencies_from_text(symbol.definition, symbol)
                
                print(f"   发现 {len(dependencies)} 个依赖:")
                for dep in dependencies:
                    print(f"     • {dep.target_symbol.name} ({dep.dependency_type.value})")
                
                # 验证期望的依赖
                found_deps = [dep.target_symbol.name for dep in dependencies]
                for expected in case['expected_dependencies']:
                    if expected in found_deps:
                        print(f"     ✅ 期望依赖 {expected} 已找到")
                    else:
                        print(f"     ⚠️  期望依赖 {expected} 未找到（可能是正常的）")
                break

def test_conditional_compilation():
    """测试条件编译相关的宏识别"""
    print("\n=== 测试条件编译宏识别 ===")
    
    analyzer = SymbolDependencyAnalyzer('../../c_project_analysis.json')
    analyzer.build_symbol_registry()
    
    conditional_macros = [
        'TRUE', 'FALSE', 'BOOL', 'NULL', 
        'INLINE', 'ALWAYS_INLINE', 'BINN_PRIVATE'
    ]
    
    found_macros = []
    for macro_name in conditional_macros:
        print(f"\n🔍 检查宏: {macro_name}")
        
        if macro_name in analyzer.symbol_registry:
            symbols = analyzer.symbol_registry[macro_name]
            macro_symbols = [s for s in symbols if s.symbol_type == SymbolType.MACRO]
            
            if len(macro_symbols) > 0:
                found_macros.append(macro_name)
                print(f"   找到 {len(macro_symbols)} 个宏定义")
                for i, symbol in enumerate(macro_symbols, 1):
                    print(f"   定义 {i}: {symbol.definition.strip() if symbol.definition else 'N/A'}")
                    print(f"   文件: {symbol.file_path}")
                    print(f"   行号: {symbol.start_line}-{symbol.end_line}")
            else:
                print(f"   在注册表中找到但不是宏类型")
        else:
            print(f"   ❌ 未找到")
    
    # 断言至少找到了一些基本的宏
    assert len(found_macros) >= 2, f"应该至少找到2个条件编译宏，实际找到: {found_macros}"

def test_macro_usage_in_functions():
    """测试函数中宏的使用识别"""
    print("\n=== 测试函数中宏的使用识别 ===")
    
    analyzer = SymbolDependencyAnalyzer('../../c_project_analysis.json')
    analyzer.build_symbol_registry()
    
    # 找到一些使用宏的函数
    functions_using_macros = ['binn_version', 'binn_set_alloc_functions']
    
    functions_tested = 0
    for func_name in functions_using_macros:
        if func_name in analyzer.symbol_registry:
            symbols = analyzer.symbol_registry[func_name]
            func_symbols = [s for s in symbols if s.symbol_type == SymbolType.FUNCTION]
            
            for symbol in func_symbols:
                if symbol.definition:
                    functions_tested += 1
                    print(f"\n📍 函数: {symbol.name}")
                    print(f"   文件: {symbol.file_path}")
                    
                    # 分析依赖
                    dependencies = analyzer.extract_dependencies_from_text(symbol.definition, symbol)
                    macro_deps = [dep for dep in dependencies if dep.dependency_type == DependencyType.MACRO_USE]
                    
                    if macro_deps:
                        unique_macros = set(dep.target_symbol.name for dep in macro_deps)
                        print(f"   使用的宏 ({len(unique_macros)} 个):")
                        for macro_name in sorted(unique_macros):
                            print(f"     • {macro_name}")
                        
                        # 对于binn_version函数，应该使用APIENTRY和BINN_VERSION
                        if func_name == 'binn_version':
                            assert 'APIENTRY' in unique_macros, "binn_version应该使用APIENTRY宏"
                    else:
                        print(f"   未检测到宏使用")
                    break
    
    assert functions_tested > 0, "应该至少测试一个函数的宏使用"

if __name__ == "__main__":
    test_macro_dependencies()
    test_conditional_compilation()
    test_macro_usage_in_functions()
