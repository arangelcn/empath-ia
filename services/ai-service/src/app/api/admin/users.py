"""Admin user management routes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...bootstrap.dependencies import AppContainer, get_container
from ..security import require_admin_permission


router = APIRouter(
    prefix="/api/admin",
    tags=["admin-users"],
    dependencies=[Depends(require_admin_permission("read"))],
)


class UserCreate(BaseModel):
    username: str
    email: str | None = None
    preferences: dict[str, Any] | None = None


class UserUpdate(BaseModel):
    email: str | None = None
    preferences: dict[str, Any] | None = None
    is_active: bool | None = None


def _serialize_user(user: dict[str, Any]) -> dict[str, Any]:
    data = dict(user)
    if "_id" in data:
        data["_id"] = str(data["_id"])
    for key in ("created_at", "updated_at", "last_login", "deactivated_at"):
        if isinstance(data.get(key), datetime):
            data[key] = data[key].isoformat()
    return data


async def _list_inferred_users_from_conversations(
    container: AppContainer,
    limit: int,
    offset: int,
    search: str | None = None,
) -> list[dict[str, Any]]:
    conversations = container.mongo.get_collection("conversations")
    match_stage: dict[str, Any] = {"username": {"$exists": True, "$nin": [None, ""]}}
    if search:
        match_stage["username"] = {"$regex": search, "$options": "i"}
    inferred_users = []
    async for row in conversations.aggregate(
        [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$username",
                    "last_login": {"$max": "$updated_at"},
                    "created_at": {"$min": "$created_at"},
                    "session_count": {"$sum": 1},
                }
            },
            {"$sort": {"last_login": -1}},
            {"$skip": offset},
            {"$limit": limit},
        ]
    ):
        username = row.get("_id")
        if not username:
            continue
        inferred_users.append(
            {
                "username": username,
                "email": username if "@" in username else None,
                "preferences": {},
                "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                "last_login": row.get("last_login").isoformat() if row.get("last_login") else None,
                "is_active": True,
                "session_count": row.get("session_count", 0),
                "inferred_from_conversations": True,
            }
        )
    return inferred_users


@router.post("/users", dependencies=[Depends(require_admin_permission("write"))])
async def create_user(user: UserCreate, container: AppContainer = Depends(get_container)) -> dict[str, Any]:
    """Create a user from the admin panel."""
    users = container.mongo.get_collection("users")
    existing = await users.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail=f"Usuario '{user.username}' ja existe")
    document = {
        "username": user.username,
        "email": user.email,
        "preferences": user.preferences or {},
        "created_at": datetime.now(UTC),
        "last_login": datetime.now(UTC),
        "is_active": True,
        "session_count": 0,
        "login_count": 0,
    }
    result = await users.insert_one(document)
    document["_id"] = str(result.inserted_id)
    return {"success": True, "user": document}


@router.get("/users")
async def list_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool | None = Query(None),
    search: str | None = None,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """List users with pagination and optional search."""
    users = container.mongo.get_collection("users")
    filter_query: dict[str, Any] = {}
    if active_only is True:
        filter_query["is_active"] = True
    elif active_only is False:
        filter_query["is_active"] = False
    if search:
        filter_query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    rows = await users.find(filter_query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
    total = await users.count_documents(filter_query)
    serialized = [_serialize_user(row) for row in rows]
    if not serialized and active_only is not False:
        serialized = await _list_inferred_users_from_conversations(container, limit, offset, search)
        total = len(await container.mongo.get_collection("conversations").distinct("username", {"username": {"$exists": True, "$nin": [None, ""]}}))
    return {
        "success": True,
        "data": {
            "users": serialized,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total,
            },
        },
    }


@router.get("/users/{username}")
async def get_user(username: str, container: AppContainer = Depends(get_container)) -> dict[str, Any]:
    """Fetch one user and their aggregate stats."""
    user = await container.user_repository.get_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    stats = await get_user_statistics(username, container)
    return {"success": True, "data": {"user": _serialize_user(user), "stats": stats["data"]}}


@router.put("/users/{username}", dependencies=[Depends(require_admin_permission("write"))])
async def update_user(
    username: str,
    user_update: UserUpdate,
    container: AppContainer = Depends(get_container),
) -> dict[str, Any]:
    """Update one user."""
    users = container.mongo.get_collection("users")
    existing = await users.find_one({"username": username})
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    update_fields: dict[str, Any] = {"updated_at": datetime.now(UTC)}
    if user_update.email is not None:
        update_fields["email"] = user_update.email
    if user_update.preferences is not None:
        update_fields["preferences"] = user_update.preferences
        if "full_name" in user_update.preferences:
            update_fields["full_name"] = user_update.preferences.get("full_name")
        if "display_name" in user_update.preferences:
            update_fields["display_name"] = user_update.preferences.get("display_name")
    if user_update.is_active is not None:
        update_fields["is_active"] = user_update.is_active
        if not user_update.is_active:
            update_fields["deactivated_at"] = datetime.now(UTC)
    await users.update_one({"username": username}, {"$set": update_fields})
    return {"success": True, "message": "Usuario atualizado com sucesso"}


@router.delete("/users/{username}", dependencies=[Depends(require_admin_permission("sensitive"))])
async def deactivate_user(username: str, container: AppContainer = Depends(get_container)) -> dict[str, Any]:
    """Soft-delete one user."""
    users = container.mongo.get_collection("users")
    result = await users.update_one(
        {"username": username},
        {"$set": {"is_active": False, "deactivated_at": datetime.now(UTC)}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return {"success": True, "message": "Usuario desativado com sucesso"}


@router.get("/users/{username}/stats")
async def get_user_statistics(username: str, container: AppContainer = Depends(get_container)) -> dict[str, Any]:
    """Return detailed user stats."""
    user = await container.user_repository.get_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    conversations = container.mongo.get_collection("conversations")
    messages = container.mongo.get_collection("messages")
    user_sessions = container.mongo.get_collection("user_therapeutic_sessions")
    stats = {
        "username": username,
        "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
        "last_login": user.get("last_login").isoformat() if user.get("last_login") else None,
        "login_count": user.get("login_count", 0),
        "session_count": user.get("session_count", 0),
        "conversation_count": await conversations.count_documents({"username": username}),
        "message_count": await messages.count_documents({"username": username}),
        "completed_sessions": await user_sessions.count_documents({"username": username, "status": "completed"}),
        "is_active": user.get("is_active", True),
        "preferences": user.get("preferences", {}),
    }
    return {"success": True, "data": stats}
