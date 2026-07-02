"""Registre central des peripheriques.

Point d'acces unique ou chaque integration enregistre ses appareils.
Les couches hautes (API, HomeKit, planificateur) interrogent le
registre sans connaitre les integrations sous-jacentes.
"""

from __future__ import annotations

from app.core.exceptions import DeviceNotFoundError
from app.core.logging import get_logger
from app.devices.base import Device, DeviceType

logger = get_logger("devices.registry")


class DeviceRegistry:
    """Annuaire en memoire des peripheriques actifs."""

    def __init__(self) -> None:
        """Initialise un registre vide."""
        self._devices: dict[str, Device] = {}

    def register(self, device: Device) -> None:
        """Ajoute ou remplace un peripherique dans le registre."""
        self._devices[device.uid] = device
        logger.info("Peripherique enregistre: %s (%s)", device.uid, device.name)

    def unregister(self, uid: str) -> None:
        """Retire un peripherique (silencieux s'il est absent)."""
        if self._devices.pop(uid, None) is not None:
            logger.info("Peripherique retire: %s", uid)

    def get(self, uid: str) -> Device:
        """Retourne le peripherique ``uid`` ou leve ``DeviceNotFoundError``."""
        try:
            return self._devices[uid]
        except KeyError as exc:
            raise DeviceNotFoundError(f"Peripherique inconnu: {uid}") from exc

    def all(self) -> list[Device]:
        """Retourne tous les peripheriques enregistres."""
        return list(self._devices.values())

    def by_type(self, device_type: DeviceType) -> list[Device]:
        """Filtre les peripheriques par categorie."""
        return [d for d in self._devices.values() if d.device_type == device_type]

    def clear(self) -> None:
        """Vide le registre (utilise par les tests et le rechargement)."""
        self._devices.clear()


# Instance globale unique
device_registry = DeviceRegistry()
