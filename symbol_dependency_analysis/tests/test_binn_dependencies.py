#!/usr/bin/env python3
"""
测试脚本：验证binn_create_type函数的依赖提取
"""

import sys
import os
# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from symbol_dependency_analyzer import SymbolDependencyAnalyzer, SymbolType, DependencyType

def test_binn_create_type_dependencies():
    """测试binn_create_type函数的依赖关系提取"""
    print("=== 测试 binn_create_type 依赖关系提取 ===")
    
    # 创建分析器
    analyzer = SymbolDependencyAnalyzer('../../c_project_analysis.json')
    analyzer.build_symbol_registry()
    
    # 找到binn_create_type函数
    binn_create_type_symbol = None
    assert 'binn_create_type' in analyzer.symbol_registry, "binn_create_type函数未在符号注册表中找到"
    
    for symbol in analyzer.symbol_registry['binn_create_type']:
        if symbol.symbol_type == SymbolType.FUNCTION and symbol.definition:
            binn_create_type_symbol = symbol
            break
    
    assert binn_create_type_symbol is not None, "未找到binn_create_type函数定义"
    
    print(f"✅ 找到函数: {binn_create_type_symbol.name}")
    print(f"📁 文件: {binn_create_type_symbol.file_path}")
    print(f"📍 行号: {binn_create_type_symbol.start_line}-{binn_create_type_symbol.end_line}")
    
    print(f"\n📝 函数定义:")
    print(binn_create_type_symbol.definition)
    
    # 提取依赖关系
    print(f"\n🔍 分析依赖关系...")
    dependencies = analyzer.extract_dependencies_from_text(
        binn_create_type_symbol.definition, 
        binn_create_type_symbol
    )
    
    assert len(dependencies) > 0, "未发现任何依赖关系"
    print(f"\n📊 发现 {len(dependencies)} 个依赖关系:")
    
    # 按依赖类型分组
    dependencies_by_type = {}
    for dep in dependencies:
        dep_type = dep.dependency_type.value
        if dep_type not in dependencies_by_type:
            dependencies_by_type[dep_type] = []
        dependencies_by_type[dep_type].append(dep)
    
    # 显示依赖关系
    for dep_type, deps in dependencies_by_type.items():
        print(f"\n📌 {dep_type.upper()} 依赖:")
        for dep in deps:
            print(f"  └── {dep.target_symbol.name} ({dep.target_symbol.symbol_type.value})")
            print(f"      文件: {dep.target_symbol.file_path}")
            if dep.location != (0, 0):
                print(f"      位置: 行 {dep.location[0]}-{dep.location[1]}")
    
    # 验证期望的依赖关系
    expected_dependencies = ['APIENTRY', 'BINN_STORAGE_MIN', 'BINN_STORAGE_MAX', 'BINN_STORAGE_HAS_MORE']
    found_dependencies = [dep.target_symbol.name for dep in dependencies]
    
    print(f"\n✅ 期望依赖验证:")
    for expected in expected_dependencies:
        assert expected in found_dependencies, f"期望依赖 {expected} 未找到"
        print(f"  ✅ {expected} - 找到")
    
    # 验证不应该包含的符号（局部变量和参数）
    unwanted_symbols = ['storage_type', 'data_type_index']
    for unwanted in unwanted_symbols:
        assert unwanted not in found_dependencies, f"不应该包含局部变量/参数: {unwanted}"
    
    # 显示所有找到的符号依赖
    unique_symbols = set()
    for dep in dependencies:
        unique_symbols.add(dep.target_symbol.name)
    
    print(f"\n📋 所有发现的符号依赖 ({len(unique_symbols)} 个):")
    for symbol_name in sorted(unique_symbols):
        print(f"  • {symbol_name}")
    
    return dependencies

def analyze_macro_detection():
    """分析宏检测的准确性"""
    print(f"\n=== 宏检测分析 ===")
    
    analyzer = SymbolDependencyAnalyzer('../../c_project_analysis.json')
    analyzer.build_symbol_registry()
    
    test_identifiers = ['APIENTRY', 'BINN_STORAGE_MIN', 'BINN_STORAGE_MAX', 'BINN_STORAGE_HAS_MORE', 
                       'malloc', 'printf', 'data_type_index', 'storage_type']
    
    for identifier in test_identifiers:
        is_likely_macro = analyzer._is_likely_macro(identifier)
        is_valid_symbol = analyzer.is_valid_symbol_reference(identifier)
        
        print(f"标识符: {identifier}")
        print(f"  是否可能是宏: {is_likely_macro}")
        print(f"  是否是有效符号: {is_valid_symbol}")
        
        if identifier in analyzer.symbol_registry:
            symbols = analyzer.symbol_registry[identifier]
            symbol_types = [s.symbol_type.value for s in symbols]
            print(f"  注册表中的类型: {symbol_types}")
            
            # 对于已知的宏进行断言
            if identifier in ['APIENTRY', 'BINN_STORAGE_MIN', 'BINN_STORAGE_MAX', 'BINN_STORAGE_HAS_MORE']:
                assert is_likely_macro, f"{identifier} 应该被识别为宏"
                assert is_valid_symbol, f"{identifier} 应该是有效符号"
                assert 'macros' in symbol_types, f"{identifier} 应该在注册表中标记为宏"
        else:
            print(f"  注册表中的类型: 未找到")
            
            # 对于不应该被识别的符号进行断言
            if identifier in ['malloc', 'printf', 'data_type_index', 'storage_type']:
                assert not is_valid_symbol, f"{identifier} 不应该被识别为有效符号"
        
        print()

if __name__ == "__main__":
    dependencies = test_binn_create_type_dependencies()
    analyze_macro_detection()
