import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))

from pipeline.cc_mini_runtime import CcMiniCommandToolset, CcMiniRuntimeAgentAdapter


class _FakeEngine:
    def __init__(self):
        self.tools = []

    def set_tools(self, tools):
        self.tools = list(tools)


class _SuccessfulFakeAgent:
    def __init__(self, on_tool_call=None, on_tool_result=None, **kwargs):
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result
        self.on_reasoning = kwargs.get("on_reasoning")
        self.kwargs = kwargs
        self.engine = _FakeEngine()
        self.prompts = []

    def call(self, prompt):
        self.prompts.append(prompt)
        if self.on_reasoning is not None:
            self.on_reasoning("Need to run cargo test before editing.")
        args = {"command": "echo agent-side-check"}
        result = {"returncode": 0, "stdout": "agent-side-check\n", "stderr": ""}
        self.on_tool_call("run_command", args)
        self.on_tool_result("run_command", args, result)
        return "finished"


class _CloseableFakeAgent(_SuccessfulFakeAgent):
    def __init__(self, on_tool_call=None, on_tool_result=None, **kwargs):
        super().__init__(on_tool_call=on_tool_call, on_tool_result=on_tool_result, **kwargs)
        self.close_called = False

    def close(self):
        self.close_called = True


class _LongReasoningFakeAgent(_SuccessfulFakeAgent):
    def call(self, prompt):
        self.prompts.append(prompt)
        if self.on_reasoning is not None:
            self.on_reasoning("a" * 5000)
        args = {"command": "echo long-reasoning"}
        result = {"returncode": 0, "stdout": "ok\n", "stderr": ""}
        self.on_tool_call("run_command", args)
        self.on_tool_result("run_command", args, result)
        return "finished"


class _FailingFakeAgent:
    def __init__(self, **kwargs):
        self.engine = SimpleNamespace(tools=[])

    def call(self, prompt):
        raise RuntimeError("agent boom")


class CcMiniCommandToolsetTest(unittest.TestCase):
    def test_strip_markdown_code_fence_handles_plain_and_fenced_code(self):
        self.assertEqual(CcMiniCommandToolset._strip_markdown_code_fence("plain"), "plain")
        self.assertEqual(
            CcMiniCommandToolset._strip_markdown_code_fence("```rust\nfn main() {}\n```"),
            "fn main() {}",
        )

    def test_run_command_executes_inside_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = CcMiniCommandToolset(tmp, command_timeout=5).run_command("pwd")

            self.assertEqual(result["returncode"], 0)
            self.assertEqual(result["stdout"].strip(), tmp)
            self.assertEqual(result["stderr"], "")

    def test_adapter_runs_acceptance_command_and_records_tool_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "cc-mini.log"
            adapter = CcMiniRuntimeAgentAdapter(
                cc_mini_cls=_SuccessfulFakeAgent,
                workspace_root=tmp,
                run_log_path=str(log_path),
                max_call_attempts=1,
            )

            result = adapter.run_task(
                "fix the module",
                acceptance_criteria=["必须执行 `true` 并保持原始退出码"],
                extra_notes="keep changes minimal",
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["final_response"], "finished")
            self.assertEqual(result["cc_mini_tool_call_count"], 1)
            self.assertEqual(len(result["tool_calls"]), 2)
            self.assertEqual(result["tool_calls"][-1]["source"], "adapter_acceptance_check")
            self.assertEqual(result["tool_calls"][-1]["args"], {"command": "true"})
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("[CC-MINI CALL START]", log_text)
            self.assertIn(
                '[CC-MINI REASONING] len=10 reasoning= "Need to run cargo test before editing."',
                log_text,
            )
            self.assertIn(
                '[CC-MINI TOOL RESULT] run_command output={"returncode": 0, "stdout": "agent-side-check\\n", "stderr": ""}',
                log_text,
            )
            self.assertNotIn("[CC-MINI TOOL RESULT] run_command input=", log_text)

    def test_adapter_truncates_long_reasoning_log_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "cc-mini.log"
            adapter = CcMiniRuntimeAgentAdapter(
                cc_mini_cls=_LongReasoningFakeAgent,
                workspace_root=tmp,
                run_log_path=str(log_path),
                max_call_attempts=1,
            )

            result = adapter.run_task("fix the module")

            self.assertEqual(result["final_response"], "finished")
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("[CC-MINI REASONING] len=1250 reasoning= ", log_text)
            self.assertIn("...(truncated)", log_text)

    def test_adapter_does_not_run_acceptance_after_agent_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = CcMiniRuntimeAgentAdapter(
                cc_mini_cls=_FailingFakeAgent,
                workspace_root=tmp,
                max_call_attempts=1,
            )

            result = adapter.run_task(
                "fix the module",
                acceptance_criteria=["必须执行 `true`"],
            )

            self.assertFalse(result["success"])
            self.assertIn("agent boom", result["error"])
            self.assertEqual(result["tool_calls"], [])

    def test_adapter_close_closes_underlying_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = CcMiniRuntimeAgentAdapter(
                cc_mini_cls=_CloseableFakeAgent,
                workspace_root=tmp,
                max_call_attempts=1,
            )

            adapter.close()

            self.assertTrue(adapter._agent.close_called)


if __name__ == "__main__":
    unittest.main()
