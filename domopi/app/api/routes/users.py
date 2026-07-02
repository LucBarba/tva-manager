"""Routes de gestion des utilisateurs (reservees aux administrateurs)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, require_admin
from app.api.schemas import MessageResponse, PasswordChange, UserCreate, UserOut
from app.container import Container, get_container
from app.core.exceptions import ValidationError
from app.database.models import User

router = APIRouter(prefix="/users", tags=["Utilisateurs"])


@router.get(
    "",
    response_model=list[UserOut],
    dependencies=[Depends(require_admin)],
    summary="Lister les utilisateurs",
)
async def list_users(container: Container = Depends(get_container)) -> list:
    """Retourne tous les comptes."""
    return container.users.list_users()


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
    summary="Creer un utilisateur",
)
async def create_user(payload: UserCreate, container: Container = Depends(get_container)):
    """Cree un compte utilisateur ou administrateur."""
    try:
        return container.users.create_user(payload.username, payload.password, payload.role)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/me/password", response_model=MessageResponse, summary="Changer son mot de passe")
async def change_own_password(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
) -> MessageResponse:
    """Change le mot de passe de l'utilisateur connecte."""
    try:
        container.users.update_password(user.id, payload.new_password)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(message="Mot de passe modifie")


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
    summary="Supprimer un utilisateur",
)
async def delete_user(
    user_id: int, container: Container = Depends(get_container)
) -> MessageResponse:
    """Supprime un compte (le dernier administrateur est protege)."""
    try:
        container.users.delete_user(user_id)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(message="Utilisateur supprime")
