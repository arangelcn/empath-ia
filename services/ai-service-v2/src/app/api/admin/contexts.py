"""Admin context routes."""

from fastapi import APIRouter

from ..shared import scaffold_payload


router = APIRouter(prefix="/api/admin/contexts", tags=["admin-contexts"])


@router.get("")
async def admin_contexts() -> dict[str, object]:
    """Scaffold admin contexts endpoint."""
    return scaffold_payload(
        route="/api/admin/contexts",
        area="admin-contexts",
    )
