"""衣物检索节点"""
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.agent.graph.state import GraphState
from app.models import UserClothes, TemperatureRange
from app.services.oss_uploader import oss_uploader


def retrieve_by_scheme(
    db: Session,
    user_id: str,
    plan: Dict[str, Any],
    temperature: Optional[float] = None,
    available_categories: List[str] = None
) -> Dict[str, Optional[Dict]]:
    """
    按穿搭方案检索衣物（批量优化版）

    只检索衣柜中已有的品类（available_categories），
    缺失品类返回 None，由 LLM 的 missing_advice 字段提供文字建议。
    """
    result = {}
    items = plan.get("items", {})

    if not isinstance(items, dict):
        return result

    if available_categories is None:
        available_categories = list(available_categories or [])

    # 收集所有需要的品类（只限于衣柜中已有的）
    categories_needed = set()
    color_hints = {}
    for item_name, item_info in items.items():
        category = item_info.get("category")
        if category and category in available_categories:
            categories_needed.add(category)
            if item_info.get("color"):
                color_hints[category] = item_info.get("color")

    if not categories_needed:
        # 所有品类都是缺失的，不需要查询数据库
        for item_name, item_info in items.items():
            result[item_name] = None
        return result

    # 温度范围
    temp_ranges = _get_temp_ranges(temperature) if temperature else None

    # 一次查询获取所有品类的衣物
    query = db.query(UserClothes).filter(
        UserClothes.user_id == user_id,
        UserClothes.category.in_(categories_needed),
        UserClothes.is_deleted == False
    )
    if temp_ranges:
        query = query.filter(UserClothes.temperature_range.in_(temp_ranges))

    all_clothes = query.all()

    # 按品类分组
    from collections import defaultdict
    clothes_by_category = defaultdict(list)
    for c in all_clothes:
        clothes_by_category[c.category].append(c)

    # 对每个 slot 匹配最佳衣物
    for item_name, item_info in items.items():
        category = item_info.get("category")
        expected_color = item_info.get("color")

        if not category or category not in clothes_by_category:
            result[item_name] = None
            continue

        clothes_list = clothes_by_category[category]

        # 颜色匹配
        matched = None
        if expected_color and clothes_list:
            for clothes in clothes_list:
                if _color_match(expected_color, clothes.color or "", clothes.description or ""):
                    matched = _clothes_to_dict(clothes)
                    break

        # 没找到精确匹配，取穿着次数最少的那件（鼓励轮换穿着）
        if not matched and clothes_list:
            clothes_list.sort(key=lambda c: c.wear_count or 0)
            matched = _clothes_to_dict(clothes_list[0])

        result[item_name] = matched

    return result


def _get_temp_ranges(temperature: float) -> List[str]:
    """根据温度获取适合的温度范围"""
    if temperature >= 25:
        return [TemperatureRange.summer.value, TemperatureRange.all_season.value]
    elif temperature >= 10:
        return [TemperatureRange.spring_autumn.value, TemperatureRange.all_season.value]
    else:
        return [TemperatureRange.winter.value, TemperatureRange.all_season.value]


def _color_match(expected: str, color: str, description: str) -> bool:
    """检查颜色是否匹配（模糊匹配）"""
    expected = expected.lower()
    color = color.lower()
    description = description.lower()

    return (expected in color) or (expected in description) or (color in expected)


def _clothes_to_dict(clothes: UserClothes) -> Dict[str, Any]:
    """将衣物对象转为字典"""
    return {
        "id": str(clothes.id),
        "category": clothes.category,
        "color": clothes.color,
        "material": clothes.material,
        "temperature_range": clothes.temperature_range,
        "tags": clothes.tags if isinstance(clothes.tags, list) else [],
        "wear_count": clothes.wear_count,
        "last_worn_at": clothes.last_worn_at.isoformat() if clothes.last_worn_at else None,
        "image_url": oss_uploader.get_signed_url(clothes.original_image_url) if clothes.original_image_url else (oss_uploader.get_signed_url(clothes.cartoon_image_url) if clothes.cartoon_image_url else ""),
        "description": getattr(clothes, 'description', None) or clothes.color or "",
    }


async def clothes_retrieval_node(state: GraphState, db: Session) -> GraphState:
    """
    衣物检索节点

    只从衣柜中已有品类检索衣物，缺失品类由 LLM missing_advice 提供文字建议。
    """
    user_id = state["user_id"]
    outfit_plan = state.get("outfit_plan")
    temperature = state.get("target_temperature")
    available_categories = state.get("available_categories", [])

    if not outfit_plan:
        state["error"] = "没有穿搭方案，无法检索衣物"
        return state

    try:
        # 用 to_thread 避免阻塞事件循环，只检索可用品类
        selected_clothes = await asyncio.to_thread(
            retrieve_by_scheme, db, user_id, outfit_plan, temperature, available_categories
        )
        state["selected_clothes"] = selected_clothes
    except Exception as e:
        state["error"] = f"衣物检索失败: {str(e)}"

    return state
