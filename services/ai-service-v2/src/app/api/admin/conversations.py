"""Admin conversation routes."""

from fastapi import APIRouter

from ..shared import scaffold_payload


router = APIRouter(prefix="/api/admin/conversations", tags=["admin-conversations"])


@router.get("")
async def admin_conversations() -> dict[str, object]:
    """Scaffold admin conversations endpoint."""
    return scaffold_payload(
        route="/api/admin/conversations",
        area="admin-conversations",
    )
