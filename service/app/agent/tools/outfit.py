"""穿搭工具（OutfitTools）。

使用 @tool 装饰器（langchain_core.tools），每个 Tool 内部通过
get_db_for_tools() / get_current_user_id() 获取 DB 和用户。
"""
import json
import re
from typing import List

from langchain_core.tools import tool

from app.agent.tools.context import get_db_for_tools, get_current_user_id
from app.services.llm_providers import get_cached_provider
from langchain_core.messages import HumanMessage, SystemMessage


# ============================================================
# 工具实现
# ============================================================

PLANNING_SYSTEM_PROMPT = """你是一个专业穿搭顾问，基于用户衣柜中的衣物生成穿搭方案。

【穿衣规则】
- 18-25℃：轻薄外套/长袖即可
- 10-17℃：需要中等厚度外套、毛衣
- <10℃：需要羽绒服/大衣
- >25℃：短袖/轻薄即可

【输出格式】
请用 JSON 格式返回穿搭方案：
{
  "description": "方案描述（口语化，不超过50字）",
  "outfits": [
    {
      "slot": "top",
      "clothes_id": "衣物ID",
      "reason": "搭配理由"
    }
  ]
}
"""


@tool
async def plan_outfit(scene: str, temperature: float, wardrobe_items: List[dict],
                      max_options: int = 3) -> str:
    """根据用户衣柜中的衣物、天气和场合生成穿搭方案。
    调用前请确保已通过 get_weather 获取温度，并通过 search_wardrobe 获取衣柜衣物，
    然后将结果作为 wardrobe_items 参数传入。此 Tool 不再查询天气或衣柜。"""
    try:
        from app.agent.graph.nodes.planning import create_planning_prompt

        # 按品类分组
        wardrobe_by_category = {}
        for item in wardrobe_items:
            cat = item.get("category", "unknown")
            wardrobe_by_category.setdefault(cat, []).append(item)

        prompt = create_planning_prompt(
            target_date=None,
            target_city=None,
            target_scene=scene,
            temperature=temperature,
            wardrobe_by_category=wardrobe_by_category,
            available_categories=list(wardrobe_by_category.keys()),
            missing_categories=[],
        )

        llm = get_cached_provider().chat_model
        response = await llm.ainvoke([
            SystemMessage(content=PLANNING_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])

        # 解析 JSON（支持嵌入在文本中的 JSON）
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            return json_match.group()
        return json.dumps({"description": response.content})
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)}, ensure_ascii=False)


@tool
async def get_outfit_history(date: str = None, limit: int = 10) -> str:
    """查询用户的穿搭历史记录。"""
    try:
        from app.models import OutfitRecord

        db = get_db_for_tools()
        user_id = get_current_user_id()

        query = db.query(OutfitRecord).filter(OutfitRecord.user_id == user_id)
        if date:
            query = query.filter(OutfitRecord.create_time >= f"{date} 00:00:00")
        records = query.order_by(OutfitRecord.create_time.desc()).limit(limit).all()

        result = []
        for r in records:
            result.append({
                "id": str(r.id),
                "date": r.create_time.isoformat() if r.create_time else None,
                "occasion": r.occasion,
                "outfit_name": r.outfit_name,
                "outfit_snapshot": r.outfit_snapshot,
                "weather_snapshot": r.weather_snapshot,
            })
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": type(e).__name__, "message": str(e)}, ensure_ascii=False)


# ============================================================
# 工具列表（供 SupervisorAgent 注册）
# ============================================================

OUTFIT_TOOLS = [
    plan_outfit,
    get_outfit_history,
]
