from datetime import date
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Date, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Category(StrEnum):
    DAIRY = "Dairy"
    PRODUCE = "Produce"
    MEAT = "Meat"
    PANTRY = "Pantry"
    FROZEN = "Frozen"
    BEVERAGES = "Beverages"
    OTHER = "Other"


# SQLAlchemy Model
class DBInventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)
    category: Mapped[Category] = mapped_column(Enum(Category), default=Category.OTHER)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


# Pydantic Schemas
class InventoryItemBase(BaseModel):
    name: str
    quantity: float
    unit: str
    category: Category = Category.OTHER
    expiration_date: Optional[date] = None


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItem(InventoryItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
