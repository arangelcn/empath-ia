"""Dependency container for the unified ai-service."""

from pathlib import Path

from dataclasses import dataclass

from fastapi import Request

from ..application.chat.chat_facade import ChatFacade
from ..application.chat.next_session_service import NextSessionService
from ..application.chat.registration_service import RegistrationService
from ..application.chat.session_context_service import SessionContextService
from ..application.chat.stream_facade import StreamFacade
from ..application.chat.user_profile_service import UserProfileService
from ..application.llm.fallback_service import FallbackService
from ..application.llm.prompt_pipeline import PromptPipeline
from ..application.llm.runtime_service import RuntimeService
from ..application.orchestration.agent_service import AgentService
from ..application.retrieval.citations import CitationService
from ..application.retrieval.rag_gateway import RAGGateway
from ..application.retrieval.retrieval_policy import RetrievalPolicy
from ..infrastructure.db.mongo import MongoManager
from ..infrastructure.http.voice_synthesis_service import VoiceSynthesisService
from ..infrastructure.llm.langchain_openai_provider import LangChainOpenAIProvider
from ..repositories.conversations import MongoConversationRepository
from ..repositories.prompts import FilePromptRepository
from ..repositories.sessions import MongoSessionRepository
from ..repositories.users import MongoUserRepository
from .settings import Settings


@dataclass(slots=True)
class AppContainer:
    """Simple container for long-lived app dependencies."""

    settings: Settings
    mongo: MongoManager
    conversation_repository: MongoConversationRepository
    user_repository: MongoUserRepository
    session_repository: MongoSessionRepository
    user_profile_service: UserProfileService
    voice_synthesis_service: VoiceSynthesisService
    prompt_pipeline: PromptPipeline
    fallback_service: FallbackService
    runtime_service: RuntimeService
    retrieval_policy: RetrievalPolicy
    rag_gateway: RAGGateway
    citation_service: CitationService
    session_context_service: SessionContextService
    next_session_service: NextSessionService
    registration_service: RegistrationService
    agent_service: AgentService
    chat_facade: ChatFacade
    stream_facade: StreamFacade


def build_container(settings: Settings) -> AppContainer:
    """Instantiate the dependency graph for the unified service."""
    mongo = MongoManager(settings.mongodb_url, settings.mongodb_database)
    conversation_repository = MongoConversationRepository(mongo)
    user_repository = MongoUserRepository(mongo)
    session_repository = MongoSessionRepository(mongo)
    user_profile_service = UserProfileService(conversation_repository, user_repository)
    voice_synthesis_service = VoiceSynthesisService(settings.voice_service_url)
    prompts_dir = Path(__file__).resolve().parents[2] / "prompts"
    prompt_repository = FilePromptRepository(prompts_dir)
    providers = []
    if settings.llm_primary_provider == "langchain_openai":
        providers.append(
            LangChainOpenAIProvider(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
        )
    prompt_pipeline = PromptPipeline(
        default_language=settings.default_language,
        prompt_repository=prompt_repository,
    )
    fallback_service = FallbackService()
    runtime_service = RuntimeService(providers=providers)
    retrieval_policy = RetrievalPolicy()
    rag_gateway = RAGGateway(settings.knowledge_service_url)
    citation_service = CitationService()
    session_context_service = SessionContextService(conversation_repository=conversation_repository)
    next_session_service = NextSessionService(
        session_repository=session_repository,
        user_profile_service=user_profile_service,
    )
    registration_service = RegistrationService(
        conversation_repository=conversation_repository,
        session_repository=session_repository,
        user_profile_service=user_profile_service,
        next_session_service=next_session_service,
        voice_synthesis_service=voice_synthesis_service,
    )
    agent_service = AgentService(
        prompt_pipeline=prompt_pipeline,
        retrieval_policy=retrieval_policy,
        rag_gateway=rag_gateway,
        citation_service=citation_service,
        runtime_service=runtime_service,
        fallback_service=fallback_service,
        conversation_repository=conversation_repository,
        user_profile_service=user_profile_service,
        session_context_service=session_context_service,
        voice_synthesis_service=voice_synthesis_service,
    )
    chat_facade = ChatFacade(
        conversation_repository=conversation_repository,
        agent_service=agent_service,
        registration_service=registration_service,
    )
    stream_facade = StreamFacade(
        conversation_repository=conversation_repository,
        agent_service=agent_service,
        registration_service=registration_service,
    )

    return AppContainer(
        settings=settings,
        mongo=mongo,
        conversation_repository=conversation_repository,
        user_repository=user_repository,
        session_repository=session_repository,
        user_profile_service=user_profile_service,
        voice_synthesis_service=voice_synthesis_service,
        prompt_pipeline=prompt_pipeline,
        fallback_service=fallback_service,
        runtime_service=runtime_service,
        retrieval_policy=retrieval_policy,
        rag_gateway=rag_gateway,
        citation_service=citation_service,
        session_context_service=session_context_service,
        next_session_service=next_session_service,
        registration_service=registration_service,
        agent_service=agent_service,
        chat_facade=chat_facade,
        stream_facade=stream_facade,
    )


def get_container(request: Request) -> AppContainer:
    """FastAPI dependency to retrieve the app container."""
    return request.app.state.container
