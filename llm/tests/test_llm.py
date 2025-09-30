from pydantic import BaseModel
import pytest
from llm.llm import LLM
from llm.template_parser.template_parser import TemplateParser, MyModel
from llm.template_parser.table_parser import TableModel, TableParser

def test_model_call():
    llm = LLM()
    answer = llm.call("你是谁")
    assert isinstance(answer, str) or isinstance(answer, dict)
    assert answer  # 非空

def test_structured_output():
    llm = LLM()
    template = "姓名={name:str}，年龄={age:int}，模型={model:json:MyModel}，激活={active:bool}"
    parser = TemplateParser(template, model_map={"MyModel": MyModel})
    result = llm.call("请输出一个用户信息示例", parser=parser)
    assert isinstance(result, dict)
    assert result.get("success", True)
    assert "name" in result.get("data", {})
    assert "age" in result.get("data", {})

def test_table_output():
    llm = LLM()
    table_parser = TableParser(TableModel, value_only=True)
    result = llm.call("请输出10行以上的表格内容。", parser=table_parser)
    print(result)
    assert isinstance(result, dict)
    assert result.get("success", True)
    assert "table" in result.get("data", {})
    rows = result["data"]["table"]["rows"]
    assert isinstance(rows, list)
    # 测试格式化输出
    # assert table_parser.to_tsv(rows)
    # assert table_parser.to_csv(rows)
    # assert table_parser.to_markdown(rows)
    # assert table_parser.to_json(rows)


def test_table_output_with_extra_fields():
    llm = LLM()
    # 表格包含额外字段
    class ExtraRowModel(BaseModel):
        index: int
        module: str
        requirement: str
        owner: str
        priority: int
    class ExtraTableModel(BaseModel):
        rows: list[ExtraRowModel]
    table_parser = TableParser(ExtraTableModel, value_only=True)
    prompt = "请输出一个需求表格，包含序号、模块、需求点、负责人和优先级。"
    result = llm.call(prompt, parser=table_parser)
    assert isinstance(result, dict)
    assert result.get("success", True)
    rows = result["data"]["table"]["rows"]
    assert isinstance(rows, list)
    for row in rows:
        assert "owner" in row
        assert "priority" in row

def test_table_output_empty():
    llm = LLM()
    table_parser = TableParser(TableModel, value_only=True)
    result = llm.call("请输出一个空表格。", parser=table_parser)
    assert isinstance(result, dict)
    assert result.get("success", True)
    rows = result["data"]["table"]["rows"]
    assert isinstance(rows, list)
    # 允许空表格
    assert len(rows) == 0 or rows is not None


def test_tool_call_add():
    from llm.llm import LLM
    from llm.tool_call import LLMToolCaller

    def add(a: float, b: float) -> float:
        return a + b

    def echo(text: str) -> str:
        return text

    def multiply(a: float, b: float) -> float:
        return a * b

    caller = LLMToolCaller([add, echo, multiply])
    llm = LLM()
    result = llm.call("请帮我计算 3 加 5", caller=caller)
    assert isinstance(result, dict)
    assert result.get("tool_name") == "add"
    assert result.get("tool_result") == 8.0

def test_tool_call_echo():
    from llm.llm import LLM
    from llm.tool_call import LLMToolCaller

    def echo(text: str) -> str:
        return text

    caller = LLMToolCaller([echo])
    llm = LLM()
    result = llm.call("请使用工具输出：你好", caller=caller)
    assert isinstance(result, dict)
    assert result.get("tool_name") == "echo"
    assert "你好" in result.get("tool_result", "")