"""Agent 核心构建器"""
import os
from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import Runnable

from app.services.llm_providers import get_cached_provider
from app.agent.prompts.system import get_system_prompt
from app.agent.tools import get_all_tools
from app.agent.memory import get_session_memory, update_session_memory


def create_conversation_agent(
    llm: BaseChatModel,
    tools: List,
    system_prompt: str
) -> Runnable:
    """
    构建对话 Agent

    使用 LangChain 的 create_tool_calling_agent 模式。
    """
    from langchain.agents import create_tool_calling_agent
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    return agent


def get_session_history_for_agent(session_id: str):
    """
    获取会话历史（用于 RunnableWithMessageHistory）

    返回一个可调用的历史消息加载器。
    """
    from app.agent.memory import memory

    class SessionHistory:
        def __init__(self, sid: str):
            self.sid = sid

        def load(self):
            import asyncio
            return asyncio.run(memory.get_messages(self.sid))

    return SessionHistory(session_id)


class ConversationAgent:
    """
    对话 Agent 封装类

    提供便捷的对话接口。
    """

    def __init__(self):
        self.llm = None
        self.tools = []
        self.system_prompt = ""

    def initialize(self):
        """初始化 Agent"""
        # 获取 LLM
        provider = get_cached_provider()
        self.llm = provider.chat_model

        # 获取 Tools
        self.tools = get_all_tools()

        # 获取 System Prompt
        self.system_prompt = get_system_prompt()

    async def chat(
        self,
        message: str,
        session_id: str,
        user_id: str,
        images: List[str] = None
    ) -> Dict[str, Any]:
        """
        处理对话

        Args:
            message: 用户消息
            session_id: 会话 ID
            user_id: 用户 ID
            images: 图片 URL 列表

        Returns:
            AI 回复和上下文更新
        """
        if not self.llm:
            self.initialize()

        # 获取短期记忆
        memory_data = await get_session_memory(session_id)
        context = memory_data.context if hasattr(memory_data, 'context') else {}

        # 构建消息
        messages = []
        if self.system_prompt:
            # 替换上下文
            formatted_prompt = self.system_prompt.format(context=context)
            messages.append(SystemMessage(content=formatted_prompt))

        # 添加用户消息
        content = message
        if images:
            # 处理图片消息
            content_parts = [{"type": "text", "text": message}]
            for img in images:
                content_parts.append({"type": "image_url", "image_url": {"url": img}})
            messages.append(HumanMessage(content=content_parts))
        else:
            messages.append(HumanMessage(content=message))

        # 调用 Agent
        from langchain.agents import create_tool_calling_agent
        from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt.format(context=context)),
            ("human", "{input}"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)

        # 简单调用（不使用 RunnableWithMessageHistory）
        result = await agent.ainvoke({
            "input": message
        })

        # 更新记忆
        await update_session_memory(
            session_id,
            user_id=user_id,
            context=context
        )

        return {
            "response": result,
            "context": context
        }


# 全局 Agent 实例
_agent_instance: Optional[ConversationAgent] = None


def get_agent() -> ConversationAgent:
    """获取全局 Agent 实例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ConversationAgent()
        _agent_instance.initialize()
    return _agent_instance


async def chat_message(
    message: str,
    session_id: str,
    user_id: str,
    images: List[str] = None
) -> Dict[str, Any]:
    """
    对话便捷函数

    Args:
        message: 用户消息
        session_id: 会话 ID
        user_id: 用户 ID
        images: 图片 URL 列表

    Returns:
        AI 回复
    """
    agent = get_agent()
    return await agent.chat(message, session_id, user_id, images)
