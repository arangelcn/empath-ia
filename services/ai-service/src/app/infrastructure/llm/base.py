"""Shared contracts for runtime LLM providers."""

from __future__ import annotations

from typing import Any, AsyncIterator, Protocol

from ...application.llm.structured_outputs import GenerationOutput


class RuntimeProvider(Protocol):
    """Contract for one provider in the runtime chain."""

    name: str

    def is_available(self) -> bool:
        """Return whether this provider can handle requests right now."""

    def supports_stream(self) -> bool:
        """Return whether this provider can stream generation deltas."""

    async def generate(self, state: Any, prompt_payload: Any) -> GenerationOutput:
        """Generate one assistant response for the current graph state."""

    async def stream_generate(
        self,
        state: Any,
        prompt_payload: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield provider-native streaming events and a final output event."""
