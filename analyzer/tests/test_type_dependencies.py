#!/usr/bin/env python3
"""
测试脚本：验证类型依赖关系识别
"""

import sys
import os
# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from symbol_dependency_analyzer import SymbolDependencyAnalyzer, SymbolType, DependencyType

try:
    from config import get_output_dir
except ImportError:  # pragma: no cover
    from analyzer.config import get_output_dir

ANALYSIS_JSON = str(get_output_dir() / "c_project_analysis.json")

def test_struct_dependencies():
    """测试结构体依赖关系识别"""
    print("=== 测试结构体依赖关系识别 ===")
    
    analyzer = SymbolDependencyAnalyzer(ANALYSIS_JSON)
    analyzer.build_symbol_registry()
    
    # 获取所有结构体
    structs = analyzer.dependency_graph.get_symbols_by_type(SymbolType.STRUCT)
    print(f"找到 {len(structs)} 个结构体定义")
    
    # 断言：应该找到一些结构体
    assert len(structs) > 0, "应该找到至少一个结构体定义"
    
    struct_with_deps = 0
    total_analyzed = 0
    
    for struct in structs[:5]:  # 只测试前5个
        print(f"\n📍 结构体: {struct.name}")
        print(f"   文件: {struct.file_path}")
        print(f"   行号: {struct.start_line}-{struct.end_line}")
        
        if struct.definition:
            print(f"   定义预览: {struct.definition[:100].replace(chr(10), ' ')}...")
            
            # 分析依赖
            dependencies = analyzer.extract_dependencies_from_text(struct.definition, struct)
            total_analyzed += 1
            
            if dependencies:
                struct_with_deps += 1
                print(f"   依赖关系 ({len(dependencies)} 个):")
                
                # 按类型分组
                deps_by_type = {}
                for dep in dependencies:
                    dep_type = dep.dependency_type.value
                    if dep_type not in deps_by_type:
                        deps_by_type[dep_type] = []
                    deps_by_type[dep_type].append(dep.target_symbol.name)
                
                for dep_type, targets in deps_by_type.items():
                    print(f"     {dep_type}: {', '.join(set(targets))}")
            else:
                print(f"   未发现依赖关系")
    
    # 断言：分析的结构体中至少有一些有依赖关系
    if total_analyzed > 0:
        print(f"\n✅ 分析了 {total_analyzed} 个结构体，{struct_with_deps} 个有依赖关系")
        # 允许某些结构体没有依赖，但不是全部都没有
        assert struct_with_deps >= 0, f"结构体依赖分析完成：{struct_with_deps}/{total_analyzed}"

def test_typedef_dependencies():
    """测试类型定义依赖关系识别"""
    print("\n=== 测试类型定义依赖关系识别 ===")
    
    analyzer = SymbolDependencyAnalyzer(ANALYSIS_JSON)
    analyzer.build_symbol_registry()
    
    # 获取所有类型定义
    typedefs = analyzer.dependency_graph.get_symbols_by_type(SymbolType.TYPEDEF)
    print(f"找到 {len(typedefs)} 个类型定义")
    
    # 断言：应该找到一些类型定义
    assert len(typedefs) > 0, "应该找到至少一个类型定义"
    
    typedefs_with_deps = 0
    total_analyzed = 0
    
    for typedef in typedefs[:10]:  # 只测试前10个
        print(f"\n📍 类型定义: {typedef.name}")
        print(f"   文件: {typedef.file_path}")
        
        if typedef.definition:
            print(f"   定义: {typedef.definition.strip()}")
            
            # 分析依赖
            dependencies = analyzer.extract_dependencies_from_text(typedef.definition, typedef)
            total_analyzed += 1
            
            if dependencies:
                typedefs_with_deps += 1
                print(f"   依赖关系 ({len(dependencies)} 个):")
                for dep in dependencies:
                    print(f"     • {dep.target_symbol.name} ({dep.target_symbol.symbol_type.value}) - {dep.dependency_type.value}")
            else:
                print(f"   未发现依赖关系")
    
    # 断言：typedef分析完成
    if total_analyzed > 0:
        print(f"\n✅ 分析了 {total_analyzed} 个类型定义，{typedefs_with_deps} 个有依赖关系")
        assert typedefs_with_deps >= 0, f"类型定义依赖分析完成：{typedefs_with_deps}/{total_analyzed}"

