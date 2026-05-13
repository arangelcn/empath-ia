"""Runtime abstraction used during the migration."""

from __future__ import annotations

from typing import Any

from .structured_outputs import GenerationOutput
from ...infrastructure.http.legacy_ai_client import LegacyAIClient
from ...infrastructure.llm.base import RuntimeProvider


class RuntimeService:
    """Runtime owner for LangGraph generation, with legacy adapter as fallback."""

    def __init__(
        self,
        legacy_ai_client: LegacyAIClient | None,
        providers: list[RuntimeProvider] | None = None,
    ) -> None:
        self.legacy_ai_client = legacy_ai_client
        self.providers = providers or []

    async def generate(self, state, prompt_payload: Any) -> GenerationOutput:
        """Generate the assistant response for the graph generation node."""
        for provider in self.providers:
            if not provider.is_available():
                continue
            result = await provider.generate(state, prompt_payload)
            if result.text.strip():
                return result

        return GenerationOutput(
            text=(
                "Runtime LLM ainda nao configurado no ai-service-v2. "
                "A cadeia de providers existe, mas nenhum backend esta disponivel."
            ),
            provider="runtime_unavailable",
            model="unconfigured",
            finish_reason="runtime_not_configured",
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
            "provider_chain": [provider.name for provider in self.providers],
            "available_providers": [
                provider.name for provider in self.providers if provider.is_available()
            ],
            "message": "Runtime pronto para LangChain; adapter legado mantido apenas como fallback temporario.",
            "legacy_ai_base_url": self.legacy_ai_client.base_url if self.legacy_ai_client else None,
        }
