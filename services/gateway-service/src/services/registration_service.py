"""
Registration/onboarding flow for session-1.
"""

import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Optional

from ..domain.user_display import first_name_from_user
from ..models.database import get_collection
from .user_profile_service import UserProfileService
from .user_therapeutic_session_service import UserTherapeuticSessionService

logger = logging.getLogger(__name__)

SaveMessage = Callable[[str, str, str, Optional[str]], Awaitable[str]]
FinalizeContext = Callable[[str, bool], Awaitable[Dict[str, Any]]]
GenerateAudio = Callable[[str, str, bool], Awaitable[Optional[str]]]
ExtractUsername = Callable[[str], Optional[str]]


REGISTRATION_QUESTIONS = [
    {
        "step": 0,
        "question": "Olá! Eu sou seu assistente terapêutico. É um prazer te conhecer! Para personalizar nossa conversa, vou fazer algumas perguntas sobre você. Primeiro, me conta: qual é a sua idade?",
        "field": "idade",
        "type": "number"
    },
    {
        "step": 1,
        "question": "Obrigado! Agora me conta: como você se identifica em relação ao seu gênero? (Por exemplo: feminino, masculino, não-binário, prefiro não responder, etc.)",
        "field": "genero",
        "type": "text"
    },
    {
        "step": 2,
        "question": "Perfeito! E como você se identifica em relação à sua cor/raça? (Por exemplo: branco, negro, pardo, indígena, asiático, prefiro não responder, etc.)",
        "field": "cor_raca",
        "type": "text"
    },
    {
        "step": 3,
        "question": "Obrigado por compartilhar! Agora me conta: em que cidade e estado você mora atualmente?",
        "field": "localizacao",
        "type": "text"
    },
    {
        "step": 4,
        "question": "Ótimo! Como é sua situação de moradia? Você mora sozinho(a), com família, amigos, companheiro(a)? Me conta um pouco sobre isso.",
        "field": "situacao_moradia",
        "type": "text"
    },
    {
        "step": 5,
        "question": "Entendi! E como você descreveria sua relação com sua família? Vocês são próximos, há conflitos, moram longe? Fique à vontade para compartilhar o que se sentir confortável.",
        "field": "relacao_familia",
        "type": "text"
    },
    {
        "step": 6,
        "question": "Obrigado por compartilhar! Agora me conta: qual é sua ocupação atual? Você trabalha, estuda, está desempregado(a)? Como é sua rotina?",
        "field": "ocupacao",
        "type": "text"
    },
    {
        "step": 7,
        "question": "Interessante! E o que te trouxe até aqui? O que você espera dessas nossas conversas? Há algo específico que gostaria de trabalhar ou simplesmente quer ter um espaço para se expressar?",
        "field": "motivacao_terapia",
        "type": "text"
    },
    {
        "step": 8,
        "question": "Muito obrigado por compartilhar todas essas informações comigo! Isso me ajuda muito a te conhecer melhor. Há mais alguma coisa sobre você que gostaria de me contar? Algo que considera importante para nossa conversa?",
        "field": "informacoes_adicionais",
        "type": "text"
    }
]


