"""衣柜查询节点"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.agent.graph.state import GraphState
from app.models import UserClothes, ClothesCategory, TemperatureRange
from app.services.oss_uploader import oss_uploader


# 衣物类别映射
CATEGORY_MAPPING = {
    "衬衫": "top",
    "短袖": "top",
    "T恤": "top",
    "上衣": "top",
    "裤子": "pants",
    "长裤": "pants",
    "短裤": "pants",
    "裙子": "pants",
    "外套": "outer",
    "夹克": "outer",
    "大衣": "outer",
    "羽绒服": "outer",
    "毛衣": "outer",
    "卫衣": "outer",
    "内搭": "inner",
    "保暖": "inner",
    "配饰": "accessory",
    "围巾": "accessory",
    "帽子": "accessory",
    "包": "accessory",
    "包袋": "accessory",
}


def _map_chinese_category(category: str) -> Optional[str]:
    """将中文类别映射为英文"""
    return CATEGORY_MAPPING.get(category)


def _get_temp_ranges(temperature: float) -> List[str]:
    """根据温度获取适合的温度范围"""
    if temperature >= 25:
        return [TemperatureRange.summer.value, TemperatureRange.all_season.value]
    elif temperature >= 10:
        return [TemperatureRange.spring_autumn.value, TemperatureRange.all_season.value]
    else:
        return [TemperatureRange.winter.value, TemperatureRange.all_season.value]


def query_wardrobe(
    db: Session,
    user_id: str,
    category: Optional[str] = None,
    color: Optional[str] = None,
    temperature: Optional[float] = None,
    tags: Optional[List[str]] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    查询用户衣柜

    Args:
        db: 数据库会话
        user_id: 用户ID
        category: 衣物类别（top/pants/outer/inner/accessory）
        color: 颜色（支持模糊匹配）
        temperature: 温度（用于筛选适合该温度的衣物）
        tags: 标签列表
        limit: 返回数量限制

    Returns:
        衣物列表
    """
    query = db.query(UserClothes).filter(
        UserClothes.user_id == user_id,
        UserClothes.is_deleted == False
    )

    # 类别过滤
    if category:
        # 支持中文类别映射
        mapped_category = _map_chinese_category(category)
        if mapped_category:
            query = query.filter(UserClothes.category == mapped_category)
        else:
            query = query.filter(UserClothes.category == category)

    # 颜色过滤（模糊匹配 color 或 description）
    if color:
        query = query.filter(
            (UserClothes.color.contains(color)) |
            (UserClothes.description.contains(color) if hasattr(UserClothes, 'description') else False)
        )

    # 温度范围过滤
    if temperature is not None:
        temp_ranges = _get_temp_ranges(temperature)
        query = query.filter(UserClothes.temperature_range.in_(temp_ranges))

    clothes = query.limit(limit).all()

    return [_clothes_to_dict(c) for c in clothes]


def get_wardrobe_stats(db: Session, user_id: str) -> Dict[str, Any]:
    """获取衣橱统计"""
    clothes = db.query(UserClothes).filter(
        UserClothes.user_id == user_id,
        UserClothes.is_deleted == False
    ).all()

    stats = {
        "total": len(clothes),
        "by_category": {},
        "by_color": {},
        "avg_wear_count": 0
    }

    total_wear = 0
    for c in clothes:
        # 按类别统计
        cat = c.category or "unknown"
        stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

        # 按颜色统计
        color = c.color or "unknown"
        stats["by_color"][color] = stats["by_color"].get(color, 0) + 1

        total_wear += c.wear_count or 0

    if clothes:
        stats["avg_wear_count"] = round(total_wear / len(clothes), 1)

    return stats


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


async def wardrobe_query_node(state: GraphState, db: Session) -> GraphState:
    """
    衣柜查询节点

    根据意图和实体查询用户衣柜
    """
    user_id = state["user_id"]
    intent = state.get("intent")
    entities = state.get("entities", {})

    # 获取查询参数
    category = entities.get("clothes_category")
    if not category:
        # 尝试从中文映射
        category = entities.get("category")

    color = entities.get("clothes_color")
    temperature = state.get("target_temperature")

    # 根据意图决定查询方式
    if intent == "query_wardrobe" or (intent == "unknown" and entities.get("query_type") == "count"):
        # 统计查询
        stats = get_wardrobe_stats(db, user_id)
        state["context"] = state.get("context", {})
        state["context"]["wardrobe_stats"] = stats
        state["user_clothes"] = []

    else:
        # 普通查询
        clothes_list = query_wardrobe(
            db=db,
            user_id=user_id,
            category=category,
            color=color,
            temperature=temperature
        )
        state["user_clothes"] = clothes_list

        # 按品类分组
        filtered_clothes = {}
        for c in clothes_list:
            cat = c["category"]
            if cat not in filtered_clothes:
                filtered_clothes[cat] = []
            filtered_clothes[cat].append(c)

        state["filtered_clothes"] = filtered_clothes

    return state
