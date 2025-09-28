"""
测试Agent的MCP功能
"""
import asyncio
import sys
import os
import pytest

# 添加项目根目录到路径

from llm.agent import Agent, create_agent_with_tools, create_agent_with_mcp

# 尝试导入MCP相关模块
try:
    from llm.mcp_client import MCPServerConfig, MCPTransportType, MCP_AVAILABLE
except ImportError:
    MCP_AVAILABLE = False


class TestAgentMCP:
    """Agent MCP功能测试类"""
    
    @pytest.mark.asyncio
    async def test_mcp_agent_async(self):
        """测试异步MCP Agent功能"""
        if not MCP_AVAILABLE:
            pytest.skip("MCP功能不可用，跳过测试")
        
        print("=== 测试异步MCP Agent功能 ===")
        
        # 创建MCP配置
        mcp_configs = [
            MCPServerConfig(
                name="demo",
                command="python",
                args=["-m", "demo.demo_mcp_server"],
                transport=MCPTransportType.STDIO
            )
        ]
        
        try:
            # 创建支持MCP的Agent
            agent = create_agent_with_mcp(
                mcp_configs=mcp_configs,
                
                max_iterations=5
            )
            
            # 初始化MCP连接
            print("初始化MCP连接...")
            await agent.init_mcp()
            
            # 获取可用工具
            tools = agent.get_available_tools()
            print(f"可用工具: {tools}")
            assert len(tools) > 0
            
            # 测试异步MCP工具调用
            print("\n--- 测试异步MCP计算工具 ---")
            result1 = await agent.chat_async("请使用calculate工具计算 15 × 3", use_mcp=True)
            print(f"结果: {result1['final_response']}")
            print(f"工具调用: {result1['tool_calls']}")
            
            # 验证结果
            assert result1['success'] == True
            assert len(result1['tool_calls']) > 0
            assert 'calculate' in result1['tool_calls'][0]['name']
            
            # 测试获取时间
            print("\n--- 测试异步获取时间 ---")
            result2 = await agent.chat_async("请获取当前时间", use_mcp=True)
            print(f"结果: {result2['final_response']}")
            print(f"工具调用: {result2['tool_calls']}")
            
            # 验证时间结果
            assert result2['success'] == True
            assert len(result2['tool_calls']) > 0
            assert 'get_current_time' in result2['tool_calls'][0]['name']
            
            # 测试天气查询
            print("\n--- 测试异步天气查询 ---")
            result3 = await agent.chat_async("请查询北京的天气", use_mcp=True)
            print(f"结果: {result3['final_response']}")
            print(f"工具调用: {result3['tool_calls']}")
            
            # 验证天气结果
            assert result3['success'] == True
            
        except Exception as e:
            print(f"异步MCP Agent测试出错: {e}")
            pytest.fail(f"异步MCP测试失败: {e}")
        finally:
            # 清理MCP连接
            await agent.cleanup_mcp()

    @pytest.mark.asyncio
    async def test_mixed_agent_async(self):
        """测试异步混合使用传统工具和MCP工具的Agent"""
        if not MCP_AVAILABLE:
            pytest.skip("MCP功能不可用，跳过混合测试")
        
        print("=== 测试异步混合Agent功能 ===")
        
        # 定义传统工具
        def subtract(a: float, b: float) -> float:
            """减法工具"""
            return a - b

        def divide(a: float, b: float) -> float:
            """除法工具"""
            if b == 0:
                return "除数不能为零"
            return a / b

        # 创建MCP配置
        mcp_configs = [
            MCPServerConfig(
                name="demo",
                command="python",
                args=["-m", "demo.demo_mcp_server"],
                transport=MCPTransportType.STDIO
            )
        ]
        
        try:
            # 创建支持混合工具的Agent
            agent = Agent(
                
                max_iterations=6,
                mcp_configs=mcp_configs
            )
            
            # 注册传统工具
            agent.register_tools([subtract, divide])
            
            # 初始化MCP连接
            await agent.init_mcp()
            
            # 获取所有可用工具
            tools = agent.get_available_tools()
            print(f"所有可用工具: {tools}")
            assert len(tools) > 0
            
            # 测试异步传统工具
            print("\n--- 使用异步传统工具 ---")
            result1 = await agent.chat_async("请使用工具计算 10 - 3", use_tools=True, use_mcp=False)
            print(f"传统工具结果: {result1['final_response']}")
            print(f"工具调用: {result1['tool_calls']}")
            
            # 验证传统工具结果
            assert result1['success'] == True
            assert len(result1['tool_calls']) > 0
            assert result1['tool_calls'][0]['name'] == 'subtract'
            
            # 测试异步MCP工具
            print("\n--- 使用异步MCP工具 ---")
            result2 = await agent.chat_async("请使用工具获取当前时间", use_mcp=True)
            print(f"MCP工具结果: {result2['final_response']}")
            print(f"工具调用: {result2['tool_calls']}")
            
            # 验证MCP工具结果
            assert result2['success'] == True
            assert len(result2['tool_calls']) > 0
            
            # 测试简单聊天接口
            print("\n--- 测试简单异步聊天 ---")
            simple_result = await agent.simple_chat_async("你好，请介绍一下你自己")
            print(f"简单聊天结果: {simple_result}")
            assert isinstance(simple_result, str)
            assert len(simple_result) > 0
            
            # 测试异步带工具聊天
            print("\n--- 测试异步带工具聊天 ---")
            def test_tool(x: int) -> str:
                return f"测试工具处理了数字: {x}"
            
            tool_result = await agent.chat_with_tools_async(
                "请使用test_tool处理数字42", 
                tools=[test_tool]
            )
            print(f"带工具聊天结果: {tool_result['final_response']}")
            assert tool_result['success'] == True
            
        except Exception as e:
            print(f"异步混合Agent测试出错: {e}")
            pytest.fail(f"异步混合测试失败: {e}")
        finally:
            await agent.cleanup_mcp()

    @pytest.mark.asyncio 
    async def test_parallel_agent_calls(self):
        """测试Agent的并行异步调用"""
        if not MCP_AVAILABLE:
            pytest.skip("MCP功能不可用，跳过并行测试")
        
        print("=== 测试Agent并行异步调用 ===")
        
        # 创建MCP配置
        mcp_configs = [
            MCPServerConfig(
                name="demo",
                command="python",
                args=["-m", "demo.demo_mcp_server"],
                transport=MCPTransportType.STDIO
            )
        ]
        
        try:
            # 创建Agent
            agent = create_agent_with_mcp(
                mcp_configs=mcp_configs,
                max_iterations=3
            )
            
            await agent.init_mcp()
            
            # 并行执行多个异步调用
            print("\n--- 并行执行多个异步调用 ---")
            import time
            start_time = time.time()
            
            tasks = [
                agent.chat_async("请获取当前时间", use_mcp=True),
                agent.chat_async("请使用echo_message工具重复'并行测试1'", use_mcp=True),
                agent.chat_async("请使用calculate工具计算 5 + 5", use_mcp=True)
            ]
            
            results = await asyncio.gather(*tasks)
            parallel_time = time.time() - start_time
            
            print(f"并行执行完成，耗时: {parallel_time:.2f}秒")
            print(f"执行了 {len(results)} 个并行任务")
            
            # 验证所有结果
            for i, result in enumerate(results):
                print(f"任务 {i+1} 结果: {result['final_response']}")
                assert result['success'] == True
                assert len(result['tool_calls']) > 0
            
            # 对比串行执行时间
            print("\n--- 对比串行执行 ---")
            start_time = time.time()
            
            serial_results = []
            for task_prompt in [
                "请获取当前时间",
                "请使用echo_message工具重复'串行测试'", 
                "请使用calculate工具计算 3 + 3"
            ]:
                result = await agent.chat_async(task_prompt, use_mcp=True)
                serial_results.append(result)
            
            serial_time = time.time() - start_time
            print(f"串行执行完成，耗时: {serial_time:.2f}秒")
            
            # 性能对比
            if parallel_time > 0:
                speedup = serial_time / parallel_time
                print(f"并行加速比: {speedup:.2f}x")
                
                # 并行应该比串行快（虽然可能不明显）
                if speedup > 1.1:
                    print("✅ 并行执行确实提供了性能提升")
                else:
                    print("⚠️  并行提升不明显，可能受限于资源竞争")
            
        except Exception as e:
            print(f"并行测试出错: {e}")
            pytest.fail(f"并行测试失败: {e}")
        finally:
            await agent.cleanup_mcp()



@pytest.mark.asyncio
async def test_mcp_agent_async():
    """测试异步MCP Agent功能（函数形式）"""
    test_instance = TestAgentMCP()
    await test_instance.test_mcp_agent_async()


@pytest.mark.asyncio
async def test_mixed_agent_async():
    """测试异步混合Agent功能（函数形式）"""
    test_instance = TestAgentMCP()
    await test_instance.test_mixed_agent_async()


@pytest.mark.asyncio
async def test_parallel_agent_calls():
    """测试Agent并行调用（函数形式）"""
    test_instance = TestAgentMCP()
    await test_instance.test_parallel_agent_calls()


async def main():
    """主测试函数"""
    print("开始测试Agent的MCP功能")
    print("=" * 60)
    
    # 创建测试实例
    test_instance = TestAgentMCP()
    
    
    # 测试异步MCP Agent
    await test_instance.test_mcp_agent_async()
    
    print("\n" + "=" * 60)
    
    # 测试异步混合Agent
    await test_instance.test_mixed_agent_async()
    
    print("\n" + "=" * 60)
    
    # 测试并行调用
    await test_instance.test_parallel_agent_calls()
    
    print("\n" + "=" * 60)
    print("Agent MCP功能测试完成！")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
