"""Morgan's tests for equipment, checkout, and returns.

The supplied example tests remain separate and are not counted here.
"""

from datetime import date, timedelta


def add_equipment(client, name="Kayak", units=2):
    response = client.post(
        "/equipment",
        json={"name": name, "category": "Water", "total_units": units},
    )
    assert response.status_code == 201
    return response.get_json()["id"]


def add_renter(client):
    response = client.post(
        "/renters", json={"name": "Alex Green", "email": "alex@example.com"}
    )
    assert response.status_code == 201
    return response.get_json()["id"]


def test_equipment_creation_list_and_detail(client):
    item_id = add_equipment(client, name="Canoe", units=3)
    listed = client.get("/equipment")
    assert listed.status_code == 200
    assert len(listed.get_json()) == 1
    assert listed.get_json()[0]["name"] == "Canoe"

    detail = client.get(f"/equipment/{item_id}")
    assert detail.status_code == 200
    assert detail.get_json()["available_units"] == 3
    assert client.get("/equipment/999").status_code == 404


def test_equipment_update_is_saved(client):
    item_id = add_equipment(client)
    updated = client.put(
        f"/equipment/{item_id}", json={"name": "Touring Kayak", "total_units": 4}
    )
    assert updated.status_code == 200
    assert client.get(f"/equipment/{item_id}").get_json()["name"] == "Touring Kayak"
    assert client.get(f"/equipment/{item_id}").get_json()["total_units"] == 4
    assert client.put("/equipment/999", json={"name": "X"}).status_code == 404


def test_equipment_deletion_removes_item(client):
    item_id = add_equipment(client)
    assert client.delete(f"/equipment/{item_id}").status_code == 204
    assert client.get("/equipment").get_json() == []
    assert client.get(f"/equipment/{item_id}").status_code == 404
    assert client.delete(f"/equipment/{item_id}").status_code == 404


