from fastapi import FastAPI

from household_manager.api.auth import router as auth_router
from household_manager.api.inventory import router as inventory_router
from household_manager.api.recipe import router as recipe_router
from household_manager.database import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Household Manager")


@app.get("/")
async def root():
    return {"message": "Welcome to the Household Manager API"}


app.include_router(auth_router)
app.include_router(inventory_router)
app.include_router(recipe_router)
