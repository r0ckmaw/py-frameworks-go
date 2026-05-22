from typing import List

from fastapi import FastAPI, HTTPException

from models import InventoryItem, InventoryItemCreate

app = FastAPI(title="Household Manager")

# In-memory storage for demonstration
inventory_db: List[InventoryItem] = []
id_counter = 1


@app.get("/")
async def root():
    return {"message": "Welcome to the Household Manager API"}


@app.post("/items/", response_model=InventoryItem)
async def create_item(item: InventoryItemCreate):
    global id_counter
    new_item = InventoryItem(id=id_counter, **item.model_dump())
    inventory_db.append(new_item)
    id_counter += 1
    return new_item


@app.get("/items/", response_model=List[InventoryItem])
async def get_items():
    return inventory_db


@app.get("/items/{item_id}", response_model=InventoryItem)
async def get_item(item_id: int):
    for item in inventory_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.put("/items/{item_id}", response_model=InventoryItem)
async def update_item(item_id: int, updated_item: InventoryItemCreate):
    for i, item in enumerate(inventory_db):
        if item.id == item_id:
            inventory_db[i] = InventoryItem(id=item_id, **updated_item.model_dump())
            return inventory_db[i]
    raise HTTPException(status_code=404, detail="Item not found")


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(inventory_db):
        if item.id == item_id:
            del inventory_db[i]
            return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")
