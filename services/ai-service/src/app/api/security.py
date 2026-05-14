"""Shared auth helpers for public/admin API routes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..bootstrap.dependencies import AppContainer, get_container


security = HTTPBearer(auto_error=False)


def create_access_token(container: AppContainer, data: dict) -> str:
    """Issue a signed JWT for the unified service."""
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + timedelta(minutes=container.settings.access_token_expire_minutes)
    return jwt.encode(
        payload,
        container.settings.jwt_secret_key,
        algorithm=container.settings.jwt_algorithm,
    )


def decode_access_token(container: AppContainer, token: str) -> dict:
    """Decode a previously issued JWT."""
    try:
        return jwt.decode(
            token,
            container.settings.jwt_secret_key,
            algorithms=[container.settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado.") from exc


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    container: AppContainer = Depends(get_container),
) -> dict:
    """Validate the bearer token for admin-only routes."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Autenticacao administrativa necessaria.")

    payload = decode_access_token(container, credentials.credentials)
    role = payload.get("role")
    email = str(payload.get("email") or "").lower()

    if role != "admin" and email not in container.settings.admin_allowed_emails:
        raise HTTPException(status_code=403, detail="Usuario sem permissao administrativa.")

    return payload


def require_admin_permission(permission: str):
    """FastAPI dependency factory for admin permission gates."""

    async def dependency(payload: dict = Depends(get_current_admin)) -> dict:
        permissions = payload.get("permissions") or []
        if "*" in permissions or permission in permissions:
            return payload
        raise HTTPException(status_code=403, detail=f"Permissao administrativa ausente: {permission}.")

    return dependency
