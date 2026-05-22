from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from household_manager.models.inventory import Category


class InventoryItemBase(BaseModel):
    name: str
    quantity: float
    min_quantity: float = 0.0
    unit: str
    category: Category = Category.OTHER
    expiration_date: Optional[date] = None


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItem(InventoryItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
