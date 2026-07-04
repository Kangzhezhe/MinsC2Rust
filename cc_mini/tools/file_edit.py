from pathlib import Path
from .base import Tool, ToolResult
from .ignored_paths import ignored_path_message, is_ignored_tool_path


class FileEditTool(Tool):
    name = "Edit"
    description = (
        "Performs exact string replacement in a file. "
        "old_string must uniquely match — fails if 0 or 2+ occurrences found. "
        "Set replace_all=true to replace every occurrence."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute path to file"},
            "old_string": {"type": "string", "description": "Exact string to replace"},
            "new_string": {"type": "string", "description": "Replacement string"},
            "replace_all": {"type": "boolean", "description": "Replace all occurrences", "default": False},
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    def execute(self, file_path: str, old_string: str, new_string: str,
                replace_all: bool = False) -> ToolResult:
        path = Path(file_path)
        if is_ignored_tool_path(path):
            return ToolResult(content=ignored_path_message(path, operation="edit"), is_error=True)
        if not path.exists():
            return ToolResult(
                content=(
                    f"[TOOL_CALL_ERROR] Edit tool failed:\n"
                    f"  file_path: {file_path}\n"
                    f"  reason: File not found\n"
                    f"Please verify the file path and try again."
                ),
                is_error=True,
            )
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            return ToolResult(
                content=(
                    f"[TOOL_CALL_ERROR] Edit tool failed:\n"
                    f"  file_path: {file_path}\n"
                    f"  reason: Error reading file: {e}\n"
                    f"Please check file permissions and try again."
                ),
                is_error=True,
            )

        count = content.count(old_string)
        if count == 0:
            return ToolResult(
                content=(
                    f"[TOOL_CALL_ERROR] Edit tool failed:\n"
                    f"  file_path: {file_path}\n"
                    f"  reason: old_string not found in file\n"
                    f"  old_string (first 200 chars): {old_string[:200]!r}\n"
                    f"  new_string (first 200 chars): {new_string[:200]!r}\n"
                    f"Hint: The old_string must exactly match the current file content. "
                    f"Check for whitespace, indentation, or line ending differences."
                ),
                is_error=True,
            )
        if count > 1 and not replace_all:
            return ToolResult(
                content=(
                    f"[TOOL_CALL_ERROR] Edit tool failed:\n"
                    f"  file_path: {file_path}\n"
                    f"  reason: old_string found {count} times (ambiguous match)\n"
                    f"  old_string (first 200 chars): {old_string[:200]!r}\n"
                    f"  new_string (first 200 chars): {new_string[:200]!r}\n"
                    f"Hint: Add more surrounding context to old_string to make it unique, "
                    f"or set replace_all=true if you want to replace all occurrences."
                ),
                is_error=True,
            )

        new_content = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
        try:
            path.write_text(new_content, encoding="utf-8")
        except OSError as e:
            return ToolResult(
                content=(
                    f"[TOOL_CALL_ERROR] Edit tool failed:\n"
                    f"  file_path: {file_path}\n"
                    f"  reason: Error writing file: {e}\n"
                    f"Please check file permissions and disk space."
                ),
                is_error=True,
            )

        replaced = count if replace_all else 1
        return ToolResult(content=f"Successfully replaced {replaced} occurrence(s) in {file_path}")
