"""Persistence execution node."""

from __future__ import annotations


class PersistenceNode:
    """Execute persistence side effects for the orchestration flow."""

    def __init__(self, conversation_repository, voice_synthesis_service, session_context_service) -> None:
        self.conversation_repository = conversation_repository
        self.voice_synthesis_service = voice_synthesis_service
        self.session_context_service = session_context_service

    async def __call__(self, state):
        state.node_trace.append("persistence")
        generation = state.generation_result or {}
        response_text = (generation.get("text") or "").strip()

        state.user_message_id = await self.conversation_repository.save_message(
            state.session_id,
            "user",
            state.user_message,
        )

        if state.voice_enabled and state.is_voice_mode and response_text:
            state.audio_url = await self.voice_synthesis_service.generate_audio(
                response_text,
                state.selected_voice,
                is_voice_mode=True,
            )

        state.ai_message_id = await self.conversation_repository.save_message(
            state.session_id,
            "ai",
            response_text,
            state.audio_url,
        )
        await self.conversation_repository.update_message_count(state.session_id)
        state.conversation_ended = self.session_context_service.detect_conversation_end(state.user_message)
        state.persistence_plan = {
            "save_user_message": {"done": True, "message_id": state.user_message_id},
            "save_ai_message": {"done": True, "message_id": state.ai_message_id},
            "update_message_count": {"done": True},
            "audio_generation": {
                "done": bool(state.audio_url),
                "voice_enabled": state.voice_enabled,
                "is_voice_mode": state.is_voice_mode,
            },
            "conversation_ended": state.conversation_ended,
        }
        return state
