"""
Admin user management endpoints.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..models.database import get_collection
from ..services.user_service import UserService
from .auth import require_admin_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin_permission("read"))],
)

user_service = UserService()


async def _list_inferred_users_from_conversations(
    limit: int,
    offset: int,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fallback: infer users from conversation history when `users` collection is empty."""
    conversations = get_collection("conversations")

    match_stage: Dict[str, Any] = {
        "username": {"$exists": True, "$nin": [None, ""]}
    }
    if search:
        match_stage["username"] = {"$regex": search, "$options": "i"}

    pipeline = [
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

    inferred_users: List[Dict[str, Any]] = []
    async for row in conversations.aggregate(pipeline):
        username = row.get("_id")
        if not username:
            continue
        inferred_users.append(
            {
                "username": username,
                "email": username if "@" in username else None,
                "preferences": {},
                "created_at": row.get("created_at"),
                "last_login": row.get("last_login"),
                "is_active": True,
                "session_count": row.get("session_count", 0),
                "inferred_from_conversations": True,
            }
        )

    return inferred_users


async def _count_inferred_users_from_conversations(search: Optional[str] = None) -> int:
    conversations = get_collection("conversations")

    match_stage: Dict[str, Any] = {
        "username": {"$exists": True, "$nin": [None, ""]}
    }
    if search:
        match_stage["username"] = {"$regex": search, "$options": "i"}

    return len(await conversations.distinct("username", match_stage))


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


@router.post("/users", dependencies=[Depends(require_admin_permission("write"))])
async def create_user(user: UserCreate):
    """
    Criar novo usuário
    """
    try:
        result = await user_service.create_user(
            username=user.username,
            email=user.email,
            preferences=user.preferences
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: Optional[bool] = Query(None),
    search: Optional[str] = None
):
    """
    Listar usuários com paginação e busca
    """
    try:
        users = await user_service.list_users(
            limit=limit,
            offset=offset,
            active_only=active_only
        )

        # Filtrar por busca se especificado
        if search:
            users = [u for u in users if search.lower() in u["username"].lower()]

        # Fallback para ambientes onde a coleção users ainda não está populada.
        if not users and active_only is not False:
            users = await _list_inferred_users_from_conversations(limit=limit, offset=offset, search=search)

        # Contar total para paginação
        total_users = await user_service.list_users(limit=1000, active_only=active_only)
        if search:
            total_users = [u for u in total_users if search.lower() in u["username"].lower()]
        if not total_users and active_only is not False:
            total_count = await _count_inferred_users_from_conversations(search=search)
        else:
            total_count = len(total_users)

        return {
            "success": True,
            "data": {
                "users": users,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_next": offset + limit < total_count
                }
            }
        }

    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{username}")
async def get_user(username: str):
    """
    Obter detalhes de um usuário
    """
    try:
        user = await user_service.get_user(username)

        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Obter estatísticas do usuário
        stats = await user_service.get_user_stats(username)

        return {
            "success": True,
            "data": {
                "user": user,
                "stats": stats
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{username}", dependencies=[Depends(require_admin_permission("write"))])
async def update_user(username: str, user_update: UserUpdate):
    """
    Atualizar usuário
    """
    try:
        user = await user_service.get_user(username)

        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Atualizar preferências se fornecidas
        if user_update.preferences is not None:
            await user_service.update_user_preferences(username, user_update.preferences)

        # Atualizar outros campos se necessário
        if user_update.is_active is not None and not user_update.is_active:
            await user_service.deactivate_user(username)

        return {
            "success": True,
            "message": "Usuário atualizado com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{username}", dependencies=[Depends(require_admin_permission("sensitive"))])
async def deactivate_user(username: str):
    """
    Desativar usuário
    """
    try:
        success = await user_service.deactivate_user(username)

        if not success:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        return {
            "success": True,
            "message": "Usuário desativado com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao desativar usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{username}/stats")
async def get_user_statistics(username: str):
    """
    Obter estatísticas detalhadas de um usuário
    """
    try:
        stats = await user_service.get_user_stats(username)

        if not stats:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        return {
            "success": True,
            "data": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))
