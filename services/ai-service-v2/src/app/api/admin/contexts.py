"""Admin session context and user session routes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ...bootstrap.dependencies import AppContainer, get_container
from ..security import require_admin_permission


router = APIRouter(
    prefix="/api/admin",
    tags=["admin-contexts"],
    dependencies=[Depends(require_admin_permission("read"))],
)


def _serialize_dt(value: Any) -> Any:
    return value.isoformat() if isinstance(value, datetime) else value


@router.get("/session-contexts")
async def list_session_contexts(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """List saved session contexts."""
    session_contexts = container.mongo.get_collection("session_contexts")
    filter_query: dict[str, Any] = {}
    if search:
        filter_query = {
            "$or": [
                {"session_id": {"$regex": search, "$options": "i"}},
                {"username": {"$regex": search, "$options": "i"}},
            ]
        }
    rows = await session_contexts.find(filter_query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
    total = await session_contexts.count_documents(filter_query)
    contexts = []
    for row in rows:
        contexts.append(
            {
                "id": str(row["_id"]),
                "session_id": row["session_id"],
                "username": row.get("username", "Usuario Anonimo"),
                "created_at": _serialize_dt(row.get("created_at")),
                "updated_at": _serialize_dt(row.get("updated_at", row.get("created_at"))),
                "context": row.get("context", {}),
                "source": row.get("source", "unknown"),
                "version": row.get("version", 1),
                "is_active": row.get("is_active", True),
            }
        )
    return {
        "success": True,
        "data": {
            "contexts": contexts,
            "pagination": {"total": total, "limit": limit, "offset": offset, "has_next": offset + limit < total},
        },
    }


@router.get("/session-contexts/{session_id}")
async def get_session_context_details(session_id: str, container: AppContainer = Depends(get_container)) -> dict[str, Any]:
    """Fetch one full session context."""
    session_contexts = container.mongo.get_collection("session_contexts")
    context_doc = await session_contexts.find_one({"session_id": session_id})
    if not context_doc:
        raise HTTPException(status_code=404, detail="Contexto nao encontrado")
    return {
        "success": True,
        "data": {
            "id": str(context_doc["_id"]),
            "session_id": context_doc["session_id"],
            "username": context_doc.get("username", "Usuario Anonimo"),
            "created_at": _serialize_dt(context_doc.get("created_at")),
            "updated_at": _serialize_dt(context_doc.get("updated_at", context_doc.get("created_at"))),
            "context": context_doc.get("context", {}),
            "conversation_text": context_doc.get("conversation_text", ""),
            "emotions_data": context_doc.get("emotions_data", []),
            "source": context_doc.get("source", "unknown"),
            "version": context_doc.get("version", 1),
            "is_active": context_doc.get("is_active", True),
        },
    }


@router.get("/user-sessions")
async def list_all_user_sessions(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    status: str | None = None,
    personalized: bool | None = None,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """List all user therapeutic sessions with optional embedded contexts."""
    user_sessions = container.mongo.get_collection("user_therapeutic_sessions")
    session_contexts = container.mongo.get_collection("session_contexts")
    filter_query: dict[str, Any] = {}
    if search:
        filter_query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"title": {"$regex": search, "$options": "i"}},
            {"session_id": {"$regex": search, "$options": "i"}},
        ]
    if status:
        filter_query["status"] = status
    if personalized is not None:
        filter_query["personalized"] = personalized
    rows = await user_sessions.find(filter_query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
    total = await user_sessions.count_documents(filter_query)
    sessions = []
    for session in rows:
        session_context_id = f"{session['username']}_{session['session_id']}"
        context_doc = await session_contexts.find_one({"session_id": session_context_id})
        sessions.append(
            {
                "id": str(session["_id"]),
                "username": session["username"],
                "session_id": session["session_id"],
                "title": session.get("title", ""),
                "subtitle": session.get("subtitle", ""),
                "objective": session.get("objective", ""),
                "status": session.get("status", "locked"),
                "progress": session.get("progress", 0),
                "personalized": session.get("personalized", False),
                "created_at": _serialize_dt(session.get("created_at")),
                "completed_at": _serialize_dt(session.get("completed_at")),
                "focus_areas": session.get("focus_areas", []),
                "connection_to_previous": session.get("connection_to_previous", ""),
                "initial_prompt": session.get("initial_prompt", ""),
                "estimated_duration": session.get("estimated_duration", ""),
                "generation_method": session.get("generation_method", ""),
                "based_on_session": session.get("based_on_session", ""),
                "is_active": session.get("is_active", True),
                "has_context": context_doc is not None,
                "context": context_doc.get("context", {}) if context_doc else None,
                "context_created_at": _serialize_dt(context_doc.get("created_at")) if context_doc else None,
            }
        )
    return {
        "success": True,
        "data": {
            "sessions": sessions,
            "pagination": {"total": total, "limit": limit, "offset": offset, "has_next": offset + limit < total},
        },
    }
