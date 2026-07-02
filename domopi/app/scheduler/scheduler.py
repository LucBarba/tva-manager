"""Planificateur horaire de DomoPi.

Charge les programmations persistees en base et les execute via
APScheduler (declencheurs cron). Toute modification d'une programmation
recharge le travail correspondant, sans redemarrage de l'application.
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.events import Event, EventType, event_bus
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.database.engine import session_scope
from app.database.models import Schedule
from app.devices.registry import device_registry
from app.devices.rf.base import ShutterCommand

logger = get_logger("scheduler")

# Types de cibles supportes par les programmations
_TARGET_TYPES = {"shutter", "shutter_group", "light"}


class SchedulerService:
    """Gestion des programmations horaires (CRUD + execution)."""

    def __init__(self, shutter_service) -> None:  # noqa: ANN001
        """Initialise le planificateur.

        Args:
            shutter_service: service volets, utilise pour les commandes
                de groupes (les appareils individuels passent par le
                registre de peripheriques).
        """
        self._scheduler = AsyncIOScheduler()
        self._shutter_service = shutter_service

    # ------------------------------------------------------------------
    # Cycle de vie
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Demarre APScheduler et charge les programmations actives."""
        self._scheduler.start()
        with session_scope() as session:
            schedules = session.query(Schedule).filter_by(enabled=True).all()
        for schedule in schedules:
            self._add_job(schedule)
        logger.info("Planificateur demarre (%d programmation(s))", len(schedules))

    def stop(self) -> None:
        """Arrete APScheduler."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    # ------------------------------------------------------------------
    # CRUD programmations
    # ------------------------------------------------------------------

    def list_schedules(self) -> list[Schedule]:
        """Retourne toutes les programmations."""
        with session_scope() as session:
            return list(session.query(Schedule).order_by(Schedule.time).all())

    def create_schedule(
        self,
        name: str,
        target_type: str,
        target_id: str,
        action: str,
        time: str,
        days: list[int],
        enabled: bool = True,
    ) -> Schedule:
        """Cree une programmation et planifie son execution.

        Args:
            name: libelle affiche dans l'interface.
            target_type: ``shutter``, ``shutter_group`` ou ``light``.
            target_id: identifiant de la cible (id volet/groupe, uid Hue).
            action: commande a executer (``open``, ``close``, ``on``...).
            time: heure d'execution au format ``HH:MM``.
            days: jours ISO actifs (1 = lundi ... 7 = dimanche).
            enabled: programmation active ou non.
        """
        self._validate(target_type, time, days)
        with session_scope() as session:
            schedule = Schedule(
                name=name,
                target_type=target_type,
                target_id=str(target_id),
                action=action,
                time=time,
                days=days,
                enabled=enabled,
            )
            session.add(schedule)
            session.flush()
            session.refresh(schedule)
        if enabled:
            self._add_job(schedule)
        return schedule

    def delete_schedule(self, schedule_id: int) -> None:
        """Supprime une programmation et son travail planifie."""
        self._remove_job(schedule_id)
        with session_scope() as session:
            schedule = session.get(Schedule, schedule_id)
            if schedule is None:
                raise ValidationError(f"Programmation {schedule_id} introuvable")
            session.delete(schedule)

    def set_enabled(self, schedule_id: int, enabled: bool) -> Schedule:
        """Active ou desactive une programmation existante."""
        with session_scope() as session:
            schedule = session.get(Schedule, schedule_id)
            if schedule is None:
                raise ValidationError(f"Programmation {schedule_id} introuvable")
            schedule.enabled = enabled
            session.flush()
            session.refresh(schedule)
        self._remove_job(schedule_id)
        if enabled:
            self._add_job(schedule)
        return schedule

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(target_type: str, time: str, days: list[int]) -> None:
        """Valide les parametres d'une programmation."""
        if target_type not in _TARGET_TYPES:
            raise ValidationError(f"Type de cible inconnu: {target_type}")
        parts = time.split(":")
        if (
            len(parts) != 2
            or not all(part.isdigit() for part in parts)
            or not (0 <= int(parts[0]) <= 23 and 0 <= int(parts[1]) <= 59)
        ):
            raise ValidationError(f"Heure invalide (attendu HH:MM): {time}")
        if not days or any(day not in range(1, 8) for day in days):
            raise ValidationError("Les jours doivent etre entre 1 (lundi) et 7 (dimanche)")

    def _add_job(self, schedule: Schedule) -> None:
        """Planifie l'execution cron d'une programmation."""
        hour, minute = schedule.time.split(":")
        # APScheduler numerote les jours 0 = lundi ... 6 = dimanche
        days_of_week = ",".join(str(day - 1) for day in schedule.days)
        self._scheduler.add_job(
            self._execute,
            CronTrigger(hour=int(hour), minute=int(minute), day_of_week=days_of_week),
            args=[schedule.id],
            id=f"schedule:{schedule.id}",
            replace_existing=True,
        )

    def _remove_job(self, schedule_id: int) -> None:
        """Retire un travail planifie (silencieux s'il est absent)."""
        job = self._scheduler.get_job(f"schedule:{schedule_id}")
        if job is not None:
            job.remove()

    async def _execute(self, schedule_id: int) -> None:
        """Execute l'action d'une programmation (appele par APScheduler)."""
        with session_scope() as session:
            schedule = session.get(Schedule, schedule_id)
        if schedule is None or not schedule.enabled:
            return
        logger.info("Programmation '%s': action %s", schedule.name, schedule.action)
        try:
            if schedule.target_type == "shutter_group":
                await self._shutter_service.command_group(
                    int(schedule.target_id), ShutterCommand(schedule.action)
                )
            elif schedule.target_type == "shutter":
                device = device_registry.get(f"shutter:{schedule.target_id}")
                await device.execute(schedule.action)
            else:  # light
                device = device_registry.get(schedule.target_id)
                await device.execute(schedule.action)
            await event_bus.publish(
                Event(
                    EventType.SCHEDULE_TRIGGERED,
                    {"schedule_id": schedule_id, "name": schedule.name, "action": schedule.action},
                )
            )
        except Exception:
            logger.exception("Echec de la programmation '%s'", schedule.name)
