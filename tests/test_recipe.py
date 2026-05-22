import os

import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def auth_headers(username: str = "recipe_user", password: str = "demo123") -> dict:
    login = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password},
    )

    if login.status_code != 200:
        register = requests.post(
            f"{BASE_URL}/auth/register",
            json={"username": username, "password": password},
        )
        assert register.status_code in (200, 400), register.text
        login = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
        )

    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_recipes():
    print("Testing Recipes...")
    headers = auth_headers("recipe_flow_user")

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
    response = requests.post(f"{BASE_URL}/recipes/", json=recipe_data, headers=headers)
    assert response.status_code == 200
    recipe = response.json()
    recipe_id = recipe["id"]
    print(f"Created recipe '{recipe['name']}' with ID: {recipe_id}")

    # 2. Check missing ingredients (should be all of them)
    response = requests.get(f"{BASE_URL}/recipes/{recipe_id}/missing", headers=headers)
    assert response.status_code == 200
    missing = response.json()
    assert len(missing) == 3
    print("Verified all ingredients missing initially")

    # 3. Add some ingredients to inventory
    requests.post(
        f"{BASE_URL}/item",
        json={"name": "Milk", "quantity": 1.0, "unit": "liters", "category": "Dairy"},
        headers=headers,
    )
    requests.post(
        f"{BASE_URL}/item",
        json={"name": "Eggs", "quantity": 1, "unit": "pieces", "category": "Dairy"},
        headers=headers,
    )

    # 4. Check missing again
    response = requests.get(f"{BASE_URL}/recipes/{recipe_id}/missing", headers=headers)
    missing = response.json()
    assert len(missing) == 2
    egg_missing = next(m for m in missing if m["item_name"] == "Eggs")
    assert egg_missing["missing_quantity"] == 1.0
    print("Verified partial ingredient availability logic")

    # 5. Cook recipe (Failure expected)
    response = requests.post(f"{BASE_URL}/recipes/{recipe_id}/cook", headers=headers)
    assert response.status_code == 400
    assert "Insufficient ingredients" in response.json()["detail"]["message"]
    print("Verified cook recipe failure when ingredients are missing")

    # 6. Add remaining ingredients and cook (Success expected)
    requests.post(
        f"{BASE_URL}/item",
        json={"name": "Eggs", "quantity": 5, "unit": "pieces", "category": "Dairy"},
        headers=headers,
    )
    requests.post(
        f"{BASE_URL}/item",
        json={"name": "Flour", "quantity": 1000, "unit": "grams", "category": "Pantry"},
        headers=headers,
    )

    response = requests.post(f"{BASE_URL}/recipes/{recipe_id}/cook", headers=headers)
    assert response.status_code == 200
    assert "Successfully cooked" in response.json()["message"]
    print("Verified successful recipe cooking")

    # 7. Verify inventory deduction
    response = requests.get(f"{BASE_URL}/items", headers=headers)
    items = response.json()
    total_eggs = sum(item["quantity"] for item in items if item["name"] == "Eggs")
    assert total_eggs == 4.0
    print("Verified inventory correctly deducted after cooking")


def test_recipe_search():
    print("Testing recipe search...")
    headers = auth_headers("recipe_search_user")

    requests.post(
        f"{BASE_URL}/recipes/",
        json={
            "name": "Pepperoni Pizza",
            "description": "Classic pizza",
            "ingredients": [{"item_name": "Dough", "quantity": 1, "unit": "piece"}],
        },
        headers=headers,
    )
    requests.post(
        f"{BASE_URL}/recipes/",
        json={
            "name": "Veggie Pizza",
            "description": "Healthy pizza",
            "ingredients": [{"item_name": "Dough", "quantity": 1, "unit": "piece"}],
        },
        headers=headers,
    )

    response = requests.get(
        f"{BASE_URL}/recipes/", params={"q": "pizza"}, headers=headers
    )
    recipes = response.json()
    assert len(recipes) == 2
    assert all("Pizza" in r["name"] for r in recipes)
    print("Verified recipe search")


