"""Deterministic registration flow for `session-1` inside ai-service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from ...domain.users.display import first_name_from_user
from ...repositories.conversations import MongoConversationRepository
from ...repositories.sessions import MongoSessionRepository
from .next_session_service import NextSessionService
from .user_profile_service import UserProfileService


logger = logging.getLogger(__name__)


REGISTRATION_QUESTIONS = [
    {
        "step": 0,
        "field": "idade",
        "question": (
            "Ola! Eu sou seu assistente terapeutico. E um prazer te conhecer! "
            "Para personalizar nossa conversa, vou fazer algumas perguntas sobre voce. "
            "Primeiro, me conta: qual e a sua idade?"
        ),
    },
    {
        "step": 1,
        "field": "genero",
        "question": (
            "Obrigado! Agora me conta: como voce se identifica em relacao ao seu genero? "
            "(Por exemplo: feminino, masculino, nao-binario, prefiro nao responder, etc.)"
        ),
    },
    {
        "step": 2,
        "field": "cor_raca",
        "question": (
            "Perfeito! E como voce se identifica em relacao a sua cor/raca? "
            "(Por exemplo: branco, negro, pardo, indigena, asiatico, prefiro nao responder, etc.)"
        ),
    },
    {
        "step": 3,
        "field": "localizacao",
        "question": "Obrigado por compartilhar! Agora me conta: em que cidade e estado voce mora atualmente?",
    },
    {
        "step": 4,
        "field": "situacao_moradia",
        "question": (
            "Otimo! Como e sua situacao de moradia? Voce mora sozinho(a), com familia, "
            "amigos, companheiro(a)? Me conta um pouco sobre isso."
        ),
    },
    {
        "step": 5,
        "field": "relacao_familia",
        "question": (
            "Entendi! E como voce descreveria sua relacao com sua familia? Voces sao proximos, "
            "ha conflitos, moram longe? Fique a vontade para compartilhar o que se sentir confortavel."
        ),
    },
    {
        "step": 6,
        "field": "ocupacao",
        "question": (
            "Obrigado por compartilhar! Agora me conta: qual e sua ocupacao atual? "
            "Voce trabalha, estuda, esta desempregado(a)? Como e sua rotina?"
        ),
    },
    {
        "step": 7,
        "field": "motivacao_terapia",
        "question": (
            "Interessante! E o que te trouxe ate aqui? O que voce espera dessas nossas conversas? "
            "Ha algo especifico que gostaria de trabalhar ou simplesmente quer ter um espaco para se expressar?"
        ),
    },
    {
        "step": 8,
        "field": "informacoes_adicionais",
        "question": (
            "Muito obrigado por compartilhar todas essas informacoes comigo! Isso me ajuda muito a te conhecer melhor. "
            "Ha mais alguma coisa sobre voce que gostaria de me contar? Algo que considera importante para nossa conversa?"
        ),
    },
]


class RegistrationService:
    """Own the deterministic onboarding flow inside the unified backend."""

    def __init__(
        self,
        conversation_repository: MongoConversationRepository,
        session_repository: MongoSessionRepository,
        user_profile_service: UserProfileService,
        next_session_service: NextSessionService,
        voice_synthesis_service,
    ) -> None:
        self.conversation_repository = conversation_repository
        self.session_repository = session_repository
        self.user_profile_service = user_profile_service
        self.next_session_service = next_session_service
        self.voice_synthesis_service = voice_synthesis_service

    async def handle_message(
        self,
        session_id: str,
        user_message: str,
        *,
        is_voice_mode: bool = False,
    ) -> dict[str, Any]:
        """Advance the registration conversation and return the compatibility payload."""
        identity = await self.conversation_repository.resolve_conversation_ref(session_id, create=True)
        legacy_session_id = identity.get("legacy_session_id") or session_id
        username = identity.get("username") or self.conversation_repository.extract_username(legacy_session_id)
        if not username:
            raise ValueError(f"Session ID invalido para cadastro: {session_id}")

        await self.session_repository.ensure_registration_session(username)
        conversation = await self.conversation_repository.get_by_session_id(legacy_session_id) or {}
        if "registration_step" not in conversation:
            await self.conversation_repository.update_conversation_fields(
                legacy_session_id,
                {
                    "username": username,
                    "session_id": legacy_session_id,
                    "legacy_session_id": legacy_session_id,
                    "therapeutic_session_id": identity.get("therapeutic_session_id") or "session-1",
                    "is_registration_complete": False,
                    "registration_step": 0,
                    "registration_data": {},
                    "started_at": datetime.now(UTC),
                },
            )
            conversation = await self.conversation_repository.get_by_session_id(legacy_session_id) or {}
        current_step = int(conversation.get("registration_step", 0))
        registration_data = dict(conversation.get("registration_data") or {})

        user_message_id = await self.conversation_repository.save_message(
            legacy_session_id,
            "user",
            user_message,
            None,
        )

        if conversation.get("is_registration_complete"):
            ai_response = self._build_post_completion_message(conversation, username)
            ai_message_id = await self.conversation_repository.save_message(legacy_session_id, "ai", ai_response, None)
            await self.conversation_repository.update_message_count(legacy_session_id)
            return self._build_result(
                chat_id=identity.get("chat_id"),
                session_id=legacy_session_id,
                therapeutic_session_id=identity.get("therapeutic_session_id") or "session-1",
                user_message_id=user_message_id,
                user_message=user_message,
                ai_message_id=ai_message_id,
                ai_response=ai_response,
                audio_url=None,
                registration_completed=True,
                conversation_ended=False,
            )

        if 0 <= current_step < len(REGISTRATION_QUESTIONS):
            field = REGISTRATION_QUESTIONS[current_step]["field"]
            registration_data[field] = user_message.strip()
            await self.conversation_repository.update_conversation_fields(
                legacy_session_id,
                {"registration_data": registration_data},
            )

            next_step = current_step + 1
            if next_step < len(REGISTRATION_QUESTIONS):
                question = REGISTRATION_QUESTIONS[next_step]["question"]
                audio_url = await self._generate_audio_for_registration(question, username, is_voice_mode)
                ai_message_id = await self.conversation_repository.save_message(
                    legacy_session_id,
                    "ai",
                    question,
                    audio_url,
                )
                await self.conversation_repository.update_conversation_fields(
                    legacy_session_id,
                    {"registration_step": next_step},
                )
                await self.conversation_repository.update_message_count(legacy_session_id)
                return self._build_result(
                    chat_id=identity.get("chat_id"),
                    session_id=legacy_session_id,
                    therapeutic_session_id=identity.get("therapeutic_session_id") or "session-1",
                    user_message_id=user_message_id,
                    user_message=user_message,
                    ai_message_id=ai_message_id,
                    ai_response=question,
                    audio_url=audio_url,
                    registration_completed=False,
                    conversation_ended=False,
                )

            return await self._complete_registration(
                identity=identity,
                session_id=legacy_session_id,
                username=username,
                user_message=user_message,
                user_message_id=user_message_id,
                registration_data=registration_data,
                current_step=current_step,
                is_voice_mode=is_voice_mode,
            )

        ai_response = self._build_post_completion_message(conversation, username)
        ai_message_id = await self.conversation_repository.save_message(legacy_session_id, "ai", ai_response, None)
        await self.conversation_repository.update_message_count(legacy_session_id)
        return self._build_result(
            chat_id=identity.get("chat_id"),
            session_id=legacy_session_id,
            therapeutic_session_id=identity.get("therapeutic_session_id") or "session-1",
            user_message_id=user_message_id,
            user_message=user_message,
            ai_message_id=ai_message_id,
            ai_response=ai_response,
            audio_url=None,
            registration_completed=True,
            conversation_ended=False,
        )

    async def _complete_registration(
        self,
        *,
        identity: dict[str, Any],
        session_id: str,
        username: str,
        user_message: str,
        user_message_id: str,
        registration_data: dict[str, Any],
        current_step: int,
        is_voice_mode: bool,
    ) -> dict[str, Any]:
        user_profile = await self.user_profile_service.save_user_profile(username, registration_data)
        registration_context = self._build_registration_context(username, registration_data, user_profile)
        await self.session_repository.save_session_context(session_id, username, registration_context)
        await self.session_repository.complete_user_session(username, "session-1", progress=100, status="completed")

        next_session = await self.next_session_service.create_next_session_automatically(
            session_id,
            registration_context,
        )

        user_label = await self._get_user_label(username)
        thanks = (
            f"Perfeito! Muito obrigado por compartilhar todas essas informacoes comigo, {user_label}!"
            if user_label
            else "Perfeito! Muito obrigado por compartilhar todas essas informacoes comigo!"
        )
        ai_response = (
            f"{thanks}\n\n"
            "Agora eu te conheco melhor e posso oferecer um apoio mais personalizado. "
            "Suas informacoes estao seguras e serao usadas apenas para tornar nossas conversas mais significativas.\n\n"
            "Seu cadastro foi finalizado com sucesso!\n\n"
            "Voce agora pode acessar as outras sessoes terapeuticas na sua jornada de autoconhecimento. "
            "Cada sessao foi cuidadosamente desenvolvida para te apoiar em diferentes aspectos da sua vida."
        )
        audio_url = await self._generate_audio_for_registration(ai_response, username, is_voice_mode)
        ai_message_id = await self.conversation_repository.save_message(
            session_id,
            "ai",
            ai_response,
            audio_url,
        )
        await self.conversation_repository.update_conversation_fields(
            session_id,
            {
                "registration_data": registration_data,
                "registration_step": current_step + 1,
                "is_registration_complete": True,
                "completed_at": datetime.now(UTC),
            },
        )
        await self.conversation_repository.update_message_count(session_id)

        result = self._build_result(
            chat_id=identity.get("chat_id"),
            session_id=session_id,
            therapeutic_session_id=identity.get("therapeutic_session_id") or "session-1",
            user_message_id=user_message_id,
            user_message=user_message,
            ai_message_id=ai_message_id,
            ai_response=ai_response,
            audio_url=audio_url,
            registration_completed=True,
            conversation_ended=True,
        )
        result["data"].update(
            {
                "session_finished": True,
                "session_status": "completed",
                "redirect_to_home": True,
                "completion_message": (
                    "Cadastro finalizado com sucesso! Esta sessao esta agora concluida. "
                    "Voce pode revisar a conversa, mas nao pode enviar mais mensagens."
                ),
                "next_session": next_session,
                "auto_redirect_delay": 3000,
            }
        )
        return result

    async def _generate_audio_for_registration(
        self,
        text: str,
        username: str,
        is_voice_mode: bool,
    ) -> str | None:
        if not is_voice_mode:
            return None

        selected_voice, _ = await self.conversation_repository.get_voice_preferences(username)
        return await self.voice_synthesis_service.generate_audio(text, selected_voice, is_voice_mode=True)

    async def _get_user_label(self, username: str) -> str | None:
        user = await self.conversation_repository.get_user_document(username)
        return first_name_from_user(user, username)

    @staticmethod
    def _build_post_completion_message(conversation: dict[str, Any], username: str) -> str:
        user_label = first_name_from_user(None, username)
        if conversation.get("is_registration_complete"):
            return (
                f"Ola novamente, {user_label}! Seu cadastro ja foi concluido. "
                "Agora podemos seguir para as proximas sessoes da sua jornada."
            )
        return "Ola novamente! Como posso te ajudar hoje?"

    @staticmethod
    def _build_registration_context(
        username: str,
        registration_data: dict[str, Any],
        user_profile: dict[str, Any],
    ) -> dict[str, Any]:
        therapeutic_info = user_profile.get("therapeutic_info") or {}
        objectives = list(therapeutic_info.get("objetivos_identificados") or [])
        if not objectives:
            objectives = ["acolhimento inicial", "autoconhecimento"]
        main_themes = objectives[:3]
        summary = user_profile.get("profile_summary") or f"Cadastro inicial concluido por {username}"
        return {
            "session_type": "registration",
            "summary": summary,
            "profile_summary": summary,
            "main_themes": main_themes,
            "registration_data": dict(registration_data),
            "personal_info": user_profile.get("personal_info", {}),
            "social_info": user_profile.get("social_info", {}),
            "therapeutic_info": therapeutic_info,
            "keywords": user_profile.get("keywords", []),
            "risk_factors": user_profile.get("risk_factors", []),
            "strengths": user_profile.get("strengths", []),
            "next_session_seed": {
                "focus_areas": main_themes,
                "objectives": objectives,
            },
            "generated_at": datetime.now(UTC).isoformat(),
            "source": "registration_service_v2",
        }

    @staticmethod
    def _build_result(
        *,
        chat_id: str | None,
        session_id: str,
        therapeutic_session_id: str,
        user_message_id: str,
        user_message: str,
        ai_message_id: str,
        ai_response: str,
        audio_url: str | None,
        registration_completed: bool,
        conversation_ended: bool,
    ) -> dict[str, Any]:
        return {
            "success": True,
            "data": {
                "chat_id": chat_id,
                "session_id": session_id,
                "therapeutic_session_id": therapeutic_session_id,
                "user_message": {"id": user_message_id, "content": user_message},
                "ai_response": {
                    "id": ai_message_id,
                    "content": ai_response,
                    "audioUrl": audio_url,
                    "provider": "registration_system",
                    "model": "registration_v2",
                },
                "registration_completed": registration_completed,
                "conversation_ended": conversation_ended,
            },
        }
