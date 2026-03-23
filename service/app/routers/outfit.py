from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import OutfitCache
from app.services.image_searcher import image_searcher

router = APIRouter(prefix="/outfit", tags=["outfit"])


class GenerateOutfitRequest(BaseModel):
    city: str
    temperature: float
    scene: Optional[str] = "daily"


class OutfitItem(BaseModel):
    slot: str
    description: str
    color: str


class GenerateOutfitResponse(BaseModel):
    description: str
    temperature: float
    city: str
    scene: str
    image_url: str
    outfit_items: List[OutfitItem]
    cached: bool


class RefreshRequest(BaseModel):
    city: str
    temperature: float
    scene: Optional[str] = "daily"


class FeedbackRequest(BaseModel):
    user_id: str
    description: Optional[str] = None
    rating: Optional[int] = None


class FeedbackResponse(BaseModel):
    message: str


def _get_temp_range(temperature: float) -> str:
    if temperature >= 25:
        return "summer"
    elif temperature >= 10:
        return "spring_autumn"
    else:
        return "winter"


def _build_search_keywords(temperature: float, scene: str) -> list[str]:
    temp_range = _get_temp_range(temperature)

    season_kw = {
        "summer": ["summer", "light", "casual"],
        "spring_autumn": ["spring", "layered", "casual"],
        "winter": ["winter", "warm", "coat"]
    }[temp_range]

    scene_kw = {
        "daily": ["streetwear", "casual", "fashion"],
        "work": ["business", "professional", "fashion"],
        "sport": ["sport", "athletic", "fitness"],
        "date": ["chic", "fashion", "romantic"],
        "party": ["fashion", "trendy", "stylish"]
    }[scene]

    return ["fashion", "model", "portrait"] + season_kw + scene_kw


