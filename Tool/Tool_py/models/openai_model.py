import os
import requests

def get_response_openai(prompt, temperature=0, response_format='text', return_usage=False):
    api_url = os.getenv("OPENAI_API_BASE", "https://apis.iflow.cn/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL_NAME", "deepseek-v3.2")
    
    if not api_key:
        return "Error: OPENAI_API_KEY is not set"
        
    if not api_url.endswith("/chat/completions"):
        if api_url.endswith("/"):
            api_url += "chat/completions"
        else:
            api_url += "/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }
    
    # if response_format == 'json_object':
    #     payload["response_format"] = { "type": "json_object" }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']
        usage = data.get('usage', {}) if isinstance(data, dict) else {}
        if return_usage:
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
                    "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
                    "total_tokens": int(usage.get("total_tokens", 0) or 0),
                },
            }
        return content
    except Exception as e:
        return f"请求出错:\n{e}"
