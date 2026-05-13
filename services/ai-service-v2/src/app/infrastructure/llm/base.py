"""Shared contracts for runtime LLM providers."""

from __future__ import annotations

from typing import Any, Protocol

from ...application.llm.structured_outputs import GenerationOutput


class RuntimeProvider(Protocol):
    """Contract for one provider in the runtime chain."""

    name: str

    def is_available(self) -> bool:
        """Return whether this provider can handle requests right now."""

    async def generate(self, state: Any, prompt_payload: Any) -> GenerationOutput:
        """Generate one assistant response for the current graph state."""
