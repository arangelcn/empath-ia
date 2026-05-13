"""Conversation repository contract."""

from typing import Protocol

from ..domain.conversations.models import ConversationRef


class ConversationRepository(Protocol):
    """Persistence contract for conversations."""

    async def resolve(self, conversation_ref: str) -> ConversationRef | None:
        """Resolve a public or legacy conversation reference."""
