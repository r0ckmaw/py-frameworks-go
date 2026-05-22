from datetime import date
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel


class Category(StrEnum):
    DAIRY = "Dairy"
    PRODUCE = "Produce"
    MEAT = "Meat"
    PANTRY = "Pantry"
    FROZEN = "Frozen"
    BEVERAGES = "Beverages"
    OTHER = "Other"


class InventoryItem(BaseModel):
    id: Optional[int] = None
    name: str
    quantity: float
    unit: str
    category: Category = Category.OTHER
    expiration_date: Optional[date] = None


class InventoryItemCreate(BaseModel):
    name: str
    quantity: float
    unit: str
    category: Category = Category.OTHER
    expiration_date: Optional[date] = None
