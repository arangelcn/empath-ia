"""
Pure helpers for chat/conversation identity compatibility.
"""

from typing import Optional

COMPOSITE_SESSION_SEPARATOR = "_session-"


def split_composite_session_id(session_id: str) -> tuple[Optional[str], str]:
    """
    Split '{username}_session-N' while allowing underscores in usernames.
    """
    if not session_id:
        return None, session_id

    separator_index = session_id.rfind(COMPOSITE_SESSION_SEPARATOR)
    if separator_index == -1:
        return None, session_id

    return session_id[:separator_index], session_id[separator_index + 1:]


def build_legacy_session_id(
    username: Optional[str],
    therapeutic_session_id: Optional[str],
) -> str:
    """
    Build the legacy Mongo key used by older conversation documents.
    """
    if username and therapeutic_session_id:
        return f"{username}_{therapeutic_session_id}"
    return therapeutic_session_id or username or "default"
