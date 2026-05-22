from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from household_manager.database import get_db
from household_manager.models.inventory import DBInventoryItem
from household_manager.models.recipe import DBRecipe, DBRecipeIngredient
from household_manager.schemas.recipe import MissingIngredient, Recipe, RecipeCreate

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post("/", response_model=Recipe)
async def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
    # Check if recipe already exists
    existing = db.execute(
        select(DBRecipe).where(DBRecipe.name == recipe.name)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Recipe already exists")

    db_recipe = DBRecipe(name=recipe.name, description=recipe.description)
    db.add(db_recipe)
    db.flush()  # Get the ID

    for ing in recipe.ingredients:
        db_ing = DBRecipeIngredient(
            recipe_id=db_recipe.id,
            item_name=ing.item_name,
            quantity=ing.quantity,
            unit=ing.unit,
        )
        db.add(db_ing)

    db.commit()
    db.refresh(db_recipe)
    return db_recipe


@router.get("/", response_model=List[Recipe])
async def get_recipes(q: Optional[str] = None, db: Session = Depends(get_db)):
    """List recipes, optionally filtered by name search."""
    query = select(DBRecipe)
    if q:
        query = query.where(DBRecipe.name.ilike(f"%{q}%"))
    result = db.execute(query)
    return result.scalars().all()


@router.get("/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    db_recipe = db.get(DBRecipe, recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return db_recipe


@router.get("/{recipe_id}/missing", response_model=List[MissingIngredient])
async def get_missing_ingredients(recipe_id: int, db: Session = Depends(get_db)):
    """Calculate what ingredients are missing for a specific recipe."""
    db_recipe = db.get(DBRecipe, recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    missing = []
    for ing in db_recipe.ingredients:
        # Sum up all available items with this name in inventory
        total_available = (
            db.execute(
                select(func.sum(DBInventoryItem.quantity)).where(
                    DBInventoryItem.name == ing.item_name
                )
            ).scalar()
            or 0.0
        )

        if total_available < ing.quantity:
            missing.append(
                MissingIngredient(
                    item_name=ing.item_name,
                    required_quantity=ing.quantity,
                    available_quantity=total_available,
                    unit=ing.unit,
                    missing_quantity=ing.quantity - total_available,
                )
            )

    return missing


@router.post("/{recipe_id}/cook", response_model=dict)
async def cook_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """
    Cook a recipe: deduct ingredients from inventory.
    Uses FEFO (First Expiring, First Out) logic.
    """
    db_recipe = db.get(DBRecipe, recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # 1. Validation: Check if we have enough of everything first
    missing = await get_missing_ingredients(recipe_id, db)
    if missing:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Insufficient ingredients to cook this recipe",
                "missing": [m.model_dump() for m in missing],
            },
        )

    # 2. Consumption: Deduct from inventory using FEFO
    for ing in db_recipe.ingredients:
        remaining_to_deduct = ing.quantity

        # Get all inventory items for this ingredient name,
        # ordered by expiration date (Nulls last)
        items_query = (
            select(DBInventoryItem)
            .where(DBInventoryItem.name == ing.item_name)
            .order_by(DBInventoryItem.expiration_date.asc().nulls_last())
        )
        inventory_items = db.execute(items_query).scalars().all()

        for item in inventory_items:
            if remaining_to_deduct <= 0:
                break

            if item.quantity <= remaining_to_deduct:
                # Use up the whole item
                remaining_to_deduct -= item.quantity
                db.delete(item)
            else:
                # Use part of the item
                item.quantity -= remaining_to_deduct
                remaining_to_deduct = 0

    db.commit()
    return {"message": f"Successfully cooked {db_recipe.name}!"}
