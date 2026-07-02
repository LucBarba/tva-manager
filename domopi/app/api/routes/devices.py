"""Routes generiques sur les peripheriques du registre.

Vue unifiee de tous les appareils (volets, lumieres, capteurs) avec
leur etat courant, et commande generique par identifiant unique.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.api.schemas import CommandRequest, DeviceOut, MessageResponse
from app.core.exceptions import DeviceNotFoundError, DomoPiError
from app.devices.registry import device_registry

router = APIRouter(
    prefix="/devices", tags=["Peripheriques"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[DeviceOut], summary="Lister tous les peripheriques")
async def list_devices(type: str | None = None, room: str | None = None) -> list[DeviceOut]:
    """Retourne tous les peripheriques avec leur etat (filtres facultatifs)."""
    devices = []
    for device in device_registry.all():
        if type and device.device_type.value != type:
            continue
        if room and device.room != room:
            continue
        state = await device.get_state()
        devices.append(
            DeviceOut(**device.to_dict(), online=state.online, attributes=state.attributes)
        )
    return devices


@router.get("/{uid}", response_model=DeviceOut, summary="Detail d'un peripherique")
async def get_device(uid: str) -> DeviceOut:
    """Retourne un peripherique et son etat courant."""
    try:
        device = device_registry.get(uid)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    state = await device.get_state()
    return DeviceOut(**device.to_dict(), online=state.online, attributes=state.attributes)


@router.post("/{uid}/command", response_model=MessageResponse, summary="Commander un peripherique")
async def command_device(uid: str, payload: CommandRequest) -> MessageResponse:
    """Execute une commande generique sur un peripherique."""
    try:
        device = device_registry.get(uid)
        await device.execute(payload.command, **payload.params)
    except DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DomoPiError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(message=f"Commande '{payload.command}' executee sur {uid}")
