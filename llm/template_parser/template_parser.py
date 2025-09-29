import datetime
import re
import json
from typing import List, Dict, Any, get_origin, get_args
from pydantic import create_model, ValidationError, constr, BaseModel
from pydantic.json_schema import JsonSchemaValue
from jsonschema import validate as jsonschema_validate, ValidationError as JsonSchemaError

def strip_think_tags(text: str) -> str:
    """
    移除所有 <think>...</think> 段（包含内部内容）以及孤立的 <think> / </think> 标签，
    并清理前后多余空白。使用示例： cleaned = strip_think_tags(raw_output)
    """
    if not text:
        return text
    # 删除成对的 <think>...</think>（非贪婪、跨行）
    cleaned = re.sub(r'(?is)<think>.*?</think>', '', text)
    # 删除任何残留的孤立 think 标签
    cleaned = re.sub(r'(?i)</?think\s*/?>', '', cleaned)
    # 去除前后及多余空白行
    return "\n".join(line for line in (l.rstrip() for l in cleaned.splitlines()) if line).strip()


def _schema_to_example(schema: dict, model_cls: type = None):
    """从 json-schema 递归生成示例数据（优先 examples/default，支持 $ref/$defs, anyOf/oneOf 等）。

    参数:
        schema: 当前要生成示例的 schema 节点，通常来自 BaseModel.model_json_schema()
    返回:
        对应的示例数据（Python 值），无法推断时返回 None。
    """
    def resolve_ref(sch, root):
        ref = sch.get("$ref")
        if not ref or not ref.startswith("#/"):
            return sch
        parts = ref.lstrip("#/").split("/")
        node = root
        for p in parts:
            if p in node:
                node = node[p]
            else:
                return sch
        return node

    def _inner(sch, root):
        if not isinstance(sch, dict):
            return None
        # 优先 examples / default
        if "examples" in sch and sch["examples"]:
            return sch["examples"][0]
        if "default" in sch:
            return sch["default"]

        # 处理 $ref
        if "$ref" in sch:
            resolved = resolve_ref(sch, root)
            if resolved is not sch:
                return _inner(resolved, root)

        # anyOf/oneOf/allOf 取第一个分支尝试
        for key in ("anyOf", "oneOf", "allOf"):
            if key in sch and isinstance(sch[key], list) and sch[key]:
                return _inner(sch[key][0], root)

        # enum 优先
        if "enum" in sch and sch["enum"]:
            return sch["enum"][0]

        t = sch.get("type")
        # 当没有 type 时，如果有 properties 或 $defs，按 object 处理
        if not t and ("properties" in sch or "$defs" in sch or "definitions" in sch):
            t = "object"

        if t == "object":
            props = sch.get("properties", {})
            obj = {}
            for k, v in props.items():
                # 递归时传入 root（最顶层 schema）以便解析 $ref
                val = _inner(v, root)
                if val is None:
                    # 如果 v 是 anyOf/oneOf/allOf，尝试各分支
                    for union_key in ("anyOf", "oneOf", "allOf"):
                        if union_key in v and isinstance(v[union_key], list):
                            for branch in v[union_key]:
                                branch_val = _inner(branch, root)
                                if branch_val is not None:
                                    val = branch_val
                                    break
                            if val is not None:
                                break

                    # 仍然为 None 时尝试解析 $ref
                    if val is None and isinstance(v, dict) and "$ref" in v:
                        resolved = resolve_ref(v, root)
                        val = _inner(resolved, root)

                    # 最后按 type 回退为合理占位，避免返回空 dict 导致校验失败
                    if val is None:
                        vt = v.get("type") if isinstance(v, dict) else None
                        if vt == "string":
                            val = "示例"
                        elif vt == "integer":
                            val = 0
                        elif vt == "number":
                            val = 0.0
                        elif vt == "boolean":
                            val = True
                        elif vt == "array":
                            items = v.get("items", {}) if isinstance(v, dict) else {}
                            item_example = _inner(items, root)
                            if item_example is None:
                                item_example = {}
                            val = [item_example]
                        else:
                            # 无法推断时使用通用占位（非 dict）
                            val = "示例"
                obj[k] = val
            return obj

        if t == "array":
            # 支持 tuple-style schema (prefixItems) 和 items 作为列表
            result = []
            # 优先处理 prefixItems（固定位置的 tuple 元素）
            if "prefixItems" in sch and isinstance(sch["prefixItems"], list):
                for pi in sch["prefixItems"]:
                    ie = _inner(pi, root)
                    if ie is None:
                        # 尝试解析 $ref
                        if isinstance(pi, dict) and "$ref" in pi:
                            ie = _inner(resolve_ref(pi, root), root)
                    # 最后回退为合适占位（非空），避免 {} 导致校验失败
                    if ie is None:
                        if isinstance(pi, dict) and pi.get("type") == "string":
                            ie = "示例"
                        elif isinstance(pi, dict) and pi.get("type") in ("integer", "number"):
                            ie = 0
                        else:
                            ie = "示例"
                    result.append(ie)
                return result

            items = sch.get("items")
            # items 可以是列表（tuple 的后续 items）或 dict
            if isinstance(items, list):
                for it in items:
                    ie = _inner(it, root)
                    if ie is None and isinstance(it, dict) and "$ref" in it:
                        ie = _inner(resolve_ref(it, root), root)
                    if ie is None:
                        # 按 type 回退
                        vt = it.get("type") if isinstance(it, dict) else None
                        if vt == "string":
                            ie = "示例"
                        elif vt in ("integer", "number"):
                            ie = 0
                        else:
                            ie = "示例"
                    result.append(ie)
                return result

            # items 为 dict 或缺失，使用单一 item 构造
            if isinstance(items, dict):
                item_example = _inner(items, root)
                if item_example is None and "$ref" in items:
                    item_example = _inner(resolve_ref(items, root), root)
                if item_example is None:
                    # 尝试用 properties 构造对象示例
                    if isinstance(items, dict) and ("properties" in items or "$ref" in items):
                        # 若 items 描述对象但 _inner 未返回，尝试构造对象字段示例
                        props = items.get("properties", {})
                        obj = {}
                        for k, v in props.items():
                            val = _inner(v, root)
                            if val is None:
                                vt = v.get("type") if isinstance(v, dict) else None
                                if vt == "string":
                                    val = "示例"
                                elif vt in ("integer", "number"):
                                    val = 0
                                elif vt == "array":
                                    val = []
                                else:
                                    val = "示例"
                            obj[k] = val
                        item_example = obj
                    else:
                        item_example = {}
                # respect minItems
                min_items = sch.get("minItems", 1)
                count = max(1, min_items)
                return [item_example for _ in range(count)]

            # 无 items 定义，返回空列表
            return []

        if t == "string":
            fmt = sch.get("format")
            if fmt == "date":
                return datetime.date.today().isoformat()
            return "示例内容"
        if t == "integer":
            return 42
        if t == "number":
            return 3.14
        if t == "boolean":
            return True

        return None

    # 顶层 root 使用 schema 本身（通常含 $defs）
    example = _inner(schema, schema)
    # 如果提供了对应的 Pydantic model，则用 model_validate 做一次严格校验
    if model_cls is not None and example is not None:
        try:
            # pydantic v2: model_validate
            model_cls.model_validate(example)
        except Exception:
            return None
    return example

