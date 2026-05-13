"""Internal health routes."""

from fastapi import APIRouter, Depends

from ...bootstrap.dependencies import AppContainer, get_container


router = APIRouter(prefix="/internal/health", tags=["internal-health"])


@router.get("")
async def internal_health(
    container: AppContainer = Depends(get_container),
) -> dict[str, object]:
    """Return detailed scaffold health information."""
    return {
        "status": "healthy",
        "service": container.settings.app_slug,
        "migration_phase": "scaffold",
        "components": {
            "chat_facade": "ready",
            "agent_service": "ready",
            "runtime_service": "scaffold",
            "retrieval_gateway": "scaffold",
        },
    }
