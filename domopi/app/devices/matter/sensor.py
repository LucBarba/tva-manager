"""Peripheriques "capteurs Matter" exposes au reste de l'application."""

from __future__ import annotations

from typing import Any

from app.core.exceptions import ValidationError
from app.devices.base import Device, DeviceState, DeviceType


class MatterSensorDevice(Device):
    """Capteur Matter (temperature, humidite, batterie).

    L'etat est un cache mis a jour periodiquement par le service Matter
    (les capteurs sur pile ne sont pas interrogeables en continu).
    """

    def __init__(self, node_id: int, name: str, room: str = "") -> None:
        """Cree la facade d'un noeud capteur.

        Args:
            node_id: identifiant du noeud Matter.
            name: nom lisible.
            room: piece d'appartenance.
        """
        super().__init__(
            uid=f"matter:{node_id}",
            name=name,
            device_type=DeviceType.TEMPERATURE_SENSOR,
            room=room,
        )
        self.node_id = node_id
        self._values: dict[str, float] = {}

    def update_values(self, values: dict[str, float]) -> None:
        """Met a jour le cache de mesures (appele par le service Matter)."""
        self._values.update(values)

    async def get_state(self) -> DeviceState:
        """Retourne les dernieres mesures connues."""
        return DeviceState(online=bool(self._values), attributes=dict(self._values))

    async def execute(self, command: str, **kwargs: Any) -> None:
        """Les capteurs n'acceptent aucune commande (lecture seule)."""
        raise ValidationError(f"Un capteur Matter n'accepte pas de commande ({command})")
