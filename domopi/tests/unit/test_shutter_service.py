"""Tests unitaires du service volets (pilote radio simule)."""

from __future__ import annotations

import pytest
from app.core.exceptions import DeviceNotFoundError, ValidationError
from app.devices.rf.base import MockRFDriver, ShutterCommand
from app.services.shutter_service import ShutterService


@pytest.fixture
def service(db: None) -> ShutterService:
    """Service volets adosse au pilote simule."""
    return ShutterService(driver=MockRFDriver())


class TestShutterCrud:
    """Creation, lecture, suppression."""

    @pytest.mark.asyncio
    async def test_create_and_get(self, service: ShutterService) -> None:
        """Un volet cree est relisible avec ses valeurs."""
        shutter = await service.create_shutter("Salon", room="Salon", protocol="rf433")
        loaded = await service.get_shutter(shutter.id)
        assert loaded.name == "Salon"
        assert loaded.position == 100

    @pytest.mark.asyncio
    async def test_somfy_gets_unique_addresses(self, service: ShutterService) -> None:
        """Chaque volet Somfy recoit une adresse distincte."""
        first = await service.create_shutter("V1", protocol="somfy_rts")
        second = await service.create_shutter("V2", protocol="somfy_rts")
        assert first.address is not None
        assert first.address != second.address

    @pytest.mark.asyncio
    async def test_unknown_protocol_rejected(self, service: ShutterService) -> None:
        """Un protocole inconnu est refuse."""
        with pytest.raises(ValidationError):
            await service.create_shutter("X", protocol="zigbee")

    @pytest.mark.asyncio
    async def test_get_missing_raises(self, service: ShutterService) -> None:
        """Un identifiant inconnu leve DeviceNotFoundError."""
        with pytest.raises(DeviceNotFoundError):
            await service.get_shutter(9999)


class TestShutterCommands:
    """Emission des commandes radio."""

    @pytest.mark.asyncio
    async def test_somfy_command_increments_rolling_code(self, service: ShutterService) -> None:
        """Chaque trame Somfy incremente le rolling code persiste."""
        shutter = await service.create_shutter("Volet", protocol="somfy_rts")
        initial = shutter.rolling_code
        await service.send_command(shutter.id, ShutterCommand.OPEN)
        await service.send_command(shutter.id, ShutterCommand.CLOSE)
        reloaded = await service.get_shutter(shutter.id)
        assert reloaded.rolling_code == initial + 2

    @pytest.mark.asyncio
    async def test_command_updates_position(self, service: ShutterService) -> None:
        """Les commandes mettent a jour la position estimee."""
        shutter = await service.create_shutter("Volet", protocol="somfy_rts")
        await service.send_command(shutter.id, ShutterCommand.CLOSE)
        assert (await service.get_shutter(shutter.id)).position == 0
        await service.send_command(shutter.id, ShutterCommand.OPEN)
        assert (await service.get_shutter(shutter.id)).position == 100

    @pytest.mark.asyncio
    async def test_rf433_without_learned_code_rejected(self, service: ShutterService) -> None:
        """Sans code appris, la commande RF433 est refusee."""
        shutter = await service.create_shutter("Volet", protocol="rf433")
        with pytest.raises(ValidationError):
            await service.send_command(shutter.id, ShutterCommand.OPEN)

    @pytest.mark.asyncio
    async def test_learn_then_command(self, service: ShutterService) -> None:
        """Apres apprentissage, la commande emet le code appris."""
        shutter = await service.create_shutter("Volet", protocol="rf433")
        code = await service.learn_code(shutter.id, ShutterCommand.OPEN)
        await service.send_command(shutter.id, ShutterCommand.OPEN)
        driver: MockRFDriver = service._driver  # type: ignore[assignment]
        assert driver.sent[-1]["kind"] == "rf433"
        assert driver.sent[-1]["code"]["code"] == code.code


class TestGroups:
    """Groupes de volets."""

    @pytest.mark.asyncio
    async def test_group_command_hits_all_members(self, service: ShutterService) -> None:
        """Une commande de groupe est emise pour chaque membre."""
        first = await service.create_shutter("V1", protocol="somfy_rts")
        second = await service.create_shutter("V2", protocol="somfy_rts")
        group = await service.create_group("Etage", [first.id, second.id])
        driver: MockRFDriver = service._driver  # type: ignore[assignment]
        before = len(driver.sent)
        await service.command_group(group.id, ShutterCommand.CLOSE)
        assert len(driver.sent) == before + 2
