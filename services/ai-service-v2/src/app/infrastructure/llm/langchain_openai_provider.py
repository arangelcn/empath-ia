"""LangChain-backed OpenAI-compatible provider."""

from __future__ import annotations

from typing import Any

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - optional dependency during scaffold phase
    HumanMessage = None
    SystemMessage = None
    ChatOpenAI = None

from ...application.llm.structured_outputs import GenerationOutput


class LangChainOpenAIProvider:
    """Primary runtime provider using LangChain's ChatOpenAI wrapper."""

    name = "langchain_openai"

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def is_available(self) -> bool:
        """Return whether LangChain/OpenAI runtime is configured."""
        return ChatOpenAI is not None and bool(self.api_key)

    async def generate(self, state: Any, prompt_payload: Any) -> GenerationOutput:
        """Generate the assistant response through ChatOpenAI."""
        if not self.is_available():
            return GenerationOutput(
                text="",
                provider=self.name,
                model=self.model,
                finish_reason="provider_unavailable",
            )

        llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        messages = self._build_messages(prompt_payload, state)
        result = await llm.ainvoke(messages)
        return GenerationOutput(
            text=getattr(result, "content", "") or "",
            provider=self.name,
            model=self.model,
            finish_reason="langchain_openai",
        )

    def _build_messages(self, prompt_payload: Any, state: Any) -> list[Any]:
        """Normalize prompt payloads into LangChain messages."""
        if hasattr(prompt_payload, "invoke"):
            prompt_value = prompt_payload.invoke(
                {
                    "conversation_history": state.conversation_history,
                    "user_message": state.user_message,
                    "previous_session_context": state.previous_session_context or {},
                    "user_profile": state.user_profile or {},
                    "retrieval_context": self._extract_retrieval_context(prompt_payload, state),
                    "citations_summary": self._extract_citations_summary(prompt_payload, state),
                }
            )
            if hasattr(prompt_value, "to_messages"):
                return prompt_value.to_messages()

        system_content = ""
        if isinstance(prompt_payload, dict):
            system_content = str(prompt_payload.get("system", ""))
            retrieval_context = str(prompt_payload.get("retrieval_context", ""))
            citations_summary = str(prompt_payload.get("citations_summary", ""))
            human_content = (
                f"Mensagem do usuário:\n{state.user_message}\n\n"
                f"Contexto anterior: {state.previous_session_context or {}}\n"
                f"Perfil do usuário: {state.user_profile or {}}\n\n"
                f"Contexto recuperado:\n{retrieval_context}\n\n"
                f"Orientação de citação: {citations_summary}"
            )
            return [
                SystemMessage(content=system_content or "Você é um assistente terapêutico seguro."),
                HumanMessage(content=human_content),
            ]
        return [
            SystemMessage(content=system_content or "Você é um assistente terapêutico seguro."),
            HumanMessage(content=state.user_message),
        ]

    def _extract_retrieval_context(self, prompt_payload: Any, state: Any) -> str:
        if isinstance(prompt_payload, dict):
            return str(prompt_payload.get("retrieval_context", ""))
        retrieval_result = getattr(state, "retrieval_result", None) or {}
        results = retrieval_result.get("results") or []
        if not results:
            return "Nenhum contexto recuperado confiável."
        lines = []
        for index, item in enumerate(results, start=1):
            citation = item.get("citation") or {}
            title = citation.get("title") or "Documento sem titulo"
            section = citation.get("section") or "secao nao informada"
            snippet = " ".join(str(item.get("content") or "").split())
            lines.append(f"[{index}] {title} | {section}\n{snippet}")
        return "\n".join(lines)

    def _extract_citations_summary(self, prompt_payload: Any, state: Any) -> str:
        if isinstance(prompt_payload, dict):
            return str(prompt_payload.get("citations_summary", ""))
        citations = getattr(state, "citations", None) or []
        if not citations:
            return "Sem citacoes disponiveis."
        indexes = ", ".join(f"[{citation['index']}]" for citation in citations)
        return f"Se usar o contexto recuperado, cite explicitamente {indexes}."
