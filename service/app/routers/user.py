from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid

from app.database import get_db
from app.models import User, UserPreference, GenderEnum

router = APIRouter(prefix="/user", tags=["user"])

class GetOrCreateUserRequest(BaseModel):
    device_id: Optional[str] = None
    nickname: Optional[str] = None

class GetOrCreateUserResponse(BaseModel):
    user_id: str
    nickname: str
    message: str

class UpdateUserInfoRequest(BaseModel):
    user_id: str
    nickname: Optional[str] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    style_preference: Optional[str] = None

class UpdateUserInfoResponse(BaseModel):
    user_id: str
    message: str

class GetPreferenceResponse(BaseModel):
    user_id: str
    liked_colors: Optional[str]
    liked_styles: Optional[str]
    liked_categories: Optional[str]
    disliked_colors: Optional[str]
    temperature_min: Optional[float]
    temperature_max: Optional[float]

@router.post("/get-or-create", response_model=GetOrCreateUserResponse)
def get_or_create_user(request: GetOrCreateUserRequest, db: Session = Depends(get_db)):
    if request.device_id:
        user = db.query(User).filter(User.user_id == request.device_id).first()
        if user:
            return GetOrCreateUserResponse(
                user_id=user.user_id,
                nickname=user.nickname,
                message="用户已存在"
            )

    user_id = request.device_id or str(uuid.uuidint())
    nickname = request.nickname or "匿名用户"

    user = User(
        user_id=user_id,
        nickname=nickname
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    preference = UserPreference(
        user_id=user_id,
        liked_colors="",
        liked_styles="",
        liked_categories="",
        disliked_colors=""
    )
    db.add(preference)
    db.commit()

    return GetOrCreateUserResponse(
        user_id=user.user_id,
        nickname=user.nickname,
        message="用户创建成功"
    )

@router.post("/update-info", response_model=UpdateUserInfoResponse)
def update_user_info(request: UpdateUserInfoRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if request.nickname is not None:
        user.nickname = request.nickname
    if request.gender is not None:
        try:
            user.gender = GenderEnum(request.gender)
        except ValueError:
            user.gender = GenderEnum.other
    if request.height is not None:
        user.height = request.height
    if request.weight is not None:
        user.weight = request.weight
    if request.style_preference is not None:
        user.style_preference = request.style_preference

    db.commit()
    db.refresh(user)

    return UpdateUserInfoResponse(
        user_id=user.user_id,
        message="用户信息更新成功"
    )

@router.get("/preference", response_model=GetPreferenceResponse)
def get_user_preference(user_id: str, db: Session = Depends(get_db)):
    preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not preference:
        raise HTTPException(status_code=404, detail="用户偏好不存在")

    return GetPreferenceResponse(
        user_id=preference.user_id,
        liked_colors=preference.liked_colors,
        liked_styles=preference.liked_styles,
        liked_categories=preference.liked_categories,
        disliked_colors=preference.disliked_colors,
        temperature_min=preference.temperature_min,
        temperature_max=preference.temperature_max
    )