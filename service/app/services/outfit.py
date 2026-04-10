"""穿搭生成服务"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.outfit import OutfitRecord, OutfitFeedback
from app.services.weather import WeatherService, get_weather
from app.services.wardrobe import (
    WardrobeService,
    ClothingItem,
    ClothingAttrs,
    MatchContext,
    search_wardrobe
)


@dataclass
class OutfitContext:
    """穿搭上下文"""
    user_id: str
    date: Optional[str] = None  # 日期
    location: Optional[str] = None  # 城市
    occasion: Optional[str] = None  # 场合
    style: Optional[str] = None  # 风格偏好
    temperature: Optional[float] = None  # 温度（直接指定，不查天气）


@dataclass
class OutfitResult:
    """穿搭结果"""
    items: List[ClothingItem]
    description: str
    weather: Optional[Dict[str, Any]] = None
    occasion: str
    match_score: float = 0.0


@dataclass
class OutfitAnalysis:
    """整套穿搭图片分析结果"""
    overall_style: str
    items: List[Dict[str, Any]]  # 识别出的各件衣物
    style_tags: List[str]
    color_palette: List[str]
    description: Optional[str] = None


@dataclass
class SimilarOutfitResult:
    """类似穿搭结果"""
    matched_items: List[Dict[str, Any]]  # {item: ClothingItem, match_score: float}
    missing_items: List[Dict[str, str]]  # {type: str, color: str, importance: str}
    suggestions: str


class OutfitService:
    """穿搭服务"""

    def __init__(self, db: Session):
        self.db = db
        self.wardrobe_service = WardrobeService(db)
        self.weather_service = WeatherService()

    async def generate_outfit(
        self,
        context: OutfitContext
    ) -> OutfitResult:
        """
        综合天气、衣柜、偏好生成穿搭方案

        Args:
            context: 穿搭上下文

        Returns:
            穿搭结果
        """
        # 1. 获取天气
        weather_info = None
        temperature_range = "all_season"

        if context.location:
            weather_info = await get_weather(context.location, context.date)
            if weather_info:
                temperature_range = self.weather_service.get_temperature_range(
                    weather_info.temperature
                )
                context.temperature = weather_info.temperature

        # 2. 查询衣柜（按条件过滤）
        filters = {}
        if context.occasion:
            filters["scene"] = context.occasion
        if temperature_range:
            filters["temperature_range"] = temperature_range

        wardrobe_items = self.wardrobe_service.search_wardrobe(context.user_id, filters)

        if not wardrobe_items:
            # 如果没有精确匹配，放宽条件
            wardrobe_items = self.wardrobe_service.search_wardrobe(context.user_id, {})

        # 3. 简单搭配逻辑：选一套完整的搭配
        outfit_items = self._build_outfit(wardrobe_items, context)

        # 4. 生成描述
        description = self._generate_description(outfit_items, context, weather_info)

        return OutfitResult(
            items=outfit_items,
            description=description,
            weather={
                "temperature": weather_info.temperature if weather_info else context.temperature,
                "weather": weather_info.weather if weather_info else "未知",
                "location": context.location
            } if weather_info or context.temperature else None,
            occasion=context.occasion or "日常",
            match_score=0.8  # TODO: 计算真实匹配分数
        )

    async def generate_similar_outfit(
        self,
        user_id: str,
        outfit_analysis: OutfitAnalysis,
        context: Optional[OutfitContext] = None
    ) -> SimilarOutfitResult:
        """
        基于参考穿搭图片的风格，用用户衣柜衣物生成类似搭配

        Args:
            user_id: 用户 ID
            outfit_analysis: 参考穿搭图片分析结果
            context: 可选的场合/季节上下文

        Returns:
            类似穿搭结果
        """
        # 1. 获取天气（如有）
        temperature_range = "all_season"
        if context and context.location:
            weather_info = await get_weather(context.location, context.date)
            if weather_info:
                temperature_range = self.weather_service.get_temperature_range(
                    weather_info.temperature
                )

        # 2. 搜索衣柜（匹配风格标签）
        filters = {"temperature_range": temperature_range}
        wardrobe_items = self.wardrobe_service.search_wardrobe(user_id, filters)

        # 3. 匹配每个参考衣物
        matched = []
        missing = []
        reference_items = outfit_analysis.items  # [{type, color, position}]

        # 建立衣柜索引（按品类）
        wardrobe_by_category = {}
        for item in wardrobe_items:
            if item.category not in wardrobe_by_category:
                wardrobe_by_category[item.category] = []
            wardrobe_by_category[item.category].append(item)

        # 匹配每件参考衣物
        for ref_item in reference_items:
            ref_type = ref_item.get("type", "").lower()
            ref_color = ref_item.get("color", "")
            position = ref_item.get("position", "")

            # 找对应品类的衣柜衣物
            category = self._infer_category(ref_type, position)
            candidates = wardrobe_by_category.get(category, [])

            if candidates:
                # 颜色匹配优先
                best_match = None
                best_score = 0
                for cand in candidates:
                    score = 0.5
                    if cand.color and ref_color:
                        if cand.color.lower() in ref_color.lower() or ref_color.lower() in cand.color.lower():
                            score = 0.9
                    if score > best_score:
                        best_score = score
                        best_match = cand

                if best_match:
                    matched.append({
                        "item": best_match,
                        "match_score": best_score,
                        "reference": ref_item
                    })
            else:
                # 衣柜中没有这类衣物
                missing.append({
                    "type": ref_type,
                    "color": ref_color,
                    "position": position,
                    "importance": "高" if position in ["上装", "下装"] else "中"
                })

        # 4. 生成建议
        suggestions = self._generate_suggestions(matched, missing, outfit_analysis)

        return SimilarOutfitResult(
            matched_items=matched,
            missing_items=missing,
            suggestions=suggestions
        )

    def _build_outfit(
        self,
        wardrobe_items: List[ClothingItem],
        context: OutfitContext
    ) -> List[ClothingItem]:
        """从衣柜中构建一套完整穿搭"""
        if not wardrobe_items:
            return []

        outfit = []
        selected_ids = set()

        # 按品类优先级选择
        priority_order = ["outer", "top", "inner", "pants", "accessory"]

        for category in priority_order:
            category_items = [
                item for item in wardrobe_items
                if item.category == category and item.id not in selected_ids
            ]

            if category_items:
                # 优先选择 wear_count 高的（常穿的）
                category_items.sort(key=lambda x: x.wear_count, reverse=True)
                selected = category_items[0]
                outfit.append(selected)
                selected_ids.add(selected.id)

        return outfit

    def _generate_description(
        self,
        items: List[ClothingItem],
        context: OutfitContext,
        weather_info: Any = None
    ) -> str:
        """生成穿搭描述"""
        if not items:
            return "衣柜中没有合适的衣物，建议添加更多衣服"

        parts = []
        for item in items:
            if item.name:
                parts.append(item.name)
            elif item.category:
                parts.append(item.category)

        base = "、".join(parts) if parts else "基础搭配"

        # 添加场合说明
        if context.occasion:
            occasion_text = {
                "daily": "日常",
                "work": "通勤",
                "date": "约会",
                "party": "派对",
                "sport": "运动"
            }.get(context.occasion, context.occasion)
            base = f"{occasion_text}穿搭：{base}"

        # 添加温度说明
        if weather_info:
            base += f"，今天{weather_info.temperature}度，{weather_info.weather}"

        return base

    def _generate_suggestions(
        self,
        matched: List[Dict],
        missing: List[Dict],
        outfit_analysis: OutfitAnalysis
    ) -> str:
        """生成搭配建议文案"""
        parts = []

        # 已匹配的部分
        if matched:
            matched_names = [m["item"].name or m["item"].category for m in matched]
            parts.append(f"衣柜中已有：{'、'.join(matched_names)}")

        # 缺失的部分
        if missing:
            missing_strs = [f"{m.get('color', '')}{m.get('type', '')}" for m in missing]
            parts.append(f"建议购买：{'、'.join(missing_strs)}")

        # 风格总结
        if outfit_analysis.overall_style:
            parts.append(f"整体风格：{outfit_analysis.overall_style}")

        return "。".join(parts) if parts else "衣柜衣物可以完成此搭配"

    def _infer_category(self, type_str: str, position: str = "") -> str:
        """从类型字符串推断品类"""
        type_str = type_str.lower()
        position = position.lower()

        # 根据位置判断
        if "上装" in position or "外套" in type_str or "衬衫" in type_str or "T恤" in type_str:
            return "top"
        if "下装" in position or "裤" in type_str or "裙" in type_str:
            return "pants"
        if "外套" in type_str or "夹克" in type_str or "大衣" in type_str:
            return "outer"
        if "内搭" in position or "背心" in type_str:
            return "inner"
        if "鞋" in type_str or "包" in type_str or "配饰" in type_str:
            return "accessory"

        return "top"  # 默认


async def generate_outfit(context: OutfitContext, db: Session) -> OutfitResult:
    """便捷函数：生成穿搭"""
    service = OutfitService(db)
    return await service.generate_outfit(context)


async def generate_similar_outfit(
    user_id: str,
    outfit_analysis: OutfitAnalysis,
    context: Optional[OutfitContext] = None,
    db: Session = None
) -> SimilarOutfitResult:
    """便捷函数：生成类似穿搭"""
    service = OutfitService(db)
    return await service.generate_similar_outfit(user_id, outfit_analysis, context)
