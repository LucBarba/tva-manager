"""Service metier des utilisateurs : comptes, roles, authentification."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.config import get_settings
from app.core.events import Event, EventType, event_bus
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password
from app.database.engine import session_scope
from app.database.models import User

logger = get_logger("web.users")


class UserService:
    """Gestion des comptes utilisateurs et de l'authentification."""

    def ensure_admin(self) -> None:
        """Cree le compte administrateur initial s'il n'existe pas.

        Les identifiants proviennent de ``.env`` ; a executer au
        demarrage de l'application.
        """
        settings = get_settings()
        with session_scope() as session:
            exists = session.query(User).filter_by(username=settings.admin_username).first()
            if exists is None:
                session.add(
                    User(
                        username=settings.admin_username,
                        password_hash=hash_password(settings.admin_password),
                        role="admin",
                    )
                )
                logger.info("Compte administrateur initial cree (%s)", settings.admin_username)

    async def authenticate(self, username: str, password: str) -> User:
        """Verifie les identifiants et retourne l'utilisateur.

        Raises:
            AuthenticationError: identifiants invalides ou compte inactif.
        """
        with session_scope() as session:
            user = session.query(User).filter_by(username=username).first()
            # Message identique que le compte existe ou non, pour ne pas
            # reveler l'existence d'un nom d'utilisateur.
            if user is None or not verify_password(password, user.password_hash):
                raise AuthenticationError("Identifiants invalides")
            if not user.is_active:
                raise AuthenticationError("Compte desactive")
            user.last_login = datetime.now(UTC)
            session.flush()
            session.refresh(user)
        await event_bus.publish(Event(EventType.USER_LOGIN, {"username": username}))
        return user

    def get_by_username(self, username: str) -> User | None:
        """Retourne un utilisateur par son nom (ou ``None``)."""
        with session_scope() as session:
            return session.query(User).filter_by(username=username).first()

    def list_users(self) -> list[User]:
        """Retourne tous les utilisateurs."""
        with session_scope() as session:
            return list(session.query(User).order_by(User.username).all())

    def create_user(self, username: str, password: str, role: str = "user") -> User:
        """Cree un utilisateur apres validation des entrees."""
        if role not in {"admin", "user"}:
            raise ValidationError(f"Role inconnu: {role}")
        if len(password) < 8:
            raise ValidationError("Le mot de passe doit contenir au moins 8 caracteres")
        with session_scope() as session:
            if session.query(User).filter_by(username=username).first() is not None:
                raise ValidationError(f"Le nom d'utilisateur '{username}' existe deja")
            user = User(username=username, password_hash=hash_password(password), role=role)
            session.add(user)
            session.flush()
            session.refresh(user)
            return user

    def update_password(self, user_id: int, new_password: str) -> None:
        """Change le mot de passe d'un utilisateur."""
        if len(new_password) < 8:
            raise ValidationError("Le mot de passe doit contenir au moins 8 caracteres")
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValidationError(f"Utilisateur {user_id} introuvable")
            user.password_hash = hash_password(new_password)

    def delete_user(self, user_id: int) -> None:
        """Supprime un utilisateur (le dernier admin est protege)."""
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValidationError(f"Utilisateur {user_id} introuvable")
            if user.role == "admin":
                admin_count = session.query(User).filter_by(role="admin", is_active=True).count()
                if admin_count <= 1:
                    raise ValidationError("Impossible de supprimer le dernier administrateur")
            session.delete(user)
