"""意图识别节点"""
import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.graph.state import GraphState, Intent
from app.services.llm_providers import get_cached_provider

logger = logging.getLogger(__name__)


INTENT_SYSTEM_PROMPT = """你是一个穿搭助手，需要理解用户的穿衣需求。

【重要】请结合上下文理解用户意图：
- 如果用户正在回答追问（如"您要去哪个城市"），用户说"北京"或"去北京" → 请识别出城市
- 如果用户正在回答追问（如"您是去什么场合"），用户说"约会"或"开会" → 请识别出场景
- 如果用户直接说"推荐穿搭"，这是新的请求
- **即使意图判断为 unknown，也要尽可能提取城市和场景**
- **请特别注意近期对话摘要，它能帮助理解用户当前输入的上下文**

请分析用户输入，提取以下信息：
1. intent: 意图类型（只能选一个）
   - generate_outfit: 用户想要获得穿搭推荐
   - query_wardrobe: 用户想查询衣柜里的衣物或统计
   - get_advice: 用户想获取搭配建议
   - give_feedback: 用户对已有穿搭提反馈（如"太正式了"、"换个颜色"）
   - unknown: 无法判断

2. entities: 实体信息（尽可能提取，即使 intent 是 unknown）
   - date: 目标日期（如"后天"转为具体日期 2026-03-25，"下周一"转为具体日期）
   - city: 城市名称（支持各种变体）
   - scene: 场景（只能是以下值之一：daily, work, sport, date, party, casual, formal）
   - temperature: 温度（如果用户提到）
   - clothes_category: 衣物类别（top, pants, outer, inner, accessory）
   - clothes_color: 衣物颜色（如蓝色、白色、黑色）
   - style: 风格偏好（如休闲、正装、简约）
   - feedback_type: 反馈类型（如果 intent 是 give_feedback）

注意（城市提取示例）：
- "后天去北京参加晚宴" → date=后天+2天, city=北京, scene=party
- "去北京" → city=北京, intent=generate_outfit
- "奔北京" → city=北京（"奔"=去）
- "飞北京出差" → city=北京, scene=work
- "在北京上班" → city=北京, scene=work
- "春城" → city=昆明（昆明别称）
- "魔都" → city=上海（上海别称）
- "约会" → scene=date, intent=generate_outfit
- "和小伙伴浪一下" → scene=casual
- "蹦迪" → scene=party
- "出差" → scene=work
- "帮我看看蓝色的短袖怎么搭" → clothes_color=蓝色, clothes_category=top, intent=get_advice
- "我衣柜里有几件衬衫？" → category=衬衫→top, intent=query_wardrobe
- "太正式了，换个休闲点的" → intent=give_feedback, feedback_type=too_formal, target_scene=casual
- "看看我衣柜里有什么" → intent=query_wardrobe
- "明天去杭州出差穿什么" → date=明天, city=杭州, scene=work
- "我想要休闲一点的风格" → intent=generate_outfit, style=casual
- "约会穿什么好" → intent=generate_outfit, scene=date
- "你那叫什么" → intent=unknown（穿搭助手闲聊）
- "你好呀" → intent=unknown（礼貌回复即可）

输出JSON格式，只输出JSON，不要有其他文字。"""


