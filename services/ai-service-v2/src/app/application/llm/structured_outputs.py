"""Structured output contracts for the unified orchestration flow."""

from pydantic import BaseModel, Field


class SessionContextOutput(BaseModel):
    """Structured session context used by context and persistence nodes."""

    summary: str = ""
    main_themes: list[str] = Field(default_factory=list)


class RetrievedDocument(BaseModel):
    """Structured representation of one retrieved document or chunk."""

    source_id: str
    title: str | None = None
    snippet: str
    score: float | None = None


class GenerationOutput(BaseModel):
    """Structured generation result produced by the runtime node."""

    text: str
    provider: str = "unconfigured"
    model: str = "unconfigured"
    finish_reason: str = "scaffold"


class SafetyOutput(BaseModel):
    """Structured safety decision for the response."""

    severity: str = "unknown"
    allow_response: bool = True
    actions: list[str] = Field(default_factory=list)


class OrchestrationOutput(BaseModel):
    """Structured final output returned by AgentService."""

    trace_id: str
    response: str
    provider: str
    model: str
    execution_mode: str
    session_id: str | None = None
    username: str | None = None
    chat_id: str | None = None
    user_message_id: str | None = None
    ai_message_id: str | None = None
    audio_url: str | None = None
    conversation_ended: bool = False
    node_trace: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
