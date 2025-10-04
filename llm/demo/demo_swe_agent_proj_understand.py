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

    source_project = REPO_ROOT / "llm/demo/c-algorithm"
    # source_project = REPO_ROOT / "pylspclient/tests/test_rust_workspace"
    if not source_project.exists():
        msg = f"源项目不存在: {source_project}"
        raise FileNotFoundError(msg)

    shutil.copytree(source_project, workspace)

    return workspace


def run_pytest(agent: SWEAgent) -> dict[str, str | int | bool]:
    """借助 SWEAgent 的命令工具执行 pytest 并返回结果。"""

    return agent.toolset.run_command("PYTHONPATH=. pytest -q", timeout=90)




def demonstrate_compile(agent: SWEAgent, max_rounds: int = 5) -> None:
    task_description = textwrap.dedent(
        f"""
        帮我编译并执行这个项目
        """
    ).strip()

    response = agent.run_task(
        task_description,
        acceptance_criteria=[
            "将整个项目编译并执行",
            "如果是一个库，编译并执行其测试用例，不论通不通过",
            "总结编译和执行的结果"
        ],
    )

    print("\n代理回复:")
    print(response.get("tool_calls", []))
    print(response["final_response"])

def demonstrate_search(agent: SWEAgent, max_rounds: int = 5) -> None:
    task_description = textwrap.dedent(
        f"""
        帮我搜索项目中的所有ArrayList 相关的函数
        """
    ).strip()

    response = agent.run_task(
        task_description,
        acceptance_criteria=[
            "列出所有包含 ArrayList 的文件和行号",
            "总结这些函数的用途"
        ],
    )

    print("\n代理回复:")
    print(response.get("tool_calls", []))
    print(response["final_response"])


def demonstrate_symbol(agent: SWEAgent, max_rounds: int = 5) -> None:
    task_description = textwrap.dedent(
        f"""
        帮我搜索项目中的符号 ArrayList 的定义和所有引用
        """
    ).strip()

    response = agent.run_task(
        task_description,
        acceptance_criteria=[
            "解释ArrayList 符号是什么",
            "列出所有 ArrayList 的定义位置和引用位置",
            "对于每个定义，搜索查看他在代码中的详细定义，包括每个字段",
            "对于每个引用，搜索查看他的代码解释它是如何使用 ArrayList 的",
        ],
    )

    print("\n代理回复:")
    print(response.get("tool_calls", []))
    print(response["final_response"])

def demonstrate_errors(agent: SWEAgent, max_rounds: int = 5) -> None:
    task_description = textwrap.dedent(
        f"""
        帮我诊断一下所有的c语言代码编译错误
        """
    ).strip()

    response = agent.run_task(
        task_description,
        acceptance_criteria=[
            "列出所有编译错误",
        ],
    )

    print("\n代理回复:")
    print(response.get("tool_calls", []))
    print(response["final_response"])

def demonstrate_errors_fix(agent: SWEAgent, max_rounds: int = 5) -> None:
    task_description = textwrap.dedent(
        f"""
        帮我修改一下所有的c语言代码编译错误
        """
    ).strip()

    response = agent.run_task(
        task_description,
        acceptance_criteria=[
            "使用lsp获得所有编译错误",
            "强制用 edit_file 工具修改部分代码片段的方式修复编译错误",
            "修改完之后再次确认，确保所有代码可以编译通过",
        ],
    )

    print("\n代理回复:")
    print(response.get("tool_calls", []))
    print(response["final_response"])

def demonstrate_symbol_rust(agent: SWEAgent, max_rounds: int = 5) -> None:
    task_description = textwrap.dedent(
        f"""
        帮我搜索项目中的符号 subtract 的定义和所有引用
        """
    ).strip()

    response = agent.run_task(
        task_description,
        acceptance_criteria=[
            "解释subtract 符号是什么",
            "列出所有 subtract 的定义位置和引用位置",
            "对于每个定义，搜索查看他在代码中的详细定义，包括每个字段",
            "对于每个引用，搜索查看他的代码解释它是如何使用 subtract 的",
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
        # memory_strategy={"name": "tokenlimit", "max_tokens": 2000},
        memory_strategy={"name": "summary", "token_trigger_max_tokens": 3000},
    )

    print("SWEAgent 代码理解演示")
    print(f"工作目录: {workspace}")

    # demonstrate_search(agent)
    # demonstrate_compile(agent)
    # demonstrate_symbol(agent)
    # demonstrate_symbol_rust(agent)
    # demonstrate_errors(agent)
    demonstrate_errors_fix(agent)

    agent.close()


if __name__ == "__main__":
    main()
