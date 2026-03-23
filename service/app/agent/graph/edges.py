"""条件分支函数"""
from typing import Literal
from app.agent.graph.state import GraphState, Intent


def route_by_intent(state: GraphState) -> Literal["wardrobe_query", "generate_outfit", "feedback", "response"]:
    """
    根据意图类型路由

    Returns:
        下一个节点的名称
    """
    intent = state.get("intent", Intent.UNKNOWN)

    if intent == Intent.QUERY_WARDROBE:
        return "wardrobe_query"
    elif intent == Intent.GENERATE_OUTFIT:
        return "generate_outfit"
    elif intent == Intent.GIVE_FEEDBACK:
        return "feedback"
    else:
        return "response"


def route_by_score(state: GraphState) -> Literal["high_score", "low_score"]:
    """
    根据匹配分数路由

    Returns:
        "high_score" 如果分数 >= 80
        "low_score" 如果分数 < 80
    """
    score = state.get("match_score", 0)

    if score >= 80:
        return "high_score"
    else:
        return "low_score"


def should_retry(state: GraphState) -> bool:
    """
    判断是否应该重试生成方案

    Returns:
        True 如果调整次数 < 3 且 匹配分数 < 60
    """
    adjustment_history = state.get("adjustment_history", [])

    if len(adjustment_history) >= 3:
        return False

    score = state.get("match_score", 0)
    if score < 60:
        return True

    return False


def should_get_weather(state: GraphState) -> bool:
    """
    判断是否需要获取天气

    Returns:
        True 如果有目标城市
    """
    return bool(state.get("target_city"))


def should_get_wardrobe(state: GraphState) -> bool:
    """
    判断是否需要查询衣柜

    Returns:
        True 如果意图是生成穿搭
    """
    intent = state.get("intent", Intent.UNKNOWN)
    return intent in [Intent.GENERATE_OUTFIT, Intent.GET_ADVICE, Intent.UNKNOWN]
