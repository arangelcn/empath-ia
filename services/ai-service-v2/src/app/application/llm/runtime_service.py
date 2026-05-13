"""Runtime abstraction used during the migration."""

from __future__ import annotations

from typing import Any

from .structured_outputs import GenerationOutput
from ...infrastructure.http.legacy_ai_client import LegacyAIClient


class RuntimeService:
    """Runtime owner for LangGraph generation, with legacy adapter as fallback."""

    def __init__(self, legacy_ai_client: LegacyAIClient | None) -> None:
        self.legacy_ai_client = legacy_ai_client

    async def generate(self, state, prompt_payload: Any) -> GenerationOutput:
        """Generate the assistant response for the graph generation node."""
        if self.legacy_ai_client is None:
            return GenerationOutput(
                text=(
                    "Runtime LLM ainda nao configurado no ai-service-v2. "
                    "O grafo e a pipeline estao prontos para receber LangChain providers."
                ),
                provider="langgraph-scaffold",
                model="unconfigured",
                finish_reason="runtime_not_configured",
            )

        legacy_payload = {
            "message": state.user_message,
            "session_id": state.session_id,
            "chat_id": state.chat_id,
            "username": state.username,
            "user_profile": state.user_profile,
            "conversation_history": state.conversation_history,
            "session_objective": state.session_objective,
            "previous_session_context": state.previous_session_context,
        }
        raw_response = await self.legacy_ai_client.chat(legacy_payload)
        return GenerationOutput(
            text=raw_response.get("response", ""),
            provider=raw_response.get("provider", "ai-service"),
            model=raw_response.get("model", "unknown"),
            finish_reason="legacy_adapter",
        )

    async def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a non-streaming chat call through the legacy ai-service."""
        if self.legacy_ai_client is None:
            raise RuntimeError("Legacy AI client nao configurado")
        return await self.legacy_ai_client.chat(payload)

    async def stream_chat(self, payload: dict[str, Any]):
        """Execute a streaming chat call through the legacy ai-service."""
        if self.legacy_ai_client is None:
            raise RuntimeError("Legacy AI client nao configurado")
        async for event in self.legacy_ai_client.stream_chat(payload):
            yield event

    def describe(self) -> dict[str, object]:
        """Describe the temporary runtime mode."""
        return {
            "service": "ai-service-v2",
            "owner": "application.llm.runtime_service",
            "status": "langchain-runtime-shell",
            "provider_chain": ["langchain-provider", "legacy-ai-adapter"],
            "message": "Runtime pronto para LangChain; adapter legado mantido apenas como fallback temporario.",
            "legacy_ai_base_url": self.legacy_ai_client.base_url if self.legacy_ai_client else None,
        }
