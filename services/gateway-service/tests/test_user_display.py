from src.domain.user_display import first_name_from_text, first_name_from_user


def test_first_name_from_user_prefers_display_name():
    user = {
        "username": "toni@example.com",
        "email": "toni@example.com",
        "name": "Google Name",
        "preferences": {
            "display_name": "Toni Roberto",
        },
    }

    assert first_name_from_user(user) == "Toni"


def test_first_name_from_user_uses_email_local_part_only_as_last_resort():
    user = {
        "username": "toni.rc.neto@example.com",
        "email": "toni.rc.neto@example.com",
        "preferences": {},
    }

    assert first_name_from_user(user) == "Toni"


def test_first_name_from_text_rejects_technical_ids():
    assert first_name_from_text("google_123456789") is None
    assert first_name_from_text("chat_abc") is None
    assert first_name_from_text("toni_session-2") is None
