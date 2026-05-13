"""Next session planning scaffold."""

from typing import Any


class NextSessionService:
    """Future owner for next-session generation."""

    def preview(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return a scaffold summary for next-session planning."""
        return {
            "owner": "application.chat.next_session_service",
            "session_objective_present": bool(payload.get("session_objective")),
        }
