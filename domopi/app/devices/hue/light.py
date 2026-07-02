"""Peripherique "ampoule Hue" expose au reste de l'application."""

from __future__ import annotations

from typing import Any

from app.core.exceptions import ValidationError
from app.devices.base import Device, DeviceState, DeviceType
from app.devices.hue.client import HueClient


class HueLightDevice(Device):
    """Ampoule Philips Hue conforme au contrat ``Device``."""

    def __init__(self, light_id: str, name: str, room: str, client: HueClient) -> None:
        """Cree la facade d'une ampoule du pont.

        Args:
            light_id: identifiant CLIP v2 de l'ampoule.
            name: nom lisible.
            room: piece d'appartenance.
            client: client partage du pont Hue.
        """
        super().__init__(uid=f"hue:{light_id}", name=name, device_type=DeviceType.LIGHT, room=room)
        self.light_id = light_id
        self._client = client
        # Cache du dernier etat connu, rafraichi par le service Hue
        self._cached: dict[str, Any] = {}

    def update_cache(self, raw: dict[str, Any]) -> None:
        """Met a jour le cache d'etat depuis une ressource CLIP v2 brute."""
        self._cached = {
            "on": raw.get("on", {}).get("on", False),
            "brightness": raw.get("dimming", {}).get("brightness"),
            "color_temp_mirek": raw.get("color_temperature", {}).get("mirek"),
        }

    async def get_state(self) -> DeviceState:
        """Retourne le dernier etat connu de l'ampoule."""
        return DeviceState(online=True, attributes=dict(self._cached))

    async def execute(self, command: str, **kwargs: Any) -> None:
        """Execute une commande d'eclairage.

        Commandes : ``on``, ``off``, ``set_brightness`` (``brightness``),
        ``set_color_temp`` (``mirek``), ``set_effect`` (``effect``).
        """
        if command == "on":
            await self._client.set_light(self.light_id, on=True)
            self._cached["on"] = True
        elif command == "off":
            await self._client.set_light(self.light_id, on=False)
            self._cached["on"] = False
        elif command == "set_brightness":
            brightness = float(kwargs["brightness"])
            await self._client.set_light(self.light_id, on=brightness > 0, brightness=brightness)
            self._cached["on"] = brightness > 0
            self._cached["brightness"] = brightness
        elif command == "set_color_temp":
            mirek = int(kwargs["mirek"])
            await self._client.set_light(self.light_id, color_temp_mirek=mirek)
            self._cached["color_temp_mirek"] = mirek
        elif command == "set_effect":
            await self._client.set_light(self.light_id, effect=str(kwargs["effect"]))
        else:
            raise ValidationError(f"Commande Hue inconnue: {command}")
