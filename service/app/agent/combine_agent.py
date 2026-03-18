from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models import UserClothes, ClothesCategory, TemperatureRange

class CombineAgent:
    def __init__(self, db: Session):
        self.db = db

    def combine_outfit(
        self,
        user_id: str,
        temperature: float,
        existing_clothes: Dict[str, Optional]
    ) -> Dict[str, Optional[UserClothes]]:
        result = dict(existing_clothes)
        temp_ranges = self._get_temp_ranges(temperature)

        required_categories = ["top", "pants", "outer"]
        if temperature < 15:
            required_categories.insert(2, "inner")

        for category in required_categories:
            if not result.get(category):
                result[category] = self._find_best_match(user_id, category, temp_ranges)

        return result

    def _find_best_match(
        self,
        user_id: str,
        category: str,
        temp_ranges: List[str]
    ) -> Optional[UserClothes]:
        query = self.db.query(UserClothes).filter(
            UserClothes.user_id == user_id,
            UserClothes.category == category,
            UserClothes.temperature_range.in_(temp_ranges)
        )

        clothes_list = query.all()
        if not clothes_list:
            query = self.db.query(UserClothes).filter(
                UserClothes.user_id == user_id,
                UserClothes.category == category
            )
            clothes_list = query.all()

        if clothes_list:
            return clothes_list[0]

        return None

    def _get_temp_ranges(self, temperature: float) -> List[str]:
        if temperature >= 25:
            return [TemperatureRange.summer.value, TemperatureRange.all_season.value]
        elif temperature >= 10:
            return [TemperatureRange.spring_autumn.value, TemperatureRange.all_season.value]
        else:
            return [TemperatureRange.winter.value, TemperatureRange.all_season.value]

    def generate_fallback_outfit(self, user_id: str, temperature: float) -> Dict[str, Optional[UserClothes]]:
        temp_ranges = self._get_temp_ranges(temperature)

        result = {}
        for category in ["top", "pants", "outer", "inner", "accessory"]:
            clothes = self._find_best_match(user_id, category, temp_ranges)
            result[category] = clothes

        return result