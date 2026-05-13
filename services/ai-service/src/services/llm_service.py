"""
Serviço LLM principal do AI Service.
Gerencia conversas terapêuticas via endpoint OpenAI-compatible configurável.
"""

import os
import re
import json
import logging
import asyncio
import time
import unicodedata
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Any, Tuple
from datetime import datetime

# Import OpenAI com tratamento de erro
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None
    OpenAI = None

from .prompt_client_service import PromptClientService

logger = logging.getLogger(__name__)

_GENERIC_SESSION_CONTEXT_THEMES = {
    "apoio",
    "apoio emocional",
    "autoconhecimento",
    "bem estar",
    "bem-estar",
    "conversa",
    "conversa terapeutica",
    "conversa terapêutica",
    "desenvolvimento pessoal",
    "escuta ativa",
    "sentimentos",
    "sessao terapeutica",
    "sessão terapêutica",
    "terapia",
    "tema geral",
    "temas importantes",
    "temas identificados",
}

# ---------------------------------------------------------------------------
# Carregamento dos prompts em disco (fallback quando Gateway indisponível)
# ---------------------------------------------------------------------------
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def _load_prompt_file(filename: str) -> str:
    try:
        return (_PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()
    except Exception as exc:
        logger.warning("Não foi possível carregar prompt '%s': %s", filename, exc)
        return ""

_SYSTEM_ROGERS_PROMPT = _load_prompt_file("system_rogers.txt")
_SYSTEM_ROGERS_LOCAL_PROMPT = _load_prompt_file("system_rogers_local.txt")
_VOICE_SHORT_PROMPT   = _load_prompt_file("voice_short_response.txt")
_SESSION_ANALYSIS_TMPL = _load_prompt_file("session_context_analysis.txt")
_SESSION_ANALYSIS_LOCAL_TMPL = _load_prompt_file("session_context_analysis_local.txt")
_NEXT_SESSION_TMPL     = _load_prompt_file("next_session_generation.txt")

try:
    _FALLBACK_RESPONSES: Dict[str, str] = json.loads(
        (_PROMPTS_DIR / "fallbacks.json").read_text(encoding="utf-8")
    )
except Exception as exc:
    logger.warning("Não foi possível carregar fallbacks.json: %s", exc)
    _FALLBACK_RESPONSES = {}


def _extract_json_payload(raw_value: Any) -> Optional[Dict[str, Any]]:
    """Extract a JSON object from plain text, fenced markdown, or wrapped content."""
    candidate: Any = raw_value

    if isinstance(candidate, dict):
        for key in ("content", "text", "data", "result", "response"):
            nested = candidate.get(key)
            if isinstance(nested, (dict, str)):
                candidate = nested
                break

    if isinstance(candidate, dict):
        return candidate

    if not isinstance(candidate, str):
        return None

    text = candidate.strip()
    if not text:
        return None

    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.IGNORECASE | re.DOTALL)
    if fenced_match:
        text = fenced_match.group(1).strip()

    for payload in (text, _extract_braced_json(text)):
        if not payload:
            continue
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    return None


def _extract_braced_json(text: str) -> Optional[str]:
    start_idx = text.find("{")
    end_idx = text.rfind("}") + 1
    if start_idx < 0 or end_idx <= start_idx:
        return None
    return text[start_idx:end_idx]


def _render_prompt_template(template: str, **variables: Any) -> str:
    """Render only known placeholders without treating JSON braces as format markers."""
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{key}}}", str(value))
    return rendered

