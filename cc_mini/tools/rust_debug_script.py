from __future__ import annotations

import subprocess
from pathlib import Path

from .base import Tool, ToolResult


class RustDebugScriptTool(Tool):
    name = "run_rust_debug_script"
    description = (
        "Write and run a Rust debug script as debug.rs with rust-script/cargo-script. "
        "Useful for runtime diagnosis during Rust test fixes."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "script_code": {"type": "string", "description": "Rust script body"},
            "relative_crate_path": {
                "type": "string",
                "description": "crate path for verify_project dependency",
                "default": ".",
            },
            "timeout": {"type": "integer", "description": "timeout seconds", "default": 120},
        },
        "required": ["script_code"],
    }

    def __init__(self, workspace_root: str, command_timeout: int = 120):
        self.workspace_root = Path(workspace_root).resolve()
        self.command_timeout = max(1, int(command_timeout or 120))
        self.debug_script_dependency_overrides: dict[str, str] = {}

    @staticmethod
    def _strip_markdown_code_fence(raw: str) -> str:
        text = str(raw or "").strip()
        if not text.startswith("```"):
            return text
        lines = text.splitlines()
        if len(lines) >= 2 and lines[-1].strip().startswith("```"):
            return "\n".join(lines[1:-1]).strip()
        return text

    def execute(
        self,
        script_code: str,
        relative_crate_path: str = ".",
        timeout: int = 120,
    ) -> ToolResult:
        body = self._strip_markdown_code_fence(script_code)
        if not body:
            return ToolResult(content="Error: script_code is empty", is_error=True)

        crate_path = str(relative_crate_path or ".").strip() or "."
        dep_lines = [f"//! verify_project = {{ path = \"{crate_path}\" }}"]
        for dep_name in sorted((self.debug_script_dependency_overrides or {}).keys()):
            dep_key = str(dep_name or "").strip()
            if not dep_key or dep_key == "verify_project":
                continue
            dep_val = str((self.debug_script_dependency_overrides or {}).get(dep_key, "")).strip()
            if not dep_val:
                continue
            dep_lines.append(f"//! {dep_key} = {dep_val}")

        header = "\n".join(
            [
                "#!/usr/bin/env rust-script",
                "//! ```cargo",
                "//! [dependencies]",
                *dep_lines,
                "//! ```",
                "",
            ]
        )
        full_script = header + body.strip() + "\n"

        script_path = self.workspace_root / "debug.rs"
        script_path.write_text(full_script, encoding="utf-8")

        effective_timeout = int(timeout or self.command_timeout)
        commands = [
            ["rust-script", str(script_path)],
            ["cargo", "script", str(script_path)],
        ]

        last_error = ""
        for idx, cmd in enumerate(commands):
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.workspace_root,
                    capture_output=True,
                    text=True,
                    timeout=effective_timeout,
                    check=False,
                )
            except FileNotFoundError:
                last_error = f"command not found: {cmd[0]}"
                continue
            except subprocess.TimeoutExpired:
                return ToolResult(
                    content=(
                        f"script_path=debug.rs\nrunner={' '.join(cmd[:2])}\n"
                        f"timeout={effective_timeout}\nfallback_used={idx > 0}\n"
                        f"stderr=debug script timeout after {effective_timeout}s"
                    ),
                    is_error=True,
                )

            content = (
                f"script_path=debug.rs\n"
                f"runner={' '.join(cmd[:2])}\n"
                f"returncode={int(result.returncode)}\n"
                f"timeout={effective_timeout}\n"
                f"fallback_used={idx > 0}\n"
                f"stdout={result.stdout or ''}\n"
                f"stderr={result.stderr or ''}"
            )
            return ToolResult(content=content, is_error=(result.returncode != 0))

        return ToolResult(
            content=(
                "Error: rust-script unavailable; please install rust-script"
                + (f"; last_error={last_error}" if last_error else "")
            ),
            is_error=True,
        )
