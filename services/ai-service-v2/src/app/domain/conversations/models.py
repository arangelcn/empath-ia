"""Conversation domain models."""

from dataclasses import dataclass


@dataclass(slots=True)
class ConversationRef:
    """Public/legacy identity bridge for conversations."""

    chat_id: str | None
    session_id: str
    username: str
