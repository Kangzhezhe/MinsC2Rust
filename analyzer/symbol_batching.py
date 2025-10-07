#!/usr/bin/env python3

"""
基于文件拓扑排序结果进行文件级分块处理，支持并行转译规划。

Usage:
    python -m analyzer.symbol_batching \
            --topo-order <OUTPUT_DIR>/symbol_topo_order.json \
            --dependencies <OUTPUT_DIR>/symbol_dependencies.json \
            --analysis <OUTPUT_DIR>/c_project_analysis.json \
      --max-chars-per-batch 8000 \
      --batch-size 1 \
            --output <OUTPUT_DIR>/symbol_batches.json

功能：
1. 以文件为单位进行批处理，按照文件拓扑顺序
2. 支持batch_size=1（每个batch一个文件）
3. 根据字符数限制控制批次大小
4. 分析批次间依赖关系，确定并行处理策略
（默认路径从 ``analyzer_config.yaml`` 的 ``output_root`` 读取）
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path

try:  # 兼容脚本直接执行与包内导入
    from config import get_output_dir
except ImportError:  # pragma: no cover
    from .config import get_output_dir

_DEFAULT_OUTPUT_DIR = get_output_dir()


def load_file_analysis(analysis_path: str) -> Dict[str, Dict]:
    """加载文件分析数据，获取每个文件的符号信息和总字符数"""
    with open(analysis_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 按文件组织信息：文件路径 -> 文件信息
    files = {}
    
    # 遍历每个文件
    for file_path, file_data in data.items():
        if not isinstance(file_data, dict):
            continue
        
        # 收集该文件中所有符号的信息
        file_symbols = []
        total_chars = 0
        
        # 从各个类别中提取符号
        categories = ['typedefs', 'structs', 'enums', 'macros', 'functions', 'variables']
        for category in categories:
            for symbol in file_data.get(category, []):
                name = symbol.get('name')
                if name:
                    content = symbol.get('content', '') or symbol.get('text', '') or symbol.get('signature','') or symbol.get('full_declaration','')
                    # content = symbol.get('content', '') or symbol.get('text', '') or symbol.get('full_definition','')
                    symbol_info = {
                        'name': name,
                        'type': category,
                        'start_line': symbol.get('start_line', 0),
                        'end_line': symbol.get('end_line', 0),
                        'content': content,
                        'size_chars': len(content)
                    }
                    file_symbols.append(symbol_info)
                    total_chars += len(content)
        
        files[file_path] = {
            'file_path': file_path,
            'symbols': file_symbols,
            'symbol_count': len(file_symbols),
            'total_chars': total_chars
        }
    
    return files


def load_file_topology(topo_order_path: str) -> Tuple[List[str], List[List[str]]]:
    """从拓扑排序结果中加载文件拓扑顺序和循环依赖组信息"""
    with open(topo_order_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    file_topo = data.get('file_topology', {})
    ordered_files = file_topo.get('ordered_names', [])
    cycle_groups = file_topo.get('cycle_groups', [])
    
    return ordered_files, cycle_groups


def create_file_to_cycle_group_mapping(cycle_groups: List[List[str]]) -> Dict[str, int]:
    """创建文件到循环组的映射"""
    file_to_group = {}
    for group_id, group in enumerate(cycle_groups):
        for file_path in group:
            file_to_group[file_path] = group_id
    return file_to_group


def create_symbol_to_cycle_group_mapping(cycle_groups: List[List[str]]) -> Dict[str, int]:
    """创建符号到循环组的映射"""
    symbol_to_group: Dict[str, int] = {}
    for group_id, group in enumerate(cycle_groups):
        for symbol_name in group:
            symbol_to_group[symbol_name] = group_id
    return symbol_to_group


def load_symbol_dependencies(dependencies_path: Optional[str]) -> List[Dict]:
    """加载符号依赖列表，若不存在则返回空列表"""
    if not dependencies_path:
        return []

    path = Path(dependencies_path)
    if not path.exists():
        return []

    try:
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as exc:  # pragma: no cover - I/O 错误
        print(f"⚠️ 无法读取依赖文件 {dependencies_path}: {exc}")
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        deps = data.get('dependencies')
        if isinstance(deps, list):
            return deps
    return []


def _symbol_key(symbol: Dict) -> Optional[Tuple[str, str]]:
    name = symbol.get('name')
    sym_type = symbol.get('type')
    if not name:
        return None
    return (name, sym_type or '')


def _dep_key(entry: Dict) -> Optional[Tuple[str, str]]:
    if not isinstance(entry, dict):
        return None
    name = entry.get('name')
    sym_type = entry.get('type')
    if not name:
        return None
    return (name, sym_type or '')


def reorder_symbols_by_dependencies(symbols: List[Dict], deps: List[Dict]) -> List[Dict]:
    """根据依赖关系对同一文件内的符号进行拓扑排序"""
    if len(symbols) <= 1 or not deps:
        return symbols

    key_to_symbol: Dict[Tuple[str, str], Dict] = {}
    original_order: Dict[Tuple[str, str], int] = {}
    for idx, symbol in enumerate(symbols):
        key = _symbol_key(symbol)
        if key is None:
            return symbols  # 存在匿名符号，无法建立映射，保持原顺序
        if key in key_to_symbol:
            return symbols  # 同名同类型重复，保持原顺序
        key_to_symbol[key] = symbol
        original_order[key] = idx

    adjacency: Dict[Tuple[str, str], Set[Tuple[str, str]]] = {k: set() for k in key_to_symbol.keys()}
    indegree: Dict[Tuple[str, str], int] = {k: 0 for k in key_to_symbol.keys()}

    for dep in deps:
        source = _dep_key(dep.get('source', {}))
        target = _dep_key(dep.get('target', {}))
        if source is None or target is None:
            continue
        if source not in indegree or target not in indegree:
            continue
        if source == target:
            continue
        # source 依赖 target，需要 target 在前 -> 添加 target -> source 边
        if source not in adjacency[target]:
            adjacency[target].add(source)
            indegree[source] += 1

    queue = [key for key, deg in indegree.items() if deg == 0]
    ordered_keys: List[Tuple[str, str]] = []

    while queue:
        queue.sort(key=lambda k: original_order.get(k, float('inf')))
        current = queue.pop(0)
        ordered_keys.append(current)
        for neighbor in adjacency[current]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if len(ordered_keys) != len(key_to_symbol):
        # 存在环或缺失，回退原顺序
        return symbols

    return [key_to_symbol[key] for key in ordered_keys]


def apply_dependency_ordering(files: Dict[str, Dict], dependencies: List[Dict]) -> int:
    """根据依赖关系调整每个文件内部符号顺序，返回调整的文件数"""
    if not dependencies:
        return 0

    deps_by_file: Dict[str, List[Dict]] = defaultdict(list)
    for dep in dependencies:
        source = dep.get('source', {})
        target = dep.get('target', {})
        source_file = source.get('file') or source.get('file_path')
        target_file = target.get('file') or target.get('file_path')
        if not source_file or source_file != target_file:
            continue
        deps_by_file[source_file].append(dep)

    adjusted = 0
    for file_path, info in files.items():
        file_deps = deps_by_file.get(file_path)
        if not file_deps:
            continue
        ordered = reorder_symbols_by_dependencies(info.get('symbols', []), file_deps)
        if ordered != info.get('symbols', []):
            info['symbols'] = ordered
            adjusted += 1
    return adjusted


def create_file_batches(ordered_files: List[str], 
                       file_cycle_groups: List[List[str]],
                       files: Dict[str, Dict],
                       batch_size: int = 1,
                       max_chars_per_batch: int = 8000) -> List[Dict]:
    """
    基于文件拓扑顺序创建批次
    
    Args:
        ordered_files: 按拓扑顺序排列的文件列表
        file_cycle_groups: 文件循环依赖组
        files: 文件信息字典
        batch_size: 每批次文件数量（当前实现为1）
        max_chars_per_batch: 每批次最大字符数
    
    Returns:
        批次列表，每个批次包含文件信息
    """
    batches = []
    file_to_cycle_group = create_file_to_cycle_group_mapping(file_cycle_groups)
    processed_cycle_groups = set()
    
    # 按拓扑顺序处理文件
    for file_path in ordered_files:
        if file_path not in files:
            continue  # 跳过不存在的文件
        
        file_info = files[file_path]
        
        # 检查是否属于循环组
        if file_path in file_to_cycle_group:
            cycle_group_id = file_to_cycle_group[file_path]
            
            # 如果这个循环组还没有被处理过
            if cycle_group_id not in processed_cycle_groups:
                processed_cycle_groups.add(cycle_group_id)
                
                # 获取整个循环组的文件
                cycle_group_files = file_cycle_groups[cycle_group_id]
                
                if batch_size == 1:
                    # 每个文件单独一个批次，但保持循环组标记
                    for cycle_file in cycle_group_files:
                        if cycle_file in files:
                            batch = {
                                'batch_id': len(batches),
                                'files': [cycle_file],
                                'file_count': 1,
                                'total_chars': files[cycle_file]['total_chars'],
                                'symbol_count': files[cycle_file]['symbol_count'],
                                'is_cycle_group': True,
                                'cycle_group_id': cycle_group_id,
                                'cycle_group_files': cycle_group_files,
                                'symbols': []  # 将添加详细符号信息
                            }
                            
                            # 添加符号信息
                            for symbol in files[cycle_file]['symbols']:
                                batch['symbols'].append({
                                    'name': symbol['name'],
                                    'type': symbol['type'],
                                    'file_path': cycle_file,
                                    'start_line': symbol['start_line'],
                                    'end_line': symbol['end_line'],
                                    'content': symbol['content'],
                                    'size_chars': symbol['size_chars']
                                })
                            
                            batches.append(batch)
                else:
                    # 多文件批次处理（暂不实现）
                    pass
        else:
            # 非循环组文件，单独处理
            if batch_size == 1:
                batch = {
                    'batch_id': len(batches),
                    'files': [file_path],
                    'file_count': 1,
                    'total_chars': file_info['total_chars'],
                    'symbol_count': file_info['symbol_count'],
                    'is_cycle_group': False,
                    'cycle_group_id': None,
                    'cycle_group_files': [],
                    'symbols': []
                }
                
                # 添加符号信息
                for symbol in file_info['symbols']:
                    batch['symbols'].append({
                        'name': symbol['name'],
                        'type': symbol['type'],
                        'file_path': file_path,
                        'start_line': symbol['start_line'],
                        'end_line': symbol['end_line'],
                        'content': symbol['content'],
                        'size_chars': symbol['size_chars']
                    })
                
                batches.append(batch)
    
    return batches


def save_batches(batches: List[Dict], output_path: str):
    """保存批次结果到JSON文件"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(batches, f, ensure_ascii=False, indent=2)


