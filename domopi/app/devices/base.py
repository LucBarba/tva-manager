"""Abstractions communes a tous les peripheriques.

Definit le contrat minimal (``Device``) que chaque integration doit
respecter afin que les couches hautes (API, HomeKit, planificateur)
manipulent les appareils de maniere uniforme.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DeviceType(StrEnum):
    """Categories de peripheriques geres par DomoPi."""

    SHUTTER = "shutter"
    LIGHT = "light"
    TEMPERATURE_SENSOR = "temperature_sensor"
    HUMIDITY_SENSOR = "humidity_sensor"
    GENERIC = "generic"


@dataclass(slots=True)
class DeviceState:
    """Instantane d'etat d'un peripherique.

    Attributes:
        online: joignabilite de l'appareil.
        attributes: paires cle/valeur specifiques au type
            (``position``, ``on``, ``brightness``, ``temperature``...).
    """

    online: bool = True
    attributes: dict[str, Any] = field(default_factory=dict)


class Device(ABC):
    """Contrat commun a tous les peripheriques.

    Chaque integration (RF, Hue, Matter) fournit des classes concretes
    qui exposent un identifiant unique, un type, un nom lisible et des
    methodes d'etat/commande asynchrones.
    """

    def __init__(self, uid: str, name: str, device_type: DeviceType, room: str = "") -> None:
        """Initialise les proprietes communes du peripherique.

        Args:
            uid: identifiant unique global (ex. ``shutter:3``, ``hue:abc``).
            name: nom lisible affiche dans l'interface et HomeKit.
            device_type: categorie fonctionnelle.
            room: piece d'appartenance (facultatif).
        """
        self.uid = uid
        self.name = name
        self.device_type = device_type
        self.room = room

    @abstractmethod
    async def get_state(self) -> DeviceState:
        """Retourne l'etat courant du peripherique."""

    @abstractmethod
    async def execute(self, command: str, **kwargs: Any) -> None:
        """Execute une commande (``open``, ``on``, ``set_position``...).

        Args:
            command: nom de la commande, propre au type d'appareil.
            **kwargs: parametres de la commande (position, luminosite...).

        Raises:
            ValidationError: commande inconnue pour ce peripherique.
            DeviceUnavailableError: appareil injoignable.
        """

    def to_dict(self) -> dict[str, Any]:
        """Serialisation legere pour l'API et les WebSockets."""
        return {
            "uid": self.uid,
            "name": self.name,
            "type": self.device_type.value,
            "room": self.room,
        }
