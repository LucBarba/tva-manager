"""Apprentissage de telecommandes RF433.

Ecoute le recepteur 433 MHz pendant une fenetre donnee et retourne le
code stable capte (celui recu le plus souvent), afin d'enregistrer les
boutons d'une telecommande existante.
"""

from __future__ import annotations

import asyncio
import time
from collections import Counter

from app.core.exceptions import DriverError, PairingError
from app.core.logging import get_logger
from app.devices.rf.base import RFCode

logger = get_logger("rf.receiver")


class RFLearner:
    """Capture de codes RF433 pour l'apprentissage des telecommandes."""

    def __init__(self, rx_gpio: int, use_mock: bool = False) -> None:
        """Prepare l'apprentissage.

        Args:
            rx_gpio: numero BCM du GPIO relie au recepteur 433 MHz.
            use_mock: en mode mock, un code factice est retourne
                (developpement sans materiel).
        """
        self._rx_gpio = rx_gpio
        self._use_mock = use_mock

    async def learn(self, timeout_s: float = 15.0) -> RFCode:
        """Attend l'appui d'un bouton et retourne le code capte.

        La capture bloquante s'execute dans un thread afin de ne pas
        geler la boucle asyncio.

        Args:
            timeout_s: duree maximale d'ecoute en secondes.

        Raises:
            PairingError: aucun code recu pendant la fenetre d'ecoute.
        """
        if self._use_mock:
            # Mode developpement : simule la reception d'un code
            await asyncio.sleep(0.1)
            return RFCode(code=123456, protocol=1, pulselength=350)
        return await asyncio.to_thread(self._capture, timeout_s)

    def _capture(self, timeout_s: float) -> RFCode:
        """Capture bloquante des codes recus (executee hors boucle asyncio)."""
        try:
            from rpi_rf import RFDevice
        except ImportError as exc:
            raise DriverError(
                "Bibliotheque rpi_rf absente : installer les dependances Raspberry Pi"
            ) from exc

        device = RFDevice(self._rx_gpio)
        device.enable_rx()
        received: Counter[tuple[int, int, int]] = Counter()
        last_timestamp = None
        deadline = time.monotonic() + timeout_s
        try:
            while time.monotonic() < deadline:
                if device.rx_code_timestamp != last_timestamp and device.rx_code:
                    last_timestamp = device.rx_code_timestamp
                    key = (device.rx_code, device.rx_proto, device.rx_pulselength)
                    received[key] += 1
                    # Un code recu 4 fois est considere comme fiable
                    if received[key] >= 4:
                        break
                time.sleep(0.01)
        finally:
            device.cleanup()

        if not received:
            raise PairingError("Aucun code RF recu : appuyer sur la telecommande pendant l'ecoute")
        (code, protocol, pulselength), count = received.most_common(1)[0]
        logger.info("Code appris: %d (protocole %d, recu %d fois)", code, protocol, count)
        return RFCode(code=code, protocol=protocol, pulselength=pulselength)
