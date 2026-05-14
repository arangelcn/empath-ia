"""Admin routes for ai-service."""

from fastapi import APIRouter

from .contexts import router as contexts_router
from .conversations import router as conversations_router
from .dashboard import router as dashboard_router
from .knowledge import router as knowledge_router
from .sessions import router as sessions_router
from .users import router as users_router


router = APIRouter()
router.include_router(dashboard_router)
router.include_router(conversations_router)
router.include_router(users_router)
router.include_router(sessions_router)
router.include_router(contexts_router)
router.include_router(knowledge_router)
