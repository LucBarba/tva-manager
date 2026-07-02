"""Routes systeme : sante, version, informations d'execution."""

from __future__ import annotations

import platform

from fastapi import APIRouter, Depends

import app as app_package
from app.api.deps import get_current_user
from app.core.config import get_settings
from app.devices.registry import device_registry

router = APIRouter(prefix="/system", tags=["Systeme"])


@router.get("/health", summary="Verification de sante")
async def health() -> dict:
    """Endpoint public de supervision (aucune donnee sensible)."""
    return {"status": "ok"}


@router.get("/info", dependencies=[Depends(get_current_user)], summary="Informations systeme")
async def info() -> dict:
    """Retourne version, plateforme et etat des integrations."""
    settings = get_settings()
    return {
        "app": settings.app_name,
        "version": app_package.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "environment": settings.environment,
        "device_count": len(device_registry.all()),
        "integrations": {
            "rf_driver": settings.rf_driver,
            "hue_enabled": settings.hue_enabled,
            "matter_enabled": settings.matter_enabled,
            "homekit_enabled": settings.homekit_enabled,
        },
    }
