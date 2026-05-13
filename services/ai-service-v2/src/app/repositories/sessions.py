"""Session repository contract."""

from typing import Protocol

from ..domain.sessions.models import SessionRef


class SessionRepository(Protocol):
    """Persistence contract for therapeutic sessions."""

    async def get(self, session_id: str) -> SessionRef | None:
        """Fetch a therapeutic session by id."""