def group_symbols_by_file(topo_order: List[Tuple[str, int]], 
                         symbols: Dict[str, Dict]) -> Dict[str, List[Tuple[str, int]]]:
    """按文件分组符号，保持拓扑顺序（不考虑循环依赖）"""
    file_groups = defaultdict(list)
    
    for name, depth in topo_order:
        if name in symbols:
            file_path = symbols[name]['file_path']
            file_groups[file_path].append((name, depth))
        else:
            # 对于没有详细信息的符号，放入未知组
            file_groups['<unknown>'].append((name, depth))
    
    return file_groups


def create_batches_from_file_groups_with_cycles(file_groups: Dict[str, List[Tuple[str, int]]], 
                                              symbols: Dict[str, Dict],
                                              cycle_groups: List[List[str]],
                                              max_chars_per_batch: int) -> List[Dict]:
    """从文件分组创建批次，考虑字符数限制和循环依赖组的完整性"""
    batches = []
    symbol_to_cycle_group = create_symbol_to_cycle_group_mapping(cycle_groups)
    
    for file_path, symbol_list in file_groups.items():
        if not symbol_list:
            continue
            
        current_batch = {
            'batch_id': len(batches),
            'symbols': [],
            'total_chars': 0,
            'min_depth': float('inf'),
            'max_depth': float('-inf'),
            'cycle_groups': []  # 记录该批次包含的循环组
        }
        
        i = 0
        while i < len(symbol_list):
            name, depth = symbol_list[i]
            symbol_info = symbols.get(name, {})
            char_count = symbol_info.get('size_chars', len(name))
            
            # 检查是否属于循环组
            if name in symbol_to_cycle_group:
                group_id = symbol_to_cycle_group[name]
                cycle_group = cycle_groups[group_id]
                
                # 计算整个循环组的字符数
                group_char_count = 0
                group_symbols = []
                for j in range(i, len(symbol_list)):
                    other_name, other_depth = symbol_list[j]
                    if other_name in cycle_group:
                        other_info = symbols.get(other_name, {})
                        other_char_count = other_info.get('size_chars', len(other_name))
                        group_char_count += other_char_count
                        group_symbols.append((j, other_name, other_depth, other_char_count, other_info))
                
                # 检查循环组是否能放入当前批次
                if (current_batch['symbols'] and 
                    current_batch['total_chars'] + group_char_count > max_chars_per_batch):
                    
                    # 完成当前批次
                    batches.append(current_batch)
                    
                    # 开始新批次
                    current_batch = {
                        'batch_id': len(batches),
                        'symbols': [],
                        'total_chars': 0,
                        'min_depth': float('inf'),
                        'max_depth': float('-inf'),
                        'cycle_groups': []
                    }
                
                # 添加整个循环组到当前批次
                for j, other_name, other_depth, other_char_count, other_info in group_symbols:
                    current_batch['symbols'].append({
                        'name': other_name,
                        'depth': other_depth,
                        'char_count': other_char_count,
                        'type': other_info.get('type', 'unknown'),
                        'content': other_info.get('content', ''),
                        'start_line': other_info.get('start_line', 0),
                        'end_line': other_info.get('end_line', 0),
                        'file_path': other_info.get('file_path', '<unknown>'),
                        'cycle_group_id': group_id
                    })
                    current_batch['total_chars'] += other_char_count
                    current_batch['min_depth'] = min(current_batch['min_depth'], other_depth)
                    current_batch['max_depth'] = max(current_batch['max_depth'], other_depth)
                
                # 记录循环组信息
                if group_id not in current_batch['cycle_groups']:
                    current_batch['cycle_groups'].append(group_id)
                
                # 跳过已处理的符号
                processed_indices = {j for j, _, _, _, _ in group_symbols}
                # 找到下一个未处理的索引
                i = i + 1
                while i < len(symbol_list) and i in processed_indices:
                    i += 1
                # 继续处理下一个未在循环组中的符号
                continue
            
            # 普通符号处理
            # 检查是否需要开始新批次
            if (current_batch['symbols'] and 
                current_batch['total_chars'] + char_count > max_chars_per_batch):
                
                # 完成当前批次
                batches.append(current_batch)
                
                # 开始新批次
                current_batch = {
                    'batch_id': len(batches),
                    'symbols': [],
                    'total_chars': 0,
                    'min_depth': float('inf'),
                    'max_depth': float('-inf'),
                    'cycle_groups': []
                }
            
            # 添加符号到当前批次
            current_batch['symbols'].append({
                'name': name,
                'depth': depth,
                'char_count': char_count,
                'type': symbol_info.get('type', 'unknown'),
                'content': symbol_info.get('content', ''),
                'start_line': symbol_info.get('start_line', 0),
                'end_line': symbol_info.get('end_line', 0),
                'file_path': symbol_info.get('file_path', '<unknown>')
            })
            current_batch['total_chars'] += char_count
            current_batch['min_depth'] = min(current_batch['min_depth'], depth)
            current_batch['max_depth'] = max(current_batch['max_depth'], depth)
            
            i += 1
        
        # 添加最后一个批次
        if current_batch['symbols']:
            batches.append(current_batch)
    
    return batches


