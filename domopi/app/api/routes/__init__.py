"""Routeurs de l'API REST, regroupes par domaine fonctionnel."""

from fastapi import APIRouter

from app.api.routes import (
    auth,
    devices,
    history,
    lights,
    matter,
    schedules,
    shutters,
    system,
    users,
)

# Routeur racine de l'API : agrege tous les domaines sous /api
api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(devices.router)
api_router.include_router(shutters.router)
api_router.include_router(lights.router)
api_router.include_router(matter.router)
api_router.include_router(schedules.router)
api_router.include_router(history.router)
api_router.include_router(users.router)
api_router.include_router(system.router)
