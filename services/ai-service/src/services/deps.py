"""
Instâncias singleton de todos os serviços do AI Service.

Importar daqui garante que existirá apenas uma conexão MongoDB,
uma conexão Redis, um cache em memória e um runtime de LLM local
em todo o processo — independente de quantos módulos importem os serviços.
"""

from .prompt_client_service import PromptClientService
from .session_context_service import SessionContextService
from .redis_performance_service import RedisPerformanceService
from .llm_service import LLMService
from .token_economy_service import TokenEconomyService

# --- instâncias únicas ---

prompt_client = PromptClientService()

session_context_svc = SessionContextService()
redis_performance_svc = RedisPerformanceService()

llm_service = LLMService(prompt_client=prompt_client)

token_economy_svc = TokenEconomyService(
    session_context_service=session_context_svc,
    redis_performance_service=redis_performance_svc,
    llm_service=llm_service,
)
