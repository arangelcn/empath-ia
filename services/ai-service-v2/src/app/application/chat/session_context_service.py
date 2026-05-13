"""Session context helpers for migrated chat flows."""

from __future__ import annotations

from typing import Any

from ...domain.conversations.identity import build_legacy_session_id, split_composite_session_id
from ...repositories.conversations import MongoConversationRepository


class SessionContextService:
    """Owner for previous-session context lookup during the migration."""

    def __init__(self, conversation_repository: MongoConversationRepository) -> None:
        self.conversation_repository = conversation_repository

    async def get_previous_context(self, current_session_id: str) -> dict[str, Any] | None:
        """Load the previous saved session context when available."""
        username = self.conversation_repository.extract_username(current_session_id)
        if not username:
            return None

        current_session_number = self._extract_session_number(current_session_id)
        if current_session_number <= 1:
            return None

        previous_session_id = build_legacy_session_id(username, f"session-{current_session_number - 1}")
        return await self.conversation_repository.get_session_context(previous_session_id)

    def detect_conversation_end(self, message: str) -> bool:
        """Use the same farewell heuristics already used by the gateway."""
        message_lower = message.lower().strip()
        farewell_patterns = [
            "tchau",
            "adeus",
            "até logo",
            "até mais",
            "até breve",
            "bye",
            "goodbye",
            "see you",
            "até a próxima",
            "obrigado pela conversa",
            "obrigada pela conversa",
            "foi bom conversar",
            "preciso ir",
            "tenho que ir",
            "vou desligar",
            "vou sair",
            "até outra hora",
            "muito obrigado",
            "muito obrigada",
            "valeu pela ajuda",
            "foi ótimo",
            "me ajudou muito",
            "estou melhor agora",
        ]
        finalization_patterns = [
            "acabou",
            "terminou",
            "é isso",
            "só isso mesmo",
            "não tenho mais nada",
            "acho que é só",
            "por hoje é só",
            "é tudo por hoje",
        ]
        return any(pattern in message_lower for pattern in farewell_patterns + finalization_patterns)

    def preview(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Keep the preview used by scaffold introspection."""
        return {
            "owner": "application.chat.session_context_service",
            "session_id": payload.get("session_id"),
            "has_previous_session_context": bool(payload.get("previous_session_context")),
        }

    @staticmethod
    def _extract_session_number(session_id: str) -> int:
        _, original_session_id = split_composite_session_id(session_id)
        session_token = original_session_id if original_session_id.startswith("session-") else session_id
        if session_token.startswith("session-"):
            try:
                return int(session_token.split("-", 1)[1])
            except ValueError:
                return 0
        return 0
