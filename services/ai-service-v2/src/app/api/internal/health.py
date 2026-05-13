"""Internal health routes."""

from fastapi import APIRouter, Depends

from ...bootstrap.dependencies import AppContainer, get_container


router = APIRouter(prefix="/internal/health", tags=["internal-health"])


@router.get("")
async def internal_health(
    container: AppContainer = Depends(get_container),
) -> dict[str, object]:
    """Return operational migration health information."""
    runtime = container.runtime_service.describe()
    return {
        "status": "healthy",
        "service": container.settings.app_slug,
        "migration_phase": "compatibility-hardening",
        "components": {
            "chat_facade": "ready",
            "agent_service": "ready",
            "stream_facade": "ready",
            "runtime_service": runtime.get("status", "unknown"),
            "retrieval_gateway": "ready",
            "registration_flow": "internalized",
            "legacy_gateway_dependency": "removed",
        },
        "runtime": runtime,
    }
