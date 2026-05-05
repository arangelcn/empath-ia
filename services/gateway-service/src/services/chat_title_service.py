"""
Chat title generation and persistence.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List

logger = logging.getLogger(__name__)

ConversationContextLoader = Callable[[str], Awaitable[List[Dict[str, Any]]]]


class ChatTitleService:
    """Generate and persist contextual titles for chat sessions."""

    def __init__(self, ai_service_url: str, collection_getter: Callable[[str], Any], async_client_factory: Any):
        self.ai_service_url = ai_service_url
        self.get_collection = collection_getter
        self.async_client_factory = async_client_factory

    async def generate_chat_title(
        self,
        chat_id: str,
        mode: str,
        load_conversation_context: ConversationContextLoader,
    ) -> Dict[str, Any]:
        """Generate a contextual title and subtitle for a chat session using AI."""
        try:
            conversations = self.get_collection("conversations")
            conv_doc = await conversations.find_one({"chat_id": chat_id})
            username = (conv_doc or {}).get("username", "_title_bot")
            therapeutic_session_id = (conv_doc or {}).get("therapeutic_session_id")

            messages = await load_conversation_context(chat_id)
            if not messages:
                return {"success": False, "title": None, "subtitle": None}

            context_messages = messages[:4] if mode == "initial" else messages[-12:]
            conversation_text = self._format_context_for_prompt(context_messages)
            if not conversation_text.strip():
                return {"success": False, "title": None, "subtitle": None}

            response = await self._request_title_completion(conversation_text)
            if response.status_code != 200:
                logger.warning("⚠️ AI service retornou %s ao gerar título para %s", response.status_code, chat_id)
                return {"success": False, "title": None, "subtitle": None}

            completion_data = response.json()
            if completion_data.get("success") is False:
                logger.warning("⚠️ AI service não gerou texto para título de %s", chat_id)
                return {"success": False, "title": None, "subtitle": None}

            parsed = self._parse_title_payload(completion_data)
            if not parsed:
                logger.warning("⚠️ Não foi possível extrair JSON do título gerado para %s: %s", chat_id, completion_data)
                return {"success": False, "title": None, "subtitle": None}

            title = self._coerce_text(parsed.get("title"))[:60]
            subtitle = self._coerce_text(parsed.get("subtitle"))[:100]
            if not title:
                return {"success": False, "title": None, "subtitle": None}

            logger.info("🏷️ Título gerado para %s (%s): %r", chat_id, mode, title)
            await self._persist_title(chat_id, title, subtitle, conv_doc, username, therapeutic_session_id)
            return {"success": True, "title": title, "subtitle": subtitle}

        except Exception as exc:
            logger.warning("⚠️ Erro ao gerar título para %s: %s", chat_id, exc)
            return {"success": False, "title": None, "subtitle": None}

    def _format_context_for_prompt(self, context_messages: List[Dict[str, Any]]) -> str:
        conversation_text = ""
        for msg in context_messages:
            role = "Usuário" if msg.get("type") == "user" else "Terapeuta"
            snippet = self._coerce_text(msg.get("content"))[:300]
            conversation_text += f"{role}: {snippet}\n"
        return conversation_text

    def _parse_title_payload(self, completion_data: Dict[str, Any]) -> Dict[str, Any] | None:
        candidates = [
            completion_data.get("text"),
            completion_data.get("data"),
            completion_data.get("result"),
            completion_data,
        ]

        for candidate in candidates:
            parsed = self._parse_title_candidate(candidate)
            if parsed:
                return parsed
        return None

    def _parse_title_candidate(self, candidate: Any) -> Dict[str, Any] | None:
        if isinstance(candidate, dict):
            if candidate.get("title") or candidate.get("subtitle"):
                return candidate
            for nested_key in ("text", "data", "result", "response"):
                nested = self._parse_title_candidate(candidate.get(nested_key))
                if nested:
                    return nested
            return None

        if not isinstance(candidate, str):
            return None

        text = candidate.strip()
        if not text:
            return None

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                nested = self._parse_title_candidate(parsed)
                if nested:
                    return nested
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            return None

        try:
            parsed = json.loads(json_match.group())
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _coerce_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (int, float, bool)):
            return str(value).strip()
        if isinstance(value, dict):
            for key in ("text", "content", "value", "title", "subtitle"):
                if key in value:
                    text = self._coerce_text(value.get(key))
                    if text:
                        return text
            return json.dumps(value, ensure_ascii=False).strip()
        if isinstance(value, list):
            return " ".join(self._coerce_text(item) for item in value).strip()
        return str(value).strip()

    async def _request_title_completion(self, conversation_text: str):
        prompt = (
            "Você é um assistente especializado em sessões terapêuticas. "
            "Com base no trecho abaixo, crie um título e um subtítulo que ajudem o usuário a lembrar desta conversa.\n\n"
            "Regras obrigatórias:\n"
            "- Título: máximo 60 caracteres, específico, empático e evocativo do tema ou emoção central. "
            "Não use frases genéricas como 'Sessão terapêutica'.\n"
            "- Subtítulo: máximo 100 caracteres, complementa o título com contexto emocional ou temático.\n"
            "- Responda SOMENTE com JSON válido no formato: {\"title\": \"...\", \"subtitle\": \"...\"}\n\n"
            f"Trecho da sessão:\n{conversation_text}"
        )

        async with self.async_client_factory(timeout=20.0) as client:
            return await client.post(
                f"{self.ai_service_url}/util/complete",
                json={
                    "prompt": prompt,
                    "system": (
                        "Você gera títulos curtos para sessões terapêuticas. "
                        "Responda somente com JSON válido."
                    ),
                    "max_tokens": 180,
                },
                timeout=20.0,
            )

    async def _persist_title(
        self,
        chat_id: str,
        title: str,
        subtitle: str,
        conv_doc: Dict[str, Any] | None,
        username: str,
        therapeutic_session_id: str | None,
    ) -> None:
        try:
            now = datetime.utcnow()
            conversations = self.get_collection("conversations")
            await conversations.update_one(
                {"chat_id": chat_id},
                {"$set": {"title": title, "subtitle": subtitle, "updated_at": now}},
            )
            if conv_doc and therapeutic_session_id:
                user_sessions = self.get_collection("user_therapeutic_sessions")
                title_payload = {"title": title, "subtitle": subtitle, "updated_at": now}
                uts_result = await user_sessions.update_one(
                    {"username": username, "session_id": therapeutic_session_id},
                    {"$set": title_payload},
                )
                if uts_result.matched_count == 0:
                    uts_doc = await user_sessions.find_one({"session_id": therapeutic_session_id})
                    if uts_doc:
                        await user_sessions.update_one(
                            {"_id": uts_doc["_id"]},
                            {"$set": title_payload},
                        )
                        logger.info(
                            "🏷️ Título persistido via fallback (conv.username=%r → uts.username=%r)",
                            username,
                            uts_doc.get("username"),
                        )
                    else:
                        logger.warning(
                            "⚠️ user_therapeutic_sessions: nenhum doc para session_id=%r",
                            therapeutic_session_id,
                        )
        except Exception as persist_exc:
            logger.warning("⚠️ Título gerado mas não persistido para %s: %s", chat_id, persist_exc)
