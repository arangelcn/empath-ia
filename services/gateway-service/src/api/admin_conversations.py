"""
Admin conversation inspection endpoints.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..models.database import get_collection
from ..services.chat_service import ChatService
from .auth import require_admin_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin_permission("read"))],
)

chat_service = ChatService()


@router.get("/conversations")
async def get_conversations_list(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None
):
    """
    Listar conversas com paginação e busca
    """
    try:
        conversations_collection = get_collection("conversations")

        # Filtro de busca
        filter_query = {}
        if search:
            filter_query = {
                "$or": [
                    {"session_id": {"$regex": search, "$options": "i"}},
                    {"user_preferences.username": {"$regex": search, "$options": "i"}}
                ]
            }

        # Obter conversas com paginação
        cursor = conversations_collection.find(filter_query).sort("updated_at", -1).skip(offset).limit(limit)
        conversations = await cursor.to_list(length=limit)

        # Contar total para paginação
        total = await conversations_collection.count_documents(filter_query)

        # Formatar dados
        formatted_conversations = []
        for conv in conversations:
            formatted_conversations.append({
                "id": str(conv["_id"]),
                "session_id": conv["session_id"],
                "username": conv.get("user_preferences", {}).get("username", "Usuário Anônimo"),
                "created_at": conv["created_at"].isoformat(),
                "updated_at": conv["updated_at"].isoformat(),
                "message_count": len(conv.get("messages", [])),
                "status": "active" if (datetime.utcnow() - conv["updated_at"]).days < 1 else "inactive"
            })

        return {
            "success": True,
            "data": {
                "conversations": formatted_conversations,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_next": offset + limit < total
                }
            }
        }

    except Exception as e:
        logger.error(f"Erro ao listar conversas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{session_id}")
async def get_conversation_details(session_id: str):
    """
    Obter detalhes completos de uma conversa
    """
    try:
        conversation = await chat_service.get_conversation_by_session_id(session_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversa não encontrada")

        # Obter estatísticas da conversa
        messages = conversation.get("messages", [])
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        ai_messages = [msg for msg in messages if msg["role"] == "assistant"]

        return {
            "success": True,
            "data": {
                "session_id": conversation["session_id"],
                "username": conversation.get("user_preferences", {}).get("username", "Usuário Anônimo"),
                "created_at": conversation["created_at"].isoformat(),
                "updated_at": conversation["updated_at"].isoformat(),
                "messages": messages,
                "statistics": {
                    "total_messages": len(messages),
                    "user_messages": len(user_messages),
                    "ai_messages": len(ai_messages),
                    "duration_minutes": calculate_conversation_duration(conversation),
                    "emotion_analysis": None
                },
                "unavailable_fields": ["emotion_analysis"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da conversa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def calculate_conversation_duration(conversation: Dict) -> int:
    """
    Calcular duração da conversa em minutos
    """
    created_at = conversation["created_at"]
    updated_at = conversation["updated_at"]
    duration = updated_at - created_at
    return int(duration.total_seconds() / 60)