def _parse_outfit_items(description: str, scene: str) -> List[dict]:
    """根据场景和描述生成搭配单品列表"""
    temp_range = _get_temp_range(
        float(description.split("℃")[0].split("约")[-1])
        if "℃" in description else 15.0
    )

    items_by_scene = {
        "daily": {
            "summer": [
                {"slot": "上装", "description": "白色纯棉T恤", "color": "白色"},
                {"slot": "下装", "description": "浅蓝色九分牛仔裤", "color": "浅蓝色"},
                {"slot": "鞋履", "description": "白色低帮帆布鞋", "color": "白色"}
            ],
            "spring_autumn": [
                {"slot": "外套", "description": "浅灰色风衣", "color": "浅灰色"},
                {"slot": "上装", "description": "米白色棉质T恤", "color": "米白色"},
                {"slot": "下装", "description": "深蓝色直筒牛仔裤", "color": "深蓝色"},
                {"slot": "鞋履", "description": "棕色复古皮鞋", "color": "棕色"}
            ],
            "winter": [
                {"slot": "外套", "description": "深蓝色毛呢大衣", "color": "深蓝色"},
                {"slot": "上装", "description": "黑色高领毛衣", "color": "黑色"},
                {"slot": "下装", "description": "深灰色保暖休闲裤", "color": "深灰色"},
                {"slot": "配饰", "description": "灰色羊绒围巾", "color": "灰色"}
            ]
        },
        "work": {
            "summer": [
                {"slot": "上装", "description": "浅蓝色商务衬衫", "color": "浅蓝色"},
                {"slot": "下装", "description": "深灰色西裤", "color": "深灰色"},
                {"slot": "鞋履", "description": "黑色皮质皮鞋", "color": "黑色"}
            ],
            "spring_autumn": [
                {"slot": "外套", "description": "黑色简约西装", "color": "黑色"},
                {"slot": "上装", "description": "白色修身衬衫", "color": "白色"},
                {"slot": "下装", "description": "深蓝色西裤", "color": "深蓝色"},
                {"slot": "鞋履", "description": "黑色正装皮鞋", "color": "黑色"}
            ],
            "winter": [
                {"slot": "外套", "description": "深灰色毛料大衣", "color": "深灰色"},
                {"slot": "上装", "description": "白色衬衫+深色针织衫", "color": "白色"},
                {"slot": "下装", "description": "黑色西裤", "color": "黑色"},
                {"slot": "鞋履", "description": "黑色正装皮鞋", "color": "黑色"}
            ]
        },
        "sport": {
            "summer": [
                {"slot": "上装", "description": "黑色速干运动T恤", "color": "黑色"},
                {"slot": "下装", "description": "深灰色运动短裤", "color": "深灰色"},
                {"slot": "鞋履", "description": "白色透气跑鞋", "color": "白色"}
            ],
            "spring_autumn": [
                {"slot": "外套", "description": "深蓝色运动夹克", "color": "深蓝色"},
                {"slot": "上装", "description": "白色吸汗运动衫", "color": "白色"},
                {"slot": "下装", "description": "黑色运动长裤", "color": "黑色"},
                {"slot": "鞋履", "description": "黑色减震跑鞋", "color": "黑色"}
            ],
            "winter": [
                {"slot": "外套", "description": "黑色加绒运动外套", "color": "黑色"},
                {"slot": "上装", "description": "灰色保暖运动卫衣", "color": "灰色"},
                {"slot": "下装", "description": "深灰色加绒运动裤", "color": "深灰色"},
                {"slot": "鞋履", "description": "黑色防滑跑鞋", "color": "黑色"}
            ]
        },
        "date": {
            "summer": [
                {"slot": "上装", "description": "淡粉色亚麻衬衫", "color": "淡粉色"},
                {"slot": "下装", "description": "卡其色休闲长裤", "color": "卡其色"},
                {"slot": "鞋履", "description": "棕色麂皮乐福鞋", "color": "棕色"}
            ],
            "spring_autumn": [
                {"slot": "外套", "description": "深棕色皮夹克", "color": "深棕色"},
                {"slot": "上装", "description": "白色棉质T恤", "color": "白色"},
                {"slot": "下装", "description": "深蓝色修身牛仔裤", "color": "深蓝色"},
                {"slot": "配饰", "description": "银色简约手表", "color": "银色"}
            ],
            "winter": [
                {"slot": "外套", "description": "黑色毛呢大衣", "color": "黑色"},
                {"slot": "上装", "description": "酒红色针织毛衣", "color": "酒红色"},
                {"slot": "下装", "description": "深灰色休闲裤", "color": "深灰色"},
                {"slot": "配饰", "description": "金色细项链", "color": "金色"}
            ]
        },
        "party": {
            "summer": [
                {"slot": "上装", "description": "黑色修身T恤", "color": "黑色"},
                {"slot": "下装", "description": "深蓝色修身牛仔裤", "color": "深蓝色"},
                {"slot": "鞋履", "description": "黑色亮面皮鞋", "color": "黑色"}
            ],
            "spring_autumn": [
                {"slot": "外套", "description": "黑色亮片小外套", "color": "黑色"},
                {"slot": "上装", "description": "深灰色高领毛衣", "color": "深灰色"},
                {"slot": "下装", "description": "黑色修身裤", "color": "黑色"},
                {"slot": "鞋履", "description": "黑色漆皮高跟鞋", "color": "黑色"}
            ],
            "winter": [
                {"slot": "外套", "description": "深蓝色双排扣大衣", "color": "深蓝色"},
                {"slot": "上装", "description": "黑色高领针织衫", "color": "黑色"},
                {"slot": "下装", "description": "深灰色呢子裤", "color": "深灰色"},
                {"slot": "配饰", "description": "银色几何耳饰", "color": "银色"}
            ]
        }
    }

    return items_by_scene.get(scene, items_by_scene["daily"]).get(temp_range, items_by_scene["daily"]["spring_autumn"])


