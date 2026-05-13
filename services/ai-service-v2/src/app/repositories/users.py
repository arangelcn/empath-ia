"""User-related repository helpers."""

from __future__ import annotations

from ..infrastructure.db.mongo import MongoManager


class MongoUserRepository:
    """Small repository focused on user documents."""

    def __init__(self, mongo: MongoManager) -> None:
        self.mongo = mongo

    async def get_by_username(self, username: str) -> dict | None:
        """Fetch a user document by username."""
        users = self.mongo.get_collection("users")
        return await users.find_one({"username": username})
