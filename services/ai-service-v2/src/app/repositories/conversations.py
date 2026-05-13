"""Mongo-backed conversation repository for ai-service-v2."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from ..domain.conversations.identity import (
    build_legacy_session_id,
    split_composite_session_id,
)
from ..infrastructure.db.mongo import MongoManager


logger = logging.getLogger(__name__)


class MongoConversationRepository:
    """Encapsulate Mongo access for conversations and messages."""

    def __init__(self, mongo: MongoManager) -> None:
        self.mongo = mongo

    def extract_username(self, session_id: str) -> str | None:
        """Extract the username from ``username_session-N`` identifiers."""
        username, original_session_id = split_composite_session_id(session_id)
        if username and original_session_id.startswith("session-"):
            return username
        if session_id in {"default", "test"}:
            return "anonymous"
        return None

    async def resolve_conversation_ref(
        self,
        conversation_ref: str,
        *,
        username: str | None = None,
        therapeutic_session_id: str | None = None,
        create: bool = False,
    ) -> dict[str, Any]:
        """Resolve a public chat id or legacy session id to the canonical document."""
        conversations = self.mongo.get_collection("conversations")
        conversation = None

        if conversation_ref:
            conversation = await conversations.find_one({"chat_id": conversation_ref})

        if not conversation and username and therapeutic_session_id:
            conversation = await conversations.find_one(
                {"username": username, "therapeutic_session_id": therapeutic_session_id}
            )

        legacy_session_id = build_legacy_session_id(username, therapeutic_session_id)
        if not conversation and conversation_ref:
            parsed_username, parsed_session_id = split_composite_session_id(conversation_ref)
            if parsed_username and parsed_session_id.startswith("session-"):
                username = username or parsed_username
                therapeutic_session_id = therapeutic_session_id or parsed_session_id
                legacy_session_id = conversation_ref
                conversation = await conversations.find_one({"session_id": conversation_ref})
            else:
                conversation = await conversations.find_one({"session_id": conversation_ref})
                legacy_session_id = conversation_ref

        if not conversation and username and therapeutic_session_id:
            legacy_session_id = build_legacy_session_id(username, therapeutic_session_id)
            conversation = await conversations.find_one({"session_id": legacy_session_id})

        if conversation:
            return await self._ensure_conversation_identity(conversation, legacy_session_id)

        if not create:
            parsed_username, parsed_session_id = split_composite_session_id(conversation_ref or "")
            return {
                "chat_id": None,
                "legacy_session_id": conversation_ref or legacy_session_id,
                "username": username or parsed_username,
                "therapeutic_session_id": therapeutic_session_id or parsed_session_id,
                "conversation": None,
            }

        if not username or not therapeutic_session_id:
            parsed_username, parsed_session_id = split_composite_session_id(conversation_ref or "")
            username = username or parsed_username
            therapeutic_session_id = therapeutic_session_id or parsed_session_id

        chat_id = f"chat_{uuid.uuid4().hex}"
        legacy_session_id = build_legacy_session_id(username, therapeutic_session_id)
        now = datetime.now(UTC)
        conversation_data = {
            "chat_id": chat_id,
            "session_id": legacy_session_id,
            "legacy_session_id": legacy_session_id,
            "therapeutic_session_id": therapeutic_session_id,
            "username": username,
            "created_at": now,
            "updated_at": now,
            "user_preferences": {},
            "message_count": 0,
            "is_active": True,
        }
        await conversations.insert_one(conversation_data)
        return {
            "chat_id": chat_id,
            "legacy_session_id": legacy_session_id,
            "username": username,
            "therapeutic_session_id": therapeutic_session_id,
            "conversation": conversation_data,
        }

    async def start_or_get_conversation(
        self,
        session_id: str,
        username: str | None = None,
        therapeutic_session_id: str | None = None,
    ) -> dict[str, Any]:
        """Create or load a conversation without mutating the legacy services."""
        identity = await self.resolve_conversation_ref(
            session_id,
            username=username,
            therapeutic_session_id=therapeutic_session_id,
            create=True,
        )
        conversation = identity["conversation"] or {}
        return {
            "chat_id": identity["chat_id"],
            "session_id": identity["legacy_session_id"],
            "therapeutic_session_id": identity["therapeutic_session_id"],
            "username": identity["username"],
            "exists": bool(conversation.get("_id")),
            "user_preferences": conversation.get("user_preferences", {}),
            "created_at": conversation.get("created_at"),
            "updated_at": conversation.get("updated_at"),
        }

    async def save_message(
        self,
        session_id: str,
        message_type: str,
        content: str,
        audio_url: str | None = None,
    ) -> str:
        """Persist a chat message."""
        messages = self.mongo.get_collection("messages")
        identity = await self.resolve_conversation_ref(session_id)
        chat_id = identity.get("chat_id")
        legacy_session_id = identity.get("legacy_session_id") or session_id
        username = identity.get("username") or self.extract_username(legacy_session_id)

        message_data = {
            "chat_id": chat_id,
            "session_id": legacy_session_id,
            "therapeutic_session_id": identity.get("therapeutic_session_id"),
            "username": username,
            "type": message_type,
            "content": content,
            "audio_url": audio_url,
            "created_at": datetime.now(UTC),
        }
        result = await messages.insert_one(message_data)
        return str(result.inserted_id)

    async def get_history(self, session_id: str) -> dict[str, Any]:
        """Load a full conversation history."""
        messages = self.mongo.get_collection("messages")
        identity = await self.resolve_conversation_ref(session_id)
        chat_id = identity.get("chat_id")
        legacy_session_id = identity.get("legacy_session_id") or session_id
        username = identity.get("username") or self.extract_username(legacy_session_id)

        if chat_id:
            query: dict[str, Any] = {"$or": [{"chat_id": chat_id}, {"session_id": legacy_session_id}]}
        else:
            query = {"session_id": legacy_session_id}
        if username:
            query["username"] = username

        cursor = messages.find(query, sort=[("created_at", 1)])
        history = []
        async for msg in cursor:
            history.append(
                {
                    "id": str(msg["_id"]),
                    "type": msg["type"],
                    "content": msg["content"],
                    "audio_url": msg.get("audio_url"),
                    "created_at": msg.get("created_at").isoformat() if msg.get("created_at") else None,
                }
            )

        return {
            "chat_id": chat_id,
            "session_id": legacy_session_id,
            "therapeutic_session_id": identity.get("therapeutic_session_id"),
            "username": username,
            "history": history,
            "message_count": len(history),
        }

    async def get_context(self, session_id: str) -> list[dict[str, Any]]:
        """Return history in the shape expected by the legacy ai-service."""
        history = await self.get_history(session_id)
        return [{"type": item["type"], "content": item["content"]} for item in history["history"]]

    async def list_recent(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent conversations for admin/debug flows."""
        conversations = self.mongo.get_collection("conversations")
        cursor = conversations.find({}, sort=[("updated_at", -1)], limit=limit)
        result = []
        async for conv in cursor:
            result.append(
                {
                    "chat_id": conv.get("chat_id"),
                    "session_id": conv["session_id"],
                    "therapeutic_session_id": conv.get("therapeutic_session_id"),
                    "username": conv.get("username"),
                    "created_at": conv.get("created_at"),
                    "updated_at": conv.get("updated_at"),
                    "message_count": conv.get("message_count", 0),
                }
            )
        return result

    async def update_message_count(self, session_id: str) -> None:
        """Increment the aggregate conversation message counter."""
        conversations = self.mongo.get_collection("conversations")
        identity = await self.resolve_conversation_ref(session_id)
        query = {"chat_id": identity["chat_id"]} if identity.get("chat_id") else {"session_id": identity.get("legacy_session_id") or session_id}
        await conversations.update_one(
            query,
            {"$inc": {"message_count": 1}, "$set": {"updated_at": datetime.now(UTC)}},
        )

    async def get_initial_prompt(self, session_id: str) -> str | None:
        """Load the personalized initial prompt from user sessions."""
        identity = await self.resolve_conversation_ref(session_id)
        username = identity.get("username")
        original_session_id = identity.get("therapeutic_session_id") or session_id
        if not username:
            return None

        user_sessions = self.mongo.get_collection("user_therapeutic_sessions")
        user_session = await user_sessions.find_one(
            {"username": username, "session_id": original_session_id}
        )
        if user_session and user_session.get("initial_prompt"):
            return user_session["initial_prompt"]
        return None

    async def get_by_session_id(self, session_id: str) -> dict[str, Any] | None:
        """Return the normalized conversation document when available."""
        identity = await self.resolve_conversation_ref(session_id)
        conversation = identity.get("conversation")
        if conversation and "_id" in conversation:
            conversation["_id"] = str(conversation["_id"])
        return conversation

    async def update_conversation_fields(self, session_id: str, fields: dict[str, Any]) -> None:
        """Update top-level conversation fields for the canonical conversation document."""
        conversations = self.mongo.get_collection("conversations")
        identity = await self.resolve_conversation_ref(session_id, create=True)
        conversation = identity.get("conversation")
        if conversation and conversation.get("_id"):
            await conversations.update_one(
                {"_id": conversation["_id"]},
                {"$set": {**fields, "updated_at": datetime.now(UTC)}},
            )
            return

        legacy_session_id = identity.get("legacy_session_id") or session_id
        await conversations.update_one(
            {"session_id": legacy_session_id},
            {"$set": {**fields, "updated_at": datetime.now(UTC)}},
            upsert=True,
        )

    async def get_voice_preferences(self, username: str) -> tuple[str, bool]:
        """Load voice preferences from the user record."""
        users = self.mongo.get_collection("users")
        user = await users.find_one({"username": username})
        preferences = (user or {}).get("preferences", {})
        selected_voice = preferences.get("selected_voice", "pt-BR-Neural2-B")
        voice_enabled = preferences.get("voice_enabled", True)
        return selected_voice, voice_enabled

    async def get_user_document(self, username: str) -> dict[str, Any] | None:
        """Fetch the raw user document."""
        users = self.mongo.get_collection("users")
        return await users.find_one({"username": username})

    async def get_session_context(self, session_id: str) -> dict[str, Any] | None:
        """Fetch a generated session context document."""
        session_contexts = self.mongo.get_collection("session_contexts")
        context_doc = await session_contexts.find_one({"session_id": session_id})
        if context_doc:
            return context_doc.get("context")
        return None

    async def _ensure_conversation_identity(
        self,
        conversation: dict[str, Any],
        fallback_ref: str | None = None,
    ) -> dict[str, Any]:
        conversations = self.mongo.get_collection("conversations")
        updates: dict[str, Any] = {}

        chat_id = conversation.get("chat_id")
        if not chat_id:
            chat_id = f"chat_{uuid.uuid4().hex}"
            updates["chat_id"] = chat_id

        legacy_session_id = conversation.get("legacy_session_id") or conversation.get("session_id") or fallback_ref
        username = conversation.get("username") or conversation.get("user_preferences", {}).get("username")
        therapeutic_session_id = conversation.get("therapeutic_session_id")

        if legacy_session_id and not therapeutic_session_id:
            parsed_username, parsed_session_id = split_composite_session_id(legacy_session_id)
            if parsed_username and parsed_session_id.startswith("session-"):
                username = username or parsed_username
                therapeutic_session_id = parsed_session_id

        if not legacy_session_id:
            legacy_session_id = build_legacy_session_id(username, therapeutic_session_id)

        if username and conversation.get("username") != username:
            updates["username"] = username
        if therapeutic_session_id and conversation.get("therapeutic_session_id") != therapeutic_session_id:
            updates["therapeutic_session_id"] = therapeutic_session_id
        if legacy_session_id and conversation.get("legacy_session_id") != legacy_session_id:
            updates["legacy_session_id"] = legacy_session_id

        if updates:
            updates["updated_at"] = datetime.now(UTC)
            await conversations.update_one({"_id": conversation["_id"]}, {"$set": updates})
            conversation.update(updates)

        return {
            "chat_id": chat_id,
            "legacy_session_id": legacy_session_id,
            "username": username,
            "therapeutic_session_id": therapeutic_session_id,
            "conversation": conversation,
        }
