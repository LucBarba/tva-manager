"""Pilote Somfy RTS (433,42 MHz) base sur ``pigpio``.

Le protocole RTS utilise un code tournant (rolling code) : chaque trame
emise incremente un compteur partage entre la "telecommande virtuelle"
(cette application) et le moteur. L'adresse et le compteur de chaque
volet sont persistes en base de donnees.

La construction de trame est isolee dans ``build_somfy_frame`` (fonction
pure, testable sans materiel) ; l'emission utilise les ondes pigpio pour
garantir des timings precis, impossibles a tenir en Python pur.

Materiel requis : emetteur 433,42 MHz (quartz specifique Somfy) cable
sur un GPIO, et le demon ``pigpiod`` actif.
"""

from __future__ import annotations

from app.core.exceptions import DriverError
from app.core.logging import get_logger
from app.devices.rf.base import RFCode, RFDriver, SomfyButton

logger = get_logger("rf.somfy")

# --- Timings du protocole RTS (microsecondes) ---
_SYMBOL = 640  # demi-bit Manchester
_HW_SYNC = 2416  # impulsion de synchro materielle
_SW_SYNC_HIGH = 4550  # synchro logicielle (etat haut)
_WAKEUP_HIGH = 9415  # reveil du recepteur (1re trame)
_WAKEUP_LOW = 89565
_INTER_FRAME_GAP = 30415  # silence entre repetitions


def build_somfy_frame(address: int, rolling_code: int, button: SomfyButton) -> bytes:
    """Construit une trame RTS de 7 octets (checksum + obfuscation).

    Args:
        address: adresse 24 bits de la telecommande virtuelle.
        rolling_code: compteur 16 bits courant.
        button: bouton simule (UP/DOWN/MY/PROG).

    Returns:
        La trame obfusquee prete a etre emise.
    """
    frame = bytearray(7)
    frame[0] = 0xA7  # cle de chiffrement (valeur usuelle)
    frame[1] = button.value << 4  # bouton en quartet haut, checksum en bas
    frame[2] = (rolling_code >> 8) & 0xFF
    frame[3] = rolling_code & 0xFF
    frame[4] = address & 0xFF  # adresse transmise octet de poids faible d'abord
    frame[5] = (address >> 8) & 0xFF
    frame[6] = (address >> 16) & 0xFF

    # Checksum : XOR de tous les quartets, stocke dans le quartet bas de frame[1]
    checksum = 0
    for byte in frame:
        checksum ^= byte ^ (byte >> 4)
    frame[1] |= checksum & 0x0F

    # Obfuscation : chaque octet est XORe avec le precedent
    for i in range(1, 7):
        frame[i] ^= frame[i - 1]

    return bytes(frame)


class SomfyRTSDriver(RFDriver):
    """Emetteur Somfy RTS pilote par ondes ``pigpio``."""

    def __init__(self, tx_gpio: int) -> None:
        """Prepare le pilote sans connexion materielle.

        Args:
            tx_gpio: numero BCM du GPIO relie a l'emetteur 433,42 MHz.
        """
        self._tx_gpio = tx_gpio
        self._pi = None  # connexion pigpio, etablie dans open()

    def open(self) -> None:
        """Se connecte au demon pigpiod et configure le GPIO en sortie."""
        try:
            # Import paresseux : pigpio n'est present que sur le Pi
            import pigpio
        except ImportError as exc:
            raise DriverError(
                "Bibliotheque pigpio absente : installer les dependances Raspberry Pi"
            ) from exc
        self._pi = pigpio.pi()
        if not self._pi.connected:
            self._pi = None
            raise DriverError("Demon pigpiod injoignable (sudo systemctl start pigpiod)")
        self._pi.set_mode(self._tx_gpio, pigpio.OUTPUT)
        self._pi.write(self._tx_gpio, 0)
        logger.info("Emetteur Somfy RTS pret sur GPIO %d", self._tx_gpio)

    def close(self) -> None:
        """Ferme la connexion pigpio."""
        if self._pi is not None:
            self._pi.write(self._tx_gpio, 0)
            self._pi.stop()
            self._pi = None

    def send_rf433(self, code: RFCode, repeats: int = 8) -> None:
        """Les codes fixes 433 MHz ne sont pas geres par ce pilote."""
        raise DriverError(
            "Le pilote somfy_rts ne gere pas les codes fixes : utiliser DOMOPI_RF_DRIVER=rf433"
        )

    def send_somfy(
        self, address: int, rolling_code: int, button: SomfyButton, repeats: int = 4
    ) -> None:
        """Emet une trame RTS puis ses repetitions.

        Args:
            address: adresse 24 bits de la telecommande virtuelle.
            rolling_code: compteur courant (a incrementer par l'appelant).
            button: bouton simule.
            repeats: nombre de repetitions apres la premiere trame.
        """
        if self._pi is None:
            raise DriverError("Pilote Somfy non initialise (appeler open())")
        frame = build_somfy_frame(address, rolling_code, button)
        # Premiere trame (avec reveil), puis repetitions
        self._transmit(frame, first=True)
        for _ in range(repeats):
            self._transmit(frame, first=False)
        logger.debug(
            "Trame RTS emise: adresse=%06X compteur=%d bouton=%s",
            address,
            rolling_code,
            button.name,
        )

    # ------------------------------------------------------------------
    # Emission bas niveau
    # ------------------------------------------------------------------

    def _transmit(self, frame: bytes, first: bool) -> None:
        """Emet une trame via une onde pigpio (timings garantis noyau)."""
        import pigpio

        gpio_on = 1 << self._tx_gpio
        pulses: list = []

        def add(level: int, duration: int) -> None:
            """Ajoute une impulsion (niveau + duree en microsecondes)."""
            on = gpio_on if level else 0
            off = 0 if level else gpio_on
            pulses.append(pigpio.pulse(on, off, duration))

        if first:
            # Reveil du recepteur, uniquement avant la premiere trame
            add(1, _WAKEUP_HIGH)
            add(0, _WAKEUP_LOW)
            hw_sync_count = 2
        else:
            add(0, _INTER_FRAME_GAP)
            hw_sync_count = 7

        # Synchronisation materielle puis logicielle
        for _ in range(hw_sync_count):
            add(1, _HW_SYNC)
            add(0, _HW_SYNC)
        add(1, _SW_SYNC_HIGH)
        add(0, _SYMBOL)

        # Donnees en Manchester : 1 = front montant, 0 = front descendant
        for byte in frame:
            for bit_index in range(7, -1, -1):
                if (byte >> bit_index) & 1:
                    add(0, _SYMBOL)
                    add(1, _SYMBOL)
                else:
                    add(1, _SYMBOL)
                    add(0, _SYMBOL)

        self._pi.wave_clear()
        self._pi.wave_add_generic(pulses)
        wave_id = self._pi.wave_create()
        try:
            self._pi.wave_send_once(wave_id)
            # Attend la fin de l'emission avant de rendre la main
            while self._pi.wave_tx_busy():
                pass
        finally:
            self._pi.wave_delete(wave_id)
