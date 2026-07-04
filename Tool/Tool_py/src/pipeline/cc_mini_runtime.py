"""Runtime adapter for optional CC-MINI fallback sessions.

The translation pipeline should not depend on CC-MINI internals directly.
This module wraps the optional agent, exposes command/debug tools, records
tool calls, and performs the final acceptance command when CC-MINI returns.
"""

import json
import os
import re
import subprocess
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

class CcMiniCommandToolset:
    """Small command/debug toolset exposed to CC-MINI fallback sessions."""

    def __init__(self, workspace_root: str, command_timeout: int = 300):
        self.workspace_root = os.path.abspath(workspace_root)
        self.command_timeout = max(1, int(command_timeout or 300))
        self.debug_script_dependency_overrides: Dict[str, str] = {}

    def _strip_markdown_code_fence(raw: str) -> str:
        text = str(raw or "").strip()
        if not text.startswith("```"):
            return text
        lines = text.splitlines()
        if len(lines) >= 2 and lines[-1].strip().startswith("```"):
            return "\n".join(lines[1:-1]).strip()
        return text

    def run_command(self, command: str) -> Dict[str, Any]:
        try:
            env = os.environ.copy()
            shared_target_dir = os.path.join(self.workspace_root, "tmp", "cargo_target_shared")
            os.makedirs(shared_target_dir, exist_ok=True)
            env["CARGO_TARGET_DIR"] = shared_target_dir

            proc = subprocess.run(
                ["bash", "-lc", command],
                cwd=self.workspace_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=self.command_timeout,
                env=env,
            )
            return {
                "returncode": int(proc.returncode),
                "stdout": proc.stdout or "",
                "stderr": proc.stderr or "",
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "returncode": 124,
                "stdout": (exc.stdout or "") if hasattr(exc, "stdout") else "",
                "stderr": f"command timeout after {self.command_timeout}s",
            }
        except Exception as exc:
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": str(exc),
            }

    def run_rust_debug_script(
        self,
        script_code: str,
        relative_crate_path: str = ".",
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        body = self._strip_markdown_code_fence(script_code)
        if not body:
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": "script_code is empty",
            }

        crate_path = str(relative_crate_path or ".").strip() or "."
        dep_lines = [
            f"//! verify_project = {{ path = \"{crate_path}\" }}",
        ]
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

        script_path = os.path.join(self.workspace_root, "debug.rs")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(full_script)

        effective_timeout = int(timeout or self.command_timeout)
        commands = [
            ["rust-script", script_path],
            ["cargo", "script", script_path],
        ]

        last_error = ""
        for idx, cmd in enumerate(commands):
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.workspace_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=effective_timeout,
                    check=False,
                )
            except FileNotFoundError:
                last_error = f"command not found: {cmd[0]}"
                continue
            except subprocess.TimeoutExpired:
                return {
                    "script_path": "debug.rs",
                    "runner": " ".join(cmd[:2]),
                    "returncode": 124,
                    "stdout": "",
                    "stderr": f"debug script timeout after {effective_timeout}s",
                    "timeout": effective_timeout,
                    "fallback_used": idx > 0,
                }

            return {
                "script_path": "debug.rs",
                "runner": " ".join(cmd[:2]),
                "returncode": int(result.returncode),
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "timeout": effective_timeout,
                "fallback_used": idx > 0,
            }

        return {
            "script_path": "debug.rs",
            "runner": "",
            "returncode": 1,
            "stdout": "",
            "stderr": "rust-script unavailable; please install rust-script" + (f"; last_error={last_error}" if last_error else ""),
            "timeout": effective_timeout,
            "fallback_used": False,
        }


@contextmanager
def _pushd(path: str):
    prev = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


