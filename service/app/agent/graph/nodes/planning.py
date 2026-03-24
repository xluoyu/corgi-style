"""穿搭规划节点"""
import logging
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.graph.state import GraphState
from app.services.llm_providers import get_cached_provider

logger = logging.getLogger(__name__)


PLANNING_SYSTEM_PROMPT = """你是一个专业穿搭顾问，基于用户衣柜中的衣物生成穿搭方案。

你有两部分信息：
1. 用户的实际衣物库存（衣柜中已有）
2. 缺失的品类（衣柜中没有）

穿搭原则：
1. 优先从用户已有的衣物中挑选
2. 缺失的品类不要硬凑，直接给出文字购买/搭配建议
3. 考虑温度适宜性
4. 色彩搭配和谐
5. 场景符合要求

输出JSON格式：
{
  "plan_id": "plan_001",
  "description": "方案描述（1-2句话）",
  "items": {
    "top": {"color": "白色", "style": "简约", "reason": "为什么选这件", "matched": true, "clothes_id": "xxx"},
    "pants": {"color": "建议选黑色或深灰色休闲裤", "style": "建议风格", "reason": "衣柜中没有匹配的裤子", "matched": false},
    "outer": {...}
  },
  "missing_advice": "裤子建议选黑色或深灰色休闲款，外套建议搭配浅灰色大衣"
}

说明：
- matched=true 表示从衣柜中选中了衣物，clothes_id 填写衣物ID
- matched=false 表示衣柜中缺失该品类，color/style 用文字描述建议
- missing_advice 字段汇总所有缺失品类的搭配建议"""


# 品类中文名
_CATEGORY_NAMES = {
    "top": "上衣",
    "pants": "裤子",
    "outer": "外套",
    "inner": "内搭",
    "accessory": "配饰"
}


def create_planning_prompt(
    target_date: str,
    target_city: str,
    target_scene: str,
    temperature: float,
    wardrobe_by_category: dict,
    available_categories: List[str],
    missing_categories: List[str],
    context: Dict[str, Any] = None
) -> str:
    """构建穿搭规划 prompt"""

    wardrobe_str = ""
    for cat, items in wardrobe_by_category.items():
        cat_name = _CATEGORY_NAMES.get(cat, cat)
        wardrobe_str += f"\n【{cat_name}】共 {len(items)} 件："
        for item in items[:5]:
            desc = f"{item.get('color', '')} {item.get('description', '')}".strip()
            wardrobe_str += f"\n  - {desc} (穿着次数: {item.get('wear_count', 0)}, id: {item.get('id', '')})"

    if not wardrobe_str:
        wardrobe_str = "\n（衣柜为空）"

    missing_str = "、".join([_CATEGORY_NAMES.get(c, c) for c in missing_categories]) if missing_categories else "无"
    available_str = "、".join([_CATEGORY_NAMES.get(c, c) for c in available_categories]) if available_categories else "无"

    # 用户画像（可选）
    profile_info = ""
    if context:
        gender = context.get("user_gender")
        style = context.get("user_style")
        season = context.get("user_season")
        occasion = context.get("user_default_occasion")
        if gender:
            profile_info += f"\n用户性别：{gender}"
        if style:
            profile_info += f"\n风格偏好：{style}"
        if season:
            profile_info += f"\n季节偏好：{season}"
        if occasion:
            scene_map = {"casual": "日常", "work": "职场", "formal": "正式", "sport": "运动", "date": "约会", "party": "派对"}
            profile_info += f"\n默认场合：{scene_map.get(occasion, occasion)}"

    prompt = f"""用户画像：
{profile_info if profile_info else "（暂无）"}

用户需求：
- 目标日期: {target_date or '今天'}
- 目标城市: {target_city or '未知'}
- 气温: {temperature or '未知'}°C
- 场景: {target_scene or '日常'}

衣柜中已有的品类（可以直接选用）：{available_str}
{wardrobe_str}

缺失的品类（无法从衣柜中选，需要文字建议）：{missing_str}

请设计一套适合的穿搭方案。要求：
1. 符合用户的性别和风格偏好
2. 考虑气温选择合适的厚度
3. 缺失品类的颜色建议要具体（如"黑色直筒裤"、"米白色针织衫"）
4. 回复要口语化、亲切"""

    if context and context.get("feedback_type"):
        feedback_map = {
            "too_formal": "用户反馈：太正式了，想要更休闲一点的风格",
            "too_casual": "用户反馈：太休闲了，想要更正式一点的风格",
            "too_colorful": "用户反馈：颜色太花哨了，想要更简约的",
            "too_simple": "用户反馈：太素了，想要更有特色的",
            "too_cold": "用户反馈：太冷了，想要更保暖的",
            "too_hot": "用户反馈：太热了，想要更清爽的",
        }
        feedback = feedback_map.get(context["feedback_type"], context["feedback_type"])
        prompt += f"\n\n用户反馈：{feedback}"

    return prompt


async def outfit_planning_node(state: GraphState) -> GraphState:
    """
    穿搭规划节点

    使用 LLM 基于用户衣柜实际衣物生成穿搭方案。
    告知 LLM 哪些品类已有、哪些缺失，让 LLM 直接给出文字建议而非硬凑。
    """
    user_clothes = state.get("user_clothes", [])

    if not user_clothes:
        state["error"] = "用户衣柜为空，无法生成穿搭方案"
        return state

    # 获取参数（来自 wardrobe_analysis_node）
    target_date = state.get("target_date")
    target_city = state.get("target_city")
    target_scene = state.get("target_scene") or "daily"
    temperature = state.get("target_temperature")
    wardrobe_by_category = state.get("wardrobe_by_category", {})
    available_categories = state.get("available_categories", [])
    missing_categories = state.get("missing_categories", [])

    # 构建 prompt（传入已有的分组信息，不再重新计算）
    prompt = create_planning_prompt(
        target_date=target_date,
        target_city=target_city,
        target_scene=target_scene,
        temperature=temperature,
        wardrobe_by_category=wardrobe_by_category,
        available_categories=available_categories,
        missing_categories=missing_categories,
        context=state.get("context")
    )

    try:
        llm = get_cached_provider()
        chat_model = llm.chat_model

        logger.info(f"[LLM] outfit_planning开始 | city={target_city} | scene={target_scene} | clothes_count={len(user_clothes)}")
        response = await chat_model.ainvoke([
            HumanMessage(content=PLANNING_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        logger.info(f"[LLM] outfit_planning完成 | response_len={len(response.content)}")

        import json
        import re

        # 提取 JSON
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            try:
                plan = json.loads(json_match.group())
            except json.JSONDecodeError:
                plan = None
                logger.warning(f"[LLM] outfit_planning JSON解析失败 | content={response.content[:200]}")

            # 安全检查：确保 items 是 dict，避免 LLM 返回错误格式导致后续崩溃
            if plan and not isinstance(plan.get("items"), dict):
                plan = None

            if plan:
                state["outfit_plan"] = plan
            else:
                state["error"] = "LLM 返回格式错误，无法解析穿搭方案"
        else:
            state["error"] = "LLM 返回格式错误，无法解析穿搭方案"

    except Exception as e:
        state["error"] = f"穿搭规划失败: {str(e)}"
        logger.error(f"[LLM] outfit_planning异常 | error={e}")

    return state
