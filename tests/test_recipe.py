import os

import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def test_recipes():
    print("Testing Recipes...")

    # 1. Create a recipe
    recipe_data = {
        "name": "Pancakes",
        "description": "Delicious breakfast pancakes",
        "ingredients": [
            {"item_name": "Milk", "quantity": 0.5, "unit": "liters"},
            {"item_name": "Eggs", "quantity": 2, "unit": "pieces"},
            {"item_name": "Flour", "quantity": 250, "unit": "grams"},
        ],
    }
    response = requests.post(f"{BASE_URL}/recipes/", json=recipe_data)
    assert response.status_code == 200
    recipe = response.json()
    recipe_id = recipe["id"]
    print(f"Created recipe '{recipe['name']}' with ID: {recipe_id}")

    # 2. Check missing ingredients (should be all of them)
    response = requests.get(f"{BASE_URL}/recipes/{recipe_id}/missing")
    assert response.status_code == 200
    missing = response.json()
    assert len(missing) == 3
    print("Verified all ingredients missing initially")

    # 3. Add some ingredients to inventory
    requests.post(
        f"{BASE_URL}/item",
        json={"name": "Milk", "quantity": 1.0, "unit": "liters", "category": "Dairy"},
    )
    requests.post(
        f"{BASE_URL}/item",
        json={"name": "Eggs", "quantity": 1, "unit": "pieces", "category": "Dairy"},
    )

    # 4. Check missing again
    response = requests.get(f"{BASE_URL}/recipes/{recipe_id}/missing")
    missing = response.json()
    # Milk should be gone (have 1.0, need 0.5)
    # Eggs should still be there (have 1, need 2)
    # Flour should still be there (have 0, need 250)
    assert len(missing) == 2
    egg_missing = next(m for m in missing if m["item_name"] == "Eggs")
    assert egg_missing["missing_quantity"] == 1.0
    print("Verified partial ingredient availability logic")

    # 5. Cook recipe (Failure expected)
    response = requests.post(f"{BASE_URL}/recipes/{recipe_id}/cook")
    assert response.status_code == 400
    assert "Insufficient ingredients" in response.json()["detail"]["message"]
    print("Verified cook recipe failure when ingredients are missing")

    # 6. Add remaining ingredients and cook (Success expected)
    requests.post(
        f"{BASE_URL}/item",
        json={"name": "Eggs", "quantity": 5, "unit": "pieces", "category": "Dairy"},
    )
    requests.post(
        f"{BASE_URL}/item",
        json={"name": "Flour", "quantity": 1000, "unit": "grams", "category": "Pantry"},
    )

    response = requests.post(f"{BASE_URL}/recipes/{recipe_id}/cook")
    assert response.status_code == 200
    assert "Successfully cooked" in response.json()["message"]
    print("Verified successful recipe cooking")

    # 7. Verify inventory deduction
    # We had 1.0 + 5.0 eggs = 6.0. Recipe used 2.0. Should have 4.0 left.
    response = requests.get(f"{BASE_URL}/items")
    items = response.json()
    total_eggs = sum(item["quantity"] for item in items if item["name"] == "Eggs")
    assert total_eggs == 4.0
    print("Verified inventory correctly deducted after cooking")


def test_recipe_search():
    print("Testing recipe search...")
    requests.post(
        f"{BASE_URL}/recipes/",
        json={
            "name": "Pepperoni Pizza",
            "description": "Classic pizza",
            "ingredients": [{"item_name": "Dough", "quantity": 1, "unit": "piece"}],
        },
    )
    requests.post(
        f"{BASE_URL}/recipes/",
        json={
            "name": "Veggie Pizza",
            "description": "Healthy pizza",
            "ingredients": [{"item_name": "Dough", "quantity": 1, "unit": "piece"}],
        },
    )

    # Search for 'pizza'
    response = requests.get(f"{BASE_URL}/recipes/", params={"q": "pizza"})
    recipes = response.json()
    assert len(recipes) == 2
    assert all("Pizza" in r["name"] for r in recipes)
    print("Verified recipe search")


if __name__ == "__main__":
    test_recipes()
    test_recipe_search()