def create_batches_from_file_groups(file_groups: Dict[str, List[Tuple[str, int]]], 
                                   symbols: Dict[str, Dict],
                                   max_chars_per_batch: int) -> List[Dict]:
    """从文件分组创建批次，考虑字符数限制（不考虑循环依赖）"""
    batches = []
    
    for file_path, symbol_list in file_groups.items():
        if not symbol_list:
            continue
            
        current_batch = {
            'batch_id': len(batches),
            'symbols': [],
            'total_chars': 0,
            'min_depth': float('inf'),
            'max_depth': float('-inf')
        }
        
        for name, depth in symbol_list:
            symbol_info = symbols.get(name, {})
            char_count = symbol_info.get('size_chars', len(name))  # 如果没有内容，至少算符号名长度
            
            # 检查是否需要开始新批次
            if (current_batch['symbols'] and 
                current_batch['total_chars'] + char_count > max_chars_per_batch):
                
                # 完成当前批次
                batches.append(current_batch)
                
                # 开始新批次
                current_batch = {
                    'batch_id': len(batches),
                    'symbols': [],
                    'total_chars': 0,
                    'min_depth': float('inf'),
                    'max_depth': float('-inf')
                }
            
            # 添加符号到当前批次
            current_batch['symbols'].append({
                'name': name,
                'depth': depth,
                'char_count': char_count,
                'type': symbol_info.get('type', 'unknown'),
                'content': symbol_info.get('content', ''),
                'start_line': symbol_info.get('start_line', 0),
                'end_line': symbol_info.get('end_line', 0),
                'file_path': symbol_info.get('file_path', '<unknown>')
            })
            current_batch['total_chars'] += char_count
            current_batch['min_depth'] = min(current_batch['min_depth'], depth)
            current_batch['max_depth'] = max(current_batch['max_depth'], depth)
        
        # 添加最后一个批次
        if current_batch['symbols']:
            batches.append(current_batch)
    
    return batches


