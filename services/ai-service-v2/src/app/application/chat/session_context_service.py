"""Session context application service scaffold."""

from typing import Any


class SessionContextService:
    """Future owner for session context within the unified boundary."""

    def preview(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return the context ownership preview used during scaffold phase."""
        return {
            "owner": "application.chat.session_context_service",
            "session_id": payload.get("session_id"),
            "has_previous_session_context": bool(payload.get("previous_session_context")),
        }
