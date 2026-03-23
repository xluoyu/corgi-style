"""反馈处理节点"""
from typing import Dict, Any
from app.agent.graph.state import GraphState


# 反馈类型到场景调整的映射
FEEDBACK_SCENE_MAP = {
    "too_formal": "casual",
    "too_casual": "formal",
    "too_colorful": "neutral",
    "too_simple": "statement",
    "too_cold": "warm",
    "too_hot": "cool",
}


async def feedback_node(state: GraphState) -> GraphState:
    """
    反馈处理节点

    处理用户反馈，调整穿搭方案参数
    """
    feedback_type = state.get("feedback_type")
    adjustment_history = state.get("adjustment_history", [])

    if not feedback_type:
        return state

    # 记录反馈到历史
    adjustment_history.append({
        "type": "feedback",
        "feedback_type": feedback_type,
        "timestamp": "now"
    })
    state["adjustment_history"] = adjustment_history

    # 根据反馈类型调整参数
    context = state.get("context", {})

    # 场景调整
    if feedback_type in FEEDBACK_SCENE_MAP:
        new_scene = FEEDBACK_SCENE_MAP[feedback_type]
        state["target_scene"] = new_scene
        context["adjusted_scene"] = new_scene

    # 温度调整
    if feedback_type == "too_cold" and state.get("target_temperature"):
        # 增加温度需求
        state["target_temperature"] = min(state["target_temperature"] + 5, 30)
        context["temperature_adjusted"] = True
    elif feedback_type == "too_hot" and state.get("target_temperature"):
        # 降低温度需求
        state["target_temperature"] = max(state["target_temperature"] - 5, 0)
        context["temperature_adjusted"] = True

    # 将调整历史存入 context
    context["last_feedback"] = {
        "type": feedback_type,
        "scene": state.get("target_scene"),
        "temperature": state.get("target_temperature")
    }
    state["context"] = context

    return state
