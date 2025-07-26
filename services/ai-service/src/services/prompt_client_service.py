"""
Serviço cliente para buscar prompts do Gateway Service
"""

import os
import logging
import httpx
from typing import Dict, Any, Optional, List
import asyncio

logger = logging.getLogger(__name__)

class PromptClientService:
    """
    Serviço cliente para buscar prompts do Gateway Service
    """
    
    def __init__(self):
        """Inicializar cliente de prompts"""
        self.gateway_url = os.getenv("GATEWAY_SERVICE_URL", "http://gateway:8000")
        self.prompts_endpoint = f"{self.gateway_url}/api/prompts"
        self.timeout = 10.0
        
        # Cache em memória para prompts
        self._prompts_cache = {}
        self._cache_ttl = 300  # 5 minutos
        self._cache_timestamps = {}
        
        logger.info(f"✅ PromptClientService inicializado - Gateway URL: {self.gateway_url}")
    
    async def get_prompt(self, prompt_key: str) -> Optional[Dict[str, Any]]:
        """
        Buscar prompt ativo por chave
        
        Args:
            prompt_key: Chave única do prompt
            
        Returns:
            Dados do prompt ou None se não encontrado
        """
        try:
            # Verificar cache primeiro
            cached_prompt = self._get_from_cache(prompt_key)
            if cached_prompt:
                logger.debug(f"📋 Prompt encontrado no cache: {prompt_key}")
                return cached_prompt
            
            # Buscar do Gateway Service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.prompts_endpoint}/active/{prompt_key}")
                
                if response.status_code == 200:
                    prompt_data = response.json()
                    
                    # Salvar no cache
                    self._save_to_cache(prompt_key, prompt_data)
                    
                    logger.info(f"✅ Prompt encontrado no Gateway: {prompt_key}")
                    return prompt_data
                
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Prompt não encontrado: {prompt_key}")
                    return None
                
                else:
                    logger.error(f"❌ Erro ao buscar prompt {prompt_key}: HTTP {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"❌ Timeout ao buscar prompt: {prompt_key}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar prompt {prompt_key}: {e}")
            return None
    
    async def get_prompts_by_type(self, prompt_type: str) -> List[Dict[str, Any]]:
        """
        Buscar todos os prompts ativos de um tipo específico
        
        Args:
            prompt_type: Tipo de prompt (system, fallback, session_generation, etc.)
            
        Returns:
            Lista de prompts do tipo especificado
        """
        try:
            # Buscar do Gateway Service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.prompts_endpoint}/type/{prompt_type}")
                
                if response.status_code == 200:
                    data = response.json()
                    prompts = data.get("prompts", [])
                    
                    logger.info(f"✅ Encontrados {len(prompts)} prompts do tipo: {prompt_type}")
                    return prompts
                
                else:
                    logger.error(f"❌ Erro ao buscar prompts tipo {prompt_type}: HTTP {response.status_code}")
                    return []
                    
        except httpx.TimeoutException:
            logger.error(f"❌ Timeout ao buscar prompts tipo: {prompt_type}")
            return []
        except Exception as e:
            logger.error(f"❌ Erro ao buscar prompts tipo {prompt_type}: {e}")
            return []
    
    async def render_prompt(self, prompt_key: str, variables: Dict[str, Any]) -> Optional[str]:
        """
        Renderizar prompt com variáveis através do Gateway Service
        
        Args:
            prompt_key: Chave única do prompt
            variables: Variáveis para substituir no prompt
            
        Returns:
            Prompt renderizado ou None se não encontrado
        """
        try:
            # Buscar do Gateway Service
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.prompts_endpoint}/render/{prompt_key}",
                    json=variables
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rendered_content = data.get("rendered_content")
                    
                    logger.info(f"✅ Prompt renderizado: {prompt_key}")
                    return rendered_content
                
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Prompt não encontrado para renderização: {prompt_key}")
                    return None
                
                else:
                    logger.error(f"❌ Erro ao renderizar prompt {prompt_key}: HTTP {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"❌ Timeout ao renderizar prompt: {prompt_key}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao renderizar prompt {prompt_key}: {e}")
            return None
    
    async def get_system_prompt(self, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Buscar prompt de sistema principal (system_rogers)
        
        Args:
            variables: Variáveis para renderizar o prompt
            
        Returns:
            Prompt de sistema renderizado
        """
        try:
            prompt_key = "system_rogers"
            
            if variables:
                # Renderizar com variáveis
                rendered_prompt = await self.render_prompt(prompt_key, variables)
                if rendered_prompt:
                    return rendered_prompt
            
            # Buscar prompt simples
            prompt_data = await self.get_prompt(prompt_key)
            if prompt_data:
                return prompt_data.get("content", "")
            
            # Fallback para prompt hardcoded
            logger.warning("⚠️ Usando prompt de sistema fallback")
            return self._get_fallback_system_prompt()
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar prompt de sistema: {e}")
            return self._get_fallback_system_prompt()
    
    async def get_session_analysis_prompt(self, variables: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Buscar prompt para análise de contexto de sessão
        
        Args:
            variables: Variáveis para renderizar o prompt (conversation_text, emotion_summary)
            
        Returns:
            Prompt de análise de sessão renderizado ou None se não encontrado
        """
        try:
            prompt_key = "session_context_analysis"
            
            if variables:
                # Renderizar com variáveis
                rendered_prompt = await self.render_prompt(prompt_key, variables)
                if rendered_prompt:
                    return rendered_prompt
            
            # Buscar prompt simples
            prompt_data = await self.get_prompt(prompt_key)
            if prompt_data:
                return prompt_data.get("content", "")
            
            # Retornar None para usar fallback hardcoded
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar prompt de análise de sessão: {e}")
            return None
    
    async def get_next_session_prompt(self, variables: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Buscar prompt para geração de próxima sessão
        
        Args:
            variables: Variáveis para renderizar o prompt (current_session_id, next_session_id, user_summary, session_summary)
            
        Returns:
            Prompt de geração de próxima sessão renderizado ou None se não encontrado
        """
        try:
            prompt_key = "next_session_generation"
            
            if variables:
                # Renderizar com variáveis
                rendered_prompt = await self.render_prompt(prompt_key, variables)
                if rendered_prompt:
                    return rendered_prompt
            
            # Buscar prompt simples
            prompt_data = await self.get_prompt(prompt_key)
            if prompt_data:
                return prompt_data.get("content", "")
            
            # Retornar None para usar fallback hardcoded
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar prompt de geração de próxima sessão: {e}")
            return None
    
    async def get_fallback_response(self, pattern_type: str) -> Optional[str]:
        """
        Buscar resposta de fallback para um padrão específico
        
        Args:
            pattern_type: Tipo de padrão (greeting, sadness, anxiety, etc.)
            
        Returns:
            Resposta de fallback ou None se não encontrada
        """
        try:
            prompt_key = f"fallback_{pattern_type}"
            
            prompt_data = await self.get_prompt(prompt_key)
            if prompt_data:
                return prompt_data.get("content", "")
            
            logger.warning(f"⚠️ Prompt de fallback não encontrado: {pattern_type}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar fallback {pattern_type}: {e}")
            return None
    
    def _get_from_cache(self, prompt_key: str) -> Optional[Dict[str, Any]]:
        """
        Buscar prompt do cache em memória
        """
        try:
            import time
            
            if prompt_key in self._prompts_cache:
                timestamp = self._cache_timestamps.get(prompt_key, 0)
                if time.time() - timestamp < self._cache_ttl:
                    return self._prompts_cache[prompt_key]
                else:
                    # Cache expirado
                    del self._prompts_cache[prompt_key]
                    del self._cache_timestamps[prompt_key]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar cache: {e}")
            return None
    
    def _save_to_cache(self, prompt_key: str, prompt_data: Dict[str, Any]) -> None:
        """
        Salvar prompt no cache em memória
        """
        try:
            import time
            
            self._prompts_cache[prompt_key] = prompt_data
            self._cache_timestamps[prompt_key] = time.time()
            
            # Limpar cache se muito grande
            if len(self._prompts_cache) > 100:
                self._cleanup_cache()
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar cache: {e}")
    
    def _cleanup_cache(self) -> None:
        """
        Limpar cache antigo
        """
        try:
            import time
            current_time = time.time()
            
            expired_keys = []
            for key, timestamp in self._cache_timestamps.items():
                if current_time - timestamp >= self._cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._prompts_cache[key]
                del self._cache_timestamps[key]
            
            logger.debug(f"🧹 Cache limpo: removidas {len(expired_keys)} entradas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar cache: {e}")
    
    def _get_fallback_system_prompt(self) -> str:
        """
        Prompt de sistema fallback hardcoded
        """
        return """DIRETRIZES:
1. SEMPRE responda em português brasileiro
2. Você é o Dr. Rogers, um psicólogo virtual empático e acolhedor
3. Use abordagem centrada na pessoa (Carl Rogers)
4. Seja sempre empático, respeitoso e profissional
5. Encoraje o usuário a expressar seus sentimentos
6. Não ofereça diagnósticos médicos ou prescrições
7. Mantenha o foco na escuta ativa e reflexão
8. Adapte sua linguagem ao contexto emocional do usuário

CONTEXTO:
- Você está conduzindo uma sessão de terapia virtual
- O usuário busca apoio emocional e psicológico
- Mantenha um ambiente seguro e acolhedor
- Priorize a validação dos sentimentos do usuário"""
    
    async def test_connection(self) -> bool:
        """
        Testar conexão com o Gateway Service
        
        Returns:
            True se conexão OK, False caso contrário
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.prompts_endpoint}/stats")
                
                if response.status_code == 200:
                    logger.info("✅ Conexão com Gateway Service OK")
                    return True
                else:
                    logger.warning(f"⚠️ Gateway Service respondeu com HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Falha na conexão com Gateway Service: {e}")
            return False 