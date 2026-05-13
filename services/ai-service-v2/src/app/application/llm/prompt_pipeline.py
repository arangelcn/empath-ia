"""Prompt assembly pipeline oriented to LangChain abstractions."""

from __future__ import annotations

from typing import Any

try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
except ImportError:  # pragma: no cover - optional dependency in scaffold phase
    ChatPromptTemplate = None
    MessagesPlaceholder = None


class PromptPipeline:
    """Owner for prompt assembly and structured prompt policies."""

    def __init__(self, default_language: str, prompt_repository) -> None:
        self.default_language = default_language
        self.prompt_repository = prompt_repository

    async def build_chat_prompt(self, state) -> Any:
        """Create the canonical chat prompt using LangChain when available."""
        system_prompt = await self._resolve_system_prompt(state)
        if ChatPromptTemplate is None or MessagesPlaceholder is None:
            return {
                "system": system_prompt,
                "history": state.conversation_history,
                "user_message": state.user_message,
                "language": self.default_language,
                "mode": "prompt-blueprint",
            }

        return ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="conversation_history", optional=True),
                (
                    "human",
                    "Mensagem do usuário:\n{user_message}\n\n"
                    "Contexto anterior: {previous_session_context}\n"
                    "Perfil do usuário: {user_profile}",
                ),
            ]
        )

    def describe(self, prompt_key: str | None) -> dict[str, object]:
        """Summarize the prompt pipeline choice."""
        return {
            "owner": "application.llm.prompt_pipeline",
            "prompt_key": prompt_key or "system_rogers",
            "default_language": self.default_language,
            "status": "langchain-ready",
            "uses_langchain": ChatPromptTemplate is not None,
        }

    async def _resolve_system_prompt(self, state) -> str:
        prompt_key = state.prompt_key or "system_rogers"
        prompt = await self.prompt_repository.get_active(prompt_key)
        system_prompt = prompt.content if prompt else self._fallback_system_prompt()

        if state.initial_prompt:
            system_prompt = (
                f"{system_prompt}\n\n"
                f"OBJETIVO INICIAL DA SESSAO:\n{state.initial_prompt.strip()}"
            )

        if state.is_voice_mode:
            voice_prompt = await self.prompt_repository.get_active("voice_short_response")
            if voice_prompt and voice_prompt.content:
                system_prompt = f"{system_prompt}\n\n{voice_prompt.content}"

        return system_prompt

    def _fallback_system_prompt(self) -> str:
        return (
            "Você é o orquestrador clínico do Empat.IA. "
            "Responda em português brasileiro, preserve segurança, grounding e rastreabilidade. "
            "Use histórico, contexto de sessão e retrieval apenas quando existirem de forma confiável. "
            "Não invente contexto. Priorize acolhimento, concisão e segurança."
        )
