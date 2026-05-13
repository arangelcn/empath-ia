"""Smoke tests for ai-service-v2 route contracts."""

from __future__ import annotations

import json
import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.app.api import register_routers
from src.app.bootstrap.settings import get_settings


class FakeChatFacade:
    async def process_user_message(
        self,
        session_id: str,
        user_message: str,
        session_objective: dict | None = None,
        is_voice_mode: bool = False,
    ) -> dict[str, object]:
        return {
            "success": True,
            "data": {
                "chat_id": "chat_1",
                "session_id": session_id,
                "therapeutic_session_id": "session-2",
                "user_message": {"id": "user_1", "content": user_message},
                "ai_response": {
                    "id": "ai_1",
                    "content": "resposta de teste",
                    "audioUrl": "/api/voice/audio/test.wav" if is_voice_mode else None,
                    "provider": "fake",
                    "model": "fake-model",
                },
                "conversation_ended": False,
            },
        }

    async def get_history(self, session_id: str) -> dict[str, object]:
        return {"chat_id": "chat_1", "session_id": session_id, "history": [], "message_count": 0}

    async def start_conversation(
        self,
        session_id: str,
        username: str | None = None,
        therapeutic_session_id: str | None = None,
    ) -> dict[str, object]:
        return {
            "chat_id": "chat_1",
            "session_id": session_id,
            "therapeutic_session_id": therapeutic_session_id or "session-2",
            "username": username or "tester",
            "exists": True,
        }

    async def list_recent_conversations(self, limit: int = 10) -> list[dict[str, object]]:
        return [{"chat_id": "chat_1", "session_id": "tester_session-2"}][:limit]

    async def generate_reply(self, payload: dict[str, object]) -> dict[str, object]:
        return {
            "response": "reply",
            "model": "fake-model",
            "session_id": str(payload.get("session_id", "default")),
            "username": str(payload.get("username", "anonymous")),
            "timestamp": "2026-01-01T00:00:00+00:00",
            "provider": "fake",
            "success": True,
            "trace_id": "trace_1",
            "chat_id": payload.get("chat_id"),
            "migration": {"phase": "test"},
        }

    async def generate_legacy_compat_reply(self, payload: dict[str, object]) -> dict[str, object]:
        return {
            "response": "legacy reply",
            "model": "fake-model",
            "session_id": str(payload.get("session_id", "default")),
            "username": str(payload.get("username", "anonymous")),
            "timestamp": "2026-01-01T00:00:00+00:00",
            "provider": "fake",
            "success": True,
        }


