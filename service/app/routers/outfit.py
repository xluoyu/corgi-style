from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import OutfitRecord, OutfitFeedback
from app.agent import Supervisor

router = APIRouter(prefix="/outfit", tags=["outfit"])

class GenerateOutfitRequest(BaseModel):
    user_id: str
    city: str
    scene: Optional[str] = "daily"

class ClothesInfo(BaseModel):
    slot: str
    clothes_id: int
    image_url: str
    category: str
    color: str
    description: Optional[str]

class GenerateOutfitResponse(BaseModel):
    outfit_id: int
    scheme_id: str
    description: str
    match_score: float
    temperature: float
    city: str
    scene: str
    is_perfect_match: bool
    clothes: List[ClothesInfo]
    create_time: Optional[datetime] = None

class FeedbackRequest(BaseModel):
    user_id: str
    outfit_id: int
    rating: int
    feedback_text: Optional[str] = None

class FeedbackResponse(BaseModel):
    message: str
    preference_updated: bool

@router.post("/generate-today", response_model=GenerateOutfitResponse)
def generate_today_outfit(request: GenerateOutfitRequest, db: Session = Depends(get_db)):
    temperature = get_weather(request.city)

    supervisor = Supervisor(db)

    result = supervisor.generate_outfit(
        user_id=request.user_id,
        temperature=temperature,
        city=request.city,
        scene=request.scene
    )

    outfit = db.query(OutfitRecord).filter(OutfitRecord.id == result["outfit_id"]).first()

    return GenerateOutfitResponse(
        outfit_id=result["outfit_id"],
        scheme_id=result["scheme_id"],
        description=result["description"],
        match_score=result["match_score"],
        temperature=result["temperature"],
        city=result["city"],
        scene=result["scene"],
        is_perfect_match=result["is_perfect_match"],
        clothes=[ClothesInfo(**c) for c in result["clothes"]],
        create_time=outfit.create_time if outfit else None
    )

@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    if request.rating < 1 or request.rating > 5:
        raise HTTPException(status_code=400, detail="评分必须在1-5之间")

    outfit = db.query(OutfitRecord).filter(
        OutfitRecord.id == request.outfit_id,
        OutfitRecord.user_id == request.user_id
    ).first()

    if not outfit:
        raise HTTPException(status_code=404, detail="穿搭记录不存在")

    feedback = OutfitFeedback(
        user_id=request.user_id,
        outfit_id=request.outfit_id,
        rating=request.rating,
        feedback_text=request.feedback_text
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    update_preference(db, request.user_id, {
        "rating": request.rating,
        "outfit_id": request.outfit_id,
        "feedback_text": request.feedback_text
    })

    return FeedbackResponse(
        message="反馈已保存",
        preference_updated=True
    )

def get_weather(city: str) -> float:
    weather_map = {
        "北京": 15.0,
        "上海": 18.0,
        "广州": 25.0,
        "深圳": 26.0,
        "杭州": 17.0,
        "成都": 16.0,
        "武汉": 14.0,
        "西安": 13.0,
        "南京": 16.0,
        "重庆": 20.0
    }

    base_temp = weather_map.get(city, 20.0)
    import random
    return base_temp + random.uniform(-3, 3)

def update_preference(db: Session, user_id: str, feedback_data: dict):
    from app.models import UserPreference

    preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not preference:
        return False

    outfit = db.query(OutfitRecord).filter(OutfitRecord.id == feedback_data["outfit_id"]).first()
    if not outfit:
        return False

    if feedback_data["rating"] >= 4:
        from app.models import UserClothes
        liked_categories = []

        if outfit.top_clothes_id:
            clothes = db.query(UserClothes).filter(UserClothes.id == outfit.top_clothes_id).first()
            if clothes:
                liked_categories.append(clothes.category.value)

        current_categories = preference.liked_categories or ""
        if liked_categories and liked_categories[0] not in current_categories:
            preference.liked_categories = current_categories + "," + liked_categories[0] if current_categories else liked_categories[0]

        if outfit.weather_temp:
            if preference.temperature_min is None or outfit.weather_temp < preference.temperature_min:
                preference.temperature_min = outfit.weather_temp - 5
            if preference.temperature_max is None or outfit.weather_temp > preference.temperature_max:
                preference.temperature_max = outfit.weather_temp + 5

    db.commit()
    return True