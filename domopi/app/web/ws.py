"""WebSocket temps reel de l'interface Web.

Chaque client connecte (et authentifie via le cookie de session)
recoit les changements d'etat des peripheriques au format JSON, ce qui
permet au tableau de bord de se mettre a jour sans rechargement.
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.events import Event, EventType, event_bus
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger
from app.core.security import decode_token

logger = get_logger("web.ws")

ws_router = APIRouter()


class ConnectionManager:
    """Suivi des clients WebSocket connectes et diffusion des messages."""

    def __init__(self) -> None:
        """Initialise la liste des connexions actives."""
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accepte et memorise une connexion."""
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Oublie une connexion fermee."""
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        """Diffuse un message JSON a tous les clients connectes."""
        data = json.dumps(message, default=str)
        for websocket in list(self._connections):
            try:
                await websocket.send_text(data)
            except Exception:
                self.disconnect(websocket)


manager = ConnectionManager()


async def _forward_event(event: Event) -> None:
    """Relaye un evenement du bus vers tous les clients WebSocket."""
    await manager.broadcast(
        {"type": event.type.value, "payload": event.payload, "timestamp": event.timestamp}
    )


# Evenements pousses vers les navigateurs
for _event_type in (
    EventType.DEVICE_STATE_CHANGED,
    EventType.DEVICE_ADDED,
    EventType.DEVICE_REMOVED,
    EventType.SCHEDULE_TRIGGERED,
):
    event_bus.subscribe(_event_type, _forward_event)


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Point d'entree WebSocket (authentification par cookie de session)."""
    token = websocket.cookies.get("access_token", "")
    try:
        decode_token(token, expected_type="access")
    except AuthenticationError:
        await websocket.close(code=4401, reason="Authentification requise")
        return
    await manager.connect(websocket)
    logger.info("Client WebSocket connecte (%d actifs)", len(manager._connections))
    try:
        while True:
            # Les clients n'envoient rien d'utile : simple keep-alive
            await asyncio.wait_for(websocket.receive_text(), timeout=300)
    except (WebSocketDisconnect, TimeoutError):
        manager.disconnect(websocket)
