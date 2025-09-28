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


def test_toolset_path_guard(tmp_path: Path):
    print(f"Temporary path for testing: {tmp_path}")
    toolset = SWEFileSystemTools(tmp_path)
    outside_file = tmp_path.parent / "outside.txt"
    outside_file.write_text("secret", encoding="utf-8")
    with pytest.raises(SWEAgentToolError):
        toolset.read_file("../outside.txt")


def test_read_write_append(tmp_path: Path):
    toolset = SWEFileSystemTools(tmp_path)
    message = "hello world"
    assert not toolset.file_exists("src/app.py")
    toolset.write_file("src/app.py", message)
    assert toolset.file_exists("src/app.py")
    result = toolset.read_file("src/app.py")
    assert result["content"] == message
    toolset.append_file("src/app.py", "\nprint('ok')\n")
    result = toolset.read_file("src/app.py")
    assert "print('ok')" in result["content"]


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


def test_run_command_and_search(tmp_path: Path):
    toolset = SWEFileSystemTools(tmp_path)
    toolset.write_file("README.md", "Needle in a haystack\n")
    command_result = toolset.run_command("pwd")
    assert command_result["returncode"] == 0
    assert tmp_path.name in command_result["stdout"]
    matches = toolset.search_text("needle", path=".")
    assert matches["matches"]
    assert matches["matches"][0]["file"] == "README.md"


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