"""User routes and onboarding preference endpoints."""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.chat_service import ChatService
from ..services.user_service import UserService
from ..services.user_therapeutic_session_service import UserTherapeuticSessionService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/user", tags=["Users"])
chat_service = ChatService()
user_service = UserService()
user_therapeutic_session_service = UserTherapeuticSessionService()


class UserPreferencesRequest(BaseModel):
    session_id: str
    username: str
    selected_voice: str
    voice_enabled: bool = True
    full_name: Optional[str] = None
    display_name: Optional[str] = None


class UserCreateRequest(BaseModel):
    username: str
    email: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


@router.post("/preferences")
async def save_user_preferences(request: UserPreferencesRequest):
    """Salva as preferências do usuário (nome, voz, voz habilitada) para uma sessão."""
    try:
        should_update_conversation = bool(request.session_id) and (
            request.session_id.startswith("chat_") or "_session-" in request.session_id
        )
        if should_update_conversation:
            await chat_service.start_or_get_conversation(request.session_id)

        display_name = (request.display_name or request.full_name or "").strip() or None
        full_name = (request.full_name or request.display_name or "").strip() or None

        user = await user_service.get_user(request.username)
        existing_preferences = (user or {}).get("preferences", {})
        user_preferences = {
            **existing_preferences,
            "selected_voice": request.selected_voice,
            "voice_enabled": request.voice_enabled,
            "theme": existing_preferences.get("theme", "dark"),
            "language": existing_preferences.get("language", "pt-BR"),
        }
        if full_name:
            user_preferences["full_name"] = full_name
        if display_name:
            user_preferences["display_name"] = display_name

        if user:
            await user_service.update_user_preferences(request.username, user_preferences)
        else:
            await user_service.create_user(username=request.username, preferences=user_preferences)

        updated_data = {
            "user_preferences": {
                "username": request.username,
                "selected_voice": request.selected_voice,
                "voice_enabled": request.voice_enabled,
                "full_name": full_name,
                "display_name": display_name,
                "completed_welcome": True,
            }
        }

        result = True
        if should_update_conversation:
            result = await chat_service.update_conversation_data(request.session_id, updated_data)

        if result:
            return {"success": True, "message": "Preferências salvas com sucesso."}
        return {"success": False, "message": "Erro ao salvar preferências."}

    except Exception as exc:
        logger.error("Erro ao salvar preferências: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.get("/status/{session_id}")
async def get_user_status(session_id: str):
    """Obtém o status de onboarding do usuário para uma sessão."""
    try:
        conversation = await chat_service.get_conversation_by_session_id(session_id)
        if not conversation:
            return {
                "success": True,
                "data": {
                    "is_onboarded": False,
                    "username": None,
                    "selected_voice": None,
                },
            }

        user_prefs = conversation.get("user_preferences", {})
        username = user_prefs.get("username")
        user = await user_service.get_user(username) if username else None
        preferences = (user or {}).get("preferences", {})

        return {
            "success": True,
            "data": {
                "is_onboarded": user_prefs.get("completed_welcome", False),
                "username": username,
                "selected_voice": preferences.get("selected_voice") or user_prefs.get("selected_voice"),
                "full_name": (user or {}).get("full_name") or preferences.get("full_name") or user_prefs.get("full_name"),
                "display_name": (user or {}).get("display_name")
                or preferences.get("display_name")
                or user_prefs.get("display_name"),
            },
        }

    except Exception as exc:
        logger.error("Erro ao obter status do usuário: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.post("/create")
async def create_user(request: UserCreateRequest):
    """Criar novo usuário"""
    try:
        return await user_service.create_user(
            username=request.username,
            email=request.email,
            preferences=request.preferences,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Erro ao criar usuário: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{username}")
async def get_user(username: str):
    """Obter detalhes de um usuário"""
    try:
        user = await user_service.get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return {"success": True, "data": user}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Erro ao obter usuário: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/{username}/preferences")
async def update_user_preferences(username: str, preferences: Dict[str, Any]):
    """Atualizar preferências do usuário"""
    try:
        success = await user_service.update_user_preferences(username, preferences)
        if not success:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return {"success": True, "message": "Preferências atualizadas com sucesso"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Erro ao atualizar preferências: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{username}/login")
async def user_login(username: str):
    """Registrar login do usuário e criar session-1 automaticamente"""
    try:
        success = await user_service.update_last_login(username)
        if not success:
            await user_service.create_user(username=username)
            await user_service.update_last_login(username)

        session_1_result = await user_therapeutic_session_service.create_session_1_for_user(username)
        unlock_result = await user_therapeutic_session_service.unlock_first_session(username)

        return {
            "success": True,
            "message": "Login registrado com sucesso",
            "session_1_creation": session_1_result,
            "unlock_result": unlock_result,
            "system_info": "Sistema de criação gradual (1 a 1) ativado - próximas sessões são criadas automaticamente",
        }

    except Exception as exc:
        logger.error("❌ Erro no login do usuário %s: %s", username, exc)
        return {"success": False, "error": str(exc)}


@router.get("/{username}/stats")
async def get_user_stats(username: str):
    """Obter estatísticas do usuário"""
    try:
        stats = await user_service.get_user_stats(username)
        if not stats:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return {"success": True, "data": stats}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Erro ao obter estatísticas do usuário: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
