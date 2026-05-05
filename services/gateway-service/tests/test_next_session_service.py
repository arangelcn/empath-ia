from src.services.next_session_service import NextSessionService
from src.services.user_profile_service import UserProfileService


def test_build_next_session_combines_context_and_profile_objectives():
    service = NextSessionService(
        extract_username_from_session_id=lambda session_id: "toni",
        user_profile_service=UserProfileService(),
    )

    next_session = service.build_next_session(
        {
            "therapeutic_info": {
                "objetivos_identificados": ["Fortalecer autoestima"],
            }
        },
        {"main_themes": ["ansiedade"]},
        "toni_session-1",
    )

    assert next_session["session_id"] == "session-2"
    assert next_session["title"] == "Sessão 2: Aprofundando nosso conhecimento"
    assert "ansiedade" in next_session["objective"]
    assert "Fortalecer autoestima" in next_session["objective"]
    assert next_session["status"] if "status" in next_session else True


def test_extract_session_number_defaults_to_one_for_invalid_ids():
    service = NextSessionService(
        extract_username_from_session_id=lambda session_id: "toni",
        user_profile_service=UserProfileService(),
    )

    assert service.extract_session_number("toni_session-12") == 12
    assert service.extract_session_number("chat_abc") == 1
