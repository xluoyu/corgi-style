from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), unique=True, index=True, nullable=False)
    nickname = Column(String(64), default="匿名用户")
    gender = Column(Enum(GenderEnum), default=GenderEnum.other)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    style_preference = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    clothes = relationship("UserClothes", back_populates="user", cascade="all, delete-orphan")
    outfits = relationship("OutfitRecord", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("OutfitFeedback", back_populates="user", cascade="all, delete-orphan")

class UserPreference(Base):
    __tablename__ = "user_preference"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("user.user_id"), nullable=False, index=True)
    liked_colors = Column(Text, nullable=True)
    liked_styles = Column(Text, nullable=True)
    liked_categories = Column(Text, nullable=True)
    disliked_colors = Column(Text, nullable=True)
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)