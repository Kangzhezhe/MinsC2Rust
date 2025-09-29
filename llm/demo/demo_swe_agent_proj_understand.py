"""示例：使用 SWEAgent 迭代修复代码以通过 pytest。

运行方式：
    python -m demo.demo_swe_agent_proj_understand
"""

from __future__ import annotations

import shutil
import sys
import textwrap
from pathlib import Path

# 确保可以通过 "import llm" 找到本地包
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from llm.llm import LLM  # type: ignore[import-not-found]  # noqa: E402
from llm.swe_agent import SWEAgent  # type: ignore[import-not-found]  # noqa: E402


def prepare_fix_workspace() -> Path:
    """构建一个包含缺陷的最小化项目，便于演示自动修复流程。"""

    workspace = Path(__file__).resolve().parent / "swe_agent_understand_workspace"
    if workspace.exists():
        shutil.rmtree(workspace)

    source_project = REPO_ROOT / "benchmarks" /"c-algorithm"
    if not source_project.exists():
        msg = f"源项目不存在: {source_project}"
        raise FileNotFoundError(msg)

    shutil.copytree(source_project, workspace)

    return workspace


def run_pytest(agent: SWEAgent) -> dict[str, str | int | bool]:
    """借助 SWEAgent 的命令工具执行 pytest 并返回结果。"""

    return agent.toolset.run_command("PYTHONPATH=. pytest -q", timeout=90)




def demonstrate_understanding(agent: SWEAgent, max_rounds: int = 5) -> None:
    task_description = textwrap.dedent(
        f"""
        我有一个项目需要你帮我理解它的结构和功能。

        """
    ).strip()

    response = agent.run_task(
        task_description,
        acceptance_criteria=[
            "请描述项目的核心工作流程。",
            "如何运行这个项目，给出运行的命令。",
        ],
    )

    print("\n代理回复:")
    print(response.get("tool_calls", []))
    print(response["final_response"])
       


def main() -> None:
    workspace = prepare_fix_workspace()
    llm = LLM(logger=True)
    # llm = LLM()
    agent = SWEAgent(
        workspace_root=workspace,
        llm_instance=llm,
        max_iterations=20,
        command_timeout=90,
        memory_strategy={"name": "tokenlimit", "max_tokens": 2000},
    )

    print("SWEAgent 代码理解演示")
    print(f"工作目录: {workspace}")

    demonstrate_understanding(agent)


if __name__ == "__main__":
    main()
