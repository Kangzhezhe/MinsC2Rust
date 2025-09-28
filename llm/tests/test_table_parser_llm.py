import pytest
from pydantic import BaseModel
from llm.template_parser.table_parser import TableParser, RowModel, TableModel

from llm.ENV import llm_url, llm_api_key, llm_default_model
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    base_url=llm_url,
    api_key=llm_api_key,
    model=llm_default_model,
    temperature=0.3
)

@pytest.mark.parametrize("value_only,prompt_suffix,check", [
    (False, "\n请输出一组表格数据。", lambda r, parser: r["success"] and r["data"]["table"][parser.table_field][0]["foo"]),
    (True, "\n请输出一组表格数据。", lambda r, parser: r["success"] and r["data"]["table"][parser.table_field][0]["foo"]),
    (True, "\n请输出foo为test，num为999的内容。", lambda r, parser: r["success"] and r["data"]["table"][parser.table_field][0]["foo"] == "test" and r["data"]["table"][parser.table_field][0]["num"] == 999),
])
def test_llm_table_parse(value_only, prompt_suffix, check):
    parser = TableParser(TableModel, value_only=value_only)
    instructions = parser.get_format_instructions()
    prompt = instructions + prompt_suffix
    response = llm.invoke(prompt)
    llm_output = response.content
    print("LLM输出：", llm_output)
    result = parser.validate(llm_output)
    print("解析结果：", result)
    assert check(result, parser)



def test_llm_table_empty():
    parser = TableParser(TableModel)
    instructions = parser.get_format_instructions()
    prompt = instructions + "\n请输出一个空表格。"
    response = llm.invoke(prompt)
    llm_output = response.content
    result = parser.validate(llm_output)
    print("空表格解析结果：", result)
    assert result["success"]
    assert result["data"]["table"][parser.table_field] == []



def test_llm_table_nested_dict():
    class ComplexRowModel(BaseModel):
        foo: str
        num: int
        meta: dict

    class ComplexTableModel(BaseModel):
        rows: list[ComplexRowModel]

    parser = TableParser(ComplexTableModel)
    instructions = parser.get_format_instructions()
    prompt = instructions + "\n请输出包含meta字段（为字典）的表格内容。"
    response = llm.invoke(prompt)
    llm_output = response.content
    result = parser.validate(llm_output)
    print("嵌套dict解析结果：", result)
    assert result["success"]
    assert "meta" in result["data"]["table"][parser.table_field][0]

def test_llm_table_large_rows():
    parser = TableParser(TableModel)
    instructions = parser.get_format_instructions()
    prompt = instructions + "\n请输出10行以上的表格内容。"
    response = llm.invoke(prompt)
    llm_output = response.content
    result = parser.validate(llm_output)
    print("大量行解析结果：", result)
    assert result["success"]
    assert len(result["data"]["table"][parser.table_field]) >= 10



def test_llm_table_mixed_types():
    parser = TableParser(TableModel)
    instructions = parser.get_format_instructions()
    prompt = instructions + "\n请输出num字段有字符串和数字混合的表格内容。"
    response = llm.invoke(prompt)
    llm_output = response.content
    result = parser.validate(llm_output)
    print("混合类型解析结果：", result)
    # 这里可以根据你的解析容错策略断言 success 或 fail