"""Prompt domain models."""

from dataclasses import dataclass


@dataclass(slots=True)
class PromptDescriptor:
    """Prompt identifier that survives transport changes."""

    prompt_key: str
    version: int | None = None
