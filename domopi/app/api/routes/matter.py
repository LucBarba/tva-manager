"""Routes Matter : appairage et resynchronisation des capteurs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, require_admin
from app.api.schemas import CommissionRequest, MessageResponse
from app.container import Container, get_container
from app.core.exceptions import DeviceUnavailableError, PairingError

router = APIRouter(prefix="/matter", tags=["Matter"], dependencies=[Depends(get_current_user)])


@router.post(
    "/commission",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
    summary="Appairer un appareil Matter",
)
async def commission(
    payload: CommissionRequest, container: Container = Depends(get_container)
) -> MessageResponse:
    """Appaire un appareil via son code de mise en service (QR/numerique)."""
    try:
        node_id = await container.matter.commission(payload.pairing_code)
    except PairingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DeviceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return MessageResponse(message=f"Appareil Matter appaire (noeud {node_id})")


@router.post("/refresh", response_model=MessageResponse, summary="Resynchroniser les appareils")
async def refresh(container: Container = Depends(get_container)) -> MessageResponse:
    """Recharge la liste des noeuds depuis le serveur Matter."""
    try:
        await container.matter.refresh_devices()
    except DeviceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return MessageResponse(message="Appareils Matter resynchronises")
