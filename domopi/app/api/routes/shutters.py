"""Routes de gestion des volets roulants et de leurs groupes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, require_admin
from app.api.schemas import (
    GroupCreate,
    GroupOut,
    LearnRequest,
    MessageResponse,
    ShutterCreate,
    ShutterOut,
    ShutterUpdate,
)
from app.container import Container, get_container
from app.core.exceptions import DeviceNotFoundError, DomoPiError, PairingError
from app.devices.rf.base import ShutterCommand

router = APIRouter(prefix="/shutters", tags=["Volets"], dependencies=[Depends(get_current_user)])


def _group_out(group) -> GroupOut:  # noqa: ANN001
    """Convertit un groupe SQLAlchemy en schema de sortie."""
    return GroupOut(id=group.id, name=group.name, shutter_ids=[s.id for s in group.shutters])


# ---------------------------------------------------------------------------
# Groupes (declares avant /{shutter_id} pour eviter les collisions de routes)
# ---------------------------------------------------------------------------


@router.get("/groups", response_model=list[GroupOut], summary="Lister les groupes")
async def list_groups(container: Container = Depends(get_container)) -> list[GroupOut]:
    """Retourne tous les groupes de volets."""
    return [_group_out(group) for group in await container.shutters.list_groups()]


@router.post(
    "/groups",
    response_model=GroupOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
    summary="Creer un groupe",
)
async def create_group(
    payload: GroupCreate, container: Container = Depends(get_container)
) -> GroupOut:
    """Cree un groupe de volets pilotable d'une seule commande."""
    group = await container.shutters.create_group(payload.name, payload.shutter_ids)
    return _group_out(group)


@router.delete(
    "/groups/{group_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
    summary="Supprimer un groupe",
)
async def delete_group(
    group_id: int, container: Container = Depends(get_container)
) -> MessageResponse:
    """Supprime un groupe (les volets membres sont conserves)."""
    try:
        await container.shutters.delete_group(group_id)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MessageResponse(message="Groupe supprime")


@router.post(
    "/groups/{group_id}/{action}",
    response_model=MessageResponse,
    summary="Commander un groupe",
)
async def command_group(
    group_id: int, action: str, container: Container = Depends(get_container)
) -> MessageResponse:
    """Applique une action (``open``/``close``/``stop``/``favorite``) au groupe."""
    try:
        await container.shutters.command_group(group_id, ShutterCommand(action))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Action inconnue: {action}"
        ) from exc
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MessageResponse(message=f"Action '{action}' envoyee au groupe {group_id}")


# ---------------------------------------------------------------------------
# Volets individuels
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ShutterOut], summary="Lister les volets")
async def list_shutters(container: Container = Depends(get_container)) -> list:
    """Retourne tous les volets enregistres."""
    return await container.shutters.list_shutters()


@router.post(
    "",
    response_model=ShutterOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
    summary="Creer un volet",
)
async def create_shutter(payload: ShutterCreate, container: Container = Depends(get_container)):
    """Cree un volet (une adresse Somfy est allouee si necessaire)."""
    return await container.shutters.create_shutter(**payload.model_dump())


@router.get("/{shutter_id}", response_model=ShutterOut, summary="Detail d'un volet")
async def get_shutter(shutter_id: int, container: Container = Depends(get_container)):
    """Retourne un volet par son identifiant."""
    try:
        return await container.shutters.get_shutter(shutter_id)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{shutter_id}",
    response_model=ShutterOut,
    dependencies=[Depends(require_admin)],
    summary="Modifier un volet",
)
async def update_shutter(
    shutter_id: int, payload: ShutterUpdate, container: Container = Depends(get_container)
):
    """Met a jour les champs modifiables d'un volet."""
    try:
        return await container.shutters.update_shutter(
            shutter_id, **payload.model_dump(exclude_none=True)
        )
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{shutter_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
    summary="Supprimer un volet",
)
async def delete_shutter(
    shutter_id: int, container: Container = Depends(get_container)
) -> MessageResponse:
    """Supprime un volet et ses codes appris."""
    try:
        await container.shutters.delete_shutter(shutter_id)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MessageResponse(message="Volet supprime")


@router.post("/{shutter_id}/{action}", response_model=MessageResponse, summary="Commander un volet")
async def command_shutter(
    shutter_id: int, action: str, container: Container = Depends(get_container)
) -> MessageResponse:
    """Execute ``open``, ``close``, ``stop``, ``favorite`` ou ``prog``."""
    try:
        await container.shutters.send_command(shutter_id, ShutterCommand(action))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Action inconnue: {action}"
        ) from exc
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DomoPiError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(message=f"Action '{action}' envoyee au volet {shutter_id}")


@router.post(
    "/{shutter_id}/learn/code",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
    summary="Apprendre un code RF433",
)
async def learn_code(
    shutter_id: int, payload: LearnRequest, container: Container = Depends(get_container)
) -> MessageResponse:
    """Capture le code d'un bouton de la telecommande d'origine.

    Appuyer sur le bouton de la telecommande pendant la fenetre
    d'ecoute (``timeout_s`` secondes).
    """
    try:
        code = await container.shutters.learn_code(
            shutter_id, ShutterCommand(payload.action), payload.timeout_s
        )
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PairingError as exc:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail=str(exc)) from exc
    return MessageResponse(message=f"Code {code.code} appris pour l'action '{payload.action}'")
