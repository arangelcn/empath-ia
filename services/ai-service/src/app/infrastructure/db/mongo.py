"""MongoDB connection helpers for ai-service."""

from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


logger = logging.getLogger(__name__)


class MongoManager:
    """Manage the MongoDB connection used by the unified service."""

    def __init__(self, mongodb_url: str, database_name: str) -> None:
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        self.client: AsyncIOMotorClient | None = None
        self.database: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        """Create the MongoDB client and database reference."""
        self.client = AsyncIOMotorClient(self.mongodb_url)
        self.database = self.client[self.database_name]
        await self.client.admin.command("ping")
        logger.info("MongoDB conectado para ai-service")

    async def close(self) -> None:
        """Close the MongoDB client."""
        if self.client is not None:
            self.client.close()
            logger.info("MongoDB fechado para ai-service")

    def get_collection(self, collection_name: str):
        """Return a collection handle from the active database."""
        if self.database is None:
            raise RuntimeError("MongoDB nao foi inicializado no ai-service")
        return self.database[collection_name]

    async def create_indexes(self) -> None:
        """Create the minimal indexes required by migrated chat flows."""
        conversations = self.get_collection("conversations")
        messages = self.get_collection("messages")
        users = self.get_collection("users")
        user_sessions = self.get_collection("user_therapeutic_sessions")
        session_contexts = self.get_collection("session_contexts")

        await conversations.create_index("chat_id", unique=True, sparse=True)
        await conversations.create_index("session_id")
        await conversations.create_index("legacy_session_id")
        await conversations.create_index("therapeutic_session_id")
        await conversations.create_index("username")
        await conversations.create_index("updated_at")
        await conversations.create_index(
            [("username", 1), ("therapeutic_session_id", 1)],
            unique=True,
            partialFilterExpression={
                "username": {"$type": "string"},
                "therapeutic_session_id": {"$type": "string"},
            },
        )

        await messages.create_index("chat_id")
        await messages.create_index("session_id")
        await messages.create_index("username")
        await messages.create_index([("session_id", 1), ("created_at", 1)])
        await messages.create_index([("session_id", 1), ("username", 1)])

        await users.create_index("username", unique=True)
        await user_sessions.create_index([("username", 1), ("session_id", 1)], unique=True)
        await session_contexts.create_index("session_id", unique=True)
        await session_contexts.create_index("username")
