"""Client Matter de DomoPi.

S'appuie sur le serveur officiel ``python-matter-server`` (execute en
service dedie sur le Pi, voir ``scripts/install.sh``) auquel ce module
se connecte en WebSocket via la bibliotheque cliente officielle.

Identifiants de clusters Matter utilises pour la lecture des capteurs :
- 0x0402 (1026) TemperatureMeasurement / attribut 0 (centiemes de degC)
- 0x0405 (1029) RelativeHumidityMeasurement / attribut 0 (centiemes de %)
- 0x002F (47)   PowerSource / attribut 12 (batterie, demi-pourcents)
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.exceptions import DeviceUnavailableError, PairingError
from app.core.logging import get_logger

logger = get_logger("matter.client")

# Chemins d'attributs "endpoint/cluster/attribut" (format python-matter-server)
_CLUSTER_TEMPERATURE = 1026
_CLUSTER_HUMIDITY = 1029
_CLUSTER_POWER_SOURCE = 47
_ATTR_MEASURED_VALUE = 0
_ATTR_BATTERY_PERCENT = 12


class MatterController:
    """Facade asynchrone du serveur Matter.

    Toutes les methodes degradent proprement (exception metier claire)
    lorsque le serveur Matter n'est pas disponible, afin que le reste
    de l'application continue de fonctionner.
    """

    def __init__(self, server_url: str) -> None:
        """Prepare le controleur.

        Args:
            server_url: URL WebSocket du serveur Matter
                (ex. ``ws://127.0.0.1:5580/ws``).
        """
        self._server_url = server_url
        self._client: Any = None  # matter_server.client.MatterClient
        self._listen_task: asyncio.Task | None = None
        self.connected = False

    async def connect(self) -> None:
        """Se connecte au serveur Matter et demarre l'ecoute des evenements.

        Raises:
            DeviceUnavailableError: bibliotheque absente ou serveur injoignable.
        """
        try:
            # Import paresseux : la bibliotheque n'est installee que sur le Pi
            from aiohttp import ClientSession
            from matter_server.client import MatterClient
        except ImportError as exc:
            raise DeviceUnavailableError(
                "python-matter-server absent : integration Matter desactivee"
            ) from exc
        try:
            self._session = ClientSession()
            self._client = MatterClient(self._server_url, self._session)
            await self._client.connect()
            # start_listening remplit le cache de noeuds puis ecoute les mises a jour
            ready = asyncio.Event()
            self._listen_task = asyncio.create_task(self._client.start_listening(ready))
            await asyncio.wait_for(ready.wait(), timeout=15)
            self.connected = True
            logger.info("Connecte au serveur Matter (%s)", self._server_url)
        except Exception as exc:
            await self.disconnect()
            raise DeviceUnavailableError(f"Serveur Matter injoignable: {exc}") from exc

    async def disconnect(self) -> None:
        """Ferme proprement la connexion au serveur Matter."""
        self.connected = False
        if self._listen_task is not None:
            self._listen_task.cancel()
            self._listen_task = None
        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception:
                logger.debug("Deconnexion Matter deja effective")
            self._client = None
        session = getattr(self, "_session", None)
        if session is not None:
            await session.close()

    # ------------------------------------------------------------------
    # Appairage et inventaire
    # ------------------------------------------------------------------

    async def commission(self, pairing_code: str) -> int:
        """Appaire un nouvel appareil via son code de mise en service.

        Args:
            pairing_code: code d'appairage (QR ou code numerique).

        Returns:
            L'identifiant du noeud Matter cree.
        """
        self._ensure_connected()
        try:
            node = await self._client.commission_with_code(pairing_code)
            logger.info("Appareil Matter appaire: noeud %s", node.node_id)
            return node.node_id
        except Exception as exc:
            raise PairingError(f"Appairage Matter en echec: {exc}") from exc

    def get_nodes(self) -> list[Any]:
        """Retourne les noeuds Matter connus du serveur."""
        self._ensure_connected()
        return list(self._client.get_nodes())

    # ------------------------------------------------------------------
    # Lecture des capteurs
    # ------------------------------------------------------------------

    def read_sensor_values(self, node: Any) -> dict[str, float]:
        """Extrait temperature, humidite et batterie d'un noeud.

        Args:
            node: noeud retourne par ``get_nodes()`` (attributs caches).

        Returns:
            Dictionnaire ``{"temperature": degC, "humidity": %, "battery": %}``
            ne contenant que les mesures presentes sur l'appareil.
        """
        values: dict[str, float] = {}
        attributes: dict[str, Any] = getattr(node, "attributes", {}) or {}
        for path, raw in attributes.items():
            if raw is None:
                continue
            try:
                _endpoint, cluster, attribute = (int(part) for part in path.split("/"))
            except ValueError:
                continue
            if cluster == _CLUSTER_TEMPERATURE and attribute == _ATTR_MEASURED_VALUE:
                values["temperature"] = round(raw / 100.0, 2)  # centiemes de degC
            elif cluster == _CLUSTER_HUMIDITY and attribute == _ATTR_MEASURED_VALUE:
                values["humidity"] = round(raw / 100.0, 1)  # centiemes de %
            elif cluster == _CLUSTER_POWER_SOURCE and attribute == _ATTR_BATTERY_PERCENT:
                values["battery"] = round(raw / 2.0, 1)  # demi-pourcents
        return values

    def _ensure_connected(self) -> None:
        """Leve une exception claire si le serveur n'est pas connecte."""
        if not self.connected or self._client is None:
            raise DeviceUnavailableError("Serveur Matter non connecte")


class MockMatterController(MatterController):
    """Controleur Matter factice pour le developpement et les tests."""

    def __init__(self) -> None:
        """Initialise un controleur simule avec un capteur factice."""
        super().__init__(server_url="mock://")
        self._mock_values = {"temperature": 21.5, "humidity": 48.0, "battery": 87.0}

    async def connect(self) -> None:
        """Simule une connexion reussie."""
        self.connected = True
        logger.info("MockMatterController connecte")

    async def disconnect(self) -> None:
        """Simule la deconnexion."""
        self.connected = False

    async def commission(self, pairing_code: str) -> int:
        """Simule un appairage reussi."""
        return 1

    def get_nodes(self) -> list[Any]:
        """Retourne un unique noeud simule."""

        class _FakeNode:
            """Noeud Matter factice avec un capteur complet."""

            node_id = 1
            attributes = {"1/1026/0": 2150, "1/1029/0": 4800, "1/47/12": 174}

            @property
            def name(self) -> str:
                """Nom lisible du noeud simule."""
                return "Capteur simule"

        return [_FakeNode()]

    def _ensure_connected(self) -> None:
        """Toujours connecte en mode simulation."""
