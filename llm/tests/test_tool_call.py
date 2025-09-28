import pytest
import json
from llm.tool_call import (
    infer_param_model,
    register_tool,
    call_tool,
    LLMToolCaller,
)

def test_infer_param_model():
    def foo(a: int, b: str): pass
    model = infer_param_model(foo)
    inst = model(a=1, b="x")
    assert inst.a == 1
    assert inst.b == "x"

def test_register_and_call_tool():
    @register_tool("sum")
    def sum_func(a: int, b: int):
        return a + b
    result = call_tool("sum", {"a": 2, "b": 3})
    assert result == 5

def test_llm_tool_caller_basic():
    def add(a: float, b: float): return a + b
    def echo(text: str): return f"你说的是: {text}"
    caller = LLMToolCaller([add, echo])
    # 构造模拟 LLM 输出
    llm_output_add = '{"tool_call": {"name": "add", "args": {"a": 1.5, "b": 2.5}}}'
    llm_output_echo = '{"tool_call": {"name": "echo", "args": {"text": "hello"}}}'
    name, result = caller.call(llm_output_add)
    assert name == "add"
    assert result == 4.0
    name, result = caller.call(llm_output_echo)
    assert name == "echo"
    assert result == "你说的是: hello"

def test_llm_tool_caller_invalid_tool():
    def add(a: float, b: float): return a + b
    caller = LLMToolCaller([add])
    llm_output = '{"tool_call": {"name": "not_exist", "args": {"a": 1, "b": 2}}}'
    name, result = caller.call(llm_output)
    assert name is None
    assert result is None

def test_llm_tool_caller_args_as_str():
    def add(a: int, b: int): return a + b
    caller = LLMToolCaller([add])
    # args 为字符串形式
    llm_output = '{"tool_call": {"name": "add", "args": "{\\"a\\": 2, \\"b\\": 3}"}}'
    name, result = caller.call(llm_output)
    assert name == "add"
    assert result == 5