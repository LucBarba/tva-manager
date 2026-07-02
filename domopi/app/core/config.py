"""Configuration centralisee de DomoPi.

Toutes les valeurs proviennent du fichier `.env` (ou des variables
d'environnement) et sont validees par Pydantic. Un singleton
`get_settings()` est expose pour l'injection de dependances.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Racine du projet (dossier contenant main.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Parametres globaux de l'application, charges depuis `.env`.

    Chaque attribut correspond a une variable d'environnement prefixee
    par ``DOMOPI_`` (ex. ``DOMOPI_PORT``). Les valeurs par defaut
    permettent un demarrage en mode developpement sans configuration.
    """

    model_config = SettingsConfigDict(
        env_prefix="DOMOPI_",
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "DomoPi"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # --- Securite ---
    secret_key: str = "dev-secret-key-do-not-use-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    admin_username: str = "admin"
    admin_password: str = "admin"

    # --- HTTPS optionnel ---
    ssl_certfile: str = ""
    ssl_keyfile: str = ""

    # --- Base de donnees ---
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'domopi.db'}"

    # --- Journalisation ---
    log_dir: Path = BASE_DIR / "logs"
    log_level: str = "INFO"
    log_max_bytes: int = 5 * 1024 * 1024
    log_backup_count: int = 5

    # --- Radiofrequence ---
    rf_driver: str = "mock"  # mock | rf433 | somfy_rts
    rf_tx_gpio: int = 17
    rf_rx_gpio: int = 27
    rf_repeats: int = 8

    # --- Philips Hue ---
    hue_enabled: bool = True
    hue_bridge_ip: str = ""
    hue_app_key: str = ""

    # --- Matter ---
    matter_enabled: bool = True
    matter_server_url: str = "ws://127.0.0.1:5580/ws"

    # --- HomeKit ---
    homekit_enabled: bool = True
    homekit_bridge_name: str = "DomoPi Bridge"
    homekit_port: int = 51826
    homekit_pincode: str = "031-45-154"
    homekit_state_file: Path = BASE_DIR / "data" / "homekit.state"

    @field_validator("rf_driver")
    @classmethod
    def _validate_rf_driver(cls, value: str) -> str:
        """Verifie que le pilote RF demande est connu."""
        allowed = {"mock", "rf433", "somfy_rts"}
        if value not in allowed:
            raise ValueError(f"rf_driver doit etre parmi {allowed}, recu: {value!r}")
        return value

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        """Normalise et valide le niveau de log."""
        level = value.upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"Niveau de log invalide: {value!r}")
        return level

    # Champ derive : True si l'app tourne en mode test
    is_test: bool = Field(default=False, exclude=True)

    @property
    def is_production(self) -> bool:
        """Indique si l'application tourne en production."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance unique de configuration (mise en cache).

    L'utilisation de ``lru_cache`` garantit une lecture unique du
    fichier `.env` et permet de surcharger la configuration dans les
    tests via ``get_settings.cache_clear()``.
    """
    return Settings()