class LLMService:
    """
    Serviço LLM principal usando endpoint OpenAI-compatible.
    Gerencia conversas terapêuticas com o Dr. Rogers.
    """

    def __init__(self, prompt_client: Optional[PromptClientService] = None):
        """Inicializar serviço LLM."""
        self.primary_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.fallback_provider = os.getenv("LLM_FALLBACK_PROVIDER", "none").lower()
        self.provider = self.primary_provider
        self.openai_base_url = self._resolve_openai_base_url()
        self.local_openai_compatible = self._is_local_openai_compatible_base(self.openai_base_url)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.effective_api_key = self._resolve_openai_api_key(self.api_key, self.openai_base_url)
        self.openai_model = self._resolve_openai_model()
        self.model = self.openai_model
        self.max_tokens = int(os.getenv("MAX_TOKENS", "220" if self.local_openai_compatible else "700"))
        self.voice_max_tokens = int(os.getenv("VOICE_MAX_TOKENS", "120" if self.local_openai_compatible else "180"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.3"))
        self.request_timeout_seconds = float(os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", "90"))

        # Configurações de contexto
        self.max_history_messages = int(os.getenv("MAX_HISTORY_MESSAGES", "4" if self.local_openai_compatible else "6"))
        self.max_context_tokens = int(os.getenv("MAX_CONTEXT_TOKENS", "2000"))
        self.enable_context_compression = os.getenv("ENABLE_CONTEXT_COMPRESSION", "true").lower() == "true"
        self.local_profile_context_chars = int(os.getenv("LOCAL_PROFILE_CONTEXT_CHARS", "360"))
        self.local_previous_context_chars = int(os.getenv("LOCAL_PREVIOUS_CONTEXT_CHARS", "420"))
        self.local_session_analysis_chars = int(os.getenv("LOCAL_SESSION_ANALYSIS_CHARS", "3200"))

        # Cache em memória por usuário
        self.user_context_cache: Dict[str, Any] = {}
        self.user_session_cache: Dict[str, Any] = {}
        self.user_session_tracking: Dict[str, Any] = {}
        self.cache_max_size = int(os.getenv("CACHE_MAX_SIZE", "100"))
        self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))
        self.session_tracking_enabled = os.getenv("SESSION_TRACKING_ENABLED", "true").lower() == "true"

        # Serviço de prompts (injetado ou criado localmente)
        self.prompt_client = prompt_client or PromptClientService()
        self.client = None

        # Verificar configuração OpenAI de forma independente para fallback
        if not self.effective_api_key or not OPENAI_AVAILABLE:
            logger.warning(
                "⚠️ OPENAI_API_KEY/OPENAI_COMPAT_API_KEY não configurada ou OpenAI SDK indisponível - usando modo fallback"
            )
        else:
            try:
                self.client = OpenAI(
                    api_key=self.effective_api_key,
                    base_url=self.openai_base_url,
                )
                logger.info("✅ Cliente OpenAI inicializado com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao inicializar cliente OpenAI: {e}")
                self.client = None

        self._log_startup_llm_mode()
                
        # ✅ NOVO: Inicializar cache de contexto
        logger.info(f"✅ Cache de contexto inicializado - Max size: {self.cache_max_size}, TTL: {self.cache_ttl}s")
        logger.info(f"✅ Session tracking: {'Habilitado' if self.session_tracking_enabled else 'Desabilitado'}")

    async def ensure_local_model_ready(self) -> bool:
        """Compat shim: local GGUF runtime foi removido; nenhuma ação necessária."""
        return False

    def _active_provider(self) -> str:
        """Return the provider that will be attempted first at runtime."""
        for provider in self._provider_order():
            if self._provider_available(provider):
                return provider
        return "fallback_template"

    def _active_mode_label(self) -> str:
        active_provider = self._active_provider()
        if active_provider in {"openai", "local"}:
            if self.local_openai_compatible:
                return "LOCAL_OPENAI_COMPAT"
            return "OPENAI_CLOUD"
        return "TEMPLATE_FALLBACK"

    def _log_startup_llm_mode(self) -> None:
        """Log the configured and active LLM mode during service startup."""
        provider_order = " -> ".join(self._provider_order()) or "none"
        active_provider = self._active_provider()
        active_model = self.openai_model if active_provider in {"openai", "local"} else "hardcoded-therapeutic-template"

        logger.info("🤖 AI Service LLM startup mode: %s", self._active_mode_label())
        logger.info(
            "🤖 LLM provider chain: primary=%s, fallback=%s, order=%s, active=%s",
            self.primary_provider,
            self.fallback_provider,
            provider_order,
            active_provider,
        )
        logger.info("🤖 Active LLM model: %s", active_model)
        logger.info("🤖 OpenAI-compatible base URL: %s", self.openai_base_url)
        if active_provider == "fallback_template":
            logger.warning("⚠️ Nenhum provider LLM configurado está disponível; usando fallback terapêutico hardcoded")
    
    def is_available(self) -> bool:
        """Verificar se algum provedor LLM configurado está disponível."""
        return any(self._provider_available(provider) for provider in self._provider_order())

    def _provider_order(self) -> List[str]:
        """Retornar a cadeia de provedores sem duplicatas."""
        providers = [self.primary_provider]
        if self.fallback_provider and self.fallback_provider not in ["none", "disabled"]:
            providers.append(self.fallback_provider)

        ordered = []
        for provider in providers:
            if provider and provider not in ordered:
                ordered.append(provider)
        return ordered

    def _provider_available(self, provider: str) -> bool:
        if provider in {"openai", "local"}:
            return self.client is not None and self.effective_api_key is not None and OPENAI_AVAILABLE
        return False

    @staticmethod
    def _is_local_openai_compatible_base(base_url: str) -> bool:
        local_hosts = ("localhost", "127.0.0.1", "host.docker.internal")
        return any(host in base_url for host in local_hosts)

    @classmethod
    def _normalize_openai_base_url(cls, raw_base_url: Optional[str], raw_completions_url: Optional[str]) -> str:
        base_url = (raw_base_url or "").strip()
        if base_url:
            return base_url.rstrip("/")

        completions_url = (raw_completions_url or "").strip()
        if not completions_url:
            return "http://host.docker.internal:1234/v1"

        normalized = completions_url.rstrip("/")
        for suffix in ("/chat/completions", "/completions", "/responses"):
            if normalized.endswith(suffix):
                return normalized[: -len(suffix)].rstrip("/")
        return normalized

    def _resolve_openai_base_url(self) -> str:
        return self._normalize_openai_base_url(
            os.getenv("OPENAI_ENDPOINT") or os.getenv("OPENAI_BASE_URL") or os.getenv("LLM_BASE_URL"),
            os.getenv("OPENAI_COMPLETIONS_URL"),
        )

    @staticmethod
    def _resolve_openai_model() -> str:
        return (
            os.getenv("OPENAI_MODEL")
            or os.getenv("MODEL_NAME")
            or "gpt-4o"
        )

    def _resolve_openai_api_key(self, configured_api_key: Optional[str], base_url: str) -> Optional[str]:
        if configured_api_key:
            return configured_api_key
        if self._is_local_openai_compatible_base(base_url):
            return os.getenv("OPENAI_COMPAT_API_KEY", "lm-studio")
        return None
    
    def _validate_session_ownership(self, session_id: str, username: str) -> bool:
        """
        Validar se o usuário tem acesso à sessão especificada
        """
        try:
            # ✅ NOVO: Validar formato do session_id
            if not session_id or not username:
                logger.error(f"❌ Parâmetros inválidos: session_id={session_id}, username={username}")
                return False
            
            # Verificar se o session_id contém o username
            if "_" in session_id:
                # Formato esperado: "username_session-X" 
                # Para usernames com underscore, precisamos encontrar o padrão "session-"
                if "session-" in session_id:
                    # Encontrar onde termina o username (antes de "session-")
                    session_part_index = session_id.find("session-")
                    extracted_username = session_id[:session_part_index].rstrip("_")
                else:
                    # Fallback para o método anterior
                    extracted_username = session_id.split("_")[0]
                
                logger.info(f"🔍 DEBUG - session_id: {session_id}, username: {username}, extracted_username: {extracted_username}")
                if extracted_username != username:
                    logger.error(f"❌ Tentativa de acesso não autorizado: {username} tentou acessar sessão de {extracted_username}")
                    return False
            else:
                # Para sessões legacy ou de teste, permitir se for formato simples
                if session_id in ["default", "test"]:
                    logger.warning(f"⚠️ Sessão legacy/test detectada: {session_id} para {username}")
                    return True
                else:
                    logger.error(f"❌ Formato de session_id inválido: {session_id}")
                    return False
            
            logger.info(f"✅ Validação de propriedade da sessão: {username} -> {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar propriedade da sessão: {e}")
            return False
    
    def _validate_user_context(self, conversation_history: List[Dict], username: str) -> List[Dict]:
        """
        Validar e filtrar histórico de conversa para garantir que pertence ao usuário
        """
        try:
            if not conversation_history:
                return []
            
            # ✅ NOVO: Filtrar apenas mensagens válidas (sem dados sensíveis de outros usuários)
            validated_history = []
            
            for i, message in enumerate(conversation_history):
                # Validar estrutura da mensagem
                if not isinstance(message, dict) or "type" not in message or "content" not in message:
                    logger.warning(f"⚠️ Mensagem {i} com formato inválido ignorada para {username}")
                    continue
                
                # Validar tipo de mensagem
                if message["type"] not in ["user", "assistant", "ai"]:
                    logger.warning(f"⚠️ Tipo de mensagem inválido ignorado: {message['type']}")
                    continue
                
                # Validar conteúdo
                content = message["content"]
                if not isinstance(content, str) or not content.strip():
                    logger.warning(f"⚠️ Conteúdo vazio ou inválido na mensagem {i} para {username}")
                    continue
                
                # ✅ NOVO: Sanitizar e validar conteúdo
                sanitized_content = self._sanitize_and_validate_content(content, username, i)
                
                if sanitized_content:
                    validated_history.append({
                        "type": message["type"],
                        "content": sanitized_content,
                        "validated": True,
                        "original_index": i
                    })
                else:
                    logger.warning(f"⚠️ Mensagem {i} rejeitada após sanitização para {username}")
            
            logger.info(f"✅ Histórico validado: {len(validated_history)}/{len(conversation_history)} mensagens para {username}")
            return validated_history
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar contexto do usuário: {e}")
            return []
    
    def _sanitize_and_validate_content(self, content: str, username: str, message_index: int) -> Optional[str]:
        """
        Sanitizar e validar conteúdo da mensagem com verificações de segurança
        """
        try:
            # Verificações de segurança
            security_checks = [
                self._check_for_user_references(content, username),
                self._check_for_sensitive_data(content),
                self._check_content_length(content),
                self._check_for_malicious_content(content),
                self._check_for_system_commands(content)
            ]
            
            # Se alguma verificação falhar, rejeitar mensagem
            for check_name, check_result in security_checks:
                if not check_result:
                    logger.warning(f"⚠️ Falha na verificação {check_name} para mensagem {message_index} do usuário {username}")
                    return None
            
            # Sanitizar conteúdo
            sanitized_content = self._sanitize_message_content(content, username)
            
            # Validar resultado final
            if len(sanitized_content.strip()) < 1:
                logger.warning(f"⚠️ Conteúdo vazio após sanitização para {username}")
                return None
            
            return sanitized_content
            
        except Exception as e:
            logger.error(f"❌ Erro ao sanitizar conteúdo para {username}: {e}")
            return None
    
    def _check_for_user_references(self, content: str, username: str) -> Tuple[str, bool]:
        """
        Verificar se há referências a outros usuários no conteúdo
        """
        try:
            content_lower = content.lower()
            
            # Padrões suspeitos de referências a outros usuários
            suspicious_patterns = [
                r'\busername[:\s]+\w+',
                r'\buser[:\s]+\w+', 
                r'\bsession[:\s]+\w+_\w+',
                r'\b\w+_session-\d+',
                r'\btoken[:\s]+\w+',
                r'\bauth[:\s]+\w+',
                r'\bcookie[:\s]+\w+'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, content_lower):
                    # Verificar se não é uma referência legítima ao próprio usuário
                    if username.lower() not in content_lower:
                        return ("user_references", False)
            
            return ("user_references", True)
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar referências de usuário: {e}")
            return ("user_references", False)
    
    def _check_for_sensitive_data(self, content: str) -> Tuple[str, bool]:
        """
        Verificar se há dados sensíveis no conteúdo
        """
        try:
            content_lower = content.lower()
            
            # Padrões de dados sensíveis
            sensitive_patterns = [
                r'\bpassword[:\s]+\w+',
                r'\bpasswd[:\s]+\w+',
                r'\bapi[_\s]key[:\s]+\w+',
                r'\btoken[:\s]+[a-zA-Z0-9]{20,}',
                r'\bsecret[:\s]+\w+',
                r'\bcpf[:\s]+\d{11}',
                r'\bcnpj[:\s]+\d{14}',
                r'\bemail[:\s]+\w+@\w+\.\w+',
                r'\bphone[:\s]+\d{10,}',
                r'\btelefone[:\s]+\d{10,}'
            ]
            
            for pattern in sensitive_patterns:
                if re.search(pattern, content_lower):
                    return ("sensitive_data", False)
            
            return ("sensitive_data", True)
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar dados sensíveis: {e}")
            return ("sensitive_data", False)
    
    def _check_content_length(self, content: str) -> Tuple[str, bool]:
        """
        Verificar se o conteúdo tem tamanho adequado
        """
        try:
            # Limites de tamanho
            MIN_LENGTH = 1
            MAX_LENGTH = 5000
            
            if len(content) < MIN_LENGTH:
                return ("content_length", False)
            
            if len(content) > MAX_LENGTH:
                return ("content_length", False)
            
            return ("content_length", True)
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar tamanho do conteúdo: {e}")
            return ("content_length", False)
    
    def _check_for_malicious_content(self, content: str) -> Tuple[str, bool]:
        """
        Verificar se há conteúdo malicioso
        """
        try:
            content_lower = content.lower()
            
            # Padrões maliciosos
            malicious_patterns = [
                r'<script[^>]*>.*?</script>',  # JavaScript
                r'javascript:',
                r'vbscript:',
                r'onload\s*=',
                r'onerror\s*=',
                r'onclick\s*=',
                r'eval\s*\(',
                r'exec\s*\(',
                r'system\s*\(',
                r'shell\s*\(',
                r'import\s+os',
                r'import\s+sys',
                r'__import__'
            ]
            
            for pattern in malicious_patterns:
                if re.search(pattern, content_lower):
                    return ("malicious_content", False)
            
            return ("malicious_content", True)
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar conteúdo malicioso: {e}")
            return ("malicious_content", False)
    
    def _check_for_system_commands(self, content: str) -> Tuple[str, bool]:
        """
        Verificar se há comandos de sistema no conteúdo
        """
        try:
            content_lower = content.lower()
            
            # Comandos de sistema suspeitos
            system_commands = [
                r'\brm\s+-rf',
                r'\bsudo\s+',
                r'\bchmod\s+',
                r'\bchown\s+',
                r'\bkill\s+',
                r'\bpkill\s+',
                r'\bps\s+',
                r'\bnetstat\s+',
                r'\bwget\s+',
                r'\bcurl\s+',
                r'\bcat\s+/etc/',
                r'\bls\s+/',
                r'\bfind\s+/',
                r'\bgrep\s+.*passwd',
                r'\bgrep\s+.*shadow'
            ]
            
            for pattern in system_commands:
                if re.search(pattern, content_lower):
                    return ("system_commands", False)
            
            return ("system_commands", True)
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar comandos de sistema: {e}")
            return ("system_commands", False)
    
    def _sanitize_message_content(self, content: str, username: str) -> str:
        """
        Sanitizar conteúdo da mensagem para remover dados sensíveis
        """
        try:
            # Remover possíveis referências a outros usuários
            # Isso é uma implementação básica - pode ser expandida conforme necessário
            
            # Limitar tamanho da mensagem
            if len(content) > 2000:
                content = content[:2000] + "..."
                logger.warning(f"⚠️ Mensagem truncada para {username} (muito longa)")
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"❌ Erro ao sanitizar conteúdo: {e}")
            return content[:500]  # Fallback seguro
    
    async def _create_system_prompt(self, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Criar prompt do sistema para o psicólogo Rogers
        Busca do banco de dados através do PromptClientService
        """
        try:
            # Buscar prompt do banco de dados
            system_prompt = await self.prompt_client.get_system_prompt(variables)
            
            if system_prompt:
                logger.info("✅ Prompt de sistema carregado do banco de dados")
                return self._normalize_system_prompt_for_runtime(system_prompt)
            else:
                logger.warning("⚠️ Usando prompt de sistema fallback")
                return self._get_fallback_system_prompt()
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar prompt de sistema: {e}")
            return self._get_fallback_system_prompt()
    
    def _get_fallback_system_prompt(self) -> str:
        """Prompt de sistema Dr. Rogers — carregado do arquivo, com literal embutido de última instância."""
        if self.local_openai_compatible:
            if _SYSTEM_ROGERS_LOCAL_PROMPT:
                return _SYSTEM_ROGERS_LOCAL_PROMPT
            return (
                "Você é o Dr. Rogers, um psicólogo virtual acolhedor em português brasileiro. "
                "Use escuta ativa, valide emoções, responda com brevidade e faça no máximo uma pergunta aberta. "
                "Evite listas, diagnósticos e respostas longas. Em risco imediato, priorize segurança e orientação urgente."
            )
        if _SYSTEM_ROGERS_PROMPT:
            return _SYSTEM_ROGERS_PROMPT
        # literal mínimo de emergência caso o arquivo não exista
        return (
            "Você é o Dr. Rogers, um psicólogo virtual empático e acolhedor. "
            "Responda sempre em português brasileiro. "
            "Priorize escuta ativa, segurança do usuário e respeito à autonomia."
        )

    def _normalize_system_prompt_for_runtime(self, system_prompt: str) -> str:
        """Swap in a compact local prompt when using a local OpenAI-compatible runtime."""
        if self.local_openai_compatible:
            return _SYSTEM_ROGERS_LOCAL_PROMPT or system_prompt
        return system_prompt

    @staticmethod
    def _compact_context_block(text: str, max_chars: int) -> str:
        """Reduce verbose profile/session context for smaller local models."""
        if not text:
            return ""

        filtered_lines: List[str] = []
        skip_markers = (
            "username:",
            "identificador técnico",
            "timestamp:",
            "sessão:",
            "session_id",
        )
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            lower_line = line.lower()
            if any(marker in lower_line for marker in skip_markers):
                continue
            filtered_lines.append(line)

        compact = "\n".join(filtered_lines).strip()
        if len(compact) <= max_chars:
            return compact

        truncated = compact[:max_chars].rsplit("\n", 1)[0].rstrip()
        if not truncated:
            truncated = compact[:max_chars].rstrip()
        return f"{truncated}\n[contexto resumido]"
    
    async def _create_conversation_context(self, session_id: str, username: str, user_message: str, conversation_history: Optional[List[Dict]] = None, session_objective: Optional[Dict[str, Any]] = None, initial_prompt: Optional[str] = None, previous_session_context: Optional[Dict[str, Any]] = None, is_voice_mode: bool = False) -> List[Dict]:
        """
        Criar contexto da conversa para o OpenAI com otimização de tokens e isolamento por usuário
        """
        # Criar prompt do sistema baseado no objetivo da sessão
        system_prompt = await self._create_system_prompt()
        
        # 🔍 Log inicial
        logger.info(f"🎯 Criando contexto para sessão {session_id} (usuário: {username})")
        
        # ✅ NOVO: Processar contexto da sessão anterior se disponível
        previous_session_info = ""
        if previous_session_context:
            logger.info(f"🔗 Contexto da sessão anterior encontrado para {username}")
            
            # ✅ NOVO: Extrair e cachear dados do usuário automaticamente
            if previous_session_context.get("registration_data"):
                auto_profile = {
                    "username": username,
                    "registration_data": previous_session_context["registration_data"]
                }
                self.cache_user_profile(username, auto_profile)
                logger.info(f"🔄 Dados do usuário extraídos e cacheados automaticamente do contexto anterior")
            
            # ✅ CONTEXTO CUMULATIVO OTIMIZADO: combinar contexto anterior + conversa atual
            if conversation_history:
                logger.info(f"🔄 Criando contexto cumulativo: anterior + atual ({len(conversation_history)} mensagens)")
                previous_session_info = self._create_cumulative_context(
                    previous_session_context, 
                    conversation_history, 
                    username
                )
            else:
                # Se não há conversa atual, usar apenas contexto anterior
                previous_session_info = self._format_previous_session_context(previous_session_context)
        
        # ✅ NOVO: Reobter perfil do usuário (pode ter sido atualizado pelo previous_session_context)
        user_profile_context = self._get_user_profile_context(username)
        cached_profile = self._get_cached_user_profile(username) or {}
        preferred_display_name = (
            cached_profile.get("preferred_name")
            or cached_profile.get("display_name")
            or cached_profile.get("full_name")
            or (cached_profile.get("preferences") or {}).get("display_name")
            or (cached_profile.get("preferences") or {}).get("full_name")
        )
        display_name = preferred_display_name or "não informado"
        first_name = self._extract_first_name(preferred_display_name) if preferred_display_name else None
        if preferred_display_name:
            treatment_name = first_name or display_name
            identity_instruction = (
                f"Você está conversando especificamente com {display_name}.\n"
                f"Se for chamar o usuário pelo nome, use somente o primeiro nome: {treatment_name}.\n"
                "Não use sobrenomes, nome completo, e-mail/username ou identificadores técnicos como forma de tratamento."
            )
        else:
            identity_instruction = (
                "O nome preferido do usuário não foi informado.\n"
                "Não use o username, e-mail, id de sessão ou identificador técnico como forma de tratamento."
            )
        
        # ✅ NOVO: Adicionar informações do usuário ao contexto
        user_context = f"""
INFORMAÇÕES DO USUÁRIO:
- Username: {username}
- Nome preferido: {display_name}
- Nome para tratamento: {first_name or "não informado"}
- Sessão: {session_id}
- Timestamp: {datetime.now().isoformat()}

{user_profile_context}

{previous_session_info}

IMPORTANTE: {identity_instruction}
Mantenha a conversa personalizada e contextualizada para este usuário.
Use as informações do perfil e das sessões anteriores para personalizar sua abordagem terapêutica.
PRIORIZE sempre as informações mais recentes e relevantes do contexto cumulativo.
"""
        
        # Se há initial_prompt fornecido diretamente, usá-lo (tem prioridade)
        if initial_prompt:
            logger.info(f"📋 INITIAL_PROMPT encontrado para sessão {session_id} (usuário: {username})")
            logger.info(f"📝 Conteúdo do initial_prompt: {initial_prompt[:200]}{'...' if len(initial_prompt) > 200 else ''}")
            
            enhanced_prompt = f"""
{user_context}

INSTRUÇÕES ESPECÍFICAS PARA ESTA SESSÃO:
{initial_prompt}

{system_prompt}
"""
            system_prompt = enhanced_prompt
            logger.info(f"✅ Prompt do sistema ENHANCED com initial_prompt para sessão {session_id} (usuário: {username})")
            
        # Se há objetivo da sessão, incorporá-lo no prompt do sistema
        elif session_objective:
            logger.info(f"🎯 SESSION_OBJECTIVE encontrado para sessão {session_id} (usuário: {username})")
            logger.info(f"📋 Título: {session_objective.get('title', 'N/A')}")
            logger.info(f"📋 Subtítulo: {session_objective.get('subtitle', 'N/A')}")
            logger.info(f"📋 Objetivo: {session_objective.get('objective', 'N/A')[:100]}{'...' if len(session_objective.get('objective', '')) > 100 else ''}")
            
            if session_objective.get('initial_prompt'):
                logger.info(f"📝 Conteúdo do initial_prompt do objective: {session_objective.get('initial_prompt')[:200]}{'...' if len(session_objective.get('initial_prompt', '')) > 200 else ''}")
            
            objective_text = f"""
{user_context}

OBJETIVO DESTA SESSÃO:
Título: {session_objective.get('title', 'Sessão Terapêutica')}
Subtitle: {session_objective.get('subtitle', '')}
Objetivo: {session_objective.get('objective', '')}

INSTRUÇÕES ESPECÍFICAS PARA ESTA SESSÃO:
{session_objective.get('initial_prompt', '')}

{system_prompt}
"""
            system_prompt = objective_text
            logger.info(f"✅ Prompt do sistema ENHANCED com session_objective para sessão {session_id} (usuário: {username})")
            
        else:
            logger.info(f"📄 Usando prompt do sistema PADRÃO para sessão {session_id} (usuário: {username})")
            system_prompt = f"""
{user_context}

{system_prompt}
"""
        
        if is_voice_mode:
            voice_prompt = await self._get_voice_short_response_prompt()
            system_prompt = f"{system_prompt}\n\n{voice_prompt}"
            logger.info("🎙️ Prompt de resposta curta para voz aplicado")

        # 🔍 Log do prompt do sistema completo (truncado para não poluir logs)
        logger.info(f"🤖 PROMPT DO SISTEMA (primeiros 300 caracteres): {system_prompt[:300]}{'...' if len(system_prompt) > 300 else ''}")
        
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Processar histórico com otimizações
        if conversation_history:
            logger.info(f"📚 Processando histórico: {len(conversation_history)} mensagens originais para {username}")
            
            # ✅ OTIMIZAÇÃO: Se há contexto cumulativo, incluir apenas as últimas mensagens
            if previous_session_context and len(conversation_history) > 4:
                # Com contexto cumulativo, manter apenas as últimas 4 mensagens (contexto recente)
                optimized_history = conversation_history[-4:]
                logger.info(f"🔄 Contexto cumulativo ativo: usando apenas últimas 4 mensagens para evitar redundância")
            else:
                # Sem contexto cumulativo, usar otimização padrão
                optimized_history = self._optimize_conversation_history(conversation_history)
            
            logger.info(f"📚 Após otimização: {len(optimized_history)} mensagens para {username}")
            
            for msg in optimized_history:
                role = "user" if msg.get("type") == "user" else "assistant"
                content = msg.get("content", "")
                if content.strip():
                    messages.append({"role": role, "content": content})
        else:
            logger.info(f"📄 Nenhum histórico fornecido para sessão {session_id} (usuário: {username})")
        
        # Adicionar mensagem atual
        logger.info(f"💬 Mensagem do usuário {username}: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
        messages.append({"role": "user", "content": user_message})
        
        # Log do tamanho do contexto
        total_tokens = self._estimate_tokens(messages)
        logger.info(f"📊 Contexto FINAL para {username}: {len(messages)} mensagens, ~{total_tokens} tokens")
        
        # 🔍 Log resumo das mensagens que serão enviadas para OpenAI
        logger.info(f"📤 RESUMO ENVIADO PARA OPENAI (usuário: {username}):")
        for i, msg in enumerate(messages):
            role = msg["role"]
            content_preview = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
            logger.info(f"  [{i+1}] {role.upper()}: {content_preview}")
        
        return messages

    async def _get_voice_short_response_prompt(self) -> str:
        """Prompt para respostas de voz curtas — banco de dados com fallback em arquivo."""
        try:
            prompt_data = await self.prompt_client.get_prompt("voice_short_response")
            content = (prompt_data or {}).get("content")
            if content:
                return content
        except Exception as exc:
            logger.warning("⚠️ Não foi possível carregar voice_short_response do Gateway: %s", exc)

        return _VOICE_SHORT_PROMPT or (
            "MODO DE VOZ ATIVO:\n"
            "- Responda em português brasileiro natural, como fala acolhedora.\n"
            "- Use 2 a 4 frases curtas, sem listas.\n"
            "- Faça no máximo uma pergunta aberta.\n"
            "- Em crise ou risco imediato, priorize segurança e orientação urgente."
        )

    def _extract_first_name(self, display_name: Optional[str]) -> Optional[str]:
        """Return a natural first-name treatment token from a preferred display name."""
        if not display_name:
            return None

        cleaned = str(display_name).strip()
        if not cleaned or "@" in cleaned:
            return None

        first_token = cleaned.split()[0].strip(".,;:()[]{}\"'")
        if any(char.isdigit() for char in first_token):
            return None
        return first_token or None
    
    def _optimize_conversation_history(self, history: List[Dict]) -> List[Dict]:
        """
        Otimizar histórico de conversa para reduzir tokens
        """
        if not history:
            return []
        
        # Limitar número de mensagens
        limited_history = history[-self.max_history_messages:]
        
        # Se habilitado, comprimir contexto longo
        if self.enable_context_compression and len(history) > self.max_history_messages:
            compressed_history = self._compress_long_conversation(history)
            return compressed_history[-self.max_history_messages:]
        
        return limited_history
    
    def _compress_long_conversation(self, history: List[Dict]) -> List[Dict]:
        """
        Comprimir conversa longa mantendo contexto essencial
        """
        if len(history) <= self.max_history_messages:
            return history
        
        # Manter primeiras mensagens (contexto inicial)
        initial_context = history[:2]
        
        # Manter últimas mensagens (contexto recente)
        recent_context = history[-self.max_history_messages+2:]
        
        # Criar resumo do meio se necessário
        middle_context = []
        if len(history) > self.max_history_messages + 2:
            middle_context = [{
                "type": "assistant",
                "content": f"[Resumo: Conversa anterior com {len(history)-self.max_history_messages} mensagens sobre o mesmo tema]"
            }]
        
        return initial_context + middle_context + recent_context
    
    def _estimate_tokens(self, messages: List[Dict]) -> int:
        """
        Estimar número de tokens (aproximação simples)
        """
        total_chars = 0
        for msg in messages:
            total_chars += len(msg.get("content", ""))
        
        # Aproximação: 1 token ≈ 4 caracteres
        return total_chars // 4
    
    async def generate_therapeutic_response(
        self, 
        user_message: str, 
        session_id: str,
        username: str,  # ✅ NOVO: Adicionar username obrigatório
        conversation_history: Optional[List[Dict]] = None,
        session_objective: Optional[Dict[str, Any]] = None,
        initial_prompt: Optional[str] = None,
        previous_session_context: Optional[Dict[str, Any]] = None  # ✅ NOVO: Contexto da sessão anterior
    ) -> Dict[str, Any]:
        """
        Gerar resposta terapêutica usando OpenAI com contexto isolado por usuário
        
        Args:
            user_message: Mensagem do usuário
            session_id: ID da sessão
            username: Username do usuário (para isolamento de contexto)
            conversation_history: Histórico da conversa (opcional)
            session_objective: Objetivo da sessão terapêutica (opcional)
            initial_prompt: Prompt inicial específico (opcional)
            
        Returns:
            Dict com resposta e metadados
        """
        try:
            # 🚀 Log inicial da função
            logger.info(f"🚀 INICIANDO GERAÇÃO DE RESPOSTA TERAPÊUTICA")
            logger.info(f"🎯 Session ID: {session_id}")
            logger.info(f"👤 Username: {username}")
            logger.info(f"💬 Mensagem do usuário: {user_message[:150]}{'...' if len(user_message) > 150 else ''}")
            logger.info(f"📚 Histórico fornecido: {'Sim' if conversation_history else 'Não'} ({len(conversation_history) if conversation_history else 0} mensagens)")
            logger.info(f"🎯 Session Objective fornecido: {'Sim' if session_objective else 'Não'}")
            logger.info(f"📋 Initial Prompt fornecido: {'Sim' if initial_prompt else 'Não'}")
            
            logger.debug("previous_session_context presente: %s", bool(previous_session_context))
            
            # ✅ NOVO: Validar propriedade da sessão
            if not self._validate_session_ownership(session_id, username):
                logger.error(f"❌ Tentativa de acesso não autorizado: {username} tentou acessar {session_id}")
                raise ValueError(f"Acesso não autorizado à sessão {session_id}")
            
            # ✅ NOVO: Validar contexto do usuário
            if conversation_history:
                conversation_history = self._validate_user_context(conversation_history, username)
            
            # ✅ NOVO: Rastrear início da sessão
            self._track_user_session(username, session_id, "session_start")
            
            # Criar contexto da conversa com isolamento por usuário
            messages = await self._create_conversation_context(
                session_id, 
                username,  # ✅ NOVO: Passar username
                user_message, 
                conversation_history, 
                session_objective, 
                initial_prompt,
                previous_session_context  # ✅ NOVO: Passar contexto da sessão anterior
            )
            
            # Fazer chamada para o provedor LLM configurado
            logger.info(f"📡 Enviando requisição para cadeia de provedores {self._provider_order()} com {len(messages)} mensagens")
            
            # ✅ NOVO: Rastrear mensagem do usuário
            self._track_user_session(username, session_id, "message")
            
            llm_result = await self._call_llm(messages)
            
            if llm_result:
                response = llm_result["content"]
                provider = llm_result["provider"]
                model = llm_result["model"]
                logger.info(f"✅ Resposta recebida do provedor {provider}: {response[:100]}{'...' if len(response) > 100 else ''}")
                
                # ✅ NOVO: Rastrear resposta bem-sucedida
                self._track_user_session(username, session_id, "response_success")
                
                # ✅ NOVO: Limpar dados antigos de tracking periodicamente
                self._cleanup_old_tracking_data()
                
                return {
                    "response": response,
                    "model": model,
                    "session_id": session_id,
                    "username": username,  # ✅ NOVO: Incluir username na resposta
                    "timestamp": datetime.now().isoformat(),
                    "provider": provider,
                    "success": True
                }
            else:
                logger.error("❌ Falha ao obter resposta dos provedores LLM")
                # ✅ NOVO: Rastrear falha
                self._track_user_session(username, session_id, "response_failure")
                self._track_user_session(username, session_id, "fallback_used")
                return await self._fallback_response(user_message, username)
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resposta terapêutica: {e}")
            return await self._fallback_response(user_message, username)
    
    async def _call_llm(
        self,
        messages: List[Dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Optional[Dict[str, str]]:
        """Fazer chamada para a cadeia configurada de endpoints OpenAI-compatible."""
        for provider in self._provider_order():
            if not self._provider_available(provider):
                logger.warning(f"⚠️ Provedor {provider} indisponível; tentando próximo")
                continue

            if provider in {"openai", "local"}:
                content = await self._call_openai(messages, max_tokens, temperature)
                model = self.openai_model
            else:
                logger.warning(f"⚠️ Provedor desconhecido ignorado: {provider}")
                continue

            if content:
                return {
                    "content": content,
                    "provider": provider,
                    "model": model,
                }

            logger.warning(f"⚠️ Provedor {provider} não retornou conteúdo; tentando próximo")

        return None

    async def generate_therapeutic_response_stream(
        self,
        user_message: str,
        session_id: str,
        username: str,
        conversation_history: Optional[List[Dict]] = None,
        session_objective: Optional[Dict[str, Any]] = None,
        initial_prompt: Optional[str] = None,
        previous_session_context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        is_voice_mode: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream therapeutic response deltas while preserving provider fallbacks."""
        started_at = time.perf_counter()

        try:
            if not self._validate_session_ownership(session_id, username):
                raise ValueError(f"Acesso não autorizado à sessão {session_id}")

            if conversation_history:
                conversation_history = self._validate_user_context(conversation_history, username)

            self._track_user_session(username, session_id, "message")

            messages = await self._create_conversation_context(
                session_id,
                username,
                user_message,
                conversation_history,
                session_objective,
                initial_prompt,
                previous_session_context,
                is_voice_mode=is_voice_mode,
            )

            max_tokens = self.voice_max_tokens if is_voice_mode else self.max_tokens
            full_response = ""
            provider_used = "fallback"
            model_used = "fallback"
            first_delta_ms: Optional[int] = None

            async for chunk in self._call_llm_stream(messages, max_tokens=max_tokens, temperature=self.temperature):
                if chunk.get("type") == "delta":
                    delta = chunk.get("content", "")
                    if not delta:
                        continue
                    if first_delta_ms is None:
                        first_delta_ms = int((time.perf_counter() - started_at) * 1000)
                    full_response += delta
                    provider_used = chunk.get("provider", provider_used)
                    model_used = chunk.get("model", model_used)
                    yield {
                        "event": "text_delta",
                        "data": {
                            "delta": delta,
                            "trace_id": trace_id,
                            "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
                        },
                    }
                elif chunk.get("type") == "meta":
                    provider_used = chunk.get("provider", provider_used)
                    model_used = chunk.get("model", model_used)

            if not full_response.strip():
                fallback = await self._fallback_response(user_message, username, conversation_history)
                full_response = fallback.get("response", "")
                provider_used = fallback.get("provider", "fallback")
                model_used = fallback.get("model", "fallback")
                yield {
                    "event": "text_delta",
                    "data": {
                        "delta": full_response,
                        "trace_id": trace_id,
                        "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
                    },
                }

            self._track_user_session(username, session_id, "response_success")
            yield {
                "event": "done",
                "data": {
                    "response": full_response.strip(),
                    "model": model_used,
                    "provider": provider_used,
                    "session_id": session_id,
                    "username": username,
                    "trace_id": trace_id,
                    "metrics": {
                        "ai_total_ms": int((time.perf_counter() - started_at) * 1000),
                        "ai_first_delta_ms": first_delta_ms,
                    },
                    "success": True,
                },
            }
        except Exception as exc:
            logger.error("❌ Erro no streaming terapêutico: %s", exc, exc_info=True)
            self._track_user_session(username, session_id, "response_failure")
            fallback = await self._fallback_response(user_message, username, conversation_history)
            response_text = fallback.get("response", "Desculpe, estou com dificuldades técnicas. Pode repetir sua mensagem?")
            yield {
                "event": "text_delta",
                "data": {
                    "delta": response_text,
                    "trace_id": trace_id,
                    "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
                },
            }
            yield {
                "event": "done",
                "data": {
                    "response": response_text,
                    "model": fallback.get("model", "fallback"),
                    "provider": fallback.get("provider", "fallback"),
                    "session_id": session_id,
                    "username": username,
                    "trace_id": trace_id,
                    "metrics": {"ai_total_ms": int((time.perf_counter() - started_at) * 1000)},
                    "success": True,
                },
            }

    async def _call_llm_stream(
        self,
        messages: List[Dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Stream from configured OpenAI-compatible providers when possible."""
        for provider in self._provider_order():
            if not self._provider_available(provider):
                logger.warning("⚠️ Provedor %s indisponível no streaming; tentando próximo", provider)
                continue

            if provider in {"openai", "local"}:
                yielded = False
                async for delta in self._call_openai_stream(messages, max_tokens, temperature):
                    yielded = True
                    yield {
                        "type": "delta",
                        "content": delta,
                        "provider": provider,
                        "model": self.openai_model,
                    }
                if yielded:
                    return

                logger.warning(
                    "⚠️ Streaming do provedor %s não retornou conteúdo visível; tentando fallback interno non-stream",
                    provider,
                )
                content = await self._call_openai(messages, max_tokens, temperature)
                if content:
                    yield {
                        "type": "delta",
                        "content": content,
                        "provider": provider,
                        "model": self.openai_model,
                    }
                    return

        return

    async def _call_openai_stream(
        self,
        messages: List[Dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream token deltas from OpenAI Chat Completions."""
        if not self.client or not OPENAI_AVAILABLE:
            return

        def _create_stream():
            return self.client.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                stream=True,
                timeout=self.request_timeout_seconds,
            )

        try:
            stream = await asyncio.to_thread(_create_stream)
            iterator = iter(stream)
            sentinel = object()

            def _next_chunk():
                try:
                    return next(iterator)
                except StopIteration:
                    return sentinel

            while True:
                chunk = await asyncio.to_thread(_next_chunk)
                if chunk is sentinel:
                    break
                if not getattr(chunk, "choices", None):
                    continue
                delta = getattr(chunk.choices[0], "delta", None)
                content = getattr(delta, "content", None)
                if content:
                    yield content
                    continue

                reasoning_content = getattr(delta, "reasoning_content", None)
                if reasoning_content:
                    logger.debug("Streaming retornou apenas reasoning_content; aguardando conteúdo final visível")
        except Exception as exc:
            logger.error("❌ ERRO no streaming OpenAI: %s", exc)
            return

    async def _call_openai(
        self,
        messages: List[Dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Optional[str]:
        """
        Fazer chamada para API da OpenAI
        """
        if not self.client or not OPENAI_AVAILABLE:
            logger.warning("⚠️ Cliente OpenAI não disponível")
            return None
            
        try:
            # 🔍 Log detalhado da chamada OpenAI
            logger.info(f"🤖 CHAMADA PARA API OPENAI:")
            logger.info(f"   Modelo: {self.openai_model}")
            logger.info(f"   Max Tokens: {max_tokens or self.max_tokens}")
            logger.info(f"   Temperatura: {temperature if temperature is not None else self.temperature}")
            logger.info(f"   Número de mensagens: {len(messages)}")
            
            # Log do sistema prompt (mais detalhado se necessário)
            if messages and len(messages) > 0 and messages[0]["role"] == "system":
                system_content = messages[0]["content"]
                logger.info(f"🎯 SYSTEM PROMPT (primeiros 500 chars): {system_content[:500]}{'...' if len(system_content) > 500 else ''}")
            
            def _create_completion():
                return self.client.chat.completions.create(
                    model=self.openai_model,
                    messages=messages,
                    max_tokens=max_tokens or self.max_tokens,
                    temperature=temperature if temperature is not None else self.temperature,
                    timeout=self.request_timeout_seconds,
                )

            response = await asyncio.to_thread(_create_completion)
            
            if response.choices and len(response.choices) > 0:
                ai_response = response.choices[0].message.content.strip()
                logger.info(f"✅ SUCESSO na chamada OpenAI")
                logger.info(f"📊 Tokens usados: prompt={getattr(response.usage, 'prompt_tokens', 'N/A')}, completion={getattr(response.usage, 'completion_tokens', 'N/A')}, total={getattr(response.usage, 'total_tokens', 'N/A')}")
                logger.info(f"🤖 Resposta da IA (primeiros 200 chars): {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}")
                return ai_response
            else:
                logger.warning("⚠️ OpenAI retornou resposta vazia")
                return None
                
        except Exception as e:
            logger.error(f"❌ ERRO na chamada OpenAI: {e}")
            if openai and hasattr(openai, 'RateLimitError') and isinstance(e, openai.RateLimitError):
                logger.error("❌ Rate limit da OpenAI atingido")
            elif openai and hasattr(openai, 'APIError') and isinstance(e, openai.APIError):
                logger.error(f"❌ Erro da API OpenAI: {e}")
            else:
                logger.error(f"❌ Erro inesperado na chamada OpenAI: {e}")
            return None
    
    async def _fallback_response(self, user_message: str, username: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Resposta de fallback quando OpenAI não está disponível
        Busca respostas do banco de dados via PromptClientService
        """
        try:
            message_lower = user_message.lower()
            
            # Padrões de reconhecimento (mantidos da implementação atual)
            greeting_patterns = ['oi', 'olá', 'hello', 'hi', 'bom dia', 'boa tarde', 'boa noite']
            sadness_patterns = ['triste', 'deprimido', 'depressão', 'mal', 'ruim', 'pessimo', 'horrível']
            anxiety_patterns = ['ansioso', 'ansiedade', 'nervoso', 'preocupado', 'estressado', 'tenso']
            anger_patterns = ['raiva', 'irritado', 'bravo', 'furioso', 'chateado']
            gratitude_patterns = ['obrigado', 'obrigada', 'valeu', 'thanks', 'thank you']
            goodbye_patterns = ['tchau', 'bye', 'adeus', 'até logo', 'até mais']
            
            # Determinar tipo de padrão e buscar resposta do banco
            pattern_type = None
            
            if any(pattern in message_lower for pattern in greeting_patterns):
                pattern_type = "greeting"
            elif any(pattern in message_lower for pattern in sadness_patterns):
                pattern_type = "sadness"
            elif any(pattern in message_lower for pattern in anxiety_patterns):
                pattern_type = "anxiety"
            elif any(pattern in message_lower for pattern in anger_patterns):
                pattern_type = "anger"
            elif any(pattern in message_lower for pattern in gratitude_patterns):
                pattern_type = "gratitude"
            elif any(pattern in message_lower for pattern in goodbye_patterns):
                pattern_type = "goodbye"
            else:
                pattern_type = "default"
            
            # Buscar resposta do banco de dados
            if pattern_type:
                response = await self.prompt_client.get_fallback_response(pattern_type)
                
                if response:
                    logger.info(f"✅ Resposta de fallback carregada do banco: {pattern_type}")
                else:
                    # Fallback para resposta hardcoded
                    response = self._get_hardcoded_fallback_response(pattern_type)
                    logger.warning(f"⚠️ Usando resposta de fallback hardcoded: {pattern_type}")
            else:
                response = self._get_hardcoded_fallback_response("default")
            
            # Evitar repetir a última resposta da IA
            if conversation_history:
                last_ai_messages = [
                    msg.get("content", "") for msg in conversation_history
                    if msg.get("type") in ("ai", "assistant")
                ]
                if last_ai_messages and last_ai_messages[-1].strip() == response.strip():
                    logger.warning(f"⚠️ Fallback evitando repetição para {username} - usando resposta default")
                    response = self._get_hardcoded_fallback_response("default")
            
            return {
                "response": response,
                "model": "fallback",
                "session_id": "default",
                "username": username, # ✅ NOVO: Incluir username na resposta de fallback
                "timestamp": datetime.now().isoformat(),
                "provider": "fallback",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resposta de fallback: {e}")
            # Fallback de emergência
            response = "Obrigado por compartilhar isso comigo. É importante que você tenha confiança para falar sobre seus sentimentos."
            
            return {
                "response": response,
                "model": "fallback_emergency",
                "session_id": "default",
                "username": username,
                "timestamp": datetime.now().isoformat(),
                "provider": "fallback",
                "success": True
            }
    
    def _get_hardcoded_fallback_response(self, pattern_type: str) -> str:
        """Respostas de fallback — carregadas de fallbacks.json com literal mínimo de emergência."""
        responses = _FALLBACK_RESPONSES or {
            "default": "Obrigado por compartilhar isso comigo. Pode me contar mais sobre como isso afeta seu dia a dia?"
        }
        return responses.get(pattern_type, responses.get("default", "Estou aqui para ouvir. Como posso ajudar?"))
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Retornar status do serviço OpenAI
        """
        return {
            "openai_configured": self.client is not None,
            "provider": self.primary_provider,
            "active_provider": self._active_provider(),
            "active_mode": self._active_mode_label(),
            "primary_provider": self.primary_provider,
            "fallback_provider": self.fallback_provider,
            "provider_order": self._provider_order(),
            "model": self.openai_model,
            "active_model": self.openai_model,
            "openai_model": self.openai_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "request_timeout_seconds": self.request_timeout_seconds,
            "api_key_present": bool(self.api_key),
            "effective_api_key_present": bool(self.effective_api_key),
            "openai_base_url": self.openai_base_url,
            "local_available": False,
            "local_file_available": False,
            "local_runtime_loadable": False,
            "local_load_error": None,
            "openai_available": self._provider_available("openai"),
            "local_llm": None,
            "local_model_path": None,
            "context_optimization": {
                "max_history_messages": self.max_history_messages,
                "max_context_tokens": self.max_context_tokens,
                "enable_compression": self.enable_context_compression
            }
        }

    async def generate_session_context(self, conversation_text: str, emotions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gerar contexto estruturado da sessão incluindo resumo e análise
        """
        try:
            # Processar dados de emoções
            emotion_summary = self._process_emotions_data(emotions_data)

            llm_result = None

            if self.local_openai_compatible:
                llm_result = await self._generate_session_context_local(
                    conversation_text,
                    emotion_summary,
                )
            else:
                # Buscar prompt para análise de contexto do banco de dados
                context_prompt = await self.prompt_client.get_session_analysis_prompt({
                    "conversation_text": conversation_text,
                    "emotion_summary": emotion_summary
                })

                if not context_prompt:
                    logger.warning("⚠️ Usando prompt de análise de sessão do arquivo local")
                    template = _SESSION_ANALYSIS_TMPL or (
                        "Analise a conversa terapêutica abaixo e retorne um JSON com: "
                        "summary, main_themes, emotional_state, key_insights, therapeutic_progress, "
                        "next_session_recommendations, risk_indicators, session_quality.\n\n"
                        "CONVERSA:\n{conversation_text}\n\nDADOS EMOCIONAIS:\n{emotion_summary}\n\n"
                        "IMPORTANTE: Retorne apenas o JSON, sem texto adicional."
                    )
                    emotion_summary_str = json.dumps(emotion_summary, ensure_ascii=False)
                    context_prompt = _render_prompt_template(
                        template,
                        conversation_text=conversation_text,
                        emotion_summary=emotion_summary_str,
                    )

                llm_result = await self._call_llm(
                    [
                        {"role": "system", "content": "Você é um especialista em análise de conversas terapêuticas. Sempre responda em JSON válido."},
                        {"role": "user", "content": context_prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3,
                )

            if not llm_result:
                raise RuntimeError("Nenhum provedor LLM disponível para gerar contexto da sessão")

            result = llm_result["content"]
            context_data = _extract_json_payload(result)
            if not context_data:
                raise ValueError("LLM retornou contexto de sessão em JSON inválido")

            context_data = self._normalize_session_context_payload(context_data, emotion_summary)
            self._validate_session_context(context_data)
            return context_data

        except Exception as e:
            logger.error(f"❌ Erro ao gerar contexto da sessão: {e}")
            raise

    async def _generate_session_context_local(
        self,
        conversation_text: str,
        emotion_summary: Dict[str, Any],
    ) -> Optional[Dict[str, str]]:
        """Use a compact schema and shorter conversation window for local runtimes."""
        compact_conversation = self._compact_session_conversation_for_local_analysis(
            conversation_text,
            max_chars=self.local_session_analysis_chars,
        )
        emotion_summary_str = json.dumps(emotion_summary, ensure_ascii=False)
        prompt_template = _SESSION_ANALYSIS_LOCAL_TMPL or (
            "Analise a conversa abaixo e retorne apenas JSON válido.\n"
            "Resumo curto. Campos: summary, main_themes, emotional_state, key_insights, "
            "next_session_recommendations, therapeutic_notes, future_sessions.\n\n"
            "CONVERSA:\n{conversation_text}\n\nEMOCOES:\n{emotion_summary}"
        )

        prompt = _render_prompt_template(
            prompt_template,
            conversation_text=compact_conversation,
            emotion_summary=emotion_summary_str,
        )

        llm_result = await self._call_llm(
            [
                {
                    "role": "system",
                    "content": (
                        "Você resume sessões terapêuticas em JSON puro. "
                        "Não use markdown, não use crases, não explique, não escreva raciocínio. "
                        "Prefira completar um JSON curto e válido."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=700,
            temperature=0.1,
        )
        if llm_result and _extract_json_payload(llm_result.get("content")):
            return llm_result

        logger.warning("⚠️ Retry local de contexto da sessão com prompt ainda mais compacto")
        retry_prompt = (
            "Retorne APENAS um JSON válido e curto, sem markdown.\n"
            "Use no máximo 2 frases no summary e listas com no máximo 3 itens.\n"
            "Campos obrigatórios: summary, main_themes, emotional_state, key_insights.\n"
            "Campos opcionais: next_session_recommendations, therapeutic_notes, future_sessions.\n\n"
            f"CONVERSA:\n{compact_conversation}\n\n"
            f"EMOCOES:\n{emotion_summary_str}"
        )
        return await self._call_llm(
            [
                {
                    "role": "system",
                    "content": (
                        "Gere imediatamente o JSON final. "
                        "Sem markdown, sem texto fora do JSON, sem raciocínio intermediário."
                    ),
                },
                {"role": "user", "content": retry_prompt},
            ],
            max_tokens=900,
            temperature=0.0,
        )

    def _compact_session_conversation_for_local_analysis(self, conversation_text: str, max_chars: int) -> str:
        """Shrink the conversation before sending it to a smaller local model."""
        lines = []
        for raw_line in conversation_text.splitlines():
            line = re.sub(r"\s+", " ", raw_line.strip())
            if not line:
                continue
            if len(line) > 220:
                line = f"{line[:217].rstrip()}..."
            lines.append(line)

        if len(lines) > 18:
            lines = lines[:6] + ["[trechos intermediários resumidos]"] + lines[-11:]

        compact_text = "\n".join(lines).strip()
        if len(compact_text) <= max_chars:
            return compact_text

        head_chars = max_chars // 2
        tail_chars = max_chars - head_chars - len("\n[trechos omitidos]\n")
        head = compact_text[:head_chars].rstrip()
        tail = compact_text[-tail_chars:].lstrip()
        return f"{head}\n[trechos omitidos]\n{tail}"

    def _normalize_session_context_payload(
        self,
        context_data: Dict[str, Any],
        emotion_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Normalize local-model JSON into the richer internal shape we expect."""
        normalized = dict(context_data or {})

        main_themes = normalized.get("main_themes", [])
        if isinstance(main_themes, str):
            main_themes = [main_themes]
        normalized["main_themes"] = [str(theme).strip() for theme in main_themes if str(theme).strip()]

        key_insights = normalized.get("key_insights", [])
        if isinstance(key_insights, str):
            key_insights = [key_insights]
        normalized["key_insights"] = [str(insight).strip() for insight in key_insights if str(insight).strip()]

        emotional_state = normalized.get("emotional_state")
        if not isinstance(emotional_state, dict):
            emotional_state = {}
        dominant_emotion = (
            emotional_state.get("dominant_emotion")
            or emotional_state.get("final")
            or emotional_state.get("initial")
            or emotion_summary.get("dominant_emotion")
            or "neutro"
        )
        emotional_journey = (
            emotional_state.get("emotional_journey")
            or emotional_state.get("progression")
            or emotional_state.get("journey")
            or "Sem jornada emocional detalhada."
        )
        emotional_state.setdefault("dominant_emotion", dominant_emotion)
        emotional_state.setdefault("emotional_journey", emotional_journey)
        emotional_state.setdefault("stability", emotional_state.get("stability") or "em_transição")
        normalized["emotional_state"] = emotional_state

        recommendations = normalized.get("next_session_recommendations", [])
        if isinstance(recommendations, str):
            recommendations = [recommendations]
        normalized["next_session_recommendations"] = [
            str(item).strip() for item in recommendations if str(item).strip()
        ][:3]

        therapeutic_notes = normalized.get("therapeutic_notes")
        if not isinstance(therapeutic_notes, dict):
            therapeutic_notes = {}
        therapeutic_progress = normalized.get("therapeutic_progress")
        if isinstance(therapeutic_progress, dict):
            engagement_level = therapeutic_progress.get("engagement_level")
            if engagement_level and not therapeutic_notes.get("engagement_level"):
                therapeutic_notes["engagement_level"] = engagement_level
        normalized["therapeutic_notes"] = therapeutic_notes

        future_sessions = normalized.get("future_sessions")
        if not isinstance(future_sessions, dict):
            future_sessions = {}
        if not future_sessions.get("suggested_topics") and normalized["next_session_recommendations"]:
            future_sessions["suggested_topics"] = normalized["next_session_recommendations"][:2]
        normalized["future_sessions"] = future_sessions

        normalized.setdefault("summary", str(normalized.get("summary", "")).strip())
        normalized.setdefault("risk_indicators", [])
        normalized.setdefault("session_quality", "boa")
        return normalized

    def _process_emotions_data(self, emotions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Processar dados de emoções para análise"""
        if not emotions_data:
            return {"dominant_emotion": "neutro", "count": 0, "distribution": {}}
        
        # Agregar emoções
        emotion_counts = {}
        total_detections = len(emotions_data)
        
        for emotion in emotions_data:
            dominant = emotion.get("dominant_emotion", "neutro")
            emotion_counts[dominant] = emotion_counts.get(dominant, 0) + 1
        
        # Encontrar emoção dominante
        dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutro"
        
        return {
            "dominant_emotion": dominant_emotion,
            "count": total_detections,
            "distribution": emotion_counts
        }
    
    def _validate_session_context(self, context_data: Dict[str, Any]) -> None:
        """Fail fast when the LLM did not produce a real structured context."""
        required_fields = ["summary", "main_themes", "emotional_state", "key_insights"]
        missing_fields = [field for field in required_fields if field not in context_data]
        if missing_fields:
            raise ValueError(f"Contexto de sessão incompleto: campos ausentes {missing_fields}")

        if not isinstance(context_data.get("summary"), str) or not context_data["summary"].strip():
            raise ValueError("Contexto de sessão inválido: summary vazio")

        main_themes = context_data.get("main_themes")
        if not isinstance(main_themes, list) or not any(str(theme).strip() for theme in main_themes):
            raise ValueError("Contexto de sessão inválido: main_themes vazio")

        meaningful_themes = [
            theme for theme in main_themes
            if self._is_meaningful_session_theme(theme)
        ]
        if not meaningful_themes:
            raise ValueError("Contexto de sessão inválido: main_themes contém apenas temas genéricos")
        context_data["main_themes"] = meaningful_themes

        if not isinstance(context_data.get("emotional_state"), dict):
            raise ValueError("Contexto de sessão inválido: emotional_state deve ser objeto")

        key_insights = context_data.get("key_insights")
        if not isinstance(key_insights, list) or not any(str(insight).strip() for insight in key_insights):
            raise ValueError("Contexto de sessão inválido: key_insights vazio")

    def _is_meaningful_session_theme(self, theme: Any) -> bool:
        text = str(theme or "").strip().lower()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(char for char in text if not unicodedata.combining(char))
        text = re.sub(r"[^a-z0-9\s-]", " ", text)
        normalized = re.sub(r"\s+", " ", text).strip()

        if not normalized or len(normalized) < 4:
            return False

        if normalized in _GENERIC_SESSION_CONTEXT_THEMES:
            return False

        generic_fragments = (
            "conversa terapeutica",
            "apoio emocional",
            "sessao terapeutica",
            "temas identificados",
            "temas importantes",
        )
        return not any(fragment in normalized for fragment in generic_fragments)

    async def generate_next_session(self, user_profile: Dict[str, Any], session_context: Dict[str, Any], current_session_id: str) -> Dict[str, Any]:
        """
        Gerar próxima sessão terapêutica personalizada baseada no contexto do usuário
        """
        try:
            logger.info(f"🎯 Gerando próxima sessão baseada no contexto de {current_session_id}")
            
            # Criar prompt para gerar a próxima sessão
            session_prompt = await self._create_next_session_prompt(user_profile, session_context, current_session_id)
            
            messages = [
                {"role": "system", "content": "Você é um especialista em terapia que cria sessões terapêuticas personalizadas baseadas no contexto do usuário."},
                {"role": "user", "content": session_prompt}
            ]

            llm_result = await self._call_llm(messages)
            if not llm_result:
                raise RuntimeError("Nenhum provedor LLM disponível para gerar próxima sessão")

            ai_response = llm_result["content"]
            provider = llm_result["provider"]

            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1

            if start_idx < 0 or end_idx <= start_idx:
                raise ValueError("LLM retornou próxima sessão sem JSON válido")

            json_str = ai_response[start_idx:end_idx]
            next_session_data = json.loads(json_str)

            next_session_data.update({
                "generated_at": datetime.now().isoformat(),
                "based_on_session": current_session_id,
                "generation_method": provider,
                "personalized": True
            })

            logger.info(f"✅ Próxima sessão gerada com {provider} para {current_session_id}")
            return next_session_data

        except Exception as e:
            logger.error(f"❌ Erro ao gerar próxima sessão: {e}")
            raise

    async def _create_next_session_prompt(self, user_profile: Dict[str, Any], session_context: Dict[str, Any], current_session_id: str) -> str:
        """
        Criar prompt para gerar a próxima sessão terapêutica
        Busca do banco de dados via PromptClientService
        """
        try:
            # Extrair número da sessão atual
            session_number = self._extract_session_number(current_session_id)
            next_session_number = session_number + 1
            next_session_id = f"session-{next_session_number}"
            
            # Extrair informações relevantes do perfil do usuário
            user_summary = self._extract_user_summary(user_profile)
            
            # Extrair informações relevantes do contexto da sessão
            session_summary = self._extract_session_summary(session_context)
            
            # Buscar prompt do banco de dados
            prompt = await self.prompt_client.get_next_session_prompt({
                "current_session_id": current_session_id,
                "next_session_id": next_session_id,
                "user_summary": user_summary,
                "session_summary": session_summary
            })
            
            if prompt:
                logger.info("✅ Prompt de geração de sessão carregado do banco")
                return prompt
            else:
                # Fallback para prompt hardcoded
                logger.warning("⚠️ Usando prompt de geração de sessão hardcoded")
                return self._get_hardcoded_next_session_prompt(current_session_id, next_session_id, user_summary, session_summary)
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar prompt de geração de sessão: {e}")
            # Fallback para prompt hardcoded
            session_number = self._extract_session_number(current_session_id)
            next_session_number = session_number + 1
            next_session_id = f"session-{next_session_number}"
            user_summary = self._extract_user_summary(user_profile)
            session_summary = self._extract_session_summary(session_context)
            
            return self._get_hardcoded_next_session_prompt(current_session_id, next_session_id, user_summary, session_summary)
    
    def _get_hardcoded_next_session_prompt(self, current_session_id: str, next_session_id: str, user_summary: str, session_summary: str) -> str:
        """Prompt para geração de próxima sessão — arquivo local com fallback mínimo."""
        template = _NEXT_SESSION_TMPL or (
            "Crie a próxima sessão terapêutica ({next_session_id}) baseada no perfil do usuário e contexto anterior. "
            "Retorne apenas JSON com: session_id, title, subtitle, objective, initial_prompt, focus_areas, "
            "therapeutic_approach, expected_outcomes, session_type, estimated_duration, "
            "preparation_notes, connection_to_previous, personalization_factors."
        )
        return template.format(
            current_session_id=current_session_id,
            next_session_id=next_session_id,
            user_summary=user_summary,
            session_summary=session_summary,
        )

    def _extract_session_number(self, session_id: str) -> int:
        """
        Extrair número da sessão do session_id
        """
        try:
            match = re.search(r'session-(\d+)', session_id)
            return int(match.group(1)) if match else 1
        except Exception:
            return 1

    def _extract_user_summary(self, user_profile: Dict[str, Any]) -> str:
        """
        Extrair resumo do perfil do usuário
        """
        try:
            summary_parts = []
            
            # Informações pessoais
            personal_info = user_profile.get("personal_info", {})
            if personal_info.get("idade", {}).get("valor"):
                summary_parts.append(f"Idade: {personal_info['idade']['valor']} anos")
            if personal_info.get("genero", {}).get("categoria"):
                summary_parts.append(f"Gênero: {personal_info['genero']['categoria']}")
            if personal_info.get("localizacao", {}).get("formatted"):
                summary_parts.append(f"Localização: {personal_info['localizacao']['formatted']}")
            
            # Informações sociais
            social_info = user_profile.get("social_info", {})
            if social_info.get("ocupacao", {}).get("content"):
                summary_parts.append(f"Ocupação: {social_info['ocupacao']['content'][:100]}")
            
            # Informações terapêuticas
            therapeutic_info = user_profile.get("therapeutic_info", {})
            if therapeutic_info.get("motivacao_terapia", {}).get("content"):
                summary_parts.append(f"Motivação: {therapeutic_info['motivacao_terapia']['content'][:150]}")
            
            # Objetivos identificados
            objectives = therapeutic_info.get("objetivos_identificados", [])
            if objectives:
                summary_parts.append(f"Objetivos: {', '.join(objectives[:3])}")
            
            return "\n".join(summary_parts) if summary_parts else "Informações limitadas do usuário"
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair resumo do usuário: {e}")
            return "Perfil do usuário indisponível"

    def _extract_session_summary(self, session_context: Dict[str, Any]) -> str:
        """
        Extrair resumo do contexto da sessão
        """
        try:
            summary_parts = []
            
            # Resumo geral
            if session_context.get("summary"):
                summary_parts.append(f"Resumo: {session_context['summary']}")
            
            # Temas principais
            main_themes = session_context.get("main_themes", [])
            if main_themes:
                summary_parts.append(f"Temas principais: {', '.join(main_themes)}")
            
            # Estado emocional
            emotional_state = session_context.get("emotional_state", {})
            if emotional_state.get("dominant_emotion"):
                summary_parts.append(f"Estado emocional: {emotional_state.get('progression', 'N/A')}")
            
            # Insights chave
            key_insights = session_context.get("key_insights", [])
            if key_insights:
                summary_parts.append(f"Insights: {'; '.join(key_insights[:3])}")
            
            # Recomendações para próxima sessão
            recommendations = session_context.get("next_session_recommendations", [])
            if recommendations:
                summary_parts.append(f"Recomendações: {'; '.join(recommendations[:3])}")
            
            return "\n".join(summary_parts) if summary_parts else "Contexto da sessão indisponível"
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair resumo da sessão: {e}")
            return "Contexto da sessão indisponível"

    def _track_user_session(self, username: str, session_id: str, action: str) -> None:
        """
        Rastrear atividade de sessão do usuário
        """
        try:
            if not self.session_tracking_enabled:
                return
                
            current_time = datetime.now().timestamp()
            
            # Inicializar tracking do usuário se não existir
            if username not in self.user_session_tracking:
                self.user_session_tracking[username] = {
                    "sessions": {},
                    "total_sessions": 0,
                    "first_seen": current_time,
                    "last_activity": current_time
                }
            
            user_tracking = self.user_session_tracking[username]
            
            # Inicializar sessão se não existir
            if session_id not in user_tracking["sessions"]:
                user_tracking["sessions"][session_id] = {
                    "created_at": current_time,
                    "last_activity": current_time,
                    "message_count": 0,
                    "actions": []
                }
                user_tracking["total_sessions"] += 1
            
            session_tracking = user_tracking["sessions"][session_id]
            
            # Registrar ação
            session_tracking["actions"].append({
                "action": action,
                "timestamp": current_time
            })
            
            # Atualizar contadores
            if action == "message":
                session_tracking["message_count"] += 1
            
            # Atualizar timestamps
            session_tracking["last_activity"] = current_time
            user_tracking["last_activity"] = current_time
            
            # Limitar histórico de ações (últimas 50)
            if len(session_tracking["actions"]) > 50:
                session_tracking["actions"] = session_tracking["actions"][-50:]
                
            logger.debug(f"📊 Tracking: {username} -> {session_id} -> {action}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao rastrear sessão do usuário: {e}")
    
    def _get_user_session_stats(self, username: str) -> Dict[str, Any]:
        """
        Obter estatísticas de sessões do usuário
        """
        try:
            if not self.session_tracking_enabled or username not in self.user_session_tracking:
                return {
                    "tracking_enabled": self.session_tracking_enabled,
                    "user_found": False,
                    "message": "Usuário não encontrado no tracking"
                }
            
            user_tracking = self.user_session_tracking[username]
            current_time = datetime.now().timestamp()
            
            # Calcular estatísticas
            active_sessions = 0
            total_messages = 0
            
            for session_id, session_data in user_tracking["sessions"].items():
                # Considerar ativa se teve atividade nas últimas 2 horas
                if current_time - session_data["last_activity"] < 7200:
                    active_sessions += 1
                
                total_messages += session_data["message_count"]
            
            return {
                "tracking_enabled": True,
                "user_found": True,
                "username": username,
                "total_sessions": user_tracking["total_sessions"],
                "active_sessions": active_sessions,
                "total_messages": total_messages,
                "first_seen": datetime.fromtimestamp(user_tracking["first_seen"]).isoformat(),
                "last_activity": datetime.fromtimestamp(user_tracking["last_activity"]).isoformat(),
                "session_details": {
                    session_id: {
                        "created_at": datetime.fromtimestamp(data["created_at"]).isoformat(),
                        "last_activity": datetime.fromtimestamp(data["last_activity"]).isoformat(),
                        "message_count": data["message_count"],
                        "recent_actions": data["actions"][-10:]  # Últimas 10 ações
                    }
                    for session_id, data in user_tracking["sessions"].items()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas de sessão: {e}")
            return {
                "tracking_enabled": self.session_tracking_enabled,
                "user_found": False,
                "error": str(e)
            }
    
    def _get_all_users_tracking_stats(self) -> Dict[str, Any]:
        """
        Obter estatísticas de tracking de todos os usuários
        """
        try:
            if not self.session_tracking_enabled:
                return {
                    "tracking_enabled": False,
                    "message": "Session tracking desabilitado"
                }
            
            current_time = datetime.now().timestamp()
            
            # Estatísticas gerais
            total_users = len(self.user_session_tracking)
            active_users = 0
            total_sessions = 0
            total_messages = 0
            
            user_summaries = {}
            
            for username, user_data in self.user_session_tracking.items():
                # Verificar se usuário está ativo (atividade nas últimas 2 horas)
                if current_time - user_data["last_activity"] < 7200:
                    active_users += 1
                
                total_sessions += user_data["total_sessions"]
                
                # Calcular mensagens do usuário
                user_messages = sum(session["message_count"] for session in user_data["sessions"].values())
                total_messages += user_messages
                
                # Resumo do usuário
                user_summaries[username] = {
                    "total_sessions": user_data["total_sessions"],
                    "total_messages": user_messages,
                    "last_activity": datetime.fromtimestamp(user_data["last_activity"]).isoformat(),
                    "active_sessions": len([
                        s for s in user_data["sessions"].values() 
                        if current_time - s["last_activity"] < 7200
                    ])
                }
            
            return {
                "tracking_enabled": True,
                "timestamp": datetime.now().isoformat(),
                "overview": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "total_sessions": total_sessions,
                    "total_messages": total_messages,
                    "average_messages_per_user": total_messages / total_users if total_users > 0 else 0,
                    "average_sessions_per_user": total_sessions / total_users if total_users > 0 else 0
                },
                "user_summaries": user_summaries
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas gerais de tracking: {e}")
            return {
                "tracking_enabled": self.session_tracking_enabled,
                "error": str(e)
            }
    
    def _cleanup_old_tracking_data(self) -> None:
        """
        Limpar dados de tracking antigos
        """
        try:
            if not self.session_tracking_enabled:
                return
                
            current_time = datetime.now().timestamp()
            cleanup_threshold = current_time - (self.cache_ttl * 2)  # 2x TTL
            
            users_to_remove = []
            
            for username, user_data in self.user_session_tracking.items():
                # Remover sessões antigas
                sessions_to_remove = [
                    session_id for session_id, session_data in user_data["sessions"].items()
                    if session_data["last_activity"] < cleanup_threshold
                ]
                
                for session_id in sessions_to_remove:
                    del user_data["sessions"][session_id]
                
                # Se usuário não tem mais sessões, marcar para remoção
                if not user_data["sessions"]:
                    users_to_remove.append(username)
            
            # Remover usuários sem sessões
            for username in users_to_remove:
                del self.user_session_tracking[username]
            
            if sessions_to_remove or users_to_remove:
                logger.info(f"🧹 Limpeza de tracking: {len(sessions_to_remove)} sessões, {len(users_to_remove)} usuários removidos")
                
        except Exception as e:
            logger.error(f"❌ Erro ao limpar dados de tracking: {e}")
    
    def _get_user_context_cache_key(self, username: str, session_id: str) -> str:
        """
        Gerar chave de cache para contexto do usuário
        """
        return f"{username}:{session_id}"
    
    def _get_cached_user_context(self, username: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Recuperar contexto do usuário do cache
        """
        try:
            cache_key = self._get_user_context_cache_key(username, session_id)
            
            if cache_key in self.user_context_cache:
                cached_data = self.user_context_cache[cache_key]
                
                # Verificar se o cache não expirou
                if datetime.now().timestamp() - cached_data["timestamp"] < self.cache_ttl:
                    logger.info(f"✅ Cache hit para {username}:{session_id}")
                    return cached_data["context"]
                else:
                    # Cache expirado, remover
                    del self.user_context_cache[cache_key]
                    logger.info(f"⏰ Cache expirado para {username}:{session_id}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar cache de contexto: {e}")
            return None
    
    def _cache_user_context(self, username: str, session_id: str, context: Dict[str, Any]) -> None:
        """
        Salvar contexto do usuário no cache
        """
        try:
            cache_key = self._get_user_context_cache_key(username, session_id)
            
            # Verificar se o cache não está cheio
            if len(self.user_context_cache) >= self.cache_max_size:
                # Remover entrada mais antiga
                oldest_key = min(self.user_context_cache.keys(), 
                               key=lambda k: self.user_context_cache[k]["timestamp"])
                del self.user_context_cache[oldest_key]
                logger.info(f"🗑️ Cache cheio, removendo entrada mais antiga: {oldest_key}")
            
            # Salvar no cache
            self.user_context_cache[cache_key] = {
                "context": context,
                "timestamp": datetime.now().timestamp()
            }
            
            logger.info(f"💾 Contexto salvo no cache para {username}:{session_id}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar contexto no cache: {e}")
    
    def _get_user_session_info(self, username: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obter informações da sessão do usuário do cache
        """
        try:
            cache_key = self._get_user_context_cache_key(username, session_id)
            
            if cache_key in self.user_session_cache:
                session_data = self.user_session_cache[cache_key]
                
                # Verificar se não expirou
                if datetime.now().timestamp() - session_data["timestamp"] < self.cache_ttl:
                    return session_data["session_info"]
                else:
                    # Expirado, remover
                    del self.user_session_cache[cache_key]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações da sessão: {e}")
            return None
    
    def _cache_user_session_info(self, username: str, session_id: str, session_info: Dict[str, Any]) -> None:
        """
        Salvar informações da sessão no cache
        """
        try:
            cache_key = self._get_user_context_cache_key(username, session_id)
            
            # Verificar tamanho do cache
            if len(self.user_session_cache) >= self.cache_max_size:
                # Remover entrada mais antiga
                oldest_key = min(self.user_session_cache.keys(), 
                               key=lambda k: self.user_session_cache[k]["timestamp"])
                del self.user_session_cache[oldest_key]
            
            # Salvar no cache
            self.user_session_cache[cache_key] = {
                "session_info": session_info,
                "timestamp": datetime.now().timestamp()
            }
            
            logger.info(f"💾 Informações da sessão salvas no cache para {username}:{session_id}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar informações da sessão: {e}")
    
    def _clear_user_cache(self, username: str) -> None:
        """
        Limpar cache específico do usuário
        """
        try:
            keys_to_remove = [key for key in self.user_context_cache.keys() if key.startswith(f"{username}:")]
            
            for key in keys_to_remove:
                del self.user_context_cache[key]
                
            session_keys_to_remove = [key for key in self.user_session_cache.keys() if key.startswith(f"{username}:")]
            
            for key in session_keys_to_remove:
                del self.user_session_cache[key]
                
            logger.info(f"🗑️ Cache limpo para usuário {username}: {len(keys_to_remove)} contextos + {len(session_keys_to_remove)} sessões")
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar cache do usuário: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obter estatísticas do cache e tracking
        """
        try:
            # Estatísticas básicas do cache
            cache_stats = {
                "context_cache_size": len(self.user_context_cache),
                "session_cache_size": len(self.user_session_cache),
                "cache_max_size": self.cache_max_size,
                "cache_ttl": self.cache_ttl,
                "memory_usage": {
                    "context_cache_keys": list(self.user_context_cache.keys()),
                    "session_cache_keys": list(self.user_session_cache.keys())
                }
            }
            
            # ✅ NOVO: Adicionar estatísticas de tracking
            if self.session_tracking_enabled:
                tracking_stats = self._get_all_users_tracking_stats()
                cache_stats["tracking"] = tracking_stats
            else:
                cache_stats["tracking"] = {
                    "tracking_enabled": False,
                    "message": "Session tracking desabilitado"
                }
            
            return cache_stats
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas do cache: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _get_user_profile_context(self, username: str) -> str:
        """
        Obter contexto do perfil do usuário para personalização
        """
        try:
            # Verificar se há perfil em cache
            cached_profile = self._get_cached_user_profile(username)
            if cached_profile:
                logger.info(f"✅ Perfil do usuário {username} encontrado em cache")
                return self._format_user_profile_context(cached_profile)
            
            # Se não houver cache, usar contexto básico
            logger.info(f"📄 Usando contexto básico para usuário {username}")
            return self._get_basic_user_context(username)
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter contexto do perfil: {e}")
            return self._get_basic_user_context(username)
    
    def _get_cached_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Buscar perfil do usuário do cache
        """
        try:
            # Usar cache de sessão para perfil do usuário
            profile_key = f"{username}:profile"
            
            if profile_key in self.user_context_cache:
                cached_data = self.user_context_cache[profile_key]
                
                # Verificar se não expirou
                if datetime.now().timestamp() - cached_data["timestamp"] < self.cache_ttl:
                    return cached_data["context"]
                else:
                    # Expirado, remover
                    del self.user_context_cache[profile_key]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar perfil do usuário no cache: {e}")
            return None
    
    def _format_user_profile_context(self, profile: Dict[str, Any]) -> str:
        """
        Formatar contexto do perfil do usuário para OpenAI
        Trabalha com dados de registration_data e user_profile
        """
        try:
            context_parts = []

            display_name = (
                profile.get("preferred_name")
                or profile.get("display_name")
                or profile.get("full_name")
                or (profile.get("preferences") or {}).get("display_name")
                or (profile.get("preferences") or {}).get("full_name")
            )
            if display_name:
                first_name = self._extract_first_name(display_name)
                context_parts.append("👤 IDENTIDADE:")
                context_parts.append(f"- Nome preferido: {display_name}")
                if first_name:
                    context_parts.append(f"- Nome para tratamento: {first_name}")
                if profile.get("username"):
                    context_parts.append(f"- Identificador técnico: {profile['username']}")
            
            # ✅ NOVO: Processar registration_data se disponível (dados da sessão-1)
            registration_data = profile.get("registration_data", {})
            if registration_data:
                context_parts.append("📋 DADOS PESSOAIS (SESSÃO-1):")
                
                if registration_data.get("idade"):
                    context_parts.append(f"- Idade: {registration_data['idade']} anos")
                
                if registration_data.get("ocupacao"):
                    ocupacao = registration_data["ocupacao"]
                    # Extrair profissão principal
                    if "engenheiro de dados" in ocupacao.lower():
                        context_parts.append(f"- Profissão: Engenheiro de Dados")
                    elif "professor" in ocupacao.lower():
                        context_parts.append(f"- Profissão: Professor")
                    else:
                        context_parts.append(f"- Ocupação: {ocupacao}")
                
                if registration_data.get("genero"):
                    context_parts.append(f"- Gênero: {registration_data['genero']}")
                
                if registration_data.get("localizacao"):
                    context_parts.append(f"- Localização: {registration_data['localizacao']}")
                
                if registration_data.get("situacao_moradia"):
                    context_parts.append(f"- Situação de moradia: {registration_data['situacao_moradia']}")
                
                if registration_data.get("relacao_familia"):
                    context_parts.append(f"- Relação familiar: {registration_data['relacao_familia']}")
                
                if registration_data.get("motivacao_terapia") and registration_data["motivacao_terapia"].lower() not in ["nada", "não", "n/a"]:
                    context_parts.append(f"- Motivação para terapia: {registration_data['motivacao_terapia']}")
                
                if registration_data.get("informacoes_adicionais") and registration_data["informacoes_adicionais"].lower() not in ["não", "nada", "n/a"]:
                    context_parts.append(f"- Informações adicionais: {registration_data['informacoes_adicionais']}")
            
            # ✅ COMPATIBILIDADE: Processar user_profile estruturado (se disponível)
            elif profile.get("personal_info"):
                personal = profile["personal_info"]
                context_parts.append("📋 INFORMAÇÕES PESSOAIS:")
                
                if personal.get("idade"):
                    context_parts.append(f"- Idade: {personal['idade']} anos")
                if personal.get("profissao"):
                    context_parts.append(f"- Profissão: {personal['profissao']}")
                if personal.get("genero"):
                    context_parts.append(f"- Gênero: {personal['genero']}")
                if personal.get("estado_civil"):
                    context_parts.append(f"- Estado civil: {personal['estado_civil']}")
            
            # ✅ COMPATIBILIDADE: Informações terapêuticas estruturadas
            if profile.get("therapeutic_info"):
                therapeutic = profile["therapeutic_info"]
                context_parts.append("\n🎯 INFORMAÇÕES TERAPÊUTICAS:")
                
                if therapeutic.get("motivacao_terapia"):
                    motivacao = therapeutic["motivacao_terapia"]
                    if isinstance(motivacao, dict) and motivacao.get("content"):
                        context_parts.append(f"- Motivação: {motivacao['content']}")
                    elif isinstance(motivacao, str):
                        context_parts.append(f"- Motivação: {motivacao}")
                
                if therapeutic.get("objetivos_identificados"):
                    objetivos = therapeutic["objetivos_identificados"]
                    if isinstance(objetivos, list) and objetivos:
                        context_parts.append(f"- Objetivos: {', '.join(objetivos)}")
                
                if therapeutic.get("experiencia_terapia_anterior"):
                    experiencia = therapeutic["experiencia_terapia_anterior"]
                    if isinstance(experiencia, dict) and experiencia.get("content"):
                        context_parts.append(f"- Experiência anterior: {experiencia['content']}")
                    elif isinstance(experiencia, str):
                        context_parts.append(f"- Experiência anterior: {experiencia}")
            
            # ✅ COMPATIBILIDADE: Preferências do usuário
            if profile.get("preferences"):
                prefs = profile["preferences"]
                context_parts.append("\n⚙️ PREFERÊNCIAS:")
                
                if prefs.get("selected_voice"):
                    context_parts.append(f"- Voz preferida: {prefs['selected_voice']}")
                if prefs.get("voice_enabled"):
                    context_parts.append(f"- Áudio habilitado: {prefs['voice_enabled']}")
            
            # ✅ NOVA SEÇÃO: Resumo do perfil se disponível
            if profile.get("profile_summary"):
                context_parts.append(f"\n📄 RESUMO: {profile['profile_summary']}")
            
            if context_parts:
                return "\n".join(context_parts)
            else:
                return self._get_basic_user_context(profile.get("username", "usuário"))
            
        except Exception as e:
            logger.error(f"❌ Erro ao formatar contexto do perfil: {e}")
            return self._get_basic_user_context("usuário")
    
    def _get_basic_user_context(self, username: str) -> str:
        """
        Obter contexto básico quando não há perfil disponível
        """
        return f"""
PERFIL DO USUÁRIO:
- Username: {username}
- Status: Usuário sem perfil detalhado
- Abordagem: Use uma abordagem terapêutica padrão e empática
- Personalização: Colete informações gradualmente durante a conversa
"""
    
    def cache_user_profile(self, username: str, profile: Dict[str, Any]) -> None:
        """
        Salvar perfil do usuário no cache
        """
        try:
            profile_key = f"{username}:profile"
            
            # Verificar tamanho do cache
            if len(self.user_context_cache) >= self.cache_max_size:
                # Remover entrada mais antiga
                oldest_key = min(self.user_context_cache.keys(), 
                               key=lambda k: self.user_context_cache[k]["timestamp"])
                del self.user_context_cache[oldest_key]
            
            # Salvar no cache
            self.user_context_cache[profile_key] = {
                "context": profile,
                "timestamp": datetime.now().timestamp()
            }
            
            logger.info(f"💾 Perfil do usuário {username} salvo no cache")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar perfil do usuário no cache: {e}")

    def _format_previous_session_context(self, previous_session_context: Dict[str, Any]) -> str:
        """
        Formatar contexto da sessão anterior para incluir no prompt do sistema
        OTIMIZADO PARA ECONOMIA DE TOKENS - trabalha com estrutura real do MongoDB
        """
        try:
            if not previous_session_context:
                return ""
            
            # Lista compacta de informações essenciais
            essential_info = []
            
            # 1. DADOS PESSOAIS do registration_data (prioridade máxima)
            registration_data = previous_session_context.get("registration_data", {})
            # ✅ DEBUG: Log do registration_data recebido
            logger.debug("registration_data recebido: %s", registration_data)
            
            personal_data = []
            if registration_data.get("idade"):
                personal_data.append(f"idade {registration_data['idade']}")
            if registration_data.get("ocupacao"):
                # Extrair apenas a profissão principal
                ocupacao = registration_data["ocupacao"]
                # ✅ DEBUG: Log da ocupação encontrada
                logger.debug("ocupacao: '%s'", ocupacao)
                if "engenheiro de dados" in ocupacao.lower():
                    personal_data.append("engenheiro de dados")
                    logger.debug("profissão: engenheiro de dados")
                elif "professor" in ocupacao.lower():
                    personal_data.append("professor")
                    logger.debug("profissão: professor")
                elif "trabalho" in ocupacao.lower():
                    personal_data.append("trabalha")
                    logger.debug("profissão: trabalha")
                else:
                    logger.debug("profissão não reconhecida: '%s'", ocupacao)
            if registration_data.get("localizacao"):
                personal_data.append(f"de {registration_data['localizacao']}")
            if registration_data.get("genero"):
                personal_data.append(f"gênero {registration_data['genero']}")
            if registration_data.get("situacao_moradia"):
                if "familia" in registration_data["situacao_moradia"].lower():
                    personal_data.append("mora com família")
            
            if personal_data:
                essential_info.append(f"PERFIL: {', '.join(personal_data)}")
                # ✅ DEBUG: Log do perfil formatado
                logger.debug("perfil formatado: %s", ', '.join(personal_data))
            
            # 2. CONTEXTO DA SESSÃO ANTERIOR
            session_context = previous_session_context.get("session_context", {})
            
            # 2.1. TEMAS PRINCIPAIS (máximo 3 temas)
            main_themes = session_context.get("main_themes", [])
            if main_themes:
                top_themes = main_themes[:3]  
                essential_info.append(f"TEMAS ANTERIORES: {', '.join(top_themes)}")
            
            # 2.2. ESTADO EMOCIONAL (resumido)
            emotional_state = session_context.get("emotional_state", {})
            if emotional_state:
                emotion_parts = []
                if emotional_state.get("final"):
                    emotion_parts.append(emotional_state["final"])
                if emotional_state.get("progression"):
                    # Resumir progressão emocional
                    prog = emotional_state["progression"]
                    if "estável" in prog.lower():
                        emotion_parts.append("(estável)")
                    elif "melhorou" in prog.lower():
                        emotion_parts.append("(melhorou)")
                    elif "piorou" in prog.lower():
                        emotion_parts.append("(piorou)")
                if emotion_parts:
                    essential_info.append(f"ESTADO EMOCIONAL: {' '.join(emotion_parts)}")
            
            # 2.3. INSIGHTS CHAVE (máximo 2 insights mais importantes)
            key_insights = session_context.get("key_insights", [])
            if key_insights:
                top_insights = key_insights[:2]  
                essential_info.append(f"INSIGHTS: {'; '.join(top_insights)}")
            
            # 2.4. PROGRESSO TERAPÊUTICO
            therapeutic_notes = session_context.get("therapeutic_notes", {})
            if therapeutic_notes.get("engagement_level"):
                essential_info.append(f"ENGAJAMENTO: {therapeutic_notes['engagement_level']}")
            
            # 3. SUGESTÕES PARA PRÓXIMAS SESSÕES (se disponível)
            future_sessions = session_context.get("future_sessions", {})
            if future_sessions.get("suggested_topics"):
                suggested_topics = future_sessions["suggested_topics"][:2]  # Máximo 2 tópicos
                essential_info.append(f"PRÓXIMOS TÓPICOS: {', '.join(suggested_topics)}")
            
            # 4. CONSTRUIR CONTEXTO FINAL
            if essential_info:
                context_text = "CONTEXTO ANTERIOR:\n" + "\n".join(essential_info)
                # ✅ DEBUG: Log do contexto final
                logger.debug("contexto anterior formatado (%d chars)", len(context_text))
                return context_text
            else:
                logger.debug("contexto anterior: sem informações essenciais")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Erro ao formatar contexto da sessão anterior: {e}")
            return ""
    
    def _create_cumulative_context(self, previous_session_context: Dict[str, Any], current_conversation: List[Dict], username: str) -> str:
        """
        Criar contexto cumulativo otimizado: contexto anterior + conversa atual
        MÁXIMA ECONOMIA DE TOKENS - mantém apenas informações essenciais e não redundantes
        """
        try:
            cumulative_parts = []
            
            # 1. CONTEXTO ANTERIOR (já otimizado)
            previous_context = self._format_previous_session_context(previous_session_context)
            if previous_context:
                cumulative_parts.append(previous_context)
            
            # 2. CONVERSA ATUAL (comprimida e otimizada)
            if current_conversation:
                current_context = self._compress_current_conversation(current_conversation, username)
                if current_context:
                    cumulative_parts.append(f"CONVERSA ATUAL:\n{current_context}")
            
            # 3. COMBINAR CONTEXTOS (evitar redundância)
            if cumulative_parts:
                return "\n\n".join(cumulative_parts)
            else:
                return ""
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar contexto cumulativo: {e}")
            return ""
    
    def _compress_current_conversation(self, conversation: List[Dict], username: str) -> str:
        """
        Comprimir conversa atual para economia máxima de tokens
        Mantém apenas informações essenciais e novidades
        """
        try:
            if not conversation:
                return ""
            
            # Extrair apenas mensagens essenciais
            essential_messages = []
            user_messages = []
            ai_messages = []
            
            # Separar mensagens por tipo
            for msg in conversation:
                if msg.get("type") == "user":
                    user_messages.append(msg.get("content", ""))
                elif msg.get("type") == "assistant":
                    ai_messages.append(msg.get("content", ""))
            
            # Análise rápida das mensagens do usuário
            if user_messages:
                # Última mensagem do usuário (sempre importante)
                last_user_msg = user_messages[-1]
                if last_user_msg and len(last_user_msg.strip()) > 0:
                    essential_messages.append(f"ÚLTIMA PERGUNTA: {last_user_msg[:100]}{'...' if len(last_user_msg) > 100 else ''}")
                
                # Identificar temas novos/importantes nas mensagens anteriores
                if len(user_messages) > 1:
                    new_themes = self._extract_new_themes_from_messages(user_messages[:-1])
                    if new_themes:
                        essential_messages.append(f"TEMAS NOVOS: {', '.join(new_themes[:3])}")
                
                # Identificar informações pessoais novas
                new_personal_info = self._extract_new_personal_info(user_messages)
                if new_personal_info:
                    essential_messages.append(f"NOVAS INFORMAÇÕES: {', '.join(new_personal_info[:3])}")
            
            # Análise das respostas da IA (identificar padrões)
            if ai_messages and len(ai_messages) > 1:
                response_pattern = self._identify_response_pattern(ai_messages)
                if response_pattern:
                    essential_messages.append(f"PADRÃO RESPOSTA: {response_pattern}")
            
            # Retornar contexto comprimido
            if essential_messages:
                return "\n".join(essential_messages)
            else:
                return ""
                
        except Exception as e:
            logger.error(f"❌ Erro ao comprimir conversa atual: {e}")
            return ""
    
    def _extract_new_themes_from_messages(self, messages: List[str]) -> List[str]:
        """
        Extrair temas novos das mensagens do usuário (economia de tokens)
        """
        try:
            themes = []
            
            for msg in messages:
                msg_lower = msg.lower()
                
                # Temas comuns em terapia
                if any(word in msg_lower for word in ["trabalho", "emprego", "carreira", "profissão"]):
                    themes.append("trabalho")
                elif any(word in msg_lower for word in ["família", "pai", "mãe", "irmão", "parente"]):
                    themes.append("família")
                elif any(word in msg_lower for word in ["relacionamento", "namorado", "namorada", "parceiro"]):
                    themes.append("relacionamento")
                elif any(word in msg_lower for word in ["ansiedade", "nervoso", "preocupado", "estresse"]):
                    themes.append("ansiedade")
                elif any(word in msg_lower for word in ["triste", "deprimido", "melancolia", "tristeza"]):
                    themes.append("tristeza")
                elif any(word in msg_lower for word in ["futuro", "planos", "objetivos", "metas"]):
                    themes.append("futuro")
                elif any(word in msg_lower for word in ["passado", "história", "lembrança", "memória"]):
                    themes.append("passado")
                elif any(word in msg_lower for word in ["saúde", "doença", "médico", "sintoma"]):
                    themes.append("saúde")
                elif any(word in msg_lower for word in ["dinheiro", "financeiro", "grana", "economia"]):
                    themes.append("financeiro")
                elif any(word in msg_lower for word in ["estudo", "escola", "universidade", "curso"]):
                    themes.append("educação")
            
            # Remover duplicatas mantendo ordem
            return list(dict.fromkeys(themes))
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair temas: {e}")
            return []
    
    def _extract_new_personal_info(self, messages: List[str]) -> List[str]:
        """
        Extrair informações pessoais novas das mensagens (economia de tokens)
        """
        try:
            personal_info = []
            
            for msg in messages:
                msg_lower = msg.lower()
                
                # Informações pessoais relevantes
                if any(word in msg_lower for word in ["anos", "idade", "nasci", "tenho"]):
                    if "anos" in msg_lower:
                        personal_info.append("idade mencionada")
                
                if any(word in msg_lower for word in ["trabalho como", "sou", "atuo como", "profissão"]):
                    personal_info.append("profissão mencionada")
                
                if any(word in msg_lower for word in ["moro", "vivo", "cidade", "bairro"]):
                    personal_info.append("localização mencionada")
                
                if any(word in msg_lower for word in ["casado", "solteiro", "namorando", "divorciado"]):
                    personal_info.append("estado civil mencionado")
                
                if any(word in msg_lower for word in ["filho", "filha", "criança", "bebê"]):
                    personal_info.append("filhos mencionados")
            
            # Remover duplicatas
            return list(dict.fromkeys(personal_info))
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair informações pessoais: {e}")
            return []
    
    def _identify_response_pattern(self, ai_messages: List[str]) -> str:
        """
        Identificar padrão nas respostas da IA (economia de tokens)
        """
        try:
            if len(ai_messages) < 2:
                return ""
            
            # Análise simples de padrões
            total_length = sum(len(msg) for msg in ai_messages)
            avg_length = total_length / len(ai_messages)
            
            if avg_length > 500:
                return "respostas detalhadas"
            elif avg_length > 200:
                return "respostas moderadas"
            else:
                return "respostas concisas"
                
        except Exception as e:
            logger.error(f"❌ Erro ao identificar padrão: {e}")
            return ""
