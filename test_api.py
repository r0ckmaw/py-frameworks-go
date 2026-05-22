import json
from datetime import date, timedelta

import requests

BASE_URL = "http://localhost:8000"


def test_crud():
    # 1. Create an item
    item_data = {
        "name": "Milk",
        "quantity": 2.0,
        "unit": "liters",
        "expiration_date": str(date.today() + timedelta(days=7)),
    }
    response = requests.post(f"{BASE_URL}/items/", json=item_data)
    assert response.status_code == 200
    item = response.json()
    assert item["name"] == "Milk"
    item_id = item["id"]
    print(f"Created item with ID: {item_id}")

    # 2. Get all items
    response = requests.get(f"{BASE_URL}/items/")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    print(f"Total items in inventory: {len(items)}")

    # 3. Get single item
    response = requests.get(f"{BASE_URL}/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Milk"

    # 4. Update item
    update_data = item_data.copy()
    update_data["quantity"] = 1.5
    response = requests.put(f"{BASE_URL}/items/{item_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["quantity"] == 1.5
    print(f"Updated item {item_id} quantity to 1.5")

    # 5. Delete item
    response = requests.delete(f"{BASE_URL}/items/{item_id}")
    assert response.status_code == 200
    print(f"Deleted item {item_id}")

    # 6. Verify deletion
    response = requests.get(f"{BASE_URL}/items/{item_id}")
    assert response.status_code == 404
    print("Verified item deletion (404)")


if __name__ == "__main__":
    test_crud()
