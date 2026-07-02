"""Abstraction materielle radiofrequence.

Le reste de l'application ne manipule que l'interface ``RFDriver`` ;
changer d'emetteur (module 433 MHz simple, emetteur RTS, dongle...)
revient a fournir une nouvelle implementation, sans toucher au metier.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum, StrEnum

from app.core.logging import get_logger

logger = get_logger("rf.base")


class ShutterCommand(StrEnum):
    """Commandes logiques d'un volet roulant."""

    OPEN = "open"
    CLOSE = "close"
    STOP = "stop"
    FAVORITE = "favorite"  # position favorite ("My" chez Somfy)
    PROG = "prog"  # appairage d'une nouvelle telecommande


class SomfyButton(IntEnum):
    """Codes boutons du protocole Somfy RTS."""

    MY = 0x1  # Stop / position favorite
    UP = 0x2
    DOWN = 0x4
    PROG = 0x8


# Correspondance commande logique -> bouton Somfy
SOMFY_BUTTONS: dict[ShutterCommand, SomfyButton] = {
    ShutterCommand.OPEN: SomfyButton.UP,
    ShutterCommand.CLOSE: SomfyButton.DOWN,
    ShutterCommand.STOP: SomfyButton.MY,
    ShutterCommand.FAVORITE: SomfyButton.MY,
    ShutterCommand.PROG: SomfyButton.PROG,
}


@dataclass(slots=True)
class RFCode:
    """Code RF433 brut appris depuis une telecommande.

    Attributes:
        code: valeur decimale du code.
        protocol: numero de protocole (au sens de ``rpi_rf``).
        pulselength: duree d'impulsion en microsecondes.
    """

    code: int
    protocol: int = 1
    pulselength: int = 350

    def to_dict(self) -> dict[str, int]:
        """Serialise le code pour stockage JSON en base."""
        return {"code": self.code, "protocol": self.protocol, "pulselength": self.pulselength}

    @classmethod
    def from_dict(cls, data: dict) -> RFCode:
        """Reconstruit un code depuis sa forme JSON."""
        return cls(
            code=int(data["code"]),
            protocol=int(data.get("protocol", 1)),
            pulselength=int(data.get("pulselength", 350)),
        )


class RFDriver(ABC):
    """Interface d'un emetteur radio.

    Les methodes sont synchrones et bloquantes (timings radio precis) :
    les services les executent dans un thread dedie via
    ``asyncio.to_thread`` pour ne pas bloquer la boucle evenementielle.
    """

    @abstractmethod
    def open(self) -> None:
        """Initialise le materiel (GPIO, connexion pigpio...)."""

    @abstractmethod
    def close(self) -> None:
        """Libere le materiel."""

    @abstractmethod
    def send_rf433(self, code: RFCode, repeats: int = 8) -> None:
        """Emet un code RF433 brut, repete ``repeats`` fois."""

    @abstractmethod
    def send_somfy(self, address: int, rolling_code: int, button: SomfyButton) -> None:
        """Emet une trame Somfy RTS pour la telecommande ``address``.

        Args:
            address: adresse 24 bits de la telecommande virtuelle.
            rolling_code: compteur 16 bits, a incrementer apres chaque envoi.
            button: bouton simule (UP/DOWN/MY/PROG).
        """


class MockRFDriver(RFDriver):
    """Pilote factice pour le developpement et les tests.

    Journalise les trames au lieu de les emettre et conserve la liste
    des envois pour verification dans les tests unitaires.
    """

    def __init__(self) -> None:
        """Initialise l'historique des trames emises."""
        self.sent: list[dict] = []
        self.is_open = False

    def open(self) -> None:
        """Marque le pilote comme initialise."""
        self.is_open = True
        logger.info("MockRFDriver initialise")

    def close(self) -> None:
        """Marque le pilote comme libere."""
        self.is_open = False

    def send_rf433(self, code: RFCode, repeats: int = 8) -> None:
        """Enregistre l'envoi simule d'un code RF433."""
        self.sent.append({"kind": "rf433", "code": code.to_dict(), "repeats": repeats})
        logger.info("[MOCK] RF433 code=%s protocole=%s", code.code, code.protocol)

    def send_somfy(self, address: int, rolling_code: int, button: SomfyButton) -> None:
        """Enregistre l'envoi simule d'une trame Somfy RTS."""
        self.sent.append(
            {"kind": "somfy", "address": address, "rolling_code": rolling_code, "button": button}
        )
        logger.info(
            "[MOCK] Somfy RTS adresse=%06X compteur=%d bouton=%s",
            address,
            rolling_code,
            button.name,
        )


def create_rf_driver(driver_name: str, tx_gpio: int) -> RFDriver:
    """Fabrique le pilote RF configure (pattern Factory).

    Args:
        driver_name: ``mock``, ``rf433`` ou ``somfy_rts``.
        tx_gpio: numero BCM du GPIO relie a l'emetteur.

    Returns:
        Une instance de ``RFDriver`` prete a etre ouverte.
    """
    if driver_name == "rf433":
        from app.devices.rf.rf433 import RF433Driver

        return RF433Driver(tx_gpio)
    if driver_name == "somfy_rts":
        from app.devices.rf.somfy_rts import SomfyRTSDriver

        return SomfyRTSDriver(tx_gpio)
    return MockRFDriver()
