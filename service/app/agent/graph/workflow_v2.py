"""LangGraph StateGraph 工作流组装 v2.0

基于 LangGraph 的状态机工作流，支持 OutfitAdvisor + WardrobeCurator Agent。
对应 implementation-plan-v2.1-langgraph.md 的 Phase 1-3。
"""
from typing import AsyncGenerator, Literal
import asyncio
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.agent.graph.state_v2 import GraphState
from app.agent.graph.edges_v2 import (
    route_by_intent,
    route_generate_outfit,
    route_feedback_iteration,
    route_wardrobe_query,
)

# 导入节点（延迟导入避免循环依赖）
from app.agent.graph.nodes import intent as intent_node_module
from app.agent.graph.nodes import weather as weather_node_module
from app.agent.graph.nodes import wardrobe as wardrobe_node_module
from app.agent.graph.nodes import analysis as analysis_node_module
from app.agent.graph.nodes import response as response_node_module
from app.agent.graph.nodes import outfit_advisor as advisor_node_module


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

_compiled_graph_cache: dict = {}


def _route_by_pending_intent(state: GraphState) -> Literal["generate_outfit_flow", "end"]:
    """
    只有当 pending_intent == "generate_outfit" 且 outfit_plan 还不存在时，重新进入子图。
    如果 should_end=True，说明正常结束（追问），直接结束。
    """
    if state.get("should_end"):
        return "end"
    if state.get("pending_intent") == "generate_outfit" and not state.get("outfit_plan"):
        # 清除 pending_intent，避免子图执行后再次触发
        state["pending_intent"] = None
        return "generate_outfit_flow"
    return "end"


async def _check_pending_generate_node(state: GraphState) -> GraphState:
    """检查是否有待触发的 generate_outfit 意图。"""
    return state


def _build_graph_structure(db: Session):
    """构建图结构 v2.0（不含缓存包装，返回原始 StateGraph）"""
    workflow = StateGraph(GraphState)

    # === 核心节点 ===
    workflow.add_node("intent", _wrap_async(intent_node_module.intent_node, "intent"))
    workflow.add_node("response", _wrap_async(response_node_module.response_node, "response"))
    workflow.add_node("check_pending_generate", _wrap_async(_check_pending_generate_node, "check_pending_generate"))

    # === 子图节点 ===
    workflow.add_node("generate_outfit_flow", _make_generate_outfit_subgraph(db))
    workflow.add_node("query_wardrobe_flow", _make_query_wardrobe_subgraph(db))
    workflow.add_node("feedback_flow", _make_feedback_subgraph(db))
    workflow.add_node("wardrobe_check_flow", _make_wardrobe_check_subgraph(db))
    workflow.add_node("style_match_flow", _make_style_match_subgraph(db))
    workflow.add_node("care_guide_flow", _make_care_guide_subgraph(db))

    # === 入口 ===
    workflow.set_entry_point("intent")

    # === 主路由：intent → 子图/节点 ===
    workflow.add_conditional_edges(
        "intent",
        route_by_intent,
        {
            "generate_outfit_flow": "generate_outfit_flow",
            "query_wardrobe_flow": "query_wardrobe_flow",
            "feedback_flow": "feedback_flow",
            "wardrobe_check_flow": "wardrobe_check_flow",
            "style_match_flow": "style_match_flow",
            "care_guide_flow": "care_guide_flow",
            "get_advice_flow": "response",  # get_advice 直接响应
            "response": "response",
        }
    )

    # === 子图/节点 → response → check_pending_generate ===
    workflow.add_edge("generate_outfit_flow", "response")
    workflow.add_edge("query_wardrobe_flow", "response")
    workflow.add_edge("feedback_flow", "response")
    workflow.add_edge("wardrobe_check_flow", "response")
    workflow.add_edge("style_match_flow", "response")
    workflow.add_edge("care_guide_flow", "response")
    workflow.add_edge("response", "check_pending_generate")

    # === check_pending_generate → 重新进入子图或结束 ===
    workflow.add_conditional_edges(
        "check_pending_generate",
        _route_by_pending_intent,
        {
            "generate_outfit_flow": "generate_outfit_flow",
            "end": END,
        }
    )

    return workflow


def get_compiled_workflow(db: Session):
    """获取编译后的主工作流（使用缓存）"""
    cache_key = "main_workflow_v2"
    if cache_key not in _compiled_graph_cache:
        graph = _build_graph_structure(db)
        _compiled_graph_cache[cache_key] = graph.compile()
    return _compiled_graph_cache[cache_key]


def create_workflow(db: Session):
    """创建并编译 StateGraph 主工作流（内部使用缓存）"""
    return get_compiled_workflow(db)


# =============================================================================
# generate_outfit_flow 子图 v2.0
#
# Phase 1 简化版（无迭代）：
# weather → wardrobe_query → wardrobe_analysis → advisor_plan → advisor_evaluate → response
# =============================================================================

