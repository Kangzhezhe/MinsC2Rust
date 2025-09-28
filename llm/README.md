# mins-llm

一个可复用的 LLM 工具集，包含：
- 结构化输出模板解析（TemplateParser / TableParser）
- 工具调用（传统函数调用器）
- 与 Agent 集成的多轮对话与工具编排
- 可选的 MCP 工具调用支持

## 安装（开发模式）
在项目根目录运行：

```bash
pip install -e ./llm
```

或在 `llm` 目录：

```bash
pip install -e .
```

## 使用示例
```python
from llm.agent import Agent, create_agent_with_tools
from llm.template_parser.template_parser import TemplateParser

agent = create_agent_with_tools([
    lambda a: a,
], logger=False)

result = agent.chat("你好")
print(result["final_response"])
```

## 运行测试
从 `llm` 目录执行：

```bash
./scripts/pytest.sh
```

脚本会自动设置 `PYTHONPATH` 到仓库根目录，确保包 `llm` 可被导入。
