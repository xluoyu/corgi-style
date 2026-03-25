"""Agent Tools — 按业务分组的 LangChain 工具集。

注意：旧的 agent/tools.py 已迁移至此，RetrievalTool 等仍可通过：
  from app.agent.tools import RetrievalTool
访问。
"""
from typing import List, Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import UserClothes, ClothesCategory, TemperatureRange
from app.agent.tools.context import (
    get_db_for_tools,
    get_current_user_id,
    set_tool_context,
)
from app.agent.tools.shared import (
    get_weather,
    analyze_clothing_image,
    remember_context,
    recall_context,
    SHARED_TOOLS,
)


# ============================================================
# 旧版 RetrievalTool（兼容现有 supervisor.py 等）
# ============================================================

class RetrievalTool:
    """衣物检索工具。兼容旧版 agent/tools.py。"""

    def __init__(self, db: Session):
        self.db = db

    def retrieve_by_conditions(
        self,
        user_id: str,
        category: Optional[str] = None,
        color: Optional[str] = None,
        temperature: Optional[float] = None,
        temperature_range: Optional[str] = None
    ) -> List[UserClothes]:
        query = self.db.query(UserClothes).filter(UserClothes.user_id == user_id)

        if category:
            query = query.filter(UserClothes.category == category)

        if color:
            query = query.filter(
                UserClothes.color.contains(color) | UserClothes.description.contains(color)
            )

        if temperature is not None:
            if temperature >= 25:
                temp_ranges = [TemperatureRange.summer, TemperatureRange.all_season]
            elif temperature >= 10:
                temp_ranges = [TemperatureRange.spring_autumn, TemperatureRange.all_season]
            else:
                temp_ranges = [TemperatureRange.winter, TemperatureRange.all_season]
            query = query.filter(UserClothes.temperature_range.in_(temp_ranges))

        return query.all()

    def retrieve_by_scheme(self, user_id: str, scheme: Dict, temperature: float) -> Dict[str, Optional[UserClothes]]:
        result = {}
        temp_ranges = self._get_temp_ranges(temperature)
        items = scheme.get("items", {})

        if not isinstance(items, dict):
            return result

        for item_name, item_info in items.items():
            category = item_info.get("category")
            color = item_info.get("color")

            clothes_list = self.db.query(UserClothes).filter(
                and_(
                    UserClothes.user_id == user_id,
                    UserClothes.category == category,
                    UserClothes.temperature_range.in_(temp_ranges)
                )
            ).all()

            matched = None
            if color:
                for clothes in clothes_list:
                    if color in clothes.color or (clothes.description and color in clothes.description):
                        matched = clothes
                        break

            if not matched and clothes_list:
                matched = clothes_list[0]

            result[item_name] = matched

        return result

    def _get_temp_ranges(self, temperature: float) -> List[str]:
        if temperature >= 25:
            return [TemperatureRange.summer.value, TemperatureRange.all_season.value]
        elif temperature >= 10:
            return [TemperatureRange.spring_autumn.value, TemperatureRange.all_season.value]
        else:
            return [TemperatureRange.winter.value, TemperatureRange.all_season.value]

    def get_user_clothes(self, user_id: str) -> List[UserClothes]:
        return self.db.query(UserClothes).filter(UserClothes.user_id == user_id).all()


__all__ = [
    # context
    "get_db_for_tools",
    "get_current_user_id",
    "set_tool_context",
    # shared tools
    "get_weather",
    "analyze_clothing_image",
    "remember_context",
    "recall_context",
    "SHARED_TOOLS",
    # old RetrievalTool (compat)
    "RetrievalTool",
]
