"""Unified chat façade with migrated public chat ownership."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any, AsyncGenerator

from ...bootstrap.settings import Settings
from ...repositories.conversations import MongoConversationRepository
from ...services.streaming_utils import SentenceChunker, now_ms
from ..orchestration.agent_service import AgentService
from .next_session_service import NextSessionService
from .registration_service import RegistrationService
from .session_context_service import SessionContextService
from .user_profile_service import UserProfileService


logger = logging.getLogger(__name__)


class ChatFacade:
    """Single chat application façade for the new unified boundary."""

    def __init__(
        self,
        settings: Settings,
        conversation_repository: MongoConversationRepository,
        user_profile_service: UserProfileService,
        legacy_gateway_client,
        voice_synthesis_service,
        agent_service: AgentService,
        session_context_service: SessionContextService,
        next_session_service: NextSessionService,
        registration_service: RegistrationService,
    ) -> None:
        self.settings = settings
        self.conversation_repository = conversation_repository
        self.user_profile_service = user_profile_service
        self.legacy_gateway_client = legacy_gateway_client
        self.voice_synthesis_service = voice_synthesis_service
        self.agent_service = agent_service
        self.session_context_service = session_context_service
        self.next_session_service = next_session_service
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
        """Process a chat message using Mongo ownership plus legacy AI runtime."""
        if self._is_registration_session(session_id):
            return await self.legacy_gateway_client.send_message(
                {
                    "message": user_message,
                    "session_id": session_id,
                    "session_objective": session_objective,
                    "is_voice_mode": is_voice_mode,
                }
            )

        identity = await self.conversation_repository.resolve_conversation_ref(session_id, create=True)
        chat_id = identity.get("chat_id")
        legacy_session_id = identity.get("legacy_session_id") or session_id
        username = identity.get("username") or self.conversation_repository.extract_username(legacy_session_id)
        if not username:
            raise ValueError(f"Session ID invalido: {legacy_session_id}")

        await self.start_conversation(legacy_session_id)
        selected_voice, voice_enabled = await self.conversation_repository.get_voice_preferences(username)
        if is_voice_mode:
            voice_enabled = True

        initial_prompt = None
        if not session_objective:
            initial_prompt = await self.conversation_repository.get_initial_prompt(legacy_session_id)

        ai_response_data = await self._get_ai_response(
            user_message=user_message,
            session_id=legacy_session_id,
            username=username,
            selected_voice=selected_voice,
            voice_enabled=voice_enabled,
            session_objective=session_objective,
            initial_prompt=initial_prompt,
            is_voice_mode=is_voice_mode,
            chat_id=chat_id,
        )

        user_message_id = await self.conversation_repository.save_message(legacy_session_id, "user", user_message)
        ai_message_id = await self.conversation_repository.save_message(
            legacy_session_id,
            "ai",
            ai_response_data["response"],
            ai_response_data.get("audio_url"),
        )
        await self.conversation_repository.update_message_count(legacy_session_id)

        conversation_ended = self.session_context_service.detect_conversation_end(user_message)
        return {
            "success": True,
            "data": {
                "chat_id": chat_id,
                "session_id": legacy_session_id,
                "therapeutic_session_id": identity.get("therapeutic_session_id"),
                "user_message": {"id": user_message_id, "content": user_message},
                "ai_response": {
                    "id": ai_message_id,
                    "content": ai_response_data["response"],
                    "audioUrl": ai_response_data.get("audio_url"),
                    "provider": ai_response_data.get("provider", "unknown"),
                    "model": ai_response_data.get("model", "unknown"),
                },
                "conversation_ended": conversation_ended,
            },
        }

    async def process_user_message_stream(
        self,
        session_id: str,
        user_message: str,
        session_objective: dict[str, Any] | None = None,
        is_voice_mode: bool = True,
        trace_id: str | None = None,
        client_metrics: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process a voice message and emit SSE-ready events."""
        if self._is_registration_session(session_id):
            async for event in self.legacy_gateway_client.stream_message(
                {
                    "message": user_message,
                    "session_id": session_id,
                    "session_objective": session_objective,
                    "is_voice_mode": is_voice_mode,
                    "client_metrics": client_metrics,
                }
            ):
                yield event
            return

        trace_id = trace_id or f"trace_{uuid.uuid4().hex}"
        started_at = time.perf_counter()
        ai_done_data: dict[str, Any] = {}
        full_response = ""
        audio_sequence = 0
        audio_url = None
        first_text_ms: int | None = None
        first_audio_ms: int | None = None
        tts_stream_failed = False
        tts_stream_disabled = False
        text_chunker = SentenceChunker(
            max_chars=220,
            max_wait_ms=450,
            min_timed_flush_chars=32,
            min_timed_flush_words=4,
        )
        voice_chunker = SentenceChunker(
            max_chars=self.settings.voice_chunk_max_chars,
            max_wait_ms=self.settings.voice_chunk_max_wait_ms,
            min_timed_flush_chars=self.settings.voice_chunk_min_timed_chars,
            min_timed_flush_words=self.settings.voice_chunk_min_timed_words,
        )

        identity = await self.conversation_repository.resolve_conversation_ref(session_id, create=True)
        chat_id = identity.get("chat_id")
        legacy_session_id = identity.get("legacy_session_id") or session_id
        username = identity.get("username") or self.conversation_repository.extract_username(legacy_session_id)
        if not username:
            raise ValueError(f"Session ID invalido: {legacy_session_id}")

        await self.start_conversation(legacy_session_id)
        selected_voice, voice_enabled = await self.conversation_repository.get_voice_preferences(username)
        voice_enabled = (voice_enabled or is_voice_mode) and is_voice_mode

        initial_prompt = None
        if not session_objective:
            initial_prompt = await self.conversation_repository.get_initial_prompt(legacy_session_id)

        user_profile = await self.user_profile_service.get_user_profile(username)
        conversation_history = await self.conversation_repository.get_context(legacy_session_id)
        previous_session_context = await self.session_context_service.get_previous_context(legacy_session_id)
        user_message_id = await self.conversation_repository.save_message(legacy_session_id, "user", user_message)

        yield {
            "event": "meta",
            "data": {
                "trace_id": trace_id,
                "chat_id": chat_id,
                "session_id": legacy_session_id,
                "therapeutic_session_id": identity.get("therapeutic_session_id"),
                "user_message": {"id": user_message_id, "content": user_message},
                "voice": selected_voice,
                "streaming": True,
                "client_metrics": client_metrics or {},
                "started_at": datetime.now(UTC).isoformat(),
            },
        }

        ai_request = {
            "message": user_message,
            "session_id": legacy_session_id,
            "chat_id": chat_id,
            "username": username,
            "user_profile": user_profile,
            "conversation_history": conversation_history,
            "session_objective": session_objective,
            "initial_prompt": initial_prompt,
            "previous_session_context": previous_session_context,
            "is_voice_mode": is_voice_mode,
            "trace_id": trace_id,
        }

        async for event in self.agent_service.stream(ai_request):
            current_event = event["event"]
            payload = event["data"]

            if current_event == "text_delta":
                delta = payload.get("delta", "")
                if not delta:
                    continue
                if first_text_ms is None:
                    first_text_ms = now_ms(started_at)
                full_response += delta

                if is_voice_mode:
                    yield {
                        "event": "text_delta",
                        "data": {"delta": delta, "trace_id": trace_id, "elapsed_ms": now_ms(started_at)},
                    }
                else:
                    for text_chunk in text_chunker.push(delta):
                        yield {
                            "event": "text_delta",
                            "data": {
                                "delta": text_chunk,
                                "trace_id": trace_id,
                                "elapsed_ms": now_ms(started_at),
                            },
                        }

                if voice_enabled and not tts_stream_disabled:
                    for text_chunk in voice_chunker.push(delta):
                        async for audio_event in self._stream_tts_or_batch_chunk(
                            text_chunk,
                            selected_voice,
                            trace_id,
                            audio_sequence,
                            started_at,
                        ):
                            if audio_event["event"] == "audio_chunk":
                                audio_sequence += 1
                                if first_audio_ms is None:
                                    first_audio_ms = now_ms(started_at)
                            elif audio_event["event"] == "audio_url":
                                audio_sequence += 1
                                audio_url = audio_event["data"].get("audio_url") or audio_url
                                if first_audio_ms is None:
                                    first_audio_ms = now_ms(started_at)
                            elif audio_event["event"] == "error" and audio_event["data"].get("stage") == "tts_stream":
                                tts_stream_failed = True
                                tts_stream_disabled = True
                            yield audio_event
            elif current_event == "done":
                ai_done_data = payload

        remaining = voice_chunker.flush()
        if remaining and voice_enabled and not tts_stream_disabled:
            async for audio_event in self._stream_tts_or_batch_chunk(
                remaining,
                selected_voice,
                trace_id,
                audio_sequence,
                started_at,
            ):
                if audio_event["event"] == "audio_chunk":
                    audio_sequence += 1
                    if first_audio_ms is None:
                        first_audio_ms = now_ms(started_at)
                elif audio_event["event"] == "audio_url":
                    audio_sequence += 1
                    audio_url = audio_event["data"].get("audio_url") or audio_url
                    if first_audio_ms is None:
                        first_audio_ms = now_ms(started_at)
                yield audio_event

        if not is_voice_mode:
            remaining_text = text_chunker.flush()
            if remaining_text:
                yield {
                    "event": "text_delta",
                    "data": {
                        "delta": remaining_text,
                        "trace_id": trace_id,
                        "elapsed_ms": now_ms(started_at),
                    },
                }

        final_text = (ai_done_data.get("response") or full_response).strip()
        if voice_enabled and audio_sequence == 0 and final_text:
            audio_url = await self.voice_synthesis_service.generate_audio(final_text, selected_voice, is_voice_mode=True)
            if audio_url:
                yield {
                    "event": "audio_url",
                    "data": {
                        "audio_url": audio_url,
                        "trace_id": trace_id,
                        "sequence": audio_sequence,
                        "segment": False,
                        "elapsed_ms": now_ms(started_at),
                    },
                }
                audio_sequence += 1
                if first_audio_ms is None:
                    first_audio_ms = now_ms(started_at)

        ai_message_id = await self.conversation_repository.save_message(
            legacy_session_id,
            "ai",
            final_text,
            audio_url,
        )
        await self.conversation_repository.update_message_count(legacy_session_id)

        conversation_ended = self.session_context_service.detect_conversation_end(user_message)
        metrics = {
            "gateway_total_ms": now_ms(started_at),
            "first_text_delta_ms": first_text_ms,
            "first_audio_chunk_ms": first_audio_ms,
            "audio_chunks": audio_sequence,
            "tts_stream_failed": tts_stream_failed,
            "client_metrics": client_metrics or {},
            **(ai_done_data.get("metrics") or {}),
        }
        yield {"event": "metrics", "data": {"trace_id": trace_id, "metrics": metrics}}
        yield {
            "event": "done",
            "data": {
                "trace_id": trace_id,
                "success": True,
                "data": {
                    "chat_id": chat_id,
                    "session_id": legacy_session_id,
                    "therapeutic_session_id": identity.get("therapeutic_session_id"),
                    "user_message": {"id": user_message_id, "content": user_message},
                    "ai_response": {
                        "id": ai_message_id,
                        "content": final_text,
                        "audioUrl": audio_url,
                        "provider": ai_done_data.get("provider", "unknown"),
                        "model": ai_done_data.get("model", "unknown"),
                    },
                    "conversation_ended": conversation_ended,
                },
                "metrics": metrics,
            },
        }

    async def generate_reply(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Use the architecture-first orchestration path for the unified endpoint."""
        result = await self.agent_service.chat(payload)
        return {
            "response": result["response"],
            "model": result["model"],
            "session_id": payload.get("session_id", "default"),
            "username": payload.get("username", "anonymous"),
            "timestamp": datetime.now(UTC).isoformat(),
            "provider": result["provider"],
            "success": True,
            "trace_id": result.get("trace_id") or payload.get("trace_id") or f"trace_{uuid.uuid4().hex}",
            "chat_id": payload.get("chat_id"),
            "migration": {
                "phase": "langgraph-orchestration",
                "node_trace": result.get("node_trace", []),
                "warnings": result.get("warnings", []),
            },
        }

    async def _get_ai_response(
        self,
        *,
        user_message: str,
        session_id: str,
        username: str,
        selected_voice: str,
        voice_enabled: bool,
        session_objective: dict[str, Any] | None,
        initial_prompt: str | None,
        is_voice_mode: bool,
        chat_id: str | None,
    ) -> dict[str, Any]:
        """Build the AI request payload and call the legacy runtime."""
        user_profile = await self.user_profile_service.get_user_profile(username)
        conversation_history = await self.conversation_repository.get_context(session_id)
        previous_session_context = await self.session_context_service.get_previous_context(session_id)

        ai_request = {
            "message": user_message,
            "session_id": session_id,
            "chat_id": chat_id,
            "username": username,
            "preferred_name": (user_profile or {}).get("preferred_name"),
            "user_profile": user_profile,
            "conversation_history": conversation_history,
            "session_objective": session_objective,
            "initial_prompt": initial_prompt,
            "previous_session_context": previous_session_context,
        }
        ai_service_response = await self.agent_service.chat(ai_request)
        ai_response = ai_service_response.get("response", "").strip()
        if not ai_response:
            raise RuntimeError("AI Service retornou resposta vazia")

        provider = ai_service_response.get("provider", "openai")
        model = ai_service_response.get("model", "unknown")
        audio_url = None
        if voice_enabled and is_voice_mode:
            audio_url = await self.voice_synthesis_service.generate_audio(ai_response, selected_voice, is_voice_mode)

        return {
            "response": ai_response,
            "model": model,
            "session_id": session_id,
            "username": username,
            "timestamp": ai_service_response.get("timestamp", datetime.now(UTC).isoformat()),
            "provider": provider,
            "audio_url": audio_url,
            "voice_enabled": voice_enabled,
            "selected_voice": selected_voice,
        }

    async def _stream_tts_or_batch_chunk(
        self,
        text: str,
        voice: str,
        trace_id: str,
        sequence: int,
        started_at: float,
    ) -> AsyncGenerator[dict[str, Any], None]:
        emitted_audio = False
        stream_failed = False

        async for audio_event in self.voice_synthesis_service.stream_tts_chunk(
            text,
            voice,
            trace_id,
            sequence,
            started_at,
        ):
            if audio_event["event"] == "audio_chunk":
                emitted_audio = True
            elif audio_event["event"] == "error":
                stream_failed = True
            yield audio_event

        if emitted_audio:
            return

        audio_url = await self.voice_synthesis_service.generate_audio(text, voice, is_voice_mode=True)
        if audio_url:
            yield {
                "event": "audio_url",
                "data": {
                    "audio_url": audio_url,
                    "trace_id": trace_id,
                    "sequence": sequence,
                    "segment": True,
                    "text_length": len(text),
                    "elapsed_ms": now_ms(started_at),
                },
            }
        elif stream_failed:
            logger.warning("Streaming TTS falhou e fallback batch por trecho nao gerou audio")

    @staticmethod
    def _is_registration_session(session_id: str) -> bool:
        return session_id.endswith("_session-1") or session_id == "session-1"
