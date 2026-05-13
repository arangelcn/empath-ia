"""Unified chat façade with migrated synchronous chat ownership."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from ...repositories.conversations import MongoConversationRepository
from ..orchestration.agent_service import AgentService
from .registration_service import RegistrationService


class ChatFacade:
    """Single chat application façade for the new unified boundary."""

    def __init__(
        self,
        conversation_repository: MongoConversationRepository,
        agent_service: AgentService,
        registration_service: RegistrationService,
    ) -> None:
        self.conversation_repository = conversation_repository
        self.agent_service = agent_service
        self.registration_service = registration_service

    async def start_conversation(
        self,
        session_id: str,
        username: str | None = None,
        therapeutic_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Create or load a conversation document."""
        return await self.conversation_repository.start_or_get_conversation(
            session_id,
            username=username,
            therapeutic_session_id=therapeutic_session_id,
        )

    async def get_history(self, session_id: str) -> dict[str, Any]:
        """Load conversation history."""
        return await self.conversation_repository.get_history(session_id)

    async def list_recent_conversations(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent conversations."""
        return await self.conversation_repository.list_recent(limit)

    async def process_user_message(
        self,
        session_id: str,
        user_message: str,
        session_objective: dict[str, Any] | None = None,
        is_voice_mode: bool = False,
    ) -> dict[str, Any]:
        """Process a chat message through the unified orchestration flow."""
        if self._is_registration_session(session_id):
            return await self.registration_service.handle_message(
                session_id,
                user_message,
                is_voice_mode=is_voice_mode,
            )

        identity = await self.conversation_repository.resolve_conversation_ref(session_id, create=True)
        chat_id = identity.get("chat_id")
        legacy_session_id = identity.get("legacy_session_id") or session_id
        username = identity.get("username") or self.conversation_repository.extract_username(legacy_session_id)
        if not username:
            raise ValueError(f"Session ID invalido: {legacy_session_id}")

        await self.start_conversation(legacy_session_id)

        initial_prompt = None
        if not session_objective:
            initial_prompt = await self.conversation_repository.get_initial_prompt(legacy_session_id)

        orchestration_result = await self.agent_service.chat(
            {
                "message": user_message,
                "session_id": legacy_session_id,
                "chat_id": chat_id,
                "username": username,
                "session_objective": session_objective,
                "initial_prompt": initial_prompt,
                "is_voice_mode": is_voice_mode,
            }
        )

        return {
            "success": True,
            "data": {
                "chat_id": orchestration_result.get("chat_id") or chat_id,
                "session_id": orchestration_result.get("session_id") or legacy_session_id,
                "therapeutic_session_id": identity.get("therapeutic_session_id"),
                "user_message": {
                    "id": orchestration_result.get("user_message_id"),
                    "content": user_message,
                },
                "ai_response": {
                    "id": orchestration_result.get("ai_message_id"),
                    "content": orchestration_result.get("response", ""),
                    "audioUrl": orchestration_result.get("audio_url"),
                    "provider": orchestration_result.get("provider", "unknown"),
                    "model": orchestration_result.get("model", "unknown"),
                },
                "conversation_ended": orchestration_result.get("conversation_ended", False),
            },
        }

    async def generate_reply(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Use the architecture-first orchestration path for the unified endpoint."""
        result = await self.agent_service.chat(payload)
        return {
            "response": result["response"],
            "model": result["model"],
            "session_id": result.get("session_id") or payload.get("session_id", "default"),
            "username": result.get("username") or payload.get("username", "anonymous"),
            "timestamp": datetime.now(UTC).isoformat(),
            "provider": result["provider"],
            "success": True,
            "trace_id": result.get("trace_id") or payload.get("trace_id") or f"trace_{uuid.uuid4().hex}",
            "chat_id": result.get("chat_id") or payload.get("chat_id"),
            "migration": {
                "phase": "langgraph-orchestration",
                "node_trace": result.get("node_trace", []),
                "warnings": result.get("warnings", []),
                "user_message_id": result.get("user_message_id"),
                "ai_message_id": result.get("ai_message_id"),
                "audio_url": result.get("audio_url"),
                "conversation_ended": result.get("conversation_ended", False),
            },
        }

    async def generate_legacy_compat_reply(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Expose the old ai-service sync contract using the new orchestration path."""
        result = await self.agent_service.chat(payload)
        return {
            "response": result.get("response", ""),
            "model": result.get("model", "unconfigured"),
            "session_id": result.get("session_id") or payload.get("session_id", "default"),
            "username": result.get("username") or payload.get("username", "anonymous"),
            "timestamp": datetime.now(UTC).isoformat(),
            "provider": result.get("provider", "unconfigured"),
            "success": True,
        }

    @staticmethod
    def _is_registration_session(session_id: str) -> bool:
        return session_id.endswith("_session-1") or session_id == "session-1"
