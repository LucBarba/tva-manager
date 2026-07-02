"""Modeles SQLAlchemy de DomoPi.

Tables : utilisateurs, volets et groupes, codes RF, programmations
horaires, journal d'evenements, historique de mesures et parametres
persistants (cle Hue, cache Matter...).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Horodatage UTC courant (fonction nommee pour SQLAlchemy)."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Classe de base declarative commune a tous les modeles."""


# Table d'association N-N entre volets et groupes de volets
shutter_group_members = Table(
    "shutter_group_members",
    Base.metadata,
    Column("group_id", ForeignKey("shutter_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("shutter_id", ForeignKey("shutters.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    """Utilisateur de l'interface Web et de l'API."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(16), default="user")  # admin | user
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Shutter(Base):
    """Volet roulant radiocommande (RF433 brut ou Somfy RTS).

    Pour Somfy RTS : ``address`` identifie la telecommande virtuelle et
    ``rolling_code`` est incremente a chaque trame emise.
    Pour RF433 brut : ``rf_codes`` contient les codes appris par action
    (``open``, ``close``, ``stop``, ``favorite``).
    """

    __tablename__ = "shutters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    room: Mapped[str] = mapped_column(String(64), default="")
    protocol: Mapped[str] = mapped_column(String(16), default="rf433")  # rf433 | somfy_rts
    # --- Somfy RTS ---
    address: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)
    rolling_code: Mapped[int] = mapped_column(Integer, default=1)
    # --- RF433 brut : {"open": {"code":..., "protocol":..., "pulselength":...}, ...}
    rf_codes: Mapped[dict] = mapped_column(JSON, default=dict)
    # Derniere position connue (0 = ferme, 100 = ouvert), estimee
    position: Mapped[int] = mapped_column(Integer, default=100)
    favorite_position: Mapped[int] = mapped_column(Integer, default=50)
    # Duree de course complete en secondes (estimation de position)
    travel_time_s: Mapped[float] = mapped_column(Float, default=20.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    groups: Mapped[list[ShutterGroup]] = relationship(
        secondary=shutter_group_members, back_populates="shutters"
    )


class ShutterGroup(Base):
    """Groupe logique de volets pilotables d'une seule commande."""

    __tablename__ = "shutter_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    shutters: Mapped[list[Shutter]] = relationship(
        secondary=shutter_group_members, back_populates="groups"
    )


class Schedule(Base):
    """Programmation horaire d'une action sur un appareil ou un groupe.

    ``days`` est une liste de jours ISO (1 = lundi ... 7 = dimanche).
    ``target_type`` vaut ``shutter``, ``shutter_group`` ou ``light``.
    """

    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str] = mapped_column(String(16))
    target_id: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(32))  # open, close, stop, favorite, on, off
    time: Mapped[str] = mapped_column(String(5))  # "HH:MM"
    days: Mapped[list] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EventLog(Base):
    """Journal d'evenements consultable depuis l'interface Web."""

    __tablename__ = "event_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    source: Mapped[str] = mapped_column(String(32))  # rf, hue, matter, homekit, web...
    event_type: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class SensorReading(Base):
    """Historique des mesures (temperature, humidite, batterie...)."""

    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_uid: Mapped[str] = mapped_column(String(64), index=True)
    metric: Mapped[str] = mapped_column(String(32))  # temperature | humidity | battery
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(8), default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Setting(Base):
    """Parametre persistant cle/valeur (cle d'application Hue, etc.)."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
