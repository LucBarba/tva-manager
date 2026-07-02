"""Client HTTP du pont Philips Hue (API CLIP v2).

Fonctions couvertes : decouverte automatique du pont (mDNS puis service
cloud Philips), appairage (creation d'une cle d'application), lecture
des pieces/ampoules/scenes/groupes et envoi des commandes (allumage,
variation, temperature de couleur, scenes, effets).

Le pont expose une API HTTPS avec certificat auto-signe : la
verification TLS est desactivee pour ces requetes locales, conformement
aux recommandations Philips pour les clients locaux.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.core.exceptions import DeviceUnavailableError, PairingError
from app.core.logging import get_logger

logger = get_logger("hue.client")

# Service de decouverte cloud officiel (fallback si mDNS echoue)
_DISCOVERY_URL = "https://discovery.meethue.com/"
_MDNS_SERVICE = "_hue._tcp.local."


async def discover_bridge(timeout_s: float = 5.0) -> str | None:
    """Recherche l'adresse IP du pont Hue sur le reseau local.

    Essaie d'abord mDNS (zeroconf), puis le service de decouverte cloud
    de Philips si aucune reponse locale.

    Returns:
        L'adresse IP du pont, ou ``None`` si aucun pont n'est trouve.
    """
    ip = await _discover_mdns(timeout_s)
    if ip:
        logger.info("Pont Hue decouvert via mDNS: %s", ip)
        return ip
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.get(_DISCOVERY_URL)
            response.raise_for_status()
            bridges = response.json()
            if bridges:
                ip = bridges[0]["internalipaddress"]
                logger.info("Pont Hue decouvert via le cloud: %s", ip)
                return ip
    except (httpx.HTTPError, KeyError, ValueError):
        logger.warning("Decouverte cloud du pont Hue impossible")
    return None


async def _discover_mdns(timeout_s: float) -> str | None:
    """Decouverte mDNS du pont (service ``_hue._tcp.local.``)."""
    try:
        from zeroconf import ServiceBrowser, Zeroconf
    except ImportError:
        return None

    found: asyncio.Queue[str] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    class _Listener:
        """Recueille la premiere adresse annoncee par un pont Hue."""

        def add_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
            """Callback zeroconf : resout l'adresse du service decouvert."""
            info = zc.get_service_info(service_type, name, timeout=2000)
            if info and info.addresses:
                address = ".".join(str(b) for b in info.addresses[0])
                loop.call_soon_threadsafe(found.put_nowait, address)

        def update_service(self, *args: Any) -> None:
            """Callback requis par zeroconf (aucune action)."""

        def remove_service(self, *args: Any) -> None:
            """Callback requis par zeroconf (aucune action)."""

    zeroconf = Zeroconf()
    browser = ServiceBrowser(zeroconf, _MDNS_SERVICE, _Listener())
    try:
        return await asyncio.wait_for(found.get(), timeout=timeout_s)
    except TimeoutError:
        return None
    finally:
        browser.cancel()
        zeroconf.close()


