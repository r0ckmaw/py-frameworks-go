import os
from datetime import date, timedelta

import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def auth_headers(username: str = "api_user", password: str = "demo123") -> dict:
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


def test_crud():
    print("Testing CRUD...")
    headers = auth_headers("crud_user")

    # 1. Create an item
    item_data = {
        "name": "Milk",
        "quantity": 2.0,
        "unit": "liters",
        "category": "Dairy",
        "expiration_date": str(date.today() + timedelta(days=7)),
    }
    response = requests.post(f"{BASE_URL}/item", json=item_data, headers=headers)
    assert response.status_code == 200
    item = response.json()
    assert item["name"] == "Milk"
    assert item["category"] == "Dairy"
    item_id = item["id"]
    print(f"Created item with ID: {item_id}")

    # 2. Get all items
    response = requests.get(f"{BASE_URL}/items", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    print(f"Total items in inventory: {len(items)}")

    # 3. Get single item
    response = requests.get(f"{BASE_URL}/items/{item_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Milk"

    # 4. Update item
    update_data = item_data.copy()
    update_data["quantity"] = 1.5
    response = requests.put(
        f"{BASE_URL}/items/{item_id}", json=update_data, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["quantity"] == 1.5
    print(f"Updated item {item_id} quantity to 1.5")

    # 5. Delete item
    response = requests.delete(f"{BASE_URL}/items/{item_id}", headers=headers)
    assert response.status_code == 200
    print(f"Deleted item {item_id}")

    # 6. Verify deletion
    response = requests.get(f"{BASE_URL}/items/{item_id}", headers=headers)
    assert response.status_code == 404
    print("Verified item deletion (404)")


def test_filtering():
    print("Testing filtering...")
    headers = auth_headers("filter_user")

    # Add two items in different categories
    requests.post(
        f"{BASE_URL}/item",
        json={"name": "Apples", "quantity": 5, "unit": "pieces", "category": "Produce"},
        headers=headers,
    )
    requests.post(
        f"{BASE_URL}/item",
        json={"name": "Cheese", "quantity": 1, "unit": "block", "category": "Dairy"},
        headers=headers,
    )

    # Filter by Produce
    response = requests.get(
        f"{BASE_URL}/items", params={"category": "Produce"}, headers=headers
    )
    items = response.json()
    assert any(item["name"] == "Apples" for item in items)
    assert all(item["category"] == "Produce" for item in items)
    print("Verified Produce filtering")

    # Filter by Dairy
    response = requests.get(
        f"{BASE_URL}/items", params={"category": "Dairy"}, headers=headers
    )
    items = response.json()
    assert any(item["name"] == "Cheese" for item in items)
    assert all(item["category"] == "Dairy" for item in items)
    print("Verified Dairy filtering")


def test_intelligence():
    print("Testing intelligence endpoints...")
    headers = auth_headers("intel_user")

    # 1. Test Low Stock
    requests.post(
        f"{BASE_URL}/item",
        json={
            "name": "Milk Intelligence",
            "quantity": 1,
            "min_quantity": 2,
            "unit": "liters",
            "category": "Dairy",
        },
        headers=headers,
    )
    response = requests.get(f"{BASE_URL}/items/low-stock", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert any(item["name"] == "Milk Intelligence" for item in items)
    print("Verified low-stock detection")

    # 2. Test Expiring
    today = date.today()
    requests.post(
        f"{BASE_URL}/item",
        json={
            "name": "Eggs Intelligence",
            "quantity": 12,
            "unit": "pieces",
            "category": "Dairy",
            "expiration_date": str(today + timedelta(days=2)),
        },
        headers=headers,
    )
    # This should be caught by default 7 days filter
    response = requests.get(f"{BASE_URL}/items/expiring", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert any(item["name"] == "Eggs Intelligence" for item in items)

    # This should NOT be caught by a 1 day filter
    response = requests.get(
        f"{BASE_URL}/items/expiring", params={"days": 1}, headers=headers
    )
    assert response.status_code == 200
    items = response.json()
    assert not any(item["name"] == "Eggs Intelligence" for item in items)
    print("Verified expiration alerts")


def test_batch_and_consumption():
    print("Testing batch and consumption...")
    headers = auth_headers("batch_user")

    # 1. Batch upload
    batch_data = [
        {"name": "Bread Batch", "quantity": 2, "unit": "loaves", "category": "Pantry"},
        {"name": "Butter Batch", "quantity": 1, "unit": "pack", "category": "Dairy"},
    ]
    response = requests.post(f"{BASE_URL}/items", json=batch_data, headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    bread_id = next(item["id"] for item in items if item["name"] == "Bread Batch")
    print("Verified batch upload")

    # 2. Consumption (Successful)
    response = requests.patch(
        f"{BASE_URL}/items/{bread_id}/consume", params={"amount": 1}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["quantity"] == 1
    print("Verified successful consumption")

    # 3. Consumption (Failure - Too much)
    response = requests.patch(
        f"{BASE_URL}/items/{bread_id}/consume", params={"amount": 5}, headers=headers
    )
    assert response.status_code == 400
    assert "Not enough quantity" in response.json()["detail"]
    print("Verified consumption safety check (prevent negative)")


def test_search():
    print("Testing inventory search...")
    headers = auth_headers("search_user")

    created_ids = []

    response = requests.post(
        f"{BASE_URL}/item",
        json={"name": "Search Whole Milk", "quantity": 1, "unit": "liters"},
        headers=headers,
    )
    assert response.status_code == 200
    created_ids.append(response.json()["id"])

    response = requests.post(
        f"{BASE_URL}/item",
        json={"name": "Search Oat Milk", "quantity": 1, "unit": "liters"},
        headers=headers,
    )
    assert response.status_code == 200
    created_ids.append(response.json()["id"])

    response = requests.post(
        f"{BASE_URL}/item",
        json={"name": "Search Bread", "quantity": 1, "unit": "loaf"},
        headers=headers,
    )
    assert response.status_code == 200
    created_ids.append(response.json()["id"])

    try:
        # Search for 'search' (case-insensitive)
        response = requests.get(
            f"{BASE_URL}/items", params={"q": "search"}, headers=headers
        )
        items = response.json()
        assert len(items) == 3
        assert all("Search" in item["name"] for item in items)

        # Search for 'milk'
        response = requests.get(
            f"{BASE_URL}/items", params={"q": "milk"}, headers=headers
        )
        items = response.json()
        assert len(items) == 2
        print("Verified inventory search")
    finally:
        for item_id in created_ids:
            delete_response = requests.delete(
                f"{BASE_URL}/items/{item_id}", headers=headers
            )
            assert delete_response.status_code == 200


def test_user_isolation_inventory():
    print("Testing inventory user isolation...")
    headers_a = auth_headers("iso_a")
    headers_b = auth_headers("iso_b")

    create = requests.post(
        f"{BASE_URL}/item",
        json={"name": "Private Item", "quantity": 1, "unit": "pcs"},
        headers=headers_a,
    )
    assert create.status_code == 200
    item_id = create.json()["id"]

    list_b = requests.get(f"{BASE_URL}/items", headers=headers_b)
    assert list_b.status_code == 200
    assert all(item["id"] != item_id for item in list_b.json())

    get_b = requests.get(f"{BASE_URL}/items/{item_id}", headers=headers_b)
    assert get_b.status_code == 404
    print("Verified inventory isolation")


if __name__ == "__main__":
    test_crud()
    test_filtering()
    test_intelligence()
    test_batch_and_consumption()
    test_search()
    test_user_isolation_inventory()