def _generate_description(temperature: float, scene: str) -> str:
    temp_range = _get_temp_range(temperature)

    temp_desc = {
        "summer": "清爽夏季",
        "spring_autumn": "春秋时节",
        "winter": "保暖冬季"
    }
    scene_desc = {
        "daily": "休闲日常",
        "work": "职场商务",
        "sport": "运动健身",
        "date": "约会出行",
        "party": "派对聚会"
    }

    return f"{temp_desc.get(temp_range, '日常')} {scene_desc.get(scene, '穿搭')} · 约{temperature:.0f}℃"


@router.post("/generate-today", response_model=GenerateOutfitResponse)
def generate_today_outfit(request: GenerateOutfitRequest, db: Session = Depends(get_db)):
    temp_range = _get_temp_range(request.temperature)

    cached = db.query(OutfitCache).filter(
        OutfitCache.city == request.city,
        OutfitCache.temperature_range == temp_range,
        OutfitCache.scene == request.scene
    ).first()

    if cached:
        return GenerateOutfitResponse(
            description=cached.description or "",
            temperature=cached.temperature,
            city=cached.city,
            scene=cached.scene,
            image_url=cached.image_url,
            outfit_items=[OutfitItem(**item) for item in (cached.outfit_items or [])],
            cached=True
        )

    keywords = _build_search_keywords(request.temperature, request.scene)
    image_url = image_searcher.search_fashion_image(keywords)

    if not image_url:
        image_url = f"https://picsum.photos/seed/{request.city}{temp_range}{request.scene}/600/800"

    description = _generate_description(request.temperature, request.scene)
    outfit_items = _parse_outfit_items(description, request.scene)

    outfit_record = OutfitCache(
        city=request.city,
        temperature=request.temperature,
        temperature_range=temp_range,
        scene=request.scene,
        image_url=image_url,
        description=description,
        outfit_items=outfit_items
    )
    db.add(outfit_record)
    db.commit()
    db.refresh(outfit_record)

    return GenerateOutfitResponse(
        description=description,
        temperature=request.temperature,
        city=request.city,
        scene=request.scene,
        image_url=image_url,
        outfit_items=[OutfitItem(**item) for item in outfit_items],
        cached=False
    )


@router.post("/refresh", response_model=GenerateOutfitResponse)
def refresh_outfit(request: RefreshRequest, db: Session = Depends(get_db)):
    temp_range = _get_temp_range(request.temperature)

    db.query(OutfitCache).filter(
        OutfitCache.city == request.city,
        OutfitCache.temperature_range == temp_range,
        OutfitCache.scene == request.scene
    ).delete()
    db.commit()

    keywords = _build_search_keywords(request.temperature, request.scene)
    image_url = image_searcher.search_fashion_image(keywords)

    if not image_url:
        image_url = f"https://picsum.photos/seed/{request.city}{temp_range}{request.scene}/600/800"

    description = _generate_description(request.temperature, request.scene)
    outfit_items = _parse_outfit_items(description, request.scene)

    outfit_record = OutfitCache(
        city=request.city,
        temperature=request.temperature,
        temperature_range=temp_range,
        scene=request.scene,
        image_url=image_url,
        description=description,
        outfit_items=outfit_items
    )
    db.add(outfit_record)
    db.commit()
    db.refresh(outfit_record)

    return GenerateOutfitResponse(
        description=description,
        temperature=request.temperature,
        city=request.city,
        scene=request.scene,
        image_url=image_url,
        outfit_items=[OutfitItem(**item) for item in outfit_items],
        cached=False
    )


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    return FeedbackResponse(message="反馈已记录，感谢您的建议")


@router.get("/cache-status")
def cache_status(city: str, temperature: float, scene: str = "daily", db: Session = Depends(get_db)):
    temp_range = _get_temp_range(temperature)
    cached = db.query(OutfitCache).filter(
        OutfitCache.city == city,
        OutfitCache.temperature_range == temp_range,
        OutfitCache.scene == scene
    ).first()

    return {
        "cached": cached is not None,
        "city": city,
        "temperature": temperature,
        "scene": scene,
        "cache_id": cached.id if cached else None,
        "create_time": cached.create_time if cached else None
    }
