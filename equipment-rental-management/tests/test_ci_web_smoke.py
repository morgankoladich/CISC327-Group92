"""Smoke tests for the equipment rental web interface."""


def test_main_web_pages_load(client):
    """The home, equipment, and renter pages should load."""

    for url in ["/", "/ui/equipment", "/ui/renters"]:
        response = client.get(url)
        assert response.status_code == 200


def test_web_equipment_form_creates_available_inventory(client):
    """Equipment added through the website appears in inventory."""

    response = client.post(
        "/ui/equipment",
        data={
            "name": "Climbing Harness",
            "category": "Climbing",
            "total_units": "3",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/equipment")

    inventory = client.get("/equipment")

    assert inventory.status_code == 200
    equipment = inventory.get_json()

    assert len(equipment) == 1
    assert equipment[0]["name"] == "Climbing Harness"
    assert equipment[0]["total_units"] == 3
    assert equipment[0]["available_units"] == 3