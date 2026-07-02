"""Conteneur de services de DomoPi (injection de dependances simple).

Instancie et detient les services metier partages par l'API, le
planificateur et le pont HomeKit. Le cycle de vie (start/stop) est
pilote par le ``lifespan`` de l'application FastAPI.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.homekit.bridge import HomeKitService
from app.scheduler.scheduler import SchedulerService
from app.services.history_service import HistoryService
from app.services.hue_service import HueService
from app.services.matter_service import MatterService
from app.services.shutter_service import ShutterService
from app.services.user_service import UserService

logger = get_logger("core.container")


class Container:
    """Regroupe les instances uniques des services applicatifs."""

    def __init__(self) -> None:
        """Cree les services (sans demarrer les integrations)."""
        self.users = UserService()
        self.history = HistoryService()
        self.shutters = ShutterService()
        self.hue = HueService()
        self.matter = MatterService()
        self.scheduler = SchedulerService(self.shutters)
        self.homekit = HomeKitService()

    async def start(self) -> None:
        """Demarre tous les services dans l'ordre des dependances.

        Le pont HomeKit demarre en dernier afin d'exposer les appareils
        deja presents dans le registre.
        """
        self.users.ensure_admin()
        self.history.start()
        await self.shutters.start()
        await self.hue.start()
        await self.matter.start()
        self.scheduler.start()
        await self.homekit.start()
        logger.info("Tous les services sont demarres")

    async def stop(self) -> None:
        """Arrete tous les services dans l'ordre inverse."""
        await self.homekit.stop()
        self.scheduler.stop()
        await self.matter.stop()
        await self.hue.stop()
        await self.shutters.stop()
        logger.info("Tous les services sont arretes")


# Instance globale, creee par l'application au demarrage
container: Container | None = None


def get_container() -> Container:
    """Retourne le conteneur actif (dependance FastAPI)."""
    if container is None:
        raise RuntimeError("Le conteneur de services n'est pas initialise")
    return container


def set_container(instance: Container | None) -> None:
    """Definit le conteneur actif (demarrage applicatif et tests)."""
    global container
    container = instance
