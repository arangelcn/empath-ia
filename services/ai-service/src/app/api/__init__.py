"""Router registration for ai-service."""

from fastapi import APIRouter, FastAPI

from .admin import router as admin_router
from .internal import router as internal_router
from .public import router as public_router


def register_routers(app: FastAPI) -> None:
    """Attach all route groups to the FastAPI app."""
    api_router = APIRouter()
    api_router.include_router(public_router)
    api_router.include_router(admin_router)
    api_router.include_router(internal_router)
    app.include_router(api_router)
