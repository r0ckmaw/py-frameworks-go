from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Category, DBInventoryItem, InventoryItem, InventoryItemCreate

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Household Manager")


@app.get("/")
async def root():
    return {"message": "Welcome to the Household Manager API"}


@app.post("/items/", response_model=InventoryItem)
async def create_item(item: InventoryItemCreate, db: Session = Depends(get_db)):
    db_item = DBInventoryItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/items/", response_model=List[InventoryItem])
async def get_items(category: Optional[Category] = None, db: Session = Depends(get_db)):
    query = select(DBInventoryItem)
    if category:
        query = query.where(DBInventoryItem.category == category)
    result = db.execute(query)
    return result.scalars().all()


@app.get("/items/{item_id}", response_model=InventoryItem)
async def get_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.get(DBInventoryItem, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.put("/items/{item_id}", response_model=InventoryItem)
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


@app.delete("/items/{item_id}")
async def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.get(DBInventoryItem, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted"}
