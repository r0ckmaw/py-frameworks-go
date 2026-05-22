from enum import StrEnum
from typing import List

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from household_manager.database import Base


class RecipeCategory(StrEnum):
    BREAKFAST = "Breakfast"
    LUNCH = "Lunch"
    DINNER = "Dinner"
    SNACK = "Snack"
    DESSERT = "Dessert"
    BEVERAGE = "Beverage"
    OTHER = "Other"


class DBRecipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_recipe_owner_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    category: Mapped[RecipeCategory] = mapped_column(
        Enum(RecipeCategory), default=RecipeCategory.OTHER
    )
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)

    # Relationship to ingredients
    ingredients: Mapped[List["DBRecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class DBRecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipes.id"))

    item_name: Mapped[str] = mapped_column(
        String
    )  # We link by name to allow flexibility
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)

    recipe: Mapped["DBRecipe"] = relationship(back_populates="ingredients")
