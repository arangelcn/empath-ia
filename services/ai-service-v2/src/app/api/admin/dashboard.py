"""Admin dashboard routes."""

from fastapi import APIRouter

from ..shared import scaffold_payload


router = APIRouter(prefix="/api/admin/dashboard", tags=["admin-dashboard"])


@router.get("")
async def admin_dashboard() -> dict[str, object]:
    """Scaffold admin dashboard endpoint."""
    return scaffold_payload(
        route="/api/admin/dashboard",
        area="admin-dashboard",
    )
