"""Tests unitaires du service utilisateurs."""

from __future__ import annotations

import pytest
from app.core.exceptions import AuthenticationError, ValidationError
from app.services.user_service import UserService


@pytest.fixture
def service(db: None) -> UserService:
    """Service utilisateurs avec compte admin initial."""
    user_service = UserService()
    user_service.ensure_admin()
    return user_service


class TestUserService:
    """Comptes et authentification."""

    @pytest.mark.asyncio
    async def test_admin_can_authenticate(self, service: UserService) -> None:
        """Le compte admin initial peut se connecter."""
        user = await service.authenticate("admin", "motdepasse-test")
        assert user.role == "admin"

    @pytest.mark.asyncio
    async def test_wrong_password_rejected(self, service: UserService) -> None:
        """Un mauvais mot de passe est refuse."""
        with pytest.raises(AuthenticationError):
            await service.authenticate("admin", "mauvais")

    def test_short_password_rejected(self, service: UserService) -> None:
        """Un mot de passe trop court est refuse a la creation."""
        with pytest.raises(ValidationError):
            service.create_user("bob", "court", "user")

    def test_duplicate_username_rejected(self, service: UserService) -> None:
        """Un nom deja pris est refuse."""
        service.create_user("bob", "motdepasse", "user")
        with pytest.raises(ValidationError):
            service.create_user("bob", "autremotdepasse", "user")

    def test_last_admin_protected(self, service: UserService) -> None:
        """Le dernier administrateur ne peut pas etre supprime."""
        admin = service.get_by_username("admin")
        assert admin is not None
        with pytest.raises(ValidationError):
            service.delete_user(admin.id)
