"""条件边路由 v2.0

基于 LangGraph 的条件边定义，支持 OutfitAdvisor + WardrobeCurator Agent。
"""
import logging
from typing import Literal
from app.agent.graph.state_v2 import GraphState, Intent

logger = logging.getLogger(__name__)


# =============================================================================
# 主路由：intent 识别后路由到对应子图
# =============================================================================

def route_by_intent(state: GraphState) -> Literal[
    "generate_outfit_flow",
    "query_wardrobe_flow",
    "feedback_flow",
    "wardrobe_check_flow",
    "style_match_flow",
    "care_guide_flow",
    "get_advice_flow",
    "response",
]:
    """
    根据 intent 路由到对应子图或节点

    Phase 1:
    - generate_outfit → generate_outfit_flow（简化版，无迭代）
    - query_wardrobe → query_wardrobe_flow
    - give_feedback → feedback_flow（Phase 2）
    - wardrobe_check → wardrobe_check_flow
    - style_match → style_match_flow
    - care_guide → care_guide_flow
    - get_advice → response（直接响应）
    - unknown → response
    """
    intent = state.get("intent") or Intent.UNKNOWN
    # 兼容字符串
    if hasattr(intent, "value"):
        intent_str = intent.value
    else:
        intent_str = str(intent) if intent else "unknown"

    logger.info(f"[edge] route_by_intent | intent={intent_str}")

    route_map = {
        Intent.GENERATE_OUTFIT: "generate_outfit_flow",
        Intent.QUERY_WARDROBE: "query_wardrobe_flow",
        Intent.GIVE_FEEDBACK: "feedback_flow",
        Intent.WARDROBE_CHECK: "wardrobe_check_flow",
        Intent.STYLE_MATCH: "style_match_flow",
        Intent.CARE_GUIDE: "care_guide_flow",
        Intent.GET_ADVICE: "response",
        Intent.UNKNOWN: "response",
    }

    route = route_map.get(intent, "response")
    logger.info(f"[edge] route_by_intent → {route}")
    return route


# =============================================================================
# generate_outfit_flow 内部路由
# =============================================================================

def route_generate_outfit(state: GraphState) -> Literal["advisor_plan", "response"]:
    """
    generate_outfit_flow 内部路由

    检查必要信息：
    - 有 city + scene → 进入 advisor_plan
    - 缺少信息 → 追问（response 节点处理）
    """
    has_city = bool(state.get("target_city"))
    has_scene = bool(state.get("target_scene"))

    if has_city and has_scene:
        return "advisor_plan"

    # 缺少信息，由 response 节点追问
    return "response"


# =============================================================================
# feedback_flow 内部路由（Phase 2）
# =============================================================================

def route_feedback_iteration(state: GraphState) -> Literal["advisor_refine", "response"]:
    """
    feedback_flow 内部路由

    - feedback_type == "accept" → 结束，response
    - iteration_count >= 5 → 结束，response
    - 否则 → advisor_refine 继续迭代
    """
    feedback_type = state.get("feedback_type", "")
    iteration_count = state.get("advisor_iteration_count", 0)

    if feedback_type == "accept" or iteration_count >= 5:
        return "response"

    return "advisor_refine"


# =============================================================================
# query_wardrobe_flow 内部路由
# =============================================================================

def route_wardrobe_query(state: GraphState) -> Literal["wardrobe_query", "response"]:
    """
    query_wardrobe_flow 内部路由

    - 有 user_clothes 或 wardrobe_stats → wardrobe_query 分析
    - 无数据 → response（返回空衣柜提示）
    """
    has_data = bool(state.get("user_clothes") or state.get("wardrobe_stats"))
    return "wardrobe_query" if has_data else "response"


# =============================================================================
# 通用结束条件
# =============================================================================

def should_continue(state: GraphState) -> Literal["continue", "end"]:
    """
    通用继续/结束判断

    用于某些节点后判断是否继续流程
    """
    if state.get("should_end"):
        return "end"
    return "continue"


def is_terminal_node(state: GraphState) -> bool:
    """判断是否应该结束对话"""
    return bool(state.get("should_end", False))
