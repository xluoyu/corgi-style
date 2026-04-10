"""衣柜服务 - 衣物 CRUD 和搭配"""
import json
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.clothes import UserClothes, ClothesCategory, TemperatureRange, Scene, WearMethod
from app.models.user import User


@dataclass
class ClothingAttrs:
    """衣物属性（用于创建或更新）"""
    name: Optional[str] = None
    category: str = "top"
    sub_category: Optional[str] = None
    original_image_url: str = ""
    cartoon_image_url: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    temperature_range: Optional[str] = None
    wear_method: Optional[str] = None
    scene: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class ClothingItem:
    """衣物项目（用于返回）"""
    id: str
    user_id: str
    name: Optional[str]
    category: str
    sub_category: Optional[str]
    original_image_url: str
    cartoon_image_url: Optional[str]
    color: Optional[str]
    material: Optional[str]
    temperature_range: Optional[str]
    wear_method: Optional[str]
    scene: Optional[str]
    tags: List[str]
    wear_count: int
    last_worn_at: Optional[str]
    created_at: str

    @classmethod
    def from_model(cls, model: UserClothes) -> "ClothingItem":
        tags = []
        if model.tags:
            if isinstance(model.tags, str):
                try:
                    tags = json.loads(model.tags)
                except json.JSONDecodeError:
                    tags = []
            elif isinstance(model.tags, list):
                tags = model.tags

        return cls(
            id=str(model.id),
            user_id=str(model.user_id),
            name=model.name,
            category=model.category,
            sub_category=model.sub_category,
            original_image_url=model.original_image_url,
            cartoon_image_url=model.cartoon_image_url,
            color=model.color,
            material=model.material,
            temperature_range=model.temperature_range,
            wear_method=model.wear_method,
            scene=model.scene,
            tags=tags,
            wear_count=model.wear_count or 0,
            last_worn_at=model.last_worn_at.isoformat() if model.last_worn_at else None,
            created_at=model.created_at.isoformat() if model.created_at else ""
        )


@dataclass
class MatchContext:
    """搭配上下文"""
    occasion: Optional[str] = None  # daily/work/date/party
    season: Optional[str] = None  # summer/spring_autumn/winter
    style: Optional[str] = None  # 风格偏好
    temperature: Optional[float] = None  # 温度


@dataclass
class OutfitSuggestion:
    """搭配建议"""
    items: List[ClothingItem]
    match_score: float
    description: str
    missing_items: List[str] = field(default_factory=list)