class FakeStreamFacade:
    async def stream_reply(self, payload: dict[str, object]):
        events = [
            ("meta", {"trace_id": "trace_1", "session_id": payload.get("session_id", "default")}),
            ("text_delta", {"trace_id": "trace_1", "delta": "hello"}),
            (
                "done",
                {
                    "trace_id": "trace_1",
                    "success": True,
                    "data": {
                        "ai_response": {"id": "ai_1", "content": "hello", "audioUrl": None},
                        "user_message": {"id": "user_1", "content": payload.get("message", "")},
                    },
                },
            ),
        ]
        for event, data in events:
            yield self._sse(event, data)

    async def stream_graph_reply(self, payload: dict[str, object]):
        for event, data in [
            ("meta", {"trace_id": "trace_1"}),
            ("status", {"trace_id": "trace_1", "node": "generation"}),
            ("done", {"trace_id": "trace_1", "response": "hello"}),
        ]:
            yield self._sse(event, data)

    async def stream_legacy_openai_compat(self, payload: dict[str, object]):
        for event, data in [
            ("text_delta", {"trace_id": "trace_1", "delta": "hello"}),
            (
                "done",
                {
                    "trace_id": "trace_1",
                    "response": "hello",
                    "provider": "fake",
                    "model": "fake-model",
                    "session_id": payload.get("session_id", "default"),
                    "username": payload.get("username", "anonymous"),
                    "success": True,
                    "metrics": {"ai_total_ms": 1, "ai_first_delta_ms": 1},
                },
            ),
        ]:
            yield self._sse(event, data)

    @staticmethod
    def _sse(event: str, data: dict[str, object]) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class SmokeRoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        settings = get_settings()

        @asynccontextmanager
        async def noop_lifespan(app: FastAPI):
            yield

        app = FastAPI(title=settings.app_name, lifespan=noop_lifespan)
        register_routers(app)

        @app.get("/")
        async def root() -> dict[str, object]:
            return {
                "service": settings.app_slug,
                "name": settings.app_name,
                "version": settings.app_version,
                "status": "bootstrapped",
                "migration_phase": "compatibility-hardening",
                "docs": "/docs",
            }

        @app.get("/health")
        async def health() -> dict[str, object]:
            return {
                "status": "healthy",
                "service": settings.app_slug,
                "version": settings.app_version,
                "migration_phase": "compatibility-hardening",
            }

        app.state.container = SimpleNamespace(
            settings=settings,
            chat_facade=FakeChatFacade(),
            stream_facade=FakeStreamFacade(),
            runtime_service=SimpleNamespace(
                describe=lambda: {
                    "service": "ai-service-v2",
                    "status": "langchain-runtime-shell",
                    "provider_chain": ["fake"],
                    "available_providers": ["fake"],
                    "native_streaming_providers": ["fake"],
                }
            ),
        )
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()

    def test_root_health_and_openapi(self) -> None:
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/openapi.json").status_code, 200)

    def test_internal_routes(self) -> None:
        health_response = self.client.get("/internal/health")
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(health_response.json()["migration_phase"], "compatibility-hardening")

        llm_response = self.client.get("/internal/llm/status")
        self.assertEqual(llm_response.status_code, 200)
        self.assertEqual(llm_response.json()["status"], "langchain-runtime-shell")

        compat_response = self.client.get("/internal/compatibility/routes")
        self.assertEqual(compat_response.status_code, 200)
        self.assertEqual(compat_response.json()["phase"], "compatibility-hardening")

    def test_chat_sync_routes(self) -> None:
        send_response = self.client.post(
            "/api/chat/send",
            json={"message": "oi", "session_id": "tester_session-2", "is_voice_mode": False},
        )
        self.assertEqual(send_response.status_code, 200)
        self.assertTrue(send_response.json()["success"])

        chat_response = self.client.post(
            "/api/chat",
            json={"message": "oi", "session_id": "tester_session-2", "username": "tester"},
        )
        self.assertEqual(chat_response.status_code, 200)
        self.assertEqual(chat_response.json()["provider"], "fake")

        openai_response = self.client.post(
            "/openai/chat",
            json={"message": "oi", "session_id": "tester_session-2", "username": "tester"},
        )
        self.assertEqual(openai_response.status_code, 200)
        self.assertEqual(openai_response.json()["response"], "legacy reply")

    def test_chat_stream_routes(self) -> None:
        send_stream_response = self.client.post(
            "/api/chat/send-stream",
            json={"message": "oi", "session_id": "tester_session-2", "is_voice_mode": False},
        )
        self.assertEqual(send_stream_response.status_code, 200)
        self.assertIn("event: meta", send_stream_response.text)
        self.assertIn("event: done", send_stream_response.text)

        stream_response = self.client.post(
            "/api/chat/stream",
            json={"message": "oi", "session_id": "tester_session-2", "username": "tester"},
        )
        self.assertEqual(stream_response.status_code, 200)
        self.assertIn("event: status", stream_response.text)

        openai_stream_response = self.client.post(
            "/openai/chat/stream",
            json={"message": "oi", "session_id": "tester_session-2", "username": "tester"},
        )
        self.assertEqual(openai_stream_response.status_code, 200)
        self.assertIn("event: text_delta", openai_stream_response.text)
        self.assertIn("event: done", openai_stream_response.text)


if __name__ == "__main__":
    unittest.main()