def create_intent_prompt(message: str, context: Dict[str, Any] = None) -> str:
    """构建意图识别 prompt（增强版）"""
    context_info = ""
    if context:
        if context.get("target_city"):
            context_info += f"\n用户之前提到的城市：{context['target_city']}"
        if context.get("target_scene"):
            context_info += f"\n用户之前提到的场景：{context['target_scene']}"
        if context.get("target_date"):
            context_info += f"\n用户之前提到的日期：{context['target_date']}"
        if context.get("asking_for"):
            context_info += f"\n正在追问用户：{context['asking_for']}"
        if context.get("pending_intent"):
            context_info += f"\n用户的待完成意图：{context['pending_intent']}"
        if context.get("recent_conversation"):
            context_info += f"\n近期对话摘要：\n{context['recent_conversation']}"

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
    logger.info(f"[intent] 入参 | msg={user_message[:30]} ctx_target_city={context.get('target_city')} ctx_target_scene={context.get('target_scene')} recent_conv={len(context.get('recent_conversation', '') or '')}chars")

    # 构建 prompt
    prompt = create_intent_prompt(user_message, context)

    # 调用 LLM
    try:
        llm = get_cached_provider()
        chat_model = llm.chat_model

        logger.info(f"[LLM] intent识别开始 | message={user_message[:50]}")
        response = await chat_model.ainvoke([
            HumanMessage(content=prompt)
        ])
        logger.info(f"[LLM] intent识别完成 | response_len={len(response.content)} | response={response.content[:100]}")

        result = parse_intent_response(response.content)

        # ============================================================
        # 后处理：当 LLM 返回 unknown，但上下文有 city 且提取了 scene
        # 说明用户在完成一个进行中的穿搭推荐对话，强制修正 intent
        # ============================================================
        if (result["intent"] == Intent.UNKNOWN
                and context.get("target_city")
                and result["entities"].get("scene")):
            result["intent"] = Intent.GENERATE_OUTFIT
            logger.info(f"[intent] 强制修正 intent: unknown → generate_outfit "
                        f"(city={context['target_city']}, scene={result['entities']['scene']})")

    except Exception as e:
        # LLM 调用失败时的降级处理
        result = {
            "intent": Intent.UNKNOWN,
            "entities": {},
            "confidence": 0.0
        }
        state["error"] = f"意图识别失败: {str(e)}"
        logger.error(f"[LLM] intent识别失败 | error={e}")

    # ============================================================
    # 城市直接从 session context 读取，不依赖 LLM
    # 原因：LLM 输出格式不稳定（可能返回 null/空字符串/错误值），
    # 直接用已存储的城市更可靠
    # ============================================================
    # 从 context 读取已有城市（来自 session 持久化）
    session_city = state.get("context", {}).get("target_city") or state.get("target_city")
    if session_city:
        state["target_city"] = session_city
        logger.info(f"[intent] 城市来自session | target_city={session_city}")

    # 更新状态
    state["intent"] = result["intent"]
    state["intent_str"] = getattr(result["intent"], "value", None) if result["intent"] else None
    # 合并 entities：只用 LLM 返回的非 null 值
    llm_entities = result["entities"]
    merged_entities = dict(state.get("entities", {}))
    logger.info(f"[intent] merge前 | llm={llm_entities} ctx_city={session_city} ctx_scene={context.get('target_scene')}")
    for key in ["scene", "date", "temperature"]:
        if llm_entities.get(key) is not None:
            merged_entities[key] = llm_entities[key]
    # 场景和日期：LLM 没返回时用 context 兜底
    if not llm_entities.get("scene") and context.get("target_scene"):
        merged_entities["scene"] = context["target_scene"]
    if not llm_entities.get("date") and context.get("target_date"):
        merged_entities["date"] = context["target_date"]
    logger.info(f"[intent] merge后 | merged={merged_entities}")
    state["entities"] = merged_entities
    state["intent_confidence"] = result["confidence"]

    # 从合并后的 entities 提取关键信息到顶层
    if merged_entities.get("scene") is not None:
        state["target_scene"] = merged_entities["scene"]
    if merged_entities.get("date") is not None:
        state["target_date"] = merged_entities["date"]
    if merged_entities.get("temperature") is not None:
        state["target_temperature"] = merged_entities["temperature"]
    if merged_entities.get("feedback_type") is not None:
        state["feedback_type"] = merged_entities["feedback_type"]

    logger.info(f"[intent] 最终 | target_city={state.get('target_city')!r} target_scene={state.get('target_scene')!r} intent={state.get('intent')}")

    # 继承上下文中的追问状态（供下一轮使用）
    if context.get("asking_for"):
        state["asking_for"] = context["asking_for"]
    if context.get("pending_intent"):
        state["pending_intent"] = context["pending_intent"]

    return state
