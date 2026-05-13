"""Graph state scaffold for the unified chat pipeline."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class GraphState:
    """Canonical state shape for future orchestration."""

    trace_id: str
    session_id: str
    username: str
    chat_id: str | None = None
    user_message: str = ""
    prompt_key: str | None = None
    rag_policy: dict[str, Any] = field(default_factory=dict)
    is_voice_mode: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize graph state for introspection endpoints."""
        return asdict(self)
