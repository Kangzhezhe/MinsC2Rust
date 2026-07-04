# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI
import os

import requests

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set")

    _client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=120, max_retries=1)
    return _client

def get_response_deepseek(prompt, temperature=0, return_usage=False):
    client = _get_client()
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": prompt},
        ],
        stream=False,
        max_tokens=8192,
        temperature=temperature
    )

    content = response.choices[0].message.content
    usage_obj = getattr(response, "usage", None)
    usage = {
        "prompt_tokens": int(getattr(usage_obj, "prompt_tokens", 0) or 0),
        "completion_tokens": int(getattr(usage_obj, "completion_tokens", 0) or 0),
        "total_tokens": int(getattr(usage_obj, "total_tokens", 0) or 0),
    }
    if return_usage:
        return {"content": content, "usage": usage}
    return content


def get_response_siliconflow_deepseek(prompt, temperature=0):
    url = "https://api.siliconflow.cn/v1/chat/completions"

    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "temperature": temperature,
        "messages": [
            {
                "content": prompt,
                "role": "user"
            }
        ]
    }
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        raise RuntimeError("SILICONFLOW_API_KEY is not set")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    for attempt in range(3):
        response = requests.request("POST", url, json=payload, headers=headers)
        response_json = response.json()
        if 'choices' in response_json:
            return response_json['choices'][0]['message']['content']
        else:
            print(f"Attempt {attempt + 1} failed, retrying...")

    # 如果所有重试都失败，返回错误消息
    return "请求失败：未能获取有效响应"

import subprocess
import json

def get_chat_response(prompt, temperature=0):
    api_key = os.getenv("ZJU_CHAT_API_KEY")
    if not api_key:
        raise RuntimeError("ZJU_CHAT_API_KEY is not set")
    curl_command = [
        'curl', '-X', 'POST', '--location', 'https://chat.zju.edu.cn/api/ai/v1/chat/completions',
        '--header', 'Content-Type: application/json',
        '--header', f'Authorization: Bearer {api_key}',
        '--data', json.dumps({
            "model": "deepseek-v3-671b",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        })
    ]

    result = subprocess.run(curl_command, capture_output=True, text=True)

    # 解析 JSON 响应
    response_json = json.loads(result.stdout)

    # 获取 content 字段
    if  'choices' not in response_json:
        import ipdb; ipdb.set_trace()
    content = response_json['choices'][0]['message']['content']

    return content

if __name__ == '__main__':
    prompt = "你是谁？"
    response = get_response_siliconflow_deepseek(prompt)
    print(response)
