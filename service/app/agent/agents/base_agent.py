"""基础 Agent 工具

提供创建 LangGraph Agent 节点的通用工具函数。
"""
import json
import re
from typing import Callable, Any, Dict, List, Optional, Union

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import BaseTool

from app.services.llm_providers import get_cached_provider


# 注释：create_react_agent 在 langchain 1.2.12 中已移除
# 如果需要创建 ReAct Agent，可以使用 langchain.agents.create_agent
# 但当前 workflow_v3 的 agents 是普通 async 函数，不需要 create_react_agent


def create_agent_node(
    agent_name: str,
    system_message: str,
    tools: List[BaseTool],
    output_key: str = "agent_output",
) -> Callable:
    """
    创建 Agent 节点的工厂函数。

    Args:
        agent_name: Agent 名称，用于日志
        system_message: 系统提示词
        tools: Agent 可用的工具列表
        output_key: Agent 输出写入 state 的 key

    Returns:
        可执行的节点函数
    """
    from app.agent.graph.state_v2 import GraphState
    from app.agent.graph.nodes.intent import _extract_text_from_content

    # 创建 ReAct Agent
    llm = get_cached_provider().chat_model

    # 使用 create_react_agent 创建 Agent
    agent = create_react_agent(
        model=llm,
        tools=tools,
        system_message=system_message,
        # 使用 stop 技术避免陷入循环
        max_iterations=10,
    )

    async def agent_node(state: GraphState) -> Dict[str, Any]:
        """Agent 节点函数"""
        import logging
        logger = logging.getLogger(f"[Agent:{agent_name}]")

        # 构建输入消息
        messages = state.get("messages", [])

        # 添加系统提示（如果需要）
        # 注意：create_react_agent 会在内部添加 system_message

        try:
            logger.info(f"[{agent_name}] 开始执行 | messages={len(messages)}")

            # 调用 Agent
            result = await agent.ainvoke({"messages": messages})

            # 提取输出
            # result 可能是 AgentFinish 或包含 messages 的 dict
            if isinstance(result, AgentFinish):
                output = result.return_values.get("output", "")
                logger.info(f"[{agent_name}] AgentFinish: {output[:100]}")
            elif isinstance(result, dict):
                output = result.get("messages", [])
                if output and isinstance(output[-1], AIMessage):
                    output = output[-1].content
                else:
                    output = str(result.get("output", ""))
            else:
                output = str(result)

            # 处理 LangChain content block 格式
            if isinstance(output, str) and output.startswith("["):
                # 可能是 content block 列表的 JSON 字符串
                try:
                    parsed = json.loads(output)
                    if isinstance(parsed, list):
                        output = _extract_text_from_content(parsed)
                except:
                    pass

            logger.info(f"[{agent_name}] 完成")

            # 返回更新
            return {
                output_key: output,
                "last_agent": agent_name,
            }

        except Exception as e:
            logger.error(f"[{agent_name}] 执行失败: {e}", exc_info=True)
            return {
                output_key: {"error": str(e)},
                "last_agent": agent_name,
            }

    return agent_node


def extract_json_from_response(text: str) -> Optional[Dict]:
    """从 LLM 响应中提取 JSON"""
    # 先尝试直接解析
    try:
        return json.loads(text)
    except:
        pass

    # 从文本中提取 JSON
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    return None


def build_agent_messages(
    user_message: str,
    context: Dict[str, Any],
    system_prompt: str,
) -> List:
    """构建 Agent 消息列表

    Args:
        user_message: 用户输入
        context: 上下文信息（天气、衣柜等）
        system_prompt: 系统提示词

    Returns:
        消息列表
    """
    messages = [SystemMessage(content=system_prompt)]

    # 添加上下文信息
    context_text = _build_context_text(context)
    if context_text:
        messages.append(HumanMessage(content=f"【上下文信息】\n{context_text}"))

    # 添加用户消息
    messages.append(HumanMessage(content=user_message))

    return messages


def _build_context_text(context: Dict[str, Any]) -> str:
    """构建上下文文本"""
    parts = []

    if context.get("weather"):
        w = context["weather"]
        temp = w.get("temperature", "未知")
        city = w.get("city", "未知")
        parts.append(f"天气：{city} {temp}℃")

    if context.get("wardrobe_items"):
        items = context["wardrobe_items"]
        parts.append(f"衣柜：共 {len(items)} 件衣物")

    if context.get("target_scene"):
        parts.append(f"场合：{context['target_scene']}")

    if context.get("target_city"):
        parts.append(f"城市：{context['target_city']}")

    return "\n".join(parts) if parts else ""
