import pytest
from pydantic import BaseModel
import os
import sys
from llm.template_parser.template_parser import TemplateParser, MyModel

import os
from llm.ENV import llm_url, llm_api_key, llm_default_model
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    base_url=llm_url,
    api_key=llm_api_key,
    model=llm_default_model,
    temperature=0.3
)

@pytest.mark.parametrize("prompt_suffix,check", [
    ("\n请输出一组示例数据。", lambda r: r["success"] and r["data"]["model"]["foo"]),
    ("\n请输出模型字段foo为test，num为999的内容。", lambda r: r["success"] and r["data"]["model"]["foo"] == "test" and r["data"]["model"]["num"] == "999")
])
def test_llm_model_parse(prompt_suffix, check):
    template = "模型={model:json:MyModel}"
    parser = TemplateParser(template, model_map={"MyModel": MyModel})
    instructions = parser.get_format_instructions()
    prompt = instructions + prompt_suffix
    response = llm.invoke(prompt)
    llm_output = response.content
    print("LLM输出：", llm_output)
    result = parser.validate(llm_output)
    print("解析结果：", result)
    assert check(result)

def test_llm_model_extra_fields():
    template = "模型={model:json:MyModel}"
    parser = TemplateParser(template, model_map={"MyModel": MyModel})
    instructions = parser.get_format_instructions()
    prompt = instructions + "\n请输出模型内容并多加一个字段extra。"
    response = llm.invoke(prompt)
    llm_output = response.content
    result = parser.validate(llm_output)
    print("多字段解析结果：", result)
    assert result["success"]
    assert "foo" in result["data"]["model"]

def test_llm_model_with_list_and_dict():
    class ListDictModel(BaseModel):
        items: list
        config: dict
    template = "数据={data:json:ListDictModel}"
    parser = TemplateParser(template, model_map={"ListDictModel": ListDictModel})
    instructions = parser.get_format_instructions()
    prompt = instructions + "\n请输出items为[1,2,3]，config为{\"a\":1,\"b\":2}的内容。"
    response = llm.invoke(prompt)
    llm_output = response.content
    result = parser.validate(llm_output)
    print("列表和字典解析结果：", result)
    assert result["success"]
    assert result["data"]["data"]["items"] == [1,2,3]
    assert result["data"]["data"]["config"]["a"] == 1

def test_llm_model_with_bool_and_float():
    class BoolFloatModel(BaseModel):
        flag: bool
        score: float
    template = "结果={result:json:BoolFloatModel}"
    parser = TemplateParser(template, model_map={"BoolFloatModel": BoolFloatModel})
    instructions = parser.get_format_instructions()
    prompt = instructions + "\n请输出flag为true，score为3.14的内容。"
    response = llm.invoke(prompt)
    llm_output = response.content
    result = parser.validate(llm_output)
    print("布尔和浮点解析结果：", result)
    assert result["success"]
    assert result["data"]["result"]["flag"] is True
    assert abs(result["data"]["result"]["score"] - 3.14) < 1e-6

def test_llm_model_nested_model():
    class SubModel(BaseModel):
        bar: int
    class MainModel(BaseModel):
        foo: str
        sub: SubModel
    template = "主模型={main:json:MainModel}"
    parser = TemplateParser(template, model_map={"MainModel": MainModel, "SubModel": SubModel})
    instructions = parser.get_format_instructions()
    prompt = instructions + "\n请输出foo为abc，sub为{\"bar\": 99}的内容。"
    response = llm.invoke(prompt)
    llm_output = response.content
    result = parser.validate(llm_output)
    print("嵌套模型解析结果：", result)
    assert result["success"]
    assert result["data"]["main"]["foo"] == "abc"
    assert result["data"]["main"]["sub"]["bar"] == 99

def test_llm_model_multiple_fields():
    template = "姓名={name:str},年龄={age:int},模型={model:json:MyModel},激活={active:bool}"
    parser = TemplateParser(template, model_map={"MyModel": MyModel})
    instructions = parser.get_format_instructions()
    prompt = instructions + "\n请输出姓名为张三，年龄为18，模型foo为bar，num为1，激活为true的内容。"
    response = llm.invoke(prompt)
    llm_output = response.content
    result = parser.validate(llm_output)
    print("多字段解析结果：", result)
    assert result["success"]
    assert result["data"]["name"] == "张三"
    assert result["data"]["age"] == 18
    assert result["data"]["model"]["foo"] == "bar"
    assert result["data"]["active"] is True

def test_llm_model_str_with_punctuation():
    template = "备注={note:str}"
    parser = TemplateParser(template)
    instructions = parser.get_format_instructions()
    prompt = instructions + "\n请输出备注内容为“测试，包含标点！@#￥%……&*（）——+”。"
    response = llm.invoke(prompt)
    llm_output = response.content
    result = parser.validate(llm_output)
    print("字符串标点解析结果：", result)
    assert result["success"]
    assert "标点" in result["data"]["note"]