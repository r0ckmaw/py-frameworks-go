from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from household_manager.database import get_db
from household_manager.models.inventory import Category, DBInventoryItem
from household_manager.schemas.inventory import InventoryItem, InventoryItemCreate

router = APIRouter(prefix="/items", tags=["inventory"])


@router.post("/", response_model=InventoryItem)
async def create_item(item: InventoryItemCreate, db: Session = Depends(get_db)):
    db_item = DBInventoryItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/", response_model=List[InventoryItem])
async def get_items(category: Optional[Category] = None, db: Session = Depends(get_db)):
    query = select(DBInventoryItem)
    if category:
        query = query.where(DBInventoryItem.category == category)
    result = db.execute(query)
    return result.scalars().all()


@router.get("/expiring", response_model=List[InventoryItem])
async def get_expiring_items(days: int = 7, db: Session = Depends(get_db)):
    """Get items expiring within the next X days."""
    threshold = date.today() + timedelta(days=days)
    query = select(DBInventoryItem).where(
        DBInventoryItem.expiration_date <= threshold,
        DBInventoryItem.expiration_date >= date.today(),
    )
    result = db.execute(query)
    return result.scalars().all()


@router.get("/low-stock", response_model=List[InventoryItem])
async def get_low_stock_items(db: Session = Depends(get_db)):
    """Get items where quantity is below min_quantity."""
    query = select(DBInventoryItem).where(
        DBInventoryItem.quantity < DBInventoryItem.min_quantity
    )
    result = db.execute(query)
    return result.scalars().all()


@router.post("/batch", response_model=List[InventoryItem])
async def create_items_batch(
    items: List[InventoryItemCreate], db: Session = Depends(get_db)
):
    """Create multiple items at once."""
    db_items = [DBInventoryItem(**item.model_dump()) for item in items]
    db.add_all(db_items)
    db.commit()
    for item in db_items:
        db.refresh(item)
    return db_items


@router.patch("/{item_id}/consume", response_model=InventoryItem)
async def consume_item(
    item_id: int, amount: float = 1.0, db: Session = Depends(get_db)
):
    """Consume a certain amount of an item. Prevents negative quantity."""
    db_item = db.get(DBInventoryItem, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if db_item.quantity < amount:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough quantity. Available: {db_item.quantity}, Requested: {amount}",
        )

    db_item.quantity -= amount
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/{item_id}", response_model=InventoryItem)
async def get_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.get(DBInventoryItem, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.put("/{item_id}", response_model=InventoryItem)
async def update_item(
    item_id: int, updated_item: InventoryItemCreate, db: Session = Depends(get_db)
):
    db_item = db.get(DBInventoryItem, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    item_data = updated_item.model_dump()
    for key, value in item_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.get(DBInventoryItem, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted"}
