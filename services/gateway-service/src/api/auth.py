"""
Autenticação Google — verifica ID Token, faz upsert do usuário e emite JWT próprio.
"""

import os
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from pymongo.errors import DuplicateKeyError

from ..models.database import get_users_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

SECRET_KEY = os.getenv("SECRET_KEY", "changeme-must-be-at-least-32-characters-long!")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 dias
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@empat-ia.io")
ADMIN_ALLOWED_EMAILS = {
    email.strip().lower()
    for email in os.getenv("ADMIN_ALLOWED_EMAILS", ADMIN_EMAIL).split(",")
    if email.strip()
}


def _get_google_client_id() -> str:
    """Lê GOOGLE_CLIENT_ID em tempo de execução para suportar injeção tardia de env vars."""
    return (os.getenv("GOOGLE_CLIENT_ID") or "").strip()


class GoogleAuthRequest(BaseModel):
    credential: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


def _create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    try:
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    except JWTError as exc:
        logger.exception("Falha ao emitir JWT: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao criar sessão.") from exc


def _decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.") from exc


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Autenticação administrativa necessária.")

    payload = _decode_access_token(credentials.credentials)
    role = payload.get("role")
    email = (payload.get("email") or "").lower()

    if role != "admin" and email not in ADMIN_ALLOWED_EMAILS:
        raise HTTPException(status_code=403, detail="Usuário sem permissão administrativa.")

    return payload


def require_admin_permission(permission: str):
    async def dependency(payload: dict = Depends(get_current_admin)) -> dict:
        permissions = payload.get("permissions") or []
        if "*" in permissions or permission in permissions:
            return payload
        raise HTTPException(status_code=403, detail=f"Permissão administrativa ausente: {permission}.")

    return dependency


def _account_username(google_sub: str, email: str | None) -> str:
    """Username único no MongoDB: índice único em `users.username` — não usar só o nome de exibição."""
    if email:
        return email.strip().lower()
    return f"google_{google_sub}"


def _user_name_fields(user: dict | None) -> tuple[str | None, str | None]:
    """Lê nomes salvos sem derivar do e-mail/Google, para o onboarding saber quando pedir."""
    if not user:
        return None, None

    preferences = user.get("preferences") or {}
    full_name = user.get("full_name") or preferences.get("full_name")
    display_name = user.get("display_name") or preferences.get("display_name")
    return full_name, display_name


@router.get("/google/status")
async def google_auth_status():
    """Informa se a autenticação Google está disponível no servidor."""
    available = bool(_get_google_client_id())
    if not available:
        logger.warning("GOOGLE_CLIENT_ID não está configurado — auth Google indisponível.")
    return {"available": available}


@router.post("/admin/login")
async def admin_login(body: AdminLoginRequest):
    """
    Login administrativo para o painel interno.

    Em produção, ADMIN_USERNAME/ADMIN_PASSWORD devem vir de segredo/IdP corporativo.
    O retorno segue o mesmo contrato de bearer token usado pelo app do usuário.
    """
    if body.username != ADMIN_USERNAME or body.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Credenciais administrativas inválidas.")

    permissions = ["read", "write", "sensitive"]
    access_token = _create_access_token(
        {
            "sub": f"admin:{ADMIN_USERNAME}",
            "username": ADMIN_USERNAME,
            "email": ADMIN_EMAIL,
            "name": "Administrador",
            "role": "admin",
            "permissions": permissions,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": f"admin:{ADMIN_USERNAME}",
            "username": ADMIN_USERNAME,
            "name": "Administrador",
            "email": ADMIN_EMAIL,
            "role": "admin",
            "permissions": permissions,
        },
    }


@router.post("/google")
async def google_auth(body: GoogleAuthRequest):
    """
    Recebe o ID Token do Google Identity Services, verifica sua assinatura,
    faz upsert do usuário no MongoDB e retorna um JWT de sessão.
    """
    GOOGLE_CLIENT_ID = _get_google_client_id()
    if not GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID não configurado")
        raise HTTPException(status_code=503, detail="Autenticação Google não configurada no servidor.")

    # Verificar ID Token com a chave pública do Google (sem segredo compartilhado)
    try:
        idinfo = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
    except ValueError as exc:
        logger.warning("Token Google inválido: %s", exc)
        raise HTTPException(status_code=401, detail="Token Google inválido ou expirado.") from exc

    google_sub: str = idinfo["sub"]
    email_raw = idinfo.get("email")
    if not email_raw:
        raise HTTPException(status_code=400, detail="Conta Google sem e-mail; não é possível continuar.")

    email = email_raw.strip().lower()
    name: str = idinfo.get("name") or email.split("@")[0]
    picture: str | None = idinfo.get("picture")
    email_verified: bool = idinfo.get("email_verified", False)
    stable_username = _account_username(google_sub, email)

    users_col = get_users_collection()

    # Buscar por google_id (login recorrente) ou email (migração de conta manual)
    user = await users_col.find_one(
        {"$or": [{"google_id": google_sub}, {"email": email}, {"email": email_raw.strip()}]}
    )

    full_name = None
    display_name = None

    if user:
        full_name, display_name = _user_name_fields(user)
        await users_col.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "google_id": google_sub,
                    "email": email,
                    "name": name,
                    "picture": picture,
                    "email_verified": email_verified,
                    "last_login": datetime.utcnow(),
                    "auth_method": "google",
                },
                "$inc": {"login_count": 1},
            },
        )
        username: str = user.get("username") or stable_username
    else:
        new_user = {
            "google_id": google_sub,
            "username": stable_username,
            "email": email,
            "name": name,
            "picture": picture,
            "email_verified": email_verified,
            "auth_method": "google",
            "preferences": {
                "selected_voice": "pt-BR-Neural2-B",
                "voice_enabled": True,
                "theme": "dark",
                "language": "pt-BR",
            },
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
            "is_active": True,
            "session_count": 0,
            "login_count": 1,
        }
        try:
            await users_col.insert_one(new_user)
        except DuplicateKeyError as exc:
            logger.warning("DuplicateKey ao criar usuário Google (re-tentando lookup): %s", exc)
            user = await users_col.find_one({"$or": [{"google_id": google_sub}, {"email": email}]})
            if not user:
                raise HTTPException(
                    status_code=409,
                    detail="Conflito ao criar conta; tente novamente em instantes.",
                ) from exc
            username = user.get("username") or stable_username
            full_name, display_name = _user_name_fields(user)
        else:
            username = stable_username
            logger.info("Novo usuário Google criado: %s", email)

    access_token = _create_access_token(
        {"sub": google_sub, "email": email, "name": name, "username": username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": google_sub,
            "email": email,
            "name": name,
            "picture": picture,
            "username": username,
            "full_name": full_name,
            "display_name": display_name,
            "preferences": (user or new_user).get("preferences", {}),
            "requires_profile_name": not bool(full_name or display_name),
            "email_verified": email_verified,
            "auth_method": "google",
        },
    }
