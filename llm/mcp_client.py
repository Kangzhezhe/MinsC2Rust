"""
MCP (Model Context Protocol) 客户端实现
支持通过MCP协议调用外部工具和资源
"""
import asyncio
import json
import logging
import re
import threading
import concurrent.futures
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from llm.template_parser.template_parser import TemplateParser

try:
    from fastmcp import FastMCP
    from fastmcp import Client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("警告: fastmcp 库未安装，MCP功能不可用。请安装: pip install fastmcp")


class MCPTransportType(Enum):
    """MCP传输类型"""
    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"
    HTTP = "http"
    STREAMABLE_HTTP = "streamable-http"
    CUSTOM = "custom"


@dataclass
class MCPServerConfig:
    """MCP服务器配置"""
    name: str
    command: str = None
    args: List[str] = None
    env: Dict[str, str] = None
    transport: MCPTransportType = MCPTransportType.STDIO
    url: Optional[str] = None  # 用于SSE、WebSocket、HTTP或streamable-http
    custom_config: Optional[Dict[str, Any]] = None  # 用于custom类型


class MCPToolCaller:
    """MCP工具调用器，兼容现有的LLMToolCaller接口"""
    
    def __init__(self, server_configs: List[MCPServerConfig]):
        """
        初始化MCP工具调用器
        
        Args:
            server_configs: MCP服务器配置列表
        """
        if not MCP_AVAILABLE:
            raise ImportError("fastmcp 库未安装，无法使用MCP功能")
        
        self.server_configs = server_configs
        self.clients = {}
        self.available_tools = {}
        self.connected_servers = set()
        # 构建通用的 template parser，用于解析 LLM 输出中的 tool_call
        # 使用通用的 args:json，能兼容不同工具的参数结构
        try:
            template = '{"tool_call":{"name":{name:str},"args":{args:json}}}'
            self.parser = TemplateParser(template)
        except Exception:
            # 解析器不可用时，继续使用回退的简单解析器
            self.parser = None
        
    async def connect_servers(self):
        """连接到所有配置的MCP服务器"""
        for config in self.server_configs:
            try:
                if config.transport == MCPTransportType.STDIO:
                    # 构造嵌套字典格式
                    client_config = {
                        "mcpServers": {
                            config.name: {
                                "transport": "stdio",
                                "command": config.command,
                                "args": config.args or [],
                                "env": config.env or {},
                            }
                        }
                    }
                elif config.transport == MCPTransportType.SSE:
                    client_config = {
                        "mcpServers": {
                            config.name: {
                                "transport": "sse",
                                "url": config.url
                            }
                        }
                    }
                elif config.transport == MCPTransportType.WEBSOCKET:
                    client_config = {
                        "mcpServers": {
                            config.name: {
                                "transport": "websocket",
                                "url": config.url
                            }
                        }
                    }
                elif config.transport == MCPTransportType.HTTP:
                    client_config = {
                        "mcpServers": {
                            config.name: {
                                "transport": "http",
                                "url": config.url
                            }
                        }
                    }
                elif config.transport == MCPTransportType.STREAMABLE_HTTP:
                    client_config = {
                        "mcpServers": {
                            config.name: {
                                "transport": "streamable-http",
                                "url": config.url
                            }
                        }
                    }
                elif config.transport == MCPTransportType.CUSTOM:
                    # 直接使用提供的自定义配置
                    if not config.custom_config:
                        raise ValueError(f"CUSTOM传输类型需要提供custom_config: {config.name}")
                    client_config = config.custom_config
                else:
                    continue

                client = Client(client_config)
                await client.__aenter__()
                self.clients[config.name] = client

                # 获取服务器提供的工具列表
                tools = await client.list_tools()
                for tool in tools:
                    tool_id = f"{config.name}.{tool.name}"
                    self.available_tools[tool_id] = {
                        'server': config.name,
                        'client': client,
                        'tool_info': tool
                    }

                self.connected_servers.add(config.name)
                print(f"已连接到MCP服务器: {config.name} ({config.transport.value})")

            except Exception as e:
                print(f"连接MCP服务器 {config.name} 失败: {e}")
    
    async def disconnect_servers(self):
        """断开所有MCP服务器连接"""
        for client in self.clients.values():
            try:
                await client.__aexit__(None, None, None)
            except Exception as e:
                print(f"断开MCP服务器连接失败: {e}")
        self.clients.clear()
        self.available_tools.clear()
        self.connected_servers.clear()
    
    def get_instructions(self) -> str:
        """获取工具使用指令（兼容现有接口）"""
        if not self.available_tools:
            return ""
        instructions = "你可以调用以下MCP工具:\n"
        for tool_id, tool_data in self.available_tools.items():
            tool_info = tool_data['tool_info']
            description = getattr(tool_info, "description", "无描述")
            instructions += f"- {tool_id}: {description}\n"

            # 添加参数信息
            try:
                schema = getattr(tool_info, 'inputSchema', None) or getattr(tool_info, 'input_schema', None)
                if schema and isinstance(schema, dict) and 'properties' in schema:
                    instructions += f"  参数: {list(schema['properties'].keys())}\n"
            except Exception:
                pass

        # 如果有 TemplateParser，则优先返回格式化说明
        if getattr(self, 'parser', None):
            try:
                instructions +=  self.parser.get_format_instructions() + "\n不同工具示例见上方工具列表。"
            except Exception as e:
                logging.debug("TemplateParser.get_format_instructions() 失败: %s", e)

        return instructions
    
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        调用MCP工具
        
        Args:
            tool_name: 工具名称（格式：服务器名.工具名 或 工具名）
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        # 规范化工具名（去掉外层引号与空白）
        tool_name = self._normalize_tool_name(tool_name)

        # 查找工具
        tool_data = None
        if tool_name in self.available_tools:
            tool_data = self.available_tools[tool_name]
        else:
            # 尝试匹配工具名（不含服务器前缀）
            for tool_id, data in self.available_tools.items():
                if tool_id.endswith(f".{tool_name}"):
                    tool_data = data
                    break

        if not tool_data:
            avail = list(self.available_tools.keys())
            raise ValueError(f"未找到MCP工具: {tool_name}. 可用工具: {avail}")

        client = tool_data['client']
        actual_tool_name = getattr(tool_data['tool_info'], 'name', None)

        try:
            result = await client.call_tool(actual_tool_name, kwargs, timeout=10)
            # result = await client.call_tool("calculate", {"operation": "add", "a": 10, "b": 20}, timeout=10)
            return result
        except Exception as e:
            raise RuntimeError(f"调用MCP工具 {tool_name} 失败: {e}")
    
    async def call(self, llm_output: str) -> tuple[Optional[str], Optional[Any]]:
        """
        解析LLM输出并调用工具（兼容现有接口）- 同步版本
        
        Args:
            llm_output: LLM的输出文本
            
        Returns:
            (工具名称, 工具结果) 或 (None, None)
        """
        # 仅使用 TemplateParser 解析（更严格、更稳健），不再回退到旧的标签解析形式
        tool_name = None
        try:
            if getattr(self, 'parser', None):
                parsed = self.parser.validate(llm_output)
                if parsed.get('success', False):
                    data = parsed.get('data', {})
                    tool_name = data.get('name')
                    tool_args = data.get('args', {}) or {}
                    result = await self.call_tool(tool_name, **tool_args)
                    return tool_name, result

            # 未配置 TemplateParser 或解析失败时，不再使用旧的标签回退；返回无工具调用
            return None, None

        except Exception as e:
            print(f"MCP工具调用错误: {e}")
            return tool_name, f"错误: {e}"
    
    def _run_async_in_sync(self, coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行中的事件循环：直接运行
            return asyncio.run(coro)

        # 如果能拿到运行循环，说明当前线程已有事件循环在运行
        # 在单独线程中执行 asyncio.run(coro) 避免死锁
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(asyncio.run, coro)
            return fut.result(timeout=15)
        
    
    def get_available_tools(self) -> List[str]:
        """获取可用工具列表"""
        return list(self.available_tools.keys())

    def _normalize_tool_name(self, name: Optional[str]) -> Optional[str]:
        """规范化从 LLM/Parser 得到的工具名：去除外层引号和左右空白。"""
        if name is None:
            return None
        s = str(name).strip()
        if (len(s) >= 2) and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
            s = s[1:-1].strip()
        return s


# 便捷函数
def create_mcp_configs() -> List[MCPServerConfig]:
    """创建常用MCP服务器配置示例"""
    configs = []
    
    # 文件系统MCP服务器示例
    configs.append(MCPServerConfig(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "."],
        transport=MCPTransportType.STDIO
    ))
    
    # 演示MCP服务器（STDIO）
    configs.append(MCPServerConfig(
        name="demo",
        command="python",
        args=["-m", "demo.demo_mcp_server"],
        transport=MCPTransportType.STDIO
    ))
    
    # HTTP MCP服务器示例
    configs.append(MCPServerConfig(
        name="http_demo",
        transport=MCPTransportType.HTTP,
        url="http://127.0.0.1:8000"
    ))
    
    # Streamable HTTP MCP服务器示例
    configs.append(MCPServerConfig(
        name="streamable_http_demo",
        transport=MCPTransportType.STREAMABLE_HTTP,
        url="http://127.0.0.1:8000"
    ))
    
    # 自定义配置示例
    # custom_config = {
    #     "mcpServers": {
    #         "custom_server": {
    #             "transport": "streamable-http",
    #             "url": "http://localhost:3000/api/mcp",
    #             "headers": {
    #                 "Authorization": "Bearer your-token"
    #             }
    #         }
    #     }
    # }
    # configs.append(MCPServerConfig(
    #     name="custom_server",
    #     transport=MCPTransportType.CUSTOM,
    #     custom_config=custom_config
    # ))
    
    return configs


def create_http_mcp_config(name: str, url: str, streamable: bool = True) -> MCPServerConfig:
    """
    创建HTTP MCP服务器配置的便捷函数
    
    Args:
        name: 服务器名称
        url: 服务器URL
        streamable: 是否使用streamable-http (True) 或 http (False)
    
    Returns:
        MCPServerConfig实例
    """
    transport = MCPTransportType.STREAMABLE_HTTP if streamable else MCPTransportType.HTTP
    return MCPServerConfig(
        name=name,
        transport=transport,
        url=url
    )


def create_custom_mcp_config(name: str, config_dict: Dict[str, Any]) -> MCPServerConfig:
    """
    创建自定义MCP服务器配置的便捷函数
    
    Args:
        name: 服务器名称
        config_dict: 完整的客户端配置字典
    
    Returns:
        MCPServerConfig实例
    """
    return MCPServerConfig(
        name=name,
        transport=MCPTransportType.CUSTOM,
        custom_config=config_dict
    )
