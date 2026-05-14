"""Admin conversation inspection routes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ...bootstrap.dependencies import AppContainer, get_container
from ..security import require_admin_permission


router = APIRouter(
    prefix="/api/admin",
    tags=["admin-conversations"],
    dependencies=[Depends(require_admin_permission("read"))],
)


@router.get("/conversations")
async def get_conversations_list(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """List conversations for the admin panel."""
    conversations = container.mongo.get_collection("conversations")
    filter_query: dict[str, Any] = {}
    if search:
        filter_query["$or"] = [
            {"session_id": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}},
            {"user_preferences.username": {"$regex": search, "$options": "i"}},
        ]
    rows = await conversations.find(filter_query).sort("updated_at", -1).skip(offset).limit(limit).to_list(length=limit)
    total = await conversations.count_documents(filter_query)
    formatted = []
    for conv in rows:
        updated_at = conv.get("updated_at") or conv.get("created_at") or datetime.now(UTC)
        formatted.append(
            {
                "id": str(conv["_id"]),
                "session_id": conv.get("session_id"),
                "chat_id": conv.get("chat_id"),
                "username": conv.get("username") or conv.get("user_preferences", {}).get("username", "Usuario Anonimo"),
                "created_at": conv.get("created_at").isoformat() if conv.get("created_at") else None,
                "updated_at": updated_at.isoformat(),
                "message_count": conv.get("message_count", 0),
                "status": "active" if (datetime.now(UTC) - updated_at) < timedelta(days=1) else "inactive",
            }
        )
    return {"success": True, "data": {"conversations": formatted, "pagination": {"total": total, "limit": limit, "offset": offset, "has_next": offset + limit < total}}}


def _calculate_conversation_duration(messages: list[dict[str, Any]], created_at: datetime | None, updated_at: datetime | None) -> int:
    if created_at and updated_at:
        return int((updated_at - created_at).total_seconds() / 60)
    if len(messages) >= 2 and messages[0].get("timestamp") and messages[-1].get("timestamp"):
        start = datetime.fromisoformat(messages[0]["timestamp"])
        end = datetime.fromisoformat(messages[-1]["timestamp"])
        return int((end - start).total_seconds() / 60)
    return 0


@router.get("/conversations/{session_id}")
async def get_conversation_details(session_id: str, container: AppContainer = Depends(get_container)) -> dict[str, Any]:
    """Fetch one conversation plus its messages."""
    conversation = await container.conversation_repository.get_by_session_id(session_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa nao encontrada")
    history = await container.conversation_repository.get_history(session_id)
    messages = []
    for item in history.get("history", []):
        messages.append(
            {
                "role": "user" if item.get("type") == "user" else "assistant",
                "content": item.get("content", ""),
                "timestamp": item.get("created_at"),
                "audio_url": item.get("audio_url"),
            }
        )
    user_messages = [msg for msg in messages if msg["role"] == "user"]
    ai_messages = [msg for msg in messages if msg["role"] == "assistant"]
    return {
        "success": True,
        "data": {
            "session_id": conversation.get("session_id"),
            "username": conversation.get("username") or conversation.get("user_preferences", {}).get("username", "Usuario Anonimo"),
            "created_at": conversation.get("created_at").isoformat() if conversation.get("created_at") else None,
            "updated_at": conversation.get("updated_at").isoformat() if conversation.get("updated_at") else None,
            "messages": messages,
            "statistics": {
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "ai_messages": len(ai_messages),
                "duration_minutes": _calculate_conversation_duration(messages, conversation.get("created_at"), conversation.get("updated_at")),
                "emotion_analysis": None,
            },
            "unavailable_fields": ["emotion_analysis"],
        },
    }
