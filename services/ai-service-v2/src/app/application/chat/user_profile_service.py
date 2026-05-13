"""User profile normalization for migrated chat flows."""

from __future__ import annotations

import logging
from typing import Any

from ...domain.users.display import first_name_from_user
from ...repositories.conversations import MongoConversationRepository


logger = logging.getLogger(__name__)


class UserProfileService:
    """Build the profile payload expected by the legacy ai-service."""

    def __init__(self, conversation_repository: MongoConversationRepository) -> None:
        self.conversation_repository = conversation_repository

    async def get_user_profile(self, username: str) -> dict[str, Any]:
        """Fetch and normalize a user profile from the existing Mongo collections."""
        user = await self.conversation_repository.get_user_document(username)
        user_profile: dict[str, Any] = {}
        preferences = (user or {}).get("preferences", {})
        preferred_name = first_name_from_user(user, username)
        display_name = (
            (user or {}).get("display_name")
            or preferences.get("display_name")
            or (user or {}).get("full_name")
            or preferences.get("full_name")
        )

        if user and user.get("user_profile"):
            user_profile = dict(user["user_profile"])

        user_profile["username"] = username
        user_profile["preferences"] = preferences
        if preferred_name:
            user_profile["preferred_name"] = preferred_name
        if display_name:
            user_profile["display_name"] = display_name
            user_profile["full_name"] = (
                (user or {}).get("full_name")
                or preferences.get("full_name")
                or display_name
            )

        session_1_context = await self.conversation_repository.get_by_session_id(f"{username}_session-1")
        if session_1_context and session_1_context.get("registration_data"):
            registration_data = session_1_context["registration_data"]
            user_profile["registration_data"] = registration_data
            if not user_profile.get("profile_summary"):
                summary_parts = []
                if registration_data.get("idade"):
                    summary_parts.append(f"{registration_data['idade']} anos")
                if registration_data.get("ocupacao"):
                    summary_parts.append(str(registration_data["ocupacao"]))
                if registration_data.get("localizacao"):
                    summary_parts.append(f"de {registration_data['localizacao']}")
                if summary_parts:
                    user_profile["profile_summary"] = f"Usuário {username}: {', '.join(summary_parts)}"

        if user_profile:
            return user_profile

        logger.warning("Perfil minimo carregado para %s", username)
        return {
            "username": username,
            "preferences": preferences,
            "preferred_name": preferred_name,
            "display_name": display_name,
            "profile_summary": f"Usuário {username} - dados limitados",
            "registration_data": {},
            "personal_info": {},
            "therapeutic_info": {},
        }
