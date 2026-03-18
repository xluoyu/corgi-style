import random
import uuid
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models import UserClothes, ClothesCategory, TemperatureRange, Scene

class PlanAgent:
    def __init__(self, db: Session):
        self.db = db

    def generate_schemes(self, user_id: str, temperature: float, city: str, scene: str = "daily") -> List[Dict]:
        schemes = []
        scheme_id = str(uuid.uuidint())[:8]

        temp_category = self._get_temp_category(temperature)
        color_palettes = self._get_color_palettes(scene, temp_category)

        for idx, palette in enumerate(color_palettes):
            scheme = {
                "scheme_id": f"{scheme_id}-{idx+1}",
                "temperature": temperature,
                "city": city,
                "scene": scene,
                "temp_category": temp_category,
                "items": {
                    "top": {"color": palette["top"], "category": "top"},
                    "pants": {"color": palette["pants"], "category": "pants"},
                    "outer": {"color": palette["outer"], "category": "outer"} if temp_category in ["spring_autumn", "winter"] else None,
                    "inner": {"color": palette["inner"], "category": "inner"} if temp_category in ["winter"] else None,
                    "accessory": {"color": palette.get("accessory"), "category": "accessory"} if random.random() > 0.5 else None,
                },
                "description": self._generate_description(palette, temp_category, scene)
            }
            scheme["items"] = {k: v for k, v in scheme["items"].items() if v is not None}
            schemes.append(scheme)

        return schemes

    def _get_temp_category(self, temperature: float) -> str:
        if temperature >= 25:
            return "summer"
        elif temperature >= 10:
            return "spring_autumn"
        else:
            return "winter"

    def _get_color_palettes(self, scene: str, temp_category: str) -> List[Dict]:
        palettes = {
            "daily": {
                "summer": [
                    {"top": "白色", "pants": "浅蓝色", "outer": None, "inner": None, "accessory": "棕色"},
                    {"top": "浅灰色", "pants": "卡其色", "outer": None, "inner": None, "accessory": "黑色"},
                    {"top": "淡蓝色", "pants": "白色", "outer": None, "inner": None, "accessory": "银色"},
                ],
                "spring_autumn": [
                    {"top": "米白色", "pants": "深蓝色", "outer": "浅灰色", "inner": None, "accessory": "棕色"},
                    {"top": "浅棕色", "pants": "黑色", "outer": "深绿色", "inner": None, "accessory": "银色"},
                    {"top": "淡粉色", "pants": "浅蓝色", "outer": "卡其色", "inner": None, "accessory": "金色"},
                ],
                "winter": [
                    {"top": "深灰色", "pants": "黑色", "outer": "深蓝色", "inner": "白色", "accessory": "灰色"},
                    {"top": "酒红色", "pants": "深灰色", "outer": "黑色", "inner": "浅灰色", "accessory": "棕色"},
                    {"top": "墨绿色", "pants": "深蓝色", "outer": "灰色", "inner": "米白色", "accessory": "黑色"},
                ]
            },
            "work": {
                "summer": [
                    {"top": "白色", "pants": "深蓝色", "outer": None, "inner": None, "accessory": "黑色"},
                    {"top": "浅蓝色", "pants": "黑色", "outer": None, "inner": None, "accessory": "银色"},
                    {"top": "白色", "pants": "灰色", "outer": None, "inner": None, "accessory": "深蓝色"},
                ],
                "spring_autumn": [
                    {"top": "浅灰色", "pants": "深蓝色", "outer": "黑色", "inner": None, "accessory": "银色"},
                    {"top": "白色", "pants": "黑色", "outer": "深灰色", "inner": None, "accessory": "黑色"},
                    {"top": "浅蓝色", "pants": "深灰色", "outer": "卡其色", "inner": None, "accessory": "棕色"},
                ],
                "winter": [
                    {"top": "白色", "pants": "深蓝色", "outer": "黑色", "inner": "浅灰色", "accessory": "黑色"},
                    {"top": "浅灰色", "pants": "黑色", "outer": "深蓝色", "inner": "白色", "accessory": "银色"},
                    {"top": "深灰色", "pants": "深灰色", "outer": "灰色", "inner": "白色", "accessory": "黑色"},
                ]
            },
            "sport": {
                "summer": [
                    {"top": "白色", "pants": "黑色", "outer": None, "inner": None, "accessory": "黑色"},
                    {"top": "荧光绿", "pants": "黑色", "outer": None, "inner": None, "accessory": "白色"},
                    {"top": "浅蓝色", "pants": "白色", "outer": None, "inner": None, "accessory": "灰色"},
                ],
                "spring_autumn": [
                    {"top": "黑色", "pants": "黑色", "outer": "灰色", "inner": None, "accessory": "白色"},
                    {"top": "深蓝色", "pants": "黑色", "outer": "黑色", "inner": None, "accessory": "荧光绿"},
                    {"top": "白色", "pants": "深灰色", "outer": "深蓝色", "inner": None, "accessory": "黑色"},
                ],
                "winter": [
                    {"top": "黑色", "pants": "黑色", "outer": "黑色", "inner": "白色", "accessory": "灰色"},
                    {"top": "深灰色", "pants": "黑色", "outer": "深蓝色", "inner": "黑色", "accessory": "白色"},
                    {"top": "白色", "pants": "深灰色", "outer": "灰色", "inner": "浅灰色", "accessory": "黑色"},
                ]
            },
            "date": {
                "summer": [
                    {"top": "白色", "pants": "浅蓝色", "outer": None, "inner": None, "accessory": "银色"},
                    {"top": "淡粉色", "pants": "白色", "outer": None, "inner": None, "accessory": "金色"},
                    {"top": "浅灰色", "pants": "卡其色", "outer": None, "inner": None, "accessory": "棕色"},
                ],
                "spring_autumn": [
                    {"top": "深棕色", "pants": "深蓝色", "outer": "灰色", "inner": None, "accessory": "银色"},
                    {"top": "酒红色", "pants": "黑色", "outer": "黑色", "inner": None, "accessory": "金色"},
                    {"top": "墨绿色", "pants": "灰色", "outer": "卡其色", "inner": None, "accessory": "棕色"},
                ],
                "winter": [
                    {"top": "酒红色", "pants": "深灰色", "outer": "黑色", "inner": "白色", "accessory": "金色"},
                    {"top": "深灰色", "pants": "黑色", "outer": "深蓝色", "inner": "浅灰色", "accessory": "银色"},
                    {"top": "黑色", "pants": "黑色", "outer": "灰色", "inner": "白色", "accessory": "黑色"},
                ]
            },
            "party": {
                "summer": [
                    {"top": "黑色", "pants": "黑色", "outer": None, "inner": None, "accessory": "银色"},
                    {"top": "白色", "pants": "深蓝色", "outer": None, "inner": None, "accessory": "金色"},
                    {"top": "深蓝色", "pants": "黑色", "outer": None, "inner": None, "accessory": "银色"},
                ],
                "spring_autumn": [
                    {"top": "黑色", "pants": "黑色", "outer": "亮片外套", "inner": None, "accessory": "金色"},
                    {"top": "深红色", "pants": "黑色", "outer": "黑色皮衣", "inner": None, "accessory": "银色"},
                    {"top": "深蓝色", "pants": "深灰色", "outer": "灰色西装", "inner": None, "accessory": "黑色"},
                ],
                "winter": [
                    {"top": "白色", "pants": "黑色", "outer": "黑色皮衣", "inner": "黑色", "accessory": "银色"},
                    {"top": "黑色", "pants": "黑色", "outer": "深蓝色大衣", "inner": "白色", "accessory": "金色"},
                    {"top": "深灰色", "pants": "黑色", "outer": "灰色西装", "inner": "浅灰色", "accessory": "黑色"},
                ]
            }
        }

        scene_palettes = palettes.get(scene, palettes["daily"])
        return scene_palettes.get(temp_category, scene_palettes["spring_autumn"])

    def _generate_description(self, palette: Dict, temp_category: str, scene: str) -> str:
        scene_desc = {
            "daily": "休闲日常",
            "work": "职场商务",
            "sport": "运动健身",
            "date": "约会出行",
            "party": "派对聚会"
        }

        temp_desc = {
            "summer": "清爽夏季",
            "spring_autumn": "春秋时节",
            "winter": "保暖冬季"
        }

        return f"{temp_desc.get(temp_category, '日常')} {scene_desc.get(scene, '穿搭')}"