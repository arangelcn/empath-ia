"""Response assembly node."""

from __future__ import annotations

from ...llm.structured_outputs import OrchestrationOutput


SAFE_BLOCKED_RESPONSE = (
    "Nao posso seguir com essa resposta do jeito que ela foi gerada. "
    "Vou priorizar seguranca: se houver risco imediato para voce ou outra pessoa, "
    "procure ajuda emergencial local agora e tente acionar alguem de confianca "
    "perto de voce."
)


def resolve_response_text(state) -> str:
    """Resolve the final response text after safety policies."""
    generation = state.generation_result or {}
    safety = state.safety_result or {}
    response_text = generation.get("text") or ""
    if not safety.get("allow_response", True):
        response_text = SAFE_BLOCKED_RESPONSE
        if "safety_blocked_generated_response" not in state.warnings:
            state.warnings.append("safety_blocked_generated_response")
    return response_text


class ResponseNode:
    """Assemble the final graph output shape."""

    def __call__(self, state):
        state.node_trace.append("response")
        generation = state.generation_result or {}
        response_text = resolve_response_text(state)

        final_output = OrchestrationOutput(
            trace_id=state.trace_id,
            response=response_text,
            provider=generation.get("provider", "unconfigured"),
            model=generation.get("model", "unconfigured"),
            execution_mode=state.execution_mode,
            session_id=state.session_id,
            username=state.username,
            chat_id=state.chat_id,
            user_message_id=state.user_message_id,
            ai_message_id=state.ai_message_id,
            audio_url=state.audio_url,
            conversation_ended=state.conversation_ended,
            citations=state.citations,
            node_trace=state.node_trace,
            warnings=state.warnings,
        )
        state.final_response = final_output.model_dump()
        return state
