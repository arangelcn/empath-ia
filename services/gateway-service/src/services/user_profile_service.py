"""
User profile normalization and persistence for registration flow.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List

from ..domain.user_display import first_name_from_user
from ..models.database import get_collection

logger = logging.getLogger(__name__)


class UserProfileService:
    """Build and persist standardized user profiles from session-1 registration data."""

    async def get_user_profile(self, username: str) -> Dict[str, Any]:
        """
        Buscar perfil completo do usuário incluindo dados de registration_data da sessão-1.
        """
        try:
            users = get_collection("users")
            conversations = get_collection("conversations")

            user = await users.find_one({"username": username})
            user_profile = {}
            preferences = (user or {}).get("preferences", {})
            preferred_name = first_name_from_user(user, username)
            display_name = (
                (user or {}).get("display_name")
                or preferences.get("display_name")
                or (user or {}).get("full_name")
                or preferences.get("full_name")
            )

            if user and user.get("user_profile"):
                user_profile = user["user_profile"]
                logger.info("✅ Perfil estruturado encontrado para %s", username)

            user_profile["username"] = username
            user_profile["preferences"] = preferences
            if preferred_name:
                user_profile["preferred_name"] = preferred_name
            if display_name:
                user_profile["display_name"] = display_name
                user_profile["full_name"] = (user or {}).get("full_name") or preferences.get("full_name") or display_name

            session_1_id = f"{username}_session-1"
            session_1_data = await conversations.find_one({"session_id": session_1_id})

            if session_1_data and session_1_data.get("registration_data"):
                registration_data = session_1_data["registration_data"]
                logger.info("✅ Registration data da sessão-1 encontrado para %s", username)
                user_profile["registration_data"] = registration_data

                if not user_profile.get("profile_summary"):
                    summary_parts = []
                    if registration_data.get("idade"):
                        summary_parts.append(f"{registration_data['idade']} anos")
                    if registration_data.get("ocupacao"):
                        if "engenheiro de dados" in registration_data["ocupacao"].lower():
                            summary_parts.append("engenheiro de dados")
                        elif "professor" in registration_data["ocupacao"].lower():
                            summary_parts.append("professor")
                    if registration_data.get("localizacao"):
                        summary_parts.append(f"de {registration_data['localizacao']}")

                    if summary_parts:
                        user_profile["profile_summary"] = f"Usuário {username}: {', '.join(summary_parts)}"

                return user_profile

            if user_profile:
                logger.info("✅ Perfil parcial encontrado para %s", username)
                return user_profile

            logger.warning("⚠️ Nenhum dado de perfil encontrado para %s", username)
            return {
                "username": username,
                "preferred_name": preferred_name,
                "display_name": display_name,
                "full_name": (user or {}).get("full_name") or preferences.get("full_name") or display_name,
                "preferences": preferences,
                "profile_summary": f"Usuário {username} - dados limitados",
                "registration_data": {},
                "personal_info": {},
                "therapeutic_info": {}
            }

        except Exception as e:
            logger.error("❌ Erro ao buscar perfil do usuário %s: %s", username, e)
            return {
                "username": username,
                "profile_summary": f"Usuário {username} - erro ao carregar dados",
                "error": str(e)
            }

    async def save_user_profile(self, username: str, registration_data: Dict[str, Any]) -> None:
        """
        Salvar perfil completo e padronizado do usuário na coleção users.
        """
        try:
            users = get_collection("users")
            user_profile = self.create_standardized_profile(username, registration_data)

            await users.update_one(
                {"username": username},
                {
                    "$set": {
                        "username": username,
                        "user_profile": user_profile,
                        "profile_completed": True,
                        "profile_completed_at": datetime.now(),
                        "updated_at": datetime.now()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now()
                    }
                },
                upsert=True
            )

            logger.info("✅ Perfil padronizado do usuário %s salvo com sucesso", username)
            logger.info("📊 Dados salvos: %s", user_profile)

        except Exception as e:
            logger.error("❌ Erro ao salvar perfil do usuário: %s", e)

    def create_standardized_profile(self, username: str, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Criar perfil padronizado a partir dos dados de cadastro.
        """
        personal_info = {
            "idade": self.normalize_age(registration_data.get("idade", "")),
            "genero": self.normalize_gender(registration_data.get("genero", "")),
            "cor_raca": self.normalize_race(registration_data.get("cor_raca", "")),
            "localizacao": self.normalize_location(registration_data.get("localizacao", ""))
        }

        social_info = {
            "situacao_moradia": self.normalize_text(registration_data.get("situacao_moradia", "")),
            "relacao_familia": self.normalize_text(registration_data.get("relacao_familia", "")),
            "ocupacao": self.normalize_text(registration_data.get("ocupacao", ""))
        }

        therapeutic_info = {
            "motivacao_terapia": self.normalize_text(registration_data.get("motivacao_terapia", "")),
            "informacoes_adicionais": self.normalize_text(registration_data.get("informacoes_adicionais", "")),
            "objetivos_identificados": self.extract_objectives(registration_data)
        }

        return {
            "personal_info": personal_info,
            "social_info": social_info,
            "therapeutic_info": therapeutic_info,
            "profile_summary": self.generate_profile_summary(personal_info, social_info, therapeutic_info),
            "keywords": self.extract_keywords(registration_data),
            "risk_factors": self.identify_risk_factors(registration_data),
            "strengths": self.identify_strengths(registration_data),
            "created_at": datetime.now().isoformat(),
            "data_source": "session-1_registration"
        }

    def normalize_age(self, age_input: str) -> Dict[str, Any]:
        """Normalizar idade."""
        try:
            age_text = str(age_input).strip().lower()
            age_numbers = re.findall(r'\d+', age_text)

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

                return {
                    "valor": age,
                    "categoria": category,
                    "original": age_input.strip()
                }

            return {
                "valor": None,
                "categoria": "nao_informado",
                "original": age_input.strip()
            }

        except Exception:
            return {
                "valor": None,
                "categoria": "erro_processamento",
                "original": age_input.strip()
            }

    def normalize_gender(self, gender_input: str) -> Dict[str, Any]:
        """Normalizar gênero."""
        gender_text = str(gender_input).strip().lower()
        gender_mapping = {
            "feminino": "feminino",
            "mulher": "feminino",
            "f": "feminino",
            "masculino": "masculino",
            "homem": "masculino",
            "m": "masculino",
            "não-binário": "nao_binario",
            "nao binario": "nao_binario",
            "não binário": "nao_binario",
            "nao-binario": "nao_binario",
            "nb": "nao_binario",
            "trans": "trans",
            "transgender": "trans",
            "prefiro não responder": "prefere_nao_responder",
            "prefiro nao responder": "prefere_nao_responder",
            "não responder": "prefere_nao_responder"
        }

        return {
            "categoria": gender_mapping.get(gender_text, "outros"),
            "original": gender_input.strip()
        }

    def normalize_race(self, race_input: str) -> Dict[str, Any]:
        """Normalizar cor/raça."""
        race_text = str(race_input).strip().lower()
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
            "asiático": "amarelo",
            "asiática": "amarelo",
            "indígena": "indigena",
            "índio": "indigena",
            "índia": "indigena",
            "prefiro não responder": "prefere_nao_responder",
            "prefiro nao responder": "prefere_nao_responder"
        }

        return {
            "categoria": race_mapping.get(race_text, "outros"),
            "original": race_input.strip()
        }

    def normalize_location(self, location_input: str) -> Dict[str, Any]:
        """Normalizar localização."""
        location_text = str(location_input).strip()
        patterns = [
            r"(.+?)[,\-]\s*(.+?)$",
            r"(.+?)\s+(\w{2})$",
        ]

        city = ""
        state = ""

        for pattern in patterns:
            match = re.search(pattern, location_text)
            if match:
                city = match.group(1).strip()
                state = match.group(2).strip()
                break

        if not city and not state:
            city = location_text

        return {
            "cidade": city,
            "estado": state,
            "original": location_input.strip(),
            "formatted": f"{city}, {state}" if state else city
        }

    def normalize_text(self, text_input: str) -> Dict[str, Any]:
        """Normalizar texto geral."""
        text = str(text_input).strip()

        return {
            "content": text,
            "length": len(text),
            "words": len(text.split()) if text else 0,
            "has_content": len(text) > 0
        }

    def extract_objectives(self, registration_data: Dict[str, Any]) -> List[str]:
        """Extrair objetivos terapêuticos baseados nas respostas."""
        objectives = []
        motivation = registration_data.get("motivacao_terapia", "").lower()
        objective_keywords = {
            "ansiedade": "Trabalhar questões de ansiedade",
            "depressão": "Apoio para questões depressivas",
            "relacionamento": "Melhorar relacionamentos",
            "família": "Resolver questões familiares",
            "trabalho": "Questões profissionais e carreira",
            "autoestima": "Fortalecer autoestima",
            "stress": "Gerenciar stress e pressão",
            "luto": "Processar perdas e luto",
            "mudança": "Lidar com mudanças de vida",
            "crescimento": "Desenvolvimento pessoal"
        }

        for keyword, objective in objective_keywords.items():
            if keyword in motivation:
                objectives.append(objective)

        if not objectives:
            objectives.append("Desenvolvimento pessoal e bem-estar")

        return objectives

    def generate_profile_summary(self, personal_info: Dict, social_info: Dict, therapeutic_info: Dict) -> str:
        """Gerar resumo do perfil do usuário."""
        summary_parts = []

        if personal_info["idade"]["valor"]:
            summary_parts.append(f"Idade: {personal_info['idade']['valor']} anos ({personal_info['idade']['categoria']})")

        if personal_info["genero"]["categoria"] != "outros":
            summary_parts.append(f"Gênero: {personal_info['genero']['categoria']}")

        if personal_info["localizacao"]["formatted"]:
            summary_parts.append(f"Localização: {personal_info['localizacao']['formatted']}")

        if social_info["ocupacao"]["has_content"]:
            summary_parts.append(f"Ocupação: {social_info['ocupacao']['content'][:50]}...")

        if therapeutic_info["motivacao_terapia"]["has_content"]:
            summary_parts.append(f"Motivação: {therapeutic_info['motivacao_terapia']['content'][:100]}...")

        return "; ".join(summary_parts)

    def extract_keywords(self, registration_data: Dict[str, Any]) -> List[str]:
        """Extrair palavras-chave relevantes do cadastro."""
        keywords = []
        text_fields = [
            registration_data.get("genero", ""),
            registration_data.get("situacao_moradia", ""),
            registration_data.get("relacao_familia", ""),
            registration_data.get("ocupacao", ""),
            registration_data.get("motivacao_terapia", ""),
            registration_data.get("informacoes_adicionais", "")
        ]
        combined_text = " ".join(text_fields).lower()
        relevant_keywords = [
            "ansiedade", "depressão", "stress", "família", "relacionamento",
            "trabalho", "estudos", "autoestima", "confiança", "medo",
            "tristeza", "raiva", "solidão", "conflito", "mudança",
            "crescimento", "desenvolvimento", "apoio", "ajuda"
        ]

        for keyword in relevant_keywords:
            if keyword in combined_text:
                keywords.append(keyword)

        return keywords

    def identify_risk_factors(self, registration_data: Dict[str, Any]) -> List[str]:
        """Identificar possíveis fatores de risco mencionados."""
        risk_factors = []
        all_responses = " ".join([
            registration_data.get("relacao_familia", ""),
            registration_data.get("motivacao_terapia", ""),
            registration_data.get("informacoes_adicionais", "")
        ]).lower()
        risk_indicators = {
            "isolamento": ["sozinho", "isolado", "sem amigos", "sem apoio"],
            "conflitos_familiares": ["conflito", "briga", "problema família", "família difícil"],
            "questoes_profissionais": ["desempregado", "sem trabalho", "stress trabalho", "problema trabalho"],
            "questoes_emocionais": ["deprimido", "triste", "ansioso", "medo", "pânico"],
            "mudancas_significativas": ["separação", "divórcio", "morte", "luto", "mudança"]
        }

        for risk_type, indicators in risk_indicators.items():
            for indicator in indicators:
                if indicator in all_responses:
                    risk_factors.append(risk_type)
                    break

        return list(set(risk_factors))

    def identify_strengths(self, registration_data: Dict[str, Any]) -> List[str]:
        """Identificar forças e recursos positivos mencionados."""
        strengths = []
        all_responses = " ".join([
            registration_data.get("situacao_moradia", ""),
            registration_data.get("relacao_familia", ""),
            registration_data.get("ocupacao", ""),
            registration_data.get("motivacao_terapia", ""),
            registration_data.get("informacoes_adicionais", "")
        ]).lower()
        strength_indicators = {
            "apoio_familiar": ["família unida", "apoio família", "família próxima", "bom relacionamento família"],
            "apoio_social": ["amigos", "apoio", "grupo", "comunidade"],
            "estabilidade_profissional": ["trabalho", "empregado", "carreira", "estudando"],
            "autoconsciencia": ["autoconhecimento", "crescimento", "desenvolvimento", "melhorar"],
            "motivacao_mudanca": ["quer mudar", "disposto", "determinado", "esperança"]
        }

        for strength_type, indicators in strength_indicators.items():
            for indicator in indicators:
                if indicator in all_responses:
                    strengths.append(strength_type)
                    break

        return list(set(strengths))
