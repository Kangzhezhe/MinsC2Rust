import re
import subprocess
from pathlib import Path
import glob as glob_module
from .base import Tool, ToolResult
from .ignored_paths import IGNORED_GLOB_PATTERNS, ignored_path_message, is_ignored_tool_path


MAX_OUTPUT_CHARS = 80_000
MAX_OUTPUT_LINES = 800


class GrepTool(Tool):
    name = "Grep"
    description = (
        "Search for a regex pattern in files. "
        "Uses ripgrep if available, falls back to Python re. "
        "output_mode='files_with_matches' returns paths; 'content' returns matching lines."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern"},
            "path": {"type": "string", "description": "Directory or file to search"},
            "glob": {"type": "string", "description": "File glob filter e.g. '*.py'"},
            "output_mode": {
                "type": "string",
                "enum": ["files_with_matches", "content"],
                "default": "files_with_matches",
            },
            "-i": {"type": "boolean", "description": "Case insensitive", "default": False},
            "-C": {"type": "integer", "description": "Context lines around each match", "default": 0},
            "head_limit": {
                "type": "integer",
                "description": "Return at most N lines to avoid oversized responses",
            },
        },
        "required": ["pattern"],
    }

    def is_read_only(self) -> bool:
        return True

    @staticmethod
    def _truncate_output(text: str, head_limit: int | None = None) -> str:
        lines = text.splitlines()
        effective_head = head_limit if isinstance(head_limit, int) and head_limit > 0 else MAX_OUTPUT_LINES
        if len(lines) > effective_head:
            lines = lines[:effective_head] + [f"... (truncated to first {effective_head} lines)"]
        truncated = "\n".join(lines)
        if len(truncated) > MAX_OUTPUT_CHARS:
            truncated = truncated[:MAX_OUTPUT_CHARS].rstrip() + "\n... (truncated by size)"
        return truncated

    def execute(self, pattern: str, path: str = ".", glob: str | None = None,
                output_mode: str = "files_with_matches", head_limit: int | None = None,
                **kwargs) -> ToolResult:
        if is_ignored_tool_path(path):
            return ToolResult(content=ignored_path_message(path, operation="search"), is_error=True)

        cmd = ["rg", "--no-heading"]
        if kwargs.get("-i"):
            cmd.append("-i")
        context = kwargs.get("-C", 0)
        if context:
            cmd.extend(["-C", str(context)])
        cmd.append("-l" if output_mode == "files_with_matches" else "-n")
        if glob:
            cmd.extend(["-g", glob])
        for ignored_pattern in IGNORED_GLOB_PATTERNS:
            cmd.extend(["-g", ignored_pattern])
        cmd.extend([pattern, path])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = result.stdout.strip()
            if not output:
                return ToolResult(content="No matches found.")
            return ToolResult(content=self._truncate_output(output, head_limit=head_limit))
        except FileNotFoundError:
            return self._python_grep(
                pattern, path, glob, kwargs.get("-i", False), output_mode, head_limit=head_limit
            )
        except subprocess.TimeoutExpired:
            return ToolResult(content="Error: Search timed out.", is_error=True)

    def _python_grep(self, pattern: str, path: str, glob_filter: str | None,
                     case_insensitive: bool, output_mode: str = "files_with_matches",
                     head_limit: int | None = None) -> ToolResult:
        base = Path(path)
        flags = re.IGNORECASE if case_insensitive else 0
        regex = re.compile(pattern, flags)

        if base.is_file():
            files = [] if is_ignored_tool_path(base) else [base]
        else:
            pat = glob_filter or "**/*"
            files = [
                base / p
                for p in glob_module.glob(pat, root_dir=str(base), recursive=True)
                if not is_ignored_tool_path(base / p)
            ]

        matched = []
        for f in files:
            if not f.is_file():
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
                if output_mode == "content":
                    for lineno, line in enumerate(text.splitlines(), 1):
                        if regex.search(line):
                            matched.append(f"{f}:{lineno}:{line}")
                else:
                    if regex.search(text):
                        matched.append(str(f))
            except OSError:
                pass

        if not matched:
            return ToolResult(content="No matches found.")
        return ToolResult(content=self._truncate_output("\n".join(matched), head_limit=head_limit))
