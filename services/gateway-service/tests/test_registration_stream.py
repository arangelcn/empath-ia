import asyncio

from src.services.chat_service import ChatService


def test_registration_stream_includes_user_message_in_meta(monkeypatch):
    service = ChatService()

    async def fake_resolve_conversation_ref(conversation_ref, **kwargs):
        return {
            "chat_id": "chat_123",
            "legacy_session_id": "ana_session-1",
            "username": "ana",
            "therapeutic_session_id": "session-1",
        }

    async def fake_process_user_message(session_id, user_message, session_objective=None, is_voice_mode=False):
        assert is_voice_mode is False
        return {
            "success": True,
            "data": {
                "user_message": {
                    "id": "user_msg_1",
                    "content": user_message,
                },
                "ai_response": {
                    "id": "ai_msg_1",
                    "content": "Obrigado. Agora me conta mais.",
                    "audioUrl": "/api/voice/audio/answer.mp3",
                },
            },
        }

    async def fake_get_voice_config(username, is_voice_mode=False):
        assert username == "ana"
        assert is_voice_mode is True
        return "pt-BR-Neural2-B", True

    async def fake_stream_tts_chunk(text, voice, trace_id, sequence, started_at):
        assert voice == "pt-BR-Neural2-B"
        yield {
            "event": "audio_chunk",
            "data": {
                "trace_id": trace_id,
                "sequence": sequence,
                "audio": "AAAA",
                "sample_rate_hz": 24000,
                "encoding": "PCM",
                "elapsed_ms": 1,
            },
        }

    monkeypatch.setattr(service, "resolve_conversation_ref", fake_resolve_conversation_ref)
    monkeypatch.setattr(service, "process_user_message", fake_process_user_message)
    monkeypatch.setattr(service, "_get_voice_config", fake_get_voice_config)
    monkeypatch.setattr(service, "_stream_tts_chunk", fake_stream_tts_chunk)

    async def collect_events():
        return [
            event
            async for event in service.process_user_message_stream(
                "chat_123",
                "28",
                is_voice_mode=True,
                trace_id="trace_test",
            )
        ]

    events = asyncio.run(collect_events())

    meta = events[0]
    done = events[-1]
    assert meta["event"] == "meta"
    assert meta["data"]["user_message"] == {"id": "user_msg_1", "content": "28"}
    assert any(event["event"] == "audio_chunk" for event in events)
    assert done["event"] == "done"
    assert done["data"]["data"]["ai_response"]["id"] == "ai_msg_1"
