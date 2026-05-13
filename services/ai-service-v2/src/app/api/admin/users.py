"""Admin user routes."""

from fastapi import APIRouter

from ..shared import scaffold_payload


router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


@router.get("")
async def admin_users() -> dict[str, object]:
    """Scaffold admin users endpoint."""
    return scaffold_payload(
        route="/api/admin/users",
        area="admin-users",
    )
