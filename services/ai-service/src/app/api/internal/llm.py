"""Internal LLM routes."""

from fastapi import APIRouter, Depends

from ...bootstrap.dependencies import AppContainer, get_container


router = APIRouter(prefix="/internal/llm", tags=["internal-llm"])


@router.get("/status")
async def llm_status(
    container: AppContainer = Depends(get_container),
) -> dict[str, object]:
    """Expose the current runtime status."""
    return container.runtime_service.describe()
