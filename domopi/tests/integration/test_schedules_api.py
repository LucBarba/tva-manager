"""Tests d'integration des routes de programmation horaire."""

from __future__ import annotations


class TestSchedulesApi:
    """CRUD des programmations."""

    def test_create_and_list(self, admin_client) -> None:  # noqa: ANN001
        """Une programmation creee apparait dans la liste."""
        shutter_id = admin_client.post(
            "/api/shutters", json={"name": "Volet", "protocol": "somfy_rts"}
        ).json()["id"]
        response = admin_client.post(
            "/api/schedules",
            json={
                "name": "Fermeture du soir",
                "target_type": "shutter",
                "target_id": str(shutter_id),
                "action": "close",
                "time": "21:30",
                "days": [1, 2, 3, 4, 5],
            },
        )
        assert response.status_code == 201
        schedules = admin_client.get("/api/schedules").json()
        assert any(schedule["name"] == "Fermeture du soir" for schedule in schedules)

    def test_invalid_time_rejected(self, admin_client) -> None:  # noqa: ANN001
        """Un format d'heure invalide est refuse par la validation."""
        response = admin_client.post(
            "/api/schedules",
            json={
                "name": "X",
                "target_type": "shutter",
                "target_id": "1",
                "action": "open",
                "time": "25:99",
                "days": [1],
            },
        )
        assert response.status_code == 422

    def test_disable_and_delete(self, admin_client) -> None:  # noqa: ANN001
        """Desactivation puis suppression d'une programmation."""
        schedule_id = admin_client.post(
            "/api/schedules",
            json={
                "name": "Test",
                "target_type": "shutter",
                "target_id": "1",
                "action": "open",
                "time": "08:00",
                "days": [6, 7],
            },
        ).json()["id"]
        disabled = admin_client.patch(f"/api/schedules/{schedule_id}/enabled?enabled=false")
        assert disabled.status_code == 200
        assert disabled.json()["enabled"] is False
        assert admin_client.delete(f"/api/schedules/{schedule_id}").status_code == 200
