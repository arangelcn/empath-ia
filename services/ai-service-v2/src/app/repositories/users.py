"""User repository contract."""

from typing import Protocol

from ..domain.users.models import UserIdentity


class UserRepository(Protocol):
    """Persistence contract for user identity data."""

    async def get_by_username(self, username: str) -> UserIdentity | None:
        """Fetch a user identity by username."""
