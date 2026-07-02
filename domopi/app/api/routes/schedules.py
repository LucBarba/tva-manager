"""Routes des programmations horaires."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, require_admin
from app.api.schemas import MessageResponse, ScheduleCreate, ScheduleOut
from app.container import Container, get_container
from app.core.exceptions import ValidationError

router = APIRouter(
    prefix="/schedules", tags=["Programmations"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[ScheduleOut], summary="Lister les programmations")
async def list_schedules(container: Container = Depends(get_container)) -> list:
    """Retourne toutes les programmations horaires."""
    return container.scheduler.list_schedules()


@router.post(
    "",
    response_model=ScheduleOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
    summary="Creer une programmation",
)
async def create_schedule(payload: ScheduleCreate, container: Container = Depends(get_container)):
    """Cree une programmation horaire (cron hebdomadaire)."""
    try:
        return container.scheduler.create_schedule(**payload.model_dump())
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch(
    "/{schedule_id}/enabled",
    response_model=ScheduleOut,
    dependencies=[Depends(require_admin)],
    summary="Activer/desactiver",
)
async def set_enabled(
    schedule_id: int, enabled: bool, container: Container = Depends(get_container)
):
    """Active ou desactive une programmation sans la supprimer."""
    try:
        return container.scheduler.set_enabled(schedule_id, enabled)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{schedule_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
    summary="Supprimer une programmation",
)
async def delete_schedule(
    schedule_id: int, container: Container = Depends(get_container)
) -> MessageResponse:
    """Supprime une programmation et son travail planifie."""
    try:
        container.scheduler.delete_schedule(schedule_id)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MessageResponse(message="Programmation supprimee")
