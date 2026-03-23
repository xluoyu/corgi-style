from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.models import OutfitRecord, OutfitFeedback, UserClothes

router = APIRouter(prefix="/history", tags=["history"])


# ============ 请求/响应模型 ============

class OutfitHistoryItem(BaseModel):
    id: int
    occasion: str
    created_at: datetime
    weather_temp: Optional[float] = None
    weather_city: Optional[str] = None
    match_score: float
    clothes_count: int
    description: Optional[str] = None

    class Config:
        from_attributes = True


class OutfitHistoryDetail(BaseModel):
    id: int
    occasion: str
    created_at: datetime
    weather_temp: Optional[float] = None
    weather_city: Optional[str] = None
    match_score: float
    scheme_description: Optional[str] = None
    clothes: List[dict]

    class Config:
        from_attributes = True


class OutfitHistoryListResponse(BaseModel):
    histories: List[OutfitHistoryItem]
    total: int
    page: int
    page_size: int


class SaveOutfitSnapshotRequest(BaseModel):
    user_id: str
    occasion: str
    weather_temp: Optional[float] = None
    weather_city: Optional[str] = None


class SaveOutfitSnapshotResponse(BaseModel):
    message: str
    history_id: int


# ============ 辅助函数 ============

def get_clothes_info(clothes_id: Optional[int], db: Session) -> Optional[dict]:
    """获取衣物信息"""
    if not clothes_id:
        return None
    
    clothes = db.query(UserClothes).filter(UserClothes.id == clothes_id).first()
    if not clothes:
        return None
    
    return {
        "id": clothes.id,
        "image_url": clothes.image_url,
        "category": clothes.category.value if hasattr(clothes.category, 'value') else str(clothes.category),
        "color": clothes.color
    }


# ============ API 路由 ============

@router.get("/list", response_model=OutfitHistoryListResponse)
def list_outfit_history(
    user_id: str = Query(..., description="用户ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取用户穿搭历史列表
    
    支持按日期范围筛选
    """
    query = db.query(OutfitRecord).filter(OutfitRecord.user_id == user_id)
    
    # 日期筛选
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(OutfitRecord.create_time >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的开始日期格式，请使用 YYYY-MM-DD")
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(OutfitRecord.create_time < end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的结束日期格式，请使用 YYYY-MM-DD")
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    records = query.order_by(desc(OutfitRecord.create_time)).offset(offset).limit(page_size).all()
    
    # 转换响应
    histories = []
    for record in records:
        clothes_count = sum([
            1 if record.top_clothes_id else 0,
            1 if record.pants_clothes_id else 0,
            1 if record.outer_clothes_id else 0,
            1 if record.inner_clothes_id else 0,
            1 if record.accessory_clothes_id else 0
        ])
        
        histories.append(OutfitHistoryItem(
            id=record.id,
            occasion=record.scheme_id or "daily",  # 使用 scheme_id 作为场合标识
            created_at=record.create_time,
            weather_temp=record.weather_temp,
            weather_city=record.weather_city,
            match_score=record.match_score or 0,
            clothes_count=clothes_count,
            description=record.scheme_description
        ))
    
    return OutfitHistoryListResponse(
        histories=histories,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{history_id}", response_model=OutfitHistoryDetail)
def get_outfit_history_detail(
    history_id: int,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    获取单条穿搭历史详情
    """
    record = db.query(OutfitRecord).filter(
        OutfitRecord.id == history_id,
        OutfitRecord.user_id == user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="穿搭记录不存在")
    
    # 获取衣物详情
    clothes_list = []
    clothes_ids = [
        record.top_clothes_id,
        record.pants_clothes_id,
        record.outer_clothes_id,
        record.inner_clothes_id,
        record.accessory_clothes_id
    ]
    
    for clothes_id in clothes_ids:
        clothes_info = get_clothes_info(clothes_id, db)
        if clothes_info:
            clothes_list.append(clothes_info)
    
    return OutfitHistoryDetail(
        id=record.id,
        occasion=record.scheme_id or "daily",
        created_at=record.create_time,
        weather_temp=record.weather_temp,
        weather_city=record.weather_city,
        match_score=record.match_score or 0,
        scheme_description=record.scheme_description,
        clothes=clothes_list
    )


@router.post("/save", response_model=SaveOutfitSnapshotResponse)
def save_outfit_snapshot(
    request: SaveOutfitSnapshotRequest,
    db: Session = Depends(get_db)
):
    """
    保存穿搭快照
    
    创建一个新的穿搭记录快照
    """
    from app.agent.supervisor import Supervisor
    
    try:
        # 使用 Supervisor 生成穿搭
        supervisor = Supervisor(db)
        result = supervisor.generate_outfit(
            user_id=request.user_id,
            temperature=request.weather_temp or 20,
            city=request.weather_city or "未知",
            scene=request.occasion
        )
        
        return SaveOutfitSnapshotResponse(
            message="穿搭快照保存成功",
            history_id=result.get("outfit_id", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/stats/summary")
def get_outfit_stats_summary(
    user_id: str = Query(..., description="用户ID"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取穿搭统计摘要
    """
    start_date = datetime.now() - timedelta(days=days)
    
    records = db.query(OutfitRecord).filter(
        OutfitRecord.user_id == user_id,
        OutfitRecord.create_time >= start_date
    ).all()
    
    # 统计各场合数量
    occasion_count = {}
    total_count = len(records)
    avg_score = 0
    
    if records:
        scores = [r.match_score for r in records if r.match_score]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        for record in records:
            occasion = record.scheme_id or "daily"
            occasion_count[occasion] = occasion_count.get(occasion, 0) + 1
    
    return {
        "total_count": total_count,
        "avg_match_score": round(avg_score, 1),
        "occasion_distribution": occasion_count,
        "period_days": days
    }
