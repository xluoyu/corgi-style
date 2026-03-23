"""LangGraph StateGraph 工作流组装"""
from typing import AsyncGenerator
import asyncio
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.agent.graph.state import GraphState
from app.agent.graph.edges import (
    route_by_intent,
    route_by_score
)

# 导入节点（延迟导入避免循环依赖）
from app.agent.graph.nodes import intent as intent_node_module
from app.agent.graph.nodes import weather as weather_node_module
from app.agent.graph.nodes import wardrobe as wardrobe_node_module
from app.agent.graph.nodes import planning as planning_node_module
from app.agent.graph.nodes import retrieval as retrieval_node_module
from app.agent.graph.nodes import evaluation as evaluation_node_module
from app.agent.graph.nodes import feedback as feedback_node_module
from app.agent.graph.nodes import response as response_node_module


def create_workflow(db: Session):
    """创建并编译 StateGraph 工作流"""
    workflow = StateGraph(GraphState)

    # 添加所有节点
    workflow.add_node("intent", _wrap_async(intent_node_module.intent_node))
    workflow.add_node("weather", _wrap_async(weather_node_module.weather_node))
    workflow.add_node("wardrobe_query", _wrap_async_with_db(wardrobe_node_module.wardrobe_query_node, db))
    workflow.add_node("outfit_planning", _wrap_async(planning_node_module.outfit_planning_node))
    workflow.add_node("clothes_retrieval", _wrap_async_with_db(retrieval_node_module.clothes_retrieval_node, db))
    workflow.add_node("outfit_evaluation", _wrap_async(evaluation_node_module.outfit_evaluation_node))
    workflow.add_node("feedback", _wrap_async(feedback_node_module.feedback_node))
    workflow.add_node("response", _wrap_async(response_node_module.response_node))

    # 入口
    workflow.set_entry_point("intent")

    # Intent 路由
    workflow.add_conditional_edges(
        "intent",
        route_by_intent,
        {
            "wardrobe_query": "wardrobe_query",
            "generate_outfit": "generate_outfit",
            "feedback": "feedback",
            "response": "response"
        }
    )

    # === generate_outfit 分支 ===
    workflow.add_node("generate_outfit", _make_generate_outfit_subgraph(db))

    # === feedback 分支 ===
    # feedback → outfit_planning（重新规划）
    workflow.add_edge("feedback", "outfit_planning")

    # === 线性边 ===
    workflow.add_edge("wardrobe_query", "response")
    workflow.add_edge("response", END)

    return workflow.compile()


def _make_generate_outfit_subgraph(db: Session):
    """穿搭生成的简化子图"""
    subgraph = StateGraph(GraphState)

    # 节点
    subgraph.add_node("weather", _wrap_async(weather_node_module.weather_node))
    subgraph.add_node("wardrobe_query", _wrap_async_with_db(wardrobe_node_module.wardrobe_query_node, db))
    subgraph.add_node("outfit_planning", _wrap_async(planning_node_module.outfit_planning_node))
    subgraph.add_node("clothes_retrieval", _wrap_async_with_db(retrieval_node_module.clothes_retrieval_node, db))
    subgraph.add_node("outfit_evaluation", _wrap_async(evaluation_node_module.outfit_evaluation_node))
    subgraph.add_node("response", _wrap_async(response_node_module.response_node))

    # 入口
    subgraph.set_entry_point("weather")

    # 线性流程
    subgraph.add_edge("weather", "wardrobe_query")
    subgraph.add_edge("wardrobe_query", "outfit_planning")
    subgraph.add_edge("outfit_planning", "clothes_retrieval")
    subgraph.add_edge("clothes_retrieval", "outfit_evaluation")

    # 条件分支
    subgraph.add_conditional_edges(
        "outfit_evaluation",
        route_by_score,
        {
            "high_score": "response",
            "low_score": "outfit_planning"  # 重试
        }
    )

    subgraph.add_edge("response", END)

    return subgraph.compile()


def _wrap_async(func):
    """包装同步函数为异步函数（用于 LangGraph）"""
    async def wrapper(state):
        return await func(state)
    return wrapper


def _wrap_async_with_db(func, db: Session):
    """包装需要 db 的异步函数"""
    async def wrapper(state):
        return await func(state, db)
    return wrapper


class DialogueWorkflow:
    """对话工作流管理器"""

    def __init__(self, db: Session):
        self.db = db
        self.graph = create_workflow(db)

    async def run(self, initial_state: GraphState) -> GraphState:
        """运行工作流"""
        result = await self.graph.ainvoke(initial_state)
        return result

    async def run_stream(self, initial_state: GraphState) -> AsyncGenerator[GraphState, None]:
        """流式运行工作流"""
        async for state in self.graph.astream(initial_state):
            yield state
