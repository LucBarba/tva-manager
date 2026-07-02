"""Tests d'integration des routes utilisateurs et des roles."""

from __future__ import annotations


class TestUsersApi:
    """Gestion des comptes et separation des roles."""

    def test_create_and_list_users(self, admin_client) -> None:  # noqa: ANN001
        """Un administrateur cree et liste les comptes."""
        response = admin_client.post(
            "/api/users",
            json={"username": "famille", "password": "motdepasse", "role": "user"},
        )
        assert response.status_code == 201
        usernames = [user["username"] for user in admin_client.get("/api/users").json()]
        assert "famille" in usernames

    def test_non_admin_cannot_manage_users(self, admin_client, client) -> None:  # noqa: ANN001
        """Un utilisateur standard ne peut pas gerer les comptes."""
        admin_client.post(
            "/api/users",
            json={"username": "famille", "password": "motdepasse", "role": "user"},
        )
        login = client.post(
            "/api/auth/login", json={"username": "famille", "password": "motdepasse"}
        )
        token = login.json()["access_token"]
        response = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403

    def test_weak_password_rejected(self, admin_client) -> None:  # noqa: ANN001
        """Un mot de passe trop court est refuse (validation Pydantic)."""
        response = admin_client.post(
            "/api/users", json={"username": "bob", "password": "court", "role": "user"}
        )
        assert response.status_code == 422

    def test_matter_mock_sensor_visible(self, admin_client) -> None:  # noqa: ANN001
        """Le capteur Matter simule est expose avec ses mesures."""
        devices = admin_client.get("/api/devices?type=temperature_sensor").json()
        assert devices, "le capteur Matter simule doit etre enregistre"
        assert devices[0]["attributes"]["temperature"] == 21.5
