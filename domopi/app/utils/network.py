"""Utilitaires reseau."""

from __future__ import annotations

import socket


def get_local_ip() -> str:
    """Retourne l'adresse IP locale principale du Raspberry Pi.

    Ouvre une socket UDP vers une adresse publique (aucun paquet n'est
    reellement emis) pour determiner l'interface de sortie par defaut.
    Retourne ``127.0.0.1`` en dernier recours.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return str(sock.getsockname()[0])
    except OSError:
        return "127.0.0.1"
