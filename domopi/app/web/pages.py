"""Routes des pages HTML de l'interface Web.

Chaque page est rendue cote serveur via Jinja2 (l'echappement
automatique protege contre le XSS) puis hydratee par JavaScript via
l'API REST et le WebSocket. Un utilisateur non authentifie est
redirige vers la page de connexion.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.exceptions import AuthenticationError
from app.core.security import decode_token

pages_router = APIRouter(include_in_schema=False)

_templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


def _current_username(request: Request) -> str | None:
    """Retourne le nom de l'utilisateur connecte, ou ``None``."""
    token = request.cookies.get("access_token", "")
    try:
        payload = decode_token(token, expected_type="access")
        return str(payload.get("sub", "")) or None
    except AuthenticationError:
        return None


def _render(request: Request, template: str, page: str) -> HTMLResponse:
    """Rend une page protegee (redirection vers /login sinon)."""
    username = _current_username(request)
    if username is None:
        return RedirectResponse(url="/login", status_code=302)
    return _templates.TemplateResponse(request, template, {"username": username, "page": page})


@pages_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    """Page de connexion (accessible sans authentification)."""
    if _current_username(request) is not None:
        return RedirectResponse(url="/", status_code=302)
    return _templates.TemplateResponse(request, "login.html", {"page": "login"})


@pages_router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request) -> HTMLResponse:
    """Tableau de bord principal."""
    return _render(request, "dashboard.html", "dashboard")


@pages_router.get("/shutters", response_class=HTMLResponse)
async def shutters_page(request: Request) -> HTMLResponse:
    """Gestion des volets et groupes."""
    return _render(request, "shutters.html", "shutters")


@pages_router.get("/lights", response_class=HTMLResponse)
async def lights_page(request: Request) -> HTMLResponse:
    """Gestion des lumieres Hue (ampoules, pieces, scenes)."""
    return _render(request, "lights.html", "lights")


@pages_router.get("/schedules", response_class=HTMLResponse)
async def schedules_page(request: Request) -> HTMLResponse:
    """Gestion des programmations horaires."""
    return _render(request, "schedules.html", "schedules")


@pages_router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request) -> HTMLResponse:
    """Journal d'evenements et historique des mesures."""
    return _render(request, "history.html", "history")


@pages_router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request) -> HTMLResponse:
    """Configuration (appairages, utilisateurs, systeme)."""
    return _render(request, "settings.html", "settings")
