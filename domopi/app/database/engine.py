"""Moteur SQLAlchemy et gestion des sessions.

Expose :
- ``init_db()`` : creation du schema au demarrage ;
- ``get_session()`` : generateur FastAPI (une session par requete) ;
- ``session_scope()`` : contexte transactionnel pour le code interne.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("database.engine")

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Retourne le moteur SQLAlchemy (cree paresseusement)."""
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        # Cree le dossier data/ si la base est un fichier local
        if settings.database_url.startswith("sqlite:///"):
            db_path = Path(settings.database_url.removeprefix("sqlite:///"))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            settings.database_url,
            # SQLite : autorise l'usage depuis plusieurs threads (FastAPI,
            # planificateur, pont HomeKit)
            connect_args={"check_same_thread": False},
            echo=False,
        )

        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
            """Active les cles etrangeres et le mode WAL sur chaque connexion."""
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

        _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
        logger.info("Moteur base de donnees initialise (%s)", settings.database_url)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Retourne la fabrique de sessions (initialise le moteur au besoin)."""
    get_engine()
    assert _session_factory is not None
    return _session_factory


def init_db() -> None:
    """Cree toutes les tables declarees dans ``models.py``."""
    from app.database import models  # noqa: F401  (enregistre les modeles)

    models.Base.metadata.create_all(get_engine())
    logger.info("Schema de base de donnees verifie/cree")


def reset_engine() -> None:
    """Reinitialise le moteur (utilise par les tests)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_db() -> Generator[Session, None, None]:
    """Dependance FastAPI : fournit une session fermee en fin de requete."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Contexte transactionnel : commit si succes, rollback sinon."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
