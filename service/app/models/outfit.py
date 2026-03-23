from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class OutfitRecord(Base):
    __tablename__ = "outfit_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    occasion = Column(String(50), nullable=False)
    outfit_name = Column(String(100), nullable=True)
    outfit_snapshot = Column(Text, nullable=True)
    weather_snapshot = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="outfits")

class OutfitFeedback(Base):
    __tablename__ = "outfit_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    outfit_id = Column(UUID(as_uuid=True), ForeignKey("outfit_histories.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    feedback_text = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="feedback")
    outfit = relationship("OutfitRecord")