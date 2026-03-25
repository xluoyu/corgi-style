"""条件分支函数"""
import logging
from typing import Literal, Optional
from app.agent.graph.state import GraphState, Intent

logger = logging.getLogger(__name__)


def _get_intent_str(state: GraphState) -> Optional[str]:
    """安全获取 intent 字符串值（兼容 Intent 枚举和 astream 部分更新）"""
    raw = state.get("intent_str") or state.get("intent")
    if raw is None:
        return None
    if hasattr(raw, "value"):
        return raw.value
    if isinstance(raw, str):
        return raw
    return str(raw)


def route_by_intent(state: GraphState) -> Literal["wardrobe_query", "generate_outfit", "feedback", "response"]:
    """根据意图类型路由"""
    intent_str = _get_intent_str(state)
    city = state.get("target_city")
    scene = state.get("target_scene")
    logger.info(f"[route] intent={intent_str} city={city!r} scene={scene!r}")

    if intent_str == "query_wardrobe":
        return "wardrobe_query"
    elif intent_str == "generate_outfit":
        # city + scene 都完整时才进子图，否则先追问补全信息
        if city and scene:
            logger.info(f"[route] → generate_outfit (city+scene完整)")
            return "generate_outfit"
        missing = []
        if not city:
            missing.append("city")
        if not scene:
            missing.append("scene")
        logger.info(f"[route] → response (缺失: {missing})")
        return "response"
    elif intent_str == "give_feedback":
        return "feedback"
    else:
        logger.info(f"[route] → response (intent={intent_str}未知)")
        return "response"


def route_by_score(state: GraphState) -> Literal["high_score", "low_score"]:
    """
    根据匹配分数路由，附带重试上限保护。

    Returns:
        "high_score" 如果分数 >= 60
        "low_score" 如果分数 < 60 且重试次数 < 3
        "high_score" 如果重试次数已达 3 次（强制退出，防止无限循环）
    """
    score = state.get("match_score", 0)
    history = state.get("adjustment_history", [])

    # 重试次数已达上限，强制退出循环
    if len(history) >= 3:
        return "high_score"

    if score >= 60:
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
