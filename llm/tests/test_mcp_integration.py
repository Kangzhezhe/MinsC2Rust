"""
测试集成MCP支持的LLM类
"""
import asyncio
import sys
import os
import pytest


from llm.llm import LLM, create_llm_with_mcp
from llm.tool_call import LLMToolCaller

# 尝试导入MCP相关模块
try:
    from llm.mcp_client import MCPServerConfig, MCPTransportType, MCP_AVAILABLE
except ImportError:
    MCP_AVAILABLE = False


class TestLLMIntegration:
    """LLM集成测试类"""
    
    def test_traditional_tools(self):
        """测试传统工具调用"""
        print("=== 测试传统工具调用 ===")
        
        # 定义工具函数
        def add(a: float, b: float) -> float:
            """加法工具"""
            return a + b

        def multiply(a: float, b: float) -> float:
            """乘法工具"""
            return a * b

        def echo(text: str) -> str:
            """回声工具"""
            return f"回声: {text}"

        # 创建传统工具调用器
        traditional_caller = LLMToolCaller([add, multiply, echo])
        
        # 创建LLM实例
        llm = LLM()
        
        # 测试传统工具调用
        print("\n--- 测试加法 ---")
        result1 = llm.call("请帮我计算 3 + 5", caller=traditional_caller)
        print(f"结果: {result1}")
        assert result1 is not None
        assert isinstance(result1, dict)
        assert "tool_name" in result1
        assert "tool_result" in result1
        assert result1["tool_name"] == "add"
        assert result1["tool_result"] == 8.0
        
        print("\n--- 测试乘法 ---")
        result2 = llm.call("请帮我计算 4 × 6", caller=traditional_caller)
        print(f"结果: {result2}")
        assert result2 is not None
        assert isinstance(result2, dict)
        assert "tool_name" in result2
        assert "tool_result" in result2
        assert result2["tool_name"] == "multiply"
        assert result2["tool_result"] == 24.0
        
        print("\n--- 测试回声 ---")
        result3 = llm.call("请重复说 'Hello World'", caller=traditional_caller)
        print(f"结果: {result3}")
        assert result3 is not None
        # 回声工具可能直接返回字符串或包含工具调用信息的字典
        if isinstance(result3, dict):
            assert "tool_name" in result3
            assert "tool_result" in result3
            assert result3["tool_name"] == "echo"
            assert "Hello World" in str(result3["tool_result"])
        else:
            assert "Hello World" in str(result3)

    @pytest.mark.asyncio
    async def test_mcp_tools(self):
        """测试MCP工具调用"""
        if not MCP_AVAILABLE:
            pytest.skip("MCP功能不可用，跳过测试")
        
        print("=== 测试MCP工具调用 ===")
        
        # 创建MCP配置
        mcp_configs = [
            MCPServerConfig(
                name="demo",
                command="python",
                args=["-m", "demo.demo_mcp_server"],
                transport=MCPTransportType.STDIO
            )
        ]
        
        # 创建支持MCP的LLM
        llm = create_llm_with_mcp(mcp_configs)
        
        try:
            # 初始化MCP连接
            print("初始化MCP连接...")
            await llm.init_mcp()
            
            # 获取可用工具
            tools = llm.get_available_tools("mcp")
            print(f"可用的MCP工具: {tools}")
            
            # 测试MCP工具调用
            print("\n--- 测试MCP计算工具 ---")
            result1 = await llm.call_async("请使用calculate工具计算 10 + 20", use_mcp=True)
            print(f"结果: {result1}")
            assert result1 is not None
            assert isinstance(result1, dict)
            assert "tool_name" in result1
            assert "tool_result" in result1
            # 验证工具调用成功
            tool_result = result1["tool_result"]
            if hasattr(tool_result, 'data'):
                assert tool_result.data == 30.0
            elif hasattr(tool_result, 'structured_content'):
                assert tool_result.structured_content.get('result') == 30.0
            
            print("\n--- 测试获取时间 ---")
            result2 = await llm.call_async("请获取当前时间", use_mcp=True)
            print(f"结果: {result2}")
            assert result2 is not None
            assert isinstance(result2, dict)
            assert "tool_name" in result2
            assert "tool_result" in result2
            # 验证时间格式（YYYY-MM-DD HH:MM:SS）
            tool_result2 = result2["tool_result"]
            if hasattr(tool_result2, 'data'):
                time_str = tool_result2.data
            elif hasattr(tool_result2, 'structured_content'):
                time_str = tool_result2.structured_content.get('result', '')
            else:
                time_str = str(tool_result2)
            assert len(time_str) >= 19  # 至少包含日期时间格式
            assert "2025" in time_str
            
            print("\n--- 测试回声消息 ---")
            result3 = await llm.call_async("请使用echo_message工具重复'MCP测试成功'", use_mcp=True)
            print(f"结果: {result3}")
            assert result3 is not None
            assert isinstance(result3, dict)
            assert "tool_name" in result3
            assert "tool_result" in result3
            # 验证回声内容
            tool_result3 = result3["tool_result"]
            if hasattr(tool_result3, 'data'):
                echo_str = tool_result3.data
            elif hasattr(tool_result3, 'structured_content'):
                echo_str = tool_result3.structured_content.get('result', '')
            else:
                echo_str = str(tool_result3)
            assert "MCP测试成功" in echo_str
            
        except Exception as e:
            print(f"MCP测试出错: {e}")
            pytest.fail(f"MCP测试失败: {e}")
        finally:
            # 清理MCP连接
            await llm.cleanup_mcp()

    @pytest.mark.asyncio
    async def test_mixed_usage(self):
        """测试混合使用传统工具和MCP工具"""
        if not MCP_AVAILABLE:
            pytest.skip("MCP功能不可用，跳过混合测试")
        
        print("=== 测试混合使用 ===")
        
        # 定义传统工具
        def add(a: float, b: float) -> float:
            return a + b
        
        traditional_caller = LLMToolCaller([add])
        
        # 创建MCP配置
        mcp_configs = [
            MCPServerConfig(
                name="demo",
                command="python",
                args=["-m", "demo.demo_mcp_server"],
                transport=MCPTransportType.STDIO
            )
        ]
        
        llm = LLM(mcp_configs=mcp_configs)
        
        try:
            await llm.init_mcp()
            
            print("\n--- 使用传统工具 ---")
            result1 = llm.call("请计算 5 + 3", caller=traditional_caller, use_mcp=False)
            print(f"传统工具结果: {result1}")
            assert result1 is not None

            result1_async = await llm.call_async("请计算 5 + 3", caller=traditional_caller, use_mcp=False)
            print(f"传统工具异步结果: {result1_async}")
            assert result1_async is not None
            
            print("\n--- 使用MCP工具 ---")
            result2 = await llm.call_async("请获取当前时间", use_mcp=True)
            print(f"MCP工具结果: {result2}")
            assert result2 is not None
            
            print("\n--- 普通对话（不使用工具） ---")
            result3 = llm.call("你好，请介绍一下你自己")
            print(f"普通对话结果: {result3}")
            assert result3 is not None
            
        except Exception as e:
            pytest.fail(f"混合使用测试失败: {e}")
        finally:
            await llm.cleanup_mcp()

    @pytest.mark.asyncio
    async def test_parallel_async_calls(self):
        """测试并行异步调用"""
        if not MCP_AVAILABLE:
            pytest.skip("MCP功能不可用，跳过并行测试")
        
        print("=== 测试并行异步调用 ===")
        
        # 定义传统工具
        def add(a: float, b: float) -> float:
            return a + b
        
        def multiply(a: float, b: float) -> float:
            return a * b
        
        traditional_caller = LLMToolCaller([add, multiply])
        
        # 创建MCP配置
        mcp_configs = [
            MCPServerConfig(
                name="demo",
                command="python",
                args=["-m", "demo.demo_mcp_server"],
                transport=MCPTransportType.STDIO
            )
        ]
        
        llm = LLM(mcp_configs=mcp_configs)
        
        try:
            await llm.init_mcp()
            
            print("\n--- 并行调用多个传统工具 ---")
            # 并行调用多个传统工具
            task1 = llm.call_async("请用工具计算 10 + 20", caller=traditional_caller, use_mcp=False)
            task2 = llm.call_async("请用工具计算 5 × 6", caller=traditional_caller, use_mcp=False)
            task3 = llm.call_async("请用工具计算 100 + 200", caller=traditional_caller, use_mcp=False)
            
            # 等待所有任务完成
            results = await asyncio.gather(task1, task2, task3)
            
            print(f"并行传统工具结果: {results}")
            assert len(results) == 3
            for result in results:
                assert "tool_name" in result
                assert "tool_result" in result
            
            print("\n--- 并行调用多个MCP工具 ---")
            # 并行调用多个MCP工具
            mcp_task1 = llm.call_async("请使用calculate工具计算 15 + 25", use_mcp=True)
            mcp_task2 = llm.call_async("请获取当前时间", use_mcp=True)
            mcp_task3 = llm.call_async("请使用echo_message工具重复'并行测试'", use_mcp=True)
            
            # 等待所有MCP任务完成
            mcp_results = await asyncio.gather(mcp_task1, mcp_task2, mcp_task3)
            
            print(f"并行MCP工具结果: {mcp_results}")
            assert len(mcp_results) == 3
            for result in mcp_results:
                assert "tool_name" in result
                assert "tool_result" in result
            
            print("\n--- 混合并行调用（传统工具 + MCP工具 + 普通对话） ---")
            # 混合并行调用
            mixed_task1 = llm.call_async("请用工具计算 7 + 8", caller=traditional_caller, use_mcp=False)
            mixed_task2 = llm.call_async("请获取当前时间", use_mcp=True)
            # 注意：普通对话需要用同步方式包装成异步
            mixed_task3 = asyncio.create_task(asyncio.to_thread(llm.call, "请简单介绍一下Python"))
            
            # 等待所有混合任务完成
            mixed_results = await asyncio.gather(mixed_task1, mixed_task2, mixed_task3)
            
            print(f"混合并行结果: {mixed_results}")
            assert len(mixed_results) == 3
            # 验证传统工具结果
            assert "tool_name" in mixed_results[0]
            assert "tool_result" in mixed_results[0]
            # 验证MCP工具结果
            assert "tool_name" in mixed_results[1]
            assert "tool_result" in mixed_results[1]
            # 验证普通对话结果
            assert mixed_results[2] is not None
            assert isinstance(mixed_results[2], str)

        except Exception as e:
            pytest.fail(f"并行异步调用测试失败: {e}")
        finally:
            await llm.cleanup_mcp()

    @pytest.mark.asyncio
    async def test_concurrent_performance(self):
        """专门测试并发性能的用例"""
        import os
        if not os.getenv('RUN_PERFORMANCE_TESTS', False):
            print("性能测试默认跳过，设置环境变量 RUN_PERFORMANCE_TESTS=1 来运行")
            return
    

        if not MCP_AVAILABLE:
            pytest.skip("MCP功能不可用，跳过并发性能测试")
        
        print("=== 专门测试并发性能 ===")
        
        # 创建MCP配置
        mcp_configs = [
            MCPServerConfig(
                name="demo",
                command="python",
                args=["-m", "demo.demo_mcp_server"],
                transport=MCPTransportType.STDIO
            )
        ]
        
        llm = LLM(mcp_configs=mcp_configs)
        
        try:
            await llm.init_mcp()
            
            import time
            
            # 测试不同并发数量的性能
            concurrent_levels = [1, 2, 5, 10, 20]
            performance_results = {}
            
            for num_calls in concurrent_levels:
                print(f"\n{'='*60}")
                print(f"测试并发数量: {num_calls}")
                print(f"{'='*60}")
                
                # 串行执行基准测试
                print(f"\n--- 串行执行 {num_calls} 个调用（基准测试） ---")
                start_time = time.time()
                
                serial_results = []
                for i in range(num_calls):
                    task_type = i % 4
                    if task_type == 0:
                        result = await llm.call_async("请获取当前时间", use_mcp=True)
                    elif task_type == 1:
                        result = await llm.call_async(f"请使用echo_message工具重复'串行{i}'", use_mcp=True)
                    elif task_type == 2:
                        result = await llm.call_async(f"请使用calculate工具计算 {i*5} + {i*3}", use_mcp=True)
                    else:
                        result = await llm.call_async("请获取当前时间", use_mcp=True)
                    serial_results.append(result)
                
                serial_time = time.time() - start_time
                print(f"串行执行时间: {serial_time:.3f}秒")
                print(f"平均每个调用: {(serial_time / num_calls):.3f}秒")
                
                # 并行执行测试
                print(f"\n--- 并行执行 {num_calls} 个调用 ---")
                start_time = time.time()
                
                parallel_tasks = []
                for i in range(num_calls):
                    task_type = i % 4
                    if task_type == 0:
                        task = llm.call_async("请获取当前时间", use_mcp=True)
                    elif task_type == 1:
                        task = llm.call_async(f"请使用echo_message工具重复'并行{i}'", use_mcp=True)
                    elif task_type == 2:
                        task = llm.call_async(f"请使用calculate工具计算 {i*5} + {i*3}", use_mcp=True)
                    else:
                        task = llm.call_async("请获取当前时间", use_mcp=True)
                    parallel_tasks.append(task)
                
                parallel_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
                parallel_time = time.time() - start_time
                
                # 统计成功和失败
                success_count = 0
                error_count = 0
                for result in parallel_results:
                    if isinstance(result, Exception):
                        error_count += 1
                        print(f"错误: {result}")
                    elif isinstance(result, dict) and "tool_name" in result:
                        success_count += 1
                    else:
                        error_count += 1
                
                print(f"并行执行时间: {parallel_time:.3f}秒")
                print(f"平均每个调用: {(parallel_time / num_calls):.3f}秒")
                print(f"成功调用: {success_count}/{num_calls} ({(success_count/num_calls*100):.1f}%)")
                print(f"失败调用: {error_count}/{num_calls} ({(error_count/num_calls*100):.1f}%)")
                
                # 计算性能指标
                if parallel_time > 0 and success_count > 0:
                    speedup = serial_time / parallel_time
                    efficiency = speedup / num_calls * 100
                    throughput_serial = num_calls / serial_time
                    throughput_parallel = success_count / parallel_time
                    
                    print(f"\n--- 性能指标 ---")
                    print(f"加速比: {speedup:.2f}x")
                    print(f"并行效率: {efficiency:.1f}%")
                    print(f"串行吞吐量: {throughput_serial:.2f} 调用/秒")
                    print(f"并行吞吐量: {throughput_parallel:.2f} 调用/秒")
                    print(f"吞吐量提升: {(throughput_parallel/throughput_serial):.2f}x")
                    
                    # 保存结果用于最终分析
                    performance_results[num_calls] = {
                        'serial_time': serial_time,
                        'parallel_time': parallel_time,
                        'speedup': speedup,
                        'efficiency': efficiency,
                        'success_rate': success_count / num_calls,
                        'throughput_improvement': throughput_parallel / throughput_serial
                    }
                    
                    # 性能评估
                    if efficiency >= 70:
                        print(f"🟢 性能评级: 优秀 (效率 {efficiency:.1f}%)")
                    elif efficiency >= 50:
                        print(f"🟡 性能评级: 良好 (效率 {efficiency:.1f}%)")
                    elif efficiency >= 30:
                        print(f"🟠 性能评级: 一般 (效率 {efficiency:.1f}%)")
                    else:
                        print(f"🔴 性能评级: 较差 (效率 {efficiency:.1f}%)")
                
                # 稍微等待一下，避免资源竞争
                await asyncio.sleep(0.5)
            
            # 最终性能分析报告
            print(f"\n{'='*80}")
            print("并发性能分析报告")
            print(f"{'='*80}")
            
            print(f"{'并发数':<8} {'串行时间':<10} {'并行时间':<10} {'加速比':<8} {'效率':<8} {'成功率':<8} {'吞吐量提升':<10}")
            print("-" * 80)
            
            for num_calls, metrics in performance_results.items():
                print(f"{num_calls:<8} "
                    f"{metrics['serial_time']:<10.3f} "
                    f"{metrics['parallel_time']:<10.3f} "
                    f"{metrics['speedup']:<8.2f} "
                    f"{metrics['efficiency']:<8.1f}% "
                    f"{metrics['success_rate']:<8.1f}% "
                    f"{metrics['throughput_improvement']:<10.2f}x")
            
            # 寻找最优并发数
            if performance_results:
                best_efficiency = max(performance_results.items(), 
                                    key=lambda x: x[1]['efficiency'])
                best_throughput = max(performance_results.items(), 
                                    key=lambda x: x[1]['throughput_improvement'])
                
                print(f"\n📊 性能分析:")
                print(f"• 最高效率: 并发数 {best_efficiency[0]} (效率 {best_efficiency[1]['efficiency']:.1f}%)")
                print(f"• 最高吞吐量: 并发数 {best_throughput[0]} (提升 {best_throughput[1]['throughput_improvement']:.2f}x)")
                
                # 性能瓶颈分析
                print(f"\n🔍 瓶颈分析:")
                high_concurrency = [k for k, v in performance_results.items() 
                                if k >= 10 and v['efficiency'] < 30]
                if high_concurrency:
                    print(f"• 高并发性能下降: 并发数 {high_concurrency} 时效率显著下降")
                    print(f"• 可能原因: MCP连接池限制、服务器处理能力瓶颈")
                
                low_speedup = [k for k, v in performance_results.items() 
                            if v['speedup'] < 1.5]
                if low_speedup:
                    print(f"• 并行加速不明显: 并发数 {low_speedup} 时加速比 < 1.5x")
                    print(f"• 可能原因: 锁竞争、同步I/O、网络延迟")
                
                success_issues = [k for k, v in performance_results.items() 
                                if v['success_rate'] < 0.95]
                if success_issues:
                    print(f"• 稳定性问题: 并发数 {success_issues} 时成功率 < 95%")
                    print(f"• 建议: 降低并发数或增加重试机制")
            
            # 给出优化建议
            print(f"\n💡 优化建议:")
            if best_efficiency[1]['efficiency'] >= 70:
                print(f"• 系统并发性能良好，推荐并发数: {best_efficiency[0]}")
            elif best_efficiency[1]['efficiency'] >= 50:
                print(f"• 系统并发性能中等，可使用并发数: {best_efficiency[0]}，但有优化空间")
                print(f"• 建议: 检查MCP连接池设置、优化网络延迟")
            else:
                print(f"• 系统并发性能较差，建议:")
                print(f"  - 使用较低并发数 (≤ 5)")
                print(f"  - 检查是否存在全局锁")
                print(f"  - 考虑使用连接池或多实例")
                print(f"  - 优化LLM API调用性能")

            # 断言验证
            assert len(performance_results) > 0, "应该至少完成一个并发级别的测试"
            
            # 验证基本的并发能力
            if 5 in performance_results:
                assert performance_results[5]['success_rate'] >= 0.8, "并发数5时成功率应该 >= 80%"
                assert performance_results[5]['speedup'] >= 1.2, "并发数5时应该有至少1.2x的加速"
                    
        except Exception as e:
            pytest.fail(f"并发性能测试失败: {e}")
        finally:
            await llm.cleanup_mcp()


