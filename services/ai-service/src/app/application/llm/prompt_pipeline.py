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
        retrieval_context = self._build_retrieval_context(state)
        citations_summary = self._build_citations_summary(state)
        if ChatPromptTemplate is None or MessagesPlaceholder is None:
            return {
                "system": system_prompt,
                "history": state.conversation_history,
                "user_message": state.user_message,
                "previous_session_context": state.previous_session_context or {},
                "user_profile": state.user_profile or {},
                "retrieval_context": retrieval_context,
                "citations_summary": citations_summary,
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
                    "Perfil do usuário: {user_profile}\n\n"
                    "Contexto recuperado:\n{retrieval_context}\n\n"
                    "Orientação de citação: {citations_summary}",
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

        grounding_instruction = self._build_grounding_instruction(state)
        if grounding_instruction:
            system_prompt = f"{system_prompt}\n\n{grounding_instruction}"

        return system_prompt

    def _fallback_system_prompt(self) -> str:
        return (
            "Você é o orquestrador clínico do Empat.IA. "
            "Responda em português brasileiro, preserve segurança, grounding e rastreabilidade. "
            "Use histórico, contexto de sessão e retrieval apenas quando existirem de forma confiável. "
            "Não invente contexto. Priorize acolhimento, concisão e segurança."
        )

    def _build_retrieval_context(self, state) -> str:
        retrieval_result = state.retrieval_result or {}
        results = retrieval_result.get("results") or []
        if not results:
            return "Nenhum contexto recuperado confiável."

        lines = []
        for index, item in enumerate(results, start=1):
            citation = item.get("citation") or {}
            title = citation.get("title") or "Documento sem titulo"
            section = citation.get("section") or "secao nao informada"
            snippet = " ".join(str(item.get("content") or "").split())
            if len(snippet) > 500:
                snippet = f"{snippet[:497].rstrip()}..."
            lines.append(f"[{index}] {title} | {section}")
            lines.append(snippet)
        return "\n".join(lines)

    def _build_citations_summary(self, state) -> str:
        citations = state.citations or []
        if not citations:
            return "Sem citacoes disponiveis."

        require_citations = bool(
            (state.retrieval_result or {}).get("policy", {}).get("require_citations", True)
        )
        indexes = ", ".join(f"[{citation['index']}]" for citation in citations)
        if require_citations:
            return f"Se usar o contexto recuperado, cite explicitamente {indexes}."
        return f"Contexto disponivel em {indexes}; cite apenas se isso ajudar a resposta."

    def _build_grounding_instruction(self, state) -> str:
        retrieval_result = state.retrieval_result or {}
        results = retrieval_result.get("results") or []
        if not results:
            fallback_behavior = retrieval_result.get("policy", {}).get(
                "fallback_behavior",
                "answer_without_sources",
            )
            if fallback_behavior == "warn_if_unavailable":
                return (
                    "Se nao houver contexto recuperado confiavel, avise brevemente que a resposta "
                    "esta sendo dada sem base documental especifica."
                )
            if fallback_behavior == "refuse_if_unavailable":
                return (
                    "Se a pergunta depender de base documental e nao houver contexto recuperado "
                    "confiavel, diga claramente que nao ha evidencias suficientes para responder "
                    "com seguranca."
                )
            return ""

        citation_summary = self._build_citations_summary(state)
        return (
            "Use o contexto recuperado apenas quando ele realmente melhorar a precisao da resposta. "
            "Se houver conflito entre historico clinico e documentos recuperados, priorize seguranca "
            "e deixe a incerteza explicita. "
            f"{citation_summary}"
        )
