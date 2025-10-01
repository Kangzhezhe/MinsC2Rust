import os
import shutil
import sys
import textwrap
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARENT_DIR = PROJECT_ROOT.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))


from llm.swe_agent import SWEAgent, SWEAgentToolError, SWEFileSystemTools


class DummyLLM:
    """用于测试的占位LLM实现，避免真实网络调用。"""

    def call(self, *args, **kwargs):
        return "dummy-response"

    async def call_async(self, *args, **kwargs):  # pragma: no cover - 异步接口保持一致
        return "dummy-response"

    def get_available_tools(self, tool_type: str = "all"):
        return []


class RepeatedToolDummyLLM:
    """模拟连续重复工具调用的LLM，触发Agent的冗余检测。"""

    def __init__(self, final_text: str = "final-answer") -> None:
        self.call_count = 0
        self.final_text = final_text
        self.notice_triggered = False

    def call(self, prompt: str, *args, **kwargs):
        self.call_count += 1
        if "禁止再次调用工具" in prompt:
            self.notice_triggered = True
            return self.final_text

        if kwargs.get("caller") is not None:
            return {
                "tool_name": "run_command",
                "tool_result": {"returncode": 0, "stdout": "ok"},
                "llm_output": "{\"tool_call\": {\"name\": \"run_command\", \"args\": {\"command\": \"PYTHONPATH=. pytest -q\"}}}",
            }

        return "unexpected-call"

    async def call_async(self, prompt: str, *args, **kwargs):  # pragma: no cover - 与 call 一致
        return self.call(prompt, *args, **kwargs)

    def get_available_tools(self, tool_type: str = "all"):
        return []

    def _apply_memory_strategy(self, messages):
        return messages


def test_toolset_path_guard(tmp_path: Path):
    toolset = SWEFileSystemTools(tmp_path)
    outside_file = tmp_path.parent / "outside.txt"
    outside_file.write_text("secret", encoding="utf-8")
    with pytest.raises(SWEAgentToolError):
        toolset.read_file("../outside.txt", start_line=1, end_line=10)


def test_read_write_append_and_list_dir(tmp_path: Path):
    toolset = SWEFileSystemTools(tmp_path)
    message = "hello world"
    assert not toolset.file_exists("src/app.py")
    toolset.write_file("src/app.py", message)
    assert toolset.file_exists("src/app.py")

    result = toolset.read_file("src/app.py", start_line=1, end_line=1)
    assert result["content"].strip() == message

    toolset.append_file("src/app.py", "\nprint('ok')\n")
    result = toolset.read_file("src/app.py", start_line=1, end_line=5)
    assert "print('ok')" in result["content"]

    listing = toolset.list_dir("src")
    entry = next(item for item in listing["entries"] if item["name"] == "app.py")
    assert entry["type"] == "file"
    assert entry["lines"] >= 2


@pytest.mark.skipif(shutil.which("git") is None, reason="git 命令不可用")
def test_apply_patch(tmp_path: Path):
    toolset = SWEFileSystemTools(tmp_path)
    file_path = tmp_path / "sample.txt"
    file_path.write_text("old line\n", encoding="utf-8")
    patch_text = textwrap.dedent(
        """
        --- sample.txt
        +++ sample.txt
        @@ -1 +1 @@
        -old line
        +new line
        """
    )
    response = toolset.apply_patch(patch_text)
    assert response["returncode"] == 0
    assert response["ignore_whitespace"] is False
    assert file_path.read_text(encoding="utf-8") == "new line\n"


def test_run_command_search_and_grep(tmp_path: Path):
    toolset = SWEFileSystemTools(tmp_path)
    toolset.write_file("README.md", "Needle in a haystack\nAnother line\n")
    toolset.write_file("src.c", "int main() { return 0; }\n")

    command_result = toolset.run_command("pwd")
    assert command_result["returncode"] == 0
    assert tmp_path.name in command_result["stdout"]

    grep_plain = toolset.grep_search("Needle", includePattern="README.md")
    assert grep_plain["matches"]
    assert grep_plain["matches"][0]["line"] == 1

    grep_regex = toolset.grep_search(r"^int\s+main", includePattern="*.c", isRegexp=True)
    assert grep_regex["matches"]
    assert grep_regex["matches"][0]["file"] == "src.c"


def test_swe_agent_prompt_and_tools(tmp_path: Path):
    agent = SWEAgent(
        workspace_root=tmp_path,
        llm_instance=DummyLLM(),
        max_iterations=2,
    )
    prompt = agent.build_prompt(
        "修复登录流程中的bug",
        acceptance_criteria=["通过单元测试", "确保日志记录"],
        repo_context="使用FastAPI构建",
        extra_notes="注意异常处理",
    )
    assert "SWE-agent" in prompt
    assert "修复登录流程中的bug" in prompt
    assert "通过单元测试" in prompt
    tool_names = agent.available_tool_names()
    assert "list_dir" in tool_names
    assert "run_command" in tool_names
    assert "grep_search" in tool_names
    assert "list_symbol_usages" in tool_names
    assert "list_symbol_definitions" in tool_names


def test_agent_stops_redundant_tool_calls(tmp_path: Path):
    repeat_llm = RepeatedToolDummyLLM()
    agent = SWEAgent(
        workspace_root=tmp_path,
        llm_instance=repeat_llm,
        max_iterations=6,
        redundant_tool_call_limit=3,
    )

    result = agent.chat("请运行测试直到通过", use_tools=True)

    assert result["final_response"] == "final-answer"
    assert repeat_llm.notice_triggered is True
    assert len(result["tool_calls"]) == 3
    assert result["iterations"] >= 4