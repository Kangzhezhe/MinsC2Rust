import os,sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from llm.ENV import *
import os
import asyncio
from typing import List, Dict, Any, Optional, Union, Callable

if USE_LANGCHAIN:
    os.environ["LANGCHAIN_TRACING_V2"] = LANGCHAIN_TRACING_V2
    os.environ["LANGCHAIN_ENDPOINT"] = LANGCHAIN_ENDPOINT
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT


from langchain_openai import ChatOpenAI
from .rag import get_embedding, search_knowledge_base, build_multi_file_knowledge_base
from .template_parser.template_parser import TemplateParser, MyModel
from .template_parser.table_parser import TableModel, TableParser
from langchain_core.callbacks import BaseCallbackHandler
from .tool_call import LLMToolCaller
from .memory import BaseMemoryStrategy, create_memory_strategy


# 尝试导入MCP相关模块
try:
    from .mcp_client import MCPToolCaller, MCPServerConfig
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

class CustomCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"\n====== LLM 开始 ====== :{len(''.join(prompts))} bytes")
        print(f"提示词：{prompts}")

    def on_llm_end(self, response, **kwargs):
        print(f"\n====== LLM 结束 ====== :{len(response.generations[0][0].text)} bytes")
        print(f"输出：{response.generations[0][0].text}")

