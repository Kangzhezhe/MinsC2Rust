import pytest

from pydantic import BaseModel
from llm.template_parser.template_parser import TemplateParser, MyModel

class NestedModel(BaseModel):
    foo: str
    bar: int

def test_nested_json_model():
    template = "嵌套={nested:json:NestedModel}。"
    llm_output = '嵌套={"foo": "hello", "bar": 99}。'
    parser = TemplateParser(template, model_map={"NestedModel": NestedModel})
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["nested"]["foo"] == "hello"
    assert result["data"]["nested"]["bar"] == 99

def test_empty_json():
    template = "模型={model:json}。"
    llm_output = "模型={}。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["model"] == {}

def test_bool_edge_cases():
    template = "激活={active:bool}。"
    for val in ["True", "true", "1", "False", "false", "0"]:
        llm_output = f"激活={val}。"
        parser = TemplateParser(template)
        result = parser.validate(llm_output)
        assert result["success"]
        if val.lower() in ("true", "1"):
            assert result["data"]["active"] is True
        else:
            assert result["data"]["active"] is False

def test_list_empty_and_single():
    template = "标签={tags:list[str]}。"
    parser = TemplateParser(template)
    result = parser.validate("标签=[\"A\"]。")
    assert result["success"]
    assert result["data"]["tags"] == ["A"]
    result = parser.validate("标签=[ ]。")
    assert result["success"]
    assert result["data"]["tags"] == []

def test_dict_empty():
    template = "配置={config:dict}。"
    parser = TemplateParser(template)
    result = parser.validate("配置={}。")
    assert result["success"]
    assert result["data"]["config"] == {}

def test_any_type():
    template = "任意={data:any}。"
    parser = TemplateParser(template)
    result = parser.validate("任意={\"x\":1,\"y\":2}。")
    assert result["success"]
    assert result["data"]["data"] == {"x": 1, "y": 2}
    result = parser.validate("任意=hello。")
    assert result["success"]
    assert result["data"]["data"] == "hello"

def test_regex_not_match():
    template = "邮箱={email:str:regex=^.+@.+$}。"
    llm_output = "邮箱=not-an-email。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert not result["success"]

def test_missing_field():
    template = "姓名={name:str}，年龄={age:int}。"
    llm_output = "姓名=张三。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert not result["success"]

def test_wrong_format():
    template = "姓名={name:str}，年龄={age:int}。"
    llm_output = "姓名=张三，年龄=abc。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert not result["success"]

def test_extra_field():
    template = "姓名={name:str}。"
    llm_output = "姓名=张三。年龄=18。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["name"] == "张三"


    
def test_multiple_fields():
    template = "姓名={name:str}，年龄={age:int}，邮箱={email:str:regex=^.+@.+$}。"
    llm_output = "姓名=李四，年龄=22，邮箱=li@ex.com。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["name"] == "李四"
    assert result["data"]["age"] == 22
    assert result["data"]["email"] == "li@ex.com"

def test_field_order_wrong():
    template = "姓名={name:str}，年龄={age:int}。"
    llm_output = "年龄=30，姓名=王五。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert not result["success"]

def test_extra_and_missing_fields():
    template = "姓名={name:str}，年龄={age:int}"
    llm_output = "姓名=张三，年龄=18，性别=男。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["name"] == "张三"
    assert result["data"]["age"] == 18

    llm_output_missing = "姓名=张三。"
    result_missing = parser.validate(llm_output_missing)
    assert not result_missing["success"]

def test_special_characters():
    template = "备注={note:str}。"
    llm_output = "备注=特殊字符!@#￥%……&*（）——+。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["note"].startswith("特殊字符")

def test_json_nested():
    template = "嵌套={nested:json:NestedModel}。"
    llm_output = '嵌套={"foo": "hello", "bar": 99}。'
    parser = TemplateParser(template, model_map={"NestedModel": NestedModel})
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["nested"]["foo"] == "hello"
    assert result["data"]["nested"]["bar"] == 99

def test_json_invalid():
    template = "嵌套={nested:json:NestedModel}。"
    llm_output = '嵌套={"foo": 123, "bar": "not_int"}。'
    parser = TemplateParser(template, model_map={"NestedModel": NestedModel})
    result = parser.validate(llm_output)
    assert not result["success"]

def test_empty_str_field():
    template = "备注={note:str}。"
    llm_output = "备注=。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["note"] == ""

def test_list_int():
    template = "数字列表={nums:list[int]}。"
    llm_output = "数字列表=[1,2,3]。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["nums"] == [1, 2, 3]

def test_bool_strict():
    template = "激活={active:bool}。"
    for val in ["yes", "no", "TRUE", "FALSE"]:
        llm_output = f"激活={val}。"
        parser = TemplateParser(template)
        result = parser.validate(llm_output)
        assert result["success"]
        # yes/no/TRUE/FALSE都被当作字符串，只有true/false/1/0才会被转bool

def test_dict_complex():
    template = "配置={config:dict}。"
    llm_output = "配置={\"a\":1,\"b\":{\"c\":2}}。"
    parser = TemplateParser(template)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["config"]["b"]["c"] == 2

def test_any_json_and_str():
    template = "内容={data:any}。"
    parser = TemplateParser(template)
    result = parser.validate("内容={\"x\":1}。")
    assert result["success"]
    assert result["data"]["data"] == {"x": 1}
    result = parser.validate("内容=hello。")
    assert result["success"]
    assert result["data"]["data"] == "hello"

def test_regex_edge():
    template = "邮箱={email:str:regex=^.+@.+$}。"
    parser = TemplateParser(template)
    result = parser.validate("邮箱=abc@def.com。")
    assert result["success"]
    result = parser.validate("邮箱=abc。")
    assert not result["success"]

