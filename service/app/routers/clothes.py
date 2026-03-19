from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import UserClothes, ClothesCategory, TemperatureRange, Scene, WearMethod
from app.agent.clothes_agent import clothes_agent

router = APIRouter(prefix="/clothes", tags=["clothes"])


class AddClothesRequest(BaseModel):
    user_id: str
    image_url: str
    category: str
    color: str
    temperature_range: str
    scene: Optional[str] = None
    wear_method: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None


class AddClothesResponse(BaseModel):
    clothes_id: int
    message: str


class ClothesItem(BaseModel):
    id: int
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
    create_time: datetime

    class Config:
        from_attributes = True


class ClothesListResponse(BaseModel):
    clothes: List[ClothesItem]
    total: int


class DeleteClothesRequest(BaseModel):
    user_id: str
    clothes_id: int


class DeleteClothesResponse(BaseModel):
    message: str


class UploadClothesResponse(BaseModel):
    clothes_id: int
    message: str
    image_url: str
    generated_image_url: Optional[str]
    color: Optional[str]
    category: Optional[str]
    material: Optional[str]
    temperature_range: Optional[str]
    wear_method: Optional[str]
    scene: Optional[str]
    completed_tasks: List[str]


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

    scene = None
    if request.scene:
        try:
            scene = Scene(request.scene)
        except ValueError:
            scene = None

    wear_method = None
    if request.wear_method:
        try:
            wear_method = WearMethod(request.wear_method)
        except ValueError:
            wear_method = None

    clothes = UserClothes(
        user_id=request.user_id,
        image_url=request.image_url,
        category=category,
        color=request.color,
        temperature_range=temperature_range,
        scene=scene,
        wear_method=wear_method,
        brand=request.brand,
        description=request.description
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

    clothes_list = query.order_by(UserClothes.create_time.desc()).all()

    return ClothesListResponse(
        clothes=[ClothesItem(
            id=c.id,
            user_id=c.user_id,
            image_url=c.image_url,
            category=c.category.value if hasattr(c.category, 'value') else c.category,
            color=c.color,
            material=c.material,
            temperature_range=c.temperature_range.value if hasattr(c.temperature_range, 'value') else c.temperature_range,
            scene=c.scene.value if c.scene and hasattr(c.scene, 'value') else c.scene,
            wear_method=c.wear_method.value if c.wear_method and hasattr(c.wear_method, 'value') else c.wear_method,
            brand=c.brand,
            description=c.description,
            generated_image_url=c.generated_image_url,
            analysis_completed=c.analysis_completed,
            generated_completed=c.generated_completed,
            create_time=c.create_time
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


@router.post("/upload", response_model=UploadClothesResponse)
async def upload_clothes(
    user_id: str,
    description: Optional[str] = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    image_data = await file.read()
    
    if len(image_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过10MB")
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只能上传图片文件")
    
    result = await clothes_agent.run(image_data, user_id, db)
    
    return UploadClothesResponse(
        clothes_id=result.clothes_id or 0,
        message=result.message,
        image_url=result.image_url or "",
        generated_image_url=result.generated_image_url,
        color=result.color,
        category=result.category,
        material=result.material,
        temperature_range=result.temperature_range,
        wear_method=result.wear_method,
        scene=result.scene,
        completed_tasks=result.completed_tasks
    )


@router.get("/status/{clothes_id}")
def get_clothes_status(
    clothes_id: int,
    db: Session = Depends(get_db)
):
    clothes = db.query(UserClothes).filter(UserClothes.id == clothes_id).first()
    
    if not clothes:
        raise HTTPException(status_code=404, detail="衣服不存在")
    
    return {
        "clothes_id": clothes.id,
        "analysis_completed": clothes.analysis_completed,
        "generated_completed": clothes.generated_completed,
        "generated_image_url": clothes.generated_image_url,
        "color": clothes.color,
        "category": clothes.category.value if hasattr(clothes.category, 'value') else clothes.category,
        "material": clothes.material,
        "temperature_range": clothes.temperature_range.value if hasattr(clothes.temperature_range, 'value') else clothes.temperature_range,
        "wear_method": clothes.wear_method.value if clothes.wear_method and hasattr(clothes.wear_method, 'value') else clothes.wear_method,
        "scene": clothes.scene.value if clothes.scene and hasattr(clothes.scene, 'value') else clothes.scene
    }