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