class WardrobeService:
    """衣柜服务"""

    def __init__(self, db: Session):
        self.db = db

    def search_wardrobe(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ClothingItem]:
        """
        查询用户衣柜

        Args:
            user_id: 用户 ID
            filters: 过滤条件 {category, color, scene, temperature_range, tags}

        Returns:
            衣物列表
        """
        query = self.db.query(UserClothes).filter(
            and_(
                UserClothes.user_id == UUID(user_id),
                UserClothes.is_deleted == False
            )
        )

        if filters:
            if filters.get("category"):
                query = query.filter(UserClothes.category == filters["category"])
            if filters.get("color"):
                query = query.filter(UserClothes.color.ilike(f"%{filters['color']}%"))
            if filters.get("scene"):
                query = query.filter(UserClothes.scene == filters["scene"])
            if filters.get("temperature_range"):
                query = query.filter(UserClothes.temperature_range == filters["temperature_range"])
            if filters.get("tags"):
                # JSONB 包含任一标签
                for tag in filters["tags"]:
                    query = query.filter(UserClothes.tags.contains(tag))

        items = query.order_by(UserClothes.wear_count.desc(), UserClothes.created_at.desc()).all()
        return [ClothingItem.from_model(item) for item in items]

    def add_clothes(self, user_id: str, attrs: ClothingAttrs) -> ClothingItem:
        """
        添加衣物到衣柜

        Args:
            user_id: 用户 ID
            attrs: 衣物属性

        Returns:
            创建的衣物
        """
        # 验证用户存在
        user = self.db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            raise ValueError(f"用户不存在: {user_id}")

        tags_json = json.dumps(attrs.tags) if attrs.tags else "[]"

        item = UserClothes(
            user_id=UUID(user_id),
            name=attrs.name,
            category=attrs.category,
            sub_category=attrs.sub_category,
            original_image_url=attrs.original_image_url,
            cartoon_image_url=attrs.cartoon_image_url,
            color=attrs.color,
            material=attrs.material,
            temperature_range=attrs.temperature_range,
            wear_method=attrs.wear_method,
            scene=attrs.scene,
            tags=tags_json,
            analysis_completed=1
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return ClothingItem.from_model(item)

    def update_clothes(self, user_id: str, clothes_id: str, attrs: Dict[str, Any]) -> ClothingItem:
        """
        更新衣物信息

        Args:
            user_id: 用户 ID
            clothes_id: 衣物 ID
            attrs: 更新属性

        Returns:
            更新后的衣物
        """
        item = self.db.query(UserClothes).filter(
            and_(
                UserClothes.id == UUID(clothes_id),
                UserClothes.user_id == UUID(user_id),
                UserClothes.is_deleted == False
            )
        ).first()

        if not item:
            raise ValueError(f"衣物不存在或无权访问: {clothes_id}")

        # 只更新提供的字段
        for key, value in attrs.items():
            if hasattr(item, key) and value is not None:
                if key == "tags" and isinstance(value, list):
                    setattr(item, key, json.dumps(value))
                else:
                    setattr(item, key, value)

        self.db.commit()
        self.db.refresh(item)

        return ClothingItem.from_model(item)

    def delete_clothes(self, user_id: str, clothes_id: str) -> bool:
        """
        软删除衣物

        Args:
            user_id: 用户 ID
            clothes_id: 衣物 ID

        Returns:
            是否成功
        """
        item = self.db.query(UserClothes).filter(
            and_(
                UserClothes.id == UUID(clothes_id),
                UserClothes.user_id == UUID(user_id),
                UserClothes.is_deleted == False
            )
        ).first()

        if not item:
            return False

        item.is_deleted = True
        item.deleted_at = datetime.now()
        self.db.commit()

        return True

    def match_outfit(
        self,
        new_item: ClothingItem,
        wardrobe: List[ClothingItem],
        context: Optional[MatchContext] = None
    ) -> List[OutfitSuggestion]:
        """
        为新衣服匹配衣柜中的搭配

        Args:
            new_item: 新衣服（可以是刚上传待入库的）
            wardrobe: 用户衣柜现有衣物
            context: 搭配上下文

        Returns:
            搭配建议列表
        """
        suggestions = []

        # 根据新衣服的品类找互补品类
        complement_categories = {
            "top": ["pants", "outer", "accessory"],
            "pants": ["top", "outer", "shoes"],
            "outer": ["top", "pants", "accessory"],
            "inner": ["top", "outer"],
            "accessory": ["top", "pants", "outer"],
        }

        needed = complement_categories.get(new_item.category, [])

        # 简单匹配逻辑：同色系/同场景/频率高的优先
        matched = []
        for item in wardrobe:
            if item.category in needed:
                # 计算匹配分数
                score = 0.5  # 基础分

                if item.color and new_item.color:
                    # 颜色协调（同色系 +0.2，对比色 +0.1）
                    if self._colors_match(item.color, new_item.color):
                        score += 0.3

                if item.scene == new_item.scene or not new_item.scene:
                    score += 0.2

                if context and context.occasion:
                    if item.scene == context.occasion:
                        score += 0.2

                matched.append((item, score))

        # 按分数排序
        matched.sort(key=lambda x: x[1], reverse=True)

        # 生成分组搭配建议
        if matched:
            suggestion = OutfitSuggestion(
                items=[new_item] + [m[0] for m in matched[:4]],
                match_score=matched[0][1] if matched else 0,
                description=f"基于{new_item.name or new_item.category}的搭配方案"
            )
            suggestions.append(suggestion)

        return suggestions

    def _colors_match(self, color1: str, color2: str) -> bool:
        """简单颜色协调判断"""
        # 基础色系映射
        color_groups = {
            "black": ["black", "gray", "white", "navy"],
            "white": ["white", "gray", "black", "navy", "blue"],
            "gray": ["black", "white", "blue", "navy"],
            "navy": ["white", "gray", " beige", "brown"],
            "blue": ["white", "gray", "black", "khaki"],
            "brown": ["beige", "white", "black", "olive"],
            "beige": ["brown", "navy", "white", "blue"],
            "black": ["white", "gray", "blue", "red"],
            "red": ["black", "white", "gray", "navy"],
            "green": ["white", "gray", "black", "brown"],
        }

        c1_lower = color1.lower()
        c2_lower = color2.lower()

        for base, group in color_groups.items():
            if c1_lower in group and c2_lower in group:
                return True

        return False

    def get_wardrobe_stats(self, user_id: str) -> Dict[str, Any]:
        """获取衣柜统计"""
        items = self.db.query(UserClothes).filter(
            and_(
                UserClothes.user_id == UUID(user_id),
                UserClothes.is_deleted == False
            )
        ).all()

        categories = {}
        colors = {}
        total_wears = 0

        for item in items:
            categories[item.category] = categories.get(item.category, 0) + 1
            if item.color:
                colors[item.color] = colors.get(item.color, 0) + 1
            total_wears += item.wear_count or 0

        return {
            "total_items": len(items),
            "categories": categories,
            "colors": colors,
            "total_wears": total_wears
        }


def search_wardrobe(
    user_id: str,
    db: Session,
    filters: Optional[Dict[str, Any]] = None
) -> List[ClothingItem]:
    """便捷函数：查询衣柜"""
    service = WardrobeService(db)
    return service.search_wardrobe(user_id, filters)


def add_clothes(user_id: str, db: Session, attrs: ClothingAttrs) -> ClothingItem:
    """便捷函数：添加衣物"""
    service = WardrobeService(db)
    return service.add_clothes(user_id, attrs)


def delete_clothes(user_id: str, db: Session, clothes_id: str) -> bool:
    """便捷函数：删除衣物"""
    service = WardrobeService(db)
    return service.delete_clothes(user_id, clothes_id)


def match_outfit(
    new_item: ClothingItem,
    wardrobe: List[ClothingItem],
    context: Optional[MatchContext] = None
) -> List[OutfitSuggestion]:
    """便捷函数：搭配建议（不需要 DB）"""
    service = WardrobeService(db=None)  # match_outfit 不需要 db
    return service.match_outfit(new_item, wardrobe, context)
