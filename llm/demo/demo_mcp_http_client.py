"""
HTTP MCP 客户端演示
使用FastMCP库连接HTTP传输的MCP服务器
"""

import asyncio
import json
from fastmcp import Client

def _run_async_in_sync(coro):
    """在同步环境中运行异步代码"""
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result(timeout=30)
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

async def test_basic_tools(client):
    """测试基础工具"""
    print("=== 基础工具测试 ===")
    
    # 1. 加法计算
    print("\n1. 加法计算:")
    result = await client.call_tool("add_numbers", {"a": 15, "b": 25})
    print(f"   15 + 25 = {result.data if hasattr(result, 'data') else result}")
    
    # 2. 乘法计算
    print("\n2. 乘法计算:")
    result = await client.call_tool("multiply_numbers", {"a": 8, "b": 9})
    print(f"   8 × 9 = {result.data if hasattr(result, 'data') else result}")
    
    # 3. 获取时间
    print("\n3. 获取当前时间:")
    result = await client.call_tool("get_current_datetime", {})
    print(f"   当前时间: {result.data if hasattr(result, 'data') else result}")
    
    # 4. 回声测试
    print("\n4. 回声测试:")
    result = await client.call_tool("echo_text", {"text": "Hello HTTP MCP!"})
    print(f"   回声: {result.data if hasattr(result, 'data') else result}")

async def test_advanced_tools(client):
    """测试高级工具"""
    print("\n=== 高级工具测试 ===")
    
    # 1. 服务器信息
    print("\n1. 服务器信息:")
    result = await client.call_tool("get_server_info", {})
    info = result.data if hasattr(result, 'data') else result
    if isinstance(info, dict):
        for key, value in info.items():
            print(f"   {key}: {value}")
    else:
        print(f"   {info}")
    
    # 2. 计算面积 - 圆形
    print("\n2. 计算圆形面积:")
    result = await client.call_tool("calculate_circle_area", {"radius": 5})
    area_info = result.data if hasattr(result, 'data') else result
    if isinstance(area_info, dict):
        print(f"   圆形半径: {area_info.get('radius')}")
        print(f"   面积: {area_info.get('area'):.2f}")
    
    # 3. 计算面积 - 矩形
    print("\n3. 计算矩形面积:")
    result = await client.call_tool("calculate_rectangle_area", {"width": 10, "height": 6})
    area_info = result.data if hasattr(result, 'data') else result
    if isinstance(area_info, dict):
        print(f"   矩形宽度: {area_info.get('width')}, 高度: {area_info.get('height')}")
        print(f"   面积: {area_info.get('area')}")
    
    # 4. 计算面积 - 三角形
    print("\n4. 计算三角形面积:")
    result = await client.call_tool("calculate_triangle_area", {"base": 8, "height": 5})
    area_info = result.data if hasattr(result, 'data') else result
    if isinstance(area_info, dict):
        print(f"   三角形底边: {area_info.get('base')}, 高度: {area_info.get('height')}")
        print(f"   面积: {area_info.get('area'):.1f}")

async def test_resources(client):
    """测试资源"""
    print("\n=== 资源测试 ===")
    
    try:
        # 列出所有资源
        print("\n1. 列出资源:")
        resources = await client.list_resources()
        for resource in resources:
            print(f"   - {resource.name}: {resource.uri}")
        
        # 读取服务器状态资源
        print("\n2. 服务器状态:")
        result = await client.read_resource("server://status")
        print(f"   状态: {result.data if hasattr(result, 'data') else result}")
        
        # 读取工具信息资源
        print("\n3. 工具信息:")
        result = await client.read_resource("server://tools")
        tools_info = result.data if hasattr(result, 'data') else result
        if isinstance(tools_info, dict) and 'tools' in tools_info:
            for tool in tools_info['tools']:
                print(f"   - {tool['name']} ({tool['type']})")
        
    except Exception as e:
        print(f"   资源测试失败: {e}")

async def interactive_mode(client):
    """交互模式"""
    print("\n=== 交互模式 ===")
    print("输入工具名称和参数进行测试，输入 'quit' 退出")
    print("示例:")
    print("  add_numbers {\"a\": 10, \"b\": 20}")
    print("  calculate_circle_area {\"radius\": 5}")
    print("  calculate_rectangle_area {\"width\": 10, \"height\": 6}")
    
    while True:
        try:
            user_input = input("\n> ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            # 解析输入
            parts = user_input.split(' ', 1)
            tool_name = parts[0]
            
            # 解析参数
            if len(parts) > 1:
                try:
                    params = json.loads(parts[1])
                except json.JSONDecodeError:
                    print("参数格式错误，请使用JSON格式")
                    continue
            else:
                params = {}
            
            # 调用工具
            result = await client.call_tool(tool_name, params)
            print(f"结果: {result.data if hasattr(result, 'data') else result}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"错误: {e}")

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="HTTP MCP客户端测试")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="MCP服务器URL")
    parser.add_argument("--basic", action="store_true", help="运行基础测试")
    parser.add_argument("--advanced", action="store_true", help="运行高级测试")
    parser.add_argument("--resources", action="store_true", help="测试资源")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互模式")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    
    args = parser.parse_args()
    
    # 如果没有指定任何选项，默认运行基础测试
    if not any([args.basic, args.advanced, args.resources, args.interactive, args.all]):
        args.basic = True
    
    # 配置HTTP客户端
    client_config = {
        "mcpServers": {
            "http_demo": {
                "transport": "streamable-http",
                "url": f"{args.url}"
            }
        }
    }
    
    print(f"连接到HTTP MCP服务器: {args.url}")
    
    try:
        client = Client(client_config)
        await client.__aenter__()
        
        # 列出工具
        print("=== 可用工具 ===")
        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool.name}: {getattr(tool, 'description', '')}")
        
        # 运行测试
        if args.all or args.basic:
            await test_basic_tools(client)
        
        if args.all or args.advanced:
            await test_advanced_tools(client)
        
        if args.all or args.resources:
            await test_resources(client)
        
        if args.interactive:
            await interactive_mode(client)
        
        await client.__aexit__(None, None, None)
        
    except Exception as e:
        print(f"连接失败: {e}")
        print("请确保HTTP MCP服务器正在运行")
        print(f"尝试启动服务器: python src/core/llm/demo/demo_mcp_http_server.py")

def run_sync():
    """同步运行入口"""
    return _run_async_in_sync(main())

if __name__ == "__main__":
    run_sync()