from src.domain.session_subjects import select_previous_session_subjects


def test_previous_session_subjects_prefer_saved_title_and_subtitle():
    subjects = select_previous_session_subjects(
        previous_context={
            "main_themes": [
                "conversa terapêutica",
                "apoio emocional",
                "ansiedade no trabalho",
            ]
        },
        previous_conversation_doc={
            "title": "Pressão no trabalho",
            "subtitle": "Limites e energia emocional",
        },
        previous_session_doc={
            "title": "Sessão 2: Cansaço no trabalho",
            "subtitle": "Reconhecendo limites",
        },
    )

    assert subjects == ["Pressão no trabalho", "Limites e energia emocional"]


def test_previous_session_subjects_remove_session_prefix_and_generic_context():
    subjects = select_previous_session_subjects(
        previous_context={"main_themes": ["conversa terapêutica", "apoio emocional"]},
        previous_conversation_doc={"title": "Sessão 3: Medo de decepcionar"},
    )

    assert subjects == ["Medo de decepcionar"]


def test_previous_session_subjects_empty_when_only_generic_values():
    subjects = select_previous_session_subjects(
        previous_context={"main_themes": ["conversa terapêutica", "apoio emocional"]},
        previous_session_doc={"title": "Sessão terapêutica", "subtitle": "Temas importantes"},
    )

    assert subjects == []
