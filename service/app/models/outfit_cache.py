from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.database import Base


class OutfitCache(Base):
    __tablename__ = "outfit_cache"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    city = Column(String(64), nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    temperature_range = Column(String(32), nullable=False, index=True)
    scene = Column(String(32), nullable=False, index=True)
    image_url = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    outfit_items = Column(JSONB, nullable=True)
    create_time = Column(DateTime, default=datetime.now)
