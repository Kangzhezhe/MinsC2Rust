import atexit
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union
from contextlib import suppress
from urllib.parse import unquote, urlparse

from pydantic import BaseModel, Field, RootModel, ValidationError

from .agent import Agent

from concurrent.futures import ThreadPoolExecutor, as_completed

from analyzer.analyzer import Analyzer

import pylspclient
from pylspclient.lsp_pydantic_strcuts import (
    LanguageIdentifier,
    DocumentSymbol,
    Location,
    LocationLink,
    Position,
    Range,
    ReferenceContext,
    ReferenceParams,
    SymbolInformation,
    SymbolKind,
    TextDocumentIdentifier,
    TextDocumentItem,
)

class ToolOperation(BaseModel):
    tool: str = Field(description='要调用的工具方法名')
    args: Dict[str, Any] = Field(description='工具参数字典，可为空；',default_factory=dict)
    kwargs: Dict[str, Any] = Field(description='关键字参数字典，可为空。',default_factory=dict)

class ToolOperations(RootModel[List[ToolOperation]]):
    """操作列表模型，封装一组工具调用。"""

    @classmethod
    def from_raw(cls, raw_ops: Iterable[Any]) -> "ToolOperations":
        data = list(raw_ops)
        if not data:
            raise SWEAgentToolError("operations 不能为空")
        return cls.model_validate(data)

    def __iter__(self):
        return iter(self.root)

class SWEAgentToolError(RuntimeError):
    """自定义异常：用于指示SWE Agent工具执行失败。"""


