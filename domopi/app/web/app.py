"""Fabrique de l'application FastAPI de DomoPi.

Assemble l'API REST (documentee via Swagger sur ``/api/docs``),
l'interface Web (gabarits Jinja2 + fichiers statiques), le WebSocket
temps reel et le cycle de vie des services (demarrage/arret).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import app as app_package
from app.api.routes import api_router
from app.container import Container, set_container
from app.core.config import get_settings
from app.core.exceptions import DomoPiError
from app.core.logging import get_logger, setup_logging
from app.database.engine import init_db
from app.web.pages import pages_router
from app.web.ws import ws_router

logger = get_logger("web.app")

_WEB_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Cycle de vie applicatif : demarre puis arrete tous les services."""
    setup_logging()
    init_db()
    container = Container()
    set_container(container)
    await container.start()
    logger.info("DomoPi est pret")
    try:
        yield
    finally:
        await container.stop()
        set_container(None)


class _SecurityHeadersMiddleware:
    """Ajoute les en-tetes de securite (XSS, clickjacking, sniffing)."""

    def __init__(self, app) -> None:  # noqa: ANN001
        """Enveloppe l'application ASGI."""
        self.app = app

    async def __call__(self, scope, receive, send) -> None:  # noqa: ANN001
        """Injecte les en-tetes sur chaque reponse HTTP."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message) -> None:  # noqa: ANN001
            """Complete les en-tetes de la reponse sortante."""
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.extend(
                    [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"same-origin"),
                        (
                            b"content-security-policy",
                            b"default-src 'self'; img-src 'self' data:; "
                            b"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                            b"script-src 'self' https://cdn.jsdelivr.net; "
                            b"font-src 'self' https://cdn.jsdelivr.net; "
                            b"connect-src 'self' ws: wss:",
                        ),
                    ]
                )
            await send(message)

        await self.app(scope, receive, send_with_headers)


def create_app() -> FastAPI:
    """Construit et retourne l'application FastAPI complete."""
    settings = get_settings()
    app = FastAPI(
        title=f"{settings.app_name} API",
        version=app_package.__version__,
        description="API REST du systeme domotique DomoPi "
        "(volets RF, Philips Hue, Matter, HomeKit).",
        lifespan=_lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(_SecurityHeadersMiddleware)

    @app.exception_handler(DomoPiError)
    async def _domain_error_handler(_request: Request, exc: DomoPiError) -> JSONResponse:
        """Convertit les erreurs metier non interceptees en HTTP 400."""
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    # API REST + WebSocket + pages HTML
    app.include_router(api_router)
    app.include_router(ws_router)
    app.include_router(pages_router)

    # Fichiers statiques (CSS/JS/icones)
    app.mount("/static", StaticFiles(directory=_WEB_DIR / "static"), name="static")

    return app
