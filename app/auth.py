from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from config import get_settings
from session import create_session, validate_and_renew_session, invalidate_session

security = HTTPBearer()


class TokenData(BaseModel):
    """Datos del token/sesión del usuario."""
    sub: str  # username
    scopes: list[str] = []
    session_id: str  # ID de sesión


class TokenResponse(BaseModel):
    """Respuesta del endpoint de login."""
    access_token: str  # SessionID
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Credenciales de login."""
    username: str
    password: str


def create_access_token(subject: str, scopes: list[str] | None = None) -> str:
    """
    Crea una nueva sesión y retorna el SessionID como token.

    Args:
        subject: Username del usuario
        scopes: Lista de permisos/scopes del usuario

    Returns:
        SessionID que funciona como token de acceso
    """
    return create_session(subject, scopes or [])


def validate_token(token: str) -> TokenData:
    """
    Valida el token (SessionID) y renueva la sesión si es válida.

    Args:
        token: SessionID a validar

    Returns:
        TokenData con información del usuario

    Raises:
        HTTPException: Si el token es inválido o expiró
    """
    settings = get_settings()
    session_data = validate_and_renew_session(token, timeout_minutes=settings.JWT_EXPIRATION_MINUTES)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return TokenData(
        sub=session_data["username"],
        scopes=session_data["scopes"],
        session_id=session_data["session_id"]
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> TokenData:
    """
    Dependency para obtener el usuario actual desde el token.
    Valida y renueva automáticamente la sesión.
    """
    return validate_token(credentials.credentials)


def require_scope(required_scope: str):
    """
    Dependency para requerir un scope específico.

    Args:
        required_scope: Scope requerido para acceder al endpoint

    Returns:
        Dependency function que valida el scope
    """
    async def scope_checker(
        current_user: Annotated[TokenData, Depends(get_current_user)]
    ) -> TokenData:
        if required_scope not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope requerido: {required_scope}"
            )
        return current_user
    return scope_checker


def logout(token: str) -> bool:
    """
    Invalida una sesión (logout).

    Args:
        token: SessionID a invalidar

    Returns:
        True si se invalidó correctamente
    """
    return invalidate_session(token)
