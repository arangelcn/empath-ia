"""
Legacy admin router placeholder.

Admin endpoints live in focused modules:
admin_dashboard, admin_knowledge, admin_conversations, admin_sessions,
admin_users and admin_contexts.
"""

from fastapi import APIRouter, Depends

from .auth import require_admin_permission

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin_permission("read"))],
)
