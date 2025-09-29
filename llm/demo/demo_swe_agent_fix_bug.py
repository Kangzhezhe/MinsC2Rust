"""示例：使用 SWEAgent 迭代修复代码以通过 pytest。

运行方式：
    python -m demo.demo_swe_agent_fix_bug
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
from llm.memory import SlidingWindowStrategy


def prepare_fix_workspace() -> Path:
    """构建一个包含缺陷的最小化项目，便于演示自动修复流程。"""

    workspace = Path(__file__).resolve().parent / "swe_agent_fix_workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)

    package_dir = workspace / "app"
    tests_dir = workspace / "tests"
    package_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    (package_dir / "__init__.py").write_text("from .calculator import divide\n", encoding="utf-8")
    (package_dir / "calculator.py").write_text(
        textwrap.dedent(
            """
            def divide(a: float, b: float) -> float:
                '''返回 a 除以 b。当前实现存在精度缺陷。'''
                if b == 0:
                    raise ValueError("division by zero")
                return a // b
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    (tests_dir / "test_calculator.py").write_text(
        textwrap.dedent(
            """
            import math
            from app import divide
            def test_divide_precise():
                assert divide(9, 4) == 2.25

            def test_divide_negative():
            assert math.isclose(divide(-9, 4), -2.25, rel_tol=1e-9)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    return workspace


def run_pytest(agent: SWEAgent) -> dict[str, str | int | bool]:
    """借助 SWEAgent 的命令工具执行 pytest 并返回结果。"""

    return agent.toolset.run_command("PYTHONPATH=. pytest -q", timeout=90)


def format_test_report(result: dict[str, str | int | bool]) -> str:
    """将 pytest 结果格式化为提示词友好的文本。"""

    stdout = (result.get("stdout") or "").strip()
    stderr = (result.get("stderr") or "").strip()
    return textwrap.dedent(
        f"""
        命令: {result.get("command")}
        返回码: {result.get("returncode")}
        stdout:
        {stdout or '<empty>'}

        stderr:
        {stderr or '<empty>'}
        """
    ).strip()


def demonstrate_fixing1(agent: SWEAgent, max_rounds: int = 5) -> None:
    """循环运行 pytest，将失败日志交给代理修复，并自动确认。"""

    for round_idx in range(1, max_rounds + 1):
        print(f"\n===> 第 {round_idx} 轮：运行 pytest")
        test_result = run_pytest(agent)

        if test_result.get("returncode") == 0:
            print("✅ 所有测试已通过，无需进一步修复。")
            break

        task_description = textwrap.dedent(
            f"""
            我的py工程有一个bug，导致单元测试无法通过。请你帮我修复它。

            项目结构：
            - app/__init__.py
            - app/calculator.py  ← divide 函数定义在此文件
            - tests/test_calculator.py

            注意：app/calculator.py 当前实现中使用了整除运算符，导致精度问题。

            期望你：
            1. 先read_file读取错误的文件诊断失败根因并说明修改理由；
            2. 使用 edit_file 工具修复相关代码，保持改动最小；
            """
        ).strip()

        response = agent.run_task(
            task_description,
            acceptance_criteria=[
                "必须使用 edit_file 提交修复代码",
                # "重新运行 PYTHONPATH=. pytest -q 并通过",
            ],
            repo_context="这是一个最小化示例项目，位于 swe_agent_fix_workspace。",
            extra_notes=f"自动修复第 {round_idx} 轮。",
        )

        print("\n代理回复:")
        print(response["final_response"])
    else:
        print("\n⚠️ 达到最大迭代次数，测试仍未通过，请人工介入。")


def demonstrate_fixing(agent: SWEAgent, max_rounds: int = 5) -> None:
    """运行 pytest，将失败日志交给代理修复，并自动确认。"""
    task_description = textwrap.dedent(
        f"""
        我的py工程有一个bug，导致单元测试无法通过。请你帮我修复它。
        """
    ).strip()

    response = agent.run_task(
        task_description,
        acceptance_criteria=[
            "修复代码中的所有bug",
            "修改之后运行一次 PYTHONPATH=. pytest -q 并通过",
            "确保所有测试用例通过则结束"
        ],
        repo_context="这是一个最小化示例项目，位于 swe_agent_fix_workspace。",
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
        max_iterations=30,
        command_timeout=90,
        # memory_strategy={"name": "slidingwindow", "max_messages": 5},
        # memory_strategy={"name": "tokenlimit", "max_tokens": 5000},
        memory_strategy={"name": "summary"},
    )

    print("SWEAgent 代码修复演示")
    print(f"工作目录: {workspace}")

    demonstrate_fixing(agent)


if __name__ == "__main__":
    main()
