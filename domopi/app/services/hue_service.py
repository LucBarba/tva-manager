"""Service metier Philips Hue.

Gere le cycle de vie du client (decouverte, appairage, persistance de
la cle d'application), synchronise les ampoules dans le registre de
peripheriques et expose pieces, scenes, groupes et commandes.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.config import get_settings
from app.core.events import Event, EventType, event_bus
from app.core.exceptions import DeviceUnavailableError, PairingError
from app.core.logging import get_logger
from app.database.engine import session_scope
from app.database.models import Setting
from app.devices.hue.client import HueClient, discover_bridge
from app.devices.hue.light import HueLightDevice
from app.devices.registry import device_registry

logger = get_logger("hue.service")

# Cles de persistance dans la table settings
_KEY_BRIDGE_IP = "hue.bridge_ip"
_KEY_APP_KEY = "hue.app_key"

# Intervalle de rafraichissement des etats (secondes)
_POLL_INTERVAL_S = 10.0


class HueService:
    """Facade metier de l'integration Philips Hue."""

    def __init__(self) -> None:
        """Initialise le service (client cree au demarrage)."""
        self._client: HueClient | None = None
        self._poll_task: asyncio.Task | None = None
        # Correspondance identifiant ampoule -> nom de piece
        self._light_rooms: dict[str, str] = {}

    @property
    def is_paired(self) -> bool:
        """Indique si un pont est appaire et joignable."""
        return self._client is not None and bool(self._client.app_key)

    # ------------------------------------------------------------------
    # Cycle de vie
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Demarre l'integration : decouverte, connexion, synchronisation.

        Ne leve jamais : en cas d'absence de pont, l'integration reste
        en attente d'un appairage manuel via l'API.
        """
        settings = get_settings()
        if not settings.hue_enabled:
            logger.info("Integration Hue desactivee par configuration")
            return
        bridge_ip = settings.hue_bridge_ip or self._load_setting(_KEY_BRIDGE_IP)
        app_key = settings.hue_app_key or self._load_setting(_KEY_APP_KEY)
        if not bridge_ip:
            bridge_ip = await discover_bridge() or ""
            if bridge_ip:
                self._save_setting(_KEY_BRIDGE_IP, bridge_ip)
        if not bridge_ip:
            logger.warning("Aucun pont Hue trouve : appairage a lancer depuis l'interface")
            return
        self._client = HueClient(bridge_ip, app_key)
        if app_key:
            try:
                await self.refresh_devices()
                self._poll_task = asyncio.create_task(self._poll_loop())
                logger.info("Integration Hue demarree (pont %s)", bridge_ip)
            except DeviceUnavailableError:
                logger.warning("Pont Hue configure mais injoignable pour le moment")

    async def stop(self) -> None:
        """Arrete la boucle de rafraichissement et ferme le client."""
        if self._poll_task is not None:
            self._poll_task.cancel()
            self._poll_task = None
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def pair(self) -> str:
        """Appaire l'application au pont (bouton presse au prealable).

        Returns:
            La cle d'application creee (egalement persistee en base).
        """
        if self._client is None:
            bridge_ip = await discover_bridge()
            if not bridge_ip:
                raise PairingError("Aucun pont Hue detecte sur le reseau")
            self._save_setting(_KEY_BRIDGE_IP, bridge_ip)
            self._client = HueClient(bridge_ip)
        app_key = await self._client.pair()
        self._save_setting(_KEY_APP_KEY, app_key)
        await self.refresh_devices()
        if self._poll_task is None:
            self._poll_task = asyncio.create_task(self._poll_loop())
        return app_key

    # ------------------------------------------------------------------
    # Synchronisation du registre
    # ------------------------------------------------------------------

    async def refresh_devices(self) -> None:
        """Synchronise ampoules et pieces du pont vers le registre."""
        client = self._require_client()
        rooms = await client.get_rooms()
        # Associe chaque appareil enfant d'une piece au nom de la piece
        self._light_rooms = {}
        for room in rooms:
            room_name = room.get("metadata", {}).get("name", "")
            for child in room.get("children", []):
                self._light_rooms[child.get("rid", "")] = room_name

        for raw in await client.get_lights():
            light_id = raw["id"]
            name = raw.get("metadata", {}).get("name", f"Lampe {light_id[:8]}")
            owner = raw.get("owner", {}).get("rid", "")
            room_name = self._light_rooms.get(owner, "")
            uid = f"hue:{light_id}"
            existing = next((d for d in device_registry.all() if d.uid == uid), None)
            if isinstance(existing, HueLightDevice):
                existing.update_cache(raw)
            else:
                device = HueLightDevice(light_id, name, room_name, client)
                device.update_cache(raw)
                device_registry.register(device)
                await event_bus.publish(Event(EventType.DEVICE_ADDED, {"uid": uid}))

    async def _poll_loop(self) -> None:
        """Rafraichit periodiquement l'etat des ampoules et notifie le bus."""
        while True:
            await asyncio.sleep(_POLL_INTERVAL_S)
            try:
                client = self._require_client()
                for raw in await client.get_lights():
                    uid = f"hue:{raw['id']}"
                    try:
                        device = device_registry.get(uid)
                    except Exception:
                        continue
                    if isinstance(device, HueLightDevice):
                        previous = dict(device._cached)
                        device.update_cache(raw)
                        if device._cached != previous:
                            await event_bus.publish(
                                Event(
                                    EventType.DEVICE_STATE_CHANGED,
                                    {"uid": uid, "attributes": dict(device._cached)},
                                )
                            )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Erreur pendant le rafraichissement Hue")

    # ------------------------------------------------------------------
    # Ressources et commandes de haut niveau
    # ------------------------------------------------------------------

    async def get_rooms(self) -> list[dict[str, Any]]:
        """Retourne les pieces du pont (id, nom, groupe de lumieres)."""
        client = self._require_client()
        rooms = []
        for raw in await client.get_rooms():
            grouped = next(
                (
                    service["rid"]
                    for service in raw.get("services", [])
                    if service.get("rtype") == "grouped_light"
                ),
                None,
            )
            rooms.append(
                {
                    "id": raw["id"],
                    "name": raw.get("metadata", {}).get("name", ""),
                    "grouped_light_id": grouped,
                }
            )
        return rooms

    async def get_scenes(self) -> list[dict[str, Any]]:
        """Retourne les scenes du pont (id, nom, piece associee)."""
        client = self._require_client()
        return [
            {
                "id": raw["id"],
                "name": raw.get("metadata", {}).get("name", ""),
                "group_rid": raw.get("group", {}).get("rid"),
            }
            for raw in await client.get_scenes()
        ]

    async def activate_scene(self, scene_id: str) -> None:
        """Active une scene sur le pont."""
        await self._require_client().activate_scene(scene_id)

    async def set_group(
        self,
        grouped_light_id: str,
        on: bool | None = None,
        brightness: float | None = None,
        color_temp_mirek: int | None = None,
    ) -> None:
        """Commande un groupe de lumieres (piece entiere)."""
        await self._require_client().set_grouped_light(
            grouped_light_id, on=on, brightness=brightness, color_temp_mirek=color_temp_mirek
        )

    def _require_client(self) -> HueClient:
        """Retourne le client ou leve une erreur claire."""
        if self._client is None:
            raise DeviceUnavailableError("Pont Hue non configure ou non appaire")
        return self._client

    # ------------------------------------------------------------------
    # Persistance des parametres
    # ------------------------------------------------------------------

    @staticmethod
    def _load_setting(key: str) -> str:
        """Lit un parametre persiste (chaine vide si absent)."""
        with session_scope() as session:
            setting = session.get(Setting, key)
            return setting.value if setting else ""

    @staticmethod
    def _save_setting(key: str, value: str) -> None:
        """Ecrit un parametre persiste (upsert)."""
        with session_scope() as session:
            setting = session.get(Setting, key)
            if setting is None:
                session.add(Setting(key=key, value=value))
            else:
                setting.value = value
