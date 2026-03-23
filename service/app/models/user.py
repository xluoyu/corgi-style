from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_fingerprint = Column(String(255), unique=True, nullable=False, index=True)
    last_active_at = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    clothes = relationship("UserClothes", back_populates="user", cascade="all, delete-orphan")
    outfits = relationship("OutfitRecord", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("OutfitFeedback", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    gender = Column(String(20), nullable=True)
    style_preferences = Column(String, nullable=True)
    season_preference = Column(String, nullable=True)
    default_occasion = Column(String(50), default="casual")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="profile")