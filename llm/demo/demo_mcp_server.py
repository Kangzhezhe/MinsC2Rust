"""
演示MCP服务器
用于测试MCP客户端功能
"""
import asyncio
import json
from typing import Any, Dict

try:
    from fastmcp import FastMCP
    
    # 创建MCP服务器
    server = FastMCP("Demo MCP Server")
    
    @server.tool()
    async def calculate(operation: str, a: float, b: float) -> float:
        """
        执行基本数学运算
        
        Args:
            operation: 运算类型 (add, subtract, multiply, divide)
            a: 第一个数字
            b: 第二个数字
            
        Returns:
            运算结果
        """
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("除数不能为零")
            return a / b
        else:
            raise ValueError(f"不支持的运算类型: {operation}")
    
    @server.tool()
    async def get_current_time() -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @server.tool()
    async def echo_message(message: str) -> str:
        """回声消息"""
        return f"回声: {message}"
    
    @server.tool()
    async def get_weather(city: str) -> str:
        """获取城市天气信息（模拟）"""
        weather_data = {
            "北京": "晴天，15-25°C",
            "上海": "多云，18-28°C", 
            "广州": "小雨，20-30°C",
            "深圳": "晴天，22-32°C"
        }
        return weather_data.get(city, f"{city}的天气信息暂时无法获取")
    
    if __name__ == "__main__":
        print("启动演示MCP服务器...")
        # 运行服务器
        server.run()

except ImportError:
    print("fastmcp 库未安装，无法运行演示服务器")
    print("请安装: pip install fastmcp")
