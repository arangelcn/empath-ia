"""Fallback service scaffold."""


class FallbackService:
    """Future owner for deterministic fallback responses."""

    def describe(self) -> dict[str, object]:
        """Describe the scaffold fallback path."""
        return {
            "owner": "application.llm.fallback_service",
            "status": "scaffold",
            "patterns": ["greeting", "sadness", "anxiety", "default"],
        }
