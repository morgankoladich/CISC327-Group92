"""Assignment 3 tests for successful rental-return notifications."""

from datetime import date
from unittest.mock import patch


def create_rental(client):
    equipment = client.post(
        "/equipment",
        json={
            "name": "Camping Tent",
            "category": "Camping",
            "total_units": 1,
        },
    )
    assert equipment.status_code == 201
    equipment_id = equipment.get_json()["id"]

    renter = client.post(
        "/renters",
        json={
            "name": "Alex Green",
            "email": "alex@example.com",
        },
    )
    assert renter.status_code == 201
    renter_id = renter.get_json()["id"]

    checkout = client.post(
        "/rentals",
        json={
            "equipment_id": equipment_id,
            "renter_id": renter_id,
        },
    )
    assert checkout.status_code == 201

    return equipment_id, checkout.get_json()["id"]


def test_successful_return_with_notification_stub(client, monkeypatch):
    """A successful notification allows the rental return to finish."""

    monkeypatch.setattr(
        "app.routes.rentals.send_notification",
        lambda recipient, subject, message: True,
    )

    equipment_id, rental_id = create_rental(client)

    response = client.put(f"/rentals/{rental_id}/return")

    assert response.status_code == 200
    assert response.get_json()["return_date"] == date.today().isoformat()

    equipment = client.get(f"/equipment/{equipment_id}")
    assert equipment.get_json()["available_units"] == 1


def test_return_notification_has_correct_details(client):
    """Verify the exact recipient, subject, and message."""

    _, rental_id = create_rental(client)

    with patch(
        "app.routes.rentals.send_notification",
        return_value=True,
    ) as mock_notification:

        response = client.put(f"/rentals/{rental_id}/return")

        assert response.status_code == 200

        mock_notification.assert_called_once_with(
            "alex@example.com",
            "Equipment Return Confirmation",
            f"Hi Alex Green, your rental #{rental_id} has been returned successfully.",
        )
def test_web_pages_load_successfully(client):
    """All four main web pages should be accessible."""

    for url in ["/", "/ui/equipment", "/ui/renters", "/ui/rentals"]:
        response = client.get(url)
        assert response.status_code == 200


def test_web_forms_complete_rental_workflow(client):
    """Create, rent, return, and delete records through the web interface."""

    equipment_response = client.post(
        "/ui/equipment",
        data={
            "name": "Camping Tent",
            "category": "Camping",
            "total_units": "2",
        },
        follow_redirects=True,
    )
    assert equipment_response.status_code == 200

    equipment = client.get("/equipment").get_json()
    assert len(equipment) == 1
    equipment_id = equipment[0]["id"]

    renter_response = client.post(
        "/ui/renters",
        data={
            "name": "Sam Rivera",
            "email": "sam@example.com",
        },
        follow_redirects=True,
    )
    assert renter_response.status_code == 200

    renters = client.get("/renters").get_json()
    assert len(renters) == 1
    renter_id = renters[0]["id"]

    checkout = client.post(
        "/ui/rentals",
        data={
            "equipment_id": str(equipment_id),
            "renter_id": str(renter_id),
        },
        follow_redirects=True,
    )
    assert checkout.status_code == 200

    rentals = client.get("/rentals").get_json()
    assert len(rentals) == 1
    rental_id = rentals[0]["id"]

    returned = client.post(
        f"/ui/rentals/{rental_id}/return",
        follow_redirects=True,
    )
    assert returned.status_code == 200

    rental = client.get("/rentals").get_json()[0]
    assert rental["return_date"] == date.today().isoformat()

    equipment_after_return = client.get(f"/equipment/{equipment_id}")
    assert equipment_after_return.get_json()["available_units"] == 2

    client.post(f"/ui/equipment/{equipment_id}/delete")
    client.post(f"/ui/renters/{renter_id}/delete")

    assert client.get("/equipment").get_json() == []
    assert client.get("/renters").get_json() == []

def test_web_return_sends_confirmation_notification(client):
    """Returning equipment through the website sends a confirmation."""

    _, rental_id = create_rental(client)

    with patch(
        "app.routes.views.send_notification",
        return_value=True,
    ) as mock_notification:

        response = client.post(f"/ui/rentals/{rental_id}/return")

    assert response.status_code == 302

    mock_notification.assert_called_once_with(
        "alex@example.com",
        "Equipment Return Confirmation",
        f"Hi Alex Green, your rental #{rental_id} has been returned successfully.",
    )