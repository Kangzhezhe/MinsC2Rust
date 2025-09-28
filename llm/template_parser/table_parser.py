import json
from typing import List, Any, Type
from pydantic import BaseModel, ValidationError
import os
import sys
from .template_parser import TemplateParser, MyModel, strip_think_tags


# 每行数据结构，支持int, str ,float等类型
class RowModel(BaseModel):
    foo: str
    num: int

class TableModel(BaseModel):
    rows: List[RowModel]


class TableParser:
    def __init__(self, table_model: Type[BaseModel], value_only: bool = False, skip_on_type_error: bool = True):
        self.table_model = table_model
        self.value_only = value_only
        self.template = f"{{table:json:{table_model.__name__}}}"
        self.skip_on_type_error = skip_on_type_error
        model_map = {table_model.__name__: table_model}
        self.table_field = None
        self.row_model = None
        for name, field in table_model.model_fields.items():
            field_type = field.annotation
            if hasattr(field_type, "__origin__") and field_type.__origin__ == list:
                elem_type = field_type.__args__[0]
                if isinstance(elem_type, type) and issubclass(elem_type, BaseModel):
                    model_map[elem_type.__name__] = elem_type
                    self.table_field = name
                    self.row_model = elem_type
            elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
                model_map[field_type.__name__] = field_type
        self.parser = TemplateParser(self.template, model_map=model_map)

    def validate(self, llm_output: str):
        llm_output = strip_think_tags(llm_output)
        if self.value_only:
            llm_output_1 = {self.table_field: self._parse_value_only(llm_output)}
            llm_output_json = json.dumps(llm_output_1, ensure_ascii=False)
            return self.parser.validate(llm_output_json)
        else:
            return self.parser.validate(llm_output)

    def get_format_instructions(self) -> str:
        if self.value_only:
            headers = list(self.row_model.model_fields.keys())
            example_row = ",".join([f'"{h}值(替换为具体数值)"' if self.row_model.model_fields[h].annotation == str else "1" for h in headers])
            instructions = (
                "请按如下格式输出，仅包含字段值（value），不需要字段名（key）：\n"
                "每一行用大括号包裹，字段顺序严格为：" + ",".join(headers) + "\n"
                "每个字段值之间用英文逗号分隔，字符串请用英文双引号括起来，数字直接填写。\n"
                "例如：\n"
                "{ " + example_row + " }\n"
                "如果有多行，可以用逗号分隔所有大括号，或放在一个列表中，如：\n"
                "{ [" + "{ " + example_row + " }, { " + example_row + " }] }\n"
                "注意：不要返回字段名，只返回字段值，字段顺序必须与上面一致。\n"
                "每一行字段值的数据类型约束如下（仅参考类型约束，不要返回字段名）：\n"
            )
            # 构建 json_schemas 字典
            json_schemas = {}
            json_schemas[self.row_model.__name__] = self.row_model.model_json_schema()
            for name, schema in json_schemas.items():
                instructions += f"\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n"
            return instructions
        else:
            return self.parser.get_format_instructions()

    def get_rows(self, llm_output: str):
        result = self.validate(llm_output)
        if not result["success"]:
            return []
        return result["data"]["table"][self.table_field]

    def _parse_value_only(self, llm_output: str) -> list:
        import re
        matches = re.findall(r"\{([^{}]+)\}", llm_output)
        headers = list(self.row_model.model_fields.keys())
        rows = []
        for m in matches:
            # 支持逗号在引号内的字段
            items = re.findall(r'"[^"]*"|\'[^\']*\'|[^,]+', m)
            items = [x.strip().strip('"').strip("'") for x in items]
            if len(items) > len(headers) and items[-1] == "":
                items = items[:-1]
            if len(items) != len(headers):
                continue
            row = {}
            try:
                for h, v in zip(headers, items):
                    typ = self.row_model.model_fields[h].annotation
                    if typ == int:
                        v = int(v)
                    elif typ == float:
                        v = float(v)
                    row[h] = v
                rows.append(row)
            except Exception as e:
                if self.skip_on_type_error:
                    continue
                else:
                    raise e
        return rows

    def to_tsv(self, llm_output) -> str:
        if isinstance(llm_output, list):
            rows = llm_output
        else:
            rows = self.get_rows(llm_output)
        if not rows:
            return ""
        headers = list(self.row_model.model_fields.keys())
        lines = ["\t".join(headers)]
        for row in rows:
            line = "\t".join(str(row[h]) for h in headers)
            lines.append(line)
        return "\n".join(lines)

    def to_csv(self, llm_output) -> str:
        import csv
        from io import StringIO
        if isinstance(llm_output, list):
            rows = llm_output
        else:
            rows = self.get_rows(llm_output)
        if not rows:
            return ""
        headers = list(self.row_model.model_fields.keys())
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row[h] for h in headers})
        return output.getvalue().strip()

    def to_markdown(self, llm_output) -> str:
        if isinstance(llm_output, list):
            rows = llm_output
        else:
            rows = self.get_rows(llm_output)
        if not rows:
            return ""
        headers = list(self.row_model.model_fields.keys())
        md = "| " + " | ".join(headers) + " |\n"
        md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        for row in rows:
            md += "| " + " | ".join(str(row[h]) for h in headers) + " |\n"
        return md.strip()

    def to_json(self, llm_output) -> str:
        if isinstance(llm_output, list):
            rows = llm_output
        else:
            rows = self.get_rows(llm_output)
        if not rows:
            return json.dumps({self.table_field: []}, ensure_ascii=False)
        return json.dumps({self.table_field: rows}, ensure_ascii=False)


def test_table_parser():
    # llm_output = 'json```{"rows": [{"foo": "A", "num": 1}, {"foo": "B", "num": 2}]}```'
    # table_parser = TableParser(TableModel)

    llm_output = '{ [{"A",1}, {"B",2}] }'
    table_parser = TableParser(TableModel)
    print(table_parser.get_format_instructions())

    print("原始解析：")
    print(table_parser.validate(llm_output))
    print("\nTSV格式：")
    print(table_parser.to_tsv(llm_output))
    print("\nCSV格式：")
    print(table_parser.to_csv(llm_output))
    print("\nMarkdown格式：")
    print(table_parser.to_markdown(llm_output))

if __name__ == "__main__":
    test_table_parser()