def test_auto_int_end():
    template = "编号={id:int}"
    parser = TemplateParser(template)
    # 结尾有逗号
    result = parser.validate("编号=123,其他=abc")
    assert result["success"]
    assert result["data"]["id"] == 123
    # 结尾有句号
    result = parser.validate("编号=456。")
    assert result["success"]
    assert result["data"]["id"] == 456
    # 非法数字
    result = parser.validate("编号=abc。")
    assert not result["success"]

def test_auto_float_end():
    template = "分数={score:float}"
    parser = TemplateParser(template)
    result = parser.validate("分数=3.14。")
    assert result["success"]
    assert result["data"]["score"] == 3.14
    result = parser.validate("分数=100,备注=优秀")
    assert result["success"]
    assert result["data"]["score"] == 100.0
    result = parser.validate("分数=abc。")
    assert not result["success"]

def test_auto_bool_end():
    template = "激活={active:bool}"
    parser = TemplateParser(template)
    for val in ["true", "false", "True", "False", "1", "0"]:
        result = parser.validate(f"激活={val}。")
        assert result["success"]
        assert isinstance(result["data"]["active"], bool)

def test_auto_list_end():
    template = "标签={tags:list[str]}"
    parser = TemplateParser(template)
    result = parser.validate("标签=[\"A\",\"B\"]。")
    assert result["success"]
    assert result["data"]["tags"] == ["A", "B"]
    result = parser.validate("标签=[ ]。")
    assert result["success"]
    assert result["data"]["tags"] == []

def test_auto_dict_end():
    template = "配置={config:dict}"
    parser = TemplateParser(template)
    result = parser.validate("配置={\"x\":1,\"y\":2}。")
    assert result["success"]
    assert result["data"]["config"]["x"] == 1
    result = parser.validate("配置={}。")
    assert result["success"]
    assert result["data"]["config"] == {}

def test_auto_any_end():
    template = "内容={data:any}"
    parser = TemplateParser(template)
    result = parser.validate("内容={\"foo\":1}。")
    assert result["success"]
    assert result["data"]["data"]["foo"] == 1

def test_model_auto_end():
    template = "模型={model:json:MyModel}"
    llm_output = '模型={"foo": "hello", "num": "123"}。'
    parser = TemplateParser(template, model_map={"MyModel": MyModel})
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["model"]["foo"] == "hello"
    assert result["data"]["model"]["num"] == "123"

    # 非法模型内容
    llm_output_invalid = '模型={"foo": 123, "num": "abc"}。'
    result_invalid = parser.validate(llm_output_invalid)
    assert not result_invalid["success"]

def test_model_auto_start_end():
    template = "{model:json:MyModel}"
    llm_output = '{"foo": "hello", "num": "123"}。'
    parser = TemplateParser(template, model_map={"MyModel": MyModel})
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["model"]["foo"] == "hello"
    assert result["data"]["model"]["num"] == "123"

    # 非法模型内容
    llm_output_invalid = '{"foo": 123, "num": "abc"}。'
    result_invalid = parser.validate(llm_output_invalid)
    assert not result_invalid["success"]


class SubModel(BaseModel):
    bar: int
    baz: str

class MainModel(BaseModel):
    foo: str
    sub: SubModel

def test_deeply_nested_model():
    template = "主模型={main:json:MainModel}"
    llm_output = '主模型={"foo": "abc", "sub": {"bar": 99, "baz": "hello"}}'
    parser = TemplateParser(template, model_map={"MainModel": MainModel, "SubModel": SubModel})
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["main"]["foo"] == "abc"
    assert result["data"]["main"]["sub"]["bar"] == 99
    assert result["data"]["main"]["sub"]["baz"] == "hello"

def test_multi_level_nested_model():
    class Level3(BaseModel):
        value: int
    class Level2(BaseModel):
        l3: Level3
    class Level1(BaseModel):
        l2: Level2

    template = "嵌套={nested:json:Level1}。"
    llm_output = '嵌套={"l2": {"l3": {"value": 123}}}。'
    parser = TemplateParser(template, model_map={"Level1": Level1, "Level2": Level2, "Level3": Level3})
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["nested"]["l2"]["l3"]["value"] == 123

def test_json_field_with_comma_in_value():
    class ModelWithComma(BaseModel):
        foo: str
        num: int
    template = "数据={data:json:ModelWithComma}。"
    llm_output = '数据={"foo": "A, 1", "num": 1}。'
    parser = TemplateParser(template, model_map={"ModelWithComma": ModelWithComma})
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["data"]["foo"] == "A, 1"
    assert result["data"]["data"]["num"] == 1

def test_json_field_with_bracket_in_value():
    class ModelWithBracket(BaseModel):
        foo: str
        num: int
    template = "数据={data:json:ModelWithBracket}。"
    llm_output = '数据={"foo": "[A]", "num": 2}。'
    parser = TemplateParser(template, model_map={"ModelWithBracket": ModelWithBracket})
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["data"]["foo"] == "[A]"
    assert result["data"]["data"]["num"] == 2

def test_json_field_with_nested_object_and_comma():
    class Nested(BaseModel):
        bar: str
    class ModelWithNested(BaseModel):
        foo: Nested
        num: int
    template = "数据={data:json:ModelWithNested}。"
    llm_output = '数据={"foo": {"bar": "baz, qux"}, "num": 3}。'
    parser = TemplateParser(template, model_map={"ModelWithNested": ModelWithNested, "Nested": Nested})
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["data"]["foo"]["bar"] == "baz, qux"
    assert result["data"]["data"]["num"] == 3