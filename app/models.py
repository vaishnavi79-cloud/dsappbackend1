# backend/app/models.py
from sqlalchemy import Column, Integer, String, Float, Date
from .database import Base

class FoodEntry(Base):
    __tablename__ = "food_entries"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    item_name = Column(String, index=True)
    prepared_qty = Column(Float, default=0.0)
    consumed_qty = Column(Float, default=0.0)
    wastage = Column(Float, default=0.0)
