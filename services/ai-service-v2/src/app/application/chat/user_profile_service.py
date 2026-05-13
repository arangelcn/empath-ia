"""User profile normalization and persistence for migrated chat flows."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

from ...domain.users.display import first_name_from_user
from ...repositories.conversations import MongoConversationRepository
from ...repositories.users import MongoUserRepository


logger = logging.getLogger(__name__)


class UserProfileService:
    """Build and persist the canonical user profile used by the unified service."""

    def __init__(
        self,
        conversation_repository: MongoConversationRepository,
        user_repository: MongoUserRepository,
    ) -> None:
        self.conversation_repository = conversation_repository
        self.user_repository = user_repository

    async def get_user_profile(self, username: str) -> dict[str, Any]:
        """Fetch and normalize a user profile from the existing Mongo collections."""
        user = await self.user_repository.get_by_username(username)
        user_profile: dict[str, Any] = {}
        preferences = (user or {}).get("preferences", {})
        preferred_name = first_name_from_user(user, username)
        display_name = (
            (user or {}).get("display_name")
            or preferences.get("display_name")
            or (user or {}).get("full_name")
            or preferences.get("full_name")
        )

        if user and user.get("user_profile"):
            user_profile = dict(user["user_profile"])

        user_profile["username"] = username
        user_profile["preferences"] = preferences
        if preferred_name:
            user_profile["preferred_name"] = preferred_name
        if display_name:
            user_profile["display_name"] = display_name
            user_profile["full_name"] = (
                (user or {}).get("full_name")
                or preferences.get("full_name")
                or display_name
            )

        session_1_context = await self.conversation_repository.get_by_session_id(f"{username}_session-1")
        if session_1_context and session_1_context.get("registration_data"):
            registration_data = session_1_context["registration_data"]
            user_profile["registration_data"] = registration_data
            if not user_profile.get("profile_summary"):
                summary_parts = []
                if registration_data.get("idade"):
                    summary_parts.append(f"{registration_data['idade']} anos")
                if registration_data.get("ocupacao"):
                    summary_parts.append(str(registration_data["ocupacao"]))
                if registration_data.get("localizacao"):
                    summary_parts.append(f"de {registration_data['localizacao']}")
                if summary_parts:
                    user_profile["profile_summary"] = f"Usuario {username}: {', '.join(summary_parts)}"

        if user_profile:
            return user_profile

        logger.warning("Perfil minimo carregado para %s", username)
        return {
            "username": username,
            "preferences": preferences,
            "preferred_name": preferred_name,
            "display_name": display_name,
            "profile_summary": f"Usuario {username} - dados limitados",
            "registration_data": {},
            "personal_info": {},
            "social_info": {},
            "therapeutic_info": {},
        }

    async def save_user_profile(self, username: str, registration_data: dict[str, Any]) -> dict[str, Any]:
        """Persist a normalized user profile after session-1 completion."""
        user_profile = self.create_standardized_profile(username, registration_data)
        await self.user_repository.save_user_profile(username, user_profile)
        return user_profile

    def create_standardized_profile(
        self,
        username: str,
        registration_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a structured profile document from registration answers."""
        personal_info = {
            "idade": self._normalize_age(registration_data.get("idade", "")),
            "genero": self._normalize_gender(registration_data.get("genero", "")),
            "cor_raca": self._normalize_race(registration_data.get("cor_raca", "")),
            "localizacao": self._normalize_location(registration_data.get("localizacao", "")),
        }
        social_info = {
            "situacao_moradia": self._normalize_text(registration_data.get("situacao_moradia", "")),
            "relacao_familia": self._normalize_text(registration_data.get("relacao_familia", "")),
            "ocupacao": self._normalize_text(registration_data.get("ocupacao", "")),
        }
        therapeutic_info = {
            "motivacao_terapia": self._normalize_text(registration_data.get("motivacao_terapia", "")),
            "informacoes_adicionais": self._normalize_text(registration_data.get("informacoes_adicionais", "")),
            "objetivos_identificados": self._extract_objectives(registration_data),
        }

        return {
            "username": username,
            "personal_info": personal_info,
            "social_info": social_info,
            "therapeutic_info": therapeutic_info,
            "profile_summary": self._generate_profile_summary(personal_info, social_info, therapeutic_info),
            "keywords": self._extract_keywords(registration_data),
            "risk_factors": self._identify_risk_factors(registration_data),
            "strengths": self._identify_strengths(registration_data),
            "registration_data": dict(registration_data),
            "updated_at": datetime.now(UTC).isoformat(),
            "data_source": "session-1_registration",
        }

    @staticmethod
    def _normalize_text(value: Any) -> str:
        return str(value or "").strip()

    def _normalize_age(self, age_input: Any) -> dict[str, Any]:
        age_text = self._normalize_text(age_input).lower()
        age_numbers = re.findall(r"\d+", age_text)
        if age_numbers:
            age = int(age_numbers[0])
            if age < 18:
                category = "menor_idade"
            elif age < 25:
                category = "jovem_adulto"
            elif age < 35:
                category = "adulto_jovem"
            elif age < 50:
                category = "adulto"
            elif age < 65:
                category = "adulto_maduro"
            else:
                category = "idoso"
            return {"valor": age, "categoria": category, "original": self._normalize_text(age_input)}
        return {"valor": None, "categoria": "nao_informado", "original": self._normalize_text(age_input)}

    def _normalize_gender(self, gender_input: Any) -> dict[str, Any]:
        gender_text = self._normalize_text(gender_input).lower()
        gender_mapping = {
            "feminino": "feminino",
            "mulher": "feminino",
            "f": "feminino",
            "masculino": "masculino",
            "homem": "masculino",
            "m": "masculino",
            "nao-binario": "nao_binario",
            "nao binario": "nao_binario",
            "não-binário": "nao_binario",
            "não binário": "nao_binario",
            "nb": "nao_binario",
            "trans": "trans",
            "transgender": "trans",
            "prefiro nao responder": "prefere_nao_responder",
            "prefiro não responder": "prefere_nao_responder",
            "nao responder": "prefere_nao_responder",
            "não responder": "prefere_nao_responder",
        }
        return {"categoria": gender_mapping.get(gender_text, "outros"), "original": self._normalize_text(gender_input)}

    def _normalize_race(self, race_input: Any) -> dict[str, Any]:
        race_text = self._normalize_text(race_input).lower()
        race_mapping = {
            "branco": "branco",
            "branca": "branco",
            "negro": "negro",
            "negra": "negro",
            "preto": "negro",
            "preta": "negro",
            "pardo": "pardo",
            "parda": "pardo",
            "amarelo": "amarelo",
            "amarela": "amarelo",
            "asiatico": "amarelo",
            "asiatica": "amarelo",
            "asiático": "amarelo",
            "asiática": "amarelo",
            "indigena": "indigena",
            "indígena": "indigena",
            "indio": "indigena",
            "india": "indigena",
            "prefiro nao responder": "prefere_nao_responder",
            "prefiro não responder": "prefere_nao_responder",
        }
        return {"categoria": race_mapping.get(race_text, "outros"), "original": self._normalize_text(race_input)}

    def _normalize_location(self, location_input: Any) -> dict[str, Any]:
        location_text = self._normalize_text(location_input)
        parts = [part.strip() for part in re.split(r"[,/-]", location_text) if part.strip()]
        return {
            "cidade_estado": location_text,
            "cidade": parts[0] if parts else "",
            "estado": parts[1] if len(parts) > 1 else "",
        }

    def _extract_objectives(self, registration_data: dict[str, Any]) -> list[str]:
        motivation = self._normalize_text(registration_data.get("motivacao_terapia", "")).lower()
        mapping = {
            "ansiedade": "lidar com ansiedade",
            "estresse": "reduzir estresse",
            "depress": "entender humor e tristeza",
            "relacion": "melhorar relacionamentos",
            "famil": "melhorar relacoes familiares",
            "autoconhecimento": "aprofundar autoconhecimento",
            "autoestima": "fortalecer autoestima",
            "trabalho": "equilibrar vida profissional",
        }
        objectives = [label for keyword, label in mapping.items() if keyword in motivation]
        if not objectives and motivation:
            objectives.append("explorar o que motivou a busca por apoio")
        return objectives

    def _extract_keywords(self, registration_data: dict[str, Any]) -> list[str]:
        values = [
            registration_data.get("genero", ""),
            registration_data.get("situacao_moradia", ""),
            registration_data.get("relacao_familia", ""),
            registration_data.get("ocupacao", ""),
            registration_data.get("motivacao_terapia", ""),
            registration_data.get("informacoes_adicionais", ""),
        ]
        keywords: list[str] = []
        for value in values:
            for token in re.findall(r"[a-zA-ZÀ-ÿ0-9_-]{4,}", self._normalize_text(value).lower()):
                if token not in keywords:
                    keywords.append(token)
        return keywords[:20]

    def _identify_risk_factors(self, registration_data: dict[str, Any]) -> list[str]:
        combined = " ".join(
            self._normalize_text(registration_data.get(field, "")).lower()
            for field in ("relacao_familia", "motivacao_terapia", "informacoes_adicionais")
        )
        markers = {
            "violencia": "historico de violencia",
            "abuso": "relato de abuso",
            "isolad": "isolamento social",
            "crise": "vivencia de crise recente",
            "luto": "processo de luto",
        }
        return [label for keyword, label in markers.items() if keyword in combined]

    def _identify_strengths(self, registration_data: dict[str, Any]) -> list[str]:
        combined = " ".join(
            self._normalize_text(registration_data.get(field, "")).lower()
            for field in (
                "situacao_moradia",
                "relacao_familia",
                "ocupacao",
                "motivacao_terapia",
                "informacoes_adicionais",
            )
        )
        markers = {
            "apoio": "rede de apoio identificada",
            "famil": "vinculos familiares relevantes",
            "trabalho": "rotina ocupacional estruturada",
            "estudo": "engajamento com estudos",
            "quero": "motivacao para mudanca",
        }
        return [label for keyword, label in markers.items() if keyword in combined]

    def _generate_profile_summary(
        self,
        personal_info: dict[str, Any],
        social_info: dict[str, Any],
        therapeutic_info: dict[str, Any],
    ) -> str:
        parts: list[str] = []
        age_value = (personal_info.get("idade") or {}).get("valor")
        if age_value:
            parts.append(f"{age_value} anos")
        occupation = social_info.get("ocupacao")
        if occupation:
            parts.append(occupation)
        location = (personal_info.get("localizacao") or {}).get("cidade_estado")
        if location:
            parts.append(f"de {location}")
        motivation = therapeutic_info.get("motivacao_terapia")
        if motivation:
            parts.append(f"buscando apoio para {motivation}")
        return ", ".join(parts) if parts else "Perfil inicial construído a partir do cadastro"