def _make_generate_outfit_subgraph(db: Session):
    """
    穿搭生成子图 v2.0

    Phase 1 流程：
    weather → wardrobe_query → wardrobe_analysis → advisor_plan → advisor_evaluate → response

    - wardrobe_analysis：分析库存，标记缺失品类
    - advisor_plan：OutfitAdvisor 生成穿搭方案 + 自评
    - advisor_evaluate：OutfitAdvisor 最终评价（生成 reasoning）
    """
    subgraph = StateGraph(GraphState)

    subgraph.add_node("weather", _wrap_async(weather_node_module.weather_node, "weather"))
    subgraph.add_node("wardrobe_query", _wrap_async_with_db(wardrobe_node_module.wardrobe_query_node, db, "wardrobe_query"))
    subgraph.add_node("wardrobe_analysis", _wrap_async(analysis_node_module.wardrobe_analysis_node, "wardrobe_analysis"))
    subgraph.add_node("advisor_plan", _wrap_async_with_db(advisor_node_module.advisor_plan_node, db, "advisor_plan"))
    subgraph.add_node("advisor_evaluate", _wrap_async_with_db(advisor_node_module.advisor_evaluate_node, db, "advisor_evaluate"))
    subgraph.add_node("response", _wrap_async(response_node_module.response_node, "response"))

    subgraph.set_entry_point("weather")

    subgraph.add_edge("weather", "wardrobe_query")
    subgraph.add_edge("wardrobe_query", "wardrobe_analysis")
    subgraph.add_edge("wardrobe_analysis", "advisor_plan")
    subgraph.add_edge("advisor_plan", "advisor_evaluate")
    subgraph.add_edge("advisor_evaluate", "response")
    subgraph.add_edge("response", END)

    return subgraph.compile()


# =============================================================================
# query_wardrobe_flow 子图
# =============================================================================

def _make_query_wardrobe_subgraph(db: Session):
    """
    衣柜查询子图

    wardrobe_query → wardrobe_analysis → response
    """
    subgraph = StateGraph(GraphState)

    subgraph.add_node("wardrobe_query", _wrap_async_with_db(wardrobe_node_module.wardrobe_query_node, db, "wardrobe_query"))
    subgraph.add_node("wardrobe_analysis", _wrap_async(analysis_node_module.wardrobe_analysis_node, "wardrobe_analysis"))
    subgraph.add_node("response", _wrap_async(response_node_module.response_node, "response"))

    subgraph.set_entry_point("wardrobe_query")

    subgraph.add_edge("wardrobe_query", "wardrobe_analysis")
    subgraph.add_edge("wardrobe_analysis", "response")
    subgraph.add_edge("response", END)

    return subgraph.compile()


# =============================================================================
# feedback_flow 子图（Phase 2 迭代版）
# =============================================================================

def _make_feedback_subgraph(db: Session):
    """
    反馈迭代子图 v2.0（Phase 2）

    advisor_analyze → advisor_refine → advisor_evaluate → response

    - advisor_analyze：解析反馈，分类类型
    - advisor_refine：基于原方案 + 调整指令生成新方案
    - advisor_evaluate：重新评价新方案
    - 迭代条件：iteration_count < 5 且非 accept
    """
    subgraph = StateGraph(GraphState)

    # Phase 2 节点（暂用 Phase 1 的 plan + evaluate 代替）
    subgraph.add_node("advisor_plan", _wrap_async_with_db(advisor_node_module.advisor_plan_node, db, "advisor_plan"))
    subgraph.add_node("advisor_evaluate", _wrap_async_with_db(advisor_node_module.advisor_evaluate_node, db, "advisor_evaluate"))
    subgraph.add_node("response", _wrap_async(response_node_module.response_node, "response"))

    subgraph.set_entry_point("advisor_plan")

    subgraph.add_edge("advisor_plan", "advisor_evaluate")
    subgraph.add_edge("advisor_evaluate", "response")
    subgraph.add_edge("response", END)

    return subgraph.compile()


# =============================================================================
# wardrobe_check_flow 子图（Phase 3）
# =============================================================================

def _make_wardrobe_check_subgraph(db: Session):
    """
    衣橱健康检查子图（Phase 3）

    curator_health_check → response
    """
    subgraph = StateGraph(GraphState)

    # Phase 3 节点（暂用空实现）
    subgraph.add_node("wardrobe_query", _wrap_async_with_db(wardrobe_node_module.wardrobe_query_node, db, "wardrobe_query"))
    subgraph.add_node("response", _wrap_async(response_node_module.response_node, "response"))

    subgraph.set_entry_point("wardrobe_query")

    subgraph.add_edge("wardrobe_query", "response")
    subgraph.add_edge("response", END)

    return subgraph.compile()


# =============================================================================
# style_match_flow 子图（Phase 3）
# =============================================================================

def _make_style_match_subgraph(db: Session):
    """
    参考图风格复刻子图（Phase 3）

    image_analyze → wardrobe_query → style_match → response
    """
    subgraph = StateGraph(GraphState)

    # Phase 3 节点（暂用空实现）
    subgraph.add_node("wardrobe_query", _wrap_async_with_db(wardrobe_node_module.wardrobe_query_node, db, "wardrobe_query"))
    subgraph.add_node("response", _wrap_async(response_node_module.response_node, "response"))

    subgraph.set_entry_point("wardrobe_query")

    subgraph.add_edge("wardrobe_query", "response")
    subgraph.add_edge("response", END)

    return subgraph.compile()


# =============================================================================
# care_guide_flow 子图
# =============================================================================

def _make_care_guide_subgraph(db: Session):
    """
    衣物护理指南子图

    直接响应（护理知识查询）
    """
    subgraph = StateGraph(GraphState)

    subgraph.add_node("response", _wrap_async(response_node_module.response_node, "response"))

    subgraph.set_entry_point("response")
    subgraph.add_edge("response", END)

    return subgraph.compile()


# =============================================================================
# 对话工作流管理器 v2.0
# =============================================================================

class DialogueWorkflow:
    """对话工作流管理器 v2.0"""

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
