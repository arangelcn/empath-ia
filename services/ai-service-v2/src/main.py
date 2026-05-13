"""Entrypoint do ai-service-v2."""

from fastapi import FastAPI

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
