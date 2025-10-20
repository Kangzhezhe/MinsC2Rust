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
import sys
from typing import Dict, List, Optional, Tuple, Iterable, Set, Literal, Union, Mapping, Any

try:  # 兼容直接脚本执行
    from config import get_output_dir, to_absolute_path
except ImportError:  # pragma: no cover
    from .config import get_output_dir, to_absolute_path

try:
    from .symbol_model import normalize_symbol_type
except ImportError:  # pragma: no cover
    from analyzer.symbol_model import normalize_symbol_type

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
        if outputs_dir:
            self.outputs_dir = os.path.abspath(str(outputs_dir))
        else:
            self.outputs_dir = str(get_output_dir())

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

                    s_name = s.get("name")
                    s_type = normalize_symbol_type(s.get("type"))
                    s_file = s.get("file")

                    t_name = t.get("name")
                    t_type = normalize_symbol_type(t.get("type"))
                    t_file = t.get("file")

                    if not (s_name and s_type and s_file and t_name and t_type and t_file):
                        continue

                    s_key = f"{s_name}:{s_type}:{s_file}"
                    t_key = f"{t_name}:{t_type}:{t_file}"
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
                    body = it.get("full_definition") or it.get("full_declaration") or ""
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

    def _find_symbol_entry(self, sym: SymbolRef) -> Optional[dict]:
        file_data = self.analysis_data.get(sym.file_path) or {}
        for item in file_data.get(sym.type, []) or []:
            if item.get("name") == sym.name:
                return item
        return None

    def _get_symbol_declaration(self, sym: SymbolRef) -> str:
        entry = self._find_symbol_entry(sym)
        if entry:
            for key in ("full_declaration", "signature", "declaration", "text"):
                value = entry.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        definition = self.extract_definition_text(sym).strip()
        if definition:
            for line in definition.splitlines():
                stripped = line.strip()
                if stripped:
                    return stripped
        return ""

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
        depth: Optional[int] = 1,
    ) -> List[str]:
        """
        获取某个符号“入边、指定深度”范围内所有边对应的文本片段列表。

        - name_or_key: 可以是简单的符号名，或完整 key("name:type:file_path")。
        - symbol_type/file_path: 当传入的是简单符号名时用于锁定唯一符号。
        - assume_relative: True 表示边上的行号相对源符号起始行；False 表示为文件绝对行号（当前导出为绝对行号，推荐 False）。
        - include_end_line/encoding: 传递给 edge2text 的参数。
        - depth: 递归向上遍历的层数，None 表示不限。
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

        # 获取入边（指定深度）
        nodes, edges = self.get_dependencies(target_sym, depth=depth, direction="in")
        valid_targets = {s.key() for s in nodes}
        # print(f"Found {len(edges)} in-edges within depth={depth} for {target_sym.key()}")
        snippets: List[str] = []
        for e in edges:
            # 只保留指向所遍历节点集合的边
            if e.target not in valid_targets:
                continue
            snippet = self.edge2text(e, lines_offset=lines_offset, assume_relative=assume_relative, include_end_line=include_end_line, encoding=encoding)
            if snippet:
                snippets.append(snippet)
        return snippets

    def get_batch_dependency_contexts(
        self,
        batch: Iterable[Union[str, Tuple[str, Optional[str], Optional[str]], SymbolRef, Mapping[str, object]]],
        *,
        lines_offset: int = 2,
        assume_relative: bool = False,
        include_end_line: bool = True,
        encoding: str = "utf-8",
        depth: Optional[int] = 1,
        default_symbol_type: Optional[str] = None,
        summary: bool = False,
        max_size: int = 10000,
    ) -> Union[Dict[str, Dict[str, Any]], str]:
        """
        批量获取符号的入边上下文片段。

        参数：
        - batch: 可迭代对象，元素可以是：
            * ``SymbolRef`` 实例
            * 符号 key（"name:type:file_path"）字符串
            * ``(name, type, file_path)`` 元组（type/file_path 可省略或为 ``None``）
            * 至少包含 ``name`` 或 ``key`` 字段的字典（可选 ``type``/``file_path``）
        - depth: 同 ``get_in_edge_texts``，控制入边遍历深度。
        - default_symbol_type: 当 batch 元素仅提供名称时用于补充的默认符号类型。
    - summary: 为 True 时，使用 ``llm.LLM`` 对整个 batch 的上下文一次性生成摘要，并直接返回字符串结果。

        返回：
                - 当 ``summary`` 为 False 时，返回 dict，key 为解析出的符号 ``SymbolRef.key()``，value 为包含 ``snippets``（代码片段列表）的字典。
                    若某个元素无法解析符号，则会在输出中以原输入的 ``str`` 形式记录，``snippets`` 为空列表。
                - 当 ``summary`` 为 True 时，返回 LLM 生成的整体摘要字符串；若生成失败，则回退到简单拼接的串联文本。
        """

        contexts: Dict[str, Dict[str, Any]] = {}

        for item in batch:
            symbol: Optional[SymbolRef] = None
            name_or_key: Optional[str] = None
            symbol_type_hint: Optional[str] = default_symbol_type
            file_path_hint: Optional[str] = None

            if isinstance(item, SymbolRef):
                symbol = item
            elif isinstance(item, str):
                name_or_key = item
            elif isinstance(item, tuple):
                if not item:
                    continue
                name_or_key = item[0]
                if len(item) > 1 and item[1]:
                    symbol_type_hint = item[1]  # type: ignore[assignment]
                if len(item) > 2 and item[2]:
                    file_path_hint = item[2]
            elif isinstance(item, dict):
                name_or_key = item.get("key") or item.get("name") or item.get("symbol")
                symbol_type_hint = item.get("type") or item.get("symbol_type") or symbol_type_hint
                file_path_hint = item.get("file_path") or item.get("file") or file_path_hint
            else:
                name_or_key = str(item)

            if symbol_type_hint:
                symbol_type_hint = normalize_symbol_type(symbol_type_hint)

            if symbol is None:
                if not name_or_key:
                    contexts[str(item)] = {"snippets": []}
                    continue

                # 若提供的是完整 key，直接获取
                if name_or_key in self._by_key:
                    symbol = self._by_key[name_or_key]
                else:
                    # 尝试按名称解析
                    cands = self.find_symbols_by_name(name_or_key, symbol_type_hint, file_path_hint)
                    if not cands and symbol_type_hint is None:
                        cands = self.find_symbols_by_name(name_or_key)
                    symbol = cands[0] if cands else None

            if symbol is None:
                contexts[name_or_key or str(item)] = {"snippets": []}
                continue

            key = symbol.key()
            if key in contexts:
                continue

            contexts[key] = {
                "declaration": self._get_symbol_declaration(symbol),
                "snippets": self.get_in_edge_texts(
                    key,
                    lines_offset=lines_offset,
                    assume_relative=assume_relative,
                    include_end_line=include_end_line,
                    encoding=encoding,
                    depth=depth,
                )
            }

        if not summary:
            return contexts

        # 为整个 batch 构造上下文汇总
        symbol_blocks: List[str] = []
        for key, payload in contexts.items():
            snippets = payload.get("snippets", [])
            declaration_text = payload.get("declaration") or ""
            decl_section = declaration_text.strip()
            if not snippets:
                continue
            combined_snippet = "\n\n".join(snippets).strip()
            if not combined_snippet:
                continue
            if max_size > 0 and len(combined_snippet) > max_size:
                combined_snippet = combined_snippet[:max_size] + "..."
            if decl_section:
                block = f"符号 {key} :\n[声明]\n{decl_section}\n\n[引用片段]\n{combined_snippet}"
            else:
                block = f"符号 {key} :\n[声明]\n(未找到声明)\n\n[引用片段]\n{combined_snippet}"
            symbol_blocks.append(block)

        if not symbol_blocks:
            return ""

        aggregated_context = "\n\n".join(symbol_blocks)

        try:
            PROJECT_DIR = Path(__file__).resolve().parents[1]
            if str(PROJECT_DIR) not in sys.path:
                sys.path.insert(0, str(PROJECT_DIR))
            from llm.llm import LLM  # 延迟导入，避免未配置环境时报错
            llm_client = LLM(logger=True)
        except Exception as exc:  # pragma: no cover - 仅在运行时环境缺失时触发
            print(f"⚠️ 无法初始化 LLM，用于生成摘要：{exc}")
            llm_client = None

        if llm_client:
            prompt = """
