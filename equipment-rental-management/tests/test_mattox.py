"""Mattox's tests for renters and rental record operations."""

from datetime import date, timedelta

from app import store


def add_renter(client, name="Sam Lee", email="sam@example.com"):
    response = client.post("/renters", json={"name": name, "email": email})
    assert response.status_code == 201
    return response.get_json()["id"]


def add_equipment(client, name="Tent"):
    response = client.post(
        "/equipment", json={"name": name, "category": "Camping", "total_units": 2}
    )
    assert response.status_code == 201
    return response.get_json()["id"]


def add_rental(client, item_id, renter_id, deposit=0.0):
    response = client.post(
        "/rentals",
        json={
            "equipment_id": item_id,
            "renter_id": renter_id,
            "deposit_amount": deposit,
        },
    )
    assert response.status_code == 201
    return response.get_json()["id"]


def test_renter_create_list_and_detail(client):
    renter_id = add_renter(client, name="Jamie Taylor")
    renters = client.get("/renters")
    assert renters.status_code == 200
    assert len(renters.get_json()) == 1
    assert renters.get_json()[0]["name"] == "Jamie Taylor"
    assert client.get(f"/renters/{renter_id}").get_json()["email"] == "sam@example.com"
    assert client.get("/renters/999").status_code == 404


