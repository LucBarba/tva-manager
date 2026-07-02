"""Service d'historique et de journal d'evenements.

S'abonne au bus d'evenements pour persister automatiquement le journal
(commandes, connexions, appairages) et expose les requetes de
consultation pour l'interface Web et l'API.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.events import Event, EventType, event_bus
from app.core.logging import get_logger
from app.database.engine import session_scope
from app.database.models import EventLog, SensorReading

logger = get_logger("web.history")

# Evenements du bus persistes dans le journal
_LOGGED_EVENTS = [
    EventType.DEVICE_ADDED,
    EventType.DEVICE_REMOVED,
    EventType.DEVICE_STATE_CHANGED,
    EventType.SCHEDULE_TRIGGERED,
    EventType.RF_CODE_LEARNED,
    EventType.USER_LOGIN,
    EventType.SYSTEM,
]


class HistoryService:
    """Persistance et consultation du journal et des mesures."""

    def start(self) -> None:
        """Abonne le service aux evenements a journaliser."""
        for event_type in _LOGGED_EVENTS:
            event_bus.subscribe(event_type, self._on_event)
        logger.info("Journalisation des evenements active")

    def _on_event(self, event: Event) -> None:
        """Persiste un evenement du bus dans le journal."""
        source = str(event.payload.get("uid", "")).split(":")[0] or "system"
        with session_scope() as session:
            session.add(
                EventLog(
                    source=source,
                    event_type=event.type.value,
                    message=self._describe(event),
                    payload=dict(event.payload),
                )
            )

    @staticmethod
    def _describe(event: Event) -> str:
        """Construit un message lisible pour le journal."""
        uid = event.payload.get("uid", "")
        command = event.payload.get("command")
        if command:
            return f"{uid}: commande '{command}'"
        if event.type == EventType.USER_LOGIN:
            return f"Connexion de {event.payload.get('username', '?')}"
        return uid or event.type.value

    # ------------------------------------------------------------------
    # Consultation
    # ------------------------------------------------------------------

    def get_events(
        self, limit: int = 100, source: str | None = None, event_type: str | None = None
    ) -> list[EventLog]:
        """Retourne les derniers evenements du journal (filtrables)."""
        with session_scope() as session:
            query = session.query(EventLog).order_by(EventLog.timestamp.desc())
            if source:
                query = query.filter(EventLog.source == source)
            if event_type:
                query = query.filter(EventLog.event_type == event_type)
            return list(query.limit(min(limit, 500)).all())

    def get_readings(
        self, device_uid: str, metric: str = "temperature", hours: int = 24
    ) -> list[SensorReading]:
        """Retourne l'historique d'une mesure sur une fenetre glissante."""
        since = datetime.now(UTC) - timedelta(hours=min(hours, 24 * 31))
        with session_scope() as session:
            return list(
                session.query(SensorReading)
                .filter(
                    SensorReading.device_uid == device_uid,
                    SensorReading.metric == metric,
                    SensorReading.timestamp >= since,
                )
                .order_by(SensorReading.timestamp.asc())
                .all()
            )

    def purge(self, days: int = 90) -> int:
        """Supprime les donnees plus anciennes que ``days`` jours.

        Returns:
            Nombre total de lignes supprimees.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        with session_scope() as session:
            deleted = (
                session.query(EventLog).filter(EventLog.timestamp < cutoff).delete()
                + session.query(SensorReading).filter(SensorReading.timestamp < cutoff).delete()
            )
        logger.info("Purge de l'historique: %d lignes supprimees", deleted)
        return deleted
