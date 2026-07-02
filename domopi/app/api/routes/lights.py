"""Routes Philips Hue : appairage, pieces, scenes, groupes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, require_admin
from app.api.schemas import HueGroupCommand, MessageResponse
from app.container import Container, get_container
from app.core.exceptions import DeviceUnavailableError, PairingError

router = APIRouter(prefix="/hue", tags=["Philips Hue"], dependencies=[Depends(get_current_user)])


@router.post(
    "/pair",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
    summary="Appairer le pont Hue",
)
async def pair(container: Container = Depends(get_container)) -> MessageResponse:
    """Appaire l'application au pont (appuyer d'abord sur son bouton)."""
    try:
        await container.hue.pair()
    except PairingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(message="Pont Hue appaire")


@router.post("/refresh", response_model=MessageResponse, summary="Resynchroniser les ampoules")
async def refresh(container: Container = Depends(get_container)) -> MessageResponse:
    """Recharge ampoules et pieces depuis le pont."""
    try:
        await container.hue.refresh_devices()
    except DeviceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return MessageResponse(message="Ampoules resynchronisees")


@router.get("/rooms", summary="Lister les pieces")
async def rooms(container: Container = Depends(get_container)) -> list[dict]:
    """Retourne les pieces declarees sur le pont Hue."""
    try:
        return await container.hue.get_rooms()
    except DeviceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.get("/scenes", summary="Lister les scenes")
async def scenes(container: Container = Depends(get_container)) -> list[dict]:
    """Retourne les scenes enregistrees sur le pont Hue."""
    try:
        return await container.hue.get_scenes()
    except DeviceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.post(
    "/scenes/{scene_id}/activate", response_model=MessageResponse, summary="Activer une scene"
)
async def activate_scene(
    scene_id: str, container: Container = Depends(get_container)
) -> MessageResponse:
    """Active une scene Hue."""
    try:
        await container.hue.activate_scene(scene_id)
    except DeviceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return MessageResponse(message="Scene activee")


@router.post(
    "/groups/{group_id}/command", response_model=MessageResponse, summary="Commander un groupe"
)
async def command_group(
    group_id: str, payload: HueGroupCommand, container: Container = Depends(get_container)
) -> MessageResponse:
    """Commande un groupe de lumieres (piece entiere)."""
    try:
        await container.hue.set_group(
            group_id,
            on=payload.on,
            brightness=payload.brightness,
            color_temp_mirek=payload.color_temp_mirek,
        )
    except DeviceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return MessageResponse(message="Groupe commande")
