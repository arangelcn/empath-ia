"""Helpers for choosing human, non-generic previous-session subjects."""

import re
import unicodedata
from typing import Any


GENERIC_SESSION_SUBJECTS = {
    "apoio",
    "apoio emocional",
    "autoconhecimento",
    "bem estar",
    "bem-estar",
    "cadastro",
    "conversa",
    "conversa terapeutica",
    "conversa terapêutica",
    "crescimento pessoal",
    "desenvolvimento pessoal",
    "emocao",
    "emocao emocional",
    "emocoes",
    "emoções",
    "escuta ativa",
    "sentimentos",
    "sessao terapeutica",
    "sessão terapêutica",
    "terapia",
    "tema",
    "temas importantes",
    "temas identificados",
}


def normalize_subject_for_compare(value: Any) -> str:
    text = coerce_subject_text(value).lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def coerce_subject_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):
        for key in (
            "title",
            "subtitle",
            "theme",
            "name",
            "label",
            "text",
            "content",
            "value",
            "objective",
            "summary",
        ):
            text = coerce_subject_text(value.get(key))
            if text:
                return text
        return ""

    return str(value).strip()


def clean_subject(value: Any) -> str:
    text = coerce_subject_text(value)
    text = re.sub(r"^\s*sess[aã]o\s+\d+\s*[:\-]\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .,-:;")


def simplify_subject_for_prompt(value: Any) -> str:
    """
    Compacta um tema para soar mais natural em prompt de abertura.
    Mantém o sentido, mas remove rótulos e verbos de sessão que deixam o texto pesado.
    """
    text = clean_subject(value)
    if not text:
        return ""

    replacements = (
        r"^(explorando|navegando|aprofundando|entendendo|compreendendo|refletindo sobre|lidando com|falando sobre|trabalhando com)\s+",
        r"^(o|a|os|as)\s+campo\s+dos?\s+",
        r"^(a|o)\s+complexidade\s+dos?\s+",
        r"^(tema[s]?\s+como\s+)",
        r"^(quest[aã]o[es]?\s+de\s+)",
    )
    simplified = text
    for pattern in replacements:
        simplified = re.sub(pattern, "", simplified, flags=re.IGNORECASE)

    simplified = re.sub(r"\s+", " ", simplified).strip(" .,-:;")
    return simplified or text


def iter_subject_candidates(value: Any):
    if value is None:
        return

    if isinstance(value, (list, tuple, set)):
        for item in value:
            yield from iter_subject_candidates(item)
        return

    subject = clean_subject(value)
    if subject:
        yield subject


def is_meaningful_subject(value: Any) -> bool:
    subject = clean_subject(value)
    normalized = normalize_subject_for_compare(subject)

    if not normalized or len(normalized) < 4:
        return False

    if normalized in GENERIC_SESSION_SUBJECTS:
        return False

    generic_fragments = (
        "conversa terapeutica",
        "apoio emocional",
        "sessao terapeutica",
        "temas identificados",
        "temas importantes",
    )
    if any(fragment in normalized for fragment in generic_fragments):
        return False

    return True


def select_previous_session_subjects(
    previous_context: dict | None,
    previous_session_doc: dict | None = None,
    previous_conversation_doc: dict | None = None,
    limit: int = 2,
) -> list[str]:
    sources = [
        (previous_conversation_doc or {}).get("title"),
        (previous_conversation_doc or {}).get("subtitle"),
        (previous_session_doc or {}).get("title"),
        (previous_session_doc or {}).get("subtitle"),
        (previous_session_doc or {}).get("objective"),
        (previous_session_doc or {}).get("focus_areas"),
        (previous_context or {}).get("main_themes"),
        (previous_context or {}).get("next_session_focus"),
        (previous_context or {}).get("focus_areas"),
    ]

    subjects: list[str] = []
    seen: set[str] = set()
    for source in sources:
        for subject in iter_subject_candidates(source):
            if not is_meaningful_subject(subject):
                continue

            normalized = normalize_subject_for_compare(subject)
            if normalized in seen:
                continue

            subjects.append(subject)
            seen.add(normalized)
            if len(subjects) >= limit:
                return subjects

    return subjects


def meaningful_subjects_from_values(values: list[Any], limit: int = 2) -> list[str]:
    subjects: list[str] = []
    seen: set[str] = set()
    for value in values:
        for subject in iter_subject_candidates(value):
            if not is_meaningful_subject(subject):
                continue

            normalized = normalize_subject_for_compare(subject)
            if normalized in seen:
                continue

            subjects.append(subject)
            seen.add(normalized)
            if len(subjects) >= limit:
                return subjects

    return subjects


def join_subjects(subjects: list[str]) -> str:
    if len(subjects) <= 1:
        return subjects[0] if subjects else ""
    return f"{', '.join(subjects[:-1])} e {subjects[-1]}"
