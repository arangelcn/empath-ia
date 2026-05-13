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

    def __init__(self, default_language: str) -> None:
        self.default_language = default_language

    def build_chat_prompt(self, state) -> Any:
        """Create the canonical chat prompt using LangChain when available."""
        system_prompt = self._system_prompt()
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

    def _system_prompt(self) -> str:
        return (
            "Você é o orquestrador clínico do Empat.IA. "
            "Responda em português brasileiro, preserve segurança, grounding e rastreabilidade. "
            "Use histórico, contexto de sessão e retrieval apenas quando existirem de forma confiável. "
            "Não invente contexto. Priorize acolhimento, concisão e segurança."
        )
