"""Prompt repository contract."""

from typing import Protocol

from ..domain.prompts.models import PromptDescriptor


class PromptRepository(Protocol):
    """Persistence contract for prompt definitions."""

    async def get_active(self, prompt_key: str) -> PromptDescriptor | None:
        """Fetch the active prompt descriptor for a key."""