class LLM:
    def __init__(
        self,
        model: Optional[Union[str, ChatOpenAI]] = None,
        temperature: float = 0.3,
        history_len: int = 0,
        logger: bool = False,
        mcp_configs=None,
        memory_strategy: Optional[Union[str, Dict[str, Any], BaseMemoryStrategy]] = None,
        memory_options: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = 60,
    ):
        """
        初始化LLM类，支持传统工具调用和MCP工具调用
        
        Args:
            model: 模型名称或已经初始化的 ChatOpenAI 实例
            temperature: 温度参数
            history_len: 历史记录长度
            logger: 是否启用日志
            mcp_configs: MCP服务器配置列表
        """
        if isinstance(model, ChatOpenAI) or (
            model is not None
            and hasattr(model, "invoke")
            and callable(getattr(model, "invoke", None))
        ):
            self.llm = model  # type: ignore[assignment]
            resolved_model_name = getattr(model, "model_name", None)
        else:
            resolved_model_name = model or llm_default_model
            self.llm = ChatOpenAI(
                base_url=llm_url,
                api_key=llm_api_key,
                model=resolved_model_name,
                temperature=temperature,
                timeout=timeout,
            )
        self.model_name = resolved_model_name
        self.file_list = None
        self.history = []
        self.history_len = history_len
        self.logger = logger
        self.memory_strategy: Optional[BaseMemoryStrategy] = None
        
        # MCP支持
        self.mcp_caller = None
        self.mcp_configs = mcp_configs
        self._mcp_initialized = False
        
        if mcp_configs and MCP_AVAILABLE:
            self.mcp_caller = MCPToolCaller(mcp_configs)

        memory_options = memory_options or {}
        if memory_strategy is not None:
            self.set_memory_strategy(memory_strategy, **memory_options)

    def _default_summarize_text(self, prompt: str) -> str:
        """使用底层 ChatOpenAI 模型生成摘要。"""
        result = self.llm.invoke([{"role": "user", "content": prompt}])
        if hasattr(result, "content"):
            return str(result.content).strip()
        if isinstance(result, dict) and "content" in result:
            return str(result["content"]).strip()
        return str(result).strip()

    def set_memory_strategy(
        self,
        strategy: Optional[Union[str, Dict[str, Any], BaseMemoryStrategy]],
        **kwargs: Any,
    ) -> None:
        """配置对话记忆策略。"""

        if strategy is None:
            self.memory_strategy = None
            return

        extra = dict(kwargs)
        summarizer = extra.pop("summarizer", None) or self._default_summarize_text
        token_counter = extra.pop("token_counter", None)

        self.memory_strategy = create_memory_strategy(
            strategy,
            summarizer=summarizer,
            token_counter=token_counter,
            **extra,
        )

        if self.memory_strategy is not None:
            self.memory_strategy.reset()

    def _apply_memory_strategy(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not self.memory_strategy:
            return messages
        try:
            return self.memory_strategy.process(messages)
        except Exception as exc:
            if self.logger:
                print(f"记忆策略处理失败，已回退到原始消息: {exc}")
            return messages

    def clear_history(self) -> None:
        """清空历史并重置记忆策略状态。"""

        self.history.clear()
        if self.memory_strategy:
            self.memory_strategy.reset()

    async def init_mcp(self):
        """初始化MCP连接（异步）"""
        if self.mcp_caller and not self._mcp_initialized:
            try:
                await self.mcp_caller.connect_servers()
                self._mcp_initialized = True
                if self.logger:
                    print("MCP服务器连接成功")
            except Exception as e:
                if self.logger:
                    print(f"MCP服务器连接失败: {e}")
                self.mcp_caller = None
    
    async def cleanup_mcp(self):
        """清理MCP连接（异步）"""
        if self.mcp_caller and self._mcp_initialized:
            try:
                await self.mcp_caller.disconnect_servers()
                self._mcp_initialized = False
                if self.logger:
                    print("MCP服务器连接已断开")
            except Exception as e:
                if self.logger:
                    print(f"MCP服务器断开连接失败: {e}")
    
    def _ensure_mcp_initialized(self):
        """确保MCP已初始化（同步方法中使用）"""
        if self.mcp_caller and not self._mcp_initialized:
            try:
                # 尝试在事件循环中运行
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果循环正在运行，创建任务但不等待
                    asyncio.create_task(self.init_mcp())
                else:
                    # 如果没有运行的循环，直接运行
                    loop.run_until_complete(self.init_mcp())
            except Exception as e:
                if self.logger:
                    print(f"MCP初始化失败: {e}")
                self.mcp_caller = None

    def build_knowledge_base(self, file_list, persist_dir="rag_chroma_db", collection_name="rag_demo", max_len=1000, overlap=100):
        self.file_list = file_list
        collection = build_multi_file_knowledge_base(
            file_list, persist_dir=persist_dir, collection_name=collection_name, max_len=max_len, overlap=overlap
        )
        return collection
        

    # def _build_prompt(self, prompt, docs=None, parser=None, caller=None):
    #     history_text = ""
    #     if self.history_len > 0:
    #         for item in self.history[-self.history_len:]:
    #             history_text += f"user: {item['prompt']}\nassistant: {item['response']}\n"

    #     if docs:
    #         context = "\n\n".join(
    #             doc["content"] if isinstance(doc, dict) and "content" in doc else doc for doc in docs
    #         )
    #         full_prompt = (
    #             history_text 
    #             + "\nuser: " 
    #             + f"你是知识库问答助手。请根据以下知识内容回答用户问题。\n\n知识内容：\n{context}\n\n用户问题：{prompt}\n\n请简明回答："
    #         )
    #     else:
    #         full_prompt = history_text + "user: " + prompt
        
    #     if parser:
    #         format_instructions = parser.get_format_instructions()
    #         full_prompt += "\n\n" + format_instructions

    #     if caller:
    #         full_prompt += "\n\n" + caller.get_instructions()

    #     return full_prompt

    def _build_prompt(self, prompt, docs=None, parser=None, caller=None):
        """构建消息格式（推荐用于ChatOpenAI）"""
        # 系统消息
        system_parts = ["你是一个智能助手，请根据用户要求提供准确、有用的回答。"]
        
        if parser:
            system_parts.append(f"最终输出格式要求：<FINAL_OUTPUT>\n{parser.get_format_instructions()}\n\n\n</FINAL_OUTPUT>")
        
        if caller:
            system_parts.append(f"工具使用说明：<TOOL_USAGE>\n{caller.get_instructions()}\n</TOOL_USAGE>")
        
        if docs:
            context_text = "\n\n".join(
                doc["content"] if isinstance(doc, dict) and "content" in doc else doc for doc in docs
            )
            system_parts.append(f"你是知识库问答助手。请根据提供的知识内容回答用户问题。<DOCUMENTATIONS>\n{context_text}\n</DOCUMENTATIONS>")

        messages = [{"role": "system", "content": "\n\n".join(system_parts)}]
        
        # 历史对话
        history_slice: List[Dict[str, str]] = []
        if self.history_len > 0:
            history_slice = self.history[-self.history_len:]

        for item in history_slice:
            messages.append({"role": "user", "content": item['prompt']})
            messages.append({"role": "assistant", "content": item['response']})
        
        # 当前用户消息
        user_content = prompt
        
        messages.append({"role": "user", "content": user_content})
        
        if self.history_len > 0 and self.memory_strategy:
            messages = self._apply_memory_strategy(messages)
        return messages

    def _invoke_llm(self, full_prompt, **kwargs):
        if self.logger:
            result = self.llm.invoke(full_prompt, **kwargs, config={"callbacks": [CustomCallbackHandler()]})
        else:
            result = self.llm.invoke(full_prompt, **kwargs)

        if hasattr(result, "content"):
            content = result.content
        elif isinstance(result, dict) and "content" in result:
            content = result["content"]
        else:
            content = str(result)
        return content

    async def _ainvoke_llm(self, full_prompt, **kwargs):
        if self.logger:
            result = await self.llm.ainvoke(full_prompt, **kwargs, config={"callbacks": [CustomCallbackHandler()]})
        else:
            result = await self.llm.ainvoke(full_prompt, **kwargs)

        if hasattr(result, "content"):
            content = result.content
        elif isinstance(result, dict) and "content" in result:
            content = result["content"]
        else:
            content = str(result)

        return content

    def _parse_template_output(self, parser, caller, content, full_prompt=None, max_retry=5, **kwargs):
        if caller:
            if hasattr(caller, 'call') and asyncio.iscoroutinefunction(caller.call):
                raise RuntimeError(
                    "检测到MCP工具调用需要异步执行，但当前在运行的事件循环中。"
                    "请使用 'await llm.call_async()' 代替 'llm.call()'"
                )
            else:
                tool_name, tool_result = caller.call(content)
            if tool_result is not None:
                return {"tool_name": tool_name, "tool_result": tool_result, "llm_output": content}

        if parser:
            parsed = parser.validate(content)
            retry_count = 0
            last_content = content
            while isinstance(parsed, dict) and not parsed.get("success", True) and retry_count < max_retry:
                retry_count += 1
                # 重新生成
                last_content = self._invoke_llm(full_prompt, **kwargs)
                parsed = parser.validate(last_content)
            return parsed
        else:
            return content

    def call(self, prompt, docs=None, parser=None, caller=None, use_mcp=False, max_retry=2, **kwargs):
        """
        通用问答接口，支持传统工具调用和MCP工具调用
        
        Args:
            prompt: 用户问题
            docs: 可选，知识块列表。传入则自动拼接为RAG问答，否则普通对话
            parser: 可选，结构化输出模板解析器
            caller: 可选，传统工具调用器
            use_mcp: 是否使用MCP工具（优先级高于传统工具）
            max_retry: 模板解析失败时最大重试次数
        """
        # 确定使用哪个工具调用器
        effective_caller = None
        
        if use_mcp and self.mcp_caller:
            # 确保MCP已初始化
            self._ensure_mcp_initialized()
            if self._mcp_initialized:
                effective_caller = self.mcp_caller
                if self.logger:
                    print("使用MCP工具调用器")
            else:
                if self.logger:
                    print("MCP未初始化，回退到传统工具调用器")
                effective_caller = caller
        else:
            effective_caller = caller

        full_prompt = self._build_prompt(prompt, docs, parser, effective_caller)
        content = self._invoke_llm(full_prompt, **kwargs)
        self.history.append({"prompt": prompt, "response": content})
        return self._parse_template_output(parser, effective_caller, content, full_prompt=full_prompt, max_retry=max_retry, **kwargs)

    async def _parse_template_output_async(self, parser, caller, content, full_prompt=None, max_retry=5, **kwargs):
        """异步版本的模板输出解析"""
        if caller:
            if hasattr(caller, 'call') and asyncio.iscoroutinefunction(caller.call):
                # MCP调用器使用异步调用
                tool_name, tool_result = await caller.call(content)
            else:
                # 传统调用器使用同步调用
                tool_name, tool_result = caller.call(content)
            
            if tool_result is not None:
                return {"tool_name": tool_name, "tool_result": tool_result, "llm_output": content}

        if parser:
            parsed = parser.validate(content)
            retry_count = 0
            last_content = content
            while isinstance(parsed, dict) and not parsed.get("success", True) and retry_count < max_retry:
                retry_count += 1
                # 重新生成
                last_content = await self._ainvoke_llm(full_prompt, **kwargs)
                parsed = parser.validate(last_content)
            return parsed
        else:
            return content

    async def call_async(self, prompt, docs=None, parser=None, caller=None, use_mcp=False, max_retry=2, **kwargs):
        """
        异步版本的通用问答接口，支持传统工具调用和MCP工具调用
        
        Args:
            prompt: 用户问题
            docs: 可选，知识块列表。传入则自动拼接为RAG问答，否则普通对话
            parser: 可选，结构化输出模板解析器
            caller: 可选，传统工具调用器
            use_mcp: 是否使用MCP工具（优先级高于传统工具）
            max_retry: 模板解析失败时最大重试次数
        """
        # 确定使用哪个工具调用器
        effective_caller = None
        
        if use_mcp and self.mcp_caller:
            # 确保MCP已初始化
            if not self._mcp_initialized:
                await self.init_mcp()
            if self._mcp_initialized:
                effective_caller = self.mcp_caller
                if self.logger:
                    print("使用MCP工具调用器")
            else:
                if self.logger:
                    print("MCP未初始化，回退到传统工具调用器")
                effective_caller = caller
        else:
            effective_caller = caller

        full_prompt = self._build_prompt(prompt, docs, parser, effective_caller)
        content = await self._ainvoke_llm(full_prompt, **kwargs)
        self.history.append({"prompt": prompt, "response": content})
        return await self._parse_template_output_async(parser, effective_caller, content, full_prompt=full_prompt, max_retry=max_retry, **kwargs)


    def get_embedding(self, text):
        return get_embedding(text)

    def search_knowledge(self, query, top_k=5, meta_filter=None, persist_dir="rag_chroma_db", collection_name="rag_demo"):
        return search_knowledge_base(query, persist_dir=persist_dir, collection_name=collection_name, top_k=top_k, meta_filter=meta_filter)

    def get_history(self):
        return self.history
    
    def get_available_tools(self, tool_type="all"):
        """
        获取可用工具列表
        
        Args:
            tool_type: 工具类型 ("all", "mcp", "traditional")
        """
        tools = []
        
        if tool_type in ["all", "mcp"] and self.mcp_caller and self._mcp_initialized:
            mcp_tools = self.mcp_caller.get_available_tools()
            tools.extend([f"MCP: {tool}" for tool in mcp_tools])
        
        return tools
    
    def __enter__(self):
        """上下文管理器支持"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器清理"""
        if self.mcp_caller and self._mcp_initialized:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.cleanup_mcp())
                else:
                    loop.run_until_complete(self.cleanup_mcp())
            except Exception as e:
                if self.logger:
                    print(f"清理MCP连接时出错: {e}")