class CcMiniRuntimeAgentAdapter:
    """Adapter around the optional CC-MINI Agent dependency.

    The project must keep running when CC-MINI is unavailable, but when fallback
    is enabled this adapter normalizes tool registration, run logs, and return
    values so the main pipeline does not depend on CC-MINI internals directly.
    """

    def __init__(
        self,
        cc_mini_cls,
        workspace_root: str,
        cc_mini_options: Optional[Dict[str, Any]] = None,
        command_timeout: int = 300,
        run_log_path: str = "",
        max_call_attempts: int = 2,
    ):
        self.workspace_root = os.path.abspath(workspace_root)
        self.run_log_path = str(run_log_path or "").strip()
        self.cc_mini_max_call_attempts = max(1, int(max_call_attempts or 2))
        self._agent_tool_calls: List[Dict[str, Any]] = []
        self._pending_reasoning_log: str = ""

        def _on_reasoning(reasoning: str) -> None:
            self._pending_reasoning_log = str(reasoning or "")

        def _append_pending_reasoning_log() -> None:
            if not self._pending_reasoning_log:
                return
            reasoning_text = self._pending_reasoning_log
            self._pending_reasoning_log = ""
            token_len = self._estimate_token_count(reasoning_text)
            self._append_run_log(
                "[CC-MINI REASONING] "
                + f"len={token_len} reasoning= "
                + self._safe_json(reasoning_text, max_chars=4000)
            )

        def _on_tool_call(tool_name: str, tool_input: dict) -> None:
            tool_name_text = str(tool_name or "")
            tool_input_dict = dict(tool_input or {})
            self._agent_tool_calls.append(
                {
                    "name": tool_name_text,
                    "args": tool_input_dict,
                }
            )
            _append_pending_reasoning_log()
            self._append_run_log(
                "[CC-MINI TOOL CALL] "
                + tool_name_text
                + " input="
                + self._safe_json(tool_input_dict, max_chars=6000)
            )
            if tool_name_text == "Bash" and "script_code" in tool_input_dict:
                self._append_run_log("[CC-MINI TOOL HINT] model used Bash to run embedded script; consider run_rust_debug_script")

        def _on_tool_result(tool_name: str, tool_input: dict, result: object) -> None:
            tool_name_text = str(tool_name or "")
            tool_input_dict = dict(tool_input or {})
            for item in reversed(self._agent_tool_calls):
                if item.get("name") == tool_name_text and item.get("args") == tool_input_dict:
                    item["result"] = result
                    self._append_run_log(
                        "[CC-MINI TOOL RESULT] "
                        + tool_name_text
                        + " output="
                        + self._safe_json(result, max_chars=8000)
                    )
                    return
            self._agent_tool_calls.append(
                {
                    "name": tool_name_text,
                    "args": tool_input_dict,
                    "result": result,
                }
            )
            self._append_run_log(
                "[CC-MINI TOOL RESULT] "
                + tool_name_text
                + " output="
                + self._safe_json(result, max_chars=8000)
            )

        kwargs = dict(cc_mini_options or {})
        kwargs.setdefault("on_tool_call", _on_tool_call)
        kwargs.setdefault("on_tool_result", _on_tool_result)
        kwargs.setdefault("on_reasoning", _on_reasoning)
        with _pushd(self.workspace_root):
            self._agent = cc_mini_cls(**kwargs)
        self.toolset = CcMiniCommandToolset(self.workspace_root, command_timeout=command_timeout)
        self.tools: Dict[str, Any] = {}

        try:
            engine = getattr(self._agent, "engine", None)
            engine_tools = list(getattr(engine, "tools", []) or getattr(engine, "_tools", {}).values() if engine else [])
            for t in engine_tools:
                t_name = getattr(t, "name", "")
                if t_name:
                    self.tools[t_name] = t
            
            # Use CC-MINI native tool wrapper if possible
            if "run_rust_debug_script" not in self.tools:
                try:
                    from cc_mini.tools.rust_debug_script import RustDebugScriptTool
                    debug_tool = RustDebugScriptTool(workspace_root=self.workspace_root, command_timeout=command_timeout)
                    # Share reference to dependency overrides dict from toolset
                    debug_tool.debug_script_dependency_overrides = self.toolset.debug_script_dependency_overrides
                    self.tools["run_rust_debug_script"] = debug_tool
                    engine_tools.append(debug_tool)
                    if hasattr(engine, "set_tools"):
                        engine.set_tools(engine_tools)
                except ImportError:
                    self.tools["run_rust_debug_script"] = self.toolset.run_rust_debug_script
        except Exception:
            pass

    def register_tools(self, tools: List[Any]) -> None:
        for tool in tools or []:
            name = getattr(tool, "name", getattr(tool, "__name__", ""))
            if name:
                self.tools[name] = tool
        
        try:
            engine = getattr(self._agent, "engine", None)
            if hasattr(engine, "set_tools"):
                engine.set_tools(list(self.tools.values()))
        except Exception:
            pass

    @staticmethod
    def _safe_json(data: Any, max_chars: int = 4000) -> str:
        try:
            text = json.dumps(data, ensure_ascii=False, default=str)
        except Exception:
            text = str(data)
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 14] + "...(truncated)"

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        raw = str(text or "")
        if not raw:
            return 0
        cjk_count = sum(1 for ch in raw if "\u4e00" <= ch <= "\u9fff")
        non_cjk_count = len(raw) - cjk_count
        return cjk_count + max(1, (non_cjk_count + 3) // 4)

    def _append_run_log(self, message: str) -> None:
        if not self.run_log_path:
            return
        try:
            os.makedirs(os.path.dirname(self.run_log_path), exist_ok=True)
            with open(self.run_log_path, "a", encoding="utf-8") as f:
                f.write(message.rstrip("\n") + "\n")
        except Exception:
            return

    def run_task(
        self,
        task_description: str,
        acceptance_criteria: Optional[List[str]] = None,
        extra_notes: str = "",
    ) -> Dict[str, Any]:
        self._agent_tool_calls = []
        prompt_parts = [
            (
                str(task_description or "").strip()
            )
        ]
        if acceptance_criteria:
            prompt_parts.append("\n验收标准:\n" + "\n".join(f"- {c}" for c in acceptance_criteria if c))
        if extra_notes:
            prompt_parts.append("\n附加策略:\n" + str(extra_notes))
        prompt = "\n\n".join(part for part in prompt_parts if part)

        final_response = ""
        error_text = ""
        max_call_attempts = max(1, int(getattr(self, "cc_mini_max_call_attempts", 2)))
        for call_attempt in range(1, max_call_attempts + 1):
            self._append_run_log(
                f"[CC-MINI CALL START] attempt={call_attempt}/{max_call_attempts} prompt_chars={len(prompt)}"
            )
            try:
                with _pushd(self.workspace_root):
                    final_response = self._agent.call(prompt)
                error_text = ""
                self._append_run_log(
                    f"[CC-MINI CALL OK] attempt={call_attempt}/{max_call_attempts} response_chars={len(final_response or '')}"
                )
                break
            except Exception as exc:
                error_text = str(exc)
                self._append_run_log(
                    "[CC-MINI CALL ERROR] attempt="
                    + f"{call_attempt}/{max_call_attempts} err="
                    + self._safe_json(error_text, max_chars=3000)
                )
                if call_attempt < max_call_attempts:
                    time.sleep(1)

        compile_cmd = ""
        if acceptance_criteria:
            for criterion in acceptance_criteria:
                m = re.search(r"`([^`]+)`", str(criterion or ""))
                if m:
                    cmd = m.group(1).strip()
                    if cmd:
                        compile_cmd = cmd
                        break

        tool_calls: List[Dict[str, Any]] = list(self._agent_tool_calls)
        success = False
        should_run_acceptance = not bool(error_text)
        if compile_cmd and should_run_acceptance:
            cmd_result = self.toolset.run_command(compile_cmd)
            self._append_run_log(
                "[CC-MINI TOOL CALL] run_command input="
                + self._safe_json({"command": compile_cmd}, max_chars=3000)
                + " source=adapter_acceptance_check"
            )
            self._append_run_log(
                "[CC-MINI TOOL RESULT] run_command output="
                + self._safe_json(cmd_result, max_chars=8000)
                + " source=adapter_acceptance_check"
            )
            tool_calls.append(
                {
                    "name": "run_command",
                    "args": {"command": compile_cmd},
                    "result": cmd_result,
                    "source": "adapter_acceptance_check",
                }
            )
            success = int((cmd_result or {}).get("returncode", 1)) == 0
        elif compile_cmd and not should_run_acceptance:
            self._append_run_log(
                "[CC-MINI ACCEPTANCE SKIPPED] reason=agent_call_failed command="
                + self._safe_json(compile_cmd, max_chars=1200)
            )

        if error_text:
            success = False

        return {
            "success": bool(success),
            "iterations": 1,
            "error": error_text,
            "final_response": final_response,
            "tool_calls": tool_calls,
            "cc_mini_tool_call_count": len(self._agent_tool_calls),
        }

    def close(self) -> None:
        close = getattr(getattr(self, "_agent", None), "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass
