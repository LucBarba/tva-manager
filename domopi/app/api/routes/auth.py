"""Routes d'authentification : connexion, rafraichissement, deconnexion.

La connexion emet les jetons JWT dans la reponse JSON (clients API) et
les depose aussi en cookies HttpOnly pour l'interface Web, accompagnes
d'un cookie CSRF lisible par JavaScript (double soumission).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.deps import ACCESS_COOKIE, CSRF_COOKIE, get_current_user
from app.api.schemas import LoginRequest, MessageResponse, TokenResponse, UserOut
from app.container import Container, get_container
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_csrf_token,
)
from app.database.models import User

router = APIRouter(prefix="/auth", tags=["Authentification"])


def _set_auth_cookies(response: Response, access_token: str) -> None:
    """Depose les cookies de session (JWT HttpOnly + jeton CSRF)."""
    settings = get_settings()
    secure = settings.is_production and bool(settings.ssl_certfile)
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=settings.access_token_expire_minutes * 60,
    )
    # Le cookie CSRF doit etre lisible par JavaScript (double soumission)
    response.set_cookie(
        CSRF_COOKIE,
        generate_csrf_token(),
        httponly=False,
        samesite="lax",
        secure=secure,
        max_age=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenResponse, summary="Connexion")
async def login(
    payload: LoginRequest,
    response: Response,
    container: Container = Depends(get_container),
) -> TokenResponse:
    """Verifie les identifiants et emet les jetons d'acces."""
    try:
        user = await container.users.authenticate(payload.username, payload.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    access_token = create_access_token(user.username)
    refresh_token = create_refresh_token(user.username)
    _set_auth_cookies(response, access_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse, summary="Rafraichir le jeton")
async def refresh(
    request: Request,
    response: Response,
    container: Container = Depends(get_container),
) -> TokenResponse:
    """Emet un nouveau jeton d'acces a partir d'un jeton de rafraichissement.

    Le jeton de rafraichissement est attendu dans le corps JSON
    (``{"refresh_token": ...}``).
    """
    body = await request.json()
    token = str(body.get("refresh_token", ""))
    try:
        payload = decode_token(token, expected_type="refresh")
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    username = str(payload.get("sub", ""))
    user = container.users.get_by_username(username)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inconnu ou desactive"
        )
    access_token = create_access_token(username)
    _set_auth_cookies(response, access_token)
    return TokenResponse(access_token=access_token, refresh_token=create_refresh_token(username))


@router.post("/logout", response_model=MessageResponse, summary="Deconnexion")
async def logout(response: Response) -> MessageResponse:
    """Supprime les cookies de session du navigateur."""
    response.delete_cookie(ACCESS_COOKIE)
    response.delete_cookie(CSRF_COOKIE)
    return MessageResponse(message="Deconnecte")


@router.get("/me", response_model=UserOut, summary="Utilisateur courant")
async def me(user: User = Depends(get_current_user)) -> User:
    """Retourne le profil de l'utilisateur authentifie."""
    return user
