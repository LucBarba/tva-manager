"""Accessoires HomeKit exposant les peripheriques DomoPi.

Chaque classe adapte un ``Device`` du registre au profil HomeKit
correspondant :
- volet    -> service ``WindowCovering`` ;
- ampoule  -> service ``Lightbulb`` (variation + temperature de couleur) ;
- capteur  -> services ``TemperatureSensor`` / ``HumiditySensor`` / ``Battery``.

Les callbacks HAP s'executent dans le thread du pont : les commandes
sont renvoyees vers la boucle asyncio principale via
``asyncio.run_coroutine_threadsafe``.
"""

from __future__ import annotations

import asyncio
from typing import Any

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_LIGHTBULB, CATEGORY_SENSOR, CATEGORY_WINDOW_COVERING

from app.core.logging import get_logger
from app.devices.base import Device

logger = get_logger("homekit.accessories")


class _BaseAccessory(Accessory):
    """Socle commun : lie un accessoire HAP a un ``Device`` DomoPi."""

    def __init__(
        self,
        driver: Any,
        device: Device,
        loop: asyncio.AbstractEventLoop,
        **kwargs: Any,
    ) -> None:
        """Initialise l'accessoire.

        Args:
            driver: ``AccessoryDriver`` HAP-python.
            device: peripherique DomoPi adosse.
            loop: boucle asyncio principale (pour les commandes).
        """
        super().__init__(driver, device.name, **kwargs)
        self.device = device
        self._loop = loop

    def _run_command(self, command: str, **kwargs: Any) -> None:
        """Execute une commande du peripherique depuis le thread HAP."""
        future = asyncio.run_coroutine_threadsafe(
            self.device.execute(command, **kwargs), self._loop
        )
        # Journalise les echecs sans bloquer le thread HAP
        future.add_done_callback(self._log_failure)

    @staticmethod
    def _log_failure(future) -> None:  # noqa: ANN001
        """Trace l'exception eventuelle d'une commande asynchrone."""
        exc = future.exception()
        if exc is not None:
            logger.error("Commande HomeKit en echec: %s", exc)


class ShutterAccessory(_BaseAccessory):
    """Volet roulant HomeKit (service WindowCovering)."""

    category = CATEGORY_WINDOW_COVERING

    def __init__(self, driver: Any, device: Device, loop: asyncio.AbstractEventLoop) -> None:
        """Cree le service WindowCovering et ses caracteristiques."""
        super().__init__(driver, device, loop)
        service = self.add_preload_service("WindowCovering")
        self._current = service.configure_char("CurrentPosition", value=100)
        self._target = service.configure_char(
            "TargetPosition", value=100, setter_callback=self._on_target
        )
        self._state = service.configure_char("PositionState", value=2)  # 2 = arrete

    def _on_target(self, value: int) -> None:
        """Callback HomeKit : l'utilisateur demande une position cible."""
        self._run_command("set_position", position=int(value))

    def update_state(self, attributes: dict[str, Any]) -> None:
        """Pousse la position estimee vers Apple Maison."""
        position = attributes.get("position")
        if position is not None:
            self._current.set_value(int(position))
            self._target.set_value(int(position))
            self._state.set_value(2)


class LightAccessory(_BaseAccessory):
    """Ampoule HomeKit (service Lightbulb avec variation et blancs)."""

    category = CATEGORY_LIGHTBULB

    def __init__(self, driver: Any, device: Device, loop: asyncio.AbstractEventLoop) -> None:
        """Cree le service Lightbulb et ses caracteristiques."""
        super().__init__(driver, device, loop)
        service = self.add_preload_service(
            "Lightbulb", chars=["On", "Brightness", "ColorTemperature"]
        )
        self._on = service.configure_char("On", value=False, setter_callback=self._on_power)
        self._brightness = service.configure_char(
            "Brightness", value=100, setter_callback=self._on_brightness
        )
        self._color_temp = service.configure_char(
            "ColorTemperature", value=300, setter_callback=self._on_color_temp
        )

    def _on_power(self, value: bool) -> None:
        """Callback HomeKit : allumage/extinction."""
        self._run_command("on" if value else "off")

    def _on_brightness(self, value: int) -> None:
        """Callback HomeKit : variation de luminosite (0-100)."""
        self._run_command("set_brightness", brightness=float(value))

    def _on_color_temp(self, value: int) -> None:
        """Callback HomeKit : temperature de couleur (mireds)."""
        self._run_command("set_color_temp", mirek=int(value))

    def update_state(self, attributes: dict[str, Any]) -> None:
        """Pousse l'etat de l'ampoule vers Apple Maison."""
        if (on := attributes.get("on")) is not None:
            self._on.set_value(bool(on))
        if (brightness := attributes.get("brightness")) is not None:
            self._brightness.set_value(int(brightness))
        if (mirek := attributes.get("color_temp_mirek")) is not None:
            self._color_temp.set_value(int(mirek))


class SensorAccessory(_BaseAccessory):
    """Capteur HomeKit (temperature, humidite, batterie)."""

    category = CATEGORY_SENSOR

    def __init__(self, driver: Any, device: Device, loop: asyncio.AbstractEventLoop) -> None:
        """Cree les services capteurs."""
        super().__init__(driver, device, loop)
        temp_service = self.add_preload_service("TemperatureSensor")
        self._temperature = temp_service.configure_char("CurrentTemperature", value=0.0)
        humidity_service = self.add_preload_service("HumiditySensor")
        self._humidity = humidity_service.configure_char("CurrentRelativeHumidity", value=0.0)
        battery_service = self.add_preload_service("BatteryService")
        self._battery = battery_service.configure_char("BatteryLevel", value=100)
        self._low_battery = battery_service.configure_char("StatusLowBattery", value=0)

    def update_state(self, attributes: dict[str, Any]) -> None:
        """Pousse les mesures vers Apple Maison."""
        if (temperature := attributes.get("temperature")) is not None:
            self._temperature.set_value(float(temperature))
        if (humidity := attributes.get("humidity")) is not None:
            self._humidity.set_value(float(humidity))
        if (battery := attributes.get("battery")) is not None:
            self._battery.set_value(int(battery))
            self._low_battery.set_value(1 if battery < 15 else 0)
