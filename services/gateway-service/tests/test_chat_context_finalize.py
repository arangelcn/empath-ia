"""Tests for chat context finalization endpoint behavior."""

import asyncio

from fastapi import HTTPException

from src.api import chat_context


class _StubChatServiceFinalizeError:
    async def resolve_conversation_ref(self, session_id):
        return {
            "chat_id": session_id,
            "legacy_session_id": session_id,
            "username": "tester",
            "therapeutic_session_id": "session-1",
        }

    async def finalize_session_context(self, session_id, manual_termination=False):
        return {"success": False, "error": "Conversa não encontrada"}


class _StubChatServiceRaisesHttpException:
    async def resolve_conversation_ref(self, session_id):
        raise HTTPException(status_code=404, detail="Conversa não encontrada")


def test_finalize_session_returns_404_when_conversation_is_missing():
    original_chat_service = chat_context.chat_service
    chat_context.chat_service = _StubChatServiceFinalizeError()

    try:
        try:
            asyncio.run(chat_context.finalize_session("chat_missing"))
        except HTTPException as exc:
            assert exc.status_code == 404
            assert exc.detail == "Conversa não encontrada"
        else:
            raise AssertionError("Expected HTTPException for missing conversation")
    finally:
        chat_context.chat_service = original_chat_service


def test_finalize_session_preserves_http_exception_status():
    original_chat_service = chat_context.chat_service
    chat_context.chat_service = _StubChatServiceRaisesHttpException()

    try:
        try:
            asyncio.run(chat_context.finalize_session("chat_missing"))
        except HTTPException as exc:
            assert exc.status_code == 404
            assert exc.detail == "Conversa não encontrada"
        else:
            raise AssertionError("Expected HTTPException from resolve_conversation_ref")
    finally:
        chat_context.chat_service = original_chat_service
