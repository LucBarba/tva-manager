"""Point d'entree de DomoPi.

Demarre le serveur Uvicorn qui heberge l'application FastAPI (API REST,
interface Web, WebSocket) ; les services domotique (RF, Hue, Matter,
HomeKit, planificateur) sont demarres par le cycle de vie applicatif.

Usage :
    python main.py
"""

from __future__ import annotations

import uvicorn
from app.core.config import get_settings
from app.utils.network import get_local_ip
from app.web.app import create_app

# Application ASGI (egalement utilisable via `uvicorn main:app`)
app = create_app()


def run() -> None:
    """Lance le serveur avec la configuration du fichier `.env`."""
    settings = get_settings()
    ssl_args = {}
    # HTTPS optionnel : active des que certificat et cle sont fournis
    if settings.ssl_certfile and settings.ssl_keyfile:
        ssl_args = {
            "ssl_certfile": settings.ssl_certfile,
            "ssl_keyfile": settings.ssl_keyfile,
        }
    scheme = "https" if ssl_args else "http"
    print(f"DomoPi disponible sur {scheme}://{get_local_ip()}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        **ssl_args,
    )


if __name__ == "__main__":
    run()
