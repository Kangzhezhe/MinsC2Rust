"""示例：如何在脚本中使用 `SWEAgent` 及其默认工具集。

运行方式：
    python -m demo.demo_swe_agent_usage

该脚本将构建一个临时演示工作区，向其中写入文件、列出目录，并借助
`SWEAgent` 生成任务提示词与模拟回复，帮助你快速熟悉核心接口。
"""

from __future__ import annotations

import sys
from pathlib import Path
import shutil
import textwrap

# 确保可以通过 "import llm" 找到本地包
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from llm.llm import LLM  # type: ignore[import-not-found]  # noqa: E402
from llm.swe_agent import SWEAgent, SWEAgentToolError  # type: ignore[import-not-found]  # noqa: E402  # 延迟导入以便先调整 sys.path


def prepare_demo_workspace() -> Path:
    """创建/返回演示工作区目录，并写入初始文件。"""

    workspace = Path(__file__).resolve().parent / "swe_agent_workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(exist_ok=True)

    docs_dir = workspace / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    readme_path = docs_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text("# Demo 项目\n\n- 初始待办事项\n", encoding="utf-8")

    guide_en_path = docs_dir / "guide_en.md"
    if not guide_en_path.exists():
        guide_en_path.write_text(
            textwrap.dedent(
                """
                # Demo Guide (English)

                This short guide shows how to run the demonstration project locally.

                ## Prerequisites

                - Python 3.11 or newer installed on your system
                - A virtual environment with project dependencies (optional but recommended)

                ## Steps

                1. Install dependencies with `pip install -r requirements.txt`.
                2. Run the showcase script via `python -m demo.demo_swe_agent_usage`.
                3. Review the generated files under the `docs/` directory.

                ## Notes

                The script writes additional assets into the workspace and prints the actions it performs.
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
    return workspace


def demonstrate_agent_workflow(agent: SWEAgent) -> None:
    """构造任务提示词并通过真实 LLM 触发一次对话。"""

    print("\n===> 触发一次 run_task，查看真实 LLM 的回复")
    result = agent.run_task(
        "请审阅 docs/README.md 并补充运行步骤。",
        acceptance_criteria=["明确命令", "提到需要 Python","修改后直接保存文件"],
    )
    print("LLM 最终回复:")
    print(result["final_response"])

    # print("\n已注册工具:")
    # for name in agent.available_tool_names():
    #     print(f"- {name}")


def translate_document(agent: SWEAgent, source: str, target: str) -> None:
    """将英文文档翻译成中文并写入新的 Markdown 文件。"""

    translation_task = textwrap.dedent(
        f"""
        请扮演专业技术文档译者，完成以下目标：

        1. 将 Markdown 内容精准翻译成简体中文，保留原有的 Markdown 结构（标题、列表、代码块等）。
        2. 把翻译后的完整 Markdown 写入文件 "{target}"（相对于工作目录）。
        3. 完成后给出简短总结，说明已生成的文件位置。

        待翻译文件：
        {source}
        """
    ).strip()

    response = agent.run_task(
        translation_task,
        acceptance_criteria=[
            "必须保留 Markdown 语法结构",
            f"将译文保存到 {target}",
            "最终回答需要包含已保存文件的说明",
        ]
    )

    print("\n===> 文档翻译完成")
    print(f"源文件: {source}")
    print(f"代理响应: {response['final_response']}")

    try:
        saved_excerpt = agent.toolset.read_file(target, max_bytes=400)["content"]
        print("\n译文预览 (前 400 字节):\n" + saved_excerpt)
    except SWEAgentToolError as exc:  # type: ignore[name-defined]
        print(f"⚠️ 无法读取保存的文件: {exc}")


def demonstrate_translation(agent: SWEAgent) -> None:
    """演示使用 LLM 将英文文档翻译成中文并另存。"""

    source_path = "docs/guide_en.md"
    target_path = "docs/guide_zh.md"

    print("\n===> 执行英文文档翻译演示")
    translate_document(agent, source_path, target_path)


def main() -> None:
    workspace = prepare_demo_workspace()
    llm = LLM(logger=True)
    # llm = LLM()
    agent = SWEAgent(
        workspace_root=workspace,
        llm_instance=llm,
        max_iterations=5,
        command_timeout=60,
    )

    print("SWEAgent 演示脚本")
    print(f"工作目录: {workspace}")

    demonstrate_agent_workflow(agent)
    demonstrate_translation(agent)


if __name__ == "__main__":
    main()
