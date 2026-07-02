"""Pont HomeKit de DomoPi.

Expose automatiquement tous les peripheriques du registre dans Apple
Maison via un pont HAP (HomeKit Accessory Protocol). Le pont tourne
dans un thread dedie (HAP-python possede sa propre boucle) et reste
synchronise grace au bus d'evenements :

- ``DEVICE_STATE_CHANGED`` -> mise a jour des caracteristiques HomeKit ;
- ``DEVICE_ADDED`` / ``DEVICE_REMOVED`` -> reconstruction du pont.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from app.core.config import get_settings
from app.core.events import Event, EventType, event_bus
from app.core.logging import get_logger
from app.devices.base import Device, DeviceType
from app.devices.registry import device_registry

logger = get_logger("homekit.bridge")


class HomeKitService:
    """Cycle de vie du pont HomeKit et synchronisation des etats."""

    def __init__(self) -> None:
        """Initialise le service (le pont demarre dans ``start()``)."""
        self._driver: Any = None  # pyhap AccessoryDriver
        self._thread: threading.Thread | None = None
        self._accessories: dict[str, Any] = {}  # uid -> accessoire HAP
        self._loop: asyncio.AbstractEventLoop | None = None

    async def start(self) -> None:
        """Demarre le pont HomeKit dans un thread dedie.

        Ne leve jamais : en cas d'echec (port occupe, bibliotheque
        absente), l'application continue sans HomeKit.
        """
        settings = get_settings()
        if not settings.homekit_enabled:
            logger.info("Pont HomeKit desactive par configuration")
            return
        try:
            # Import paresseux pour ne pas imposer HAP-python aux tests legers
            from pyhap.accessory import Bridge
            from pyhap.accessory_driver import AccessoryDriver
        except ImportError:
            logger.warning("HAP-python absent : pont HomeKit desactive")
            return

        self._loop = asyncio.get_running_loop()
        settings.homekit_state_file.parent.mkdir(parents=True, exist_ok=True)

        def _run_bridge() -> None:
            """Corps du thread HAP : cree le pont puis boucle jusqu'a l'arret."""
            try:
                driver = AccessoryDriver(
                    port=settings.homekit_port,
                    persist_file=str(settings.homekit_state_file),
                    pincode=settings.homekit_pincode.encode("utf-8"),
                )
                bridge = Bridge(driver, settings.homekit_bridge_name)
                for device in device_registry.all():
                    accessory = self._make_accessory(driver, device)
                    if accessory is not None:
                        bridge.add_accessory(accessory)
                        self._accessories[device.uid] = accessory
                driver.add_accessory(accessory=bridge)
                self._driver = driver
                logger.info(
                    "Pont HomeKit demarre (%d accessoire(s), code %s)",
                    len(self._accessories),
                    settings.homekit_pincode,
                )
                driver.start()  # bloquant jusqu'a driver.stop()
            except Exception:
                logger.exception("Le pont HomeKit s'est arrete sur une erreur")

        self._thread = threading.Thread(target=_run_bridge, name="homekit", daemon=True)
        self._thread.start()

        # Synchronisation des etats via le bus d'evenements
        event_bus.subscribe(EventType.DEVICE_STATE_CHANGED, self._on_state_changed)

    async def stop(self) -> None:
        """Arrete proprement le pont HomeKit."""
        event_bus.unsubscribe(EventType.DEVICE_STATE_CHANGED, self._on_state_changed)
        if self._driver is not None:
            self._driver.stop()
            self._driver = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        self._accessories.clear()

    def _make_accessory(self, driver: Any, device: Device) -> Any:
        """Cree l'accessoire HAP adapte au type de peripherique."""
        from app.homekit.accessories import LightAccessory, SensorAccessory, ShutterAccessory

        assert self._loop is not None
        if device.device_type == DeviceType.SHUTTER:
            return ShutterAccessory(driver, device, self._loop)
        if device.device_type == DeviceType.LIGHT:
            return LightAccessory(driver, device, self._loop)
        if device.device_type in {DeviceType.TEMPERATURE_SENSOR, DeviceType.HUMIDITY_SENSOR}:
            return SensorAccessory(driver, device, self._loop)
        return None

    def _on_state_changed(self, event: Event) -> None:
        """Repercute un changement d'etat DomoPi vers Apple Maison."""
        accessory = self._accessories.get(str(event.payload.get("uid", "")))
        attributes = event.payload.get("attributes") or {}
        if accessory is not None and attributes:
            accessory.update_state(attributes)