class RegistrationService:
    """Owns the deterministic session-1 registration flow."""

    def __init__(
        self,
        *,
        save_message: SaveMessage,
        finalize_session_context: FinalizeContext,
        generate_audio: GenerateAudio,
        extract_username_from_session_id: ExtractUsername,
        user_profile_service: UserProfileService,
    ):
        self.save_message = save_message
        self.finalize_session_context = finalize_session_context
        self.generate_audio = generate_audio
        self.extract_username_from_session_id = extract_username_from_session_id
        self.user_profile_service = user_profile_service

    async def handle_session(
        self,
        session_id: str,
        user_message: str,
        is_voice_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Gerenciar a sessão de cadastro (session-1) com perguntas próprias, sem OpenAI.
        """
        try:
            logger.info("🔍 PROCESSANDO SESSÃO DE CADASTRO para %s", session_id)
            if is_voice_mode:
                logger.info("🎤 VoiceMode ativo na sessão de cadastro")

            username = self.extract_username_from_session_id(session_id) or "usuario"
            user_label = await self._get_user_label(username)
            conversations = get_collection("conversations")
            conversation = await conversations.find_one({"session_id": session_id})

            if not conversation:
                conversation = {
                    "session_id": session_id,
                    "username": username,
                    "started_at": datetime.now(),
                    "messages": [],
                    "registration_data": {},
                    "registration_step": 0,
                    "is_registration_complete": False
                }
                await conversations.insert_one(conversation)

            registration_data = conversation.get("registration_data", {})
            current_step = conversation.get("registration_step", 0)

            if current_step >= 0 and current_step < len(REGISTRATION_QUESTIONS):
                user_message_id = await self.save_message(session_id, "user", user_message, None)

                field = REGISTRATION_QUESTIONS[current_step]["field"]
                registration_data[field] = user_message.strip()
                await conversations.update_one(
                    {"session_id": session_id},
                    {"$set": {"registration_data": registration_data}}
                )
                logger.info("📝 CADASTRO: Campo %r salvo para %s", field, username)

                next_step_index = current_step + 1
                if next_step_index < len(REGISTRATION_QUESTIONS):
                    return await self._next_question_response(
                        conversations,
                        session_id,
                        username,
                        user_message,
                        user_message_id,
                        next_step_index,
                        is_voice_mode,
                    )

                return await self._complete_registration_response(
                    conversations,
                    session_id,
                    username,
                    user_label,
                    user_message,
                    user_message_id,
                    registration_data,
                    current_step,
                    is_voice_mode,
                )

            ai_response = (
                f"Olá novamente, {user_label}! Como posso te ajudar hoje?"
                if user_label
                else "Olá novamente! Como posso te ajudar hoje?"
            )
            user_message_id = await self.save_message(session_id, "user", user_message, None)
            ai_message_id = await self.save_message(session_id, "ai", ai_response, None)

            logger.info("💬 CADASTRO: Conversa normal pós-cadastro para %s", username)

            return {
                "success": True,
                "data": {
                    "user_message": {
                        "id": user_message_id,
                        "content": user_message
                    },
                    "ai_response": {
                        "id": ai_message_id,
                        "content": ai_response,
                        "audioUrl": None,
                        "provider": "registration_system",
                        "model": "cadastro_v1"
                    }
                }
            }

        except Exception as e:
            logger.error("❌ Erro na sessão de cadastro: %s", e)
            return {
                "success": False,
                "error": f"Erro na sessão de cadastro: {str(e)}"
            }

    async def _next_question_response(
        self,
        conversations,
        session_id: str,
        username: str,
        user_message: str,
        user_message_id: str,
        next_step_index: int,
        is_voice_mode: bool,
    ) -> Dict[str, Any]:
        ai_response = REGISTRATION_QUESTIONS[next_step_index]["question"]
        logger.info("❓ CADASTRO: Pergunta %s para %s", next_step_index + 1, username)

        ai_message_id = await self.save_message(session_id, "ai", ai_response, None)
        audio_url = await self._generate_audio_for_registration(ai_response, username, is_voice_mode)

        await conversations.update_one(
            {"session_id": session_id},
            {"$set": {"registration_step": next_step_index}}
        )

        logger.info("📝 CADASTRO: Pergunta %s de %s para %s", next_step_index + 1, len(REGISTRATION_QUESTIONS), username)
        return {
            "success": True,
            "data": {
                "user_message": {
                    "id": user_message_id,
                    "content": user_message
                },
                "ai_response": {
                    "id": ai_message_id,
                    "content": ai_response,
                    "audioUrl": audio_url,
                    "provider": "registration_system",
                    "model": "cadastro_v1"
                }
            }
        }

    async def _complete_registration_response(
        self,
        conversations,
        session_id: str,
        username: str,
        user_label: Optional[str],
        user_message: str,
        user_message_id: str,
        registration_data: Dict[str, Any],
        current_step: int,
        is_voice_mode: bool,
    ) -> Dict[str, Any]:
        logger.info("🎯 INICIANDO FINALIZAÇÃO DO CADASTRO para %s", username)

        thanks = (
            f"Perfeito! Muito obrigado por compartilhar todas essas informações comigo, {user_label}!"
            if user_label
            else "Perfeito! Muito obrigado por compartilhar todas essas informações comigo!"
        )
        ai_response = f"""{thanks}

Agora eu te conheço melhor e posso oferecer um apoio mais personalizado. Suas informações estão seguras e serão usadas apenas para tornar nossas conversas mais significativas.

Seu cadastro foi finalizado com sucesso! 🎉

Você agora pode acessar as outras sessões terapêuticas na sua jornada de autoconhecimento. Cada sessão foi cuidadosamente desenvolvida para te apoiar em diferentes aspectos da sua vida."""

        ai_message_id = await self.save_message(session_id, "ai", ai_response, None)
        logger.info("✅ CADASTRO: Mensagem de finalização salva para %s", username)

        finalization_audio_url = await self._generate_audio_for_registration(ai_response, username, is_voice_mode)

        await conversations.update_one(
            {"session_id": session_id},
            {"$set": {
                "is_registration_complete": True,
                "registration_step": current_step + 1,
                "completed_at": datetime.utcnow()
            }}
        )
        logger.info("✅ CADASTRO: Marcado como completo para %s", username)

        await self.user_profile_service.save_user_profile(username, registration_data)
        logger.info("✅ CADASTRO: Perfil do usuário salvo para %s", username)

        await self._complete_user_session(username)
        finalize_success = await self._finalize_context_and_create_next_session(session_id)

        logger.info("🎉 CADASTRO: Finalizado com sucesso para %s - Flags de finalização definidos", username)
        return {
            "success": True,
            "data": {
                "user_message": {
                    "id": user_message_id,
                    "content": user_message
                },
                "ai_response": {
                    "id": ai_message_id,
                    "content": ai_response,
                    "audioUrl": finalization_audio_url,
                    "provider": "registration_system",
                    "model": "cadastro_v1"
                },
                "registration_completed": True,
                "session_finished": True,
                "session_status": "completed",
                "redirect_to_home": True,
                "completion_message": "Cadastro finalizado com sucesso! Esta sessão está agora concluída. Você pode revisar a conversa, mas não pode enviar mais mensagens.",
                "finalize_success": finalize_success,
                "auto_redirect_delay": 3000
            }
        }

    async def _complete_user_session(self, username: str) -> None:
        try:
            user_session_service = UserTherapeuticSessionService()
            completion_success = await user_session_service.complete_session(username, "session-1", 100, status="completed")
            if completion_success:
                logger.info("✅ CADASTRO: Session-1 marcada como COMPLETED para %s", username)
            else:
                logger.warning("⚠️ CADASTRO: Falha ao marcar session-1 como completed para %s", username)
        except Exception as session_error:
            logger.error("❌ CADASTRO: Erro ao finalizar session-1: %s", session_error)

    async def _finalize_context_and_create_next_session(self, session_id: str) -> bool:
        try:
            logger.info("🚀 CADASTRO: Finalizando contexto da session-1 para criar próxima sessão automaticamente")
            finalize_result = await self.finalize_session_context(session_id, manual_termination=True)

            if finalize_result.get("success"):
                next_session_info = finalize_result.get("next_session", {})
                if next_session_info.get("success"):
                    logger.info(
                        "✅ CADASTRO: Próxima sessão criada automaticamente após session-1: %s",
                        next_session_info.get("session_id"),
                    )
                else:
                    logger.warning("⚠️ CADASTRO: Próxima sessão não foi criada: %s", next_session_info)
                return True

            logger.warning("⚠️ CADASTRO: Falha ao finalizar contexto da session-1: %s", finalize_result)
            return False

        except Exception as finalize_error:
            logger.error("❌ CADASTRO: Erro ao finalizar contexto da session-1: %s", finalize_error)
            return False

    async def _get_user_label(self, username: str) -> Optional[str]:
        try:
            users_collection = get_collection("users")
            user = await users_collection.find_one({"username": username})
            return first_name_from_user(user, username)
        except Exception as exc:
            logger.warning("⚠️ CADASTRO: não foi possível resolver nome humano para %s: %s", username, exc)
            return first_name_from_user(None, username)

    async def _generate_audio_for_registration(
        self,
        ai_response: str,
        username: str,
        is_voice_mode: bool,
    ) -> Optional[str]:
        """
        Gerar áudio para respostas da sessão de cadastro quando VoiceMode está ativo.
        """
        if not is_voice_mode:
            return None

        try:
            users_collection = get_collection("users")
            user = await users_collection.find_one({"username": username})

            selected_voice = "pt-BR-Neural2-B"
            if user and user.get("preferences"):
                selected_voice = user["preferences"].get("selected_voice", selected_voice)

            logger.info("🎤 Gerando áudio para cadastro (VoiceMode) - %s, voz: %s", username, selected_voice)
            audio_url = await self.generate_audio(ai_response, selected_voice, is_voice_mode)

            if audio_url:
                logger.info("✅ Áudio gerado para cadastro: %s", audio_url)
            else:
                logger.warning("⚠️ Falha ao gerar áudio para cadastro")

            return audio_url

        except Exception as e:
            logger.error("❌ Erro ao gerar áudio para cadastro: %s", e)
            return None
