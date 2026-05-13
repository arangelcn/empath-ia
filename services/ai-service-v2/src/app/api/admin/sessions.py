"""Admin session routes."""

from fastapi import APIRouter

from ..shared import scaffold_payload


router = APIRouter(prefix="/api/admin/sessions", tags=["admin-sessions"])


@router.get("")
async def admin_sessions() -> dict[str, object]:
    """Scaffold admin sessions endpoint."""
    return scaffold_payload(
        route="/api/admin/sessions",
        area="admin-sessions",
    )
