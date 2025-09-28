#!/usr/bin/env python3
"""
符号依赖关系可视化完整演示
展示所有主要功能
"""

import sys
import os

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from dependency_visualizer import DependencyVisualizer

def demo_visualization():
    """演示可视化功能"""
    print("🎨 符号依赖关系可视化演示")
    print("=" * 50)
    
    # 检查依赖文件
    deps_file = "output/symbol_dependencies.json"
    if not os.path.exists(deps_file):
        print("❌ 请先运行 symbol_dependency_analyzer.py 生成依赖数据")
        return
    
    # 创建可视化器
    visualizer = DependencyVisualizer(deps_file, "vis")
    
    # 1. 列出可用符号
    print("\n1️⃣ 可用符号示例:")
    symbols = visualizer.list_available_symbols(15)
    for i, symbol in enumerate(symbols, 1):
        print(f"  {i:2d}. {symbol}")
    
    # 2. 演示符号搜索
    print("\n2️⃣ 符号搜索演示:")
    search_terms = ["binn", "main", "BOOL"]
    for term in search_terms:
        matches = [s for s in visualizer.symbol_by_name.keys() if term.lower() in s.lower()]
        print(f"  搜索 '{term}': 找到 {len(matches)} 个匹配")
        if matches:
            print(f"    示例: {', '.join(matches[:3])}")
    
    # 3. 生成依赖摘要
    print("\n3️⃣ 依赖摘要演示:")
    demo_symbols = ["main", "binn_create_type", "BOOL", "APIENTRY"]
    
    for symbol_name in demo_symbols:
        if symbol_name in visualizer.symbol_by_name:
            print(f"\n📊 {symbol_name} 依赖摘要:")
            
            # 计算依赖统计
            forward_deps = visualizer.forward_deps.get(symbol_name, [])
            backward_deps = visualizer.backward_deps.get(symbol_name, [])
            
            print(f"  ├── 依赖其他符号: {len(forward_deps)} 个")
            print(f"  └── 被其他符号依赖: {len(backward_deps)} 个")
            
            # 按类型分组
            if forward_deps:
                by_type = {}
                for dep in forward_deps:
                    dep_type = dep['dependency_type']
                    by_type[dep_type] = by_type.get(dep_type, 0) + 1
                print(f"      依赖类型: {dict(by_type)}")
            
            break  # 只详细展示第一个找到的符号
    
    # 4. 可视化演示
    print("\n4️⃣ 可视化演示:")
    
    # 找几个有代表性的符号进行可视化
    vis_symbols = [
        ("main", "forward", 1),
        ("BOOL", "backward", 1), 
        ("binn_create_type", "both", 1)
    ]
    
    for symbol_name, direction, depth in vis_symbols:
        if symbol_name in visualizer.symbol_by_name:
            print(f"\n🎨 可视化 {symbol_name} ({direction}, 深度{depth})")
            try:
                filepath = visualizer.visualize_dependencies(
                    symbol_name, direction, depth, max_nodes=20
                )
                if filepath:
                    file_size = os.path.getsize(filepath) / 1024  # KB
                    print(f"  ✅ 生成成功: {os.path.basename(filepath)} ({file_size:.1f}KB)")
            except Exception as e:
                print(f"  ⚠️ 生成失败: {e}")
    
    # 5. 输出文件统计
    print("\n5️⃣ 输出文件统计:")
    output_dir = "output"
    if os.path.exists(output_dir):
        files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
        total_size = sum(os.path.getsize(os.path.join(output_dir, f)) for f in files)
        print(f"  📁 输出目录: {output_dir}/")
        print(f"  📊 生成图片: {len(files)} 个")
        print(f"  💾 总大小: {total_size / 1024 / 1024:.2f} MB")
        
        print(f"\n  📋 文件列表:")
        for f in sorted(files):
            size = os.path.getsize(os.path.join(output_dir, f)) / 1024
            print(f"    - {f} ({size:.1f}KB)")
    
    # 6. 使用建议
    print("\n6️⃣ 使用建议:")
    print("  🔍 交互模式: python3 dependency_visualizer.py --interactive")
    print("  📊 快速可视化: python3 dependency_visualizer.py --symbol <符号名> --direction both")
    print("  📋 依赖摘要: python3 dependency_visualizer.py --symbol <符号名> --summary")
    
    print(f"\n✅ 演示完成！")
    print(f"📁 所有可视化文件已保存到 vis/ 目录")

if __name__ == "__main__":
    demo_visualization()
