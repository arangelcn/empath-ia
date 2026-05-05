"""Prompt management routes."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..services.prompt_service import PromptService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/prompts", tags=["Prompts"])
prompt_service = PromptService()


@router.post("")
async def create_prompt(prompt_data: dict):
    """Criar novo prompt"""
    try:
        return await prompt_service.create_prompt(prompt_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("❌ Erro ao criar prompt: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


@router.get("/stats")
async def get_prompt_stats():
    """Obter estatísticas dos prompts"""
    try:
        return await prompt_service.get_prompt_stats()
    except Exception as exc:
        logger.error("❌ Erro ao obter estatísticas de prompts: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


@router.post("/initialize")
async def initialize_default_prompts():
    """Inicializar prompts padrão do sistema"""
    try:
        return await prompt_service.create_default_prompts()
    except Exception as exc:
        logger.error("❌ Erro ao inicializar prompts padrão: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


@router.get("/active/{prompt_key}")
async def get_active_prompt(prompt_key: str):
    """Buscar prompt ativo por chave"""
    try:
        prompt = await prompt_service.get_active_prompt(prompt_key)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt ativo não encontrado")
        return prompt
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("❌ Erro ao buscar prompt ativo: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


@router.get("/type/{prompt_type}")
async def get_prompts_by_type(prompt_type: str):
    """Buscar prompts por tipo"""
    try:
        prompts = await prompt_service.get_prompts_by_type(prompt_type)
        return {"prompts": prompts}
    except Exception as exc:
        logger.error("❌ Erro ao buscar prompts por tipo: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


@router.post("/render/{prompt_key}")
async def render_prompt(prompt_key: str, variables: dict):
    """Renderizar prompt com variáveis"""
    try:
        rendered = await prompt_service.render_prompt(prompt_key, variables)
        if not rendered:
            raise HTTPException(status_code=404, detail="Prompt não encontrado ou não pôde ser renderizado")
        return {"rendered_content": rendered}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("❌ Erro ao renderizar prompt: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


@router.get("/{prompt_key}")
async def get_prompt(prompt_key: str):
    """Buscar prompt por chave"""
    try:
        prompt = await prompt_service.get_prompt(prompt_key)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt não encontrado")
        return prompt
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("❌ Erro ao buscar prompt: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


@router.put("/{prompt_key}")
async def update_prompt(prompt_key: str, update_data: dict):
    """Atualizar prompt"""
    try:
        return await prompt_service.update_prompt(prompt_key, update_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("❌ Erro ao atualizar prompt: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


@router.delete("/{prompt_key}")
async def delete_prompt(prompt_key: str):
    """Deletar prompt (soft delete)"""
    try:
        return await prompt_service.delete_prompt(prompt_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("❌ Erro ao deletar prompt: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc


@router.get("")
async def list_prompts(prompt_type: Optional[str] = None, active_only: bool = True):
    """Listar prompts com filtros"""
    try:
        prompts = await prompt_service.list_prompts(prompt_type=prompt_type, active_only=active_only)
        return {"prompts": prompts}
    except Exception as exc:
        logger.error("❌ Erro ao listar prompts: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno do servidor") from exc
