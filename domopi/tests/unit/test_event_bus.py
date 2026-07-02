"""Tests unitaires du bus d'evenements."""

from __future__ import annotations

import pytest
from app.core.events import Event, EventBus, EventType


class TestEventBus:
    """Publication et abonnement."""

    @pytest.mark.asyncio
    async def test_async_subscriber_receives_event(self) -> None:
        """Un abonne async recoit l'evenement publie."""
        bus = EventBus()
        received: list[Event] = []

        async def subscriber(event: Event) -> None:
            received.append(event)

        bus.subscribe(EventType.SYSTEM, subscriber)
        await bus.publish(Event(EventType.SYSTEM, {"info": "test"}))
        assert len(received) == 1
        assert received[0].payload["info"] == "test"

    @pytest.mark.asyncio
    async def test_sync_subscriber_supported(self) -> None:
        """Un abonne synchrone est egalement supporte."""
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe(EventType.SYSTEM, received.append)
        await bus.publish(Event(EventType.SYSTEM))
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_failing_subscriber_does_not_break_others(self) -> None:
        """Une exception d'un abonne n'empeche pas les suivants."""
        bus = EventBus()
        received: list[Event] = []

        def failing(_event: Event) -> None:
            raise RuntimeError("boom")

        bus.subscribe(EventType.SYSTEM, failing)
        bus.subscribe(EventType.SYSTEM, received.append)
        await bus.publish(Event(EventType.SYSTEM))
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe(self) -> None:
        """Un abonne retire ne recoit plus rien."""
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe(EventType.SYSTEM, received.append)
        bus.unsubscribe(EventType.SYSTEM, received.append)
        await bus.publish(Event(EventType.SYSTEM))
        assert not received
