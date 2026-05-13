"""User domain models."""

from dataclasses import dataclass


@dataclass(slots=True)
class UserIdentity:
    """Minimal user identity for the unified boundary."""

    username: str
    preferred_name: str | None = None
