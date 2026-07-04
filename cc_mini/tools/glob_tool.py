import glob as glob_module
from pathlib import Path
from .base import Tool, ToolResult
from .ignored_paths import is_ignored_tool_path


class GlobTool(Tool):
    name = "Glob"
    description = "Find files matching a glob pattern. Returns paths sorted by modification time."
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern e.g. '**/*.py'"},
            "path": {"type": "string", "description": "Base directory to search (default: cwd)"},
        },
        "required": ["pattern"],
    }

    def is_read_only(self) -> bool:
        return True

    def execute(self, pattern: str, path: str = ".") -> ToolResult:
        base = Path(path).resolve()
        if not base.exists():
            return ToolResult(content=f"Error: Directory not found: {path}", is_error=True)
        if is_ignored_tool_path(base):
            return ToolResult(content="No files found matching the pattern.")

        matches = [
            p
            for p in glob_module.glob(pattern, root_dir=str(base), recursive=True)
            if not is_ignored_tool_path(base / p)
        ]
        matches = sorted(matches, key=lambda p: (base / p).stat().st_mtime, reverse=True)

        if not matches:
            return ToolResult(content="No files found matching the pattern.")
        return ToolResult(content="\n".join(matches))
