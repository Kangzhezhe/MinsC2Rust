import inspect
import json
from openai import OpenAI
from llm.ENV import llm_url, llm_api_key, llm_default_model
from llm.template_parser.template_parser import TemplateParser
from pydantic import BaseModel, create_model

tool_registry = {}

def infer_param_model(func):
    """
    根据函数签名自动生成pydantic参数模型
    """
    sig = inspect.signature(func)
    fields = {}
    for name, param in sig.parameters.items():
        ann = param.annotation if param.annotation != inspect.Parameter.empty else str
        # 处理默认值
        if param.default != inspect.Parameter.empty:
            fields[name] = (ann, param.default)
        else:
            fields[name] = (ann, ...)
    model = create_model(f"{func.__name__.capitalize()}Params", **fields)
    return model

def register_tool(name=None):
    """
    装饰器注册工具函数，自动推导参数模型
    """
    def decorator(func):
        tool_name = name or func.__name__
        param_model = infer_param_model(func)
        tool_registry[tool_name] = {"func": func, "param_model": param_model}
        return func
    return decorator

def call_tool(name, args):
    if name not in tool_registry:
        raise ValueError(f"未注册的工具: {name}")
    func = tool_registry[name]["func"]
    param_model = tool_registry[name]["param_model"]
    params = param_model(**args)
    return func(**params.model_dump())

def call_llm(prompt):
    client = OpenAI(
        api_key=llm_api_key,
        base_url=llm_url
    )
    resp = client.chat.completions.create(
        model=llm_default_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    if hasattr(resp, "choices"):
        return resp.choices[0].message.content
    return str(resp)

def build_tool_template(tool_names, param_models):
    """
    构建通用tool_call模板，工具名为{name:str}，参数为所有工具的联合
    直接用参数模型Model构建template，语法使用 {args:json:Model}
    """
    args_examples = []
    for tool_name, param_model in param_models.items():
        args_examples.append(
            f'{tool_name}的args为: {{{param_model.__name__}}}'
        )
    template = '{"tool_call": {"name": {name:str}, "args": {args:json:对应工具参数Model}}}'
    example = '\n'.join(args_examples)
    return template, example


class LLMToolCaller:
    def __init__(self, tools):
        """
        tools: List[function]，每个函数需有类型注解
        """
        self.tool_registry = {}
        for func in tools:
            tool_name = func.__name__
            param_model = infer_param_model(func)
            self.tool_registry[tool_name] = {
                "func": func,
                "param_model": param_model,
                "doc": inspect.getdoc(func) or "",
            }
        self.param_models = {name: info["param_model"] for name, info in self.tool_registry.items()}
        self.template, self.example = build_tool_template(list(self.param_models.keys()), self.param_models)
        self.model_map = {model.__name__: model for model in self.param_models.values()}
        self.parser = TemplateParser(self.template, model_map=self.model_map)
        self.instructions = (
            "\n\n[以下是工具调用格式的说明（可根据情况忽略）]\n"
            + "注意：如果没有任何一个工具能满足你的需求，请直接按原来的要求回复原始内容，不要调用 tool_call, 忽略以下内容，不要在回答中提到工具这件事。\n"
            + "注意：一次只允许调用一个工具，如果回答中包含了多个工具调用，只会执行第一个\n"
            + self.parser.get_format_instructions()
            + "\n不同工具的args示例：\n" + self.example
        )
        tool_docs = []
        for name, info in self.tool_registry.items():
            doc = info["doc"].replace("\n", "\n    ") if info["doc"] else "(无)"
            tool_docs.append(f"- {name}: {doc}")
        if tool_docs:
            self.instructions += "\n\n工具说明：\n" + "\n".join(tool_docs)

    def call(self, llm_output):
        try:
            parsed = self.parser.validate(llm_output)
            if not parsed.get('success', False):
                return None, None
            data = parsed["data"]
            tool_name = data.get("name")
            if isinstance(tool_name, str) and tool_name.startswith('"') and tool_name.endswith('"'):
                tool_name = tool_name[1:-1]
            if tool_name in self.param_models:
                param_model = self.param_models[tool_name]
                tool_args = data.get("args", {})
                if isinstance(tool_args, str):
                    from json_repair import loads
                    tool_args = loads(tool_args)
                params = param_model(**tool_args)
                func = self.tool_registry[tool_name]["func"]
                # print("调用工具:", tool_name, "参数:", params,"结果:", func(**params.model_dump()))
                return tool_name, func(**params.model_dump())
        except Exception as e:
            print("工具解析或调用失败:", e)
            return tool_name, f"工具解析或调用失败: {e}"
        return None, None

    def get_instructions(self):
        return self.instructions





def run_llm_tool_console(tools):
    """
    传入工具函数列表，自动完成 LLM 工具调用交互流程
    """
    caller = LLMToolCaller(tools)
    print("【格式化指令】\n", caller.get_instructions())
    while True:
        user_input = input("用户问题: ").strip()
        if user_input.lower() == "exit":
            break
        prompt = user_input + "\n\n" + caller.get_instructions()
        llm_output = call_llm(prompt)
        print("大模型回复:", llm_output)
        tool_name, tool_result = caller.call(llm_output)
        if tool_result is not None:
            print(f"本地工具调用结果（{tool_name}）:", tool_result)
            print("最终回复:", tool_result)
        else:
            print("最终回复:", llm_output)


if __name__ == "__main__":
    # 示例工具函数（无需手动定义参数模型）
    @register_tool("add")
    def add(a: float, b: float):
        return a + b

    @register_tool("echo")
    def echo(text: str):
        return f"你说的是: {text}"

    @register_tool("multiply")
    def multiply(x: float, y: float):
        return x * y
    # 只允许调用 add、echo、multiply
    run_llm_tool_console([add, echo, multiply])