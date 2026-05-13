"""Registration and persistence scaffold."""

from typing import Any


class RegistrationService:
    """Future owner for persistence side effects after chat execution."""

    def preview(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Describe which persistence actions will move here later."""
        return {
            "owner": "application.chat.registration_service",
            "chat_id": payload.get("chat_id"),
            "message_length": len(payload.get("message", "")),
        }
