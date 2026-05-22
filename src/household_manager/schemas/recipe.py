from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class RecipeIngredientBase(BaseModel):
    item_name: str
    quantity: float
    unit: str


class RecipeIngredientCreate(RecipeIngredientBase):
    pass


class RecipeIngredient(RecipeIngredientBase):
    id: int
    recipe_id: int
    model_config = ConfigDict(from_attributes=True)


class RecipeBase(BaseModel):
    name: str
    description: Optional[str] = None


class RecipeCreate(RecipeBase):
    ingredients: List[RecipeIngredientCreate]


class Recipe(RecipeBase):
    id: int
    ingredients: List[RecipeIngredient]
    model_config = ConfigDict(from_attributes=True)

    ingredients: List[RecipeIngredient]
    model_config = ConfigDict(from_attributes=True)


class MissingIngredient(BaseModel):
    item_name: str
    required_quantity: float
    available_quantity: float
    unit: str
    missing_quantity: float
