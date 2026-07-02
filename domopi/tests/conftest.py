"""Configuration commune des tests DomoPi.

Chaque session de test utilise :
- une base SQLite temporaire ;
- le pilote RF simule (``mock``) ;
- les integrations reseau (Hue, HomeKit) desactivees ;
- un client HTTP FastAPI avec cycle de vie complet.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest


def _configure_environment(tmp_dir: Path) -> None:
    """Positionne les variables d'environnement de test."""
    os.environ.update(
        {
            "DOMOPI_ENVIRONMENT": "test",
            "DOMOPI_SECRET_KEY": "cle-de-test-uniquement-suffisamment-longue-pour-hs256",
            "DOMOPI_DATABASE_URL": f"sqlite:///{tmp_dir / 'test.db'}",
            "DOMOPI_LOG_DIR": str(tmp_dir / "logs"),
            "DOMOPI_RF_DRIVER": "mock",
            "DOMOPI_HUE_ENABLED": "false",
            "DOMOPI_HOMEKIT_ENABLED": "false",
            "DOMOPI_MATTER_ENABLED": "true",
            "DOMOPI_ADMIN_USERNAME": "admin",
            "DOMOPI_ADMIN_PASSWORD": "motdepasse-test",
        }
    )


@pytest.fixture(scope="session", autouse=True)
def test_settings(tmp_path_factory: pytest.TempPathFactory) -> Generator[None, None, None]:
    """Configure l'environnement de test pour toute la session."""
    tmp_dir = tmp_path_factory.mktemp("domopi")
    _configure_environment(tmp_dir)

    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def db(test_settings: None) -> Generator[None, None, None]:
    """Base de donnees initialisee et videe apres chaque test."""
    from app.database.engine import get_engine, init_db, reset_engine
    from app.database.models import Base

    init_db()
    yield
    Base.metadata.drop_all(get_engine())
    reset_engine()


@pytest.fixture
def client(db: None) -> Generator[object, None, None]:
    """Client HTTP de test avec cycle de vie applicatif complet."""
    from app.devices.registry import device_registry
    from app.web.app import create_app
    from fastapi.testclient import TestClient

    device_registry.clear()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    device_registry.clear()


@pytest.fixture
def admin_client(client) -> object:  # noqa: ANN001
    """Client authentifie en administrateur (cookies + en-tete CSRF)."""
    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "motdepasse-test"}
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    # Utilise l'en-tete Bearer : pas de contrainte CSRF pour les clients API
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
