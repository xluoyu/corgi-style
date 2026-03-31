"""LangGraph Multi-Agent 工作流组装 v3.0

基于 LangGraph 的多 Agent 协调架构：
- SupervisorAgent: 协调者，负责意图识别和任务分发
- WeatherAgent: 天气查询
- WardrobeAgent: 衣柜管理
- OutfitAdvisorAgent: 穿搭推荐
- KnowledgeAgent: 知识问答

Agent 之间通过共享 State 传递数据，而非 Tool Call。
"""
from typing import AsyncGenerator, Literal, Dict, Any, Union
import asyncio
import logging
import json

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.agent.graph.state_v2 import GraphState
from app.agent.agents.supervisor import (
    supervisor_node,
    weather_agent_node,
    wardrobe_agent_node,
    outfit_advisor_agent_node,
    knowledge_agent_node,
    AGENT_NODES,
)

logger = logging.getLogger(__name__)


# ============================================================
# 编译后的 Graph 缓存
# ============================================================

_compiled_graph_cache: dict = {}


def _route_after_supervisor(state: GraphState) -> Literal[
    "weather_agent",
    "wardrobe_agent",
    "outfit_advisor_agent",
    "knowledge_agent",
    "response",
    END
]:
    """
    Supervisor 决定后的路由

    Returns:
        要执行的 Agent 节点名，或 END
    """
    routing = state.get("routing_decision", "")

    if state.get("should_end"):
        logger.info(f"[_route_after_supervisor] 直接结束")
        return END

    if routing in AGENT_NODES:
        logger.info(f"[_route_after_supervisor] 路由到 {routing}")
        return routing

    if routing == "direct":
        logger.info(f"[_route_after_supervisor] 直接回答")
        return "response"

    # 默认直接回答
    logger.info(f"[_route_after_supervisor] 默认路由到 response")
    return "response"


def _route_after_agent(state: GraphState) -> Literal[
    "weather_agent",
    "wardrobe_agent",
    "outfit_advisor_agent",
    "knowledge_agent",
    "supervisor",
    "response",
    END
]:
    """
    Agent 执行完成后的路由

    根据 Agent 结果决定下一步：
    - 如果需要其他 Agent 继续处理 → 调用下一个 Agent
    - 否则 → 返回 supervisor 重新分析
    """
    last_agent = state.get("last_agent", "")
    agent_result = state.get("agent_result", {})

    # 检查是否有错误
    if isinstance(agent_result, dict) and agent_result.get("error"):
        logger.info(f"[_route_after_agent] Agent {last_agent} 返回错误: {agent_result['error']}")
        return "response"  # 出错则返回 response 生成错误回复

    # 根据 Agent 类型决定下一步
    if last_agent == "weather_agent":
        # 天气查询完成后，可以继续查衣柜或生成穿搭
        if not state.get("wardrobe_items"):
            return "wardrobe_agent"
        if not state.get("outfit_plan"):
            return "outfit_advisor_agent"
        return "response"

    elif last_agent == "wardrobe_agent":
        # 衣柜查询完成后，可以生成穿搭
        if not state.get("outfit_plan"):
            return "outfit_advisor_agent"
        return "response"

    elif last_agent == "outfit_advisor_agent":
        # 穿搭推荐完成
        return "response"

    elif last_agent == "knowledge_agent":
        # 知识查询完成
        return "response"

    return "response"


async def response_node(state: GraphState) -> GraphState:
    """
    响应生成节点

    根据 Agent 结果生成最终回复
    """
    from app.agent.graph.nodes.response import _handle_generate_outfit, _handle_wardrobe_query

    routing = state.get("routing_decision", "")
    agent_result = state.get("agent_result", {})

    # 根据路由和结果生成回复
    if isinstance(agent_result, dict) and agent_result.get("error"):
        response_text = f"抱歉，发生了错误：{agent_result['error']}"
        state["response_data"] = {"type": "error", "content": response_text}
    elif routing == "weather_agent":
        weather = state.get("weather_data", {})
        temp = weather.get("temperature", "未知")
        city = state.get("target_city", "")
        response_text = f"{city}今天的天气是{weather.get('condition', '未知')}，温度{temp}℃"
        state["response_data"] = {"type": "text", "content": response_text}
    elif routing == "wardrobe_agent":
        items = state.get("wardrobe_items", [])
        if items:
            response_text = f"您的衣柜里有{len(items)}件衣物"
        else:
            response_text = "您的衣柜里还没有衣物哦"
        state["response_data"] = {"type": "text", "content": response_text}
    elif routing == "outfit_advisor_agent" or state.get("outfit_plan"):
        # 生成穿搭回复
        response_text, data = _handle_generate_outfit(state)
        state["response_data"] = data
    elif state.get("supervisor_response"):
        response_text = state["supervisor_response"]
        state["response_data"] = {"type": "text", "content": response_text}
    else:
        response_text = "抱歉，我暂时无法处理这个请求"
        state["response_data"] = {"type": "text", "content": response_text}

    # 更新消息
    messages = state.get("messages", [])
    messages.append({"role": "assistant", "content": response_text})
    state["messages"] = messages
    state["should_end"] = True

    logger.info(f"[ResponseNode] 生成回复: {response_text[:50]}")

    return state


