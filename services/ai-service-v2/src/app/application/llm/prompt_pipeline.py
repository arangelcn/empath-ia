"""Prompt pipeline scaffold."""


class PromptPipeline:
    """Future owner for prompt assembly and structured prompt policies."""

    def __init__(self, default_language: str) -> None:
        self.default_language = default_language

    def describe(self, prompt_key: str | None) -> dict[str, object]:
        """Summarize the prompt pipeline choice for scaffold responses."""
        return {
            "owner": "application.llm.prompt_pipeline",
            "prompt_key": prompt_key or "system_rogers",
            "default_language": self.default_language,
            "status": "scaffold",
        }
