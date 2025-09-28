"""
演示MCP客户端
用于测试本地MCP服务器功能
"""

import asyncio
from fastmcp import Client

def _run_async_in_sync(coro):
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result(timeout=15)
        else:
            return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)


async def main():
    # 配置本地MCP服务器（以python脚本方式启动）
    client_config = {
        "mcpServers": {
            "demo": {
                "transport": "stdio",
                "command": "python",
                "args": ["-m", "demo.demo_mcp_server"]
            }
        }
    }
    client = Client(client_config)

    await client.__aenter__()

    print("已连接到MCP服务器")
    # 列出所有工具
    tools = await client.list_tools()
    print("可用工具:")
    for tool in tools:
        print(f"- {tool.name}: {getattr(tool, 'description', '')}")

    # 调用计算工具
    print("\n调用 calculate(operation='add', a=10, b=20):")
    result = await client.call_tool("calculate", {"operation": "add", "a": 10, "b": 20})
    print("计算结果:", result.data if hasattr(result, "data") else result)

    # 调用获取时间工具
    print("\n调用 get_current_time():")
    result = await client.call_tool("get_current_time", {})
    print("当前时间:", result.data if hasattr(result, "data") else result)

    # 调用回声工具
    print("\n调用 echo_message(message='Hello MCP'):")
    result = await client.call_tool("echo_message", {"message": "Hello MCP"})
    print("回声结果:", result.data if hasattr(result, "data") else result)

    # 调用天气工具
    print("\n调用 get_weather(city='北京'):")
    result = await client.call_tool("get_weather", {"city": "北京"})
    print("天气结果:", result.data if hasattr(result, "data") else result)

    await client.__aexit__(None, None, None)

if __name__ == "__main__":
    _run_async_in_sync(main())