class HueClient:
    """Client asynchrone du pont Hue (une instance par pont)."""

    def __init__(self, bridge_ip: str, app_key: str = "") -> None:
        """Prepare le client.

        Args:
            bridge_ip: adresse IP du pont.
            app_key: cle d'application obtenue lors de l'appairage
                (vide tant que l'appairage n'a pas eu lieu).
        """
        self.bridge_ip = bridge_ip
        self.app_key = app_key
        # Certificat auto-signe du pont : verification TLS desactivee
        self._http = httpx.AsyncClient(base_url=f"https://{bridge_ip}", verify=False, timeout=10.0)

    async def close(self) -> None:
        """Ferme la connexion HTTP."""
        await self._http.aclose()

    # ------------------------------------------------------------------
    # Appairage
    # ------------------------------------------------------------------

    async def pair(self, app_name: str = "domopi#raspberry") -> str:
        """Cree une cle d'application (bouton du pont presse au prealable).

        Returns:
            La cle d'application a persister.

        Raises:
            PairingError: bouton non presse ou pont injoignable.
        """
        try:
            response = await self._http.post("/api", json={"devicetype": app_name})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PairingError(f"Pont Hue injoignable: {exc}") from exc
        payload = response.json()[0]
        if "error" in payload:
            raise PairingError(
                "Appairage refuse : appuyer sur le bouton central du pont puis reessayer"
            )
        self.app_key = payload["success"]["username"]
        logger.info("Appairage Hue reussi")
        return self.app_key

    # ------------------------------------------------------------------
    # Lecture des ressources (API CLIP v2)
    # ------------------------------------------------------------------

    async def _get(self, resource: str) -> list[dict[str, Any]]:
        """GET generique sur ``/clip/v2/resource/{resource}``."""
        if not self.app_key:
            raise DeviceUnavailableError("Pont Hue non appaire (cle d'application absente)")
        try:
            response = await self._http.get(
                f"/clip/v2/resource/{resource}",
                headers={"hue-application-key": self.app_key},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise DeviceUnavailableError(f"Pont Hue injoignable: {exc}") from exc
        return response.json().get("data", [])

    async def _put(self, resource: str, rid: str, body: dict[str, Any]) -> None:
        """PUT generique sur une ressource identifiee."""
        if not self.app_key:
            raise DeviceUnavailableError("Pont Hue non appaire (cle d'application absente)")
        try:
            response = await self._http.put(
                f"/clip/v2/resource/{resource}/{rid}",
                headers={"hue-application-key": self.app_key},
                json=body,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise DeviceUnavailableError(f"Commande Hue en echec: {exc}") from exc

    async def get_lights(self) -> list[dict[str, Any]]:
        """Retourne toutes les ampoules du pont."""
        return await self._get("light")

    async def get_rooms(self) -> list[dict[str, Any]]:
        """Retourne toutes les pieces declarees sur le pont."""
        return await self._get("room")

    async def get_scenes(self) -> list[dict[str, Any]]:
        """Retourne toutes les scenes."""
        return await self._get("scene")

    async def get_grouped_lights(self) -> list[dict[str, Any]]:
        """Retourne les groupes de lumieres (pieces/zones agregees)."""
        return await self._get("grouped_light")

    # ------------------------------------------------------------------
    # Commandes
    # ------------------------------------------------------------------

    async def set_light(
        self,
        light_id: str,
        on: bool | None = None,
        brightness: float | None = None,
        color_temp_mirek: int | None = None,
        effect: str | None = None,
    ) -> None:
        """Commande une ampoule.

        Args:
            light_id: identifiant v2 de l'ampoule.
            on: allumage/extinction.
            brightness: luminosite 0-100.
            color_temp_mirek: temperature de couleur en mireds (153-500).
            effect: effet lumineux (``candle``, ``fire``, ``no_effect``...).
        """
        body = self._build_light_body(on, brightness, color_temp_mirek, effect)
        await self._put("light", light_id, body)

    async def set_grouped_light(
        self,
        group_id: str,
        on: bool | None = None,
        brightness: float | None = None,
        color_temp_mirek: int | None = None,
    ) -> None:
        """Commande un groupe de lumieres (piece ou zone entiere)."""
        body = self._build_light_body(on, brightness, color_temp_mirek, None)
        await self._put("grouped_light", group_id, body)

    async def activate_scene(self, scene_id: str) -> None:
        """Active une scene enregistree sur le pont."""
        await self._put("scene", scene_id, {"recall": {"action": "active"}})

    @staticmethod
    def _build_light_body(
        on: bool | None,
        brightness: float | None,
        color_temp_mirek: int | None,
        effect: str | None,
    ) -> dict[str, Any]:
        """Assemble le corps JSON d'une commande lumiere CLIP v2."""
        body: dict[str, Any] = {}
        if on is not None:
            body["on"] = {"on": on}
        if brightness is not None:
            # L'API v2 attend une luminosite entre 0 et 100
            body["dimming"] = {"brightness": max(0.0, min(100.0, brightness))}
        if color_temp_mirek is not None:
            body["color_temperature"] = {"mirek": max(153, min(500, color_temp_mirek))}
        if effect is not None:
            body["effects"] = {"effect": effect}
        return body