@pytest.mark.asyncio
async def test_concurrent_performance():
    """并发性能测试（函数形式）"""
    test_instance = TestLLMIntegration()
    await test_instance.test_concurrent_performance()

# 为了保持向后兼容，保留原来的函数形式
def test_traditional_tools():
    """测试传统工具调用（函数形式）"""
    test_instance = TestLLMIntegration()
    test_instance.test_traditional_tools()


@pytest.mark.asyncio
async def test_mcp_tools():
    """测试MCP工具调用（函数形式）"""
    test_instance = TestLLMIntegration()
    await test_instance.test_mcp_tools()


@pytest.mark.asyncio
async def test_mixed_usage():
    """测试混合使用（函数形式）"""
    test_instance = TestLLMIntegration()
    await test_instance.test_mixed_usage()


@pytest.mark.asyncio
async def test_parallel_async_calls():
    """测试并行异步调用（函数形式）"""
    test_instance = TestLLMIntegration()
    await test_instance.test_parallel_async_calls()


# 手动运行脚本时的主函数
async def main():
    """主测试函数（手动运行时使用）"""
    print("开始测试集成MCP支持的LLM类")
    print("=" * 50)
    
    # 创建测试实例
    test_instance = TestLLMIntegration()
    
    # 测试传统工具
    test_instance.test_traditional_tools()
    
    print("\n" + "=" * 50)
    
    # 测试MCP工具
    await test_instance.test_mcp_tools()
    
    print("\n" + "=" * 50)
    
    # 测试混合使用
    await test_instance.test_mixed_usage()
    
    print("\n" + "=" * 50)
    
    # 测试并行异步调用
    await test_instance.test_parallel_async_calls()
    
    print("\n" + "=" * 50)
    
     # 专门的并发性能测试
    await test_instance.test_concurrent_performance()
    print("\n" + "=" * 50)
    print("所有测试完成！")


if __name__ == "__main__":
    # 手动运行时使用异步
    asyncio.run(main())