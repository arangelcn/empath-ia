"""
Admin session context and user session endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..models.database import get_collection
from .auth import require_admin_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin_permission("read"))],
)


@router.get("/session-contexts")
async def list_session_contexts(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None
):
    """
    Listar contextos de sessão com paginação e busca
    """
    try:
        session_contexts_collection = get_collection("session_contexts")

        # Filtro de busca
        filter_query = {}
        if search:
            filter_query = {
                "$or": [
                    {"session_id": {"$regex": search, "$options": "i"}},
                    {"username": {"$regex": search, "$options": "i"}}
                ]
            }

        # Obter contextos com paginação
        cursor = session_contexts_collection.find(filter_query).sort("created_at", -1).skip(offset).limit(limit)
        contexts = await cursor.to_list(length=limit)

        # Contar total para paginação
        total = await session_contexts_collection.count_documents(filter_query)

        # Formatar dados
        formatted_contexts = []
        for ctx in contexts:
            formatted_contexts.append({
                "id": str(ctx["_id"]),
                "session_id": ctx["session_id"],
                "username": ctx.get("username", "Usuário Anônimo"),
                "created_at": ctx["created_at"].isoformat(),
                "updated_at": ctx.get("updated_at", ctx["created_at"]).isoformat(),
                "context": ctx.get("context", {}),
                "source": ctx.get("source", "unknown"),
                "version": ctx.get("version", 1),
                "is_active": ctx.get("is_active", True)
            })

        return {
            "success": True,
            "data": {
                "contexts": formatted_contexts,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_next": offset + limit < total
                }
            }
        }

    except Exception as e:
        logger.error(f"Erro ao listar contextos de sessão: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session-contexts/{session_id}")
async def get_session_context_details(session_id: str):
    """
    Obter detalhes completos de um contexto de sessão
    """
    try:
        session_contexts_collection = get_collection("session_contexts")
        context_doc = await session_contexts_collection.find_one({"session_id": session_id})

        if not context_doc:
            raise HTTPException(status_code=404, detail="Contexto não encontrado")

        return {
            "success": True,
            "data": {
                "id": str(context_doc["_id"]),
                "session_id": context_doc["session_id"],
                "username": context_doc.get("username", "Usuário Anônimo"),
                "created_at": context_doc["created_at"].isoformat(),
                "updated_at": context_doc.get("updated_at", context_doc["created_at"]).isoformat(),
                "context": context_doc.get("context", {}),
                "conversation_text": context_doc.get("conversation_text", ""),
                "emotions_data": context_doc.get("emotions_data", []),
                "source": context_doc.get("source", "unknown"),
                "version": context_doc.get("version", 1),
                "is_active": context_doc.get("is_active", True)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter contexto da sessão: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-sessions")
async def list_all_user_sessions(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    status: Optional[str] = None,
    personalized: Optional[bool] = None
):
    """
    Listar todas as sessões dos usuários com filtros
    """
    try:
        user_sessions_collection = get_collection("user_therapeutic_sessions")

        # Filtro de busca
        filter_query = {}

        if search:
            filter_query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"title": {"$regex": search, "$options": "i"}},
                {"session_id": {"$regex": search, "$options": "i"}}
            ]

        if status:
            filter_query["status"] = status

        if personalized is not None:
            filter_query["personalized"] = personalized

        # Obter sessões com paginação
        cursor = user_sessions_collection.find(filter_query).sort("created_at", -1).skip(offset).limit(limit)
        sessions = await cursor.to_list(length=limit)

        # Contar total para paginação
        total = await user_sessions_collection.count_documents(filter_query)

        # Formatar dados e buscar contextos
        formatted_sessions = []
        session_contexts_collection = get_collection("session_contexts")

        for session in sessions:
            # Buscar contexto da sessão se existir
            session_context_id = f"{session['username']}_{session['session_id']}"
            context_doc = await session_contexts_collection.find_one({"session_id": session_context_id})

            session_data = {
                "id": str(session["_id"]),
                "username": session["username"],
                "session_id": session["session_id"],
                "title": session.get("title", ""),
                "subtitle": session.get("subtitle", ""),
                "objective": session.get("objective", ""),
                "status": session.get("status", "locked"),
                "progress": session.get("progress", 0),
                "personalized": session.get("personalized", False),
                "created_at": session["created_at"].isoformat(),
                "completed_at": session.get("completed_at").isoformat() if session.get("completed_at") else None,
                "focus_areas": session.get("focus_areas", []),
                "connection_to_previous": session.get("connection_to_previous", ""),
                "initial_prompt": session.get("initial_prompt", ""),
                "estimated_duration": session.get("estimated_duration", ""),
                "generation_method": session.get("generation_method", ""),
                "based_on_session": session.get("based_on_session", ""),
                "is_active": session.get("is_active", True),
                # Adicionar contexto se disponível
                "has_context": context_doc is not None,
                "context": context_doc.get("context", {}) if context_doc else None,
                "context_created_at": context_doc.get("created_at").isoformat() if context_doc else None
            }
            formatted_sessions.append(session_data)

        return {
            "success": True,
            "data": {
                "sessions": formatted_sessions,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_next": offset + limit < total
                }
            }
        }

    except Exception as e:
        logger.error(f"Erro ao listar sessões dos usuários: {e}")
        raise HTTPException(status_code=500, detail=str(e))
