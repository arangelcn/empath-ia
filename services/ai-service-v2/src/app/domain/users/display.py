"""Helpers for human-facing user names."""

import re
from typing import Any


TECHNICAL_PREFIXES = ("google_", "chat_", "session_")


def _clean_token(token: str) -> str:
    token = token.strip(" \t\n\r,.;:!?()[]{}<>\"'")
    if not token:
        return ""
    if token.islower():
        return token.capitalize()
    return token


def first_name_from_text(value: str | None) -> str | None:
    """Return a safe first name, avoiding emails and technical ids."""
    if not value:
        return None

    text = str(value).strip()
    if not text:
        return None

    lower = text.lower()
    if lower.startswith(TECHNICAL_PREFIXES) or "_session-" in lower:
        return None

    if "@" in text:
        local_part = text.split("@", 1)[0]
        local_part = re.sub(r"[._-]+", " ", local_part).strip()
        token = _clean_token(local_part.split()[0] if local_part else "")
        return token or None

    token = _clean_token(text.split()[0])
    if not token or any(char.isdigit() for char in token):
        return None
    return token


def first_name_from_user(user: dict[str, Any] | None, fallback: str | None = None) -> str | None:
    """Resolve the preferred first name from a user document."""
    preferences = (user or {}).get("preferences", {})
    candidates = [
        (user or {}).get("display_name"),
        preferences.get("display_name"),
        (user or {}).get("full_name"),
        preferences.get("full_name"),
        (user or {}).get("name"),
        fallback,
        (user or {}).get("email"),
        (user or {}).get("username"),
    ]

    for candidate in candidates:
        first_name = first_name_from_text(candidate)
        if first_name:
            return first_name
    return None
