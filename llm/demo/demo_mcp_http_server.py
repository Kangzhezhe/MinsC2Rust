"""
HTTP MCP 服务器演示
使用FastMCP库创建HTTP传输的MCP服务器
"""

import asyncio
from datetime import datetime
from fastmcp import FastMCP

# 创建MCP应用
mcp = FastMCP("HTTP MCP Demo Server")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """加法计算工具"""
    return a + b

@mcp.tool()
def multiply_numbers(a: int, b: int) -> int:
    """乘法计算工具"""
    return a * b

@mcp.tool()
def get_current_datetime() -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool()
def echo_text(text: str) -> str:
    """回声工具"""
    return f"Echo: {text}"

@mcp.tool()
def get_server_info() -> dict:
    """获取服务器信息"""
    return {
        "name": "HTTP MCP Demo Server",
        "version": "1.0.0",
        "transport": "http",
        "status": "running"
    }

@mcp.tool()
def calculate_circle_area(radius: float) -> dict:
    """计算圆形面积"""
    area = 3.14159 * radius * radius
    return {"shape": "circle", "radius": radius, "area": area}

@mcp.tool()
def calculate_rectangle_area(width: float, height: float) -> dict:
    """计算矩形面积"""
    area = width * height
    return {"shape": "rectangle", "width": width, "height": height, "area": area}

@mcp.tool()
def calculate_triangle_area(base: float, height: float) -> dict:
    """计算三角形面积"""
    area = 0.5 * base * height
    return {"shape": "triangle", "base": base, "height": height, "area": area}

@mcp.resource("server://status")
def get_status():
    """服务器状态资源"""
    return {
        "status": "healthy",
        "uptime": "running",
        "tools_count": 8,
        "transport": "http"
    }

@mcp.resource("server://tools")
def get_tools_info():
    """工具信息资源"""
    return {
        "tools": [
            {"name": "add_numbers", "type": "math"},
            {"name": "multiply_numbers", "type": "math"},
            {"name": "get_current_datetime", "type": "utility"},
            {"name": "echo_text", "type": "utility"},
            {"name": "get_server_info", "type": "info"},
            {"name": "calculate_circle_area", "type": "math"},
            {"name": "calculate_rectangle_area", "type": "math"},
            {"name": "calculate_triangle_area", "type": "math"}
        ]
    }

def run_server(host: str = "127.0.0.1", port: int = 8000):
    """启动HTTP MCP服务器"""
    print(f"启动HTTP MCP服务器: http://{host}:{port}")
    print("可用工具:")
    print("- add_numbers: 加法计算")
    print("- multiply_numbers: 乘法计算") 
    print("- get_current_datetime: 获取当前时间")
    print("- echo_text: 回声工具")
    print("- get_server_info: 服务器信息")
    print("- calculate_circle_area: 计算圆形面积")
    print("- calculate_rectangle_area: 计算矩形面积")
    print("- calculate_triangle_area: 计算三角形面积")
    
    # 使用FastMCP的run方法启动HTTP服务器
    mcp.run(transport="streamable-http", host=host, port=port, path="/")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HTTP MCP服务器")
    parser.add_argument("--host", default="127.0.0.1", help="服务器主机")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    
    args = parser.parse_args()
    run_server(args.host, args.port)