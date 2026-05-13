"""Runtime abstraction scaffold."""


class RuntimeService:
    """Future owner for provider orchestration and execution."""

    def describe(self) -> dict[str, object]:
        """Describe the scaffold runtime mode."""
        return {
            "service": "ai-service-v2",
            "owner": "application.llm.runtime_service",
            "status": "scaffold",
            "provider_chain": [],
            "message": "Nenhum runtime LLM foi migrado para este boundary ainda.",
        }
