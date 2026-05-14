"""Admin therapeutic session template routes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...bootstrap.dependencies import AppContainer, get_container
from ..security import require_admin_permission


router = APIRouter(
    prefix="/api/admin",
    tags=["admin-sessions"],
    dependencies=[Depends(require_admin_permission("read"))],
)


class TherapeuticSessionCreate(BaseModel):
    session_id: str
    title: str
    subtitle: str
    objective: str
    initial_prompt: str
    is_active: bool = True


class TherapeuticSessionUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    objective: str | None = None
    initial_prompt: str | None = None
    is_active: bool | None = None


def _serialize_session(session: dict[str, Any]) -> dict[str, Any]:
    data = dict(session)
    if "_id" in data:
        data["_id"] = str(data["_id"])
    for key in ("created_at", "updated_at"):
        if isinstance(data.get(key), datetime):
            data[key] = data[key].isoformat()
    return data


@router.post("/therapeutic-sessions", dependencies=[Depends(require_admin_permission("write"))])
async def create_therapeutic_session(
    session: TherapeuticSessionCreate,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """Create one therapeutic session template."""
    collection = container.mongo.get_collection("therapeutic_sessions")
    existing = await collection.find_one({"session_id": session.session_id})
    if existing:
        raise HTTPException(status_code=400, detail=f"Sessao '{session.session_id}' ja existe")
    document = {
        "session_id": session.session_id,
        "title": session.title,
        "subtitle": session.subtitle,
        "objective": session.objective,
        "initial_prompt": session.initial_prompt,
        "is_active": session.is_active,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    result = await collection.insert_one(document)
    document["_id"] = str(result.inserted_id)
    return {"success": True, "data": _serialize_session(document)}


@router.get("/therapeutic-sessions")
async def list_therapeutic_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(False),
    search: str | None = None,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """List therapeutic session templates."""
    collection = container.mongo.get_collection("therapeutic_sessions")
    filter_query: dict[str, Any] = {}
    if active_only:
        filter_query["is_active"] = True
    if search:
        filter_query["$or"] = [
            {"session_id": {"$regex": search, "$options": "i"}},
            {"title": {"$regex": search, "$options": "i"}},
            {"subtitle": {"$regex": search, "$options": "i"}},
        ]
    rows = await collection.find(filter_query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
    total = await collection.count_documents(filter_query)
    return {
        "success": True,
        "data": {
            "sessions": [_serialize_session(row) for row in rows],
            "pagination": {"total": total, "limit": limit, "offset": offset, "has_next": offset + limit < total},
        },
    }


@router.get("/therapeutic-sessions/{session_id}")
async def get_therapeutic_session(session_id: str, container: AppContainer = Depends(get_container)) -> dict[str, Any]:
    """Fetch one therapeutic session template."""
    collection = container.mongo.get_collection("therapeutic_sessions")
    session = await collection.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Sessao terapeutica nao encontrada")
    return {"success": True, "data": _serialize_session(session)}


@router.put("/therapeutic-sessions/{session_id}", dependencies=[Depends(require_admin_permission("write"))])
async def update_therapeutic_session(
    session_id: str,
    session_update: TherapeuticSessionUpdate,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """Update one therapeutic session template."""
    collection = container.mongo.get_collection("therapeutic_sessions")
    update_data = {field: value for field, value in session_update.model_dump().items() if value is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhuma alteracao foi enviada")
    update_data["updated_at"] = datetime.now(UTC)
    result = await collection.update_one({"session_id": session_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sessao terapeutica nao encontrada")
    return {"success": True, "data": {"session_id": session_id, "message": "Sessao terapeutica atualizada com sucesso"}}


@router.delete("/therapeutic-sessions/{session_id}", dependencies=[Depends(require_admin_permission("sensitive"))])
async def delete_therapeutic_session(session_id: str, container: AppContainer = Depends(get_container)) -> dict[str, Any]:
    """Delete one therapeutic session template."""
    collection = container.mongo.get_collection("therapeutic_sessions")
    result = await collection.delete_one({"session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sessao terapeutica nao encontrada")
    return {"success": True, "data": {"session_id": session_id, "message": "Sessao terapeutica deletada com sucesso"}}
