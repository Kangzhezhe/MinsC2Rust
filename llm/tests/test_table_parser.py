import pytest
from pydantic import BaseModel
from llm.template_parser.table_parser import TableParser, RowModel, TableModel

def test_parse_json_table():
    llm_output = '{"rows": [{"foo": "A", "num": 1}, {"foo": "B", "num": 2}]}'
    parser = TableParser(TableModel)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["table"]["rows"][0]["foo"] == "A"
    assert result["data"]["table"]["rows"][1]["num"] == 2

def test_parse_value_only_table():
    llm_output = '{ {"A",1}, {"B",2} }'
    parser = TableParser(TableModel, value_only=True)
    result = parser.validate(llm_output)
    assert result["success"]
    rows = result["data"]["table"]["rows"]
    assert rows[0]["foo"] == "A"
    assert rows[0]["num"] == 1
    assert rows[1]["foo"] == "B"
    assert rows[1]["num"] == 2

def test_tsv_output():
    llm_output = '{ {"A",1}, {"B",2} }'
    parser = TableParser(TableModel, value_only=True)
    tsv = parser.to_tsv(llm_output)
    assert "foo\tnum" in tsv
    assert "A\t1" in tsv
    assert "B\t2" in tsv

def test_csv_output():
    llm_output = '{ {"A",1}, {"B",2} }'
    parser = TableParser(TableModel, value_only=True)
    csv_str = parser.to_csv(llm_output)
    assert "foo,num" in csv_str
    assert "A,1" in csv_str
    assert "B,2" in csv_str

def test_markdown_output():
    llm_output = '{ {"A",1}, {"B",2} }'
    parser = TableParser(TableModel, value_only=True)
    md = parser.to_markdown(llm_output)
    assert "| foo | num |" in md
    assert "| A | 1 |" in md
    assert "| B | 2 |" in md

def test_empty_rows():
    llm_output = ""
    parser = TableParser(TableModel, value_only=True)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["table"]["rows"] == []

def test_wrong_value_count():
    llm_output = '{ {"A"} }'
    parser = TableParser(TableModel, value_only=True)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["table"]["rows"] == []

def test_type_convert_error():
    llm_output = '{ {"A","not_int"} }'
    parser = TableParser(TableModel, value_only=True)
    result = parser.validate(llm_output)
    # num 字段类型转换失败会被跳过
    assert result["success"]
    assert result["data"]["table"]["rows"] == []

def test_extra_spaces_and_quotes():
    llm_output = '{ { "A" , 1 }, { "B" , 2 } }'
    parser = TableParser(TableModel, value_only=True)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["table"]["rows"][0]["foo"] == "A"
    assert result["data"]["table"]["rows"][1]["foo"] == "B"


# 新的行模型
class PersonRowModel(BaseModel):
    name: str
    age: int
    score: float

# 新的表格模型
class PersonTableModel(BaseModel):
    people: list[PersonRowModel]

def test_parse_json_person_table():
    llm_output = '{"people": [{"name": "Tom", "age": 20, "score": 88.5}, {"name": "Lily", "age": 22, "score": 92.0}]}'
    parser = TableParser(PersonTableModel)
    table_field = parser.table_field
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["table"][table_field][0]["name"] == "Tom"
    assert result["data"]["table"][table_field][1]["score"] == 92.0

def test_parse_value_only_person_table():
    llm_output = '{ {"Tom",20,88.5}, {"Lily",22,92.0} }'
    parser = TableParser(PersonTableModel, value_only=True)
    table_field = parser.table_field
    result = parser.validate(llm_output)
    assert result["success"]
    rows = result["data"]["table"][table_field]
    assert rows[0]["name"] == "Tom"
    assert rows[0]["age"] == 20
    assert rows[0]["score"] == 88.5
    assert rows[1]["name"] == "Lily"
    assert rows[1]["score"] == 92.0

def test_person_tsv_output():
    llm_output = '{ {"Tom",20,88.5}, {"Lily",22,92.0} }'
    parser = TableParser(PersonTableModel, value_only=True)
    tsv = parser.to_tsv(llm_output)
    assert "name\tage\tscore" in tsv
    assert "Tom\t20\t88.5" in tsv
    assert "Lily\t22\t92.0" in tsv

def test_person_csv_output():
    llm_output = '{ {"Tom",20,88.5}, {"Lily",22,92.0} }'
    parser = TableParser(PersonTableModel, value_only=True)
    csv_str = parser.to_csv(llm_output)
    assert "name,age,score" in csv_str
    assert "Tom,20,88.5" in csv_str
    assert "Lily,22,92.0" in csv_str

def test_person_markdown_output():
    llm_output = '{ {"Tom",20,88.5}, {"Lily",22,92.0} }'
    parser = TableParser(PersonTableModel, value_only=True)
    md = parser.to_markdown(llm_output)
    assert "| name | age | score |" in md
    assert "| Tom | 20 | 88.5 |" in md
    assert "| Lily | 22 | 92.0 |" in md

def test_person_type_convert_error():
    llm_output = '{ {"Tom","not_int",88.5} }'
    parser = TableParser(PersonTableModel, value_only=True)
    table_field = parser.table_field
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["table"][table_field] == []

def test_to_json_output():
    llm_output = '{ {"A",1}, {"B",2} }'
    parser = TableParser(TableModel, value_only=True)
    json_str = parser.to_json(llm_output)
    import json
    data = json.loads(json_str)
    table_field = parser.table_field
    assert table_field in data
    assert data[table_field][0]["foo"] == "A"
    assert data[table_field][1]["num"] == 2

def test_to_json_empty():
    llm_output = ""
    parser = TableParser(TableModel, value_only=True)
    json_str = parser.to_json(llm_output)
    import json
    data = json.loads(json_str)
    table_field = parser.table_field
    assert table_field in data
    assert data[table_field] == []


def test_json_field_with_comma_in_value():
    # 字段值中包含逗号，不能被分割符截断
    llm_output = '{"rows": [{"foo": "A,1", "num": 1}, {"foo": "B,2", "num": 2}]}'
    parser = TableParser(TableModel)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["table"]["rows"][0]["foo"] == "A,1"
    assert result["data"]["table"]["rows"][1]["foo"] == "B,2"

def test_list_field_with_bracket_in_value():
    # 列表字段值中包含方括号
    llm_output = '{"rows": [{"foo": "[A]", "num": 1}, {"foo": "[B]", "num": 2}]}'
    parser = TableParser(TableModel)
    result = parser.validate(llm_output)
    assert result["success"]
    assert result["data"]["table"]["rows"][0]["foo"] == "[A]"
    assert result["data"]["table"]["rows"][1]["foo"] == "[B]"


def test_list_field_with_comma_in_value_only():
    # value_only模式下，列表字段值中包含逗号
    llm_output = '{ {"A,1",1}, {"B,2",2} }'
    parser = TableParser(TableModel, value_only=True)
    result = parser.validate(llm_output)
    print(result)
    assert result["success"]
    assert result["data"]["table"]["rows"][0]["foo"] == "A,1"
    assert result["data"]["table"]["rows"][1]["foo"] == "B,2"