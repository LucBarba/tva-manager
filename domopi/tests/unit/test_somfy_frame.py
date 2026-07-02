"""Tests unitaires de la construction de trames Somfy RTS."""

from __future__ import annotations

from app.devices.rf.base import SomfyButton
from app.devices.rf.somfy_rts import build_somfy_frame


def _deobfuscate(frame: bytes) -> bytearray:
    """Inverse l'obfuscation XOR pour retrouver la trame claire."""
    clear = bytearray(frame)
    for i in range(6, 0, -1):
        clear[i] ^= clear[i - 1]
    return clear


class TestSomfyFrame:
    """Proprietes structurelles des trames RTS."""

    def test_frame_length(self) -> None:
        """Une trame RTS fait exactement 7 octets."""
        assert len(build_somfy_frame(0x123456, 42, SomfyButton.UP)) == 7

    def test_checksum_is_valid(self) -> None:
        """Le XOR de tous les quartets de la trame claire vaut zero."""
        frame = build_somfy_frame(0x123456, 42, SomfyButton.DOWN)
        clear = _deobfuscate(frame)
        checksum = 0
        for byte in clear:
            checksum ^= byte ^ (byte >> 4)
        assert checksum & 0x0F == 0

    def test_fields_roundtrip(self) -> None:
        """Bouton, compteur et adresse se retrouvent dans la trame claire."""
        address, rolling = 0xABCDEF, 1234
        clear = _deobfuscate(build_somfy_frame(address, rolling, SomfyButton.MY))
        assert clear[1] >> 4 == SomfyButton.MY.value
        assert (clear[2] << 8) | clear[3] == rolling
        assert clear[4] | (clear[5] << 8) | (clear[6] << 16) == address

    def test_rolling_code_changes_frame(self) -> None:
        """Deux compteurs differents donnent deux trames differentes."""
        first = build_somfy_frame(0x123456, 1, SomfyButton.UP)
        second = build_somfy_frame(0x123456, 2, SomfyButton.UP)
        assert first != second
