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


def test_renter_update_is_saved(client):
    renter_id = add_renter(client)
    updated = client.put(
        f"/renters/{renter_id}", json={"email": "new@example.com"}
    )
    assert updated.status_code == 200
    assert client.get(f"/renters/{renter_id}").get_json()["email"] == "new@example.com"
    assert client.get(f"/renters/{renter_id}").get_json()["name"] == "Sam Lee"
    assert client.put("/renters/999", json={"name": "X"}).status_code == 404


def test_renter_deletion_clears_record(client):
    renter_id = add_renter(client)
    assert client.delete(f"/renters/{renter_id}").status_code == 204
    assert client.get("/renters").get_json() == []
    assert client.get(f"/renters/{renter_id}").status_code == 404
    assert client.delete(f"/renters/{renter_id}").status_code == 404


def test_rental_list_and_equipment_filter(client):
    renter_id = add_renter(client)
    tent_id = add_equipment(client, "Tent")
    bike_id = add_equipment(client, "Bike")
    tent_rental = add_rental(client, tent_id, renter_id)
    add_rental(client, bike_id, renter_id)
    all_rentals = client.get("/rentals")
    assert all_rentals.status_code == 200
    assert len(all_rentals.get_json()) == 2
    filtered = client.get(f"/rentals?equipment_id={tent_id}")
    assert [r["id"] for r in filtered.get_json()] == [tent_rental]


def test_rental_filter_by_renter_id(client):
    """FR-11: a customer should get only their own rental records."""
    renter_a = add_renter(client, "Alex", "alex@example.com")
    renter_b = add_renter(client, "Blair", "blair@example.com")
    item_a = add_equipment(client, "Kayak")
    item_b = add_equipment(client, "Helmet")
    rental_a = add_rental(client, item_b, renter_a)
    add_rental(client, item_a, renter_b)
    filtered = client.get(f"/rentals?renter_id={renter_a}")
    assert filtered.status_code == 200
    assert [r["id"] for r in filtered.get_json()] == [rental_a]


def test_extension_changes_due_date_and_preserves_rental(client):
    renter_id = add_renter(client)
    item_id = add_equipment(client)
    rental_id = add_rental(client, item_id, renter_id)
    original = next(r for r in client.get("/rentals").get_json() if r["id"] == rental_id)
    response = client.put(f"/rentals/{rental_id}/extend", json={"days": 3})
    assert response.status_code == 200
    expected = date.fromisoformat(original["due_date"]) + timedelta(days=3)
    assert response.get_json()["due_date"] == expected.isoformat()
    assert client.get("/rentals").get_json()[0]["due_date"] == expected.isoformat()


def test_extension_rejects_returned_or_missing_rentals(client):
    renter_id = add_renter(client)
    item_id = add_equipment(client)
    rental_id = add_rental(client, item_id, renter_id)
    assert client.put(f"/rentals/{rental_id}/return").status_code == 200
    assert client.put(f"/rentals/{rental_id}/extend", json={"days": 2}).status_code == 400
    assert client.put("/rentals/999/extend", json={"days": 2}).status_code == 404


def test_deposit_release_requires_return_and_is_saved(client):
    renter_id = add_renter(client)
    item_id = add_equipment(client)
    rental_id = add_rental(client, item_id, renter_id, deposit=50.0)
    assert client.put(f"/rentals/{rental_id}/deposit/release").status_code == 400
    assert client.put(f"/rentals/{rental_id}/return").status_code == 200
    released = client.put(f"/rentals/{rental_id}/deposit/release")
    assert released.status_code == 200
    assert released.get_json()["deposit_released"] is True
    stored = next(r for r in client.get("/rentals").get_json() if r["id"] == rental_id)
    assert stored["deposit_amount"] == 50.0
    assert stored["deposit_released"] is True


