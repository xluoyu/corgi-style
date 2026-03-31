from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from app.database import get_db
from app.models import User, UserProfile, UserClothes, OutfitRecord

router = APIRouter(prefix="/user", tags=["user"])

# 默认头像（avataaars.json boys 第一条）
DEFAULT_AVATAR_URL = (
    "https://avataaars.io/?avatarStyle=Circle&topType=ShortHairShortCurly"
    "&accessoriesType=Blank&hairColor=Black&facialHairType=Blank"
    "&clotheType=Hoodie&clotheColor=Black&eyeType=Happy"
    "&eyebrowType=DefaultNatural&mouthType=Smile&skinColor=Yellow"
)


class GetOrCreateUserRequest(BaseModel):
    device_fingerprint: str


class GetOrCreateUserResponse(BaseModel):
    user_id: str
    device_fingerprint: str
    nickname: str
    avatar_url: str
    height: Optional[int] = None
    weight: Optional[int] = None
    message: str


class UpdateUserInfoRequest(BaseModel):
    user_id: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[str] = None
    style_preferences: Optional[List[str]] = None
    default_occasion: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None


class UpdateUserInfoResponse(BaseModel):
    user_id: str
    message: str


class GetPreferenceResponse(BaseModel):
    user_id: str
    gender: Optional[str]
    style_preferences: Optional[List[str]]
    default_occasion: Optional[str]


class UserProfileResponse(BaseModel):
    user_id: str
    device_fingerprint: str
    nickname: str
    avatar_url: str
    gender: Optional[str]
    style_preferences: Optional[List[str]]
    default_occasion: str
    height: Optional[int]
    weight: Optional[int]
    clothes_count: int
    outfit_count: int
    created_at: str


@router.post("/get-or-create", response_model=GetOrCreateUserResponse)
def get_or_create_user(request: GetOrCreateUserRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.device_fingerprint == request.device_fingerprint).first()
    if user:
        user.last_active_at = datetime.now()
        db.commit()
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        return GetOrCreateUserResponse(
            user_id=str(user.id),
            device_fingerprint=user.device_fingerprint,
            nickname=profile.nickname if profile else "时尚路人甲",
            avatar_url=profile.avatar_url if profile else DEFAULT_AVATAR_URL,
            height=profile.height if profile else None,
            weight=profile.weight if profile else None,
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
        nickname="时尚路人甲",
        avatar_url=DEFAULT_AVATAR_URL,
        default_occasion="casual"
    )
    db.add(profile)
    db.commit()

    return GetOrCreateUserResponse(
        user_id=str(user.id),
        device_fingerprint=user.device_fingerprint,
        nickname="时尚路人甲",
        avatar_url=DEFAULT_AVATAR_URL,
        height=None,
        weight=None,
        message="用户创建成功"
    )


@router.post("/update-info", response_model=UpdateUserInfoResponse)
def update_user_info(request: UpdateUserInfoRequest, db: Session = Depends(get_db)):
    try:
        user_uuid = uuid.UUID(request.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用户ID")
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()
    if not profile:
        profile = UserProfile(user_id=user_uuid)
        db.add(profile)

    if request.nickname is not None:
        profile.nickname = request.nickname
    if request.avatar_url is not None:
        profile.avatar_url = request.avatar_url
    if request.gender is not None:
        profile.gender = request.gender
    if request.style_preferences is not None:
        profile.style_preferences = request.style_preferences
    if request.default_occasion is not None:
        profile.default_occasion = request.default_occasion
    if request.height is not None:
        profile.height = request.height
    if request.weight is not None:
        profile.weight = request.weight

    db.commit()

    return UpdateUserInfoResponse(
        user_id=request.user_id,
        message="用户信息更新成功"
    )


@router.get("/preference", response_model=GetPreferenceResponse)
def get_user_preference(user_id: str, db: Session = Depends(get_db)):
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用户ID")
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()
    if not profile:
        raise HTTPException(status_code=404, detail="用户偏好不存在")

    return GetPreferenceResponse(
        user_id=str(profile.user_id),
        gender=profile.gender,
        style_preferences=profile.style_preferences,
        default_occasion=profile.default_occasion
    )


@router.get("/profile", response_model=UserProfileResponse)
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """获取用户完整资料（含统计数据）"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的用户ID")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_uuid).first()

    clothes_count = db.query(UserClothes).filter(
        UserClothes.user_id == user_uuid,
        UserClothes.is_deleted == False  # type: ignore
    ).count()

    outfit_count = db.query(OutfitRecord).filter(OutfitRecord.user_id == user_uuid).count()

    return UserProfileResponse(
        user_id=str(user.id),
        device_fingerprint=user.device_fingerprint,
        nickname=profile.nickname if profile and profile.nickname else "时尚路人甲",
        avatar_url=profile.avatar_url if profile and profile.avatar_url else DEFAULT_AVATAR_URL,
        gender=profile.gender if profile else None,
        style_preferences=profile.style_preferences if profile else None,
        default_occasion=profile.default_occasion if profile else "casual",
        height=profile.height if profile else None,
        weight=profile.weight if profile else None,
        clothes_count=clothes_count,
        outfit_count=outfit_count,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )