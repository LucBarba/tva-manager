"""Primitives de securite de DomoPi.

Regroupe :
- hachage des mots de passe (bcrypt) ;
- creation/verification de jetons JWT (acces + rafraichissement) ;
- generation/verification de jetons CSRF (double soumission signee).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError

# ---------------------------------------------------------------------------
# Mots de passe
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hache un mot de passe avec bcrypt (sel automatique)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Compare un mot de passe en clair a son hachage bcrypt."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Hachage corrompu ou format inattendu : refus systematique
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


def _create_token(subject: str, token_type: str, lifetime: timedelta) -> str:
    """Construit un JWT signe pour le sujet donne.

    Args:
        subject: identifiant de l'utilisateur (username).
        token_type: ``access`` ou ``refresh``.
        lifetime: duree de validite du jeton.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + lifetime,
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str) -> str:
    """Cree un jeton d'acces de courte duree."""
    settings = get_settings()
    return _create_token(subject, "access", timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(subject: str) -> str:
    """Cree un jeton de rafraichissement de longue duree."""
    settings = get_settings()
    return _create_token(subject, "refresh", timedelta(days=settings.refresh_token_expire_days))


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Decode et valide un JWT ; leve ``AuthenticationError`` sinon.

    Args:
        token: jeton JWT brut.
        expected_type: type attendu (``access`` ou ``refresh``) afin
            d'empecher l'usage d'un refresh token comme jeton d'acces.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Jeton expire") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Jeton invalide") from exc
    if payload.get("type") != expected_type:
        raise AuthenticationError("Type de jeton inattendu")
    return payload


# ---------------------------------------------------------------------------
# CSRF (double soumission signee : cookie + en-tete X-CSRF-Token)
# ---------------------------------------------------------------------------


def generate_csrf_token() -> str:
    """Genere un jeton CSRF aleatoire signe par la cle secrete."""
    settings = get_settings()
    nonce = secrets.token_hex(16)
    signature = hmac.new(
        settings.secret_key.encode("utf-8"), nonce.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{nonce}.{signature}"


def verify_csrf_token(token: str | None) -> bool:
    """Verifie l'integrite d'un jeton CSRF emis par ``generate_csrf_token``."""
    if not token or "." not in token:
        return False
    settings = get_settings()
    nonce, _, signature = token.partition(".")
    expected = hmac.new(
        settings.secret_key.encode("utf-8"), nonce.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
