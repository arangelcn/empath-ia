"""Dependency container for ai-service-v2."""

from dataclasses import dataclass

from fastapi import Request

from ..application.chat.chat_facade import ChatFacade
from ..application.chat.next_session_service import NextSessionService
from ..application.chat.registration_service import RegistrationService
from ..application.chat.session_context_service import SessionContextService
from ..application.chat.stream_facade import StreamFacade
from ..application.llm.fallback_service import FallbackService
from ..application.llm.prompt_pipeline import PromptPipeline
from ..application.llm.runtime_service import RuntimeService
from ..application.orchestration.agent_service import AgentService
from ..application.retrieval.citations import CitationService
from ..application.retrieval.rag_gateway import RAGGateway
from ..application.retrieval.retrieval_policy import RetrievalPolicy
from .settings import Settings


@dataclass(slots=True)
class AppContainer:
    """Simple container for long-lived app dependencies."""

    settings: Settings
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
    """Instantiate the dependency graph for the scaffold."""
    prompt_pipeline = PromptPipeline(default_language=settings.default_language)
    fallback_service = FallbackService()
    runtime_service = RuntimeService()
    retrieval_policy = RetrievalPolicy()
    rag_gateway = RAGGateway(settings.knowledge_service_url)
    citation_service = CitationService()
    session_context_service = SessionContextService()
    next_session_service = NextSessionService()
    registration_service = RegistrationService()
    agent_service = AgentService(
        prompt_pipeline=prompt_pipeline,
        retrieval_policy=retrieval_policy,
        rag_gateway=rag_gateway,
        runtime_service=runtime_service,
        fallback_service=fallback_service,
    )
    chat_facade = ChatFacade(
        agent_service=agent_service,
        session_context_service=session_context_service,
        next_session_service=next_session_service,
        registration_service=registration_service,
    )
    stream_facade = StreamFacade(chat_facade=chat_facade)

    return AppContainer(
        settings=settings,
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
