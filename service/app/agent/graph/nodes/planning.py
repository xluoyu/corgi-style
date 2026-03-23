"""穿搭规划节点"""
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.graph.state import GraphState
from app.services.llm_providers import create_llm_provider


PLANNING_SYSTEM_PROMPT = """你是一个专业穿搭顾问，基于用户衣柜中的衣物生成穿搭方案。

你需要根据以下信息设计一套完整的穿搭：
1. 用户的目标（日期、城市、场景）
2. 用户衣柜中已有的衣物

穿搭原则：
1. 优先使用用户已有的衣物
2. 考虑温度适宜性（冬季保暖、夏季清爽）
3. 色彩搭配和谐（主色+辅色+点缀色）
4. 场景符合要求（工作要正式、约会要得体等）

输出JSON格式：
{
  "plan_id": "plan_001",
  "description": "方案描述（1-2句话）",
  "items": {
    "top": {"color": "白色", "style": "简约", "reason": "为什么选这件"},
    "pants": {"color": "深蓝色", "style": "修身", "reason": "..."},
    "outer": {"color": "灰色", "style": "...", "reason": "..."},
    "inner": {...},
    "accessory": {...}
  },
  "color_harmony": "色彩搭配说明",
  "scene_appropriateness": "场景契合度评估",
  "temperature_suitability": "温度适宜性评估"
}

注意：items 中的每个 item 的 key 必须是英文类别名（top/pants/outer/inner/accessory）"""


def create_planning_prompt(
    target_date: str,
    target_city: str,
    target_scene: str,
    temperature: float,
    wardrobe_items: List[Dict],
    context: Dict[str, Any] = None
) -> str:
    """构建穿搭规划 prompt"""

    # 按品类整理衣物
    wardrobe_by_category = {}
    for item in wardrobe_items:
        cat = item.get("category", "unknown")
        if cat not in wardrobe_by_category:
            wardrobe_by_category[cat] = []
        wardrobe_by_category[cat].append(item)

    wardrobe_str = ""
    for cat, items in wardrobe_by_category.items():
        wardrobe_str += f"\n【{cat}】共 {len(items)} 件："
        for item in items[:5]:  # 每个品类最多显示5件
            desc = f"{item.get('color', '')} {item.get('description', '')}".strip()
            wardrobe_str += f"\n  - {desc} (穿着次数: {item.get('wear_count', 0)})"

    prompt = f"""用户信息：
- 目标日期: {target_date or '今天'}
- 目标城市: {target_city or '未知'}
- 气温: {temperature or '未知'}°C
- 场景: {target_scene or '日常'}

用户衣柜中的衣物：
{wardrobe_str}

请为用户设计一套完整的穿搭方案。"""

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

    使用 LLM 基于用户衣柜实际衣物生成穿搭方案
    """
    user_clothes = state.get("user_clothes", [])

    if not user_clothes:
        state["error"] = "用户衣柜为空，无法生成穿搭方案"
        return state

    # 获取参数
    target_date = state.get("target_date")
    target_city = state.get("target_city")
    target_scene = state.get("target_scene") or "daily"
    temperature = state.get("target_temperature")

    # 构建 prompt
    prompt = create_planning_prompt(
        target_date=target_date,
        target_city=target_city,
        target_scene=target_scene,
        temperature=temperature,
        wardrobe_items=user_clothes,
        context=state.get("context")
    )

    try:
        llm = create_llm_provider()
        chat_model = llm.chat_model

        response = await chat_model.ainvoke([
            HumanMessage(content=PLANNING_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])

        import json
        import re

        # 提取 JSON
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            plan = json.loads(json_match.group())
            state["outfit_plan"] = plan
        else:
            state["error"] = "LLM 返回格式错误，无法解析穿搭方案"

    except Exception as e:
        state["error"] = f"穿搭规划失败: {str(e)}"

    return state
