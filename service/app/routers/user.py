from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.models import User, UserProfile

router = APIRouter(prefix="/user", tags=["user"])


class GetOrCreateUserRequest(BaseModel):
    device_fingerprint: str


class GetOrCreateUserResponse(BaseModel):
    user_id: str
    device_fingerprint: str
    message: str


class UpdateUserInfoRequest(BaseModel):
    user_id: str
    gender: Optional[str] = None
    style_preferences: Optional[str] = None
    season_preference: Optional[str] = None
    default_occasion: Optional[str] = None


class UpdateUserInfoResponse(BaseModel):
    user_id: str
    message: str


class GetPreferenceResponse(BaseModel):
    user_id: str
    gender: Optional[str]
    style_preferences: Optional[str]
    season_preference: Optional[str]
    default_occasion: Optional[str]


@router.post("/get-or-create", response_model=GetOrCreateUserResponse)
def get_or_create_user(request: GetOrCreateUserRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.device_fingerprint == request.device_fingerprint).first()
    if user:
        user.last_active_at = datetime.now()
        db.commit()
        return GetOrCreateUserResponse(
            user_id=str(user.id),
            device_fingerprint=user.device_fingerprint,
            message="用户已存在"
        )

    user = User(
        device_fingerprint=request.device_fingerprint
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = UserProfile(
        user_id=user.id,
        default_occasion="casual"
    )
    db.add(profile)
    db.commit()

    return GetOrCreateUserResponse(
        user_id=str(user.id),
        device_fingerprint=user.device_fingerprint,
        message="用户创建成功"
    )


@router.post("/update-info", response_model=UpdateUserInfoResponse)
def update_user_info(request: UpdateUserInfoRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    profile = db.query(UserProfile).filter(UserProfile.user_id == request.user_id).first()
    if not profile:
        profile = UserProfile(user_id=request.user_id)
        db.add(profile)

    if request.gender is not None:
        profile.gender = request.gender
    if request.style_preferences is not None:
        profile.style_preferences = request.style_preferences
    if request.season_preference is not None:
        profile.season_preference = request.season_preference
    if request.default_occasion is not None:
        profile.default_occasion = request.default_occasion

    db.commit()

    return UpdateUserInfoResponse(
        user_id=request.user_id,
        message="用户信息更新成功"
    )


@router.get("/preference", response_model=GetPreferenceResponse)
def get_user_preference(user_id: str, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="用户偏好不存在")

    return GetPreferenceResponse(
        user_id=str(profile.user_id),
        gender=profile.gender,
        style_preferences=profile.style_preferences,
        season_preference=profile.season_preference,
        default_occasion=profile.default_occasion
    )