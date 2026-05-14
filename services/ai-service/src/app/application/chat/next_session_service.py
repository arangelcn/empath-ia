"""Automatic next-session generation after a therapeutic session is finalized."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

from ...repositories.sessions import MongoSessionRepository
from .user_profile_service import UserProfileService


logger = logging.getLogger(__name__)


class NextSessionService:
    """Create or unlock the next user therapeutic session."""

    def __init__(
        self,
        session_repository: MongoSessionRepository,
        user_profile_service: UserProfileService,
    ) -> None:
        self.session_repository = session_repository
        self.user_profile_service = user_profile_service

    async def create_next_session_automatically(
        self,
        current_session_id: str,
        session_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Create the next user session from the current normalized context."""
        username = self._extract_username(current_session_id)
        if not username:
            return {"success": False, "error": "Username nao encontrado"}

        current_session_number = self.extract_session_number(current_session_id)
        next_session_id = f"session-{current_session_number + 1}"
        existing_session = await self.session_repository.get_user_session(username, next_session_id)
        if existing_session:
            if existing_session.get("status") == "locked":
                await self.session_repository.unlock_user_session(username, next_session_id)
            return {
                "success": True,
                "created": False,
                "session_id": next_session_id,
                "title": existing_session.get("title", f"Sessao {current_session_number + 1}"),
            }

        user_profile = await self.user_profile_service.get_user_profile(username)
        next_session = self.build_next_session(user_profile, session_context, current_session_id)
        if not next_session:
            return {"success": False, "error": "Falha ao gerar proxima sessao"}

        next_session["session_id"] = next_session_id
        stored = await self.session_repository.create_user_session(username, next_session)
        return {
            "success": True,
            "created": True,
            "session_id": next_session_id,
            "title": stored.get("title", next_session.get("title", f"Sessao {current_session_number + 1}")),
            "generation_method": stored.get("generation_method", next_session.get("generation_method")),
        }

    def build_next_session(
        self,
        user_profile: dict[str, Any],
        session_context: dict[str, Any],
        current_session_id: str,
    ) -> dict[str, Any] | None:
        """Build a deterministic next-session payload from context and profile."""
        session_number = self.extract_session_number(current_session_id)
        next_session_number = session_number + 1
        main_themes = self._meaningful_subjects(session_context.get("main_themes", []), limit=3)
        if not main_themes:
            main_themes = self._meaningful_subjects(
                (session_context.get("next_session_seed") or {}).get("focus_areas", []),
                limit=3,
            )
        therapeutic_info = user_profile.get("therapeutic_info") or {}
        user_objectives = list(therapeutic_info.get("objetivos_identificados") or [])

        combined_themes: list[str] = []
        for theme in [*main_themes, *user_objectives[:2]]:
            normalized = str(theme).strip()
            if normalized and normalized not in combined_themes:
                combined_themes.append(normalized)

        if not combined_themes:
            combined_themes = ["autoconhecimento", "processo terapeutico"]

        if next_session_number == 2:
            session_title = f"Sessao {next_session_number}: Aprofundando nosso conhecimento"
            session_subtitle = "Construindo sobre nossa primeira conversa"
        else:
            session_title = f"Sessao {next_session_number}: Continuando sua jornada"
            session_subtitle = "Aprofundando temas importantes para voce"

        objective = f"Explorar e aprofundar os temas: {', '.join(combined_themes[:2])}"
        subjects_text = self._join_subjects(combined_themes[:2])
        if next_session_number == 2:
            initial_prompt = (
                "Ola! Como voce esta se sentindo desde nossa primeira conversa? "
                f"Na nossa sessao anterior, apareceram temas como {subjects_text}. "
                "Gostaria de continuar por ai ou ha algo mais presente para voce hoje?"
            )
        else:
            initial_prompt = (
                "Ola! Como voce esta se sentindo desde nossa ultima conversa? "
                f"Na sessao anterior, apareceram temas como {subjects_text}. "
                "Gostaria de continuar por ai ou trazer algo novo hoje?"
            )

        return {
            "session_id": f"session-{next_session_number}",
            "title": session_title,
            "subtitle": session_subtitle,
            "objective": objective,
            "initial_prompt": initial_prompt,
            "focus_areas": combined_themes[:3],
            "therapeutic_approach": "Abordagem centrada na pessoa (Carl Rogers)",
            "expected_outcomes": [
                "Maior clareza sobre os temas identificados",
                "Desenvolvimento de insights pessoais",
                "Fortalecimento do processo terapeutico",
            ],
            "session_type": "continuacao",
            "estimated_duration": "45-60 minutos",
            "preparation_notes": "Revisar contexto da sessao anterior e temas identificados",
            "connection_to_previous": "Continuacao dos temas e insights da sessao anterior",
            "personalization_factors": ["historico do usuario", "temas identificados", "progresso terapeutico"],
            "generated_at": datetime.now(UTC).isoformat(),
            "based_on_session": current_session_id,
            "generation_method": "context_based_template",
            "personalized": True,
            "is_active": True,
        }

    @staticmethod
    def extract_session_number(session_id: str) -> int:
        """Extract the numeric portion from a composite or plain session id."""
        match = re.search(r"session-(\d+)", session_id)
        if match:
            return int(match.group(1))
        return 1

    @staticmethod
    def _extract_username(session_id: str) -> str | None:
        separator = "_session-"
        separator_index = session_id.rfind(separator)
        if separator_index == -1:
            return None
        return session_id[:separator_index]

    @staticmethod
    def _join_subjects(subjects: list[str]) -> str:
        if not subjects:
            return "temas importantes para voce"
        if len(subjects) == 1:
            return subjects[0]
        if len(subjects) == 2:
            return f"{subjects[0]} e {subjects[1]}"
        return f"{', '.join(subjects[:-1])} e {subjects[-1]}"

    @staticmethod
    def _meaningful_subjects(values: Any, limit: int = 3) -> list[str]:
        if not isinstance(values, list):
            values = [values]
        subjects: list[str] = []
        for value in values:
            normalized = str(value or "").strip()
            if not normalized:
                continue
            if normalized.lower() in {"none", "n/a", "na", "null"}:
                continue
            if normalized not in subjects:
                subjects.append(normalized)
            if len(subjects) >= limit:
                break
        return subjects
