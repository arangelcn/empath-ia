"""Runtime abstraction used by the unified backend."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, AsyncIterator

from .structured_outputs import GenerationOutput
from ...infrastructure.llm.base import RuntimeProvider


class RuntimeService:
    """Runtime owner for LangGraph generation."""

    def __init__(
        self,
        providers: list[RuntimeProvider] | None = None,
    ) -> None:
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
                "Runtime LLM ainda nao configurado no ai-service. "
                "A cadeia de providers existe, mas nenhum backend esta disponivel."
            ),
            provider="runtime_unavailable",
            model="unconfigured",
            finish_reason="runtime_not_configured",
        )

    async def complete_text(
        self,
        *,
        prompt: str,
        system: str = "Voce e um assistente que responde de forma concisa e objetiva.",
    ) -> GenerationOutput:
        """Run a lightweight completion without the therapeutic orchestration pipeline."""
        state = SimpleNamespace(
            conversation_history=[],
            user_message=prompt,
            previous_session_context={},
            user_profile={},
            retrieval_result={},
            citations=[],
        )
        prompt_payload = {
            "system": system,
            "retrieval_context": "",
            "citations_summary": "",
        }
        return await self.generate(state, prompt_payload)

    async def stream_generate(
        self,
        state,
        prompt_payload: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Generate through the provider chain, preserving native stream support when available."""
        for provider in self.providers:
            if not provider.is_available():
                continue

            if provider.supports_stream():
                try:
                    async for event in provider.stream_generate(state, prompt_payload):
                        yield event
                        if event.get("type") == "final":
                            output = event.get("output")
                            if isinstance(output, GenerationOutput) and output.text.strip():
                                return
                except Exception:
                    continue
                continue

            result = await provider.generate(state, prompt_payload)
            yield {"type": "final", "output": result}
            if result.text.strip():
                return

        yield {
            "type": "final",
            "output": GenerationOutput(
                text=(
                    "Runtime LLM ainda nao configurado no ai-service. "
                    "A cadeia de providers existe, mas nenhum backend esta disponivel."
                ),
                provider="runtime_unavailable",
                model="unconfigured",
                finish_reason="runtime_not_configured",
            ),
        }

    def describe(self) -> dict[str, object]:
        """Describe the active runtime mode."""
        return {
            "service": "ai-service",
            "owner": "application.llm.runtime_service",
            "status": "langchain-runtime-shell",
            "provider_chain": [provider.name for provider in self.providers],
            "available_providers": [
                provider.name for provider in self.providers if provider.is_available()
            ],
            "native_streaming_providers": [
                provider.name
                for provider in self.providers
                if provider.is_available() and provider.supports_stream()
            ],
            "message": "Runtime pronto para LangChain com providers locais do backend unificado.",
        }
