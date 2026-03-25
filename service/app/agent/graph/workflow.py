"""LangGraph StateGraph 工作流组装"""
from typing import AsyncGenerator, Literal
import asyncio
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.agent.graph.state import GraphState
from app.agent.graph.edges import route_by_intent

# 导入节点（延迟导入避免循环依赖）
from app.agent.graph.nodes import intent as intent_node_module
from app.agent.graph.nodes import weather as weather_node_module
from app.agent.graph.nodes import wardrobe as wardrobe_node_module
from app.agent.graph.nodes import planning as planning_node_module
from app.agent.graph.nodes import retrieval as retrieval_node_module
from app.agent.graph.nodes import evaluation as evaluation_node_module
from app.agent.graph.nodes import feedback as feedback_node_module
from app.agent.graph.nodes import response as response_node_module
from app.agent.graph.nodes import analysis as analysis_node_module


# =============================================================================
# Wrapper 函数（节点执行前后注入 next_node，方便流式追踪）
# =============================================================================

def _wrap_async(func, node_name: str = None):
    """包装异步节点函数，注入 next_node"""
    async def wrapper(state):
        if node_name:
            state["next_node"] = node_name
        return await func(state)
    return wrapper


def _wrap_async_with_db(func, db: Session, node_name: str = None):
    """包装需要 db 的异步节点函数"""
    async def wrapper(state):
        if node_name:
            state["next_node"] = node_name
        return await func(state, db)
    return wrapper


# =============================================================================
# 编译后的 Graph 缓存（避免每次请求都重新编译 StateGraph）
# =============================================================================

_compiled_graph_cache: dict = {}  # {"main": compiled_graph, "subgraph": subgraph}


def _route_by_pending_intent(state: GraphState) -> Literal["generate_outfit", "end"]:
    """
    只有当 pending_intent == "generate_outfit" 且 outfit_plan 还不存在时，重新进入子图。
    如果 should_end=True，说明正常结束（追问），直接结束。
    """
    if state.get("should_end"):
        return "end"
    if state.get("pending_intent") == "generate_outfit" and not state.get("outfit_plan"):
        # 清除 pending_intent，避免子图执行后再次触发
        state["pending_intent"] = None
        return "generate_outfit"
    return "end"


async def _check_pending_generate_node(state: GraphState) -> GraphState:
    """
    检查是否有待触发的 generate_outfit 意图。

    由 response_node 在 city+scene 完整时设置 pending_intent，
    本节点负责将流程重新路由到 generate_outfit 子图。
    """
    return state


def _build_graph_structure(db: Session):
    """构建图结构（不含缓存包装，返回原始 StateGraph）"""
    workflow = StateGraph(GraphState)

    workflow.add_node("intent",           _wrap_async(intent_node_module.intent_node, "intent"))
    workflow.add_node("weather",           _wrap_async(weather_node_module.weather_node, "weather"))
    workflow.add_node("wardrobe_query",   _wrap_async_with_db(wardrobe_node_module.wardrobe_query_node, db, "wardrobe_query"))
    workflow.add_node("outfit_planning",  _wrap_async(planning_node_module.outfit_planning_node, "outfit_planning"))
    workflow.add_node("clothes_retrieval", _wrap_async_with_db(retrieval_node_module.clothes_retrieval_node, db, "clothes_retrieval"))
    workflow.add_node("outfit_evaluation", _wrap_async(evaluation_node_module.outfit_evaluation_node, "outfit_evaluation"))
    workflow.add_node("feedback",         _wrap_async(feedback_node_module.feedback_node, "feedback"))
    workflow.add_node("response",         _wrap_async(response_node_module.response_node, "response"))

    workflow.set_entry_point("intent")

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

    workflow.add_node("generate_outfit", _make_generate_outfit_subgraph(db))

    workflow.add_edge("feedback", "outfit_planning")
    workflow.add_edge("wardrobe_query", "response")
    workflow.add_edge("response", "check_pending_generate")
    workflow.add_node("check_pending_generate", _wrap_async(_check_pending_generate_node, "check_pending_generate"))
    workflow.add_conditional_edges(
        "check_pending_generate",
        _route_by_pending_intent,
        {
            "generate_outfit": "generate_outfit",
            "end": END,
        }
    )

    return workflow


def get_compiled_workflow(db: Session):
    """获取编译后的主工作流（使用缓存）"""
    cache_key = "main_workflow"
    if cache_key not in _compiled_graph_cache:
        graph = _build_graph_structure(db)
        _compiled_graph_cache[cache_key] = graph.compile()
    return _compiled_graph_cache[cache_key]


# =============================================================================
# 主工作流
# =============================================================================

def create_workflow(db: Session):
    """创建并编译 StateGraph 主工作流（内部使用缓存）"""
    return get_compiled_workflow(db)


def _make_generate_outfit_subgraph(db: Session):
    """
    穿搭生成的子图（无重试循环版）

    weather → wardrobe_query → wardrobe_analysis → outfit_planning → clothes_retrieval → response

    - wardrobe_analysis：分析库存，标记缺失品类
    - outfit_planning：LLM 基于实际库存规划，缺失品类用文字建议
    - clothes_retrieval：只检索衣柜中已有的品类
    - 无 evaluation 和重试循环
    """
    subgraph = StateGraph(GraphState)

    subgraph.add_node("weather",           _wrap_async(weather_node_module.weather_node, "weather"))
    subgraph.add_node("wardrobe_query",   _wrap_async_with_db(wardrobe_node_module.wardrobe_query_node, db, "wardrobe_query"))
    subgraph.add_node("wardrobe_analysis", _wrap_async(analysis_node_module.wardrobe_analysis_node, "wardrobe_analysis"))
    subgraph.add_node("outfit_planning",  _wrap_async(planning_node_module.outfit_planning_node, "outfit_planning"))
    subgraph.add_node("clothes_retrieval", _wrap_async_with_db(retrieval_node_module.clothes_retrieval_node, db, "clothes_retrieval"))
    subgraph.add_node("response",         _wrap_async(response_node_module.response_node, "response"))

    subgraph.set_entry_point("weather")

    subgraph.add_edge("weather", "wardrobe_query")
    subgraph.add_edge("wardrobe_query", "wardrobe_analysis")
    subgraph.add_edge("wardrobe_analysis", "outfit_planning")
    subgraph.add_edge("outfit_planning", "clothes_retrieval")
    subgraph.add_edge("clothes_retrieval", "response")
    subgraph.add_edge("response", END)

    return subgraph.compile()


# =============================================================================
# 对话工作流管理器
# =============================================================================

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