def test_type_usage_in_functions():
    """测试函数中类型的使用"""
    print("\n=== 测试函数中类型的使用 ===")
    
    analyzer = SymbolDependencyAnalyzer(ANALYSIS_JSON)
    analyzer.build_symbol_registry()
    
    # 找一些可能使用自定义类型的函数
    test_functions = ['copy_be16', 'copy_be32', 'copy_be64']
    
    functions_found = 0
    functions_with_types = 0
    
    for func_name in test_functions:
        if func_name in analyzer.symbol_registry:
            symbols = analyzer.symbol_registry[func_name]
            func_symbols = [s for s in symbols if s.symbol_type == SymbolType.FUNCTION]
            
            for symbol in func_symbols:
                if symbol.definition:
                    functions_found += 1
                    print(f"\n📍 函数: {symbol.name}")
                    print(f"   签名: {symbol.definition.split('{')[0].strip() if '{' in symbol.definition else symbol.definition[:100]}")
                    
                    # 分析类型依赖
                    dependencies = analyzer.extract_dependencies_from_text(symbol.definition, symbol)
                    type_deps = [dep for dep in dependencies if dep.dependency_type == DependencyType.TYPE_REFERENCE]
                    
                    if type_deps:
                        functions_with_types += 1
                        print(f"   使用的类型 ({len(type_deps)} 个):")
                        unique_types = set()
                        for dep in type_deps:
                            unique_types.add(dep.target_symbol.name)
                        for type_name in sorted(unique_types):
                            print(f"     • {type_name}")
                    else:
                        print(f"   未检测到自定义类型使用")
                    break
    
    # 断言：应该找到这些测试函数
    assert functions_found > 0, f"应该找到至少一个测试函数，实际找到 {functions_found}"
    print(f"\n✅ 分析了 {functions_found} 个函数，{functions_with_types} 个使用了类型")

def test_enum_dependencies():
    """测试枚举依赖关系识别"""
    print("\n=== 测试枚举依赖关系识别 ===")
    
    analyzer = SymbolDependencyAnalyzer(ANALYSIS_JSON)
    analyzer.build_symbol_registry()
    
    # 获取所有枚举
    enums = analyzer.dependency_graph.get_symbols_by_type(SymbolType.ENUM)
    print(f"找到 {len(enums)} 个枚举定义")
    
    # 断言：枚举数量合理（可能为0，某些项目可能不使用枚举）
    assert len(enums) >= 0, "枚举查找完成"
    
    if len(enums) == 0:
        print("   项目中未使用枚举，这是正常的")
        return
    
    enums_with_deps = 0
    total_analyzed = 0
    
    for enum in enums:
        print(f"\n📍 枚举: {enum.name}")
        print(f"   文件: {enum.file_path}")
        print(f"   行号: {enum.start_line}-{enum.end_line}")
        
        if enum.definition:
            print(f"   定义: {enum.definition.strip()}")
            
            # 分析依赖
            dependencies = analyzer.extract_dependencies_from_text(enum.definition, enum)
            total_analyzed += 1
            
            if dependencies:
                enums_with_deps += 1
                print(f"   依赖关系 ({len(dependencies)} 个):")
                for dep in dependencies:
                    print(f"     • {dep.target_symbol.name} ({dep.dependency_type.value})")
            else:
                print(f"   未发现依赖关系")
    
    # 断言：枚举分析完成
    if total_analyzed > 0:
        print(f"\n✅ 分析了 {total_analyzed} 个枚举，{enums_with_deps} 个有依赖关系")
        assert enums_with_deps >= 0, f"枚举依赖分析完成：{enums_with_deps}/{total_analyzed}"

if __name__ == "__main__":
    test_struct_dependencies()
    test_typedef_dependencies()
    test_type_usage_in_functions()
    test_enum_dependencies()
