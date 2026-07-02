"""Routes de consultation du journal et de l'historique des mesures."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.api.schemas import EventLogOut, ReadingOut
from app.container import Container, get_container

router = APIRouter(prefix="/history", tags=["Historique"], dependencies=[Depends(get_current_user)])


@router.get("/events", response_model=list[EventLogOut], summary="Journal d'evenements")
async def events(
    limit: int = Query(default=100, ge=1, le=500),
    source: str | None = None,
    event_type: str | None = None,
    container: Container = Depends(get_container),
) -> list:
    """Retourne les derniers evenements du journal (filtrables)."""
    return container.history.get_events(limit=limit, source=source, event_type=event_type)


@router.get(
    "/readings/{device_uid}", response_model=list[ReadingOut], summary="Historique de mesures"
)
async def readings(
    device_uid: str,
    metric: str = Query(default="temperature", pattern=r"^[a-z_]+$"),
    hours: int = Query(default=24, ge=1, le=744),
    container: Container = Depends(get_container),
) -> list:
    """Retourne l'historique d'une mesure d'un capteur."""
    return container.history.get_readings(device_uid, metric=metric, hours=hours)
