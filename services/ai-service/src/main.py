"""Entrypoint do ai-service unificado."""

from datetime import UTC, datetime

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .app.api import register_routers
from .app.bootstrap.lifespan import build_lifespan
from .app.bootstrap.logging import configure_logging
from .app.bootstrap.settings import get_settings


configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=build_lifespan(),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routers(app)


@app.get("/")
async def root() -> dict[str, object]:
    """Landing endpoint do novo boundary unificado."""
    return {
        "service": settings.app_slug,
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "bootstrapped",
        "migration_phase": "compatibility-hardening",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict[str, object]:
    """Healthcheck de conveniência para o serviço."""
    return {
        "status": "healthy",
        "service": settings.app_slug,
        "version": settings.app_version,
        "migration_phase": "compatibility-hardening",
    }


@app.get("/health/all")
async def health_all(request: Request) -> dict[str, object]:
    """Expose a gateway-compatible aggregate health view."""
    container = request.app.state.container
    checked_at = datetime.now(UTC)
    service_urls = {
        "emotion-service": container.settings.emotion_service_url,
        "voice-service": container.settings.voice_service_url,
        "knowledge-service": container.settings.knowledge_service_url,
    }
    results: dict[str, object] = {}

    try:
        await container.mongo.client.admin.command("ping")
        database = "connected"
    except Exception:
        database = "error"

    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in service_urls.items():
            try:
                response = await client.get(f"{service_url}/health")
                results[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response": response.json() if response.status_code == 200 else None,
                }
            except Exception as exc:
                results[service_name] = {
                    "status": "unreachable",
                    "error": str(exc),
                }

    return {
        "gateway": "healthy",
        "database": database,
        "services": results,
        "timestamp": checked_at.isoformat(),
    }


@app.get("/config")
async def config() -> dict[str, object]:
    """Expose runtime configuration compatible with the old gateway contract."""
    return {
        "services": {
            "emotion": settings.emotion_service_url,
            "voice": settings.voice_service_url,
            "knowledge": settings.knowledge_service_url,
        },
        "database": {
            "type": "mongodb",
            "url": settings.mongodb_url,
            "database": settings.mongodb_database,
        },
        "timeout_settings": {
            "llm": None,
            "emotion_analysis": 30,
            "voice_synthesis": 120,
        },
        "gateway_port": 8001,
        "debug": settings.environment != "production",
        "version": settings.app_version,
        "features": [
            "mongodb",
            "chat_persistence",
            "session_management",
            "emotion_tracking",
            "session_context",
            "unified_backend",
        ],
    }
