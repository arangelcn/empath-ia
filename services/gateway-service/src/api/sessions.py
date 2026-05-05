"""Therapeutic session and user-session routes."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from ..services.therapeutic_session_service import TherapeuticSessionService
from ..services.user_therapeutic_session_service import UserTherapeuticSessionService


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Sessions"])
therapeutic_session_service = TherapeuticSessionService()
user_therapeutic_session_service = UserTherapeuticSessionService()


@router.get("/api/sessions")
async def get_therapeutic_sessions(active_only: bool = True, limit: int = 50):
    """Obter sessões terapêuticas ativas (endpoint público)"""
    try:
        return await therapeutic_session_service.list_sessions(
            limit=limit,
            offset=0,
            active_only=active_only,
        )
    except Exception as exc:
        logger.error("Erro ao buscar sessões terapêuticas: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.get("/api/sessions/{session_id}")
async def get_therapeutic_session(session_id: str):
    """Obter detalhes de uma sessão terapêutica específica"""
    try:
        session = await therapeutic_session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sessão terapêutica não encontrada")

        return {
            "success": True,
            "data": {
                "id": str(session["_id"]),
                "session_id": session["session_id"],
                "title": session["title"],
                "subtitle": session["subtitle"],
                "objective": session["objective"],
                "initial_prompt": session["initial_prompt"],
                "is_active": session["is_active"],
                "created_at": session["created_at"].isoformat(),
                "updated_at": session["updated_at"].isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Erro ao obter sessão terapêutica: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.post("/api/session/complete")
async def complete_session(request: Request):
    """Marcar uma sessão como concluída para um usuário"""
    try:
        data = await request.json()
        session_id = data.get("session_id")
        user_id = data.get("user_id")

        if not session_id or not user_id:
            raise HTTPException(status_code=400, detail="session_id e user_id são obrigatórios")

        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "user_id": user_id,
                "completed_at": datetime.now().isoformat(),
                "message": "Sessão marcada como concluída",
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Erro ao marcar sessão como concluída: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.get("/api/user/{username}/sessions")
async def get_user_sessions(username: str, status: Optional[str] = None):
    """Obter sessões terapêuticas de um usuário"""
    try:
        sessions = await user_therapeutic_session_service.get_user_sessions(username, status)
        return {
            "success": True,
            "data": {
                "username": username,
                "sessions": sessions,
                "total": len(sessions),
            },
        }
    except Exception as exc:
        logger.error("Erro ao obter sessões do usuário %s: %s", username, exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.post("/api/user/{username}/sessions/create-dynamic")
async def create_dynamic_session_manually(username: str, request: Request):
    """Criar sessão dinâmica manualmente (para testes)"""
    try:
        data = await request.json()
        can_create = await user_therapeutic_session_service.can_create_next_session(username)
        if not can_create:
            return {
                "success": False,
                "error": "Usuário possui sessões pendentes. Complete as sessões existentes primeiro.",
            }

        success = await user_therapeutic_session_service.create_dynamic_session(username, data)
        if success:
            return {
                "success": True,
                "message": "Sessão dinâmica criada com sucesso",
                "session_id": data.get("session_id"),
            }
        return {"success": False, "error": "Falha ao criar sessão dinâmica"}
    except Exception as exc:
        logger.error("Erro ao criar sessão dinâmica para %s: %s", username, exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.get("/api/user/{username}/sessions/info")
async def get_user_sessions_info(username: str):
    """Obter informações detalhadas sobre as sessões do usuário"""
    try:
        sessions = await user_therapeutic_session_service.get_user_sessions(username)
        latest_completed = await user_therapeutic_session_service.get_latest_completed_session(username)
        can_create_next = await user_therapeutic_session_service.can_create_next_session(username)

        return {
            "success": True,
            "data": {
                "username": username,
                "total_sessions": len(sessions),
                "latest_completed_session": latest_completed,
                "can_create_next_session": can_create_next,
                "session_statistics": {
                    "locked": len([s for s in sessions if s.get("status") == "locked"]),
                    "unlocked": len([s for s in sessions if s.get("status") == "unlocked"]),
                    "in_progress": len([s for s in sessions if s.get("status") == "in_progress"]),
                    "completed": len([s for s in sessions if s.get("status") == "completed"]),
                    "dynamic_sessions": len([s for s in sessions if s.get("personalized", False)]),
                    "template_sessions": len([s for s in sessions if not s.get("personalized", False)]),
                },
                "dynamic_session_behavior": {
                    "description": "Sistema dinâmico: ao finalizar uma sessão, uma nova sessão personalizada é criada automaticamente baseada no contexto da sessão anterior",
                    "sequence": "session-1 (cadastro) -> session-2 (personalizada) -> session-3 (personalizada) -> ...",
                    "ai_generation": "Cada nova sessão é gerada pelo AI Service com base no perfil do usuário e contexto da sessão anterior",
                    "auto_unlock": "Novas sessões são automaticamente desbloqueadas após criação",
                },
            },
        }
    except Exception as exc:
        logger.error("Erro ao obter informações das sessões do usuário %s: %s", username, exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.get("/api/user/{username}/sessions/{session_id}/sequence")
async def get_user_session_sequence(username: str):
    """Obter sequência ordenada de sessões do usuário (incluindo sessões dinâmicas)"""
    try:
        sessions = await user_therapeutic_session_service.get_user_session_sequence(username)
        return {
            "success": True,
            "data": {
                "username": username,
                "sessions": sessions,
                "total": len(sessions),
                "sequence_info": {
                    "dynamic_sessions": len([s for s in sessions if s.get("personalized", False)]),
                    "template_sessions": len([s for s in sessions if not s.get("personalized", False)]),
                    "completed_sessions": len([s for s in sessions if s.get("status") == "completed"]),
                    "available_sessions": len([s for s in sessions if s.get("status") == "unlocked"]),
                },
            },
        }
    except Exception as exc:
        logger.error("Erro ao obter sequência de sessões do usuário %s: %s", username, exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.post("/api/user/{username}/sessions/{session_id}/unlock")
async def unlock_user_session(username: str, session_id: str):
    """Desbloquear uma sessão para o usuário"""
    try:
        success = await user_therapeutic_session_service.unlock_session(username, session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        return {"success": True, "message": f"Sessão {session_id} desbloqueada com sucesso"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Erro ao desbloquear sessão %s para usuário %s: %s", session_id, username, exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.post("/api/user/{username}/sessions/{session_id}/start")
async def start_user_session(username: str, session_id: str):
    """Iniciar uma sessão para o usuário"""
    try:
        success = await user_therapeutic_session_service.start_session(username, session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        return {"success": True, "message": f"Sessão {session_id} iniciada com sucesso"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Erro ao iniciar sessão %s para usuário %s: %s", session_id, username, exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.post("/api/user/{username}/sessions/{session_id}/complete")
async def complete_user_session(username: str, session_id: str, request: Request):
    """Marcar uma sessão como concluída para o usuário"""
    try:
        data = await request.json()
        progress = data.get("progress", 100)
        success = await user_therapeutic_session_service.complete_session(username, session_id, progress)
        if not success:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        return {"success": True, "message": f"Sessão {session_id} concluída com sucesso"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Erro ao concluir sessão %s para usuário %s: %s", session_id, username, exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.get("/api/user/{username}/sessions/{session_id}")
async def get_user_session(username: str, session_id: str):
    """Obter uma sessão específica de um usuário"""
    try:
        session = await user_therapeutic_session_service.get_user_session(username, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        return {"success": True, "data": session}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Erro ao obter sessão %s do usuário %s: %s", session_id, username, exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc


@router.get("/api/user/{username}/progress")
async def get_user_progress(username: str):
    """Obter progresso geral do usuário"""
    try:
        progress = await user_therapeutic_session_service.get_user_progress(username)
        return {"success": True, "data": progress}
    except Exception as exc:
        logger.error("Erro ao obter progresso do usuário %s: %s", username, exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}") from exc
