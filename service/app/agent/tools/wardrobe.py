"""衣柜相关工具"""
import json
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool

from app.services.wardrobe import (
    search_wardrobe as service_search_wardrobe,
    add_clothes as service_add_clothes,
    ClothingAttrs,
    ClothingItem,
    MatchContext
)


@tool
async def search_wardrobe(
    category: Optional[str] = None,
    color: Optional[str] = None,
    scene: Optional[str] = None,
    temperature_range: Optional[str] = None,
    user_id: str = ""
) -> str:
    """
    查询用户衣柜中的衣物。

    Args:
        category: 衣物品类（top/pants/outer/inner/accessory）
        color: 颜色
        scene: 场合（daily/work/date/party/sport）
        temperature_range: 温度范围（summer/spring_autumn/winter/all_season）
        user_id: 用户 ID（必填）

    Returns:
        JSON 格式的衣物列表
    """
    from app.database import SessionLocal

    if not user_id:
        return json.dumps({"error": "user_id is required"})

    filters = {}
    if category:
        filters["category"] = category
    if color:
        filters["color"] = color
    if scene:
        filters["scene"] = scene
    if temperature_range:
        filters["temperature_range"] = temperature_range

    db = SessionLocal()
    try:
        items = service_search_wardrobe(user_id, db, filters)
        return json.dumps({
            "items": [item.__dict__ for item in items],
            "count": len(items)
        }, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@tool
async def add_to_wardrobe(
    category: str = "top",
    color: Optional[str] = None,
    name: Optional[str] = None,
    image_url: str = "",
    material: Optional[str] = None,
    temperature_range: Optional[str] = None,
    wear_method: Optional[str] = None,
    scene: Optional[str] = None,
    tags: Optional[str] = None,
    user_id: str = ""
) -> str:
    """
    将衣物添加到用户衣柜。

    Args:
        category: 衣物品类（top/pants/outer/inner/accessory）
        color: 颜色
        name: 衣物名称
        image_url: 图片 URL
        material: 材质
        temperature_range: 温度范围
        wear_method: 穿着方式
        scene: 场合
        tags: 标签（JSON 数组格式字符串）
        user_id: 用户 ID（必填）

    Returns:
        JSON 格式的创建结果
    """
    from app.database import SessionLocal

    if not user_id:
        return json.dumps({"error": "user_id is required"})

    # 解析 tags
    tag_list = None
    if tags:
        try:
            tag_list = json.loads(tags)
        except json.JSONDecodeError:
            tag_list = [t.strip() for t in tags.split(",")]

    attrs = ClothingAttrs(
        category=category,
        color=color,
        name=name,
        original_image_url=image_url,
        material=material,
        temperature_range=temperature_range,
        wear_method=wear_method,
        scene=scene,
        tags=tag_list
    )

    db = SessionLocal()
    try:
        item = service_add_clothes(user_id, db, attrs)
        return json.dumps({
            "success": True,
            "item": item.__dict__,
            "message": f"已添加 {item.name or item.category} 到衣柜"
        }, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@tool
async def match_outfit(
    new_item_type: str = "top",
    new_item_color: Optional[str] = None,
    new_item_name: Optional[str] = None,
    occasion: Optional[str] = None,
    season: Optional[str] = None,
    user_id: str = ""
) -> str:
    """
    为新衣服匹配衣柜中的搭配。

    Args:
        new_item_type: 新衣服品类
        new_item_color: 新衣服颜色
        new_item_name: 新衣服名称
        occasion: 场合
        season: 季节
        user_id: 用户 ID（必填）

    Returns:
        JSON 格式的搭配建议
    """
    from app.database import SessionLocal

    if not user_id:
        return json.dumps({"error": "user_id is required"})

    # 构建新衣服对象
    new_item = ClothingItem(
        id="temp",
        user_id=user_id,
        name=new_item_name,
        category=new_item_type,
        sub_category=None,
        original_image_url="",
        cartoon_image_url=None,
        color=new_item_color,
        material=None,
        temperature_range=None,
        wear_method=None,
        scene=None,
        tags=[],
        wear_count=0,
        last_worn_at=None,
        created_at=""
    )

    # 构建上下文
    context = None
    if occasion or season:
        context = MatchContext(occasion=occasion, season=season)

    # 搜索衣柜
    db = SessionLocal()
    try:
        wardrobe_items = service_search_wardrobe(user_id, db, {})
        from app.services.wardrobe import match_outfit as service_match_outfit
        suggestions = service_match_outfit(new_item, wardrobe_items, context)

        return json.dumps({
            "suggestions": [
                {
                    "items": [item.__dict__ for item in s.items],
                    "match_score": s.match_score,
                    "description": s.description,
                    "missing_items": s.missing_items
                }
                for s in suggestions
            ]
        }, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


def create_wardrobe_tools():
    """创建衣柜相关工具列表"""
    return [search_wardrobe, add_to_wardrobe, match_outfit]
