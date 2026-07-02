"""Service metier Matter.

Connecte le controleur Matter, synchronise les capteurs dans le
registre de peripheriques et historise periodiquement les mesures
(temperature, humidite, batterie) en base de donnees.
"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.events import Event, EventType, event_bus
from app.core.exceptions import DeviceUnavailableError
from app.core.logging import get_logger
from app.database.engine import session_scope
from app.database.models import SensorReading
from app.devices.matter.client import MatterController, MockMatterController
from app.devices.matter.sensor import MatterSensorDevice
from app.devices.registry import device_registry

logger = get_logger("matter.service")

# Unites associees aux metriques historisees
_UNITS = {"temperature": "°C", "humidity": "%", "battery": "%"}

# Intervalle de releve des capteurs (secondes)
_POLL_INTERVAL_S = 60.0


class MatterService:
    """Facade metier de l'integration Matter."""

    def __init__(self, controller: MatterController | None = None) -> None:
        """Initialise le service.

        Args:
            controller: controleur a utiliser ; par defaut, le controleur
                reel est cree (ou un mock si le pilote RF est en mode mock,
                signe d'un environnement de developpement).
        """
        settings = get_settings()
        if controller is not None:
            self._controller = controller
        elif settings.rf_driver == "mock":
            self._controller = MockMatterController()
        else:
            self._controller = MatterController(settings.matter_server_url)
        self._poll_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Cycle de vie
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Connecte le serveur Matter et demarre l'historisation.

        Ne leve jamais : si le serveur est absent, l'integration reste
        inactive et pourra etre relancee.
        """
        if not get_settings().matter_enabled:
            logger.info("Integration Matter desactivee par configuration")
            return
        try:
            await self._controller.connect()
        except DeviceUnavailableError as exc:
            logger.warning("Matter indisponible: %s", exc)
            return
        await self.refresh_devices()
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("Integration Matter demarree")

    async def stop(self) -> None:
        """Arrete l'historisation et deconnecte le controleur."""
        if self._poll_task is not None:
            self._poll_task.cancel()
            self._poll_task = None
        await self._controller.disconnect()

    # ------------------------------------------------------------------
    # Appairage et synchronisation
    # ------------------------------------------------------------------

    async def commission(self, pairing_code: str) -> int:
        """Appaire un nouvel appareil Matter puis synchronise le registre."""
        node_id = await self._controller.commission(pairing_code)
        await self.refresh_devices()
        return node_id

    async def refresh_devices(self) -> None:
        """Synchronise les noeuds Matter vers le registre de peripheriques."""
        for node in self._controller.get_nodes():
            node_id = getattr(node, "node_id", 0)
            uid = f"matter:{node_id}"
            name = getattr(node, "name", None) or f"Capteur Matter {node_id}"
            existing = next((d for d in device_registry.all() if d.uid == uid), None)
            if not isinstance(existing, MatterSensorDevice):
                existing = MatterSensorDevice(node_id, name)
                device_registry.register(existing)
                await event_bus.publish(Event(EventType.DEVICE_ADDED, {"uid": uid}))
            existing.update_values(self._controller.read_sensor_values(node))

    # ------------------------------------------------------------------
    # Historisation
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        """Releve periodiquement les capteurs et historise les mesures."""
        while True:
            try:
                await self._poll_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Erreur pendant le releve Matter")
            await asyncio.sleep(_POLL_INTERVAL_S)

    async def _poll_once(self) -> None:
        """Effectue un releve unique de tous les noeuds."""
        for node in self._controller.get_nodes():
            node_id = getattr(node, "node_id", 0)
            uid = f"matter:{node_id}"
            values = self._controller.read_sensor_values(node)
            if not values:
                continue
            # Met a jour le peripherique en registre
            try:
                device = device_registry.get(uid)
                if isinstance(device, MatterSensorDevice):
                    device.update_values(values)
            except Exception:
                pass
            # Historise chaque metrique
            with session_scope() as session:
                for metric, value in values.items():
                    session.add(
                        SensorReading(
                            device_uid=uid,
                            metric=metric,
                            value=value,
                            unit=_UNITS.get(metric, ""),
                        )
                    )
            await event_bus.publish(
                Event(EventType.DEVICE_STATE_CHANGED, {"uid": uid, "attributes": values})
            )
