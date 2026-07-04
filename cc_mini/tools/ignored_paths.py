from __future__ import annotations

from pathlib import Path


IGNORED_FILE_NAMES = frozenset(
    {
        "cc-mini-llm.log",
        "cc-mini-llm-raw.txt",
    }
)
IGNORED_DIR_NAMES = frozenset({"target"})
IGNORED_GLOB_PATTERNS = tuple(
    [f"!{name}" for name in sorted(IGNORED_FILE_NAMES)]
    + [f"!{name}/**" for name in sorted(IGNORED_DIR_NAMES)]
    + [f"!**/{name}/**" for name in sorted(IGNORED_DIR_NAMES)]
)

# Backward-compatible name used by grep_tool before the ignore list was generalized.
INTERNAL_LOG_FILE_NAMES = IGNORED_FILE_NAMES


def is_ignored_tool_path(path: str | Path) -> bool:
    """Return True for paths CC-MINI tools should avoid reading or writing."""
    candidate = Path(path)
    return candidate.name in IGNORED_FILE_NAMES or any(part in IGNORED_DIR_NAMES for part in candidate.parts)


def is_ignored_read_path(path: str | Path) -> bool:
    return is_ignored_tool_path(path)


def ignored_path_message(path: str | Path, operation: str = "access") -> str:
    candidate = Path(path)
    if candidate.name in IGNORED_FILE_NAMES:
        return (
            f"Error: Refusing to {operation} internal CC-MINI log file: {candidate.name}. "
            "Use project source files, tests, and command output instead."
        )
    for part in candidate.parts:
        if part in IGNORED_DIR_NAMES:
            return (
                f"Error: Refusing to {operation} ignored directory path: {part}. "
                "Ignored target directory path to avoid build-artifact context pollution."
            )
    return f"Error: Refusing to {operation} ignored path: {candidate}"
