import os
from openai import OpenAI

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("QWEN_API_KEY")
    if not api_key:
        raise RuntimeError("QWEN_API_KEY is not set")

    _client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=120,
        max_retries=1,
    )
    return _client

def get_response_qianwen(prompt, response_format='text', temperature=0, return_usage=False):
    try:
        client = _get_client()
        request_params = {
            'model': 'deepseek-v3.2',  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            # 'model': 'qwen-coder-plus',  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature,
            'timeout': 300
        }
        
        if response_format == 'json':
            request_params['response_format'] = {"type": "json_object"}
        
        completion = client.chat.completions.create(**request_params)
        content = completion.choices[0].message.content
        usage_obj = getattr(completion, "usage", None)
        usage = {
            "prompt_tokens": int(getattr(usage_obj, "prompt_tokens", 0) or 0),
            "completion_tokens": int(getattr(usage_obj, "completion_tokens", 0) or 0),
            "total_tokens": int(getattr(usage_obj, "total_tokens", 0) or 0),
        }
        if return_usage:
            return {"content": content, "usage": usage}
        return content
    except Exception as e:
        # 捕获异常并返回错误消息
        return f"请求出错: {e}"


def process_completion_qwq(question,response_format='text', temperature=0):
    client = _get_client()
     # 创建聊天完成请求
    completion = client.chat.completions.create(
        model="qwq-plus",  # 此处以 qwq-32b 为例，可按需更换模型名称
        messages=[
            {"role": "user", "content": question}
        ],
        stream=True,
        temperature=temperature
        # 解除以下注释会在最后一个chunk返回Token使用量
        # stream_options={
        #     "include_usage": True
        # }
    )

    reasoning_content = ""  # 定义完整思考过程
    answer_content = ""     # 定义完整回复
    is_answering = False   # 判断是否结束思考过程并开始回复

    for chunk in completion:
        # 如果chunk.choices为空，则打印usage
        if not chunk.choices:
            print("\nUsage:")
            print(chunk.usage)
        else:
            delta = chunk.choices[0].delta
            # 打印思考过程
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                print(delta.reasoning_content, end='', flush=True)
                reasoning_content += delta.reasoning_content
            else:
                # 开始回复
                if delta.content != "" and is_answering is False:
                    # print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                    is_answering = True
                # 打印回复过程
                # print(delta.content, end='', flush=True)
                answer_content += delta.content

    # print("=" * 20 + "完整思考过程" + "=" * 20 + "\n")
    # print(reasoning_content)
    # print("=" * 20 + "完整回复" + "=" * 20 + "\n")
    # print(answer_content)
    return answer_content

if __name__ == '__main__':
    prompt = "你是谁？"
    response = get_response_qianwen(prompt)
    print(response)