def test_recipe_categories():
    print("Testing recipe categories...")
    headers = auth_headers("recipe_cat_user")

    requests.post(
        f"{BASE_URL}/recipes/",
        json={
            "name": "Oatmeal",
            "category": "Breakfast",
            "ingredients": [{"item_name": "Oats", "quantity": 50, "unit": "grams"}],
        },
        headers=headers,
    )
    requests.post(
        f"{BASE_URL}/recipes/",
        json={
            "name": "Salad",
            "category": "Lunch",
            "ingredients": [{"item_name": "Lettuce", "quantity": 1, "unit": "head"}],
        },
        headers=headers,
    )

    response = requests.get(
        f"{BASE_URL}/recipes/", params={"category": "Breakfast"}, headers=headers
    )
    recipes = response.json()
    assert any(r["name"] == "Oatmeal" for r in recipes)
    assert all(r["category"] == "Breakfast" for r in recipes)
    print("Verified recipe category filtering")


def test_shopping_list():
    print("Testing shopping list generation...")
    headers = auth_headers("shopping_user")

    r1 = requests.post(
        f"{BASE_URL}/recipes/",
        json={
            "name": "Tea",
            "ingredients": [
                {"item_name": "Water", "quantity": 0.3, "unit": "liters"},
                {"item_name": "Tea Bag", "quantity": 1, "unit": "piece"},
            ],
        },
        headers=headers,
    ).json()

    r2 = requests.post(
        f"{BASE_URL}/recipes/",
        json={
            "name": "Coffee",
            "ingredients": [
                {"item_name": "Water", "quantity": 0.2, "unit": "liters"},
                {"item_name": "Coffee Beans", "quantity": 15, "unit": "grams"},
            ],
        },
        headers=headers,
    ).json()

    requests.post(
        f"{BASE_URL}/item",
        json={"name": "Water", "quantity": 0.1, "unit": "liters"},
        headers=headers,
    )

    response = requests.post(
        f"{BASE_URL}/recipes/shopping-list",
        json={"recipe_ids": [r1["id"], r2["id"]]},
        headers=headers,
    )
    assert response.status_code == 200
    shopping_list = response.json()

    assert len(shopping_list) == 3
    water = next(item for item in shopping_list if item["item_name"] == "Water")
    assert water["quantity_to_buy"] == 0.4
    print("Verified shopping list aggregation and inventory deduction")


def test_user_isolation_recipe():
    print("Testing recipe user isolation...")
    headers_a = auth_headers("recipe_iso_a")
    headers_b = auth_headers("recipe_iso_b")

    r = requests.post(
        f"{BASE_URL}/recipes/",
        json={
            "name": "Secret Recipe",
            "ingredients": [{"item_name": "Salt", "quantity": 1, "unit": "tsp"}],
        },
        headers=headers_a,
    )
    assert r.status_code == 200
    recipe_id = r.json()["id"]

    list_b = requests.get(f"{BASE_URL}/recipes/", headers=headers_b)
    assert list_b.status_code == 200
    assert all(recipe["id"] != recipe_id for recipe in list_b.json())

    get_b = requests.get(f"{BASE_URL}/recipes/{recipe_id}", headers=headers_b)
    assert get_b.status_code == 404
    print("Verified recipe isolation")


def test_same_recipe_name_different_users():
    print("Testing same recipe name allowed for different users...")
    headers_a = auth_headers("dupe_user_a")
    headers_b = auth_headers("dupe_user_b")

    payload = {
        "name": "Shared Name",
        "ingredients": [{"item_name": "Flour", "quantity": 100, "unit": "grams"}],
    }

    r1 = requests.post(f"{BASE_URL}/recipes/", json=payload, headers=headers_a)
    r2 = requests.post(f"{BASE_URL}/recipes/", json=payload, headers=headers_b)

    assert r1.status_code == 200
    assert r2.status_code == 200
    print("Verified per-user recipe name uniqueness")


if __name__ == "__main__":
    test_recipes()
    test_recipe_search()
    test_recipe_categories()
    test_shopping_list()
    test_user_isolation_recipe()
    test_same_recipe_name_different_users()
