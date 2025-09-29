import os
import re
import shlex
import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pydantic import BaseModel,Field, RootModel

from .agent import Agent

import subprocess
import tempfile
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed

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

        条目缺失字段或工具不可用将立即抛出异常；执行期间出错的任务会被收集在返回值的 `errors` 中。
        `max_workers` 默认为任务数量。
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
                except OSError:
                    entry_info["size"] = None
            entries.append(entry_info)
        return {"path": self._relative_to_root(target), "entries": entries}

    def file_exists(self, path: str) -> bool:
        """判断文件或目录是否存在。"""
        target = self._resolve_path(path, allow_nonexistent=True)
        return target.exists()

    def read_file(
        self,
        path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        max_bytes: int = 64_000,
    ) -> Dict[str, Any]:
        """读取文件内容，可选行范围截取。

        返回信息包含：
        - ``path``：相对工作区根目录的路径；
        - ``content``：读取到的文本内容（可能被截断）；
        - ``start_line`` / ``end_line``：当前片段在文件中的行号范围。
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
        """向文件追加内容。"""
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
    ) -> Dict[str, Any]:
        """在指定文件中执行一次唯一的字符串替换。

        要求调用方提供足够长的上下文确保 ``old_string`` 在文件内只出现一次，
        否则会抛出 ``SWEAgentToolError``；如果成功，将替换首个匹配并写回原文件。
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
        if occurrences > 1:
            raise SWEAgentToolError("old_string 在文件中出现超过一次，请提供更精确的上下文以确保唯一性")

        updated = content.replace(old_string, new_string, 1)

        try:
            target.write_text(updated, encoding=self.encoding)
        except OSError as exc:
            raise SWEAgentToolError(f"写入文件失败: {exc}") from exc

        return {
            "tool": "search_replace",
            "path": self._relative_to_root(target),
            "replacements": 1,
        }

    def search_text(
        self,
        pattern: str,
        path: str = ".",
        case_sensitive: bool = False,
        max_matches: int = 20,
    ) -> Dict[str, Any]:
        """递归搜索文本，返回匹配行。"""
        compiled = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
        base = self._resolve_path(path)
        matches: List[Dict[str, Any]] = []
        for file_path in self._iter_files(base):
            try:
                with file_path.open("r", encoding=self.encoding, errors="ignore") as fh:
                    for idx, line in enumerate(fh, start=1):
                        if compiled.search(line):
                            matches.append(
                                {
                                    "file": self._relative_to_root(file_path),
                                    "line": idx,
                                    "content": line.rstrip("\n"),
                                }
                            )
                            if len(matches) >= max_matches:
                                return {"pattern": pattern, "matches": matches}
            except OSError:
                continue
        return {"pattern": pattern, "matches": matches}

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

            1. **完整重写**：提供目标文件的全部内容（允许使用 Markdown 代码块包裹）。文件会被按给出的文本直接创建或覆盖。
            2. **片段编辑**：尽量减少未修改文本，并使用 `// ... existing code ...` 或 `# ... existing code ...` 之类的占位行划分片段。每个占位符表示原文件中未改动的部分应原样保留。请提供足够的上下文以便唯一定位每段修改，若无法匹配将抛出错误并提示补充上下文或改用 diff。

            - 不要在未加占位符的情况下省略原有代码，否则下游应用器会将缺失部分视作删除。
            - 修改同一文件应集中在一次 `edit_file` 调用中；如需编辑多个文件，请并行发起多次调用，每次对应一个文件。
            - `target_file` 建议使用工作区内的相对路径，也支持绝对路径（会保持原值）。

            成功时返回执行元信息（模式、写入字节等）；若无法安全应用，抛出 `SWEAgentToolError`。
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


class SWEAgent(Agent):
    """在现有Agent框架基础上提供SWE-agent风格能力。"""

    DEFAULT_INSTRUCTIONS = textwrap.dedent(
        """
        你是一名经验丰富的软件工程师助手（SWE-agent）。
        你可以使用提供的工具在仓库中浏览、搜索、修改文件，并运行命令或测试。
        请严格遵循以下原则：
        1. 在分析问题前先查看相关文件与目录结构。
        2. 对代码改动前先确认复现步骤，并在修改后重新运行验证命令。
        3. 每次修改需说明原因，并保持改动最小化，避免无关文件变化。
        4. 输出时请总结解决方案、列出关键改动文件以及测试执行情况。
        """
    ).strip()

    def __init__(
        self,
        workspace_root: str | Path,
        *,
        instructions: Optional[str] = None,
        extra_instructions: Optional[str] = None,
        toolset: Optional[SWEFileSystemTools] = None,
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

        super().__init__(llm_instance=llm_instance, **agent_kwargs)
        self.register_tools(self._default_tools())

    def _default_tools(self) -> List[Any]:
        return [
            self.toolset.list_dir,
            self.toolset.file_exists,
            self.toolset.read_file,
            self.toolset.write_file,
            self.toolset.append_file,
            self.toolset.search_text,
            self.toolset.search_replace,
            self.toolset.run_command,
            self.toolset.run_tests,
            # self.toolset.apply_patch,
            self.toolset.edit_file,
            self.toolset.run_tools_parallel
        ]

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
