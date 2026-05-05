"""Tests for SessionContextService pure logic (no external I/O)."""
from datetime import datetime, timedelta

from src.services.session_context_service import SessionContextService


def make_service():
    return SessionContextService(
        ai_service_url="http://ai:8001",
        conversation_repo=None,
        resolve_ref=None,
        extract_username=None,
        split_session_id=None,
        next_session_service=None,
    )


def test_detect_conversation_end_on_farewell():
    svc = make_service()
    assert svc.detect_conversation_end("tchau") is True
    assert svc.detect_conversation_end("Até logo, obrigado!") is True
    assert svc.detect_conversation_end("me ajudou muito") is True


def test_detect_conversation_end_returns_false_for_regular_message():
    svc = make_service()
    assert svc.detect_conversation_end("quero falar sobre ansiedade") is False
    assert svc.detect_conversation_end("como você está?") is False
    assert svc.detect_conversation_end("") is False


def test_estimate_conversation_duration_returns_one_for_single_message():
    svc = make_service()
    messages = [{"content": "oi", "created_at": datetime.utcnow()}]
    assert svc._estimate_conversation_duration(messages) == 1


def test_estimate_conversation_duration_uses_timestamp_delta():
    svc = make_service()
    start = datetime(2025, 1, 1, 10, 0, 0)
    end = start + timedelta(minutes=15)
    messages = [
        {"content": "oi", "created_at": start},
        {"content": "como vai?", "created_at": end},
    ]
    result = svc._estimate_conversation_duration(messages)
    assert result == 15


def test_analyze_basic_emotions_detects_tristeza():
    svc = make_service()
    messages = [{"content": "estou muito triste hoje", "type": "user"}]
    result = svc._analyze_basic_emotions(messages)
    assert result["dominant_emotion"] == "tristeza"


def test_analyze_basic_emotions_returns_neutro_when_no_keywords():
    svc = make_service()
    messages = [{"content": "hoje foi um dia comum", "type": "user"}]
    result = svc._analyze_basic_emotions(messages)
    assert result["dominant_emotion"] == "neutro"


def test_identify_basic_themes_detects_trabalho():
    svc = make_service()
    messages = [{"content": "meu trabalho está me deixando estressado", "type": "user"}]
    themes = svc._identify_basic_themes(messages)
    assert "trabalho" in themes


def test_identify_basic_themes_returns_at_most_five():
    svc = make_service()
    messages = [
        {
            "content": "trabalho família namorado saúde escola autoestima futuro",
            "type": "user",
        }
    ]
    themes = svc._identify_basic_themes(messages)
    assert len(themes) <= 5


def test_format_conversation_for_analysis():
    svc = make_service()
    messages = [
        {"type": "user", "content": "Estou ansioso."},
        {"type": "ai", "content": "Entendo, me conta mais."},
    ]
    text = svc._format_conversation_for_analysis(messages)
    assert "Usuário: Estou ansioso." in text
    assert "Terapeuta: Entendo, me conta mais." in text


def test_validate_ai_context_rejects_generic_themes():
    svc = make_service()
    context = {
        "summary": "Resumo gerado pela IA",
        "main_themes": ["conversa terapêutica", "apoio emocional"],
        "emotional_state": {"dominant_emotion": "neutro"},
        "key_insights": ["Insight específico"],
    }

    try:
        svc._validate_ai_context_data(context)
    except ValueError as exc:
        assert "main_themes" in str(exc)
    else:
        raise AssertionError("generic themes should be rejected")


def test_validate_ai_context_accepts_meaningful_theme():
    svc = make_service()
    context = {
        "summary": "Resumo gerado pela IA",
        "main_themes": ["ansiedade no trabalho"],
        "emotional_state": {"dominant_emotion": "ansiedade"},
        "key_insights": ["Usuário relacionou ansiedade a cobranças profissionais"],
    }

    svc._validate_ai_context_data(context)
