import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict


def _call_with_timeout(fn, timeout_seconds):
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn)
    try:
        return future.result(timeout=timeout_seconds)
    except FuturesTimeoutError:
        future.cancel()
        raise
    finally:
        # Do not block caller on hung provider requests.
        executor.shutdown(wait=False, cancel_futures=True)


def _normalize_response_with_usage(response: Any) -> Dict[str, Any]:
    if isinstance(response, dict):
        content = str(response.get("content", "") or "")
        usage_raw = response.get("usage", {}) or {}
        usage = {
            "prompt_tokens": int(usage_raw.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage_raw.get("completion_tokens", 0) or 0),
            "total_tokens": int(usage_raw.get("total_tokens", 0) or 0),
        }
        if usage["total_tokens"] <= 0:
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
        return {"content": content, "usage": usage}

    return {
        "content": str(response or ""),
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


def generate_response(
    prompt,
    llm_model='qwen',
    temperature=0.0,
    response_format='text',
    max_prompt_length=30000,
    timeout_seconds=None,
    return_usage=False,
):
    if len(prompt) > max_prompt_length:
        too_long = {"content": "上下文长度超过限制", "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
        return too_long if return_usage else too_long["content"]
    timeout_seconds = timeout_seconds or int(os.getenv("LLM_CALL_TIMEOUT_SECONDS", "180"))

    max_retries = 5
    for attempt in range(max_retries + 1):
        response_str = None
        try:
            if llm_model == "local":
                from models.local import get_response_from_model
                response = _call_with_timeout(lambda: asyncio.run(get_response_from_model(prompt)), timeout_seconds)
            elif llm_model == "qwen":
                from models.qianwen import get_response_qianwen
                response = _call_with_timeout(
                    lambda: get_response_qianwen(
                        prompt,
                        temperature=temperature,
                        response_format=response_format,
                        return_usage=return_usage,
                    ),
                    timeout_seconds,
                )
                # response = process_completion_qwq(prompt,temperature=temperature)
            elif llm_model == "deepseek":
                from models.deepseek import get_response_deepseek
                response = _call_with_timeout(
                    lambda: get_response_deepseek(prompt, temperature=temperature, return_usage=return_usage),
                    timeout_seconds,
                )
                # response = get_response_siliconflow_deepseek(prompt,temperature)
                # response = get_chat_response(prompt,temperature)
            elif llm_model == "zhipu":
                from models.zhipu import get_response_zhipu
                response = _call_with_timeout(lambda: get_response_zhipu(prompt), timeout_seconds)
            elif llm_model == "claude":
                from models.claude import get_response_claude
                response = _call_with_timeout(
                    lambda: get_response_claude(prompt, temperature=temperature, response_format=response_format),
                    timeout_seconds,
                )
            elif llm_model == "gpt4o":
                from models.gpt import get_response_gpt4o
                response = _call_with_timeout(lambda: get_response_gpt4o(prompt, temperature=temperature), timeout_seconds)
            elif llm_model == "openai":
                from models.openai_model import get_response_openai
                response = _call_with_timeout(
                    lambda: get_response_openai(
                        prompt,
                        temperature=temperature,
                        response_format=response_format,
                        return_usage=return_usage,
                    ),
                    timeout_seconds,
                )
            else:
                response = f"不支持的模型: {llm_model}"

            if response is None:
                response_obj = {
                    "content": "请求出错: 模型返回空响应",
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                }
            else:
                response_obj = _normalize_response_with_usage(response)
            response_str = response_obj["content"]

        except FuturesTimeoutError:
            response_obj = {
                "content": f"请求超时: 超过 {timeout_seconds} 秒未返回",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
            response_str = response_obj["content"]
        except Exception as e:
            response_obj = {
                "content": f"请求出错: {e}",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
            response_str = response_obj["content"]

        # 加上对"请求出错"或"Error"的判断，防止普通回答中刚好包含"429"被误判为报错
        if isinstance(response_str, str) and "429" in response_str and ("请求出错" in response_str or "Error" in response_str):
            if attempt < max_retries:
                time.sleep(2)
                continue
            else:
                return response_obj if return_usage else response_str

        # If we reach here, it wasn't a 429 error
        return response_obj if return_usage else response_str

    # Fallback in case of logic drop-through
    return response_obj if return_usage else response_str
