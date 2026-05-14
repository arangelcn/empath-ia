"""User-related repository helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..infrastructure.db.mongo import MongoManager


class MongoUserRepository:
    """Small repository focused on user documents."""

    def __init__(self, mongo: MongoManager) -> None:
        self.mongo = mongo

    async def get_by_username(self, username: str) -> dict | None:
        """Fetch a user document by username."""
        users = self.mongo.get_collection("users")
        return await users.find_one({"username": username})

    async def save_user_profile(self, username: str, user_profile: dict[str, Any]) -> None:
        """Persist the normalized profile as the canonical user profile."""
        users = self.mongo.get_collection("users")
        now = datetime.now(UTC)
        await users.update_one(
            {"username": username},
            {
                "$set": {
                    "username": username,
                    "user_profile": user_profile,
                    "profile_completed": True,
                    "profile_completed_at": now,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )
