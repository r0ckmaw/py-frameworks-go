from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    id: Optional[int] = None
    name: str
    quantity: float
    unit: str  # e.g., "kg", "liters", "units"
    expiration_date: Optional[date] = None


class InventoryItemCreate(BaseModel):
    name: str
    quantity: float
    unit: str
    expiration_date: Optional[date] = None
