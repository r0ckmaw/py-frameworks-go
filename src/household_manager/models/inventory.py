from datetime import date
from enum import StrEnum
from typing import Optional

from sqlalchemy import Date, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from household_manager.database import Base


class Category(StrEnum):
    DAIRY = "Dairy"
    PRODUCE = "Produce"
    MEAT = "Meat"
    PANTRY = "Pantry"
    FROZEN = "Frozen"
    BEVERAGES = "Beverages"
    OTHER = "Other"


class DBInventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    quantity: Mapped[float] = mapped_column(Float)
    min_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str] = mapped_column(String)
    category: Mapped[Category] = mapped_column(Enum(Category), default=Category.OTHER)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
