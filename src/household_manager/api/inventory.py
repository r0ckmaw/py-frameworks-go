from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from household_manager.core.deps import get_current_user
from household_manager.database import get_db
from household_manager.models.inventory import Category, DBInventoryItem
from household_manager.models.user import DBUser
from household_manager.schemas.inventory import InventoryItem, InventoryItemCreate

router = APIRouter(tags=["inventory"])


@router.post("/item", response_model=InventoryItem)
async def create_item(
    item: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    """Create a single inventory item."""
    db_item = DBInventoryItem(**item.model_dump(), owner_id=current_user.id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.post("/items", response_model=List[InventoryItem])
async def create_items_batch(
    items: List[InventoryItemCreate],
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    """Create multiple items at once."""
    db_items = [
        DBInventoryItem(**item.model_dump(), owner_id=current_user.id) for item in items
    ]
    db.add_all(db_items)
    db.commit()
    for item in db_items:
        db.refresh(item)
    return db_items


@router.get("/items", response_model=List[InventoryItem])
async def get_items(
    category: Optional[Category] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    """List items, optionally filtered by category or name search."""
    query = select(DBInventoryItem).where(DBInventoryItem.owner_id == current_user.id)
    if category:
        query = query.where(DBInventoryItem.category == category)
    if q:
        query = query.where(DBInventoryItem.name.ilike(f"%{q}%"))
    result = db.execute(query)
    return result.scalars().all()


@router.get("/items/expiring", response_model=List[InventoryItem])
async def get_expiring_items(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    """Get items expiring within the next X days."""
    threshold = date.today() + timedelta(days=days)
    query = select(DBInventoryItem).where(
        DBInventoryItem.expiration_date <= threshold,
        DBInventoryItem.expiration_date >= date.today(),
        DBInventoryItem.owner_id == current_user.id,
    )
    result = db.execute(query)
    return result.scalars().all()


@router.get("/items/low-stock", response_model=List[InventoryItem])
async def get_low_stock_items(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    """Get items where quantity is below min_quantity."""
    query = select(DBInventoryItem).where(
        DBInventoryItem.quantity < DBInventoryItem.min_quantity,
        DBInventoryItem.owner_id == current_user.id,
    )
    result = db.execute(query)
    return result.scalars().all()


@router.get("/items/{item_id}", response_model=InventoryItem)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    db_item = db.get(DBInventoryItem, item_id)
    if db_item is None or db_item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.put("/items/{item_id}", response_model=InventoryItem)
async def update_item(
    item_id: int,
    updated_item: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    db_item = db.get(DBInventoryItem, item_id)
    if db_item is None or db_item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")

    item_data = updated_item.model_dump()
    for key, value in item_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    db_item = db.get(DBInventoryItem, item_id)
    if db_item is None or db_item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted"}


@router.patch("/items/{item_id}/consume", response_model=InventoryItem)
async def consume_item(
    item_id: int,
    amount: float = 1.0,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
):
    """Consume a certain amount of an item. Prevents negative quantity."""
    db_item = db.get(DBInventoryItem, item_id)
    if db_item is None or db_item.owner_id != current_user.id:
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
