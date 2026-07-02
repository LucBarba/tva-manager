"""Tests unitaires des primitives de securite."""

from __future__ import annotations

import pytest
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_csrf_token,
    hash_password,
    verify_csrf_token,
    verify_password,
)


class TestPasswords:
    """Hachage bcrypt des mots de passe."""

    def test_hash_and_verify(self) -> None:
        """Un mot de passe correct est verifie avec succes."""
        hashed = hash_password("super-secret")
        assert hashed != "super-secret"
        assert verify_password("super-secret", hashed)

    def test_wrong_password_rejected(self) -> None:
        """Un mauvais mot de passe est refuse."""
        hashed = hash_password("super-secret")
        assert not verify_password("mauvais", hashed)

    def test_corrupt_hash_rejected(self) -> None:
        """Un hachage corrompu ne leve pas mais refuse."""
        assert not verify_password("x", "pas-un-hash-bcrypt")


class TestJwt:
    """Creation et validation des jetons JWT."""

    def test_access_token_roundtrip(self) -> None:
        """Un jeton d'acces emis est decodable."""
        token = create_access_token("alice")
        payload = decode_token(token, expected_type="access")
        assert payload["sub"] == "alice"

    def test_refresh_not_usable_as_access(self) -> None:
        """Un refresh token ne passe pas pour un jeton d'acces."""
        token = create_refresh_token("alice")
        with pytest.raises(AuthenticationError):
            decode_token(token, expected_type="access")

    def test_garbage_token_rejected(self) -> None:
        """Un jeton corrompu est rejete."""
        with pytest.raises(AuthenticationError):
            decode_token("n.importe.quoi")


class TestCsrf:
    """Jetons CSRF a double soumission signee."""

    def test_valid_token(self) -> None:
        """Un jeton emis est valide."""
        assert verify_csrf_token(generate_csrf_token())

    def test_tampered_token_rejected(self) -> None:
        """Un jeton modifie est rejete."""
        token = generate_csrf_token()
        assert not verify_csrf_token(token[:-4] + "0000")

    def test_missing_token_rejected(self) -> None:
        """L'absence de jeton est rejetee."""
        assert not verify_csrf_token(None)
        assert not verify_csrf_token("")
