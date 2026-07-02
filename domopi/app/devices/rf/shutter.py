"""Peripherique "volet roulant" expose au reste de l'application.

``ShutterDevice`` est une facade legere : il traduit le contrat
generique ``Device`` (utilise par l'API, HomeKit, le planificateur) en
appels au service volets, qui detient le pilote radio et la base.
L'injection du service via le constructeur evite tout import circulaire.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.core.exceptions import ValidationError
from app.devices.base import Device, DeviceState, DeviceType
from app.devices.rf.base import ShutterCommand

if TYPE_CHECKING:  # uniquement pour les annotations, pas d'import runtime
    from app.services.shutter_service import ShutterService


class ShutterDevice(Device):
    """Volet roulant pilote par radiofrequence (RF433 ou Somfy RTS)."""

    def __init__(self, shutter_id: int, name: str, room: str, service: ShutterService) -> None:
        """Cree la facade d'un volet persiste en base.

        Args:
            shutter_id: cle primaire du volet en base.
            name: nom lisible.
            room: piece d'appartenance.
            service: service metier detenant pilote radio et persistance.
        """
        super().__init__(
            uid=f"shutter:{shutter_id}", name=name, device_type=DeviceType.SHUTTER, room=room
        )
        self.shutter_id = shutter_id
        self._service = service

    async def get_state(self) -> DeviceState:
        """Retourne la position estimee du volet (0 = ferme, 100 = ouvert)."""
        shutter = await self._service.get_shutter(self.shutter_id)
        return DeviceState(
            online=True,
            attributes={
                "position": shutter.position,
                "favorite_position": shutter.favorite_position,
                "protocol": shutter.protocol,
            },
        )

    async def execute(self, command: str, **kwargs: Any) -> None:
        """Execute une commande de volet.

        Commandes supportees : ``open``, ``close``, ``stop``,
        ``favorite`` et ``set_position`` (parametre ``position``).
        """
        if command == "set_position":
            position = kwargs.get("position")
            if position is None:
                raise ValidationError("set_position requiert le parametre 'position'")
            await self._service.set_position(self.shutter_id, int(position))
            return
        try:
            shutter_command = ShutterCommand(command)
        except ValueError as exc:
            raise ValidationError(f"Commande de volet inconnue: {command}") from exc
        await self._service.send_command(self.shutter_id, shutter_command)