# 便捷函数
def create_llm_with_mcp(mcp_server_configs=None, **llm_kwargs):
    """
    创建支持MCP的LLM实例
    
    Args:
        mcp_server_configs: MCP服务器配置列表
        **llm_kwargs: LLM的其他参数
    """
    return LLM(mcp_configs=mcp_server_configs, **llm_kwargs)




# 用法示例
if __name__ == "__main__":
    import asyncio

    # 定义传统工具函数
    def add(a: float, b: float) -> float:
        return a + b

    def echo(text: str) -> str:
        return text

    def multiply(a: float, b: float) -> float:
        return a * b

    # 构建传统工具调用器
    traditional_caller = LLMToolCaller([add, echo, multiply])

    async def run_examples():
        # 创建MCP配置（如果需要）
        mcp_configs = None
        if MCP_AVAILABLE:
            from .mcp_client import MCPServerConfig, MCPTransportType
            mcp_configs = [
                MCPServerConfig(
                    name="demo",
                    command="python",
                    args=["-m", "demo.demo_mcp_server"],
                    transport=MCPTransportType.STDIO
                )
            ]

        # 创建LLM
        llm = LLM(logger=True, mcp_configs=mcp_configs)
        
        try:
            # 手动初始化MCP（可选）
            if mcp_configs:
                await llm.init_mcp()

            print("=== 普通对话示例 ===")
            answer = llm.call("你是谁")
            print(f"普通对话: {answer}")

            print("\n=== 传统工具调用示例 ===")
            tool_result = llm.call("请帮我计算 3 + 5", caller=traditional_caller)
            print(f"传统工具结果: {tool_result}")

            if MCP_AVAILABLE and mcp_configs:
                print("\n=== MCP工具调用示例 ===")
                mcp_result = await llm.call_async("请帮我计算 10 * 2", use_mcp=True)
                print(f"MCP工具结果: {mcp_result}")

                print("\n=== 可用工具列表 ===")
                all_tools = llm.get_available_tools()
                print(f"所有工具: {all_tools}")

            """知识库使用示例"""
            file_list = [
                {"file_path":"data/需求文件/需求分析报告-湖北中烟新型烟草产品调研与开发信息反馈系统项目.docx", "type":"需求文档"},
                {"file_path":"data/需求文件/湖北中烟工程中心数字管理应用用户操作手册v1.0.docx", "type":"用户手册"},
                {"file_path":"data/需求文件/数字信息化管理应用系统接口文档.docx", "type":"技术文档"}
            ]
            
            # 注意：这里假设文件存在，实际使用时请确保文件路径正确
            try:
                llm.build_knowledge_base(file_list)
                query = "请简要介绍用户手册的主要内容。"
                docs = llm.search_knowledge(query, collection_name="rag_demo")
                print("\n【检索到的知识块】")
                for i, doc in enumerate(docs):
                    print(f"Top{i+1}:\n{doc}\n------")
                answer = llm.call(query, docs=docs)
                print("\n【RAG答案】\n", answer)
            except Exception as e:
                print(f"知识库示例跳过（文件不存在）: {e}")

            """结构化输出示例"""
            template = "姓名={name:str}，年龄={age:int}，模型={model:json:MyModel}，激活={active:bool}"
            parser = TemplateParser(template, model_map={"MyModel": MyModel})
            query = "请输出一个用户信息示例"
            result = llm.call(query, parser=parser, caller=traditional_caller)
            print("\n【结构化解析】\n", result)

            """表格结构化解析示例"""
            table_query = "请输出10行以上的表格内容。"
            table_parser = TableParser(TableModel, value_only=True)
            table_result = llm.call(table_query, parser=table_parser, caller=traditional_caller)
            print("\n【表格解析】\n", table_result)
            if isinstance(table_result, dict) and 'data' in table_result:
                rows = table_result['data']['table']['rows']
                print("\ntsv格式输出：")
                print(table_parser.to_tsv(rows))

        finally:
            # 清理MCP连接
            await llm.cleanup_mcp()

    # 同步方式使用（简化版本）
    def sync_example():
        print("\n=== 同步使用示例 ===")
        
        # 创建不带MCP的LLM
        llm = LLM(logger=True)
        
        # 使用上下文管理器
        with llm:
            result = llm.call("Hello, world!", caller=traditional_caller)
            print(f"同步结果: {result}")

    # 运行异步示例
    print("运行异步示例...")
    asyncio.run(run_examples())
    
    # 运行同步示例
    sync_example()