"""Agent 模块

架构：
- agent/core.py: Agent 构建器
- agent/memory.py: 短期记忆（Redis/Upstash）
- agent/prompts/: Prompt 模板
- agent/tools/: LangChain Tools（调用 services 层）
"""

from app.agent.core import ConversationAgent, chat_message, get_agent
from app.agent.memory import (
    ConversationMemory,
    SessionData,
    ConversationContext,
    Message,
    get_session_memory,
    update_session_memory,
    clear_session_memory,
)
from app.agent.tools import get_all_tools

__all__ = [
    # core
    "ConversationAgent",
    "chat_message",
    "get_agent",
    # memory
    "ConversationMemory",
    "SessionData",
    "ConversationContext",
    "Message",
    "get_session_memory",
    "update_session_memory",
    "clear_session_memory",
    # tools
    "get_all_tools",
]
