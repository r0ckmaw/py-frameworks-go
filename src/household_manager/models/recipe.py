from typing import List

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from household_manager.database import Base


class DBRecipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True, unique=True)
    description: Mapped[str] = mapped_column(String, nullable=True)

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
