"""
Automatic next-session generation after a therapeutic session is finalized.
"""

import logging
import re
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from ..domain.session_subjects import join_subjects, meaningful_subjects_from_values
from ..models.database import get_collection
from .user_profile_service import UserProfileService
from .user_therapeutic_session_service import UserTherapeuticSessionService

logger = logging.getLogger(__name__)

ExtractUsername = Callable[[str], Optional[str]]


class NextSessionService:
    """Create or unlock the next user therapeutic session."""

    def __init__(
        self,
        *,
        extract_username_from_session_id: ExtractUsername,
        user_profile_service: UserProfileService,
    ):
        self.extract_username_from_session_id = extract_username_from_session_id
        self.user_profile_service = user_profile_service

    async def create_next_session_automatically(
        self,
        current_session_id: str,
        session_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Criar APENAS a próxima sessão automaticamente usando dados do contexto atual.
        """
        try:
            logger.info("🚀 CRIANDO PRÓXIMA SESSÃO AUTOMATICAMENTE para %s", current_session_id)

            username = self.extract_username_from_session_id(current_session_id)
            if not username:
                logger.error("❌ Não foi possível extrair username de %s", current_session_id)
                return {"success": False, "error": "Username não encontrado"}

            current_session_number = self.extract_session_number(current_session_id)
            next_session_number = current_session_number + 1
            next_session_id = f"session-{next_session_number}"

            logger.info("📋 Criando session-%s após session-%s", next_session_number, current_session_number)

            user_session_service = UserTherapeuticSessionService()
            existing_session = await user_session_service.get_user_session(username, next_session_id)
            if existing_session:
                logger.info("ℹ️ Session-%s já existe para %s", next_session_number, username)

                if existing_session.get("status") == "locked":
                    unlock_success = await user_session_service.unlock_session(username, next_session_id)
                    if unlock_success:
                        logger.info("🔓 Session-%s desbloqueada para %s", next_session_number, username)

                return {
                    "success": True,
                    "created": False,
                    "session_id": next_session_id,
                    "title": existing_session.get("title", f"Sessão {next_session_number}"),
                    "message": "Sessão já existe e foi desbloqueada"
                }

            user_profile = await self.user_profile_service.get_user_profile(username)
            next_session = self.build_next_session(user_profile, session_context, current_session_id)

            if next_session:
                next_session["session_id"] = next_session_id
                creation_result = await self.create_user_session_in_db(username, next_session)

                if creation_result:
                    logger.info("✅ Session-%s criada automaticamente para %s", next_session_number, username)
                    return {
                        "success": True,
                        "created": True,
                        "session_id": next_session_id,
                        "title": next_session.get("title", f"Sessão {next_session_number}"),
                        "generation_method": next_session.get("generation_method", "ai_service")
                    }

                logger.error("❌ Falha ao criar session-%s no banco", next_session_number)
                return {"success": False, "error": "Falha ao criar sessão no banco"}

            logger.warning("⚠️ Falha ao gerar session-%s via AI Service", next_session_number)
            return {"success": False, "error": "Falha ao gerar próxima sessão"}

        except Exception as e:
            logger.error("❌ Erro ao criar próxima sessão automaticamente: %s", e)
            return {"success": False, "error": str(e)}

    def build_next_session(
        self,
        user_profile: Dict[str, Any],
        session_context: Dict[str, Any],
        current_session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Build next-session payload from context and user profile.
        """
        session_number = self.extract_session_number(current_session_id)
        next_session_number = session_number + 1
        next_session_id = f"session-{next_session_number}"
        main_themes = meaningful_subjects_from_values([session_context.get("main_themes", [])], limit=3)
        if not main_themes:
            logger.error(
                "❌ Contexto sem temas reais; próxima sessão não será criada para %s",
                current_session_id,
            )
            return None

        user_objectives = []
        if user_profile and user_profile.get("therapeutic_info"):
            therapeutic_info = user_profile["therapeutic_info"]
            user_objectives = therapeutic_info.get("objetivos_identificados", [])

        combined_themes = []
        seen_themes = set()
        for theme in main_themes + user_objectives[:2]:
            if theme in seen_themes:
                continue
            combined_themes.append(theme)
            seen_themes.add(theme)

        if next_session_number == 2:
            session_title = f"Sessão {next_session_number}: Aprofundando nosso conhecimento"
            session_subtitle = "Construindo sobre nossa primeira conversa"
        else:
            session_title = f"Sessão {next_session_number}: Continuando sua jornada"
            session_subtitle = "Aprofundando temas importantes para você"

        objective = f"Explorar e aprofundar os temas: {', '.join(combined_themes[:2])}"

        if main_themes and next_session_number == 2:
            subjects_text = join_subjects(main_themes[:2])
            initial_prompt = f"Olá! Como você está se sentindo desde nossa primeira conversa? Na nossa sessão anterior, apareceram temas como {subjects_text}. Gostaria de continuar por aí ou há algo mais presente para você hoje?"
        elif main_themes:
            subjects_text = join_subjects(main_themes[:2])
            initial_prompt = f"Olá! Como você está se sentindo desde nossa última conversa? Na sessão anterior, apareceram temas como {subjects_text}. Gostaria de continuar por aí ou trazer algo novo hoje?"
        else:
            initial_prompt = f"Olá! Como você está se sentindo hoje? O que gostaria de explorar em nossa sessão {next_session_number}?"

        return {
            "session_id": next_session_id,
            "title": session_title,
            "subtitle": session_subtitle,
            "objective": objective,
            "initial_prompt": initial_prompt,
            "focus_areas": combined_themes[:3],
            "therapeutic_approach": "Abordagem centrada na pessoa (Carl Rogers)",
            "expected_outcomes": [
                "Maior clareza sobre os temas identificados",
                "Desenvolvimento de insights pessoais",
                "Fortalecimento do processo terapêutico"
            ],
            "session_type": "continuação",
            "estimated_duration": "45-60 minutos",
            "preparation_notes": "Revisar contexto da sessão anterior e temas identificados",
            "connection_to_previous": "Continuação dos temas e insights da sessão anterior",
            "personalization_factors": ["histórico do usuário", "temas identificados", "progresso terapêutico"],
            "generated_at": datetime.utcnow().isoformat(),
            "based_on_session": current_session_id,
            "generation_method": "context_based_template",
            "personalized": True,
            "is_active": True
        }

    def extract_session_number(self, session_id: str) -> int:
        """
        Extrair número da sessão do session_id.
        """
        try:
            match = re.search(r'session-(\d+)', session_id)
            if match:
                return int(match.group(1))
            return 1
        except Exception:
            return 1

    async def create_user_session_in_db(self, username: str, session_data: Dict[str, Any]) -> bool:
        """
        Criar sessão do usuário no banco de dados.
        """
        try:
            session_id = session_data.get("session_id")
            if not session_id:
                logger.error("❌ session_id não encontrado nos dados da sessão")
                return False

            user_sessions = get_collection("user_therapeutic_sessions")
            session_document = {
                "username": username,
                "session_id": session_id,
                "title": session_data.get("title", "Sessão Terapêutica"),
                "subtitle": session_data.get("subtitle", ""),
                "objective": session_data.get("objective", ""),
                "initial_prompt": session_data.get("initial_prompt", ""),
                "focus_areas": session_data.get("focus_areas", []),
                "therapeutic_approach": session_data.get("therapeutic_approach", ""),
                "expected_outcomes": session_data.get("expected_outcomes", []),
                "session_type": session_data.get("session_type", "individual"),
                "estimated_duration": session_data.get("estimated_duration", "45-60 minutos"),
                "preparation_notes": session_data.get("preparation_notes", ""),
                "connection_to_previous": session_data.get("connection_to_previous", ""),
                "personalization_factors": session_data.get("personalization_factors", []),
                "generated_at": session_data.get("generated_at"),
                "based_on_session": session_data.get("based_on_session"),
                "generation_method": session_data.get("generation_method", "ai_service"),
                "personalized": session_data.get("personalized", True),
                "is_active": session_data.get("is_active", True),
                "status": "unlocked",
                "progress": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await user_sessions.insert_one(session_document)
            if result.inserted_id:
                logger.info("✅ Sessão criada e desbloqueada no banco: %s para %s", session_id, username)
                return True

            logger.error("❌ Falha ao inserir sessão no banco: %s", session_id)
            return False

        except Exception as e:
            logger.error("❌ Erro ao criar sessão no banco: %s", e)
            return False
