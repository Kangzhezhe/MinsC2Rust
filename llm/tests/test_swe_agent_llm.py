import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARENT_DIR = PROJECT_ROOT.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from llm.swe_agent import SWEAgent
from llm import llm as llm_module


class RecordingLLM:
    """轻量级LLM替身，用于验证SWEAgent与LLM的交互流程。"""

    def __init__(self) -> None:
        self.prompts: list[dict[str, object]] = []

    def call(self, prompt: str, **kwargs):  # type: ignore[override]
        # 记录每次调用收到的提示词与附加参数
        self.prompts.append({"prompt": prompt, "kwargs": kwargs})
        return "stub-final-answer"

    async def call_async(self, prompt: str, **kwargs):  # pragma: no cover
        return self.call(prompt, **kwargs)

    def get_available_tools(self, tool_type: str = "all") -> list[str]:
        return []


def test_run_task_uses_llm_prompt(tmp_path: Path):
    """SWEAgent.run_task 应构建完整提示词并传递给注入的 LLM。"""

    llm_stub = RecordingLLM()
    agent = SWEAgent(
        workspace_root=tmp_path,
        llm_instance=llm_stub,
        max_iterations=2,
    )

    task_description = "修复支付接口错误"
    acceptance = ["通过所有支付相关单测"]
    repo_context = "项目使用 Django"
    notes = "优先考虑回归风险"

    expected_prompt = agent.build_prompt(
        task_description,
        acceptance_criteria=acceptance,
        repo_context=repo_context,
        extra_notes=notes,
    )

    result = agent.run_task(
        task_description,
        acceptance_criteria=acceptance,
        repo_context=repo_context,
        extra_notes=notes,
        use_tools=False,
    )

    assert result["final_response"] == "stub-final-answer"
    assert llm_stub.prompts, "LLM 替身应被调用一次"
    assert llm_stub.prompts[0]["prompt"] == expected_prompt
    history = agent.get_conversation_history()
    assert history[-1]["content"] == "stub-final-answer"


def test_run_task_with_real_llm_class(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """通过真实 LLM 类（内部封装 ChatOpenAI）验证提示词构建与调用流程。"""

    class StubChatOpenAI:
        def __init__(self, *args, **kwargs) -> None:
            self.calls: list[dict[str, object]] = []

        def invoke(self, messages, **kwargs):  # type: ignore[override]
            self.calls.append({"messages": messages, "kwargs": kwargs})
            return SimpleNamespace(content="real-llm-answer")

    monkeypatch.setattr(llm_module, "ChatOpenAI", StubChatOpenAI)

    agent = SWEAgent(workspace_root=tmp_path, max_iterations=2)

    task_description = "排查订单不同步问题"
    acceptance = ["新增集成测试通过"]
    repo_context = "微服务架构，订单服务与库存服务解耦"
    notes = "需要记录根因分析"

    expected_prompt = agent.build_prompt(
        task_description,
        acceptance_criteria=acceptance,
        repo_context=repo_context,
        extra_notes=notes,
    )

    result = agent.run_task(
        task_description,
        acceptance_criteria=acceptance,
        repo_context=repo_context,
        extra_notes=notes,
        use_tools=False,
    )

    assert result["final_response"] == "real-llm-answer"
    stub_chat = agent.llm.llm
    assert isinstance(stub_chat, StubChatOpenAI)
    assert len(stub_chat.calls) == 1
    call_messages = stub_chat.calls[0]["messages"]
    assert isinstance(call_messages, list) and call_messages
    assert call_messages[-1]["content"] == expected_prompt