# 示例 pydantic 子模型
class MyModel(BaseModel):
    foo: str
    num: str

class TemplateParser:
    def __init__(self, template, model_map=None):
        self.template = template
        self.model_map = model_map or {}
        self.fields, self.segments = self.parse_template(template, model_map)
        self.DynamicModel = create_model('DynamicModel', **self.fields)

    @staticmethod
    def parse_template(template, model_map=None):
        pattern = r"\{(\w+):(\w+(\[[^\]]+\])?)(:regex=([^\}:]+))?(?::(\w+))?\}"
        fields = {}
        segments = []
        last_end = 0
        type_map = {
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list[str]": List[str],
            "list[int]": List[int],
            "dict": dict,
            "json": Any,
            "any": Any,
        }
        for m in re.finditer(pattern, template):
            name, typ, _, _, regex, model_name = m.groups()
            segments.append(template[last_end:m.start()])
            last_end = m.end()
            if typ == "str" and regex:
                fields[name] = (constr(pattern=regex), ...)
            elif typ == "json" and model_name and model_map and model_name in model_map:
                fields[name] = (model_map[model_name], ...)
            elif typ in type_map:
                fields[name] = (type_map[typ], ...)
            else:
                fields[name] = (str, ...)
        segments.append(template[last_end:])
        return fields, segments

    def locate_template_segment(self, llm_output):
        start_str = self.segments[0]
        end_str = self.segments[-1]
        start_idx = llm_output.find(start_str)
        if start_idx == -1:
            raise ValueError(f"输出中未找到模板起始标识 '{start_str}'")
        if end_str:
            end_idx = llm_output.rfind(end_str, start_idx)
            if end_idx == -1:
                raise ValueError(f"输出中未找到模板结尾标识 '{end_str}'")
            return llm_output[start_idx:end_idx + len(end_str)]
        else:
            return llm_output[start_idx:]

    def strict_parse_llm_output(self, matched_output):
        result = {}
        idx = 0
        for i, name in enumerate(self.fields.keys()):
            seg_start = self.segments[i]
            seg_end = self.segments[i+1]
            typ = self.fields[name][0]
            if seg_start:
                if not matched_output.startswith(seg_start, idx):
                    raise ValueError(f"输出格式错误，期望 '{seg_start}'")
                idx += len(seg_start)
            else:
                # seg_start 为空时，根据类型自动定位
                if typ == int:
                    m = re.search(r"\d+", matched_output[idx:])
                    if m:
                        idx += m.start()
                    else:
                        raise ValueError(f"未找到字段 {name} 的整数值")
                elif typ == float:
                    m = re.search(r"\d+(\.\d+)?", matched_output[idx:])
                    if m:
                        idx += m.start()
                    else:
                        raise ValueError(f"未找到字段 {name} 的浮点值")
                elif typ == bool:
                    m = re.search(r"(true|false|True|False|1|0)", matched_output[idx:])
                    if m:
                        idx += m.start()
                    else:
                        raise ValueError(f"未找到字段 {name} 的布尔值")
                elif typ in [List[str], List[int]]:
                    m = re.search(r"\[.*?\]", matched_output[idx:])
                    if m:
                        idx += m.start()
                    else:
                        raise ValueError(f"未找到字段 {name} 的列表值")
                elif typ == dict or typ == Any or (isinstance(typ, type) and issubclass(typ, BaseModel)):
                    m = re.search(r"\{.*\}", matched_output[idx:], re.DOTALL)
                    if m:
                        idx += m.start()
                    else:
                        raise ValueError(f"未找到字段 {name} 的 JSON/dict 值")

            if seg_end:
                remain = matched_output[idx:]
                # 优先处理复杂类型
                if (typ == dict or typ == Any or (isinstance(typ, type) and issubclass(typ, BaseModel))) and remain.startswith("{"):
                    count = 0
                    for i, c in enumerate(remain):
                        if c == "{":
                            count += 1
                        elif c == "}":
                            count -= 1
                            if count == 0:
                                value = remain[:i+1].strip()
                                idx += i+1
                                break
                    else:
                        # 没有闭合，退回分割符处理
                        next_pos = remain.find(seg_end)
                        if next_pos == -1:
                            raise ValueError(f"输出格式错误，缺少 '{seg_end}'")
                        value = remain[:next_pos].strip()
                        idx += next_pos
                elif typ in [List[str], List[int]] and remain.startswith("["):
                    count = 0
                    for i, c in enumerate(remain):
                        if c == "[":
                            count += 1
                        elif c == "]":
                            count -= 1
                            if count == 0:
                                value = remain[:i+1].strip()
                                idx += i+1
                                break
                    else:
                        next_pos = remain.find(seg_end)
                        if next_pos == -1:
                            raise ValueError(f"输出格式错误，缺少 '{seg_end}'")
                        value = remain[:next_pos].strip()
                        idx += next_pos
                else:
                    # 统一用分割符处理
                    next_pos = remain.find(seg_end)
                    if next_pos == -1:
                        raise ValueError(f"输出格式错误，缺少 '{seg_end}'")
                    value = remain[:next_pos].strip()
                    idx += next_pos
            else:
                # 自动识别类型结尾
                remain = matched_output[idx:]
                if typ == int:
                    m = re.match(r"^(\d+)", remain)
                    if m:
                        value = m.group(1)
                        idx += len(value)
                    else:
                        raise ValueError(f"结尾字段 {name} 不是合法整数")
                elif typ == float:
                    m = re.match(r"^(\d+(\.\d+)?)", remain)
                    if m:
                        value = m.group(1)
                        idx += len(value)
                    else:
                        raise ValueError(f"结尾字段 {name} 不是合法浮点数")
                elif typ == bool:
                    m = re.match(r"^(true|false|True|False|1|0)", remain)
                    if m:
                        value = m.group(1)
                        idx += len(value)
                    else:
                        value = remain.strip()
                        idx = len(matched_output)
                elif typ in [List[str], List[int]]:
                    # 匹配列表内容，遇到第一个闭合方括号
                    m = re.match(r"^(\[.*?\])", remain)
                    if m:
                        value = m.group(1)
                        idx += len(value)
                    else:
                        raise ValueError(f"结尾字段 {name} 不是合法列表")
                elif typ == dict or typ == Any or (isinstance(typ, type) and issubclass(typ, BaseModel)):
                    # 用括号计数法提取完整 JSON
                    remain = matched_output[idx:]
                    if remain.startswith("{"):
                        count = 0
                        for i, c in enumerate(remain):
                            if c == "{":
                                count += 1
                            elif c == "}":
                                count -= 1
                                if count == 0:
                                    value = remain[:i+1]
                                    idx += i+1
                                    break
                        else:
                            # 没有闭合
                            value = remain.strip()
                            idx = len(matched_output)
                else:
                    # 默认取剩余内容
                    value = remain.strip()
                    idx = len(matched_output)
            result[name] = value
        # 自动类型转换和嵌套模型校验
        for name, field in self.fields.items():
            typ = field[0]
            val = result[name]
            if isinstance(typ, type) and issubclass(typ, BaseModel):
                try:
                    json_obj = json.loads(val)
                    # 严格用 jsonschema 校验
                    schema: JsonSchemaValue = typ.model_json_schema()
                    jsonschema_validate(instance=json_obj, schema=schema)
                    result[name] = typ.model_validate(json_obj)
                except (JsonSchemaError, Exception) as e:
                    # 尝试使用 json_repair 修复非标准 JSON 字符串
                    try:
                        from json_repair import repair_json  # type: ignore
                        repaired = repair_json(val,skip_json_loads=True)
                        json_obj = json.loads(repaired)
                        schema: JsonSchemaValue = typ.model_json_schema()
                        jsonschema_validate(instance=json_obj, schema=schema)
                        result[name] = typ.model_validate(json_obj)
                        # print(f"[TemplateParser] 字段 {name} 使用 json_repair 修复后解析成功。")
                        continue
                    except Exception:
                        pass
                    raise ValueError(f"字段 {name} 不符合 schema: {e}")
            elif typ == bool:
                if isinstance(val, str):
                    if val.lower() in ("true", "1"):
                        result[name] = True
                    elif val.lower() in ("false", "0"):
                        result[name] = False
            elif typ in [List[str], List[int], dict]:
                try:
                    result[name] = eval(val)
                except Exception:
                    pass
            elif typ == Any:
                try:
                    result[name] = json.loads(val)
                except Exception:
                    result[name] = val
        return result

    def validate(self, llm_output):
        llm_output = strip_think_tags(llm_output)
        # 如果模板起始段为空，则直接尝试对整个输出进行严格解析一次
        start_str = self.segments[0]
        end_str = self.segments[-1]

        last_err = None
        last_candidate = None

        # 如果起始标识为空，直接尝试全文解析一次
        if not start_str:
            try:
                matched_output = llm_output
                data = self.strict_parse_llm_output(matched_output)
                validated = self.DynamicModel(**data)
                return {
                    "success": True,
                    "data": validated.model_dump(),
                    "matched_output": matched_output,
                    "raw_output": llm_output
                }
            except (ValidationError, ValueError) as e:
                return {
                    "success": False,
                    "data": str(e),
                    "matched_output": llm_output,
                    "raw_output": llm_output
                }

        # 查找所有可能的起始位置，逐个尝试
        matches = [m for m in re.finditer(re.escape(start_str), llm_output)]
        # for m in reversed(matches):
        for m in matches:
            start_idx = m.start()
            # 定位对应的结尾位置
            if end_str:
                end_idx = llm_output.rfind(end_str, start_idx)
                if end_idx == -1:
                    # 没有找到对应结尾，跳过该起始位置
                    continue
                candidate = llm_output[start_idx:end_idx + len(end_str)]
            else:
                candidate = llm_output[start_idx:]

            last_candidate = candidate
            try:
                data = self.strict_parse_llm_output(candidate)
                validated = self.DynamicModel(**data)
                return {
                    "success": True,
                    "data": validated.model_dump(),
                    "matched_output": candidate,
                    "raw_output": llm_output
                }
            except (ValidationError, ValueError) as e:
                last_err = e
                # 尝试下一个可能的起始位置
                continue

        # 如果所有候选位置都尝试失败，返回最后一次错误信息
        if last_err is not None:
            return {
                "success": False,
                "data": str(last_err),
                "matched_output": last_candidate,
                "raw_output": llm_output
            }
        else:
            # 未找到任何起始标识或结尾标识
            return {
                "success": False,
                "data": f"输出中未找到模板起始标识 '{start_str}' 或模板结尾 '{end_str}'",
                "matched_output": None,
                "raw_output": llm_output
            }

    def get_format_instructions(self):
        instructions = (
            "请严格按照如下格式输出，直接输出指定输出格式的内容，不要输出任何解释或者思考的文本：\n"
            "变量值需替换模板中的变量定义部分（如 {name:str}），其他内容保持所有字符完全一致，包括所有标点符号，换行符，缩进及其中英文差别\n"
            "例如：\"姓名={name:str}，年龄={age:int}。\"替换为\"姓名=张三，年龄=18。\"\n"
            "如遇 json 类型变量，请直接嵌入合法 JSON，特殊字符需正确转义，需严格符合指定的 schema 格式。\n\n"
            "模板如下：\n"
            f"{self.template}\n\n"
            "输出的格式示例如下：\n"
        )
        example = self.template
        example_values = {
            "int": "42",
            "float": "3.14",
            "str": "示例内容",
            "bool": "true",
            "list[str]": "[\"A\", \"B\"]",
            "list[int]": "[1, 2]",
            "dict": "{\"key\": \"value\"}",
            "json": "{\"foo\": \"bar\", \"num\": 1}",
            "any": "{\"foo\": \"bar\"}"
        }
        for name, field in self.fields.items():
            typ = field[0]
            origin = get_origin(typ)
            args = get_args(typ)
            # BaseModel 子类
            if isinstance(typ, type) and issubclass(typ, BaseModel):
                # 使用全局的 schema -> example 生成更准确的示例值
                try:
                    schema = typ.model_json_schema()
                    example_obj = _schema_to_example(schema, typ)
                    if example_obj is None:
                        fields = list(typ.model_fields.keys())
                        value_dict = {f: f"示例值" for f in fields}
                        value = json.dumps(value_dict, ensure_ascii=False)
                    else:
                        value = json.dumps(example_obj, ensure_ascii=False)
                except Exception:
                    fields = list(typ.model_fields.keys())
                    value_dict = {f: f"示例值" for f in fields}
                    value = json.dumps(value_dict, ensure_ascii=False)
            # typing.List / list
            elif origin in (list, List) or typ is list:
                item_type = args[0] if args else None
                if item_type == str:
                    value = example_values["list[str]"]
                elif item_type == int:
                    value = example_values["list[int]"]
                else:
                    value = "[...]"
            # typing.Dict / dict
            elif origin in (dict, Dict) or typ is dict:
                value = example_values["dict"]
            # typing.Any
            elif typ is Any:
                value = example_values["json"]
            # 原始类型 int/float/str/bool
            elif typ in (int,):
                value = example_values["int"]
            elif typ in (float,):
                value = example_values["float"]
            elif typ in (bool,):
                value = example_values["bool"]
            elif typ in (str,):
                value = example_values["str"]
            else:
                # 兜底
                value = "示例内容"
            example = re.sub(rf"\{{{name}:[^\}}]+\}}", value, example)
        instructions +=  example 
        if self.model_map:
            instructions += "\n所有可用 json 类型变量的 schema 如下：\n"
            for model_name, model_cls in self.model_map.items():
                if issubclass(model_cls, BaseModel):
                    schema = model_cls.model_json_schema()
                    instructions += f"{model_name} 的 schema:\n{json.dumps(schema, ensure_ascii=False)}\n"
        return instructions



if __name__ == "__main__":
    class ListDictModel(BaseModel):
            items: list
            config: dict
    template = "数据={data:json:ListDictModel}"
    # template = "模型={model:json:MyModel}"
    # llm_output = '模型={"foo": "hello", "num": "123"}。'
    # llm_output = '数据={"items": [1, 2, 3], "config": {"a": 1, "b": 2}}'
    llm_output = '姓名=张三，年龄=18，模型={"foo": "bar", "num": "1"}， 激活=true'
    template = "姓名={name:str}，年龄={age:int}，模型={model:json:MyModel}，激活={active:bool}"
    parser = TemplateParser(template, model_map={"MyModel": MyModel})
    # validator = TemplateParser(template, model_map={"ListDictModel": ListDictModel})
    print(parser.get_format_instructions())
    result = parser.validate(llm_output)
    print(result)