"""Systeme de journalisation de DomoPi.

Fournit des loggers par module avec rotation automatique des fichiers :
- un fichier global ``domopi.log`` recevant tous les messages ;
- un fichier par module (``rf.log``, ``hue.log``, ``matter.log``...) ;
- une sortie console lisible en developpement.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import get_settings

# Format commun a tous les handlers
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Modules disposant de leur propre fichier de log
_MODULE_FILES = {
    "domopi.rf": "rf.log",
    "domopi.hue": "hue.log",
    "domopi.matter": "matter.log",
    "domopi.homekit": "homekit.log",
    "domopi.web": "web.log",
    "domopi.scheduler": "scheduler.log",
    "domopi.database": "database.log",
}

_configured = False


def _make_file_handler(path: Path) -> RotatingFileHandler:
    """Cree un handler de fichier avec rotation automatique."""
    settings = get_settings()
    handler = RotatingFileHandler(
        path,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(_FORMAT, _DATE_FORMAT))
    return handler


def setup_logging() -> None:
    """Initialise la journalisation globale (idempotent).

    A appeler une seule fois au demarrage de l'application, avant
    toute creation de logger metier.
    """
    global _configured
    if _configured:
        return

    settings = get_settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("domopi")
    root.setLevel(settings.log_level)

    # Fichier global avec rotation
    root.addHandler(_make_file_handler(settings.log_dir / "domopi.log"))

    # Console (utile en developpement et sous systemd/journalctl)
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_FORMAT, _DATE_FORMAT))
    root.addHandler(console)

    # Un fichier dedie par module fonctionnel
    for logger_name, filename in _MODULE_FILES.items():
        module_logger = logging.getLogger(logger_name)
        module_logger.addHandler(_make_file_handler(settings.log_dir / filename))

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger enfant de ``domopi``.

    Args:
        name: nom court du module (ex. ``rf.somfy``) ; le prefixe
            ``domopi.`` est ajoute automatiquement s'il est absent.
    """
    if not name.startswith("domopi"):
        name = f"domopi.{name}"
    return logging.getLogger(name)
