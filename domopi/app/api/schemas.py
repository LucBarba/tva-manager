"""Schemas Pydantic de l'API REST.

Chaque schema valide les entrees (longueurs, bornes, formats) afin de
proteger les couches basses ; les schemas ``*Out`` controlent les
champs exposes (jamais de hachage de mot de passe, par exemple).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Authentification et utilisateurs
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """Identifiants de connexion."""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Jetons emis apres connexion."""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class UserCreate(BaseModel):
    """Creation d'un utilisateur."""

    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    role: Literal["admin", "user"] = "user"


class PasswordChange(BaseModel):
    """Changement de mot de passe."""

    new_password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    """Representation publique d'un utilisateur."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None


# ---------------------------------------------------------------------------
# Peripheriques generiques
# ---------------------------------------------------------------------------


class DeviceOut(BaseModel):
    """Peripherique du registre avec son etat courant."""

    uid: str
    name: str
    type: str
    room: str
    online: bool = True
    attributes: dict[str, Any] = Field(default_factory=dict)


class CommandRequest(BaseModel):
    """Commande generique adressee a un peripherique."""

    command: str = Field(min_length=1, max_length=32)
    params: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Volets
# ---------------------------------------------------------------------------


class ShutterCreate(BaseModel):
    """Creation d'un volet roulant."""

    name: str = Field(min_length=1, max_length=64)
    room: str = Field(default="", max_length=64)
    protocol: Literal["rf433", "somfy_rts"] = "rf433"
    travel_time_s: float = Field(default=20.0, ge=1.0, le=120.0)
    favorite_position: int = Field(default=50, ge=0, le=100)


class ShutterUpdate(BaseModel):
    """Mise a jour partielle d'un volet."""

    name: str | None = Field(default=None, min_length=1, max_length=64)
    room: str | None = Field(default=None, max_length=64)
    travel_time_s: float | None = Field(default=None, ge=1.0, le=120.0)
    favorite_position: int | None = Field(default=None, ge=0, le=100)


class ShutterOut(BaseModel):
    """Representation d'un volet."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    room: str
    protocol: str
    position: int
    favorite_position: int
    travel_time_s: float
    rf_codes: dict[str, Any]


class LearnRequest(BaseModel):
    """Apprentissage d'un bouton de telecommande RF433."""

    action: Literal["open", "close", "stop", "favorite"]
    timeout_s: float = Field(default=15.0, ge=1.0, le=60.0)


class GroupCreate(BaseModel):
    """Creation d'un groupe de volets."""

    name: str = Field(min_length=1, max_length=64)
    shutter_ids: list[int] = Field(min_length=1)


class GroupOut(BaseModel):
    """Representation d'un groupe de volets."""

    id: int
    name: str
    shutter_ids: list[int]


# ---------------------------------------------------------------------------
# Lumieres Hue
# ---------------------------------------------------------------------------


class HueGroupCommand(BaseModel):
    """Commande d'un groupe de lumieres Hue."""

    on: bool | None = None
    brightness: float | None = Field(default=None, ge=0, le=100)
    color_temp_mirek: int | None = Field(default=None, ge=153, le=500)


# ---------------------------------------------------------------------------
# Matter
# ---------------------------------------------------------------------------


class CommissionRequest(BaseModel):
    """Appairage d'un appareil Matter."""

    pairing_code: str = Field(min_length=8, max_length=48)


# ---------------------------------------------------------------------------
# Programmations
# ---------------------------------------------------------------------------


class ScheduleCreate(BaseModel):
    """Creation d'une programmation horaire."""

    name: str = Field(min_length=1, max_length=64)
    target_type: Literal["shutter", "shutter_group", "light"]
    target_id: str = Field(min_length=1, max_length=64)
    action: str = Field(min_length=1, max_length=32)
    time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    days: list[int] = Field(min_length=1, max_length=7)
    enabled: bool = True


class ScheduleOut(BaseModel):
    """Representation d'une programmation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    target_type: str
    target_id: str
    action: str
    time: str
    days: list[int]
    enabled: bool


# ---------------------------------------------------------------------------
# Historique
# ---------------------------------------------------------------------------


class EventLogOut(BaseModel):
    """Entree du journal d'evenements."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    source: str
    event_type: str
    message: str
    payload: dict[str, Any]


class ReadingOut(BaseModel):
    """Point d'historique d'une mesure."""

    model_config = ConfigDict(from_attributes=True)

    metric: str
    value: float
    unit: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# Divers
# ---------------------------------------------------------------------------


class MessageResponse(BaseModel):
    """Reponse generique de confirmation."""

    message: str
