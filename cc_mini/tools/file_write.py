from pathlib import Path
from .base import Tool, ToolResult
from .ignored_paths import ignored_path_message, is_ignored_tool_path


class FileWriteTool(Tool):
    name = "Write"
    description = (
        "Creates a new file or completely overwrites an existing file. "
        "Parent directories are created automatically if they don't exist. "
        "Use the Edit tool instead if you only need to change part of a file."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute path to the file to write"},
            "content": {"type": "string", "description": "The full content to write to the file"},
        },
        "required": ["file_path", "content"],
    }

    def execute(self, file_path: str, content: str) -> ToolResult:
        path = Path(file_path)
        if is_ignored_tool_path(path):
            return ToolResult(content=ignored_path_message(path, operation="write"), is_error=True)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except OSError as e:
            return ToolResult(
                content=(
                    f"[TOOL_CALL_ERROR] Write tool failed:\n"
                    f"  file_path: {file_path}\n"
                    f"  reason: Error writing file: {e}\n"
                    f"Please check directory permissions and disk space."
                ),
                is_error=True,
            )

        lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        return ToolResult(content=f"Successfully wrote {lines} lines to {file_path}")
