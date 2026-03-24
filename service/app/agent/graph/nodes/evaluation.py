"""穿搭评估节点"""
from typing import Dict, Any, List, Optional
from app.agent.graph.state import GraphState
from app.models import UserClothes


def calculate_match_score(
    plan: Dict[str, Any],
    selected_clothes: Dict[str, Optional[Dict]]
) -> float:
    """
    计算穿搭方案匹配分数

    基于颜色匹配、品类完整性、温度适宜性计算综合分数

    Returns:
        0-100 的匹配分数
    """
    if not plan or not selected_clothes:
        return 0.0

    items = plan.get("items", {})
    if not isinstance(items, dict):
        return 0.0
    if not items:
        return 0.0

    total_weight = 0
    matched_weight = 0

    for item_name, item_info in items.items():
        category = item_info.get("category")
        expected_color = item_info.get("color")

        if not category:
            continue

        total_weight += 1

        clothes = selected_clothes.get(item_name)
        if not clothes:
            continue

        # 颜色匹配权重最高
        if expected_color:
            actual_color = clothes.get("color", "") or ""
            actual_desc = clothes.get("description", "") or ""

            if (expected_color.lower() in actual_color.lower() or
                expected_color.lower() in actual_desc.lower()):
                matched_weight += 1
        else:
            # 没有期望颜色，只要有这个品类就得分
            matched_weight += 1

    if total_weight == 0:
        return 0.0

    return round((matched_weight / total_weight) * 100, 1)


def evaluate_outfit(
    plan: Dict[str, Any],
    selected_clothes: Dict[str, Optional[Dict]],
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """
    评估穿搭方案

    Returns:
        评估结果包含：
        - match_score: 匹配分数
        - missing_items: 缺失的品类
        - temperature_warning: 温度警告
    """
    score = calculate_match_score(plan, selected_clothes)

    items = plan.get("items", {})
    if not isinstance(items, dict):
        items = {}
    missing_items = []
    temperature_warning = None

    # 检查缺失品类
    for item_name, item_info in items.items():
        category = item_info.get("category")
        if category and not selected_clothes.get(item_name):
            missing_items.append(item_name)

    # 温度检查
    if temperature is not None:
        if temperature < 10:
            # 冬季，需要 outer 和 inner
            if not selected_clothes.get("outer"):
                temperature_warning = "气温较低，建议添加外套"
            elif not selected_clothes.get("inner"):
                temperature_warning = "气温较低，建议添加保暖内搭"
        elif temperature < 20:
            # 春秋，早晚温差大
            if not selected_clothes.get("outer"):
                temperature_warning = "早晚温差大，建议携带外套"

    return {
        "match_score": score,
        "missing_items": missing_items,
        "temperature_warning": temperature_warning,
        "is_acceptable": score >= 60 or len(missing_items) == 0
    }


async def outfit_evaluation_node(state: GraphState) -> GraphState:
    """
    穿搭评估节点

    评估穿搭方案的匹配度，并决定是否需要重试
    """
    plan = state.get("outfit_plan")
    selected_clothes = state.get("selected_clothes", {})
    temperature = state.get("target_temperature")

    if not plan:
        state["error"] = "没有穿搭方案，无法评估"
        return state

    try:
        evaluation = evaluate_outfit(plan, selected_clothes, temperature)

        state["match_score"] = evaluation["match_score"]
        state["context"] = state.get("context", {})
        state["context"]["evaluation"] = evaluation

        # 判断是否需要重试
        should_retry = False
        if evaluation["match_score"] < 60:
            should_retry = True
            state["context"]["retry_reason"] = "匹配度过低"

        # 记录调整历史
        adjustment_history = state.get("adjustment_history", [])
        adjustment_history.append({
            "plan_id": plan.get("plan_id"),
            "score": evaluation["match_score"],
            "timestamp": "now"
        })
        state["adjustment_history"] = adjustment_history

        # 如果重试次数过多，停止
        if len(adjustment_history) >= 3:
            state["context"]["retry_exhausted"] = True

    except Exception as e:
        state["error"] = f"穿搭评估失败: {str(e)}"
        state["match_score"] = 0.0

    return state
