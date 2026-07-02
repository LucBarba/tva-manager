"""Service metier des volets roulants.

Orchestration complete : persistance (codes RF, rolling codes Somfy,
positions), emission radio serialisee (un seul emetteur physique),
apprentissage de telecommandes, groupes de volets et publication des
changements d'etat sur le bus d'evenements.
"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.events import Event, EventType, event_bus
from app.core.exceptions import DeviceNotFoundError, ValidationError
from app.core.logging import get_logger
from app.database.engine import session_scope
from app.database.models import Shutter, ShutterGroup
from app.devices.registry import device_registry
from app.devices.rf.base import (
    SOMFY_BUTTONS,
    MockRFDriver,
    RFCode,
    RFDriver,
    ShutterCommand,
    create_rf_driver,
)
from app.devices.rf.receiver import RFLearner
from app.devices.rf.shutter import ShutterDevice

logger = get_logger("rf.service")

# Position atteinte apres une commande complete
_COMMAND_POSITIONS = {ShutterCommand.OPEN: 100, ShutterCommand.CLOSE: 0}


class ShutterService:
    """Facade metier des volets RF433 / Somfy RTS."""

    def __init__(self, driver: RFDriver | None = None) -> None:
        """Initialise le service.

        Args:
            driver: pilote radio a utiliser ; si ``None``, le pilote
                configure dans ``.env`` est instancie (pattern Factory).
        """
        settings = get_settings()
        self._driver = driver or create_rf_driver(settings.rf_driver, settings.rf_tx_gpio)
        self._learner = RFLearner(
            settings.rf_rx_gpio, use_mock=isinstance(self._driver, MockRFDriver)
        )
        self._repeats = settings.rf_repeats
        # Un seul emetteur physique : les emissions sont serialisees
        self._tx_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Cycle de vie
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Ouvre le pilote radio et enregistre les volets connus."""
        await asyncio.to_thread(self._driver.open)
        for shutter in await self.list_shutters():
            self._register_device(shutter)
        logger.info("Service volets demarre")

    async def stop(self) -> None:
        """Libere le materiel radio."""
        await asyncio.to_thread(self._driver.close)

    def _register_device(self, shutter: Shutter) -> None:
        """Cree la facade ``ShutterDevice`` et l'ajoute au registre."""
        device_registry.register(
            ShutterDevice(shutter.id, shutter.name, shutter.room, service=self)
        )

    # ------------------------------------------------------------------
    # CRUD volets
    # ------------------------------------------------------------------

    async def list_shutters(self) -> list[Shutter]:
        """Retourne tous les volets enregistres."""
        with session_scope() as session:
            return list(session.query(Shutter).order_by(Shutter.name).all())

    async def get_shutter(self, shutter_id: int) -> Shutter:
        """Retourne un volet ou leve ``DeviceNotFoundError``."""
        with session_scope() as session:
            shutter = session.get(Shutter, shutter_id)
            if shutter is None:
                raise DeviceNotFoundError(f"Volet {shutter_id} introuvable")
            return shutter

    async def create_shutter(
        self,
        name: str,
        room: str = "",
        protocol: str = "rf433",
        travel_time_s: float = 20.0,
        favorite_position: int = 50,
    ) -> Shutter:
        """Cree un volet et l'enregistre dans le registre de peripheriques.

        Pour Somfy RTS, une adresse de telecommande virtuelle unique est
        allouee automatiquement.
        """
        if protocol not in {"rf433", "somfy_rts"}:
            raise ValidationError(f"Protocole inconnu: {protocol}")
        with session_scope() as session:
            shutter = Shutter(
                name=name,
                room=room,
                protocol=protocol,
                travel_time_s=travel_time_s,
                favorite_position=favorite_position,
            )
            if protocol == "somfy_rts":
                # Alloue la prochaine adresse libre (plage privee arbitraire)
                max_address = (
                    session.query(Shutter.address)
                    .filter(Shutter.address.isnot(None))
                    .order_by(Shutter.address.desc())
                    .limit(1)
                    .scalar()
                )
                shutter.address = (max_address or 0x120000) + 1
                shutter.rolling_code = 1
            session.add(shutter)
            session.flush()
            session.refresh(shutter)
        self._register_device(shutter)
        await event_bus.publish(Event(EventType.DEVICE_ADDED, {"uid": f"shutter:{shutter.id}"}))
        return shutter

    async def update_shutter(self, shutter_id: int, **fields: object) -> Shutter:
        """Met a jour les champs modifiables d'un volet."""
        allowed = {"name", "room", "favorite_position", "travel_time_s"}
        with session_scope() as session:
            shutter = session.get(Shutter, shutter_id)
            if shutter is None:
                raise DeviceNotFoundError(f"Volet {shutter_id} introuvable")
            for key, value in fields.items():
                if key in allowed and value is not None:
                    setattr(shutter, key, value)
            session.flush()
            session.refresh(shutter)
        self._register_device(shutter)  # rafraichit nom/piece dans le registre
        return shutter

    async def delete_shutter(self, shutter_id: int) -> None:
        """Supprime un volet et le retire du registre."""
        with session_scope() as session:
            shutter = session.get(Shutter, shutter_id)
            if shutter is None:
                raise DeviceNotFoundError(f"Volet {shutter_id} introuvable")
            session.delete(shutter)
        device_registry.unregister(f"shutter:{shutter_id}")
        await event_bus.publish(Event(EventType.DEVICE_REMOVED, {"uid": f"shutter:{shutter_id}"}))

    # ------------------------------------------------------------------
    # Apprentissage RF433
    # ------------------------------------------------------------------

    async def learn_code(
        self, shutter_id: int, action: ShutterCommand, timeout_s: float = 15.0
    ) -> RFCode:
        """Apprend le code d'un bouton de la telecommande d'origine.

        L'utilisateur appuie sur le bouton correspondant pendant la
        fenetre d'ecoute ; le code capte est associe a l'action.
        """
        code = await self._learner.learn(timeout_s)
        with session_scope() as session:
            shutter = session.get(Shutter, shutter_id)
            if shutter is None:
                raise DeviceNotFoundError(f"Volet {shutter_id} introuvable")
            # Copie du JSON : SQLAlchemy ne detecte pas les mutations en place
            codes = dict(shutter.rf_codes or {})
            codes[action.value] = code.to_dict()
            shutter.rf_codes = codes
        await event_bus.publish(
            Event(EventType.RF_CODE_LEARNED, {"shutter_id": shutter_id, "action": action.value})
        )
        return code

    # ------------------------------------------------------------------
    # Commandes
    # ------------------------------------------------------------------

    async def send_command(self, shutter_id: int, command: ShutterCommand) -> None:
        """Emet la commande radio et met a jour l'etat persiste.

        Pour Somfy RTS le rolling code est incremente de maniere atomique
        avant l'emission ; pour RF433 le code appris est rejoue.
        """
        async with self._tx_lock:
            with session_scope() as session:
                shutter = session.get(Shutter, shutter_id)
                if shutter is None:
                    raise DeviceNotFoundError(f"Volet {shutter_id} introuvable")
                if shutter.protocol == "somfy_rts":
                    button = SOMFY_BUTTONS[command]
                    address, rolling = shutter.address, shutter.rolling_code
                    shutter.rolling_code += 1  # incremente AVANT l'envoi (persistance garantie)
                else:
                    raw = (shutter.rf_codes or {}).get(command.value)
                    if raw is None:
                        raise ValidationError(
                            f"Aucun code appris pour l'action '{command.value}' de ce volet"
                        )
                    code = RFCode.from_dict(raw)
                # Met a jour la position estimee
                if command in _COMMAND_POSITIONS:
                    shutter.position = _COMMAND_POSITIONS[command]
                elif command == ShutterCommand.FAVORITE:
                    shutter.position = shutter.favorite_position
                new_position = shutter.position
                protocol = shutter.protocol

            # Emission radio hors transaction (operation lente, thread dedie)
            if protocol == "somfy_rts":
                await asyncio.to_thread(self._driver.send_somfy, address, rolling, button)
            else:
                await asyncio.to_thread(self._driver.send_rf433, code, self._repeats)

        logger.info("Volet %d: commande %s emise", shutter_id, command.value)
        await event_bus.publish(
            Event(
                EventType.DEVICE_STATE_CHANGED,
                {
                    "uid": f"shutter:{shutter_id}",
                    "command": command.value,
                    "attributes": {"position": new_position},
                },
            )
        )

    async def set_position(self, shutter_id: int, position: int) -> None:
        """Approche une position cible (0 = ferme, 100 = ouvert).

        Sans retour de position des moteurs RF, la strategie est :
        0 -> fermeture, 100 -> ouverture, sinon position favorite si elle
        est proche, a defaut ouverture/fermeture selon le sens.
        """
        position = max(0, min(100, position))
        shutter = await self.get_shutter(shutter_id)
        if position == 0:
            command = ShutterCommand.CLOSE
        elif position == 100:
            command = ShutterCommand.OPEN
        elif abs(position - shutter.favorite_position) <= 10:
            command = ShutterCommand.FAVORITE
        else:
            command = ShutterCommand.OPEN if position > shutter.position else ShutterCommand.CLOSE
        await self.send_command(shutter_id, command)

    async def pair_somfy(self, shutter_id: int) -> None:
        """Appaire la telecommande virtuelle avec un moteur Somfy.

        Procedure : maintenir le bouton PROG de la telecommande d'origine
        jusqu'au va-et-vient du volet, puis appeler cette methode dans la
        foulee (emission d'une trame PROG).
        """
        await self.send_command(shutter_id, ShutterCommand.PROG)

    # ------------------------------------------------------------------
    # Groupes
    # ------------------------------------------------------------------

    async def list_groups(self) -> list[ShutterGroup]:
        """Retourne tous les groupes avec leurs volets charges."""
        with session_scope() as session:
            groups = session.query(ShutterGroup).order_by(ShutterGroup.name).all()
            for group in groups:
                _ = list(group.shutters)  # chargement avant fermeture de session
            return list(groups)

    async def create_group(self, name: str, shutter_ids: list[int]) -> ShutterGroup:
        """Cree un groupe de volets."""
        with session_scope() as session:
            shutters = session.query(Shutter).filter(Shutter.id.in_(shutter_ids)).all()
            group = ShutterGroup(name=name, shutters=shutters)
            session.add(group)
            session.flush()
            session.refresh(group)
            _ = list(group.shutters)
            return group

    async def delete_group(self, group_id: int) -> None:
        """Supprime un groupe (les volets membres sont conserves)."""
        with session_scope() as session:
            group = session.get(ShutterGroup, group_id)
            if group is None:
                raise DeviceNotFoundError(f"Groupe {group_id} introuvable")
            session.delete(group)

    async def command_group(self, group_id: int, command: ShutterCommand) -> None:
        """Applique une commande a tous les volets d'un groupe."""
        with session_scope() as session:
            group = session.get(ShutterGroup, group_id)
            if group is None:
                raise DeviceNotFoundError(f"Groupe {group_id} introuvable")
            shutter_ids = [shutter.id for shutter in group.shutters]
        for shutter_id in shutter_ids:
            await self.send_command(shutter_id, command)