def analyze_batch_dependencies(batches: List[Dict], 
                              dependencies: List[Dict],
                              symbols_info: Dict[str, Dict]) -> Dict[int, Set[int]]:
    """分析批次间的依赖关系"""
    # 创建符号到批次的映射
    symbol_to_batch = {}
    for batch in batches:
        batch_id = batch['batch_id']
        for symbol in batch['symbols']:
            symbol_to_batch[symbol['name']] = batch_id
    
    # 分析批次间依赖
    batch_dependencies = defaultdict(set)
    
    for dep in dependencies:
        source_name = dep.get('source', {}).get('name')
        target_name = dep.get('target', {}).get('name')
        
        if not source_name or not target_name:
            continue
            
        source_batch = symbol_to_batch.get(source_name)
        target_batch = symbol_to_batch.get(target_name)
        
        # 如果源和目标在不同批次中，记录依赖关系
        if (source_batch is not None and target_batch is not None and 
            source_batch != target_batch):
            batch_dependencies[source_batch].add(target_batch)
            print(f"Batch {source_batch} depends on Batch {target_batch} due to {source_name} -> {target_name}")
    
    return batch_dependencies


def find_parallel_batches(batches: List[Dict], 
                         batch_dependencies: Dict[int, Set[int]]) -> List[List[int]]:
    """找到可以并行处理的批次组"""
    num_batches = len(batches)
    
    # 计算每个批次的入度
    in_degree = defaultdict(int)
    for batch_id in range(num_batches):
        in_degree[batch_id] = 0
    
    for source_batch, target_batches in batch_dependencies.items():
        for target_batch in target_batches:
            in_degree[target_batch] += 1
    
    # 拓扑排序，找到并行层级
    parallel_levels = []
    remaining_batches = set(range(num_batches))
    
    while remaining_batches:
        # 找到当前可以处理的批次（入度为0）
        current_level = []
        for batch_id in list(remaining_batches):
            if in_degree[batch_id] == 0:
                current_level.append(batch_id)
        
        if not current_level:
            # 如果没有入度为0的批次，说明有循环依赖，按深度顺序处理
            current_level = [min(remaining_batches, key=lambda x: batches[x]['min_depth'])]
        
        parallel_levels.append(sorted(current_level))
        
        # 移除已处理的批次，更新入度
        for batch_id in current_level:
            remaining_batches.remove(batch_id)
            for target_batch in batch_dependencies.get(batch_id, []):
                if target_batch in remaining_batches:
                    in_degree[target_batch] -= 1
    
    return parallel_levels


