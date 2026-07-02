"""Exceptions communes de DomoPi.

Une hierarchie unique permet aux couches hautes (API, HomeKit) de
convertir proprement les erreurs metier en reponses adaptees.
"""

from __future__ import annotations


class DomoPiError(Exception):
    """Erreur de base de l'application (toutes en heritent)."""


class DeviceNotFoundError(DomoPiError):
    """Peripherique introuvable dans le registre ou la base."""


class DeviceUnavailableError(DomoPiError):
    """Peripherique connu mais injoignable (hors-ligne, non appaire)."""


class DriverError(DomoPiError):
    """Erreur materielle ou pilote (GPIO, emetteur RF...)."""


class PairingError(DomoPiError):
    """Echec d'appairage (Hue, Matter, telecommande RF)."""


class AuthenticationError(DomoPiError):
    """Identifiants invalides ou jeton expire."""


class AuthorizationError(DomoPiError):
    """Utilisateur authentifie mais droits insuffisants."""


class ValidationError(DomoPiError):
    """Donnee d'entree invalide au niveau metier."""