请阅读以下符号的 C 代码上下文，它们包含真实的调用片段与依赖关系：
{symbols}
请重点提取：
1. 每个符号的参数/返回值含义、依赖的宏或 typedef；
2. 指出上下文中的调用示例（包含实参类型）；
3. 针对涉及指针/引用/结构体字段的类型，说明所有权或借用关系（谁负责释放、是否共享等）。
4. 对于 void * 等万能指针需说明它作为具体类型或是作为泛型用途，并解释所有权处理。

限制：
- 只讨论列表内的符号；完整输出所有列出的符号，不要省略；
- 如无足够信息，明确写出“未知”；不要猜测；
- 对于结构体，说出每一个字段的所有权/借用提示，对于函数，给出其对传入的参数的所有权/借用提示，以及函数对其输入参数的可变性和生命周期。
- 输出格式为分条列出，每条结构为：
  符号 {{key}}:
    - 语义摘要: ...
    - 关键依赖: ...
    - 相关调用示例(列举3条左右): ...
        - 所有权/借用提示: ...
        - 可变性与生命周期: ...
  若缺项请写“无”。
""".format(symbols=", ".join(contexts.keys()))
            prompt = f"{prompt}\n\n<上下文集合>\n{aggregated_context}\n</上下文集合>"
            try:
                summary_text = llm_client.call(prompt)
                if isinstance(summary_text, dict):
                    summary_text = summary_text.get("llm_output") or summary_text.get("summary") or ""
                return str(summary_text).strip()
            except Exception as exc:  # pragma: no cover
                print(f"⚠️ 生成 batch 摘要失败：{exc}")

        # 无法调用 LLM 时回退到直接返回拼接内容
        return aggregated_context

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
    # az.demo_get_dependencies("int_compare")
    # output = az.get_in_edge_texts("ListEntry",depth=2)
    output = az.get_batch_dependency_contexts(["_ListEntry"], depth=1,summary=True)
    print(output)