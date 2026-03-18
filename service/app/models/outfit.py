from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class OutfitRecord(Base):
    __tablename__ = "outfit_record"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("user.user_id"), nullable=False, index=True)
    scheme_id = Column(String(32), nullable=False)
    weather_temp = Column(Float, nullable=True)
    weather_city = Column(String(64), nullable=True)
    top_clothes_id = Column(Integer, ForeignKey("user_clothes.id"), nullable=True)
    pants_clothes_id = Column(Integer, ForeignKey("user_clothes.id"), nullable=True)
    outer_clothes_id = Column(Integer, ForeignKey("user_clothes.id"), nullable=True)
    inner_clothes_id = Column(Integer, ForeignKey("user_clothes.id"), nullable=True)
    accessory_clothes_id = Column(Integer, ForeignKey("user_clothes.id"), nullable=True)
    scheme_description = Column(Text, nullable=True)
    match_score = Column(Float, default=0.0)
    create_time = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="outfits")
    top_clothes = relationship("UserClothes", foreign_keys=[top_clothes_id])
    pants_clothes = relationship("UserClothes", foreign_keys=[pants_clothes_id])
    outer_clothes = relationship("UserClothes", foreign_keys=[outer_clothes_id])
    inner_clothes = relationship("UserClothes", foreign_keys=[inner_clothes_id])
    accessory_clothes = relationship("UserClothes", foreign_keys=[accessory_clothes_id])

class OutfitFeedback(Base):
    __tablename__ = "outfit_feedback"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("user.user_id"), nullable=False, index=True)
    outfit_id = Column(Integer, ForeignKey("outfit_record.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    feedback_text = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="feedback")
    outfit = relationship("OutfitRecord")