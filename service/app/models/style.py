"""风格知识库模型"""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import json
from app.database import Base


class StyleKnowledge(Base):
    """风格知识库"""
    __tablename__ = "style_knowledge"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=False, default="[]")  # JSON array
    rules = Column(Text, nullable=False, default="{}")  # JSON object
    colors = Column(Text, nullable=False, default="[]")  # JSON array
    occasion = Column(String(50), nullable=True)  # 适用场合
    season = Column(String(50), nullable=True)  # 适用季节
    temperature_range = Column(String(50), nullable=True)
    is_builtin = Column(Boolean, default=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NULL 表示内置风格
    created_at = Column(String, default=datetime.now)
    updated_at = Column(String, default=datetime.now, onupdate=datetime.now)


class UserPreferences(Base):
    """用户偏好"""
    __tablename__ = "user_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    disliked_colors = Column(Text, nullable=True, default="[]")  # JSON array
    disliked_styles = Column(Text, nullable=True, default="[]")  # JSON array
    body_conditions = Column(Text, nullable=True, default="{}")  # JSON object
    shopping_budget = Column(String(50), nullable=True)  # 购物预算
    updated_at = Column(String, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", backref="preferences")
