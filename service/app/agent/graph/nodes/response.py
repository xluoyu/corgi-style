"""响应生成节点"""
from typing import Dict, Any, List
from app.agent.graph.state import GraphState, Intent


async def response_node(state: GraphState) -> GraphState:
    """
    响应生成节点

    根据状态生成最终回复消息
    """
    intent = state.get("intent", Intent.UNKNOWN)
    user_message = state.get("messages", [{}])[-1].get("content", "") if state.get("messages") else ""

    response_content = ""
    data = {}

    if intent == Intent.QUERY_WARDROBE:
        response_content, data = _handle_wardrobe_query(state)
    elif intent == Intent.GENERATE_OUTFIT:
        response_content, data = _handle_generate_outfit(state)
    elif intent == Intent.GIVE_FEEDBACK:
        response_content, data = _handle_feedback(state)
    elif intent == Intent.GET_ADVICE:
        response_content, data = _handle_get_advice(state)
    else:
        response_content, data = _handle_unknown(state)

    # 更新消息历史
    messages = state.get("messages", [])
    messages.append({
        "role": "assistant",
        "content": response_content
    })
    state["messages"] = messages

    # 设置返回数据
    state["response_data"] = data
    state["should_end"] = True

    return state


def _handle_wardrobe_query(state: GraphState) -> tuple[str, Dict[str, Any]]:
    """处理衣柜查询响应"""
    stats = state.get("context", {}).get("wardrobe_stats")
    user_clothes = state.get("user_clothes", [])

    if stats:
        total = stats.get("total", 0)
        by_category = stats.get("by_category", {})

        category_text = ""
        for cat, count in by_category.items():
            cat_name = {
                "top": "上衣",
                "pants": "裤子",
                "outer": "外套",
                "inner": "内搭",
                "accessory": "配饰"
            }.get(cat, cat)
            category_text += f"{cat_name} {count} 件、"

        response = f"您的衣柜里共有 {total} 件衣物，其中{category_text.rstrip('、')}。"
    elif user_clothes:
        total = len(user_clothes)
        response = f"为您找到 {total} 件符合条件的衣物。"
    else:
        response = "您的衣柜里还没有衣物，添加一些来开始穿搭搭配吧！"

    return response, {"type": "wardrobe_query", "stats": stats, "clothes": user_clothes}


def _handle_generate_outfit(state: GraphState) -> tuple[str, Dict[str, Any]]:
    """处理生成穿搭响应"""
    outfit_plan = state.get("outfit_plan", {})
    selected_clothes = state.get("selected_clothes", {})
    match_score = state.get("match_score", 0)
    evaluation = state.get("context", {}).get("evaluation", {})

    if not outfit_plan:
        response = "抱歉，无法为您生成穿搭方案。请先添加一些衣物到您的衣柜中。"
        return response, {"type": "outfit_result", "success": False}

    # 构建回复
    response = f"为您推荐以下穿搭方案：\n\n"
    response += f"{outfit_plan.get('description', '')}\n\n"

    # 列出衣物
    for slot, clothes in selected_clothes.items():
        if clothes:
            slot_name = {
                "top": "上衣",
                "pants": "裤子",
                "outer": "外套",
                "inner": "内搭",
                "accessory": "配饰"
            }.get(slot, slot)
            color = clothes.get("color", "")
            response += f"• {slot_name}：{color}\n"

    response += f"\n匹配度：{match_score}%"

    if evaluation.get("temperature_warning"):
        response += f"\n\n温馨提示：{evaluation['temperature_warning']}"

    data = {
        "type": "outfit_result",
        "success": True,
        "plan": outfit_plan,
        "clothes": selected_clothes,
        "match_score": match_score
    }

    return response, data


def _handle_feedback(state: GraphState) -> tuple[str, Dict[str, Any]]:
    """处理反馈响应"""
    feedback_type = state.get("feedback_type", "")
    match_score = state.get("match_score", 0)

    feedback_text = {
        "too_formal": "太正式",
        "too_casual": "太休闲",
        "too_colorful": "颜色太花哨",
        "too_simple": "太素",
        "too_cold": "太冷",
        "too_hot": "太热"
    }.get(feedback_type, "需要调整")

    if match_score >= 80:
        response = f"好的，已经为您调整了穿搭方案，{feedback_text}的问题应该已经解决。"
    else:
        response = f"好的，根据您的反馈'{feedback_text}'，为您重新调整了穿搭方案。"

    return response, {"type": "feedback_response", "feedback_type": feedback_type}


def _handle_get_advice(state: GraphState) -> tuple[str, Dict[str, Any]]:
    """处理获取建议响应"""
    user_clothes = state.get("user_clothes", [])
    outfit_plan = state.get("outfit_plan", {})

    if not user_clothes:
        return "您的衣柜里没有找到符合条件的衣物。", {"type": "advice", "success": False}

    if outfit_plan:
        response = f"根据您的情况，为您提供以下穿搭建议：\n\n"
        response += f"{outfit_plan.get('description', '')}\n\n"

        items = outfit_plan.get("items", {})
        for slot, item_info in items.items():
            slot_name = {
                "top": "上衣",
                "pants": "裤子",
                "outer": "外套",
                "inner": "内搭",
                "accessory": "配饰"
            }.get(slot, slot)
            color = item_info.get("color", "")
            reason = item_info.get("reason", "")
            response += f"• {slot_name}：{color} - {reason}\n"
    else:
        response = "为您整理了以下搭配建议..."

    return response, {"type": "advice", "success": True, "plan": outfit_plan}


def _handle_unknown(state: GraphState) -> tuple[str, Dict[str, Any]]:
    """处理未知意图响应"""
    user_message = state.get("messages", [{}])[-1].get("content", "") if state.get("messages") else ""

    suggestions = [
        "您可以尝试说：'帮我推荐一套穿搭'",
        "或者：'我明天要去北京，想看看穿什么合适'",
        "也可以说：'我衣柜里有几件蓝色的衣服？'"
    ]

    response = f"抱歉，我不太理解您的意思。\n\n" + "\n".join(suggestions)

    return response, {"type": "unknown"}
