#!/usr/bin/env 
import json
import os
import sys
import argparse
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
import matplotlib.pyplot as plt

import matplotlib.patches as mpatches
import networkx as nx
from matplotlib.font_manager import FontProperties
import warnings

# Add parent directory to path for importing analyzer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from symbol_dependency_analyzer import SymbolDependencyAnalyzer, SymbolType, DependencyType

# Suppress matplotlib warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

class DependencyVisualizer:
    """Symbol Dependency Visualizer"""
    
    def __init__(self, dependencies_json_path: str, output_dir: str = "output"):
        """Initialize the visualizer"""
        self.dependencies_json_path = dependencies_json_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Load dependency data
        with open(dependencies_json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.symbols = self.data['symbols']
        self.dependencies = self.data['dependencies']
        
        # Build symbol indexes
        self._build_symbol_indexes()
        
        # Define color scheme
        self.colors = {
            'functions': '#3498db',      # Blue
            'macros': '#e74c3c',         # Red
            'structs': '#2ecc71',        # Green
            'typedefs': '#f39c12',       # Orange
            'variables': '#9b59b6',      # Purple
            'enums': '#1abc9c'           # Teal
        }
        
        # Edge styles for dependency types
        self.edge_styles = {
            'function_call': '-',        # Solid line
            'type_reference': '--',      # Dashed line
            'macro_use': '-.',           # Dash-dot line
            'variable_use': ':',         # Dotted line
            'struct_member': '-',        # Solid line
            'enum_use': '--'             # Dashed line
        }
    
    def _setup_chinese_font(self) -> Optional[FontProperties]:
        """设置中文字体"""
        try:
            # 尝试常见的中文字体
            chinese_fonts = [
                'SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei',
                'DejaVu Sans', 'Arial Unicode MS'
            ]
            
            for font_name in chinese_fonts:
                try:
                    font_prop = FontProperties(fname=None, family=font_name)
                    # 测试字体是否可用
                    plt.figure(figsize=(1, 1))
                    plt.text(0, 0, '测试', fontproperties=font_prop)
                    plt.close()
                    return font_prop
                except:
                    continue
            
            return None
        except:
            return None
    
    def _build_symbol_indexes(self):
        """构建符号索引以便快速查找"""
        # 按名称索引符号
        self.symbol_by_name = {}
        for symbol_key, symbol_info in self.symbols.items():
            name = symbol_info['name']
            if name not in self.symbol_by_name:
                self.symbol_by_name[name] = []
            self.symbol_by_name[name].append((symbol_key, symbol_info))
        
        # 构建依赖关系索引
        self.forward_deps = {}   # symbol -> [dependencies]
        self.backward_deps = {}  # symbol -> [dependents]
        
        for dep in self.dependencies:
            source_name = dep['source']['name']
            target_name = dep['target']['name']
            
            # 前向依赖
            if source_name not in self.forward_deps:
                self.forward_deps[source_name] = []
            self.forward_deps[source_name].append(dep)
            
            # 后向依赖
            if target_name not in self.backward_deps:
                self.backward_deps[target_name] = []
            self.backward_deps[target_name].append(dep)
    
    def find_symbol_dependencies(self, symbol_name: str, direction: str = "both", 
                                max_depth: int = 2, max_nodes: int = 50) -> Dict:
        """
        查找符号的依赖关系
        
        Args:
            symbol_name: 符号名称
            direction: 依赖方向 ("forward", "backward", "both")
            max_depth: 最大搜索深度
            max_nodes: 最大节点数量
        
        Returns:
            包含节点和边信息的字典
        """
        if symbol_name not in self.symbol_by_name:
            raise ValueError(f"符号 '{symbol_name}' 未找到")
        
        nodes = {}
        edges = []
        visited = set()
        
        def add_symbol_to_nodes(name: str, symbol_info: dict = None):
            """添加符号到节点集合"""
            if name in nodes:
                return
            
            if symbol_info is None and name in self.symbol_by_name:
                symbol_info = self.symbol_by_name[name][0][1]  # 取第一个匹配的符号
            
            if symbol_info:
                nodes[name] = {
                    'name': name,
                    'type': symbol_info['type'],
                    'file': os.path.basename(symbol_info['file_path']),
                    'color': self.colors.get(symbol_info['type'], '#95a5a6')
                }
            else:
                # 如果找不到符号信息，使用默认值
                nodes[name] = {
                    'name': name,
                    'type': 'unknown',
                    'file': 'unknown',
                    'color': '#95a5a6'
                }
        
        def explore_dependencies(current_name: str, current_depth: int, explore_forward: bool):
            """递归探索依赖关系"""
            if current_depth > max_depth or len(nodes) >= max_nodes:
                return
            
            if current_name in visited:
                return
            visited.add(current_name)
            
            # 添加当前符号
            add_symbol_to_nodes(current_name)
            
            # 选择探索方向
            deps_to_explore = []
            if explore_forward and current_name in self.forward_deps:
                deps_to_explore = self.forward_deps[current_name]
            elif not explore_forward and current_name in self.backward_deps:
                deps_to_explore = self.backward_deps[current_name]
            
            for dep in deps_to_explore:
                if len(nodes) >= max_nodes:
                    break
                
                if explore_forward:
                    target_name = dep['target']['name']
                    source_name = current_name
                else:
                    target_name = current_name
                    source_name = dep['source']['name']
                
                # 添加目标符号
                add_symbol_to_nodes(target_name)
                
                # 添加边
                edge_info = {
                    'source': source_name,
                    'target': target_name,
                    'type': dep['dependency_type'],
                    'style': self.edge_styles.get(dep['dependency_type'], '-')
                }
                
                if edge_info not in edges:
                    edges.append(edge_info)
                
                # 递归探索
                next_name = target_name if explore_forward else source_name
                explore_dependencies(next_name, current_depth + 1, explore_forward)
        
        # 开始探索
        if direction in ["forward", "both"]:
            explore_dependencies(symbol_name, 0, True)
        
        if direction in ["backward", "both"]:
            visited.clear()  # 清空访问记录以允许反向探索
            explore_dependencies(symbol_name, 0, False)
        
        return {
            'nodes': nodes,
            'edges': edges,
            'root_symbol': symbol_name,
            'direction': direction
        }
    
    def visualize_dependencies(self, symbol_name: str, direction: str = "both",
                              max_depth: int = 2, max_nodes: int = 50, 
                              save_to_file: bool = True) -> str:
        """
        可视化符号依赖关系
        
        Args:
            symbol_name: 符号名称
            direction: 依赖方向
            max_depth: 最大搜索深度
            max_nodes: 最大节点数量
            save_to_file: 是否保存到文件
        
        Returns:
            保存的文件路径
        """
        # 获取依赖数据
        dep_data = self.find_symbol_dependencies(symbol_name, direction, max_depth, max_nodes)
        nodes = dep_data['nodes']
        edges = dep_data['edges']
        
        if not nodes:
            raise ValueError(f"未找到符号 '{symbol_name}' 的依赖关系")
        
        # 创建网络图
        G = nx.DiGraph()
        
        # 添加节点
        for name, info in nodes.items():
            G.add_node(name, **info)
        
        # 添加边
        for edge in edges:
            G.add_edge(edge['source'], edge['target'], 
                      edge_type=edge['type'], style=edge['style'])
        
        # 设置图形大小
        fig_size = (16, 12) if len(nodes) > 20 else (12, 9)
        plt.figure(figsize=fig_size)
        
        # 计算布局
        if len(nodes) <= 10:
            pos = nx.spring_layout(G, k=3, iterations=50)
        elif len(nodes) <= 30:
            pos = nx.spring_layout(G, k=2, iterations=30)
        else:
            pos = nx.spring_layout(G, k=1.5, iterations=20)
        
        # 绘制节点
        for node_type in self.colors.keys():
            node_list = [n for n, d in G.nodes(data=True) if d.get('type') == node_type]
            if node_list:
                nx.draw_networkx_nodes(G, pos, nodelist=node_list,
                                     node_color=self.colors[node_type],
                                     node_size=1000 if len(nodes) <= 20 else 600,
                                     alpha=0.8)
        
        # 突出显示根节点
        if symbol_name in G.nodes():
            nx.draw_networkx_nodes(G, pos, nodelist=[symbol_name],
                                 node_color='#f1c40f', node_size=1500 if len(nodes) <= 20 else 900,
                                 alpha=1.0, edgecolors='black', linewidths=3)
        
        # 绘制边
        edge_types = set(edge['type'] for edge in edges)
        for edge_type in edge_types:
            edge_list = [(e['source'], e['target']) for e in edges if e['type'] == edge_type]
            if edge_list:
                style = self.edge_styles.get(edge_type, '-')
                nx.draw_networkx_edges(G, pos, edgelist=edge_list,
                                     edge_color='#34495e', arrows=True,
                                     arrowsize=20 if len(nodes) <= 20 else 15,
                                     style=style, alpha=0.7, width=1.5)
        
        # 绘制标签
        font_size = 10 if len(nodes) <= 20 else 8
        if self.font_prop:
            nx.draw_networkx_labels(G, pos, font_size=font_size, 
                                  font_family=self.font_prop.get_family())
        else:
            nx.draw_networkx_labels(G, pos, font_size=font_size)
        
        # 设置标题
        direction_map = {
            "forward": "依赖关系",
            "backward": "被依赖关系", 
            "both": "双向依赖关系"
        }
        title = f"符号 '{symbol_name}' 的{direction_map.get(direction, '依赖关系')}"
        if self.font_prop:
            plt.title(title, fontsize=16, fontweight='bold', fontproperties=self.font_prop)
        else:
            plt.title(title, fontsize=16, fontweight='bold')
        
        # 创建图例
        legend_elements = []
        
        # 符号类型图例
        for symbol_type, color in self.colors.items():
            if any(d.get('type') == symbol_type for _, d in G.nodes(data=True)):
                legend_elements.append(mpatches.Patch(color=color, label=f'{symbol_type}'))
        
        # 根节点图例
        legend_elements.append(mpatches.Patch(color='#f1c40f', label='目标符号'))
        
        # 依赖类型图例
        legend_elements.append(mpatches.Patch(color='white', label=''))  # 分隔符
        for edge_type in edge_types:
            style_name = {
                'function_call': '函数调用',
                'type_reference': '类型引用',
                'macro_use': '宏使用',
                'variable_use': '变量使用',
                'struct_member': '结构体成员',
                'enum_use': '枚举使用'
            }.get(edge_type, edge_type)
            legend_elements.append(mpatches.Patch(color='#34495e', label=style_name))
        
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1))
        
        # 添加统计信息
        stats_text = f"节点数: {len(nodes)}\n边数: {len(edges)}\n深度: {max_depth}"
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.axis('off')
        plt.tight_layout()
        
        # 保存文件
        if save_to_file:
            safe_name = "".join(c for c in symbol_name if c.isalnum() or c in "._-")
            filename = f"deps_{safe_name}_{direction}_{max_depth}d.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight', format='png')
            print(f"✅ 依赖图已保存到: {filepath}")
            return str(filepath)
        else:
            plt.show()
            return ""
    
    def generate_dependency_summary(self, symbol_name: str) -> str:
        """生成符号依赖关系摘要"""
        if symbol_name not in self.symbol_by_name:
            return f"符号 '{symbol_name}' 未找到"
        
        summary = []
        summary.append(f"{'='*60}")
        summary.append(f"符号 '{symbol_name}' 依赖关系摘要")
        summary.append(f"{'='*60}")
        
        # 获取符号信息
        symbol_info = self.symbol_by_name[symbol_name][0][1]
        summary.append(f"类型: {symbol_info['type']}")
        summary.append(f"文件: {symbol_info['file_path']}")
        summary.append("")
        
        # 前向依赖（该符号依赖什么）
        forward_deps = self.forward_deps.get(symbol_name, [])
        summary.append(f"📤 依赖的符号 ({len(forward_deps)} 个):")
        if forward_deps:
            by_type = {}
            for dep in forward_deps:
                dep_type = dep['dependency_type']
                if dep_type not in by_type:
                    by_type[dep_type] = []
                by_type[dep_type].append(dep['target']['name'])
            
            for dep_type, targets in by_type.items():
                summary.append(f"  {dep_type}: {', '.join(sorted(set(targets)))}")
        else:
            summary.append("  (无)")
        
        summary.append("")
        
        # 后向依赖（什么依赖该符号）
        backward_deps = self.backward_deps.get(symbol_name, [])
        summary.append(f"📥 被依赖的符号 ({len(backward_deps)} 个):")
        if backward_deps:
            by_type = {}
            for dep in backward_deps:
                dep_type = dep['dependency_type']
                if dep_type not in by_type:
                    by_type[dep_type] = []
                by_type[dep_type].append(dep['source']['name'])
            
            for dep_type, sources in by_type.items():
                summary.append(f"  {dep_type}: {', '.join(sorted(set(sources)))}")
        else:
            summary.append("  (无)")
        
        summary.append(f"{'='*60}")
        
        return "\n".join(summary)
    
    def list_available_symbols(self, limit: int = 20) -> List[str]:
        """列出可用的符号"""
        symbols = list(self.symbol_by_name.keys())
        symbols.sort()
        return symbols[:limit]
    
    def interactive_mode(self):
        """交互式模式"""
        print("🔍 符号依赖关系可视化器 - 交互模式")
        print("=" * 50)
        print("可用命令:")
        print("  list                    - 列出前20个可用符号")
        print("  search <name>           - 搜索符号")
        print("  vis <symbol> [options]  - 可视化依赖关系")
        print("  summary <symbol>        - 显示依赖摘要")
        print("  help                    - 显示帮助")
        print("  quit                    - 退出")
        print("=" * 50)
        
        while True:
            try:
                cmd = input("\n> ").strip()
                if not cmd:
                    continue
                
                parts = cmd.split()
                command = parts[0].lower()
                
                if command == 'quit':
                    break
                elif command == 'help':
                    print("可视化选项:")
                    print("  vis <symbol> forward   - 显示符号依赖的其他符号")
                    print("  vis <symbol> backward  - 显示依赖该符号的其他符号")
                    print("  vis <symbol> both      - 显示双向依赖关系")
                    print("  vis <symbol> both 3    - 指定搜索深度为3")
                elif command == 'list':
                    symbols = self.list_available_symbols()
                    print(f"前{len(symbols)}个可用符号:")
                    for i, symbol in enumerate(symbols, 1):
                        print(f"  {i:2d}. {symbol}")
                elif command == 'search':
                    if len(parts) < 2:
                        print("❌ 请提供搜索关键词")
                        continue
                    keyword = parts[1]
                    matches = [s for s in self.symbol_by_name.keys() if keyword.lower() in s.lower()]
                    if matches:
                        print(f"找到 {len(matches)} 个匹配的符号:")
                        for match in sorted(matches)[:20]:
                            print(f"  - {match}")
                        if len(matches) > 20:
                            print(f"  ... 还有 {len(matches) - 20} 个符号")
                    else:
                        print("❌ 未找到匹配的符号")
                elif command == 'vis':
                    if len(parts) < 2:
                        print("❌ 请提供符号名称")
                        continue
                    
                    symbol_name = parts[1]
                    direction = parts[2] if len(parts) > 2 else "both"
                    max_depth = int(parts[3]) if len(parts) > 3 else 2
                    
                    try:
                        filepath = self.visualize_dependencies(symbol_name, direction, max_depth)
                        if filepath:
                            print(f"✅ 可视化完成，文件保存到: {filepath}")
                    except Exception as e:
                        print(f"❌ 可视化失败: {e}")
                elif command == 'summary':
                    if len(parts) < 2:
                        print("❌ 请提供符号名称")
                        continue
                    
                    symbol_name = parts[1]
                    summary = self.generate_dependency_summary(symbol_name)
                    print(summary)
                else:
                    print(f"❌ 未知命令: {command}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
        
        print("\n👋 再见!")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='符号依赖关系可视化器')
    parser.add_argument('--deps-file', default='symbol_dependencies.json',
                       help='依赖关系JSON文件路径')
    parser.add_argument('--output-dir', default='output',
                       help='输出目录')
    parser.add_argument('--symbol', help='要可视化的符号名称')
    parser.add_argument('--direction', choices=['forward', 'backward', 'both'], 
                       default='both', help='依赖方向')
    parser.add_argument('--depth', type=int, default=2, help='最大搜索深度')
    parser.add_argument('--max-nodes', type=int, default=50, help='最大节点数量')
    parser.add_argument('--interactive', action='store_true', help='交互模式')
    parser.add_argument('--summary', action='store_true', help='显示依赖摘要')
    
    args = parser.parse_args()
    
    # 检查依赖文件是否存在
    if not os.path.exists(args.deps_file):
        print(f"❌ 依赖文件未找到: {args.deps_file}")
        print("请先运行符号依赖分析器生成依赖数据")
        return
    
    try:
        visualizer = DependencyVisualizer(args.deps_file, args.output_dir)
        
        if args.interactive:
            visualizer.interactive_mode()
        elif args.symbol:
            if args.summary:
                summary = visualizer.generate_dependency_summary(args.symbol)
                print(summary)
            else:
                filepath = visualizer.visualize_dependencies(
                    args.symbol, args.direction, args.depth, args.max_nodes
                )
                if filepath:
                    print(f"✅ 可视化完成: {filepath}")
        else:
            print("请指定 --symbol 参数或使用 --interactive 模式")
            print("使用 --help 查看详细帮助")
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1

if __name__ == "__main__":
    main()
