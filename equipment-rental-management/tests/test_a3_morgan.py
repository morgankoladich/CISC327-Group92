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
