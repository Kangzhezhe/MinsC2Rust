"""
Agent模块的测试用例
"""
import sys
import os

from llm.template_parser.template_parser import TemplateParser
from llm.agent import Agent, create_agent_with_tools


def tool_calculate_add(a: float, b: float) -> float:
    """加法工具函数"""
    return a + b


def tool_calculate_multiply(a: float, b: float) -> float:
    """乘法工具函数"""
    return a * b


def tool_echo(text: str) -> str:
    """回声工具函数"""
    return f"回声: {text}"


def tool_get_info(name: str) -> str:
    """信息获取工具函数"""
    return f"获取到{name}的信息: 这是一个测试用户"


def test_agent_basic():
    """测试基本功能"""
    # 创建agent
    agent = Agent(logger=False, max_iterations=5)
    
    # 注册工具
    tools = [tool_calculate_add, tool_calculate_multiply, tool_echo, tool_get_info]
    agent.register_tools(tools)
    
    available_tools = agent.get_available_tools()
    assert len(available_tools) == 4
    assert "tool_calculate_add" in available_tools
    
    # 测试1: 简单计算
    result = agent.chat("请使用工具计算 3 + 5")
    assert result["success"] == True
    assert "tool_calls" in result
    assert len(result["tool_calls"]) > 0
    
    # 测试2: 不需要工具的对话
    result = agent.chat("你好，今天天气不错")
    assert result["success"] == True
    assert "final_response" in result
    assert len(result["final_response"]) > 0


def test_agent_with_create_function():
    """测试使用便捷创建函数"""
    parser = TemplateParser("最后结果是:{result:int}")
    
    tools = [tool_calculate_add, tool_calculate_multiply]
    agent = create_agent_with_tools(tools, logger=False, max_iterations=8, max_consecutive_tools=7)
    
    # 测试复合计算1: 简单的两步运算
    result1 = agent.chat("请使用工具计算 (4 + 6) × 3 的结果，每一步需要数学计算的都调用工具计算", parser=parser)
    assert result1["success"] == True
    assert len(result1["tool_calls"]) >= 1  # 至少有一次工具调用
    assert result1["iterations"] >= 1
    print(result1)

    # 清空历史，开始新的测试
    agent.clear_history()
    
    # 测试复合计算2: 三步运算
    result2 = agent.chat("请使用工具计算 (2 + 3) × (4 + 5) 的结果，每一步数学运算都要调用相应的工具", parser=parser)
    assert result2["success"] == True
    assert len(result2["tool_calls"]) >= 1  # 至少1次工具调用
    assert result2["iterations"] >= 1
    print(result2)

    # 清空历史，开始新的测试
    agent.clear_history()
    
    # 测试复合计算3: 更复杂的多步运算
    result3 = agent.chat("请使用工具计算 ((1 + 2) × 3) + (4 × 5) 的结果，每个加法和乘法运算都必须调用对应的工具", parser=parser)
    assert result3["success"] == True
    assert len(result3["tool_calls"]) >= 1  # 至少1次工具调用
    assert result3["iterations"] >= 1
    print(result3)

    # 清空历史，开始新的测试
    agent.clear_history()
    
    # 测试复合计算4: 连续多次相同运算
    result4 = agent.chat("请使用加法工具计算 1 + 2 + 3 + 4 + 5 的结果，每次加法都要调用工具", parser=parser)
    assert result4["success"] == True
    assert len(result4["tool_calls"]) >= 1  # 至少1次工具调用
    assert result4["iterations"] >= 1
    print(result4)


def test_conversation_history():
    """测试对话历史功能"""
    agent = create_agent_with_tools([tool_calculate_add], logger=False)
    
    # 进行几轮对话
    agent.chat("使用工具计算 1 + 1")
    agent.chat("使用工具计算 2 + 3")
    agent.chat("你好")
    
    # 查看历史
    history = agent.get_conversation_history()
    assert len(history) == 6  # 3轮对话，每轮用户+助手各一条
    
    # 验证历史条目结构
    for entry in history:
        assert "role" in entry
        assert "content" in entry
        assert entry["role"] in ["user", "assistant"]


def test_simple_chat():
    """测试简单聊天接口"""
    agent = create_agent_with_tools([tool_calculate_add], logger=False)
    
    # 使用简单接口
    response = agent.simple_chat("计算 5 + 7")
    assert isinstance(response, str)
    assert len(response) > 0


def test_chat_with_tools():
    """测试临时工具功能"""
    agent = Agent(logger=False)
    
    # 定义临时工具
    def temp_tool(x: int) -> str:
        return f"临时工具处理了: {x}"
    
    # 使用临时工具
    result = agent.chat_with_tools("请使用临时工具处理数字 42", tools=[temp_tool])
    assert result["success"] == True
    assert len(result["tool_calls"]) > 0
    assert result["tool_calls"][0]["name"] == "temp_tool"
    
    # 检查工具是否被清理
    available_tools = agent.get_available_tools()
    assert "temp_tool" not in available_tools


if __name__ == "__main__":
    try:
        # 运行所有测试
        test_agent_basic()
        test_agent_with_create_function()
        test_conversation_history()
        test_simple_chat()
        test_chat_with_tools()
        
        print("✅ 所有测试通过")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
