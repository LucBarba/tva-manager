"""Pilote emetteur 433 MHz generique (bibliotheque ``rpi_rf``).

Convient aux volets et prises pilotes par codes fixes appris depuis la
telecommande d'origine. Necessite un module emetteur FS1000A (ou
equivalent) cable sur un GPIO du Raspberry Pi.
"""

from __future__ import annotations

from app.core.exceptions import DriverError
from app.core.logging import get_logger
from app.devices.rf.base import RFCode, RFDriver, SomfyButton

logger = get_logger("rf.rf433")


class RF433Driver(RFDriver):
    """Emetteur RF433 base sur ``rpi_rf`` (codes fixes)."""

    def __init__(self, tx_gpio: int) -> None:
        """Prepare le pilote sans toucher au materiel.

        Args:
            tx_gpio: numero BCM du GPIO relie a la broche DATA de
                l'emetteur 433 MHz.
        """
        self._tx_gpio = tx_gpio
        self._device = None  # instance rpi_rf.RFDevice, creee dans open()

    def open(self) -> None:
        """Initialise le GPIO d'emission via ``rpi_rf``."""
        try:
            # Import paresseux : la bibliotheque n'existe que sur le Pi
            from rpi_rf import RFDevice
        except ImportError as exc:
            raise DriverError(
                "Bibliotheque rpi_rf absente : installer les dependances Raspberry Pi"
            ) from exc
        self._device = RFDevice(self._tx_gpio)
        self._device.enable_tx()
        logger.info("Emetteur RF433 pret sur GPIO %d", self._tx_gpio)

    def close(self) -> None:
        """Libere le GPIO d'emission."""
        if self._device is not None:
            self._device.cleanup()
            self._device = None

    def send_rf433(self, code: RFCode, repeats: int = 8) -> None:
        """Emet un code appris, repete pour fiabiliser la reception."""
        if self._device is None:
            raise DriverError("Pilote RF433 non initialise (appeler open())")
        self._device.tx_repeat = repeats
        ok = self._device.tx_code(code.code, code.protocol, code.pulselength)
        if not ok:
            raise DriverError(f"Echec d'emission du code {code.code}")
        logger.debug("Code %d emis (protocole %d)", code.code, code.protocol)

    def send_somfy(self, address: int, rolling_code: int, button: SomfyButton) -> None:
        """Somfy RTS non supporte par ce pilote (timing incompatible)."""
        raise DriverError(
            "Le pilote rf433 ne gere pas Somfy RTS : utiliser DOMOPI_RF_DRIVER=somfy_rts"
        )
