"""Internal routes for ai-service-v2."""

from fastapi import APIRouter

from .compatibility import router as compatibility_router
from .health import router as health_router
from .llm import router as llm_router


router = APIRouter()
router.include_router(compatibility_router)
router.include_router(health_router)
router.include_router(llm_router)
