"""Streaming adapters for unified and compatibility chat endpoints."""

from __future__ import annotations

import json
import time
import uuid
from datetime import UTC, datetime
from typing import Any, AsyncGenerator, AsyncIterator

from ...repositories.conversations import MongoConversationRepository
from ...services.streaming_utils import now_ms
from ..orchestration.agent_service import AgentService
from .registration_service import RegistrationService


class StreamFacade:
    """Emit SSE events while adapting the new orchestration flow to public contracts."""

    def __init__(
        self,
        conversation_repository: MongoConversationRepository,
        agent_service: AgentService,
        registration_service: RegistrationService,
    ) -> None:
        self.conversation_repository = conversation_repository
        self.agent_service = agent_service
        self.registration_service = registration_service

    async def stream_reply(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        """Yield the compatibility streaming sequence for gateway-style endpoints."""
        async for event in self._stream_compat_reply(payload):
            yield self._event(event["event"], event["data"])

    async def stream_graph_reply(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        """Yield the architecture-first LangGraph streaming sequence."""
        async for event in self.agent_service.stream(payload):
            yield self._event(event["event"], event["data"])

    async def stream_legacy_openai_compat(self, payload: dict[str, Any]) -> AsyncGenerator[str, None]:
        """Yield the legacy `/openai/chat/stream` contract using the new orchestration path."""
        first_text_delta_ms: int | None = None
        total_ms: int | None = None
        trace_id = payload.get("trace_id")

        try:
            async for event in self.agent_service.stream(payload):
                event_name = event["event"]
                data = event["data"]

                if event_name == "text_delta":
                    if first_text_delta_ms is None:
                        first_text_delta_ms = data.get("elapsed_ms")
                    trace_id = data.get("trace_id") or trace_id
                    yield self._event("text_delta", data)
                    continue

                if event_name == "metrics":
                    metrics = data.get("metrics") or {}
                    total_ms = metrics.get("orchestration_total_ms") or total_ms
                    if metrics.get("first_text_delta_ms") is not None:
                        first_text_delta_ms = metrics.get("first_text_delta_ms")
                    trace_id = data.get("trace_id") or trace_id
                    continue

                if event_name == "done":
                    trace_id = data.get("trace_id") or trace_id
                    yield self._event(
                        "done",
                        {
                            "response": data.get("response", ""),
                            "model": data.get("model", "unconfigured"),
                            "provider": data.get("provider", "unconfigured"),
                            "session_id": data.get("session_id") or payload.get("session_id", "default"),
                            "username": data.get("username") or payload.get("username", "anonymous"),
                            "trace_id": trace_id,
                            "metrics": {
                                "ai_total_ms": total_ms,
                                "ai_first_delta_ms": first_text_delta_ms,
                            },
                            "success": True,
                        },
                    )
                    return
        except Exception:
            yield self._event(
                "error",
                {"error": "Erro interno no stream", "trace_id": trace_id},
            )

    async def _stream_compat_reply(
        self,
        payload: dict[str, Any],
    ) -> AsyncGenerator[dict[str, Any], None]:
        session_id = payload.get("session_id", "default")
        user_message = payload.get("message", "")
        is_voice_mode = bool(payload.get("is_voice_mode", False))
        trace_id = payload.get("trace_id") or f"trace_{uuid.uuid4().hex}"
        client_metrics = payload.get("client_metrics") or {}

        if self._is_registration_session(session_id):
            async for event in self._stream_registration_compat(
                session_id=session_id,
                user_message=user_message,
                is_voice_mode=is_voice_mode,
                trace_id=trace_id,
                client_metrics=client_metrics,
            ):
                yield event
            return

        started_at = time.perf_counter()
        identity = await self.conversation_repository.resolve_conversation_ref(session_id, create=True)
        chat_id = identity.get("chat_id")
        legacy_session_id = identity.get("legacy_session_id") or session_id
        username = identity.get("username") or self.conversation_repository.extract_username(legacy_session_id)
        if not username:
            raise ValueError(f"Session ID invalido: {legacy_session_id}")

        await self.conversation_repository.start_or_get_conversation(legacy_session_id)
        selected_voice, _ = await self.conversation_repository.get_voice_preferences(username)
        user_message_id = await self.conversation_repository.save_message(
            legacy_session_id,
            "user",
            user_message,
        )

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
                "client_metrics": client_metrics,
                "started_at": datetime.now(UTC).isoformat(),
            },
        }

        ai_request = {
            "message": user_message,
            "session_id": legacy_session_id,
            "chat_id": chat_id,
            "username": username,
            "session_objective": payload.get("session_objective"),
            "is_voice_mode": is_voice_mode,
            "trace_id": trace_id,
            "user_message_id": user_message_id,
        }

        metrics_payload: dict[str, Any] = {}
        tts_stream_failed = False
        done_data: dict[str, Any] | None = None

        async for event in self.agent_service.stream(ai_request):
            event_name = event["event"]
            data = event["data"]

            if event_name == "text_delta":
                yield event
                continue

            if event_name in {"audio_chunk", "audio_url"}:
                yield event
                continue

            if event_name == "error":
                if data.get("stage") == "tts_stream":
                    tts_stream_failed = True
                yield event
                continue

            if event_name == "metrics":
                metrics_payload = data.get("metrics") or {}
                continue

            if event_name == "done":
                done_data = data

        if done_data is None:
            raise RuntimeError("Fluxo de streaming concluido sem evento final")

        compat_metrics = {
            "gateway_total_ms": metrics_payload.get("orchestration_total_ms", now_ms(started_at)),
            "first_text_delta_ms": metrics_payload.get("first_text_delta_ms"),
            "first_audio_chunk_ms": metrics_payload.get("first_audio_event_ms"),
            "audio_chunks": metrics_payload.get("audio_events", 0),
            "tts_stream_failed": tts_stream_failed,
            "client_metrics": client_metrics,
            **metrics_payload,
        }
        yield {"event": "metrics", "data": {"trace_id": trace_id, "metrics": compat_metrics}}
        yield {
            "event": "done",
            "data": {
                "trace_id": trace_id,
                "success": True,
                "data": {
                    "chat_id": done_data.get("chat_id") or chat_id,
                    "session_id": done_data.get("session_id") or legacy_session_id,
                    "therapeutic_session_id": identity.get("therapeutic_session_id"),
                    "user_message": {"id": user_message_id, "content": user_message},
                    "ai_response": {
                        "id": done_data.get("ai_message_id"),
                        "content": done_data.get("response", ""),
                        "audioUrl": done_data.get("audio_url"),
                        "provider": done_data.get("provider", "unknown"),
                        "model": done_data.get("model", "unknown"),
                    },
                    "conversation_ended": done_data.get("conversation_ended", False),
                },
                "metrics": compat_metrics,
            },
        }

    async def _stream_registration_compat(
        self,
        *,
        session_id: str,
        user_message: str,
        is_voice_mode: bool,
        trace_id: str,
        client_metrics: dict[str, Any],
    ) -> AsyncGenerator[dict[str, Any], None]:
        started_at = time.perf_counter()
        identity = await self.conversation_repository.resolve_conversation_ref(session_id, create=True)
        username = identity.get("username") or self.conversation_repository.extract_username(session_id)
        if not username:
            raise ValueError(f"Session ID invalido: {session_id}")

        selected_voice, _ = await self.conversation_repository.get_voice_preferences(username)
        result = await self.registration_service.handle_message(
            session_id,
            user_message,
            is_voice_mode=is_voice_mode,
        )
        data = result.get("data") or {}
        user_message_data = data.get("user_message") or {"content": user_message}
        ai_response = data.get("ai_response") or {}

        yield {
            "event": "meta",
            "data": {
                "trace_id": trace_id,
                "chat_id": data.get("chat_id") or identity.get("chat_id"),
                "session_id": data.get("session_id") or identity.get("legacy_session_id") or session_id,
                "therapeutic_session_id": data.get("therapeutic_session_id") or identity.get("therapeutic_session_id"),
                "user_message": user_message_data,
                "voice": selected_voice,
                "streaming": True,
                "client_metrics": client_metrics,
                "started_at": datetime.now(UTC).isoformat(),
            },
        }
        if ai_response.get("content"):
            yield {
                "event": "text_delta",
                "data": {
                    "delta": ai_response["content"],
                    "trace_id": trace_id,
                    "elapsed_ms": now_ms(started_at),
                },
            }
        if is_voice_mode and ai_response.get("audioUrl"):
            yield {
                "event": "audio_url",
                "data": {
                    "audio_url": ai_response["audioUrl"],
                    "trace_id": trace_id,
                    "sequence": 0,
                    "segment": False,
                    "elapsed_ms": now_ms(started_at),
                },
            }

        metrics = {
            "gateway_total_ms": now_ms(started_at),
            "first_text_delta_ms": now_ms(started_at),
            "first_audio_chunk_ms": now_ms(started_at) if ai_response.get("audioUrl") else None,
            "audio_chunks": 1 if ai_response.get("audioUrl") else 0,
            "tts_stream_failed": False,
            "client_metrics": client_metrics,
        }
        yield {"event": "metrics", "data": {"trace_id": trace_id, "metrics": metrics}}
        yield {
            "event": "done",
            "data": {
                "trace_id": trace_id,
                "success": bool(result.get("success", True)),
                "data": data,
                "metrics": metrics,
            },
        }

    @staticmethod
    def _is_registration_session(session_id: str) -> bool:
        return session_id.endswith("_session-1") or session_id == "session-1"

    @staticmethod
    def _event(event: str, data: dict[str, Any]) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
