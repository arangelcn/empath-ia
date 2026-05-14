"""Session context assembly node."""

from __future__ import annotations


class ContextNode:
    """Gather and attach session context to the graph state."""

    def __init__(self, conversation_repository, user_profile_service, session_context_service) -> None:
        self.conversation_repository = conversation_repository
        self.user_profile_service = user_profile_service
        self.session_context_service = session_context_service

    async def __call__(self, state):
        state.node_trace.append("session_context")
        identity = await self.conversation_repository.resolve_conversation_ref(
            state.session_id,
            username=state.username,
            create=True,
        )
        state.chat_id = identity.get("chat_id")
        state.session_id = identity.get("legacy_session_id") or state.session_id
        state.username = identity.get("username") or state.username

        if not state.user_profile:
            state.user_profile = await self.user_profile_service.get_user_profile(state.username)
        if not state.conversation_history:
            state.conversation_history = await self.conversation_repository.get_context(state.session_id)
        if state.previous_session_context is None:
            state.previous_session_context = await self.session_context_service.get_previous_context(
                state.session_id
            )
        if state.initial_prompt is None and not state.session_objective:
            state.initial_prompt = await self.conversation_repository.get_initial_prompt(state.session_id)
        state.selected_voice, state.voice_enabled = await self.conversation_repository.get_voice_preferences(
            state.username
        )
        if state.is_voice_mode:
            state.voice_enabled = True

        if state.previous_session_context is None:
            state.warnings.append("previous_session_context_missing")
        return state
