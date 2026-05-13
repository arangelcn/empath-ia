"""Legacy ai-service runtime provider."""

from __future__ import annotations

from typing import Any, AsyncIterator

from ...application.llm.structured_outputs import GenerationOutput
from ..http.legacy_ai_client import LegacyAIClient


class LegacyAdapterProvider:
    """Fallback provider that delegates generation to the old ai-service."""

    name = "legacy_ai"

    def __init__(self, client: LegacyAIClient | None) -> None:
        self.client = client

    def is_available(self) -> bool:
        """Return whether the legacy client is configured."""
        return self.client is not None

    def supports_stream(self) -> bool:
        """Return whether this provider has a provider-native stream implementation."""
        return False

    async def generate(self, state: Any, prompt_payload: Any) -> GenerationOutput:
        """Generate through the current legacy ai-service contract."""
        if self.client is None:
            return GenerationOutput(
                text="",
                provider=self.name,
                model="unconfigured",
                finish_reason="provider_unavailable",
            )

        raw_response = await self.client.chat(
            {
                "message": state.user_message,
                "session_id": state.session_id,
                "chat_id": state.chat_id,
                "username": state.username,
                "user_profile": state.user_profile,
                "conversation_history": state.conversation_history,
                "session_objective": state.session_objective,
                "previous_session_context": state.previous_session_context,
            }
        )
        return GenerationOutput(
            text=raw_response.get("response", ""),
            provider=raw_response.get("provider", self.name),
            model=raw_response.get("model", "legacy"),
            finish_reason="legacy_adapter",
        )

    async def stream_generate(
        self,
        state: Any,
        prompt_payload: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Expose a final-only streaming contract for compatibility in the runtime chain."""
        result = await self.generate(state, prompt_payload)
        yield {"type": "final", "output": result}