def main():
    parser = argparse.ArgumentParser(description="对文件进行分块处理，支持并行转译规划")
    
    # 输入文件
    parser.add_argument("--topo-order", default=str(_DEFAULT_OUTPUT_DIR / "symbol_topo_order.json"),
                       help="拓扑排序结果文件（默认读取配置的输出目录）")
    parser.add_argument("--analysis", default=str(_DEFAULT_OUTPUT_DIR / "c_project_analysis.json"),
                       help="C项目分析结果文件（默认读取配置的输出目录）")
    parser.add_argument("--dependencies", default=str(_DEFAULT_OUTPUT_DIR / "symbol_dependencies.json"),
                       help="符号依赖关系文件（用于排序符号，默认为配置输出目录）")
    
    # 配置参数
    parser.add_argument("--batch-size", type=int, default=1,
                       help="每个批次的文件数量（当前实现为1）")
    parser.add_argument("--max-chars-per-batch", type=int, default=8000,
                       help="每个批次的最大字符数")
    
    # 输出文件
    parser.add_argument("--output", default=str(_DEFAULT_OUTPUT_DIR / "file_batches.json"),
                       help="输出的批次规划文件（默认写入配置的输出目录）")
    
    args = parser.parse_args()
    
    # 确保输入文件存在
    topo_path = Path(args.topo_order)
    if not topo_path.is_absolute():
        topo_path = (_DEFAULT_OUTPUT_DIR / topo_path).resolve()

    analysis_path = Path(args.analysis)
    if not analysis_path.is_absolute():
        analysis_path = (_DEFAULT_OUTPUT_DIR / analysis_path).resolve()

    dependencies_path = Path(args.dependencies)
    if not dependencies_path.is_absolute():
        dependencies_path = (_DEFAULT_OUTPUT_DIR / dependencies_path).resolve()

    if not topo_path.exists():
        print(f"错误: 文件不存在 {topo_path}")
        return 1

    if not analysis_path.exists():
        print(f"错误: 文件不存在 {analysis_path}")
        return 1
    
    print("正在加载数据...")
    
    # 加载数据
    files = load_file_analysis(str(analysis_path))
    ordered_files, file_cycle_groups = load_file_topology(str(topo_path))

    dependencies = load_symbol_dependencies(str(dependencies_path))
    adjusted_files = apply_dependency_ordering(files, dependencies)

    if dependencies:
        print(f"已根据符号依赖调整 {adjusted_files} 个文件的符号顺序")
    else:
        print("未加载到符号依赖文件，保留原始符号顺序")
    
    print(f"加载了 {len(files)} 个文件")
    print(f"文件拓扑顺序包含 {len(ordered_files)} 个文件")
    print(f"发现 {len(file_cycle_groups)} 个文件循环依赖组")
    
    # 创建基于文件的批次
    print("创建文件批次...")
    batches = create_file_batches(ordered_files, file_cycle_groups, files, 
                                 args.batch_size, args.max_chars_per_batch)
    
    # 统计信息
    total_files = sum(len(batch['files']) for batch in batches)
    total_symbols = sum(len(batch['symbols']) for batch in batches)
    print(f"创建了 {len(batches)} 个批次，包含 {total_files} 个文件，{total_symbols} 个符号")
    
    # 生成输出
    result = {
        'config': {
            'batch_size': args.batch_size,
            'max_chars_per_batch': args.max_chars_per_batch,
            'total_files': len(files),
            'total_batches': len(batches),
            'file_cycle_groups_count': len(file_cycle_groups),
            'files_in_cycles': sum(len(group) for group in file_cycle_groups)
        },
        'file_topology': {
            'ordered_files': ordered_files,
            'cycle_groups': file_cycle_groups
        },
        'batches': batches
    }
    
    # 保存结果
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (_DEFAULT_OUTPUT_DIR / output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open('w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 输出统计信息
    print(f"\n✓ 文件批次规划完成: {output_path}")
    print(f"  总文件数: {len(files)}")
    print(f"  总批次数: {len(batches)}")
    print(f"  批次大小: {args.batch_size} 文件/批次")
    if file_cycle_groups:
        print(f"  文件循环依赖组: {len(file_cycle_groups)} 组，包含 {sum(len(group) for group in file_cycle_groups)} 个文件")
    
    print("\n批次统计:")
    for i, batch in enumerate(batches[:10]):  # 显示前10个批次
        cycle_info = f"(循环组 {batch['cycle_group_id']})" if batch['is_cycle_group'] else ""
        print(f"  批次 {i}: {len(batch['files'])} 个文件, {len(batch['symbols'])} 个符号, "
              f"{batch['total_chars']} 字符 {cycle_info}")
        for file_path in batch['files']:
            print(f"    - {file_path}")
    if len(batches) > 10:
        print(f"  ... 还有 {len(batches) - 10} 个批次")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())