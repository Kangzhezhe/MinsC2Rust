from zhipuai import ZhipuAI
import os

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        raise RuntimeError("ZHIPU_API_KEY is not set")

    _client = ZhipuAI(api_key=api_key)
    return _client

def get_response_zhipu(prompt):
    model = "glm-4-plus"
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        # 解析并返回结果
        return response.choices[0].message.content
    except Exception as e:
        # 捕获异常并返回错误消息
        return f"请求出错: {e}"

if __name__ == "__main__":
    prompt = "你是谁"
    result = get_response_zhipu(prompt)
    print(result)
