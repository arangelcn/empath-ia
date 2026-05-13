"""Unified chat façade scaffold."""

from datetime import UTC, datetime
import uuid
from typing import Any

from ..orchestration.agent_service import AgentService
from .next_session_service import NextSessionService
from .registration_service import RegistrationService
from .session_context_service import SessionContextService


class ChatFacade:
    """Facade that will become the single chat entrypoint in the unified boundary."""

    def __init__(
        self,
        agent_service: AgentService,
        session_context_service: SessionContextService,
        next_session_service: NextSessionService,
        registration_service: RegistrationService,
    ) -> None:
        self.agent_service = agent_service
        self.session_context_service = session_context_service
        self.next_session_service = next_session_service
        self.registration_service = registration_service

    async def generate_reply(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return a contract-compatible scaffold response."""
        trace_id = payload.get("trace_id") or f"trace_{uuid.uuid4().hex}"
        state = self.agent_service.build_graph_state(payload, trace_id=trace_id)
        execution_plan = self.agent_service.plan(state)

        return {
            "response": (
                "ai-service-v2 scaffold ativo. O fluxo terapeutico unificado "
                "ainda nao foi migrado para producao."
            ),
            "model": "scaffold",
            "session_id": payload.get("session_id", "default"),
            "username": payload.get("username", "anonymous"),
            "timestamp": datetime.now(UTC).isoformat(),
            "provider": "ai-service-v2",
            "success": False,
            "trace_id": trace_id,
            "chat_id": payload.get("chat_id"),
            "migration": {
                "phase": "scaffold",
                "graph_state": state.to_dict(),
                "execution_plan": execution_plan,
                "session_context": self.session_context_service.preview(payload),
                "next_session": self.next_session_service.preview(payload),
                "registration": self.registration_service.preview(payload),
            },
        }
