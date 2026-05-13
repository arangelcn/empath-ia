"""Structured output contracts scaffold."""

from pydantic import BaseModel, Field


class SessionContextOutput(BaseModel):
    """Example structured output schema for future session context generation."""

    summary: str = ""
    main_themes: list[str] = Field(default_factory=list)
