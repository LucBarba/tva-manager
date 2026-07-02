"""Bus d'evenements asynchrone de DomoPi.

Implemente un pattern Publish/Subscribe minimaliste permettant de
decoupler les producteurs d'etats (pilotes RF, Hue, Matter) des
consommateurs (pont HomeKit, WebSocket, historique en base).

Exemple::

    bus = EventBus()
    bus.subscribe(EventType.DEVICE_STATE_CHANGED, on_change)
    await bus.publish(Event(EventType.DEVICE_STATE_CHANGED, {"id": 1}))
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.core.logging import get_logger

logger = get_logger("core.events")


class EventType(StrEnum):
    """Types d'evenements circulant sur le bus."""

    DEVICE_ADDED = "device_added"
    DEVICE_REMOVED = "device_removed"
    DEVICE_STATE_CHANGED = "device_state_changed"
    DEVICE_COMMAND = "device_command"
    SCHEDULE_TRIGGERED = "schedule_triggered"
    RF_CODE_LEARNED = "rf_code_learned"
    USER_LOGIN = "user_login"
    SYSTEM = "system"


@dataclass(slots=True)
class Event:
    """Evenement transporte par le bus.

    Attributes:
        type: categorie de l'evenement.
        payload: donnees associees (identifiant d'appareil, etat...).
        timestamp: date de creation, en UTC.
    """

    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# Un abonne est un callable (sync ou async) recevant l'evenement
Subscriber = Callable[[Event], Any]


class EventBus:
    """Bus Publish/Subscribe asynchrone et tolerant aux pannes.

    Les erreurs levees par un abonne sont journalisees mais
    n'interrompent jamais la distribution aux autres abonnes.
    """

    def __init__(self) -> None:
        """Initialise le bus avec des listes d'abonnes vides."""
        self._subscribers: dict[EventType, list[Subscriber]] = defaultdict(list)

    def subscribe(self, event_type: EventType, subscriber: Subscriber) -> None:
        """Abonne un callable a un type d'evenement."""
        self._subscribers[event_type].append(subscriber)

    def unsubscribe(self, event_type: EventType, subscriber: Subscriber) -> None:
        """Desabonne un callable (silencieux s'il n'etait pas abonne)."""
        with contextlib.suppress(ValueError):
            self._subscribers[event_type].remove(subscriber)

    async def publish(self, event: Event) -> None:
        """Distribue l'evenement a tous les abonnes du type concerne."""
        for subscriber in list(self._subscribers[event.type]):
            try:
                result = subscriber(event)
                # Supporte indifferemment les abonnes sync et async
                if inspect.isawaitable(result):
                    await result
            except Exception:
                logger.exception("Abonne en erreur pour l'evenement %s", event.type)

    def publish_nowait(self, event: Event) -> None:
        """Publie depuis un contexte synchrone (thread pilote, HAP).

        L'evenement est planifie sur la boucle asyncio courante si elle
        existe ; sinon il est distribue immediatement en synchrone.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None:
            loop.create_task(self.publish(event))
        else:
            asyncio.run(self.publish(event))


# Instance globale unique, partagee par toute l'application
event_bus = EventBus()
