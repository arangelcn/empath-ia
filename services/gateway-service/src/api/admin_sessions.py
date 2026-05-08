"""
Admin therapeutic session template endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..services.therapeutic_session_service import TherapeuticSessionService
from .auth import require_admin_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin_permission("read"))],
)

therapeutic_session_service = TherapeuticSessionService()


class TherapeuticSessionCreate(BaseModel):
    session_id: str
    title: str
    subtitle: str
    objective: str
    initial_prompt: str
    is_active: bool = True


class TherapeuticSessionUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    objective: Optional[str] = None
    initial_prompt: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/therapeutic-sessions", dependencies=[Depends(require_admin_permission("write"))])
async def create_therapeutic_session(session: TherapeuticSessionCreate):
    """
    Criar nova sessão terapêutica
    """
    try:
        session_data = {
            "session_id": session.session_id,
            "title": session.title,
            "subtitle": session.subtitle,
            "objective": session.objective,
            "initial_prompt": session.initial_prompt,
            "is_active": session.is_active
        }

        result = await therapeutic_session_service.create_session(session_data)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao criar sessão terapêutica: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/therapeutic-sessions")
async def list_therapeutic_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(False),
    search: Optional[str] = None
):
    """
    Listar sessões terapêuticas com paginação e filtros
    """
    try:
        result = await therapeutic_session_service.list_sessions(
            limit=limit,
            offset=offset,
            active_only=active_only,
            search=search
        )
        return result

    except Exception as e:
        logger.error(f"Erro ao listar sessões terapêuticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/therapeutic-sessions/{session_id}")
async def get_therapeutic_session(session_id: str):
    """
    Obter detalhes de uma sessão terapêutica
    """
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
                "updated_at": session["updated_at"].isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter sessão terapêutica: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/therapeutic-sessions/{session_id}", dependencies=[Depends(require_admin_permission("write"))])
async def update_therapeutic_session(session_id: str, session_update: TherapeuticSessionUpdate):
    """
    Atualizar uma sessão terapêutica
    """
    try:
        # Preparar dados para atualização
        update_data = {}

        if session_update.title is not None:
            update_data["title"] = session_update.title
        if session_update.subtitle is not None:
            update_data["subtitle"] = session_update.subtitle
        if session_update.objective is not None:
            update_data["objective"] = session_update.objective
        if session_update.initial_prompt is not None:
            update_data["initial_prompt"] = session_update.initial_prompt
        if session_update.is_active is not None:
            update_data["is_active"] = session_update.is_active

        success = await therapeutic_session_service.update_session(session_id, update_data)

        if not success:
            raise HTTPException(status_code=400, detail="Nenhuma alteração foi feita")

        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "message": "Sessão terapêutica atualizada com sucesso"
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao atualizar sessão terapêutica: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/therapeutic-sessions/{session_id}", dependencies=[Depends(require_admin_permission("sensitive"))])
async def delete_therapeutic_session(session_id: str):
    """
    Deletar uma sessão terapêutica
    """
    try:
        success = await therapeutic_session_service.delete_session(session_id)

        if not success:
            raise HTTPException(status_code=400, detail="Erro ao deletar sessão")

        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "message": "Sessão terapêutica deletada com sucesso"
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao deletar sessão terapêutica: {e}")
        raise HTTPException(status_code=500, detail=str(e))
