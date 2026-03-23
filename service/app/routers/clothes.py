from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import asyncio
import threading

from app.database import get_db
from app.models import UserClothes, ClothesCategory, TemperatureRange
from app.agent.clothes_agent import clothes_agent
from app.services.oss_uploader import oss_uploader

router = APIRouter(prefix="/clothes", tags=["clothes"])


class AddClothesRequest(BaseModel):
    user_id: str
    image_url: str
    category: str
    color: str
    temperature_range: str


class AddClothesResponse(BaseModel):
    clothes_id: int
    message: str


class ClothesItem(BaseModel):
    id: str
    user_id: str
    image_url: str
    category: str
    color: str
    material: Optional[str] = None
    temperature_range: str
    scene: Optional[str]
    wear_method: Optional[str]
    brand: Optional[str]
    description: Optional[str]
    generated_image_url: Optional[str]
    analysis_completed: bool
    generated_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ClothesListResponse(BaseModel):
    clothes: List[ClothesItem]
    total: int


class DeleteClothesRequest(BaseModel):
    user_id: str
    clothes_id: str


class DeleteClothesResponse(BaseModel):
    message: str


class UploadSimpleResponse(BaseModel):
    clothes_id: str
    message: str
    image_url: str


@router.post("/add", response_model=AddClothesResponse)
def add_clothes(request: AddClothesRequest, db: Session = Depends(get_db)):
    try:
        category = ClothesCategory(request.category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的类别: {request.category}")

    try:
        temperature_range = TemperatureRange(request.temperature_range)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的温度区间: {request.temperature_range}")

    clothes = UserClothes(
        user_id=request.user_id,
        original_image_url=request.image_url,
        category=category,
        color=request.color,
        temperature_range=temperature_range,
        tags="{}",
        analysis_completed=0,
        generated_completed=0
    )

    db.add(clothes)
    db.commit()
    db.refresh(clothes)

    return AddClothesResponse(
        clothes_id=clothes.id,
        message="衣服添加成功"
    )


@router.get("/list", response_model=ClothesListResponse)
def list_clothes(
    user_id: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(UserClothes).filter(UserClothes.user_id == user_id)

    if category:
        try:
            cat_enum = ClothesCategory(category)
            query = query.filter(UserClothes.category == cat_enum)
        except ValueError:
            pass

    clothes_list = query.order_by(UserClothes.created_at.desc()).all()

    return ClothesListResponse(
        clothes=[ClothesItem(
            id=str(c.id),
            user_id=str(c.user_id),
            image_url=oss_uploader.get_signed_url(c.original_image_url) if c.original_image_url else (oss_uploader.get_signed_url(c.cartoon_image_url) if c.cartoon_image_url else ""),
            category=c.category,
            color=c.color or "",
            material=c.material,
            temperature_range=c.temperature_range or "",
            scene=None,
            wear_method=None,
            brand=None,
            description=None,
            generated_image_url=oss_uploader.get_signed_url(c.cartoon_image_url) if c.cartoon_image_url else None,
            analysis_completed=c.analysis_completed == 1,
            generated_completed=c.generated_completed == 1,
            created_at=c.created_at
        ) for c in clothes_list],
        total=len(clothes_list)
    )


@router.post("/delete", response_model=DeleteClothesResponse)
def delete_clothes(request: DeleteClothesRequest, db: Session = Depends(get_db)):
    clothes = db.query(UserClothes).filter(
        UserClothes.id == request.clothes_id,
        UserClothes.user_id == request.user_id
    ).first()

    if not clothes:
        raise HTTPException(status_code=404, detail="衣服不存在或无权删除")

    db.delete(clothes)
    db.commit()

    return DeleteClothesResponse(message="衣服删除成功")


def run_clothes_agent_async(image_data: bytes, user_id: str, db_session):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(clothes_agent.run(image_data, user_id, db_session))
    except Exception as e:
        print(f"异步处理衣物失败: {e}")
    finally:
        loop.close()


@router.post("/upload", response_model=UploadSimpleResponse)
async def upload_clothes(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的 user_id 格式")

    image_data = await file.read()

    if len(image_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过10MB")

    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只能上传图片文件")

    image_path = oss_uploader.upload(image_data, user_id, sub_dir="clothes")

    clothes = UserClothes(
        user_id=user_uuid,
        original_image_url=image_path,
        category="top",
        color="识别中...",
        material="识别中...",
        temperature_range="all_season",
        tags="{}",
        analysis_completed=0,
        generated_completed=0
    )

    db.add(clothes)
    db.commit()
    db.refresh(clothes)

    def async_task():
        from app.database import SessionLocal
        new_db = SessionLocal()
        try:
            run_clothes_agent_async(image_data, user_id, new_db)
        finally:
            new_db.close()

    thread = threading.Thread(target=async_task)
    thread.daemon = True
    thread.start()

    return UploadSimpleResponse(
        clothes_id=str(clothes.id),
        message="上传成功",
        image_url=oss_uploader.get_signed_url(image_path)
    )


@router.get("/status/{clothes_id}")
def get_clothes_status(
    clothes_id: str,
    db: Session = Depends(get_db)
):
    clothes = db.query(UserClothes).filter(UserClothes.id == clothes_id).first()

    if not clothes:
        raise HTTPException(status_code=404, detail="衣服不存在")

    return {
        "clothes_id": str(clothes.id),
        "analysis_completed": clothes.analysis_completed,
        "generated_completed": clothes.generated_completed,
        "generated_image_url": oss_uploader.get_signed_url(clothes.cartoon_image_url) if clothes.cartoon_image_url else None,
        "color": clothes.color,
        "category": clothes.category,
        "material": clothes.material,
        "temperature_range": clothes.temperature_range
    }