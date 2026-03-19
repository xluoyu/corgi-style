from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
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
    __tablename__ = "user_clothes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("user.user_id"), nullable=False, index=True)
    image_url = Column(String(512), nullable=False)
    category = Column(Enum(ClothesCategory), nullable=False)
    color = Column(String(32), nullable=False)
    material = Column(String(64), nullable=True)
    temperature_range = Column(Enum(TemperatureRange), nullable=False)
    scene = Column(Enum(Scene), nullable=True)
    wear_method = Column(Enum(WearMethod), nullable=True)
    brand = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    generated_image_url = Column(String(512), nullable=True)
    analysis_completed = Column(Boolean, default=False)
    generated_completed = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="clothes")
