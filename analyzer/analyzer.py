#!/usr/bin/env python3
"""
统一 Analyzer 类

功能：
- 加载并管理 analyzer/output 下的产物：
  - c_project_analysis.json（精确到起始/结束字节的符号定义信息）
  - symbol_topo_order.json（拓扑序及深度、环）
  - symbol_dependencies.json（如果存在且包含依赖列表则直接复用）
- 对外提供：
  - 按名称查找符号（可选类型、文件过滤）
  - 获取符号定义位置（行号、字节范围）与按字节精确提取定义文本
  - 查找符号的依赖/被依赖（支持递归深度，前向/反向/双向）
  - 统一管理拓扑排序信息，并可按拓扑序过滤/排序

说明：
- 如 symbol_dependencies.json 不含依赖边，则在按需查询单个符号时，
  复用现有 SymbolDependencyAnalyzer 的解析能力，仅对该符号进行依赖提取。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Dict, List, Optional, Tuple, Iterable, Set, Literal

try:  # 兼容直接脚本执行
    from config import to_absolute_path
except ImportError:  # pragma: no cover
    from .config import to_absolute_path

# 懒加载：仅当需要做 AST 解析时才导入（避免环境未装 tree_sitter 时影响其它功能）
_SYMBOL_ANALYZER = None


@dataclass(frozen=True)
class SymbolRef:
    name: str
    type: str  # "functions" | "structs" | "typedefs" | "macros" | "variables" | "enums"
    file_path: str
    start_line: int
    end_line: int
    start_byte: Optional[int]
    end_byte: Optional[int]

    def key(self) -> str:
        return f"{self.name}:{self.type}:{self.file_path}"


@dataclass(frozen=True)
class Edge:
    source: str  # SymbolRef.key()
    target: str  # SymbolRef.key()
    dep_type: str  # DependencyType value if available
    start_line: Optional[int] = None  # 依赖发生位置的起始行（1-based，文件绝对行号）
    end_line: Optional[int] = None    # 依赖发生位置的结束行（1-based，文件绝对行号）


class Analyzer:
    def __init__(
        self,
        analyzer_root: str = os.path.dirname(__file__),
        project_root: Optional[str] = None,
        outputs_dir: Optional[str] = None,
    ) -> None:
        self.analyzer_root = analyzer_root
        self.outputs_dir = outputs_dir or os.path.join(analyzer_root, "output")

        self.path_analysis = os.path.join(self.outputs_dir, "c_project_analysis.json")
        self.path_topo = os.path.join(self.outputs_dir, "symbol_topo_order.json")
        self.path_deps = os.path.join(self.outputs_dir, "symbol_dependencies.json")

        if project_root:
            self.run_pipeline(project_root,self.outputs_dir) 

        # 基础数据
        self.analysis_data: Dict[str, dict] = {}
        self._by_name: Dict[str, List[SymbolRef]] = {}
        self._by_key: Dict[str, SymbolRef] = {}

        # 依赖图（若文件包含则优先加载）
        self._edges: List[Edge] = []
        self._adj_out: Dict[str, List[Edge]] = {}
        self._adj_in: Dict[str, List[Edge]] = {}

        # 拓扑信息（可选）
        self.ordered_names: List[str] = []
        self.depth_by_name: Dict[str, int] = {}
        self.cycle_groups: List[List[str]] = []

        self._load_analysis()
        self._build_symbol_index()
        self._load_topo()
        self._load_dependencies_if_available()

    def run_pipeline(self, project_root: str, output_root: str) -> None:
        """
        执行一整套分析流程：

        1. 更新 analyzer/config.yaml 的 project_root 与 output_root
        2. 依次运行 c_project_analyzer.py、c_project_reconstructor.py、
           symbol_dependency_analyzer.py、demo_visualization.py、
           topo_sort_dependencies.py --node-type non_functions、symbol_batching.py
        """
        analyzer_dir = Path(self.analyzer_root).resolve()
        config_path = analyzer_dir.parent / "analyzer_config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        text = config_path.read_text(encoding="utf-8")
        text, ok_project = re.subn(r"^(project_root:\s*).*$", rf"\1{project_root}", text, flags=re.MULTILINE)
        text, ok_output = re.subn(r"^(output_root:\s*).*$", rf"\1{output_root}", text, flags=re.MULTILINE)
        if not (ok_project and ok_output):
            raise ValueError("未在配置文件中找到 project_root 或 output_root 行")
        config_path.write_text(text, encoding="utf-8")

        commands = [
            ["python", "c_project_analyzer.py"],
            ["python", "c_project_reconstructor.py"],
            ["python", "symbol_dependency_analyzer.py"],
            ["python", "demo_visualization.py"],
            ["python", "topo_sort_dependencies.py", "--node-type", "non_functions"],
            ["python", "symbol_batching.py"],
        ]

        for cmd in commands:
            subprocess.run(cmd, cwd=analyzer_dir, check=True)

    # ---------------------------- 加载阶段 ----------------------------
    def _load_analysis(self) -> None:
        if not os.path.exists(self.path_analysis):
            raise FileNotFoundError(f"c_project_analysis.json 不存在: {self.path_analysis}")
        with open(self.path_analysis, "r", encoding="utf-8") as f:
            self.analysis_data = json.load(f)

    def _build_symbol_index(self) -> None:
        by_name: Dict[str, List[SymbolRef]] = {}
        by_key: Dict[str, SymbolRef] = {}

        type_keys = ["functions", "structs", "typedefs", "macros", "variables", "enums"]
        for file_path, file_data in self.analysis_data.items():
            if not file_data or not file_data.get("parse_success", False):
                continue
            for typ in type_keys:
                for entry in file_data.get(typ, []) or []:
                    name = entry.get("name") or entry.get("text")  # 宏/typedef 可能只在 text
                    if not name:
                        continue
                    sr = SymbolRef(
                        name=name,
                        type=typ,
                        file_path=file_path,
                        start_line=entry.get("start_line", 0),
                        end_line=entry.get("end_line", 0),
                        start_byte=entry.get("start_byte"),
                        end_byte=entry.get("end_byte"),
                    )
                    by_name.setdefault(name, []).append(sr)
                    by_key[sr.key()] = sr

        self._by_name = by_name
        self._by_key = by_key

    def _load_topo(self) -> None:
        if not os.path.exists(self.path_topo):
            return
        try:
            with open(self.path_topo, "r", encoding="utf-8") as f:
                topo = json.load(f)
            self.ordered_names = topo.get("ordered_names") or [n for n, _ in topo.get("ordered_depth", [])]
            od = topo.get("ordered_depth") or []
            self.depth_by_name = {name: depth for name, depth in od}
            self.cycle_groups = topo.get("cycle_groups") or []
        except Exception:
            # topo 文件不是必须
            self.ordered_names = []
            self.depth_by_name = {}
            self.cycle_groups = []

    def _load_dependencies_if_available(self) -> None:
        if not os.path.exists(self.path_deps):
            return
        try:
            with open(self.path_deps, "r", encoding="utf-8") as f:
                data = json.load(f)
            deps = data.get("dependencies")
            syms = data.get("symbols")
            if isinstance(deps, list) and isinstance(syms, dict):
                edges: List[Edge] = []
                for d in deps:
                    s = d.get("source", {})
                    t = d.get("target", {})
                    s_key = f"{s.get('name')}:{s.get('type')}:{s.get('file')}"
                    t_key = f"{t.get('name')}:{t.get('type')}:{t.get('file')}"
                    occ = d.get("occurrence") or {}
                    edges.append(Edge(
                        source=s_key,
                        target=t_key,
                        dep_type=d.get("dependency_type", ""),
                        start_line=occ.get("start_line"),
                        end_line=occ.get("end_line"),
                    ))

                self._set_edges(edges)
        except Exception:
            # 依赖文件不是必须，或结构不包含依赖列表
            pass

    def _set_edges(self, edges: Iterable[Edge]) -> None:
        self._edges = list(edges)
        adj_out: Dict[str, List[Edge]] = {}
        adj_in: Dict[str, List[Edge]] = {}
        for e in self._edges:
            adj_out.setdefault(e.source, []).append(e)
            adj_in.setdefault(e.target, []).append(e)
        self._adj_out = adj_out
        self._adj_in = adj_in

    # ---------------------------- 查询 API ----------------------------
    def find_symbols_by_name(
        self,
        name: str,
        symbol_type: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> List[SymbolRef]:
        """按名称查找符号（可选类型、文件过滤）。"""
        cands = self._by_name.get(name, [])
        if symbol_type:
            cands = [s for s in cands if s.type == symbol_type]
        if file_path:
            cands = [s for s in cands if s.file_path == file_path]
        return cands

    def get_symbol_by_key(self, key: str) -> Optional[SymbolRef]:
        return self._by_key.get(key)

    def get_definition_location(
        self,
        name: str,
        symbol_type: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> List[Tuple[str, int, int, Optional[int], Optional[int]]]:
        """返回 [(file_path, start_line, end_line, start_byte, end_byte), ...]"""
        result = []
        for s in self.find_symbols_by_name(name, symbol_type, file_path):
            result.append((s.file_path, s.start_line, s.end_line, s.start_byte, s.end_byte))
        return result

    def extract_definition_text(
        self,
        sym: SymbolRef,
        encoding_candidates: Tuple[str, ...] = ("utf-8", "latin-1")
    ) -> str:
        """按字节范围精确提取定义文本；若缺少字节信息，则回退到行范围粗略提取。"""
        abs_path = to_absolute_path(sym.file_path)

        if sym.start_byte is not None and sym.end_byte is not None:
            with open(abs_path, "rb") as f:
                f.seek(max(sym.start_byte, 0))
                raw = f.read(max(sym.end_byte - sym.start_byte, 0))
            for enc in encoding_candidates:
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            # 无法可靠解码则按 latin-1 强解
            return raw.decode("latin-1", errors="ignore")

        # 字节信息缺失：回退到行号提取
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            start = max(sym.start_line - 1, 0)
            end = min(sym.end_line, len(lines))
            return "".join(lines[start:end])
        except Exception:
            return ""

    # ---------------------------- 依赖遍历 ----------------------------
    def get_dependencies(
        self,
        start: SymbolRef | str,
        depth: Optional[int] = 1,
        direction: Literal["out", "in", "both"] = "out",
        symbol_types: Optional[Iterable[str]] = None,
    ) -> Tuple[List[SymbolRef], List[Edge]]:
        """
        获取符号在给定层数内的相关符号与边。

        - direction = "out": 出边（依赖谁）
        - direction = "in": 入边（被谁依赖）
        - direction = "both": 双向
        返回 (节点列表, 边列表)，节点包含符合过滤条件的起点与遍历到的所有节点，边为去重后集合。
        如当前未加载全量依赖边，则对起点按需解析其依赖一次（仅第一层）。

        参数：
        - symbol_types: 当提供时，仅保留类型属于该集合的符号与其相互之间的边；遍历仍会穿过其它类型节点。
        """
        start_key = start if isinstance(start, str) else start.key()
        if start_key not in self._by_key:
            raise KeyError(f"起点不存在: {start_key}")

        # 如边为空或缺失，尝试按需补齐起点的第一层出边（仅前向）
        if not self._edges and direction in ("out", "both"):
            self._augment_edges_for_symbol_once(self._by_key[start_key])

        seen_nodes: Set[str] = set([start_key])
        nodes: List[SymbolRef] = []
        edges: List[Edge] = []
        edge_seen: Set[Tuple[str, str, str]] = set()

        type_filter: Optional[Set[str]] = set(symbol_types) if symbol_types else None

        def include(sym: SymbolRef) -> bool:
            return not type_filter or sym.type in type_filter

        start_sym = self._by_key[start_key]
        if include(start_sym):
            nodes.append(start_sym)

        frontier: List[Tuple[str, int]] = [(start_key, 0)]
        while frontier:
            cur, d = frontier.pop(0)
            if depth is not None and d >= depth:
                continue

            # 若依赖未预先加载，且当前节点无出边且需要前向遍历，则尝试按需补齐当前节点的出边
            if not self._edges and direction in ("out", "both") and not self._adj_out.get(cur):
                cur_sym = self._by_key.get(cur)
                if cur_sym:
                    self._augment_edges_for_symbol_once(cur_sym)

            out_edges = self._adj_out.get(cur, []) if direction in ("out", "both") else []
            in_edges = self._adj_in.get(cur, []) if direction in ("in", "both") else []

            for e in out_edges + in_edges:
                nxt = e.target if e.source == cur else e.source
                if nxt not in seen_nodes and nxt in self._by_key:
                    seen_nodes.add(nxt)
                    frontier.append((nxt, d + 1))

                nxt_sym = self._by_key.get(nxt)
                src_sym = self._by_key.get(e.source)
                tgt_sym = self._by_key.get(e.target)

                if nxt_sym and include(nxt_sym) and nxt_sym not in nodes:
                    nodes.append(nxt_sym)

                if src_sym and tgt_sym and include(src_sym) and include(tgt_sym):
                    edge_key = (e.source, e.target, e.dep_type)
                    if edge_key not in edge_seen:
                        edge_seen.add(edge_key)
                        edges.append(e)

        return nodes, edges

    def _augment_edges_for_symbol_once(self, sym: SymbolRef) -> None:
        """当依赖边未全量可用时，对指定符号做一次按需解析并补充出边。"""
        global _SYMBOL_ANALYZER
        try:
            if _SYMBOL_ANALYZER is None:
                # 延迟导入，避免环境无 tree_sitter 时影响基本查询能力
                from .symbol_dependency_analyzer import SymbolDependencyAnalyzer, SymbolType
                _SYMBOL_ANALYZER = SymbolDependencyAnalyzer(self.path_analysis)
                _SYMBOL_ANALYZER.build_symbol_registry()

            # 在 _SYMBOL_ANALYZER 的注册表中找到对应 Symbol
            key = sym.key()
            # symbol_dependency_analyzer 里的 key 规则相同
            source_symbol = _SYMBOL_ANALYZER.dependency_graph.symbols.get(key)
            if not source_symbol:
                return

            # 找到定义文本（优先 full_definition/text）
            file_data = self.analysis_data.get(sym.file_path) or {}
            items = file_data.get(sym.type, [])
            body = ""
            for it in items:
                if it.get("name") == sym.name:
                    body = it.get("full_definition") or it.get("full_declaration") or it.get("text") or ""
                    break

            if not body:
                return

            deps = _SYMBOL_ANALYZER.extract_dependencies_from_text(body, source_symbol)
            if not deps:
                return

            new_edges = []
            for d in deps:
                s_key = f"{d.source_symbol.name}:{d.source_symbol.symbol_type.value}:{d.source_symbol.file_path}"
                t_key = f"{d.target_symbol.name}:{d.target_symbol.symbol_type.value}:{d.target_symbol.file_path}"
                # symbol_dependency_analyzer.Dependency 含 start_line/end_line
                start_line = getattr(d, 'start_line', None)
                end_line = getattr(d, 'end_line', None)
                new_edges.append(Edge(source=s_key, target=t_key, dep_type=d.dependency_type.value,
                                       start_line=start_line, end_line=end_line))

            # 合并并去重
            merged = { (e.source, e.target, e.dep_type): e for e in self._edges }
            for e in new_edges:
                merged[(e.source, e.target, e.dep_type)] = e
            self._set_edges(merged.values())
        except Exception:
            # 按需补充失败时静默忽略，保留已有能力
            return

    # ---------------------------- 拓扑辅助 ----------------------------
    def sort_by_topo(self, symbols: Iterable[SymbolRef]) -> List[SymbolRef]:
        """按已加载的拓扑序对给定符号排序；若未加载拓扑序，原样返回。"""
        if not self.ordered_names:
            return list(symbols)
        order_index = {name: i for i, name in enumerate(self.ordered_names)}
        return sorted(symbols, key=lambda s: order_index.get(s.name, 1 << 30))

    # ---------------------------- 文本提取 ----------------------------
    def edge2text(
        self,
        edge: Edge,
        lines_offset: int = 0,
        assume_relative: bool = True,
        include_end_line: bool = True,
        encoding: str = "utf-8",
    ) -> str:
        """
        提取一条依赖边在源符号文件中的文本片段。

        语义：
        - 当 assume_relative=True（默认）时，认为 edge.start_line/end_line 是相对源符号定义起始行的偏移（0-based 或 1-based？这里按 0-based 处理更直观）。
          即：abs_start = source.start_line - 1 + (edge.start_line or 0)
              abs_end   = source.start_line - 1 + (edge.end_line or edge.start_line or 0)
        - 当 assume_relative=False 时，认为 edge 的行号是文件绝对行号（1-based）。

        注意：当前工程导出的 occurrence.start_line/end_line 为文件绝对行号；
        若你的 edge 来自该导出，建议传 assume_relative=False。
        """
        # 找源符号
        src = self._by_key.get(edge.source)
        if not src:
            return ""
        abs_src_path = to_absolute_path(src.file_path)
        if not os.path.exists(abs_src_path):
            return ""

        try:
            with open(abs_src_path, "r", encoding=encoding) as f:
                lines = f.readlines()
        except Exception:
            return ""

        # 计算绝对行号（0-based slice 边界）
        if assume_relative:
            rel_start = edge.start_line or 0
            rel_end = edge.end_line if edge.end_line is not None else rel_start
            # 将相对偏移视为 0-based 行偏移
            abs_start0 = max((src.start_line - 1) + rel_start, 0)
            abs_end0 = max((src.start_line - 1) + rel_end, abs_start0)
        else:
            # 绝对 1-based -> 0-based
            if edge.start_line is None and edge.end_line is None:
                # 没有行号信息，回退到源符号的整段
                abs_start0 = max(src.start_line - 1, 0)
                abs_end0 = max(src.end_line - 1, abs_start0)
            else:
                start1 = edge.start_line if edge.start_line is not None else src.start_line
                end1 = edge.end_line if edge.end_line is not None else start1
                abs_start0 = max(start1 - 1, 0)
                abs_end0 = max(end1 - 1, abs_start0)

        # 截取（右端含/不含）
        right = abs_end0 + (1 if include_end_line else 0)
        left = max(min(abs_start0 - lines_offset, len(lines)), 0)
        right = max(min(right+lines_offset, len(lines)), left)
        return "".join(lines[left:right])

    def get_in_edge_texts(
        self,
        name_or_key: str,
        lines_offset: int = 2,
        symbol_type: Optional[str] = None,
        file_path: Optional[str] = None,
        assume_relative: bool = False,
        include_end_line: bool = True,
        encoding: str = "utf-8",
    ) -> List[str]:
        """
        获取某个符号“入边、深度=1”的所有边对应的文本片段列表。

        - name_or_key: 可以是简单的符号名，或完整 key("name:type:file_path")。
        - symbol_type/file_path: 当传入的是简单符号名时用于锁定唯一符号。
        - assume_relative: True 表示边上的行号相对源符号起始行；False 表示为文件绝对行号（当前导出为绝对行号，推荐 False）。
        - include_end_line/encoding: 传递给 edge2text 的参数。
        返回：每条入边在其源文件中的代码片段（字符串）列表。
        """
        # 解析目标符号
        target_sym: Optional[SymbolRef] = None
        if name_or_key in self._by_key:
            target_sym = self._by_key[name_or_key]
        else:
            cands = self.find_symbols_by_name(name_or_key, symbol_type, file_path)
            if cands:
                target_sym = cands[0]

        if not target_sym:
            return []

        # 获取入边（深度=1）
        _, edges = self.get_dependencies(target_sym, depth=1, direction="in")
        print(f"Found {len(edges)} in-edges for {target_sym.key()}")
        snippets: List[str] = []
        for e in edges:
            # 只保留真正以该符号为 target 的边
            if e.target != target_sym.key():
                continue
            snippet = self.edge2text(e, lines_offset=lines_offset, assume_relative=assume_relative, include_end_line=include_end_line, encoding=encoding)
            if snippet:
                snippets.append(snippet)
        return snippets

    # ---------------------------- 便捷演示 ----------------------------
    def demo_lookup(self, name: str) -> None:
        cands = self.find_symbols_by_name(name)
        print(f"找到 {name} 的候选 {len(cands)} 个：")
        for s in cands[:5]:
            print(f"- {s.type} @ {s.file_path}:{s.start_line}-{s.end_line} bytes[{s.start_byte},{s.end_byte}]")

        syms = self.find_symbols_by_name(name, symbol_type="functions")
        if syms:
            for i in range(len(syms)):
                text = self.extract_definition_text(syms[i])
                print("--- 片段预览 ---")
                print(text)
        
    def demo_get_dependencies(self, name: str) -> None:
        cands = self.find_symbols_by_name(name)
        if not cands:
            print(f"未找到符号 {name}")
            return
        sym = cands[0]
        print(f"取 {sym.key()} 的出边深度1：")
        nodes, edges = self.get_dependencies(sym, depth=1, direction="out")
        print(f"- 共 {len(nodes)} 个节点，{len(edges)} 条边")
        for n in nodes[:5]:
            print(f"  - {n.key()}")
        for e in edges[:5]:
            print(f"  - {e.source} --[{e.dep_type}]--> {e.target} @ lines[{e.start_line},{e.end_line}]")
        if edges:
            snippet = self.edge2text(edges[0], assume_relative=False)
            print("  片段示例:\n" + (snippet if len(snippet) < 400 else snippet[:400] + "..."))

        print(f"取 {sym.key()} 的入边深度1：")
        nodes, edges = self.get_dependencies(sym, depth=1, direction="in")
        print(f"- 共 {len(nodes)} 个节点，{len(edges)} 条边")
        for n in nodes[:5]:
            print(f"  - {n.key()}")
        for e in edges[:5]:
            print(f"  - {e.source} --[{e.dep_type}]--> {e.target} @ lines[{e.start_line},{e.end_line}]")
        if edges:
            snippet = self.edge2text(edges[0], assume_relative=False)
            print("  片段示例:\n" + (snippet if len(snippet) < 400 else snippet[:400] + "..."))


if __name__ == "__main__":
    # 轻量自检（不会触发 AST）
    az = Analyzer()
    # az.demo_lookup("Queue")
    az.demo_get_dependencies("int_compare")
    # output = az.get_in_edge_texts("int_compare")
    # print(output)