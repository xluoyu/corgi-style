"""意图识别节点"""
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.graph.state import GraphState, Intent
from app.services.llm_providers import create_llm_provider


INTENT_SYSTEM_PROMPT = """你是一个穿搭助手，需要理解用户的穿衣需求。

请分析用户输入，提取以下信息：
1. intent: 意图类型（只能选一个）
   - generate_outfit: 用户想要获得穿搭推荐
   - query_wardrobe: 用户想查询衣柜里的衣物或统计
   - get_advice: 用户想获取搭配建议
   - give_feedback: 用户对已有穿搭提反馈（如"太正式了"、"换个颜色"）
   - unknown: 无法判断

2. entities: 实体信息（尽可能提取）
   - date: 目标日期（如"后天"转为具体日期 2026-03-25，"下周一"转为具体日期）
   - city: 城市名称
   - scene: 场景（只能是以下值之一：daily, work, sport, date, party, casual, formal）
   - temperature: 温度（如果用户提到）
   - clothes_category: 衣物类别（top, pants, outer, inner, accessory）
   - clothes_color: 衣物颜色（如蓝色、白色、黑色）
   - style: 风格偏好（如休闲、正装、简约）
   - feedback_type: 反馈类型（如果 intent 是 give_feedback）

注意：
- "后天去北京参加晚宴" → date=后天+2天, city=北京, scene=party
- "帮我看看蓝色的短袖怎么搭" → clothes_color=蓝色, clothes_category=top, intent=get_advice
- "我衣柜里有几件衬衫？" → query_type=count, category=衬衫→top, intent=query_wardrobe
- "太正式了，换个休闲点的" → intent=give_feedback, feedback_type=too_formal, target_scene=casual

输出JSON格式，只输出JSON，不要有其他文字。"""


def create_intent_prompt(message: str, context: Dict[str, Any] = None) -> str:
    """构建意图识别 prompt"""
    context_info = ""
    if context:
        if context.get("target_city"):
            context_info += f"\n用户之前提到的城市：{context['target_city']}"
        if context.get("target_scene"):
            context_info += f"\n用户之前提到的场景：{context['target_scene']}"

    return f"{INTENT_SYSTEM_PROMPT}\n\n用户输入：{message}{context_info}"


def parse_intent_response(response: str) -> Dict[str, Any]:
    """解析 LLM 返回的意图识别结果"""
    import json
    import re

    # 提取 JSON
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if not json_match:
        return {"intent": Intent.UNKNOWN, "entities": {}, "confidence": 0.0}

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError:
        return {"intent": Intent.UNKNOWN, "entities": {}, "confidence": 0.0}

    # 解析 intent
    intent_str = data.get("intent", "unknown").lower()
    try:
        intent = Intent(intent_str)
    except ValueError:
        intent = Intent.UNKNOWN

    # 解析 entities
    entities = data.get("entities", {})

    # 处理相对日期
    if "date" in entities and entities["date"]:
        entities["date"] = _resolve_relative_date(entities["date"])

    # 映射中文场景到英文
    scene_mapping = {
        "日常": "daily", "日常休闲": "daily", "休闲": "casual",
        "工作": "work", "上班": "work", "职场": "work", "商务": "work",
        "运动": "sport", "健身": "sport",
        "约会": "date", "出行": "date",
        "派对": "party", "聚会": "party", "晚宴": "party",
        "正式": "formal"
    }
    if "scene" in entities and entities["scene"]:
        scene = entities["scene"]
        entities["scene"] = scene_mapping.get(scene, scene)

    return {
        "intent": intent,
        "entities": entities,
        "confidence": data.get("confidence", 0.8)
    }


def _resolve_relative_date(date_str: str) -> str:
    """解析相对日期为具体日期"""
    from datetime import datetime, timedelta

    today = datetime.now()
    date_str = date_str.strip()

    relative_map = {
        "今天": 0,
        "明天": 1,
        "后天": 2,
        "大后天": 3,
        "昨天": -1,
        "前天": -2,
    }

    if date_str in relative_map:
        target = today + timedelta(days=relative_map[date_str])
        return target.strftime("%Y-%m-%d")

    # 尝试解析 "下周一" 等
    if "下周一" in date_str:
        days_ahead = 7 - today.weekday() + 0  # 0 = Monday
        target = today + timedelta(days=days_ahead)
        return target.strftime("%Y-%m-%d")

    # 尝试直接解析日期格式
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        pass

    try:
        datetime.strptime(date_str, "%m-%d")
        return f"{today.year}-{date_str}"
    except ValueError:
        pass

    return today.strftime("%Y-%m-%d")


async def intent_node(state: GraphState) -> GraphState:
    """
    意图识别节点

    使用 LLM 分析用户消息，提取意图和实体
    """
    user_message = state.get("messages", [])[-1]["content"] if state.get("messages") else ""

    # 获取上下文
    context = state.get("context", {})

    # 构建 prompt
    prompt = create_intent_prompt(user_message, context)

    # 调用 LLM
    try:
        llm = create_llm_provider()
        chat_model = llm.chat_model

        response = await chat_model.ainvoke([
            HumanMessage(content=prompt)
        ])

        result = parse_intent_response(response.content)
    except Exception as e:
        # LLM 调用失败时的降级处理
        result = {
            "intent": Intent.UNKNOWN,
            "entities": {},
            "confidence": 0.0
        }
        state["error"] = f"意图识别失败: {str(e)}"

    # 更新状态
    state["intent"] = result["intent"]
    state["entities"] = result["entities"]
    state["intent_confidence"] = result["confidence"]

    # 从 entities 中提取关键信息到顶层
    entities = result["entities"]
    if "date" in entities:
        state["target_date"] = entities["date"]
    if "city" in entities:
        state["target_city"] = entities["city"]
    if "scene" in entities:
        state["target_scene"] = entities["scene"]
    if "temperature" in entities:
        state["target_temperature"] = entities["temperature"]
    if "feedback_type" in entities:
        state["feedback_type"] = entities["feedback_type"]

    return state
