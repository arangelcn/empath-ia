"""Gateway health and configuration routes."""

from datetime import datetime

import httpx
from fastapi import APIRouter

from ..config import SERVICE_URLS, settings


router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "gateway-service",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": ["chat_persistence", "mongodb", "conversation_history"],
        "services": SERVICE_URLS,
    }


@router.get("/")
async def root():
    return {
        "message": "empatIA Gateway Service v2.0",
        "description": "API Gateway com persistência MongoDB",
        "docs": "/docs",
        "services": list(SERVICE_URLS.keys()),
        "new_features": [
            "Persistência de conversas",
            "Histórico de mensagens",
            "MongoDB integrado",
            "Session management",
        ],
    }


@router.get("/health/all")
async def health_all():
    """Verificar saúde de todos os serviços"""
    results = {}

    async with httpx.AsyncClient() as client:
        for service_name, service_url in SERVICE_URLS.items():
            try:
                response = await client.get(f"{service_url}/health", timeout=5)
                results[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response": response.json() if response.status_code == 200 else None,
                }
            except Exception as e:
                results[service_name] = {
                    "status": "unreachable",
                    "error": str(e),
                }

    return {
        "gateway": "healthy",
        "database": "connected",
        "services": results,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/config")
async def get_config():
    """Retorna configurações do gateway"""
    return {
        "services": SERVICE_URLS,
        "database": {
            "type": "mongodb",
            "url": settings.mongodb_url,
            "database": settings.mongodb_database,
        },
        "timeout_settings": {
            "ai_chat": 30,
            "avatar_generation": 60,
            "emotion_analysis": 30,
        },
        "gateway_port": settings.gateway_port,
        "debug": settings.debug,
        "version": "2.0.0",
        "features": [
            "mongodb",
            "chat_persistence",
            "session_management",
            "emotion_tracking",
            "session_context",
        ],
    }
