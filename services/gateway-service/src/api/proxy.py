"""Compatibility proxy routes for internal services."""

import httpx
from fastapi import APIRouter, HTTPException, Request

from ..config import SERVICE_URLS


router = APIRouter(tags=["Service Proxy"])


@router.post("/api/ai/chat")
async def ai_chat(request: Request):
    """Proxy para o serviço de IA (LEGADO)"""
    body = await request.json()

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['ai']}/chat",
                json=body,
                timeout=30,
            )
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Serviço AI indisponível: {str(exc)}") from exc
