"""Dependances FastAPI transverses : authentification, roles, CSRF.

L'authentification accepte deux vecteurs :
- en-tete ``Authorization: Bearer <jwt>`` (clients API) ;
- cookie ``access_token`` HttpOnly (interface Web).

Les requetes mutantes issues du navigateur (cookie) doivent presenter
un en-tete ``X-CSRF-Token`` valide (double soumission signee).
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.container import Container, get_container
from app.core.exceptions import AuthenticationError
from app.core.security import decode_token, verify_csrf_token
from app.database.models import User

# auto_error=False : on gere nous-memes l'absence de credentials
_bearer_scheme = HTTPBearer(auto_error=False)

# Cookie utilise par l'interface Web
ACCESS_COOKIE = "access_token"
CSRF_COOKIE = "csrf_token"


def _extract_token(request: Request, credentials: HTTPAuthorizationCredentials | None) -> str:
    """Extrait le JWT de l'en-tete Bearer ou du cookie de session."""
    if credentials is not None and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    token = request.cookies.get(ACCESS_COOKIE)
    if token:
        return token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    container: Container = Depends(get_container),
) -> User:
    """Authentifie la requete et retourne l'utilisateur courant.

    Applique egalement la protection CSRF : si l'authentification vient
    du cookie (navigateur) et que la methode est mutante, l'en-tete
    ``X-CSRF-Token`` doit correspondre a un jeton signe valide.
    """
    token = _extract_token(request, credentials)
    try:
        payload = decode_token(token, expected_type="access")
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    # Protection CSRF pour l'authentification par cookie uniquement
    from_cookie = credentials is None or credentials.scheme.lower() != "bearer"
    if from_cookie and request.method not in {"GET", "HEAD", "OPTIONS"}:
        csrf_header = request.headers.get("X-CSRF-Token")
        if not verify_csrf_token(csrf_header):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Jeton CSRF absent ou invalide"
            )

    user = container.users.get_by_username(str(payload.get("sub", "")))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inconnu ou desactive"
        )
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Restreint l'acces aux administrateurs."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Droits administrateur requis"
        )
    return user