def _build_multi_agent_workflow(db: Session) -> StateGraph:
    """
    构建多 Agent 工作流

    流程：
    supervisor → weather_agent/wardrobe_agent/outfit_advisor_agent/knowledge_agent
                ↓
              response
    """
    workflow = StateGraph(GraphState)

    # === Supervisor 节点 ===
    workflow.add_node("supervisor", supervisor_node)

    # === Agent 节点 ===
    workflow.add_node("weather_agent", weather_agent_node)
    workflow.add_node("wardrobe_agent", wardrobe_agent_node)
    workflow.add_node("outfit_advisor_agent", outfit_advisor_agent_node)
    workflow.add_node("knowledge_agent", knowledge_agent_node)

    # === 响应节点 ===
    workflow.add_node("response", response_node)

    # === 入口 ===
    workflow.set_entry_point("supervisor")

    # === Supervisor → Agent/Response ===
    workflow.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "weather_agent": "weather_agent",
            "wardrobe_agent": "wardrobe_agent",
            "outfit_advisor_agent": "outfit_advisor_agent",
            "knowledge_agent": "knowledge_agent",
            "response": "response",
            END: END,
        }
    )

    # === Agent → Agent/Response ===
    workflow.add_conditional_edges(
        "weather_agent",
        _route_after_agent,
        {
            "wardrobe_agent": "wardrobe_agent",
            "outfit_advisor_agent": "outfit_advisor_agent",
            "response": "response",
            "supervisor": "supervisor",
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "wardrobe_agent",
        _route_after_agent,
        {
            "outfit_advisor_agent": "outfit_advisor_agent",
            "response": "response",
            "supervisor": "supervisor",
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "outfit_advisor_agent",
        _route_after_agent,
        {
            "response": "response",
            "supervisor": "supervisor",
            END: END,
        }
    )

    workflow.add_conditional_edges(
        "knowledge_agent",
        _route_after_agent,
        {
            "response": "response",
            "supervisor": "supervisor",
            END: END,
        }
    )

    # === Response → 结束 ===
    workflow.add_edge("response", END)

    return workflow


def get_compiled_workflow_v3(db: Session):
    """获取编译后的多 Agent 工作流"""
    cache_key = "multi_agent_workflow_v3"
    if cache_key not in _compiled_graph_cache:
        graph = _build_multi_agent_workflow(db)
        _compiled_graph_cache[cache_key] = graph.compile()
    return _compiled_graph_cache[cache_key]


# ============================================================
# 对话工作流管理器 v3.0（多 Agent）
# ============================================================

class DialogueWorkflowV3:
    """多 Agent 对话工作流管理器"""

    def __init__(self, db: Session):
        self.db = db
        self.graph = get_compiled_workflow_v3(db)

    async def run(self, initial_state: GraphState) -> GraphState:
        """运行工作流"""
        result = await self.graph.ainvoke(initial_state)
        return result

    async def run_stream(self, initial_state: GraphState) -> AsyncGenerator[GraphState, None]:
        """流式运行工作流"""
        async for state in self.graph.astream(initial_state):
            yield state

    async def run_stream_sse(
        self, initial_state: GraphState
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式运行工作流，生成 SSE 格式事件

        生成的事件类型：
        - thinking: 思考中
        - routing_decision: 路由决定
        - agent_started: Agent 开始执行
        - agent_finished: Agent 执行完成
        - agent_result: Agent 执行结果
        - response: 最终响应生成
        - done: 完成
        - error: 错误
        """
        last_agent = None

        async for state in self.graph.astream(initial_state):
            # 检测当前节点（通过 routing_decision 或 last_agent）
            routing = state.get("routing_decision", "")
            current_agent = state.get("last_agent", routing)

            # 检测节点变化，生成事件
            if current_agent != last_agent:
                if last_agent is not None:
                    # 上一个 Agent 完成
                    yield {
                        "type": "agent_finished",
                        "agent": last_agent,
                        "result": state.get("agent_result"),
                    }

                if current_agent and current_agent not in ["response", "END", "supervisor"]:
                    # 新 Agent 开始
                    yield {
                        "type": "agent_started",
                        "agent": current_agent,
                    }

                last_agent = current_agent

            # 根据路由状态生成事件
            if routing == "supervisor" or routing == "direct":
                if state.get("supervisor_response"):
                    yield {
                        "type": "thinking",
                        "content": state["supervisor_response"][:100],
                    }
                else:
                    yield {
                        "type": "thinking",
                        "content": "正在分析您的请求...",
                    }
            elif routing in AGENT_NODES:
                yield {
                    "type": "routing_decision",
                    "agent": routing,
                    "params": state.get("routing_params", {}),
                }
            elif routing == "response" or state.get("should_end"):
                # 最终响应
                response_data = state.get("response_data", {})
                if response_data:
                    yield {
                        "type": "response",
                        "content": response_data.get("content", ""),
                        "data": response_data,
                    }
                else:
                    # 从 messages 获取
                    messages = state.get("messages", [])
                    for msg in reversed(messages):
                        if msg.get("role") == "assistant":
                            yield {
                                "type": "response",
                                "content": msg.get("content", ""),
                                "data": state.get("response_data"),
                            }
                            break

            yield {
                "type": "state_update",
                "state": {
                    "routing_decision": state.get("routing_decision"),
                    "last_agent": state.get("last_agent"),
                    "agent_result": state.get("agent_result"),
                    "weather_data": state.get("weather_data"),
                    "wardrobe_items_count": len(state.get("wardrobe_items", [])),
                    "outfit_plan": state.get("outfit_plan") is not None,
                    "should_end": state.get("should_end", False),
                },
            }

        # 确保最后一个 Agent 完成
        if last_agent and last_agent not in ["response", "END"]:
            yield {
                "type": "agent_finished",
                "agent": last_agent,
            }

        yield {"type": "done", "content": ""}
