from src.domain.conversation_identity import build_legacy_session_id, split_composite_session_id


def test_split_composite_session_id_preserves_usernames_with_underscores():
    username, session_id = split_composite_session_id("toni_silva_session-12")

    assert username == "toni_silva"
    assert session_id == "session-12"


def test_split_composite_session_id_returns_original_when_not_composite():
    username, session_id = split_composite_session_id("chat_abc123")

    assert username is None
    assert session_id == "chat_abc123"


def test_build_legacy_session_id_uses_existing_compatibility_format():
    assert build_legacy_session_id("toni", "session-2") == "toni_session-2"
    assert build_legacy_session_id(None, "session-2") == "session-2"
    assert build_legacy_session_id("toni", None) == "toni"
    assert build_legacy_session_id(None, None) == "default"
