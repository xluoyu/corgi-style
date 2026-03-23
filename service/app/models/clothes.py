from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class ClothesCategory(str, enum.Enum):
    top = "top"
    pants = "pants"
    outer = "outer"
    inner = "inner"
    accessory = "accessory"


class TemperatureRange(str, enum.Enum):
    summer = "summer"
    spring_autumn = "spring_autumn"
    winter = "winter"
    all_season = "all_season"


class Scene(str, enum.Enum):
    daily = "daily"
    work = "work"
    sport = "sport"
    date = "date"
    party = "party"


class WearMethod(str, enum.Enum):
    inner_wear = "inner_wear"
    outer_wear = "outer_wear"
    single_wear = "single_wear"
    layering = "layering"


class UserClothes(Base):
    __tablename__ = "clothing_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    sub_category = Column(String(100), nullable=True)
    original_image_url = Column(String(500), nullable=False)
    cartoon_image_url = Column(String(500), nullable=True)
    color = Column(String(32), nullable=True)
    material = Column(String(64), nullable=True)
    temperature_range = Column(String(50), nullable=True)
    tags = Column(Text, nullable=False, default="{}")
    wear_count = Column(Integer, default=0)
    last_worn_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    analysis_completed = Column(Integer, default=0)
    generated_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="clothes")