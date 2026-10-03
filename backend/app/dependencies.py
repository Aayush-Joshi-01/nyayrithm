from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.core.auth import AuthenticatedUser, AuthError, KeycloakVerifier, dev_user, get_verifier

bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def authenticate_token(
    token: str | None, verifier: KeycloakVerifier
) -> AuthenticatedUser:
    """Shared by the HTTP dependency and the WebSocket handshake."""
    if not token:
        if get_settings().auth_bypass:
            return dev_user()
        raise _unauthorized("Not authenticated")
    try:
        return await verifier.verify(token)
    except AuthError as exc:
        raise _unauthorized(str(exc)) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    verifier: KeycloakVerifier = Depends(get_verifier),
) -> AuthenticatedUser:
    return await authenticate_token(credentials.credentials if credentials else None, verifier)
