"""Tests d'integration de l'authentification."""

from __future__ import annotations


class TestAuth:
    """Connexion, protection des routes, CSRF."""

    def test_login_success(self, client) -> None:  # noqa: ANN001
        """La connexion retourne des jetons et pose les cookies."""
        response = client.post(
            "/api/auth/login", json={"username": "admin", "password": "motdepasse-test"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        assert "access_token" in response.cookies
        assert "csrf_token" in response.cookies

    def test_login_wrong_password(self, client) -> None:  # noqa: ANN001
        """Un mauvais mot de passe retourne 401."""
        response = client.post("/api/auth/login", json={"username": "admin", "password": "mauvais"})
        assert response.status_code == 401

    def test_protected_route_requires_auth(self, client) -> None:  # noqa: ANN001
        """Les routes protegees exigent une authentification."""
        assert client.get("/api/devices").status_code == 401

    def test_me_with_bearer(self, admin_client) -> None:  # noqa: ANN001
        """/auth/me retourne le profil avec un jeton Bearer."""
        response = admin_client.get("/api/auth/me")
        assert response.status_code == 200
        assert response.json()["username"] == "admin"

    def test_cookie_mutation_requires_csrf(self, client) -> None:  # noqa: ANN001
        """Une mutation authentifiee par cookie sans CSRF est refusee."""
        client.post("/api/auth/login", json={"username": "admin", "password": "motdepasse-test"})
        # Cookie de session present, mais aucun en-tete X-CSRF-Token
        response = client.post("/api/shutters", json={"name": "Volet"})
        assert response.status_code == 403

    def test_cookie_mutation_with_csrf(self, client) -> None:  # noqa: ANN001
        """La meme mutation passe avec l'en-tete CSRF valide."""
        login = client.post(
            "/api/auth/login", json={"username": "admin", "password": "motdepasse-test"}
        )
        csrf = login.cookies["csrf_token"]
        response = client.post(
            "/api/shutters", json={"name": "Volet"}, headers={"X-CSRF-Token": csrf}
        )
        assert response.status_code == 201

    def test_health_is_public(self, client) -> None:  # noqa: ANN001
        """/system/health reste accessible sans authentification."""
        assert client.get("/api/system/health").status_code == 200