@dataclass
class SWEFileSystemTools:
    """SWE Agent默认工具集，实现文件操作、命令执行等能力。"""
    PLACEHOLDER_LINE_RE = re.compile(r"^\s*(?:(?://|#)\s*)?\.\.\. existing code \.\.\.\s*$")

    workspace_root: Path
    encoding: str = "utf-8"
    command_timeout: int = 120
    max_output_chars: int = 12_000
    _workspace_root: Path = field(init=False, repr=False)
    _symbol_analyzer: Optional[Analyzer] = field(default=None, init=False, repr=False)
    _analyzer_lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.workspace_root).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"工作目录不存在或不是文件夹: {self.workspace_root}")
        self._workspace_root = root

    # ------------------------------------------------------------------
    # 基础路径处理
    # ------------------------------------------------------------------
    def _resolve_path(self, path: str | os.PathLike[str], *, allow_nonexistent: bool = False) -> Path:
        candidate = (self._workspace_root / Path(path)).expanduser()
        try:
            resolved = candidate.resolve(strict=not allow_nonexistent)
        except FileNotFoundError:
            resolved = candidate.resolve(strict=False)
        if not self._is_within_root(resolved):
            raise SWEAgentToolError("路径越界：禁止访问工作目录之外的文件")
        return resolved

    def _relative_to_root(self, path: Path) -> str:
        try:
            rel = path.relative_to(self._workspace_root)
        except ValueError as exc:
            raise SWEAgentToolError("路径越界：禁止访问工作目录之外的文件") from exc
        return "." if rel == Path(".") else rel.as_posix()

    def _is_within_root(self, path: Path) -> bool:
        try:
            path.relative_to(self._workspace_root)
            return True
        except ValueError:
            return False

    def _iter_files(self, start: Path) -> Iterable[Path]:
        if start.is_file():
            yield start
            return
        for item in start.rglob("*"):
            if item.is_file():
                yield item

    def _clip_output(self, text: str) -> Tuple[str, bool]:
        if text is None:
            return "", False
        if len(text) <= self.max_output_chars:
            return text, False
        clipped = text[: self.max_output_chars]
        suffix = f"\n...（输出已截断，剩余 {len(text) - self.max_output_chars} 字符）"
        return clipped + suffix, True

    def _get_analyzer(self) -> Analyzer:
        with self._analyzer_lock:
            if self._symbol_analyzer is not None:
                return self._symbol_analyzer

            try:
                self._symbol_analyzer = Analyzer(project_root=str(self._workspace_root))
            except FileNotFoundError as exc:
                raise SWEAgentToolError(
                    f"加载 analyzer 产物失败: {exc}"
                ) from exc
            except Exception as exc:  # pragma: no cover - 保护性兜底
                raise SWEAgentToolError(
                    f"初始化 Analyzer 失败: {exc}"
                ) from exc

            return self._symbol_analyzer

    def _build_path_filter(
        self, filePaths: Optional[List[str]]
    ) -> Tuple[Callable[[str], bool], List[str]]:
        if not filePaths:
            return (lambda _rel: True), []

        filters: List[Tuple[Path, bool]] = []
        normalized: List[str] = []
        for raw_path in filePaths:
            resolved = self._resolve_path(raw_path, allow_nonexistent=False)
            filters.append((resolved, resolved.is_dir()))
            normalized.append(self._relative_to_root(resolved))

        def matcher(rel_path: str) -> bool:
            abs_path = (self._workspace_root / Path(rel_path)).resolve()
            for base, is_dir in filters:
                if is_dir:
                    try:
                        abs_path.relative_to(base)
                        return True
                    except ValueError:
                        continue
                else:
                    if abs_path == base:
                        return True
            return False

        return matcher, normalized

    def _normalize_patch(self, patch: str) -> Tuple[str, bool]:
        """调整补丁块头部的行数，避免因统计不准导致应用失败。"""
        if not patch:
            return patch, False

        lines = patch.splitlines(keepends=True)
        hunk_header_re = re.compile(r"^@@ -(\d+)(,\d+)? \+(\d+)(,\d+)? @@.*")

        current_header: Optional[str] = None
        hunk_lines: List[str] = []
        rebuilt: List[str] = []
        changed = False

        def flush_hunk() -> None:
            nonlocal current_header, hunk_lines, changed
            if current_header is None:
                return

            match = hunk_header_re.match(current_header)
            if not match:
                rebuilt.append(current_header)
                rebuilt.extend(hunk_lines)
                current_header = None
                hunk_lines = []
                return

            # 正确统计行数：上下文行和删除行计入原文件，上下文行和新增行计入新文件
            original_len = sum(1 for line in hunk_lines if line.startswith((" ", "-")))
            modified_len = sum(1 for line in hunk_lines if line.startswith((" ", "+")))

            start_orig = match.group(1)
            start_mod = match.group(3)

            # 如果原始补丁的行数统计是正确的，就保持不变
            orig_count_str = match.group(2) or ""  # 可能是 ",4" 或者为空
            mod_count_str = match.group(4) or ""   # 可能是 ",4" 或者为空
            
            # 只有当我们计算出的行数与原始不同时才修改
            if orig_count_str:
                orig_expected = int(orig_count_str[1:])  # 去掉逗号
            else:
                orig_expected = 1
            
            if mod_count_str:
                mod_expected = int(mod_count_str[1:])  # 去掉逗号  
            else:
                mod_expected = 1
                
            # 只在计算结果与原始不同时才修改头部
            if original_len == orig_expected and modified_len == mod_expected:
                # 保持原始头部不变
                rebuilt.append(current_header)
            else:
                # 重新计算行数
                orig_count = f",{original_len}" if original_len != 1 else ""
                mod_count = f",{modified_len}" if modified_len != 1 else ""
                new_header = f"@@ -{start_orig}{orig_count} +{start_mod}{mod_count} @@\n"
                changed = True
                rebuilt.append(new_header)
            
            rebuilt.extend(hunk_lines)
            current_header = None
            hunk_lines = []

        for line in lines:
            if line.startswith("@@"):
                flush_hunk()
                current_header = line
                hunk_lines = []
            elif current_header is not None:
                hunk_lines.append(line)
            else:
                rebuilt.append(line)

        flush_hunk()

        return "".join(rebuilt), changed

    # ------------------------------------------------------------------
    # 工具接口
    # ------------------------------------------------------------------
    
    def run_tools_parallel(
        self,
        operations: List[ToolOperation],
        max_workers: Optional[int] = None,
    ) -> Dict[str, Any]:
        """并行执行多个工具调用。
        您能够在单次响应中调用多个工具。当需要获取多个独立信息时，请将工具调用批量处理以实现最优性能。例如使用可用的搜索工具来理解代码库和用户的查询。我们鼓励您广泛地并行或顺序使用搜索工具。
        """
        ops_model = ToolOperations.from_raw(operations)
        tasks = list(ops_model)
        worker_count = max_workers or len(tasks)
        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(
                    getattr(self, task.tool),
                    **(task.args or {}),
                    **(task.kwargs or {}),
                ): (idx, task.tool)
                for idx, task in enumerate(tasks)
            }
            for future in as_completed(future_map):
                idx, tool_name = future_map[future]
                try:
                    outcome = future.result()
                    results.append({"index": idx, "tool": tool_name, "result": outcome})
                except Exception as exc:
                    errors.append({"index": idx, "tool": tool_name, "error": str(exc)})

        results.sort(key=lambda item: item["index"])
        errors.sort(key=lambda item: item["index"])
        return {
            "tool": "run_tools_parallel",
            "workers": worker_count,
            "results": results,
            "errors": errors,
        }

    def list_dir(self, path: str = ".") -> Dict[str, Any]:
        """列出目录内容。"""
        target = self._resolve_path(path)
        entries: List[Dict[str, Any]] = []
        for entry in sorted(target.iterdir(), key=lambda item: item.name):
            entry_info: Dict[str, Any] = {
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
            }
            if entry.is_file():
                try:
                    entry_info["size"] = entry.stat().st_size
                    entry_info["lines"] = sum(1 for _ in entry.open("r", encoding=self.encoding, errors="ignore"))
                except OSError:
                    entry_info["size"] = None
                    entry_info["lines"] = None
            entries.append(entry_info)
        return {"path": self._relative_to_root(target), "entries": entries}

    def file_search(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        """按照 glob 模式搜索工作区内的文件或目录。

        使用示例::

            # 搜索所有 Python 源文件（最多返回 20 条）
            toolset.file_search("**/*.py")

            # 搜索 src 目录下的 C 文件，最多返回 10 条
            toolset.file_search("src/**/*.c", max_results=10)

        :param query: 需要匹配的 glob 模式，例如 ``src/**/*.py``。
        :param max_results: 返回的最大结果数，默认 20，必须为正数。
        """

        if not query or not query.strip():
            raise SWEAgentToolError("query 不能为空")
        if max_results <= 0:
            raise SWEAgentToolError("max_results 必须是正整数")

        normalized_query = query.strip()
        seen: Set[Path] = set()
        matches: List[Dict[str, Any]] = []

        candidates = sorted(self._workspace_root.glob(normalized_query))

        for candidate in candidates:
            resolved = candidate.resolve(strict=False)
            if not self._is_within_root(resolved):
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            matches.append(
                {
                    "path": self._relative_to_root(resolved),
                    "type": "directory" if resolved.is_dir() else "file",
                }
            )
            if len(matches) >= max_results:
                break

        return {"pattern": normalized_query, "matches": matches, "limit": max_results}

    def grep_search(
        self,
        query: str,
        includePattern: Optional[str] = None,
        isRegexp: bool = False,
        max_results: int = 20,
    ) -> Dict[str, Any]:
        """在工作区内执行快速文本搜索。

        使用示例:

            # 精确查找 README 中的 "TODO"
            toolset.grep_search("TODO", includePattern="README.md")

            # 在 C 源文件中用正则匹配函数定义（最多 20 条结果）
            toolset.grep_search(r"^int\\s+main", includePattern="src/**/*.c", isRegexp=True)

        :param query: 要搜索的文本或正则表达式，不能为空。
        :param includePattern: 可选的 glob 模式，仅在匹配的文件中搜索；默认遍历全部文件。
        :param isRegexp: 当为 True 时，按正则表达式处理 ``query``。
        """

        if not query or not query.strip():
            raise SWEAgentToolError("query 不能为空")
        if max_results <= 0:
            raise SWEAgentToolError("max_results 必须是正整数")

        normalized_query = query if isRegexp else query.strip()

        try:
            compiled: Optional[re.Pattern[str]] = re.compile(normalized_query) if isRegexp else None
        except re.error as exc:
            raise SWEAgentToolError(f"正则表达式无效: {exc}") from exc

        if includePattern:
            candidates = sorted(self._workspace_root.glob(includePattern))
        else:
            candidates = sorted(self._workspace_root.rglob("*"))

        matches: List[Dict[str, Any]] = []
        seen: Set[Path] = set()

        for candidate in candidates:
            if not candidate.is_file():
                continue

            resolved = candidate.resolve(strict=False)
            if resolved in seen:
                continue
            if not self._is_within_root(resolved):
                continue
            seen.add(resolved)

            try:
                with resolved.open("r", encoding=self.encoding, errors="ignore") as fh:
                    for idx, line in enumerate(fh, start=1):
                        haystack = line.rstrip("\n")
                        matched = compiled.search(haystack) if compiled else (normalized_query in haystack)
                        if matched:
                            matches.append(
                                {
                                    "file": self._relative_to_root(resolved),
                                    "line": idx,
                                    "content": haystack,
                                }
                            )
                            if len(matches) >= max_results:
                                return {
                                    "query": query,
                                    "matches": matches,
                                    "limit": max_results,
                                    "pattern": includePattern,
                                    "regex": isRegexp,
                                }
            except OSError:
                continue

        return {
            "query": query,
            "matches": matches,
            "limit": max_results,
            "pattern": includePattern,
            "regex": isRegexp,
        }

    def list_symbol_usages(
        self,
        symbolName: str,
        max_results: int,
        filePaths: Optional[List[str]] = None,
        include_end_line: bool = True,
    ) -> Dict[str, Any]:
        """查找指定C语言符号的入边引用。

        用法：
        - 必填 `symbolName`，大小写敏感；可选 `filePaths`（相对路径或目录数组）限制搜索范围。
        - `max_results` 控制返回的使用点数量（默认 200），`include_end_line` 决定片段是否包含结束行。
        - 返回的 `usages` 中每一项包含：触发引用的文件、起止行、依赖类型、源符号信息以及片段文本。
        - `filters` 字段回显路径过滤参数，`truncated=True` 表示结果已被数量上限截断。
        """

        symbol = (symbolName or "").strip()
        if not symbol:
            raise SWEAgentToolError("symbolName 不能为空")
        if max_results <= 0:
            raise SWEAgentToolError("max_results 必须是正整数")

        analyzer = self._get_analyzer()
        matches_path, normalized_filters = self._build_path_filter(filePaths)

        usages: List[Dict[str, Any]] = []
        truncated = False

        symbol_refs = analyzer.find_symbols_by_name(symbol )
        if not symbol_refs:
            raise SWEAgentToolError(f"未在 analyzer 产物中找到符号: {symbol}")

        file_cache: Dict[str, List[str]] = {}

        for ref in symbol_refs:
            target_key = ref.key()
            nodes, edges = analyzer.get_dependencies(ref, depth=1, direction="in")
            for edge in edges:
                if edge.target != target_key:
                    continue
                src_sym = analyzer.get_symbol_by_key(edge.source)
                if not src_sym:
                    continue
                if not matches_path(src_sym.file_path):
                    continue

                start_line = edge.start_line or edge.end_line or src_sym.start_line
                end_line = edge.end_line or edge.start_line or src_sym.end_line
                if not start_line or start_line < 1:
                    start_line = 1
                if not end_line or end_line < start_line:
                    end_line = start_line
                rel_file = src_sym.file_path
                abs_file = (self._workspace_root / Path(rel_file)).resolve()
                try:
                    if rel_file not in file_cache:
                        with abs_file.open("r", encoding=self.encoding, errors="ignore") as fh:
                            file_cache[rel_file] = fh.readlines()
                    lines = file_cache[rel_file]
                    left = max(start_line - 1, 0)
                    right = max(end_line - 1, left)
                    slice_end = right + 1 if include_end_line else left + 1
                    slice_end = min(max(slice_end, left + 1), len(lines))
                    snippet_lines = lines[left:slice_end]
                    snippet = "".join(snippet_lines).rstrip("\n")
                except OSError:
                    snippet = ""

                usages.append(
                    {
                        "file": rel_file,
                        "start_line": start_line,
                        "end_line": end_line,
                        "dependency_type": edge.dep_type,
                        "source_symbol": {
                            "name": src_sym.name,
                            "type": src_sym.type,
                            "file": src_sym.file_path,
                        },
                        "snippet": snippet,
                    }
                )

                if len(usages) >= max_results:
                    truncated = True
                    break
            if truncated:
                break

        return {
            "tool": "list_symbol_usages",
            "symbol": symbol,
            "usages": usages,
            "limit": max_results,
            "truncated": truncated,
            "filters": normalized_filters,
        }

    def list_symbol_definitions(
        self,
        symbolName: str,
        filePaths: Optional[List[str]] = None,
        include_definition_text: bool = False,
    ) -> Dict[str, Any]:
        """查询C语言符号的定义位置。

        用法：
        - 提供 `symbolName`（必填），可用 `filePaths` 数组限制返回范围。
        - 设定 `include_definition_text=True` 时，结果会携带 `definition`（及可选 `signature`）文本，适合生成参考片段。
        - 返回 `definitions` 列表，每项包含文件路径、行号区间、符号类型以及可选的定义内容。
        - `filters` 字段回显路径筛选参数，方便调用方确认范围。
        """

        symbol = (symbolName or "").strip()
        if not symbol:
            raise SWEAgentToolError("symbolName 不能为空")

        analyzer = self._get_analyzer()
        matches_path, normalized_filters = self._build_path_filter(filePaths)

        symbol_refs = analyzer.find_symbols_by_name(symbol)
        if not symbol_refs:
            raise SWEAgentToolError(f"未在 analyzer 产物中找到符号: {symbol}")

        definitions: List[Dict[str, Any]] = []
        for ref in symbol_refs:
            if not matches_path(ref.file_path):
                continue
            entry: Dict[str, Any] = {
                "file": ref.file_path,
                "start_line": ref.start_line,
                "end_line": ref.end_line,
                "type": ref.type,
            }
            if include_definition_text:
                definition = ""
                signature = ""
                file_data = analyzer.analysis_data.get(ref.file_path) or {}
                for item in file_data.get(ref.type, []) or []:
                    if item.get("name") == ref.name:
                        definition = (
                            item.get("full_definition")
                            or item.get("full_declaration")
                            or item.get("text")
                            or ""
                        )
                        signature = item.get("signature") or signature
                        break
                if not definition:
                    try:
                        definition = analyzer.extract_definition_text(ref)
                    except Exception:
                        definition = ""
                definition = definition.replace("\r\n", "\n")
                entry["definition"] = definition
                if signature:
                    entry["signature"] = signature.replace("\r\n", "\n")
            definitions.append(entry)

        return {
            "tool": "list_symbol_definitions",
            "symbol": symbol,
            "definitions": definitions,
            "filters": normalized_filters,
            "include_definition_text": include_definition_text,
        }

    def file_exists(self, path: str) -> bool:
        """判断文件或目录是否存在。"""
        target = self._resolve_path(path, allow_nonexistent=True)
        return target.exists()

    def read_file(
        self,
        path: str,
        start_line: int,
        end_line: int,
        max_bytes: int = 64_000,
    ) -> Dict[str, Any]:
        """读取文件内容，可选行范围截取。

        返回信息包含：
        - ``path``：相对工作区根目录的路径；
        - ``content``：读取到的文本内容（可能被截断）；
        - ``start_line`` / ``end_line``：必须提供当前片段在文件中的行号范围。行以1开始计数。
        """
        target = self._resolve_path(path)
        if target.is_dir():
            raise SWEAgentToolError("目标是目录，无法读取文本内容")
        if start_line is not None and start_line < 1:
            raise SWEAgentToolError("start_line 必须大于等于 1")
        if end_line is not None and end_line < 1:
            raise SWEAgentToolError("end_line 必须大于等于 1")
        try:
            with target.open("r", encoding=self.encoding, errors="ignore") as fh:
                truncated = False
                visible_text = ""
                snippet_start = start_line if start_line else 1
                if start_line is None and end_line is None:
                    raw_content = fh.read(max_bytes + 1)
                    truncated = len(raw_content) > max_bytes
                    visible_text = raw_content[:max_bytes] if truncated else raw_content
                else:
                    lines = fh.readlines()
                    total_lines = len(lines)
                    start_idx = max((start_line or 1) - 1, 0)
                    start_idx = min(start_idx, total_lines)
                    if end_line is None:
                        end_idx = total_lines
                    else:
                        end_idx = min(max(end_line, 0), total_lines)
                    if total_lines:
                        snippet_start = start_idx + 1
                    selected_lines = lines[start_idx:end_idx] if end_idx >= start_idx else []
                    joined = "".join(selected_lines)
                    truncated = len(joined) > max_bytes
                    visible_text = joined[:max_bytes] if truncated else joined

                line_count = 0
                if visible_text:
                    line_count = visible_text.count("\n")
                    if not visible_text.endswith("\n"):
                        line_count += 1
                snippet_end = snippet_start + line_count - 1 if line_count > 0 else snippet_start - 1

                content = visible_text
                if truncated:
                    content = visible_text + "\n...（内容已截断）"
        except OSError as exc:
            raise SWEAgentToolError(f"读取文件失败: {exc}") from exc
        return {
            "path": self._relative_to_root(target),
            "content": content,
            "start_line": snippet_start,
            "end_line": snippet_end,
        }

    def write_file(self, path: str, content: str, create_parents: bool = True) -> str:
        """写入文件，必要时创建父目录。"""
        target = self._resolve_path(path, allow_nonexistent=True)
        if create_parents:
            target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("w", encoding=self.encoding) as fh:
                fh.write(content)
        except OSError as exc:
            raise SWEAgentToolError(f"写入文件失败: {exc}") from exc
        return f"已写入文件: {self._relative_to_root(target)}"

    def append_file(self, path: str, content: str, create_parents: bool = True) -> str:
        """向文件追加内容。调用这个工具前必须先读取文件的末尾内容"""
        target = self._resolve_path(path, allow_nonexistent=True)
        if create_parents:
            target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("a", encoding=self.encoding) as fh:
                fh.write(content)
        except OSError as exc:
            raise SWEAgentToolError(f"追加文件失败: {exc}") from exc
        return f"已追加内容到: {self._relative_to_root(target)}"

    def search_replace(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> Dict[str, Any]:
        """在指定文件中执行字符串替换。

        要求调用方提供足够长的上下文确保 ``old_string`` 在文件内至少出现一次。
        默认仅替换唯一匹配；若设置 ``replace_all=True``，则替换文件中的全部匹配项。
        """
        if not old_string:
            raise SWEAgentToolError("old_string 不能为空")
        if old_string == new_string:
            raise SWEAgentToolError("new_string 必须与 old_string 不同")

        target = self._resolve_path(file_path)
        if target.is_dir():
            raise SWEAgentToolError("目标是目录，无法执行替换")

        try:
            content = target.read_text(encoding=self.encoding)
        except OSError as exc:
            raise SWEAgentToolError(f"读取文件失败: {exc}") from exc

        occurrences = content.count(old_string)
        if occurrences == 0:
            raise SWEAgentToolError("未找到 old_string 对应内容，请检查上下文是否精确匹配")
        if not replace_all and occurrences > 1:
            raise SWEAgentToolError(
                "old_string 在文件中出现超过一次，请提供更精确的上下文或使用 replace_all=True"
            )

        updated = (
            content.replace(old_string, new_string)
            if replace_all
            else content.replace(old_string, new_string, 1)
        )

        try:
            target.write_text(updated, encoding=self.encoding)
        except OSError as exc:
            raise SWEAgentToolError(f"写入文件失败: {exc}") from exc

        return {
            "tool": "search_replace",
            "path": self._relative_to_root(target),
            "replacements": occurrences if replace_all else 1,
        }


    def run_command(self, command: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """在仓库根目录下执行命令。"""
        if not command or not command.strip():
            raise SWEAgentToolError("命令不能为空")
        effective_timeout = timeout or self.command_timeout
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self._workspace_root,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise SWEAgentToolError(f"命令执行超时（>{effective_timeout}s）") from exc
        stdout, trunc_out = self._clip_output(result.stdout)
        stderr, trunc_err = self._clip_output(result.stderr)
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "timeout": effective_timeout,
            "truncated": trunc_out or trunc_err,
        }

    def run_tests(self, command: str = "pytest -q", timeout: Optional[int] = None) -> Dict[str, Any]:
        """执行测试命令，默认使用pytest。"""
        return self.run_command(command, timeout=timeout)

    def _strip_md_fences(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            first_nl = stripped.find("\n")
            last_fence = stripped.rfind("\n```")
            if first_nl != -1 and last_fence != -1 and last_fence > first_nl:
                return stripped[first_nl + 1:last_fence]
        return text

    def _split_placeholder_segments(self, text: str) -> Optional[Tuple[List[str], List[str]]]:
        lines = text.splitlines(keepends=True)
        segments: List[str] = []
        tokens: List[str] = []
        buffer: List[str] = []
        for line in lines:
            if self.PLACEHOLDER_LINE_RE.match(line.strip("\r\n")):
                segments.append("".join(buffer))
                tokens.append(line)
                buffer = []
            else:
                buffer.append(line)
        segments.append("".join(buffer))
        return (segments, tokens) if tokens else None

    def _locate_anchor(self, haystack: str, needle: str, start: int) -> int:
        if not needle:
            return -1
        direct = haystack.find(needle, start)
        if direct != -1:
            return direct
        for line in needle.splitlines():
            piece = line.strip()
            if not piece:
                continue
            idx = haystack.find(piece, start)
            if idx != -1:
                return idx
        return -1


    def edit_file(self, target_file: str, instructions: str, code_edit: str) -> Dict[str, Any]:
        """用于创建或更新单个文件（请务必将 `target_file` 作为首个参数传入）。
            - `instructions` 必须由第一人称一句话组成，用来明确你打算进行的修改，如“我将更新处理函数以记录错误”。保持简短有助于下游模型正确理解意图。
            - 在 `code_edit` 中提供完整编辑内容，支持两种写法：

            1. **完整重写**：提供目标文件的全部内容。文件会被按给出的文本直接创建或覆盖。
            2. **片段编辑**：尽量减少未修改文本，并使用 `// ... existing code ...` 或 `# ... existing code ...` 之类的占位行划分片段。每个占位符表示原文件中未改动的部分应原样保留。请提供足够的上下文以便唯一定位每段修改，若无法匹配将抛出错误并提示补充上下文。

            - 不要在未加占位符的情况下省略原有代码，否则下游应用器会将缺失部分视作删除。
            - 修改同一文件应集中在一次 `edit_file` 调用中；如需编辑多个文件，请并行发起多次调用，每次对应一个文件。
            - `target_file` 建议使用工作区内的相对路径，也支持绝对路径（会保持原值）。
            例如： 只修改文件中的main函数片段
#include <stdio.h>
int main() {
// ... existing code ...
    printf("Hi!\\n");
    return 0;
// ... existing code ...
}
int func(){}
"""
        if not code_edit or not code_edit.strip():
            raise SWEAgentToolError("code_edit 不能为空")

        cleaned = self._strip_md_fences(code_edit)

        placeholder_data = self._split_placeholder_segments(cleaned)
        target_path = self._resolve_path(target_file, allow_nonexistent=True)
        relative = self._relative_to_root(target_path)

        if placeholder_data:
            segments, placeholders = placeholder_data
            if not target_path.exists():
                raise SWEAgentToolError("目标文件不存在，无法根据占位符合并片段")
            try:
                original = target_path.read_text(encoding=self.encoding)
            except OSError as exc:
                raise SWEAgentToolError(f"读取原文件失败: {exc}") from exc

            merged_parts: List[str] = []
            position = 0
            total_segments = len(segments)

            for idx, segment in enumerate(segments):
                if segment:
                    merged_parts.append(segment)
                    anchor = self._locate_anchor(original, segment, position)
                    if anchor != -1:
                        position = anchor + len(segment)

                if idx < len(placeholders):
                    next_segment = segments[idx + 1] if idx + 1 < total_segments else ""
                    if next_segment:
                        anchor = self._locate_anchor(original, next_segment, position)
                        if anchor == -1:
                            raise SWEAgentToolError(
                                "无法定位占位符上下文，请提供更多上下文。"
                            )
                        merged_parts.append(original[position:anchor])
                        position = anchor
                    else:
                        merged_parts.append(original[position:])
                        position = len(original)

            final_content = "".join(merged_parts)
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(final_content, encoding=self.encoding)
            except OSError as exc:
                raise SWEAgentToolError(f"写入文件失败: {exc}") from exc

            return {
                "tool": "edit_file",
                "mode": "merge",
                "instructions": instructions,
                "target_file": relative,
                "bytes": len(final_content.encode(self.encoding)),
            }

        message = self.write_file(relative, cleaned, create_parents=True)
        return {
            "tool": "edit_file",
            "mode": "write",
            "instructions": instructions,
            "target_file": relative,
            "message": message,
            "bytes": len(cleaned.encode(self.encoding)),
        }

    # TODO: fix bug
    def apply_patch(self, patch: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """应用统一补丁格式（unified diff）。
        补丁要求：
        - 必须是 unified diff；每个文件块需包含 `--- a/<path>` 与 `+++ b/<path>` 行。
        - 每个补丁块以 `@@ -<start>,<count> +<start>,<count> @@` 形式开头：`start` 为上下文在原/新文件中的首行行号，`count` 为该块包含的行数（当值为 1 时可省略 `,<count>`）。
        - 未改动的上下文行必须以前缀空格保留，新增行以 `+` 开头，删除行以 `-` 开头；至少保留一行上下文。
        - 补丁文件末尾需要换行符，以避免部分解析器报 `corrupt patch`。
        - 未改动的相邻上下文必须保持原始一致，包括所有的字符和缩进
        - 如果补应用失败，请检查补丁内容是否正确，修改补丁内容后重试。
        - 示例：
```
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -10,7 +10,7 @@ def some_function():
 existing_context()
-    old_call()
+    new_call()
 existing_context()
```
        """
        if not patch or not patch.strip():
            raise SWEAgentToolError("补丁内容不能为空")

        normalized_patch, normalized_changed = self._normalize_patch(patch)
        patch_content = normalized_patch
        if not patch_content.endswith("\n"):
            patch_content += "\n"

        effective_timeout = timeout or self.command_timeout
        ignore_whitespace = False
        command_str = ""
        process: Optional[subprocess.CompletedProcess[str]] = None
        attempts: List[Tuple[List[str], subprocess.CompletedProcess[str]]] = []
        tmp_path: Optional[Path] = None

        with tempfile.NamedTemporaryFile(
            "w",
            encoding=self.encoding,
            suffix=".patch",
            delete=False,
            dir=self._workspace_root,
        ) as tmp_file:
            tmp_file.write(patch_content)
            tmp_path = Path(tmp_file.name)

        try:
            assert tmp_path is not None  # for type checkers; runtime应已赋值

            for ignore in (False, True):
                args = ["git", "apply", "--verbose"]
                if ignore:
                    args.append("--ignore-whitespace")
                args.append(str(tmp_path))
                command_str = " ".join(shlex.quote(part) for part in args)
                try:
                    proc = subprocess.run(
                        args,
                        cwd=self._workspace_root,
                        capture_output=True,
                        text=True,
                        timeout=effective_timeout,
                    )
                except subprocess.TimeoutExpired as exc:
                    raise SWEAgentToolError(f"应用补丁超时（>{effective_timeout}s）") from exc

                if proc.returncode == 0:
                    ignore_whitespace = ignore
                    process = proc
                    break

                attempts.append((args, proc))

            if process is None:
                # 将最后一次尝试的输出纳入错误信息
                if attempts:
                    _, last_proc = attempts[-1]
                    stdout, _ = self._clip_output(last_proc.stdout)
                    stderr, _ = self._clip_output(last_proc.stderr)
                    last_command = " ".join(shlex.quote(part) for part in attempts[-1][0])
                    message = (
                        f"应用补丁失败：命令 {last_command} 退出码 {last_proc.returncode}\n"
                        f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                    )
                else:
                    message = "应用补丁失败：未知错误"
                raise SWEAgentToolError(message)

            stdout, trunc_out = self._clip_output(process.stdout)
            stderr, trunc_err = self._clip_output(process.stderr)

            return {
                "command": command_str,
                "returncode": process.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "timeout": effective_timeout,
                "truncated": trunc_out or trunc_err,
                "ignore_whitespace": ignore_whitespace,
                "recalculated_hunks": normalized_changed,
            }
        finally:
            if tmp_path is not None:
                try:
                    tmp_path.unlink()
                except OSError:
                    pass


@dataclass
class _LspSession:
    process: subprocess.Popen
    client: pylspclient.LspClient
    endpoint: pylspclient.LspEndpoint
    language: str
    language_id: LanguageIdentifier
    opened_documents: Dict[Path, int] = field(default_factory=dict)
    document_mtimes: Dict[Path, int] = field(default_factory=dict)
    diagnostics: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    diagnostic_events: Dict[str, threading.Event] = field(default_factory=dict)
    diagnostics_lock: threading.Lock = field(default_factory=threading.Lock)

    def is_alive(self) -> bool:
        return self.process.poll() is None


@dataclass
class _SymbolLocation:
    session: _LspSession
    language: str
    location: Location
    name: str
    kind: Optional[SymbolKind]
    container: Optional[str]
    abs_path: Path
    rel_path: str


class SWELspTools:
    """基于 LSP 的跨语言符号查询工具集。"""

    _PYTHON_EXECUTABLE: str = sys.executable or "python3"

    DEFAULT_LANGUAGE_SERVERS: Dict[str, Sequence[Sequence[str]]] = {
        "python": (
            ("pylsp",),
            (_PYTHON_EXECUTABLE, "-m", "pylsp"),
        ),
        "c": (("clangd", "--background-index"),),
        "rust": (("rust-analyzer",),),
    }

    DEFAULT_CLIENT_CAPABILITIES: Dict[str, Any] = {
        "textDocument": {
            "definition": {"dynamicRegistration": False},
            "references": {"dynamicRegistration": False},
            "documentSymbol": {"dynamicRegistration": False},
        },
        "workspace": {
            "symbol": {"dynamicRegistration": False},
        },
    }

    DIAGNOSTIC_SEVERITY_MAP: Dict[int, str] = {
        1: "Error",
        2: "Warning",
        3: "Information",
        4: "Hint",
    }
    SEVERITY_VALUE_BY_NAME: Dict[str, int] = {name.lower(): value for value, name in DIAGNOSTIC_SEVERITY_MAP.items()}
    SEVERITY_ALIAS_MAP: Dict[str, int] = {
        "err": 1,
        "errors": 1,
        "warn": 2,
        "warnings": 2,
        "info": 3,
        "infos": 3,
        "informational": 3,
        "hint": 4,
        "hints": 4,
    }

    EXTENSION_LANGUAGE_MAP: Dict[str, str] = {
        ".py": "python",
        ".pyi": "python",
        ".c": "c",
        ".h": "c",
        ".hpp": "c",
        ".hh": "c",
        ".rs": "rust",
    }

    LANGUAGE_IDENTIFIERS: Dict[str, LanguageIdentifier] = {
        "python": LanguageIdentifier.PYTHON,
        "c": LanguageIdentifier.C,
        "rust": LanguageIdentifier.RUST,
    }

    LANGUAGE_FILE_PATTERNS: Dict[str, Tuple[str, ...]] = {
        "python": ("*.py", "*.pyi"),
        "c": ("*.c", "*.h", "*.hpp", "*.hh"),
        "rust": ("*.rs",),
    }

    MAX_SYMBOL_CANDIDATES: int = 64
    MAX_FALLBACK_FILES_PER_LANGUAGE: int = 200

    def __init__(
        self,
        workspace_root: str | Path,
        *,
        encoding: str = "utf-8",
        command_timeout: int = 10,
    language_servers: Optional[Dict[str, Union[str, Sequence[str], Sequence[Sequence[str]]]]] = None,
        language_capabilities: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).expanduser().resolve()
        if not self.workspace_root.exists() or not self.workspace_root.is_dir():
            raise ValueError(f"工作目录不存在或不是文件夹: {workspace_root}")

        self.encoding = encoding
        self.command_timeout = command_timeout

        self.language_servers = self._normalize_language_servers(language_servers)
        self.language_capabilities = language_capabilities or {}

        self._sessions: Dict[str, _LspSession] = {}
        self._sessions_lock = threading.RLock()
        self._symbol_presence_cache: Dict[Tuple[str, str], bool] = {}
        self._language_sources_cache: Dict[str, bool] = {}
        self._compile_commands_dir: Optional[Path] = None
        self._file_cache_lock = threading.RLock()
        self._document_cache: Dict[Path, Tuple[int, str]] = {}
        self._file_lines_cache: Dict[Path, Tuple[int, Tuple[str, ...]]] = {}

        atexit.register(self.close)

    # ------------------------------------------------------------------
    # 初始化与清理
    # ------------------------------------------------------------------
    def _normalize_language_servers(
        self,
        overrides: Optional[Dict[str, Union[str, Sequence[str], Sequence[Sequence[str]]]]],
    ) -> Dict[str, List[List[str]]]:
        normalized: Dict[str, List[List[str]]] = {}
        merged: Dict[str, Union[str, Sequence[str], Sequence[Sequence[str]]]] = dict(self.DEFAULT_LANGUAGE_SERVERS)
        if overrides:
            for lang, cmd in overrides.items():
                merged[lang.lower()] = cmd

        def add_candidate(container: List[List[str]], candidate: Union[str, Sequence[str]]) -> None:
            if isinstance(candidate, str):
                parts = shlex.split(candidate)
            else:
                parts = [str(part) for part in candidate]
            if parts:
                container.append(parts)

        for language, command in merged.items():
            candidates: List[List[str]] = []
            if isinstance(command, str):
                add_candidate(candidates, command)
            elif isinstance(command, Sequence):
                if command and isinstance(command[0], Sequence) and not isinstance(command[0], (str, bytes)):
                    for nested in command:  # type: ignore[assignment]
                        add_candidate(candidates, nested)  # type: ignore[arg-type]
                else:
                    add_candidate(candidates, command)
            else:
                raise TypeError(f"不支持的语言服务器配置: {command!r}")

            if not candidates:
                raise SWEAgentToolError(f"语言 {language} 未配置可用的语言服务器命令")
            normalized[language] = candidates
        return normalized

    def close(self) -> None:
        with self._sessions_lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()

        for session in sessions:
            with suppress(Exception):
                self._shutdown_session(session)

    # ------------------------------------------------------------------
    # 路径与缓存处理
    # ------------------------------------------------------------------
    def _is_within_root(self, path: Path) -> bool:
        try:
            path.relative_to(self.workspace_root)
            return True
        except ValueError:
            return False

    def _relative_to_root(self, path: Path) -> str:
        return path.relative_to(self.workspace_root).as_posix()

    def _resolve_path(self, path: str | os.PathLike[str]) -> Path:
        candidate = (self.workspace_root / Path(path)).expanduser()
        resolved = candidate.resolve(strict=False)
        if not self._is_within_root(resolved):
            raise SWEAgentToolError("路径越界：禁止访问工作目录之外的文件")
        return resolved

    def _expand_file_paths(self, raw_paths: Sequence[str]) -> Tuple[List[Path], List[str]]:
        resolved_paths: List[Path] = []
        warnings: List[str] = []
        seen: Set[Path] = set()

        for raw_path in raw_paths:
            if not raw_path:
                warnings.append("空路径已忽略")
                continue

            has_glob = any(token in raw_path for token in "*?[")
            if has_glob:
                pattern_path = Path(raw_path)
                if pattern_path.is_absolute():
                    try:
                        rel_pattern = pattern_path.relative_to(self.workspace_root).as_posix()
                    except ValueError:
                        warnings.append(f"{raw_path}: 路径越界，已忽略")
                        continue
                    pattern = rel_pattern
                else:
                    pattern = raw_path

                matches = sorted(self.workspace_root.glob(pattern))
                matched_files = [match for match in matches if match.is_file()]
                if not matched_files:
                    warnings.append(f"{raw_path}: 未匹配到任何文件")
                    continue

                for match in matched_files:
                    try:
                        resolved = match.resolve(strict=False)
                    except OSError:
                        warnings.append(f"{raw_path}: 无法解析匹配路径 {match}")
                        continue
                    if not self._is_within_root(resolved):
                        warnings.append(f"{raw_path}: 匹配路径越界 {match}")
                        continue
                    if resolved in seen:
                        continue
                    seen.add(resolved)
                    resolved_paths.append(resolved)
                continue

            try:
                resolved = self._resolve_path(raw_path)
            except SWEAgentToolError as exc:
                warnings.append(str(exc))
                continue

            if resolved.is_dir():
                warnings.append(f"{self._relative_to_root(resolved)}: 当前仅支持文件路径")
                continue

            if resolved in seen:
                continue

            seen.add(resolved)
            resolved_paths.append(resolved)

        return resolved_paths, warnings

    def _build_path_filter(
        self,
        file_paths: Optional[List[str]],
    ) -> Tuple[Callable[[str], bool], List[str]]:
        if not file_paths:
            return (lambda _rel: True), []

        filters: List[Tuple[Path, bool]] = []
        normalized: List[str] = []
        for raw_path in file_paths:
            resolved = self._resolve_path(raw_path)
            filters.append((resolved, resolved.is_dir()))
            normalized.append(self._relative_to_root(resolved))

        def matcher(rel_path: str) -> bool:
            abs_path = (self.workspace_root / Path(rel_path)).resolve()
            for base, is_dir in filters:
                if is_dir:
                    try:
                        abs_path.relative_to(base)
                        return True
                    except ValueError:
                        continue
                if abs_path == base:
                    return True
            return False

        return matcher, normalized

    def _detect_language_for_path(self, path: Path) -> Optional[str]:
        return self.EXTENSION_LANGUAGE_MAP.get(path.suffix.lower())

    def _iter_language_files(self, language: str) -> Iterable[Path]:
        patterns = self.LANGUAGE_FILE_PATTERNS.get(language.lower(), ())
        seen: Set[Path] = set()
        for pattern in patterns:
            for candidate in self.workspace_root.rglob(pattern):
                if not candidate.is_file():
                    continue
                try:
                    resolved = candidate.resolve(strict=False)
                except OSError:
                    continue
                if resolved in seen:
                    continue
                if not self._is_within_root(resolved):
                    continue
                seen.add(resolved)
                yield resolved

    def _language_has_sources(self, language: str) -> bool:
        cached = self._language_sources_cache.get(language)
        if cached is not None:
            return cached

        has_sources = False
        for _ in self._iter_language_files(language):
            has_sources = True
            break

        if language == "rust" and has_sources:
            has_cargo = any(
                file_path.name in {"Cargo.toml", "rust-project.json"}
                for file_path in self.workspace_root.rglob("Cargo.toml")
            ) or any(
                file_path.name == "rust-project.json"
                for file_path in self.workspace_root.rglob("rust-project.json")
            )
            has_sources = has_sources and has_cargo

        self._language_sources_cache[language] = has_sources
        return has_sources

    def _language_has_symbol(self, language: str, symbol: str) -> bool:
        cache_key = (language, symbol)
        cached = self._symbol_presence_cache.get(cache_key)
        if cached is not None:
            return cached

        found = False
        scanned = 0
        for path in self._iter_language_files(language):
            if scanned >= self.MAX_FALLBACK_FILES_PER_LANGUAGE:
                break
            scanned += 1
            try:
                text = self._get_document_text(path)
            except SWEAgentToolError:
                continue
            if symbol in text:
                found = True
                break

        self._symbol_presence_cache[cache_key] = found
        return found

    def _detect_languages_for_symbol(
        self,
        symbol: str,
        normalized_filters: List[str],
    ) -> List[str]:
        candidate_languages: Set[str] = set()

        for rel in normalized_filters:
            try:
                resolved = (self.workspace_root / Path(rel)).resolve()
            except Exception:
                continue
            if resolved.is_file():
                language = self.EXTENSION_LANGUAGE_MAP.get(resolved.suffix.lower())
                if language:
                    candidate_languages.add(language)
            elif resolved.is_dir():
                for child in resolved.rglob("*"):
                    if not child.is_file():
                        continue
                    language = self.EXTENSION_LANGUAGE_MAP.get(child.suffix.lower())
                    if language:
                        candidate_languages.add(language)
                        break

        if candidate_languages:
            return [language for language in self.language_servers if language in candidate_languages]

        languages_with_symbol: List[str] = []
        for language in self.language_servers:
            if not self._language_has_sources(language):
                continue
            if self._language_has_symbol(language, symbol):
                languages_with_symbol.append(language)

        if languages_with_symbol:
            return languages_with_symbol

        fallback_languages = [language for language in self.language_servers if self._language_has_sources(language)]
        if fallback_languages:
            return fallback_languages

        return list(self.language_servers.keys())

    @staticmethod
    def _is_method_not_found_error(message: str) -> bool:
        lowered = message.lower()
        return "method not found" in lowered or "-32601" in lowered

    def _uri_to_path(self, uri: str) -> Path:
        parsed = urlparse(uri)
        if parsed.scheme != "file":
            raise ValueError(f"Unsupported URI scheme: {uri}")
        path = Path(unquote(parsed.path)).resolve()
        return path

    def _get_document_state(self, path: Path) -> Tuple[str, int]:
        try:
            initial_stat = path.stat()
        except OSError as exc:
            raise SWEAgentToolError(f"读取文件失败: {exc}") from exc

        initial_mtime_ns = getattr(initial_stat, "st_mtime_ns", int(initial_stat.st_mtime * 1_000_000_000))

        with self._file_cache_lock:
            cached = self._document_cache.get(path)
            if cached is not None and cached[0] == initial_mtime_ns:
                return cached[1], initial_mtime_ns

        try:
            text = path.read_text(encoding=self.encoding)
        except OSError as exc:
            raise SWEAgentToolError(f"读取文件失败: {exc}") from exc

        try:
            final_stat = path.stat()
            final_mtime_ns = getattr(final_stat, "st_mtime_ns", int(final_stat.st_mtime * 1_000_000_000))
        except OSError:
            final_mtime_ns = initial_mtime_ns

        if final_mtime_ns != initial_mtime_ns:
            with self._file_cache_lock:
                cached = self._document_cache.get(path)
                if cached is not None and cached[0] == final_mtime_ns:
                    return cached[1], final_mtime_ns

        with self._file_cache_lock:
            self._document_cache[path] = (final_mtime_ns, text)
            self._file_lines_cache.pop(path, None)

        return text, final_mtime_ns

    def _get_document_text(self, path: Path) -> str:
        text, _mtime_ns = self._get_document_state(path)
        return text

    def _get_file_lines(self, path: Path) -> List[str]:
        text, mtime_ns = self._get_document_state(path)

        with self._file_cache_lock:
            cached = self._file_lines_cache.get(path)
            if cached is not None and cached[0] == mtime_ns:
                return list(cached[1])

        lines_tuple = tuple(text.splitlines(keepends=True))
        with self._file_cache_lock:
            self._file_lines_cache[path] = (mtime_ns, lines_tuple)

        return list(lines_tuple)

    def _extract_snippet(
        self,
        path: Path,
        start_line_zero: int,
        end_line_zero: int,
        include_end_line: bool,
    ) -> str:
        lines = self._get_file_lines(path)
        start_idx = max(start_line_zero, 0)
        end_idx = max(end_line_zero, start_idx)
        slice_end = end_idx + 1 if include_end_line else start_idx + 1
        slice_end = min(slice_end, len(lines))
        snippet_lines = lines[start_idx:slice_end]
        return "".join(snippet_lines).rstrip("\n")

    # ------------------------------------------------------------------
    # 会话管理
    # ------------------------------------------------------------------
    def _ensure_session(self, language: str) -> _LspSession:
        language = language.lower()
        if language not in self.language_servers:
            raise SWEAgentToolError(f"未配置语言服务器: {language}")

        language_id = self.LANGUAGE_IDENTIFIERS.get(language)
        if language_id is None:
            raise SWEAgentToolError(f"暂不支持该语言: {language}")

        with self._sessions_lock:
            session = self._sessions.get(language)
            if session and session.is_alive():
                return session

            if session:
                self._shutdown_session(session)

            candidates = self.language_servers[language]

            compile_commands_dir: Optional[Path] = None
            if language == "c":
                compile_commands_dir = self._get_compile_commands_dir()

            errors: List[str] = []

            for candidate in candidates:
                command = list(candidate)
                if not command:
                    continue

                if language == "c" and compile_commands_dir is not None:
                    self._ensure_compile_commands_flag(command, compile_commands_dir)

                resolved_exec = shutil.which(command[0]) or command[0]
                if shutil.which(resolved_exec) is None and not Path(resolved_exec).exists():
                    errors.append(f"{language}: 找不到语言服务器可执行文件 {command[0]}")
                    continue
                command[0] = resolved_exec

                try:
                    process = subprocess.Popen(
                        command,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=self.workspace_root,
                    )
                except FileNotFoundError as exc:
                    errors.append(f"{language}: 启动语言服务器失败 {command[0]} ({exc})")
                    continue

                if process.stdin is None or process.stdout is None:
                    process.terminate()
                    errors.append(f"{language}: 语言服务器启动失败：无法连接标准输入输出")
                    continue

                json_rpc = pylspclient.JsonRpcEndpoint(process.stdin, process.stdout)
                endpoint = pylspclient.LspEndpoint(
                    json_rpc,
                    timeout=self.command_timeout,
                    notify_callbacks={},
                )
                client = pylspclient.LspClient(endpoint)

                session_candidate = _LspSession(
                    process=process,
                    client=client,
                    endpoint=endpoint,
                    language=language,
                    language_id=language_id,
                )
                endpoint.notify_callbacks["textDocument/publishDiagnostics"] = (
                    lambda params, session=session_candidate: self._handle_publish_diagnostics(session, params)
                )

                capabilities = self.language_capabilities.get(language) or self.DEFAULT_CLIENT_CAPABILITIES
                try:
                    client.initialize(
                        processId=os.getpid(),
                        rootPath=None,
                        rootUri=self.workspace_root.as_uri(),
                        initializationOptions=None,
                        capabilities=capabilities,
                        trace="off",
                        workspaceFolders=None,
                    )
                    client.initialized()
                except Exception as exc:
                    errors.append(
                        f"{language}: 初始化语言服务器失败 ({' '.join(command)}) - {exc}"
                    )
                    with suppress(Exception):
                        endpoint.stop()
                    process.terminate()
                    with suppress(Exception):
                        process.wait(timeout=3)
                    continue

                session = session_candidate
                self._sessions[language] = session
                return session

            if errors:
                raise SWEAgentToolError("; ".join(errors))
            raise SWEAgentToolError(f"未能启动语言 {language} 的语言服务器")

    def _shutdown_session(self, session: _LspSession) -> None:
        with suppress(Exception):
            session.endpoint.stop()
        if session.endpoint.is_alive():
            with suppress(Exception):
                session.endpoint.join(timeout=1)
        with suppress(Exception):
            session.client.shutdown()
        with suppress(Exception):
            session.client.exit()
        if session.process.poll() is None:
            session.process.terminate()
            with suppress(Exception):
                session.process.wait(timeout=3)
            if session.process.poll() is None:
                with suppress(Exception):
                    session.process.kill()

    def _handle_publish_diagnostics(self, session: _LspSession, params: Optional[dict]) -> None:
        if not params:
            return

        uri = params.get("uri") or params.get("textDocument", {}).get("uri")
        if not uri:
            return

        diagnostics_payload = params.get("diagnostics") or []

        with session.diagnostics_lock:
            session.diagnostics[uri] = diagnostics_payload
            event = session.diagnostic_events.get(uri)
            if event is None:
                event = threading.Event()
                session.diagnostic_events[uri] = event
            event.set()

    def _ensure_compile_commands(self) -> Optional[Path]:
        compile_commands = self.workspace_root / "compile_commands.json"
        if compile_commands.exists():
            return compile_commands

        entries: List[Dict[str, Any]] = []
        for c_file in self.workspace_root.rglob("*.c"):
            rel = c_file.relative_to(self.workspace_root)
            entries.append(
                {
                    "directory": str(self.workspace_root),
                    "command": f"clang -std=c11 -I{self.workspace_root} -c {rel.as_posix()}",
                    "file": str((self.workspace_root / rel).resolve()),
                }
            )

        if not entries:
            return None

        compile_commands.write_text(json.dumps(entries, indent=2))
        return compile_commands

    def _get_compile_commands_dir(self) -> Path:
        if self._compile_commands_dir and (self._compile_commands_dir / "compile_commands.json").is_file():
            return self._compile_commands_dir

        root_candidate = self.workspace_root / "compile_commands.json"
        if root_candidate.is_file():
            self._compile_commands_dir = root_candidate.parent
            return self._compile_commands_dir

        candidates = [candidate for candidate in self.workspace_root.rglob("compile_commands.json") if candidate.is_file()]
        if not candidates:
            raise SWEAgentToolError("未在工作区找到 compile_commands.json")

        def candidate_key(path: Path) -> Tuple[int, str]:
            try:
                rel = path.relative_to(self.workspace_root)
                depth = len(rel.parents)
            except ValueError:
                depth = len(path.parents)
            return (depth, str(path))

        target = min(candidates, key=candidate_key)
        self._compile_commands_dir = target.parent
        return self._compile_commands_dir

    @staticmethod
    def _ensure_compile_commands_flag(command: List[str], directory: Path) -> None:
        flag = "--compile-commands-dir"
        directory_str = str(directory)

        for index, part in enumerate(command):
            if part == flag:
                if index + 1 < len(command):
                    command[index + 1] = directory_str
                else:
                    command.append(directory_str)
                return
            if part.startswith(f"{flag}="):
                command[index] = f"{flag}={directory_str}"
                return

        command.extend([flag, directory_str])

    # ------------------------------------------------------------------
    # 文档管理
    # ------------------------------------------------------------------
    def _close_document(self, session: _LspSession, path: Path, uri: str) -> None:
        if path not in session.opened_documents:
            return

        with suppress(Exception):
            session.client.didClose(TextDocumentIdentifier(uri=uri))

        session.opened_documents.pop(path, None)
        session.document_mtimes.pop(path, None)
        with session.diagnostics_lock:
            session.diagnostics.pop(uri, None)
            event = session.diagnostic_events.get(uri)
            if event is not None:
                event.clear()

    def _ensure_document_open(self, session: _LspSession, path: Path, *, uri: Optional[str] = None) -> str:
        text, mtime_ns = self._get_document_state(path)
        document_uri = uri or path.as_uri()

        existing_version = session.opened_documents.get(path)
        previous_mtime = session.document_mtimes.get(path)
        needs_reopen = existing_version is None or previous_mtime != mtime_ns
        base_version = existing_version or 0

        if needs_reopen and existing_version is not None:
            self._close_document(session, path, document_uri)

        if not needs_reopen and existing_version is not None:
            with session.diagnostics_lock:
                session.diagnostic_events.setdefault(document_uri, threading.Event())
            return text

        with session.diagnostics_lock:
            session.diagnostics.pop(document_uri, None)
            event = session.diagnostic_events.get(document_uri)
            if event is None:
                session.diagnostic_events[document_uri] = threading.Event()
            else:
                event.clear()

        version = base_version + 1
        session.client.didOpen(
            TextDocumentItem(
                uri=document_uri,
                languageId=session.language_id,
                version=version,
                text=text,
            )
        )
        session.opened_documents[path] = version
        session.document_mtimes[path] = mtime_ns
        return text

    def _wait_for_diagnostics(
        self,
        session: _LspSession,
        uri: str,
        *,
        timeout: float = 2.0,
    ) -> List[Dict[str, Any]]:
        deadline = time.monotonic() + timeout

        with session.diagnostics_lock:
            event = session.diagnostic_events.get(uri)
            if event is None:
                event = threading.Event()
                session.diagnostic_events[uri] = event
            else:
                event.clear()

            diagnostics = session.diagnostics.get(uri)
            if diagnostics is not None:
                return diagnostics

        remaining = max(deadline - time.monotonic(), 0.0)
        if remaining > 0:
            event.wait(timeout=remaining)

        with session.diagnostics_lock:
            return session.diagnostics.get(uri, [])

    def _normalize_min_severity(self, min_severity: Optional[Any]) -> Optional[int]:
        if min_severity is None:
            return None

        value: Optional[int]
        if isinstance(min_severity, int):
            value = min_severity
        else:
            normalized = str(min_severity).strip().lower()
            if not normalized:
                return None
            if normalized.isdigit():
                value = int(normalized)
            else:
                value = self.SEVERITY_VALUE_BY_NAME.get(normalized)
                if value is None:
                    value = self.SEVERITY_ALIAS_MAP.get(normalized)

        if value in self.DIAGNOSTIC_SEVERITY_MAP:
            return value

        raise SWEAgentToolError(
            "min_severity 无效，支持: error, warning, information, hint 或 1-4"
        )

    # ------------------------------------------------------------------
    # 符号查询
    # ------------------------------------------------------------------
    def _workspace_symbol_query(self, session: _LspSession, symbol: str) -> List[SymbolInformation]:
        try:
            raw_result = session.client.lsp_endpoint.call_method("workspace/symbol", query=symbol)
        except Exception as exc:
            raise SWEAgentToolError(f"workspace/symbol 调用失败: {exc}") from exc

        if not raw_result:
            return []

        infos: List[SymbolInformation] = []
        for item in raw_result[: self.MAX_SYMBOL_CANDIDATES]:
            try:
                info = SymbolInformation.model_validate(item)
            except ValidationError:
                continue
            infos.append(info)
        return infos

    def _extract_symbol_infos_from_document(
        self,
        items: Sequence[Union[DocumentSymbol, SymbolInformation]],
        uri: str,
        symbol: str,
    ) -> List[SymbolInformation]:
        results: List[SymbolInformation] = []

        if not items:
            return results

        def normalize_kind(value: Any) -> SymbolKind:
            if isinstance(value, SymbolKind):
                return value
            try:
                return SymbolKind(int(value))
            except Exception:
                return SymbolKind.Function

        def handle_document_symbol(node: DocumentSymbol, container: Optional[str]) -> None:
            if node.name == symbol:
                results.append(
                    SymbolInformation(
                        name=node.name,
                        kind=normalize_kind(node.kind),
                        deprecated=node.deprecated,
                        location=Location(uri=uri, range=node.range),
                        containerName=container,
                    )
                )
            for child in node.children or []:
                handle_document_symbol(child, node.name)

        first = items[0]
        if isinstance(first, DocumentSymbol):
            for node in items:  # type: ignore[assignment]
                if isinstance(node, DocumentSymbol):
                    handle_document_symbol(node, None)
        else:
            for item in items:
                if isinstance(item, SymbolInformation) and item.name == symbol:
                    results.append(item)
        return results[: self.MAX_SYMBOL_CANDIDATES]

    def _fallback_symbol_query_document_symbols(
        self,
        session: _LspSession,
        symbol: str,
        matches_path: Callable[[str], bool],
    ) -> List[SymbolInformation]:
        patterns = self.LANGUAGE_FILE_PATTERNS.get(session.language, ())
        if not patterns:
            raise SWEAgentToolError("该语言不支持 fallback 文档扫描")

        results: List[SymbolInformation] = []
        seen_locations: Set[Tuple[str, int, int, int, int]] = set()
        scanned_files = 0

        for path in self._iter_language_files(session.language):
            rel_path = self._relative_to_root(path)
            if not matches_path(rel_path):
                continue
            try:
                text = self._get_document_text(path)
            except SWEAgentToolError:
                continue
            if symbol not in text:
                continue

            scanned_files += 1
            if scanned_files > self.MAX_FALLBACK_FILES_PER_LANGUAGE:
                break

            uri = path.as_uri()
            try:
                self._ensure_document_open(session, path, uri=uri)
                symbols = session.client.documentSymbol(TextDocumentIdentifier(uri=uri))
            except Exception:
                continue

            if not symbols:
                continue

            infos = self._extract_symbol_infos_from_document(symbols, uri, symbol)
            for info in infos:
                location = info.location
                loc_key = (
                    location.uri,
                    location.range.start.line,
                    location.range.start.character,
                    location.range.end.line,
                    location.range.end.character,
                )
                if loc_key in seen_locations:
                    continue
                seen_locations.add(loc_key)
                results.append(info)
                if len(results) >= self.MAX_SYMBOL_CANDIDATES:
                    return results

        return results

    def _collect_symbol_locations(
        self,
        symbol: str,
        matches_path: Callable[[str], bool],
        candidate_languages: Sequence[str],
    ) -> Tuple[List[_SymbolLocation], List[str]]:
        locations: List[_SymbolLocation] = []
        errors: List[str] = []

        if not candidate_languages:
            return locations, ["未检测到可用语言服务器"]

        for language in candidate_languages:
            try:
                session = self._ensure_session(language)
            except Exception as exc:
                errors.append(f"{language}: {exc}")
                continue

            used_fallback = False
            try:
                symbol_infos = self._workspace_symbol_query(session, symbol)
            except SWEAgentToolError as exc:
                message = str(exc)
                if self._is_method_not_found_error(message):
                    try:
                        symbol_infos = self._fallback_symbol_query_document_symbols(session, symbol, matches_path)
                        used_fallback = True
                    except SWEAgentToolError as fb_exc:
                        errors.append(f"{language}: {fb_exc}")
                        continue
                else:
                    errors.append(f"{language}: {exc}")
                    continue

            if not symbol_infos and not used_fallback:
                try:
                    symbol_infos = self._fallback_symbol_query_document_symbols(session, symbol, matches_path)
                except SWEAgentToolError as fb_exc:
                    errors.append(f"{language}: {fb_exc}")
                    symbol_infos = []

            for info in symbol_infos:
                if info.name != symbol:
                    continue
                try:
                    abs_path = self._uri_to_path(info.location.uri)
                except Exception:
                    continue
                if not self._is_within_root(abs_path):
                    continue
                rel_path = self._relative_to_root(abs_path)
                if not matches_path(rel_path):
                    continue
                locations.append(
                    _SymbolLocation(
                        session=session,
                        language=language,
                        location=info.location,
                        name=info.name,
                        kind=info.kind,
                        container=info.containerName,
                        abs_path=abs_path,
                        rel_path=rel_path,
                    )
                )

        return locations, errors

    @staticmethod
    def _symbol_kind_name(kind: Optional[SymbolKind]) -> Optional[str]:
        return kind.name if isinstance(kind, SymbolKind) else None

    # ------------------------------------------------------------------
    # 对外工具接口
    # ------------------------------------------------------------------
    def lsp_list_symbol_definitions(
        self,
        symbolName: str,
        filePaths: Optional[List[str]] = None,
        include_definition_text: bool = False,
    ) -> Dict[str, Any]:
        symbol = (symbolName or "").strip()
        if not symbol:
            raise SWEAgentToolError("symbolName 不能为空")

        matches_path, normalized_filters = self._build_path_filter(filePaths)
        candidate_languages = self._detect_languages_for_symbol(symbol, normalized_filters)
        locations, errors = self._collect_symbol_locations(symbol, matches_path, candidate_languages)

        if not locations:
            if errors:
                raise SWEAgentToolError("; ".join(errors))
            raise SWEAgentToolError(f"未找到符号: {symbol}")

        definitions: List[Dict[str, Any]] = []
        for loc in locations:
            start = loc.location.range.start
            end = loc.location.range.end
            entry: Dict[str, Any] = {
                "file": loc.rel_path,
                "start_line": start.line + 1,
                "end_line": end.line + 1,
                "language": loc.language,
                "symbol": loc.name,
                "symbol_kind": self._symbol_kind_name(loc.kind),
                "container": loc.container,
            }
            if include_definition_text:
                snippet = self._extract_snippet(
                    loc.abs_path,
                    start.line,
                    end.line,
                    include_end_line=True,
                )
                entry["definition"] = snippet
            definitions.append(entry)

        result: Dict[str, Any] = {
            "tool": "lsp_list_symbol_definitions",
            "symbol": symbol,
            "definitions": definitions,
            "filters": normalized_filters,
            "include_definition_text": include_definition_text,
        }
        if errors:
            result["warnings"] = errors
        return result

    def lsp_list_symbol_usages(
        self,
        symbolName: str,
        max_results: int,
        filePaths: Optional[List[str]] = None,
        include_end_line: bool = True,
    ) -> Dict[str, Any]:
        symbol = (symbolName or "").strip()
        if not symbol:
            raise SWEAgentToolError("symbolName 不能为空")
        if max_results <= 0:
            raise SWEAgentToolError("max_results 必须是正整数")

        matches_path, normalized_filters = self._build_path_filter(filePaths)
        candidate_languages = self._detect_languages_for_symbol(symbol, normalized_filters)
        locations, errors = self._collect_symbol_locations(symbol, matches_path, candidate_languages)

        if not locations:
            if errors:
                raise SWEAgentToolError("; ".join(errors))
            raise SWEAgentToolError(f"未找到符号: {symbol}")

        usages: List[Dict[str, Any]] = []
        seen: Set[Tuple[str, int, int]] = set()
        truncated = False
        reference_errors: List[str] = []

        for loc in locations:
            try:
                self._ensure_document_open(loc.session, loc.abs_path, uri=loc.location.uri)
            except SWEAgentToolError as exc:
                reference_errors.append(f"{loc.rel_path}: {exc}")
                continue

            origin_start = loc.location.range.start
            document_uri = loc.location.uri
            params = ReferenceParams(
                textDocument=TextDocumentIdentifier(uri=document_uri),
                position=Position(line=origin_start.line, character=origin_start.character),
                context=ReferenceContext(includeDeclaration=False),
            )

            try:
                raw_refs = loc.session.client.lsp_endpoint.call_method(
                    "textDocument/references",
                    **params.model_dump(),
                )
            except Exception as exc:
                reference_errors.append(f"{loc.rel_path}: {exc}")
                continue

            for item in raw_refs or []:
                try:
                    reference = Location.model_validate(item)
                except ValidationError:
                    continue

                try:
                    ref_path = self._uri_to_path(reference.uri)
                except Exception:
                    continue
                if not self._is_within_root(ref_path):
                    continue
                rel_ref_path = self._relative_to_root(ref_path)
                if not matches_path(rel_ref_path):
                    continue

                start = reference.range.start
                dedup_key = (reference.uri, start.line, start.character)
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                snippet = self._extract_snippet(
                    ref_path,
                    start.line,
                    reference.range.end.line,
                    include_end_line=include_end_line,
                )

                usages.append(
                    {
                        "file": rel_ref_path,
                        "start_line": start.line + 1,
                        "end_line": reference.range.end.line + 1,
                        "dependency_type": "reference",
                        "snippet": snippet,
                    }
                )

                if len(usages) >= max_results:
                    truncated = True
                    break

            if truncated:
                break

        result: Dict[str, Any] = {
            "tool": "lsp_list_symbol_usages",
            "symbol": symbol,
            "usages": usages,
            "limit": max_results,
            "truncated": truncated,
            "filters": normalized_filters,
        }
        combined_errors = errors + reference_errors
        if combined_errors:
            result["warnings"] = combined_errors
        return result

    def lsp_get_errors(
        self,
        filePaths: List[str],
        min_severity: Optional[Union[str, int]] = 1,
    ) -> Dict[str, Any]:
        """
        获取指定文件的诊断信息。min_severity 可选，指定返回的最小诊断级别。支持: error, warning, information, hint 或 1-4"
        """
        if not filePaths:
            raise SWEAgentToolError("filePaths 不能为空")

        severity_threshold = self._normalize_min_severity(min_severity)
        severity_label = (
            self.DIAGNOSTIC_SEVERITY_MAP.get(severity_threshold)
            if severity_threshold is not None
            else None
        )

        results: List[Dict[str, Any]] = []
        warnings: List[str] = []

        resolved_paths, expand_warnings = self._expand_file_paths(filePaths)
        warnings.extend(expand_warnings)

        if not resolved_paths:
            response: Dict[str, Any] = {
                "tool": "lsp_get_errors",
                "files": results,
            }
            if severity_threshold is not None:
                response["min_severity"] = {
                    "value": severity_threshold,
                    "label": severity_label,
                }
            if warnings:
                response["warnings"] = warnings
            return response
        
        for resolved in resolved_paths:
            rel_path = self._relative_to_root(resolved)

            language = self._detect_language_for_path(resolved)
            if not language:
                warnings.append(f"{rel_path}: 暂不支持的文件类型")
                continue

            try:
                session = self._ensure_session(language)
            except SWEAgentToolError as exc:
                warnings.append(f"{rel_path}: {exc}")
                continue

            uri = resolved.as_uri()
            try:
                self._ensure_document_open(session, resolved, uri=uri)
            except SWEAgentToolError as exc:
                warnings.append(f"{rel_path}: {exc}")
                continue

            diagnostics = self._wait_for_diagnostics(
                session,
                uri,
                timeout=max(float(self.command_timeout), 2.0),
            )

            entries: List[Dict[str, Any]] = []
            for diag in diagnostics:
                diag_range = diag.get("range") or {}
                start = diag_range.get("start") or {}
                end = diag_range.get("end") or {}
                severity_val = diag.get("severity")
                if (
                    severity_threshold is not None
                    and severity_val is not None
                    and severity_val > severity_threshold
                ):
                    continue
                severity_name = self.DIAGNOSTIC_SEVERITY_MAP.get(severity_val)

                entries.append(
                    {
                        "message": diag.get("message", ""),
                        "severity": severity_name or severity_val,
                        "severity_value": severity_val,
                        "source": diag.get("source"),
                        "code": diag.get("code"),
                        "start_line": (start.get("line") or 0) + 1,
                        "start_character": (start.get("character") or 0) + 1,
                        "end_line": (end.get("line") or 0) + 1,
                        "end_character": (end.get("character") or 0) + 1,
                    }
                )

            if len(entries) > 0:
                results.append(
                    {
                        "file": rel_path,
                        "language": language,
                        "diagnostics": entries,
                    }
                )

        response: Dict[str, Any] = {
            "tool": "lsp_get_errors",
            "files": results,
        }
        if severity_threshold is not None:
            response["min_severity"] = {
                "value": severity_threshold,
                "label": severity_label,
            }
        if warnings:
            response["warnings"] = warnings
        return response


class SWEAgent(Agent):
    """在现有Agent框架基础上提供SWE-agent风格能力。"""

    DEFAULT_INSTRUCTIONS = textwrap.dedent(
        """
        你是一名经验丰富的软件工程师助手（SWE-agent）。
        你可以使用提供的工具在仓库中浏览、搜索、修改文件，并运行命令或测试。
        请严格遵循以下原则：
        1. 在分析问题前先查看相关文件与目录结构搜索相关内容。如果你不确定问题所在，请多搜索、多阅读代码。
        2. 对代码改动前先确认复现步骤，并在修改后重新运行验证命令。
        3. 如果有要求每次修改需说明原因，并保持改动最小化，避免无关文件变化。
        4. 输出时请总结解决方案、列出关键改动文件以及当前测试执行情况。
        5. 您能够在单次响应中调用多个工具。当需要获取多个独立信息时，请将工具调用批量处理以实现最优性能。
        """
    ).strip()

    def __init__(
        self,
        workspace_root: str | Path,
        *,
        instructions: Optional[str] = None,
        extra_instructions: Optional[str] = None,
        toolset: Optional[SWEFileSystemTools] = None,
        lsp_toolset: Optional[SWELspTools] = None,
        enable_lsp_tools: bool = True,
        lsp_options: Optional[Dict[str, Any]] = None,
        llm_instance=None,
        encoding: str = "utf-8",
        command_timeout: int = 120,
        max_output_chars: int = 12_000,
        **agent_kwargs: Any,
    ) -> None:
        self.workspace_root = Path(workspace_root).expanduser().resolve()
        if not self.workspace_root.exists() or not self.workspace_root.is_dir():
            raise ValueError(f"工作目录不存在或不是文件夹: {workspace_root}")

        base_instructions = (instructions or self.DEFAULT_INSTRUCTIONS).strip()
        if extra_instructions:
            base_instructions = base_instructions + "\n\n" + extra_instructions.strip()
        self.instructions = base_instructions

        self.toolset = toolset or SWEFileSystemTools(
            workspace_root=self.workspace_root,
            encoding=encoding,
            command_timeout=command_timeout,
            max_output_chars=max_output_chars,
        )

        self.lsp_toolset = None
        if enable_lsp_tools:
            if lsp_toolset is not None:
                self.lsp_toolset = lsp_toolset
            else:
                options = dict(lsp_options or {})
                options.setdefault("encoding", encoding)
                options.setdefault("command_timeout", 10)
                self.lsp_toolset = SWELspTools(
                    workspace_root=self.workspace_root,
                    **options,
                )

        super().__init__(llm_instance=llm_instance, **agent_kwargs)
        self.register_tools(self._default_tools())

    def _default_tools(self) -> List[Any]:
        tools = [
            self.toolset.list_dir,
            self.toolset.file_search,
            self.toolset.file_exists,
            self.toolset.read_file,
            self.toolset.write_file,
            # self.toolset.append_file,
            self.toolset.grep_search,
            self.toolset.search_replace,
            # self.toolset.run_command,
            # self.toolset.run_tests,
            # self.toolset.apply_patch,
            # self.toolset.edit_file,
            # self.toolset.run_tools_parallel,
            # self.toolset.list_symbol_usages,
            # self.toolset.list_symbol_definitions,
        ]
        if self.lsp_toolset is not None:
            tools.extend(
                [
                    self.lsp_toolset.lsp_list_symbol_definitions,
                    self.lsp_toolset.lsp_list_symbol_usages,
                    self.lsp_toolset.lsp_get_errors,
                ]
            )
        return tools

    def build_prompt(
        self,
        task_description: str,
        *,
        acceptance_criteria: Optional[List[str]] = None,
        repo_context: Optional[str] = None,
        extra_notes: Optional[str] = None,
    ) -> str:
        """根据任务信息构造提示词。"""
        sections: List[str] = [self.instructions]
        sections.append(f"### 工作目录\n{self.workspace_root}")
        sections.append(f"### 任务描述\n{task_description.strip()}")

        if acceptance_criteria:
            bullets = "\n".join(f"- {item}" for item in acceptance_criteria)
            sections.append(f"### 验收标准\n{bullets}")
        if repo_context:
            sections.append(f"### 仓库上下文\n{repo_context.strip()}")
        if extra_notes:
            sections.append(f"### 额外说明\n{extra_notes.strip()}")

        sections.append(
            "### 输出格式\n"
            "- 总结解决方案与关键修改\n"
            "- 列出被修改的文件及理由\n"
            "- 说明执行过的测试命令及结果"
        )
        return "\n\n".join(section.strip() for section in sections if section)

    def run_task(
        self,
        task_description: str,
        *,
        acceptance_criteria: Optional[List[str]] = None,
        repo_context: Optional[str] = None,
        extra_notes: Optional[str] = None,
        use_tools: bool = True,
        **chat_kwargs: Any,
    ) -> Dict[str, Any]:
        """执行SWE任务，返回Agent的执行结果。"""
        prompt = self.build_prompt(
            task_description,
            acceptance_criteria=acceptance_criteria,
            repo_context=repo_context,
            extra_notes=extra_notes,
        )
        return self.chat(prompt, use_tools=use_tools, **chat_kwargs)

    def available_tool_names(self) -> List[str]:
        """获取当前注册的工具名称列表。"""
        return self.get_available_tools()

    def close(self) -> None:
        if self.lsp_toolset:
            self.lsp_toolset.close()
