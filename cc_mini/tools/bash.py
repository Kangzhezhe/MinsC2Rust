from __future__ import annotations

import locale
import subprocess
from typing import TYPE_CHECKING

from .base import Tool, ToolResult

if TYPE_CHECKING:
    from ..sandbox.manager import SandboxManager

_DEFAULT_TIMEOUT = 300


class BashTool(Tool):
    name = "Bash"
    description = (
        "Execute a bash command. Returns stdout + stderr. "
        "Timeout defaults to 300s. Avoid interactive commands."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The bash command to execute"},
            "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 300},
            "dangerously_disable_sandbox": {
                "type": "boolean",
                "description": "If true and allowed by config, run outside sandbox",
            },
        },
        "required": ["command"],
    }

    def __init__(self, sandbox_manager: SandboxManager | None = None):
        self._sandbox = sandbox_manager

    def execute(
        self,
        command: str,
        timeout: int = _DEFAULT_TIMEOUT,
        dangerously_disable_sandbox: bool = False,
    ) -> ToolResult:
        # Sandbox decision
        use_sandbox = (
            self._sandbox is not None
            and self._sandbox.should_sandbox(command, dangerously_disable_sandbox)
        )

        actual_command = self._sandbox.wrap(command) if use_sandbox else command

        try:
            # On Windows, Python defaults to the ANSI code page (e.g. gbk/cp936).
            # Tool outputs may contain UTF-8 bytes from modern CLIs, causing decode errors.
            # Decode using preferred encoding with a safe fallback and replacement.
            encoding = locale.getpreferredencoding(False) or "utf-8"
            result = subprocess.run(
                actual_command,
                shell=True,
                capture_output=True,
                text=True,
                encoding=encoding,
                errors="replace",
                timeout=timeout,
            )
            parts = []
            if result.stdout:
                parts.append(result.stdout.rstrip())
            if result.stderr:
                parts.append(f"[stderr]\n{result.stderr.rstrip()}")
            if result.returncode != 0:
                parts.append(f"[exit code: {result.returncode}]")
            return ToolResult(content="\n".join(parts) if parts else "(no output)")
        except subprocess.TimeoutExpired:
            return ToolResult(content=f"Error: Command timed out after {timeout}s", is_error=True)
        except Exception as e:
            return ToolResult(content=f"Error: {e}", is_error=True)
