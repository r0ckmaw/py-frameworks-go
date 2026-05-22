from datetime import date, timedelta

import requests

BASE_URL = "http://localhost:8000/items"


def test_crud():
    print("Testing CRUD...")
    # 1. Create an item
    item_data = {
        "name": "Milk",
        "quantity": 2.0,
        "unit": "liters",
        "category": "Dairy",
        "expiration_date": str(date.today() + timedelta(days=7)),
    }
    response = requests.post(f"{BASE_URL}/", json=item_data)
    assert response.status_code == 200
    item = response.json()
    assert item["name"] == "Milk"
    assert item["category"] == "Dairy"
    item_id = item["id"]
    print(f"Created item with ID: {item_id}")

    # 2. Get all items
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    print(f"Total items in inventory: {len(items)}")

    # 3. Get single item
    response = requests.get(f"{BASE_URL}/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Milk"

    # 4. Update item
    update_data = item_data.copy()
    update_data["quantity"] = 1.5
    response = requests.put(f"{BASE_URL}/{item_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["quantity"] == 1.5
    print(f"Updated item {item_id} quantity to 1.5")

    # 5. Delete item
    response = requests.delete(f"{BASE_URL}/{item_id}")
    assert response.status_code == 200
    print(f"Deleted item {item_id}")

    # 6. Verify deletion
    response = requests.get(f"{BASE_URL}/{item_id}")
    assert response.status_code == 404
    print("Verified item deletion (404)")


def test_filtering():
    print("Testing filtering...")
    # Add two items in different categories
    requests.post(
        f"{BASE_URL}/",
        json={"name": "Apples", "quantity": 5, "unit": "pieces", "category": "Produce"},
    )
    requests.post(
        f"{BASE_URL}/",
        json={"name": "Cheese", "quantity": 1, "unit": "block", "category": "Dairy"},
    )

    # Filter by Produce
    response = requests.get(f"{BASE_URL}/", params={"category": "Produce"})
    items = response.json()
    assert any(item["name"] == "Apples" for item in items)
    assert all(item["category"] == "Produce" for item in items)
    print("Verified Produce filtering")

    # Filter by Dairy
    response = requests.get(f"{BASE_URL}/", params={"category": "Dairy"})
    items = response.json()
    assert any(item["name"] == "Cheese" for item in items)
    assert all(item["category"] == "Dairy" for item in items)
    print("Verified Dairy filtering")


def test_intelligence():
    print("Testing intelligence endpoints...")
    # 1. Test Low Stock
    requests.post(
        f"{BASE_URL}/",
        json={
            "name": "Milk",
            "quantity": 1,
            "min_quantity": 2,
            "unit": "liters",
            "category": "Dairy",
        },
    )
    response = requests.get(f"{BASE_URL}/low-stock")
    assert response.status_code == 200
    items = response.json()
    assert any(item["name"] == "Milk" for item in items)
    print("Verified low-stock detection")

    # 2. Test Expiring
    today = date.today()
    requests.post(
        f"{BASE_URL}/",
        json={
            "name": "Eggs",
            "quantity": 12,
            "unit": "pieces",
            "category": "Dairy",
            "expiration_date": str(today + timedelta(days=2)),
        },
    )
    # This should be caught by default 7 days filter
    response = requests.get(f"{BASE_URL}/expiring")
    assert response.status_code == 200
    items = response.json()
    assert any(item["name"] == "Eggs" for item in items)

    # This should NOT be caught by a 1 day filter
    response = requests.get(f"{BASE_URL}/expiring", params={"days": 1})
    assert response.status_code == 200
    items = response.json()
    assert not any(item["name"] == "Eggs" for item in items)
    print("Verified expiration alerts")


if __name__ == "__main__":
    test_crud()
    test_filtering()
    test_intelligence()
