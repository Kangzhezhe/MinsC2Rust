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

try:
    from config import get_output_dir
except ImportError:  # pragma: no cover
    from analyzer.config import get_output_dir

# Suppress matplotlib warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

class DependencyVisualizer:
    """Symbol Dependency Visualizer"""
    
    def __init__(self, dependencies_json_path: str, output_dir: str = "vis"):
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
    
    def _build_symbol_indexes(self):
        """Build symbol indexes for fast lookup"""
        # Index symbols by name
        self.symbol_by_name = {}
        for symbol_key, symbol_info in self.symbols.items():
            name = symbol_info['name']
            if name not in self.symbol_by_name:
                self.symbol_by_name[name] = []
            self.symbol_by_name[name].append((symbol_key, symbol_info))
        
        # Build dependency relationship indexes
        self.forward_deps = {}   # symbol -> [dependencies]
        self.backward_deps = {}  # symbol -> [dependents]
        
        for dep in self.dependencies:
            source_name = dep['source']['name']
            target_name = dep['target']['name']
            
            # Forward dependencies
            if source_name not in self.forward_deps:
                self.forward_deps[source_name] = []
            self.forward_deps[source_name].append(dep)
            
            # Backward dependencies
            if target_name not in self.backward_deps:
                self.backward_deps[target_name] = []
            self.backward_deps[target_name].append(dep)
    
    def find_symbol_dependencies(self, symbol_name: str, direction: str = "both", 
                                max_depth: int = 2, max_nodes: int = 50) -> Dict:
        """
        Find symbol dependencies
        
        Args:
            symbol_name: Symbol name
            direction: Dependency direction ("forward", "backward", "both")
            max_depth: Maximum search depth
            max_nodes: Maximum number of nodes
        
        Returns:
            Dictionary containing node and edge information
        """
        if symbol_name not in self.symbol_by_name:
            raise ValueError(f"Symbol '{symbol_name}' not found")
        
        nodes = {}
        edges = []
        visited = set()
        
        def add_symbol_to_nodes(name: str, symbol_info: dict = None):
            """Add symbol to node collection"""
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
            """Recursively explore dependencies"""
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
        Visualize symbol dependencies
        
        Args:
            symbol_name: Symbol name
            direction: Dependency direction
            max_depth: Maximum search depth
            max_nodes: Maximum number of nodes
            save_to_file: Whether to save to file
        
        Returns:
            Saved file path
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
        nx.draw_networkx_labels(G, pos, font_size=font_size)
        
        # 设置标题
        direction_map = {
            "forward": "Dependencies",
            "backward": "Dependents", 
            "both": "Bidirectional Dependencies"
        }
        title = f"Symbol '{symbol_name}' {direction_map.get(direction, 'Dependency')}"
        plt.title(title, fontsize=16, fontweight='bold')
        
        # Create legend
        legend_elements = []
        
        # Symbol type legend
        for symbol_type, color in self.colors.items():
            if any(d.get('type') == symbol_type for _, d in G.nodes(data=True)):
                legend_elements.append(mpatches.Patch(color=color, label=f'{symbol_type}'))
        
        # Root node legend
        legend_elements.append(mpatches.Patch(color='#f1c40f', label='Root Symbol'))
        
        # Dependency type legend
        legend_elements.append(mpatches.Patch(color='white', label=''))  # Separator
        for edge_type in edge_types:
            style_name = {
                'function_call': 'Function Call',
                'type_reference': 'Type Reference',
                'macro_use': 'Macro Use',
                'variable_use': 'Variable Use',
                'struct_member': 'Struct Member',
                'enum_use': 'Enum Use'
            }.get(edge_type, edge_type)
            legend_elements.append(mpatches.Patch(color='#34495e', label=style_name))
        
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1))
        
        # Add stats info
        stats_text = f"Nodes: {len(nodes)}\nEdges: {len(edges)}\nDepth: {max_depth}"
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
        """Generate symbol dependency summary (English)"""
        if symbol_name not in self.symbol_by_name:
            return f"Symbol '{symbol_name}' not found"
        
        summary = []
        summary.append(f"{'='*60}")
        summary.append(f"Symbol '{symbol_name}' Dependency Summary")
        summary.append(f"{'='*60}")
        
        # Get symbol info
        symbol_info = self.symbol_by_name[symbol_name][0][1]
        summary.append(f"Type: {symbol_info['type']}")
        summary.append(f"File: {symbol_info['file_path']}")
        summary.append("")
        
        # Forward dependencies (what this symbol depends on)
        forward_deps = self.forward_deps.get(symbol_name, [])
        summary.append(f"📤 Dependencies ({len(forward_deps)}):")
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
            summary.append("  (None)")
        
        summary.append("")
        
        # Backward dependencies (what depends on this symbol)
        backward_deps = self.backward_deps.get(symbol_name, [])
        summary.append(f"📥 Dependents ({len(backward_deps)}):")
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
            summary.append("  (None)")
        
        summary.append(f"{'='*60}")
        
        return "\n".join(summary)
    
    def list_available_symbols(self, limit: int = 20) -> List[str]:
        """List available symbols"""
        symbols = list(self.symbol_by_name.keys())
        symbols.sort()
        return symbols[:limit]
    
    def interactive_mode(self):
        """Interactive mode (English)"""
        print("🔍 Symbol Dependency Visualizer - Interactive Mode")
        print("=" * 50)
        print("Available commands:")
        print("  list                    - List first 20 available symbols")
        print("  search <name>           - Search for symbols")
        print("  vis <symbol> [options]  - Visualize dependencies")
        print("  summary <symbol>        - Show dependency summary")
        print("  help                    - Show help")
        print("  quit                    - Exit")
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
                    print("Visualization options:")
                    print("  vis <symbol> forward   - Show symbols that this symbol depends on")
                    print("  vis <symbol> backward  - Show symbols that depend on this symbol")
                    print("  vis <symbol> both      - Show bidirectional dependencies")
                    print("  vis <symbol> both 3    - Specify search depth as 3")
                elif command == 'list':
                    symbols = self.list_available_symbols()
                    print(f"First {len(symbols)} available symbols:")
                    for i, symbol in enumerate(symbols, 1):
                        print(f"  {i:2d}. {symbol}")
                elif command == 'search':
                    if len(parts) < 2:
                        print("❌ Please provide search keyword")
                        continue
                    keyword = parts[1]
                    matches = [s for s in self.symbol_by_name.keys() if keyword.lower() in s.lower()]
                    if matches:
                        print(f"Found {len(matches)} matching symbols:")
                        for match in sorted(matches)[:20]:
                            print(f"  - {match}")
                        if len(matches) > 20:
                            print(f"  ... and {len(matches) - 20} more symbols")
                    else:
                        print("❌ No matching symbols found")
                elif command == 'vis':
                    if len(parts) < 2:
                        print("❌ Please provide symbol name")
                        continue
                    
                    symbol_name = parts[1]
                    direction = parts[2] if len(parts) > 2 else "both"
                    max_depth = int(parts[3]) if len(parts) > 3 else 2
                    
                    try:
                        filepath = self.visualize_dependencies(symbol_name, direction, max_depth)
                        if filepath:
                            print(f"✅ Visualization completed, saved to: {filepath}")
                    except Exception as e:
                        print(f"❌ Visualization failed: {e}")
                elif command == 'summary':
                    if len(parts) < 2:
                        print("❌ Please provide symbol name")
                        continue
                    
                    symbol_name = parts[1]
                    summary = self.generate_dependency_summary(symbol_name)
                    print(summary)
                else:
                    print(f"❌ Unknown command: {command}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n👋 Goodbye!")

def main():
    """Main function (English)"""
    parser = argparse.ArgumentParser(description='Symbol Dependency Visualizer')
    parser.add_argument('--deps-file', default=str(get_output_dir() / 'symbol_dependencies.json'),
                       help='Dependency JSON file path（默认读取配置的输出目录）')
    parser.add_argument('--output-dir', default=str(get_output_dir()),
                       help='Output directory（默认写入配置的输出目录）')
    parser.add_argument('--symbol', help='Symbol name to visualize')
    parser.add_argument('--direction', choices=['forward', 'backward', 'both'], 
                       default='both', help='Dependency direction')
    parser.add_argument('--depth', type=int, default=2, help='Maximum search depth')
    parser.add_argument('--max-nodes', type=int, default=50, help='Maximum number of nodes')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--summary', action='store_true', help='Show dependency summary')
    
    args = parser.parse_args()
    
    # Check if dependency file exists
    if not os.path.exists(args.deps_file):
        print(f"❌ Dependency file not found: {args.deps_file}")
        print("Please run the symbol dependency analyzer first to generate dependency data")
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
                    print(f"✅ Visualization completed: {filepath}")
        else:
            print("Please specify --symbol parameter or use --interactive mode")
            print("Use --help for detailed help")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    main()
