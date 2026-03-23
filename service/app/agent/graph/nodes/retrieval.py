"""衣物检索节点"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.agent.graph.state import GraphState
from app.models import UserClothes, TemperatureRange
from app.services.oss_uploader import oss_uploader


def retrieve_by_scheme(
    db: Session,
    user_id: str,
    plan: Dict[str, Any],
    temperature: Optional[float] = None
) -> Dict[str, Optional[Dict]]:
    """
    按穿搭方案检索衣物

    Args:
        db: 数据库会话
        user_id: 用户ID
        plan: 穿搭方案（包含 items）
        temperature: 温度

    Returns:
        每个品类的最佳匹配衣物
    """
    result = {}
    items = plan.get("items", {})

    # 获取温度范围
    temp_ranges = _get_temp_ranges(temperature) if temperature else None

    for item_name, item_info in items.items():
        category = item_info.get("category")
        expected_color = item_info.get("color")

        if not category:
            continue

        # 构建查询
        query = db.query(UserClothes).filter(
            UserClothes.user_id == user_id,
            UserClothes.category == category,
            UserClothes.is_deleted == False
        )

        # 温度过滤
        if temp_ranges:
            query = query.filter(UserClothes.temperature_range.in_(temp_ranges))

        clothes_list = query.all()

        # 颜色匹配
        matched = None
        if expected_color and clothes_list:
            for clothes in clothes_list:
                if _color_match(expected_color, clothes.color or "", clothes.description or ""):
                    matched = _clothes_to_dict(clothes)
                    break

        # 如果没找到精确匹配，取第一件
        if not matched and clothes_list:
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

    根据穿搭方案从用户衣柜检索具体衣物
    """
    user_id = state["user_id"]
    outfit_plan = state.get("outfit_plan")
    temperature = state.get("target_temperature")

    if not outfit_plan:
        state["error"] = "没有穿搭方案，无法检索衣物"
        return state

    try:
        selected_clothes = retrieve_by_scheme(
            db=db,
            user_id=user_id,
            plan=outfit_plan,
            temperature=temperature
        )
        state["selected_clothes"] = selected_clothes
    except Exception as e:
        state["error"] = f"衣物检索失败: {str(e)}"

    return state
