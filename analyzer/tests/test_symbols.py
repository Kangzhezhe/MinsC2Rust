#!/usr/bin/env python3
"""
测试脚本：验证符号注册表中的特定符号
"""

import sys
import os
# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from symbol_dependency_analyzer import SymbolDependencyAnalyzer, SymbolType

try:
    from config import get_output_dir
except ImportError:  # pragma: no cover
    from analyzer.config import get_output_dir

ANALYSIS_JSON = str(get_output_dir() / "c_project_analysis.json")

def test_specific_symbols():
    """测试特定符号是否在注册表中"""
    analyzer = SymbolDependencyAnalyzer(ANALYSIS_JSON)
    analyzer.build_symbol_registry()
    
    # 测试你提到的符号
    test_symbols = [
        'binn_create_type',
        'APIENTRY', 
        'BINN_STORAGE_MIN',
        'BINN_STORAGE_MAX',
        'BINN_STORAGE_HAS_MORE'
    ]
    
    print("=== 测试特定符号 ===")
    for symbol_name in test_symbols:
        assert symbol_name in analyzer.symbol_registry, f"符号 '{symbol_name}' 未在注册表中找到"
        
        symbols = analyzer.symbol_registry[symbol_name]
        assert len(symbols) > 0, f"符号 '{symbol_name}' 在注册表中没有实例"
        
        print(f"\n符号 '{symbol_name}' 找到 {len(symbols)} 个定义:")
        for symbol in symbols:
            print(f"  类型: {symbol.symbol_type.value}")
            print(f"  文件: {symbol.file_path}")
            print(f"  行号: {symbol.start_line}-{symbol.end_line}")
            if symbol.definition:
                definition_preview = symbol.definition[:100].replace('\n', ' ')
                print(f"  定义预览: {definition_preview}...")
    
    # 特别验证binn_create_type函数
    binn_symbols = analyzer.symbol_registry['binn_create_type']
    func_symbols = [s for s in binn_symbols if s.symbol_type == SymbolType.FUNCTION]
    assert len(func_symbols) > 0, "binn_create_type应该至少有一个函数定义"
    
    # 找到binn_create_type函数并显示其完整定义
    print(f"\n=== binn_create_type 完整定义 ===")
    for symbol in func_symbols:
        if symbol.definition:
            print(f"定义:\n{symbol.definition}")
            assert 'APIENTRY' in symbol.definition, "binn_create_type定义中应该包含APIENTRY"
            assert 'BINN_STORAGE_MIN' in symbol.definition, "binn_create_type定义中应该包含BINN_STORAGE_MIN"
            break

if __name__ == "__main__":
    test_specific_symbols()
