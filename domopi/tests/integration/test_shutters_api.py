"""Tests d'integration des routes volets et groupes."""

from __future__ import annotations


class TestShuttersApi:
    """Cycle de vie complet d'un volet via l'API."""

    def test_full_lifecycle(self, admin_client) -> None:  # noqa: ANN001
        """Creation, commande, apprentissage, suppression."""
        # Creation (Somfy pour pouvoir commander sans apprentissage)
        created = admin_client.post(
            "/api/shutters",
            json={"name": "Salon", "room": "Salon", "protocol": "somfy_rts"},
        )
        assert created.status_code == 201
        shutter_id = created.json()["id"]

        # Le volet apparait dans le registre unifie
        devices = admin_client.get("/api/devices").json()
        assert any(device["uid"] == f"shutter:{shutter_id}" for device in devices)

        # Commande d'ouverture puis verification de la position
        assert admin_client.post(f"/api/shutters/{shutter_id}/close").status_code == 200
        detail = admin_client.get(f"/api/shutters/{shutter_id}").json()
        assert detail["position"] == 0

        # Action inconnue refusee
        assert admin_client.post(f"/api/shutters/{shutter_id}/explode").status_code == 400

        # Suppression
        assert admin_client.delete(f"/api/shutters/{shutter_id}").status_code == 200
        assert admin_client.get(f"/api/shutters/{shutter_id}").status_code == 404

    def test_learn_rf433_code(self, admin_client) -> None:  # noqa: ANN001
        """L'apprentissage simule associe un code a une action."""
        shutter_id = admin_client.post(
            "/api/shutters", json={"name": "Cuisine", "protocol": "rf433"}
        ).json()["id"]
        response = admin_client.post(
            f"/api/shutters/{shutter_id}/learn/code",
            json={"action": "open", "timeout_s": 1},
        )
        assert response.status_code == 200
        detail = admin_client.get(f"/api/shutters/{shutter_id}").json()
        assert "open" in detail["rf_codes"]

    def test_groups(self, admin_client) -> None:  # noqa: ANN001
        """Creation et commande d'un groupe."""
        first = admin_client.post(
            "/api/shutters", json={"name": "V1", "protocol": "somfy_rts"}
        ).json()["id"]
        second = admin_client.post(
            "/api/shutters", json={"name": "V2", "protocol": "somfy_rts"}
        ).json()["id"]
        group = admin_client.post(
            "/api/shutters/groups", json={"name": "Etage", "shutter_ids": [first, second]}
        )
        assert group.status_code == 201
        group_id = group.json()["id"]
        assert admin_client.post(f"/api/shutters/groups/{group_id}/open").status_code == 200
        # Les deux volets sont ouverts
        for shutter_id in (first, second):
            assert admin_client.get(f"/api/shutters/{shutter_id}").json()["position"] == 100
