"""Mongo repositories for therapeutic sessions and saved session contexts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..infrastructure.db.mongo import MongoManager


REGISTRATION_SESSION_ID = "session-1"


class MongoSessionRepository:
    """Persistence boundary for user therapeutic sessions and derived contexts."""

    def __init__(self, mongo: MongoManager) -> None:
        self.mongo = mongo

    async def get_user_session(self, username: str, session_id: str) -> dict[str, Any] | None:
        """Fetch a user-owned therapeutic session."""
        user_sessions = self.mongo.get_collection("user_therapeutic_sessions")
        return await user_sessions.find_one({"username": username, "session_id": session_id})

    async def ensure_registration_session(self, username: str) -> dict[str, Any]:
        """Create the deterministic onboarding session when it does not exist yet."""
        existing = await self.get_user_session(username, REGISTRATION_SESSION_ID)
        if existing:
            return existing

        now = datetime.now(UTC)
        document = {
            "username": username,
            "session_id": REGISTRATION_SESSION_ID,
            "template_session_id": REGISTRATION_SESSION_ID,
            "title": "Cadastro e Apresentacao",
            "subtitle": "Vamos nos conhecer melhor",
            "description": "Sessao inicial para coleta de informacoes pessoais e vinculo terapeutico",
            "objective": "Coletar informacoes pessoais do usuario e estabelecer o primeiro contato terapeutico",
            "initial_prompt": (
                "Ola! Eu sou seu assistente terapeutico. E um prazer te conhecer! "
                "Para personalizar nossa conversa, vou fazer algumas perguntas sobre voce. "
                "Primeiro, me conta: qual e a sua idade?"
            ),
            "category": "onboarding",
            "difficulty": "beginner",
            "focus_areas": ["cadastro", "autoconhecimento", "vinculo_terapeutico"],
            "session_type": "registration",
            "estimated_duration": 30,
            "generation_method": "registration_seed",
            "status": "unlocked",
            "progress": 0,
            "completed_at": None,
            "started_at": None,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "is_registration_session": True,
            "personalized": False,
        }
        user_sessions = self.mongo.get_collection("user_therapeutic_sessions")
        await user_sessions.update_one(
            {"username": username, "session_id": REGISTRATION_SESSION_ID},
            {"$setOnInsert": document},
            upsert=True,
        )
        current = await self.get_user_session(username, REGISTRATION_SESSION_ID)
        return current or document

    async def complete_user_session(
        self,
        username: str,
        session_id: str,
        *,
        progress: int = 100,
        status: str = "completed",
    ) -> None:
        """Mark a user session as completed."""
        user_sessions = self.mongo.get_collection("user_therapeutic_sessions")
        now = datetime.now(UTC)
        await user_sessions.update_one(
            {"username": username, "session_id": session_id},
            {
                "$set": {
                    "status": status,
                    "progress": progress,
                    "completed_at": now,
                    "updated_at": now,
                }
            },
        )

    async def update_user_session_fields(
        self,
        username: str,
        session_id: str,
        fields: dict[str, Any],
    ) -> None:
        """Patch arbitrary metadata on a user therapeutic session."""
        user_sessions = self.mongo.get_collection("user_therapeutic_sessions")
        await user_sessions.update_one(
            {"username": username, "session_id": session_id},
            {"$set": fields},
        )

    async def unlock_user_session(self, username: str, session_id: str) -> None:
        """Unlock an existing user session."""
        user_sessions = self.mongo.get_collection("user_therapeutic_sessions")
        await user_sessions.update_one(
            {"username": username, "session_id": session_id},
            {"$set": {"status": "unlocked", "updated_at": datetime.now(UTC)}},
        )

    async def create_user_session(self, username: str, session_data: dict[str, Any]) -> dict[str, Any]:
        """Upsert a personalized user session document."""
        session_id = session_data["session_id"]
        user_sessions = self.mongo.get_collection("user_therapeutic_sessions")
        now = datetime.now(UTC)
        document = {
            "username": username,
            "session_id": session_id,
            "title": session_data.get("title", "Sessao Terapeutica"),
            "subtitle": session_data.get("subtitle", ""),
            "objective": session_data.get("objective", ""),
            "initial_prompt": session_data.get("initial_prompt", ""),
            "focus_areas": session_data.get("focus_areas", []),
            "therapeutic_approach": session_data.get("therapeutic_approach", ""),
            "expected_outcomes": session_data.get("expected_outcomes", []),
            "session_type": session_data.get("session_type", "continuacao"),
            "estimated_duration": session_data.get("estimated_duration", "45-60 minutos"),
            "preparation_notes": session_data.get("preparation_notes", ""),
            "connection_to_previous": session_data.get("connection_to_previous", ""),
            "personalization_factors": session_data.get("personalization_factors", []),
            "generated_at": session_data.get("generated_at"),
            "based_on_session": session_data.get("based_on_session"),
            "generation_method": session_data.get("generation_method", "context_based_template"),
            "personalized": session_data.get("personalized", True),
            "is_active": session_data.get("is_active", True),
            "status": session_data.get("status", "unlocked"),
            "progress": session_data.get("progress", 0),
            "updated_at": now,
        }
        await user_sessions.update_one(
            {"username": username, "session_id": session_id},
            {"$set": document, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        stored = await self.get_user_session(username, session_id)
        return stored or document

    async def save_session_context(
        self,
        session_id: str,
        username: str,
        context: dict[str, Any],
    ) -> None:
        """Persist the normalized session context in the canonical collection."""
        session_contexts = self.mongo.get_collection("session_contexts")
        now = datetime.now(UTC)
        await session_contexts.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "session_id": session_id,
                    "username": username,
                    "context": context,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )
