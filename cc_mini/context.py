from datetime import date
from pathlib import Path

_BASE_PROMPT = """\
You are Claude Code, an AI assistant for software engineering tasks in the terminal.
You help with coding tasks by reading files, editing code, running commands, and searching codebases.

Guidelines:
- Always read a file before editing it
- Prefer small, targeted edits over rewriting large sections
- Run tests after making changes when test commands are available
- Use Glob/Grep to find relevant files before reading them all
- STRICT WORKDIR RULE: only inspect/edit/run commands inside the provided Working directory unless explicitly instructed otherwise"""


def build_system_prompt(cwd: str | None = None, memory_dir: Path | None = None, use_finish_tool: bool = False) -> str:
    parts = [_BASE_PROMPT]

    if use_finish_tool:
        parts.append(
            "\n# TASK COMPLETION\n"
            "You MUST call the `finish` tool to deliver your final response when the task is fully completed. "
            "Never output plain text as your final response without calling a tool."
        )

    parts.append(f"\n# Environment\nToday's date: {date.today().isoformat()}")

    cwd = cwd or str(Path.cwd())
    parts.append(f"Working directory: {cwd}")

    claude_md = _find_claude_md(cwd)
    if claude_md:
        parts.append(f"\n# CLAUDE.md\n{claude_md}")

    if memory_dir is not None:
        from .memory import build_memory_system_section
        parts.append(build_memory_system_section(memory_dir))

    return "\n".join(parts)


def _find_claude_md(cwd: str) -> str:
    path = Path(cwd) / "CLAUDE.md"
    if path.exists():
        try:
            return path.read_text(encoding="utf-8", errors="replace")[:10_000]
        except OSError:
            pass
    return ""
