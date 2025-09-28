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

from .agent import Agent


class SWEAgentToolError(RuntimeError):
    """自定义异常：用于指示SWE Agent工具执行失败。"""


@dataclass
class SWEFileSystemTools:
    """SWE Agent默认工具集，实现文件操作、命令执行等能力。"""

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
            self.toolset.run_command,
            self.toolset.run_tests,
            self.toolset.apply_patch,
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
