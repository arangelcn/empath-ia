import asyncio
import json

from src.services import chat_service as chat_service_module
from src.services.chat_service import ChatService


class FakeUpdateResult:
    matched_count = 1


class FakeCollection:
    def __init__(self):
        self.updates = []

    async def find_one(self, query):
        return {
            "chat_id": query["chat_id"],
            "username": "toni",
            "therapeutic_session_id": "session-2",
        }

    async def update_one(self, query, update):
        self.updates.append((query, update))
        return FakeUpdateResult()


class FakeResponse:
    status_code = 200
    payload = {
        "success": True,
        "text": json.dumps(
            {
                "title": "Ansiedade no trabalho",
                "subtitle": "Explorando pressões e limites no dia a dia",
            }
        ),
    }

    def json(self):
        return self.payload


class FakeAsyncClient:
    requests = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json, timeout):
        self.requests.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse()


def test_generate_chat_title_uses_ai_util_complete(monkeypatch):
    conversations = FakeCollection()
    user_sessions = FakeCollection()

    def fake_get_collection(name):
        return {
            "conversations": conversations,
            "user_therapeutic_sessions": user_sessions,
        }[name]

    async def fake_context(chat_id):
        return [
            {"type": "user", "content": "Estou me sentindo muito pressionado no trabalho."},
            {"type": "ai", "content": "Parece que essa pressão tem pesado bastante para você."},
        ]

    FakeAsyncClient.requests = []
    monkeypatch.setattr(chat_service_module, "get_collection", fake_get_collection)
    monkeypatch.setattr(chat_service_module.httpx, "AsyncClient", FakeAsyncClient)

    service = ChatService()
    service.ai_service_url = "http://ai-service:8001"
    monkeypatch.setattr(service, "_get_conversation_context", fake_context)

    result = asyncio.run(service.generate_chat_title("chat_123", "initial"))

    assert result == {
        "success": True,
        "title": "Ansiedade no trabalho",
        "subtitle": "Explorando pressões e limites no dia a dia",
    }
    assert FakeAsyncClient.requests[0]["url"] == "http://ai-service:8001/util/complete"
    assert FakeAsyncClient.requests[0]["json"]["prompt"]
    assert FakeAsyncClient.requests[0]["json"]["max_tokens"] == 180
    assert conversations.updates[0][1]["$set"]["title"] == "Ansiedade no trabalho"


def test_generate_chat_title_accepts_dict_text_payload(monkeypatch):
    conversations = FakeCollection()
    user_sessions = FakeCollection()

    def fake_get_collection(name):
        return {
            "conversations": conversations,
            "user_therapeutic_sessions": user_sessions,
        }[name]

    async def fake_context(chat_id):
        return [
            {"type": "user", "content": {"text": "Estou sem energia no trabalho."}},
            {"type": "ai", "content": {"content": "Parece que sua energia tem sido muito exigida."}},
        ]

    FakeAsyncClient.requests = []
    FakeResponse.payload = {
        "success": True,
        "text": {
            "title": "Cansaço no trabalho",
            "subtitle": "Reconhecendo limites e energia emocional",
        },
    }
    monkeypatch.setattr(chat_service_module, "get_collection", fake_get_collection)
    monkeypatch.setattr(chat_service_module.httpx, "AsyncClient", FakeAsyncClient)

    service = ChatService()
    service.ai_service_url = "http://ai-service:8001"
    monkeypatch.setattr(service, "_get_conversation_context", fake_context)

    try:
        result = asyncio.run(service.generate_chat_title("chat_123", "initial"))
    finally:
        FakeResponse.payload = {
            "success": True,
            "text": json.dumps(
                {
                    "title": "Ansiedade no trabalho",
                    "subtitle": "Explorando pressões e limites no dia a dia",
                }
            ),
        }

    assert result == {
        "success": True,
        "title": "Cansaço no trabalho",
        "subtitle": "Reconhecendo limites e energia emocional",
    }


def test_generate_chat_title_parses_fenced_json_inside_content(monkeypatch):
    conversations = FakeCollection()
    user_sessions = FakeCollection()

    def fake_get_collection(name):
        return {
            "conversations": conversations,
            "user_therapeutic_sessions": user_sessions,
        }[name]

    async def fake_context(chat_id):
        return [
            {"type": "user", "content": "Estou sem energia no trabalho."},
            {"type": "ai", "content": "Parece que sua energia tem sido muito exigida."},
        ]

    FakeAsyncClient.requests = []
    FakeResponse.payload = {
        "success": True,
        "text": {
            "content": """```json
{
  "title": "Cansaço no trabalho",
  "subtitle": "Reconhecendo limites e energia emocional"
}
```"""
        },
    }
    monkeypatch.setattr(chat_service_module, "get_collection", fake_get_collection)
    monkeypatch.setattr(chat_service_module.httpx, "AsyncClient", FakeAsyncClient)

    service = ChatService()
    service.ai_service_url = "http://ai-service:8001"
    monkeypatch.setattr(service, "_get_conversation_context", fake_context)

    try:
        result = asyncio.run(service.generate_chat_title("chat_123", "initial"))
    finally:
        FakeResponse.payload = {
            "success": True,
            "text": json.dumps(
                {
                    "title": "Ansiedade no trabalho",
                    "subtitle": "Explorando pressões e limites no dia a dia",
                }
            ),
        }

    assert result == {
        "success": True,
        "title": "Cansaço no trabalho",
        "subtitle": "Reconhecendo limites e energia emocional",
    }
