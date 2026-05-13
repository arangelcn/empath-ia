"""Canonical graph state for the unified chat pipeline."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class GraphState:
    """Canonical state shape for LangGraph orchestration."""

    trace_id: str
    session_id: str
    username: str
    chat_id: str | None = None
    user_message: str = ""
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    user_profile: dict[str, Any] = field(default_factory=dict)
    previous_session_context: dict[str, Any] | None = None
    session_objective: dict[str, Any] | None = None
    prompt_key: str | None = None
    compiled_prompt: Any = None
    rag_policy: dict[str, Any] = field(default_factory=dict)
    retrieval_result: dict[str, Any] | None = None
    citations: list[dict[str, Any]] = field(default_factory=list)
    generation_result: dict[str, Any] | None = None
    safety_result: dict[str, Any] | None = None
    persistence_plan: dict[str, Any] | None = None
    final_response: dict[str, Any] | None = None
    node_trace: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    is_voice_mode: bool = False
    execution_mode: str = "langgraph"

    def to_dict(self) -> dict[str, Any]:
        """Serialize graph state for introspection endpoints."""
        return asdict(self)
