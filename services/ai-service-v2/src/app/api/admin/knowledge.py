"""Admin knowledge routes."""

from fastapi import APIRouter

from ..shared import scaffold_payload


router = APIRouter(prefix="/api/admin/knowledge", tags=["admin-knowledge"])


@router.get("")
async def admin_knowledge() -> dict[str, object]:
    """Scaffold admin knowledge endpoint."""
    return scaffold_payload(
        route="/api/admin/knowledge",
        area="admin-knowledge",
        extra={"delegates_to": "knowledge-service"},
    )
