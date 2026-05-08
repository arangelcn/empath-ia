"""Tests for session-1 registration flow."""
import asyncio
from typing import Any, Dict, Optional

from src.services.registration_service import RegistrationService, REGISTRATION_QUESTIONS
from src.services.user_profile_service import UserProfileService


class FakeCollection:
    def __init__(self, existing_conversation=None):
        self.docs = {}
        if existing_conversation:
            self.docs[existing_conversation["session_id"]] = existing_conversation
        self.inserted = []
        self.updates = []

    async def find_one(self, query):
        session_id = query.get("session_id") or query.get("username")
        return self.docs.get(session_id)

    async def insert_one(self, doc):
        self.docs[doc["session_id"]] = doc
        self.inserted.append(doc)

    async def update_one(self, query, update):
        session_id = query.get("session_id")
        if session_id and session_id in self.docs:
            if "$set" in update:
                self.docs[session_id].update(update["$set"])
        self.updates.append((query, update))


saved_messages = []
finalize_called = []
generated_audio_calls = []


async def fake_save_message(session_id, msg_type, content, audio_url=None):
    saved_messages.append({"session_id": session_id, "type": msg_type, "content": content})
    return f"msg_{len(saved_messages)}"


async def fake_finalize(session_id, manual_termination=False):
    finalize_called.append(session_id)
    return {"success": True}


async def fake_generate_audio(text, voice, is_voice_mode=False):
    generated_audio_calls.append({"text": text, "voice": voice, "is_voice_mode": is_voice_mode})
    return None


def fake_extract_username(session_id):
    parts = session_id.rsplit("_", 1)
    return parts[0] if len(parts) == 2 and parts[1].startswith("session-") else None


def make_service(fake_conversations):
    import src.services.registration_service as reg_module
    orig_get_collection = None

    def patched_get_collection(name):
        if name == "conversations":
            return fake_conversations
        if name == "users":
            return FakeCollection()
        if name == "user_therapeutic_sessions":
            return FakeCollection()
        return FakeCollection()

    reg_module_get_collection = reg_module.get_collection
    reg_module.get_collection = patched_get_collection

    service = RegistrationService(
        save_message=fake_save_message,
        finalize_session_context=fake_finalize,
        generate_audio=fake_generate_audio,
        extract_username_from_session_id=fake_extract_username,
        user_profile_service=UserProfileService(),
    )

    return service, reg_module, reg_module_get_collection


def test_first_registration_step_saves_answer_and_returns_next_question():
    saved_messages.clear()

    conversation = {
        "session_id": "joao_session-1",
        "username": "joao",
        "registration_data": {},
        "registration_step": 0,
        "is_registration_complete": False,
    }
    fake_conv = FakeCollection(existing_conversation=conversation)
    service, reg_module, orig = make_service(fake_conv)

    try:
        result = asyncio.run(service.handle_session("joao_session-1", "28", is_voice_mode=False))
    finally:
        reg_module.get_collection = orig

    assert result["success"] is True
    data = result["data"]
    # User message saved
    user_msgs = [m for m in saved_messages if m["type"] == "user"]
    assert any(m["content"] == "28" for m in user_msgs)
    # Next question returned
    assert REGISTRATION_QUESTIONS[1]["question"] in data["ai_response"]["content"]


def test_registration_first_field_stored_as_idade():
    saved_messages.clear()

    conversation = {
        "session_id": "maria_session-1",
        "username": "maria",
        "registration_data": {},
        "registration_step": 0,
        "is_registration_complete": False,
    }
    fake_conv = FakeCollection(existing_conversation=conversation)
    service, reg_module, orig = make_service(fake_conv)

    try:
        asyncio.run(service.handle_session("maria_session-1", "35"))
    finally:
        reg_module.get_collection = orig

    stored = fake_conv.docs["maria_session-1"]["registration_data"]
    assert stored.get("idade") == "35"


def test_registration_new_conversation_is_created_when_missing():
    saved_messages.clear()

    fake_conv = FakeCollection()  # no existing conversation
    service, reg_module, orig = make_service(fake_conv)

    try:
        result = asyncio.run(service.handle_session("novo_session-1", "20"))
    finally:
        reg_module.get_collection = orig

    assert result["success"] is True
    assert len(fake_conv.inserted) == 1
    assert fake_conv.inserted[0]["username"] == "novo"


def test_registration_voice_mode_uses_current_default_voice():
    saved_messages.clear()
    generated_audio_calls.clear()

    conversation = {
        "session_id": "joao_session-1",
        "username": "joao",
        "registration_data": {},
        "registration_step": 0,
        "is_registration_complete": False,
    }
    fake_conv = FakeCollection(existing_conversation=conversation)
    service, reg_module, orig = make_service(fake_conv)

    try:
        result = asyncio.run(service.handle_session("joao_session-1", "28", is_voice_mode=True))
    finally:
        reg_module.get_collection = orig

    assert result["success"] is True
    assert generated_audio_calls
    assert generated_audio_calls[0]["voice"] == "pt-BR-Neural2-B"
