"""
TokenEconomyService - Lógica de economia de tokens baseada em reutilização de contextos
Combina SessionContextService (MongoDB) e RedisPerformanceService para economia de tokens OpenAI
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from .session_context_service import SessionContextService
from .redis_performance_service import RedisPerformanceService
from .openai_service import OpenAIService

logger = logging.getLogger(__name__)


class TokenEconomyService:
    """
    Serviço de economia de tokens baseado em reutilização de contextos
    
    Este serviço combina:
    - MongoDB como repositório principal (SessionContextService)
    - Redis para otimização de performance (RedisPerformanceService)
    - OpenAI para geração apenas quando necessário
    
    Economia vem da reutilização de contextos existentes no MongoDB.
    """
    
    def __init__(self):
        """Inicializar serviço de economia de tokens"""
        self.session_context_service = SessionContextService()
        self.redis_performance_service = RedisPerformanceService()
        self.openai_service = OpenAIService()
        
        # Configurações de economia
        self.enable_context_reuse = os.getenv("ENABLE_CONTEXT_REUSE", "true").lower() == "true"
        self.enable_next_session_reuse = os.getenv("ENABLE_NEXT_SESSION_REUSE", "true").lower() == "true"
        self.context_similarity_threshold = float(os.getenv("CONTEXT_SIMILARITY_THRESHOLD", "0.7"))
        
        # Métricas de economia
        self.economy_stats = {
            "total_requests": 0,
            "context_reused": 0,
            "next_session_reused": 0,
            "tokens_saved": 0,
            "generation_avoided": 0
        }
        
        # Configurações de TTL para diferentes tipos de contexto
        self.context_ttl_hours = int(os.getenv("CONTEXT_TTL_HOURS", "168"))  # 7 dias
        self.next_session_ttl_hours = int(os.getenv("NEXT_SESSION_TTL_HOURS", "720"))  # 30 dias
        
        logger.info("✅ TokenEconomyService inicializado com economia de tokens ativa")
    
    async def initialize(self):
        """Inicializar serviços dependentes"""
        try:
            # Inicializar índices do MongoDB
            await self.session_context_service.initialize_indexes()
            
            logger.info("✅ TokenEconomyService inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar TokenEconomyService: {e}")
    
    async def get_or_generate_session_context(self, conversation_text: str, session_id: str, 
                                            username: str, emotions_data: List[Dict] = None) -> Tuple[Dict[str, Any], str, bool]:
        """
        Obter contexto existente ou gerar novo, priorizando economia de tokens
        
        Args:
            conversation_text: Texto da conversa
            session_id: ID da sessão
            username: Username do usuário
            emotions_data: Dados de emoções (opcional)
            
        Returns:
            Tuple[context_data, source, tokens_saved] onde:
            - context_data: Dados do contexto
            - source: "mongodb_reuse" | "redis_performance" | "openai_generated"
            - tokens_saved: True se tokens foram economizados
        """
        try:
            self.economy_stats["total_requests"] += 1
            
            # 1. Verificar se contexto já existe no MongoDB (repositório principal)
            if self.enable_context_reuse:
                logger.info(f"🔍 Buscando contexto existente da sessão {session_id} (usuário: {username})")
                
                existing_context = await self.session_context_service.get_session_context(session_id, username)
                
                if existing_context:
                    context_data = existing_context.get("context")
                    if context_data and self._is_context_valid(context_data):
                        logger.info(f"💾 Contexto da sessão {session_id} reutilizado do MongoDB (ECONOMIA DE TOKENS)")
                        
                        # Cachear no Redis para performance
                        self.redis_performance_service.cache_context_for_performance(session_id, context_data)
                        
                        # Atualizar métricas
                        self.economy_stats["context_reused"] += 1
                        self.economy_stats["tokens_saved"] += self._estimate_tokens_saved("context")
                        
                        return context_data, "mongodb_reuse", True
            
            # 2. Verificar cache de performance do Redis (se sessão está ativa)
            if self.redis_performance_service.is_session_active(session_id):
                logger.debug(f"⚡ Verificando cache de performance para sessão ativa {session_id}")
                
                cached_context = self.redis_performance_service.get_cached_context(session_id)
                if cached_context:
                    logger.info(f"⚡ Contexto da sessão {session_id} obtido do cache de performance")
                    return cached_context, "redis_performance", False
            
            # 3. Gerar novo contexto usando OpenAI
            logger.info(f"🤖 Gerando novo contexto para sessão {session_id} (usuário: {username})")
            
            context_data = await self.openai_service.generate_session_context(
                conversation_text, 
                emotions_data or []
            )
            
            if context_data:
                # Salvar no MongoDB como dados primários
                await self.session_context_service.save_session_context(
                    session_id, 
                    username, 
                    context_data, 
                    conversation_text, 
                    emotions_data
                )
                
                # Cachear no Redis para performance
                self.redis_performance_service.cache_context_for_performance(session_id, context_data)
                
                logger.info(f"✅ Novo contexto gerado e salvo para sessão {session_id}")
                return context_data, "openai_generated", False
            
            # 4. Fallback em caso de erro
            logger.error(f"❌ Falha ao gerar contexto para sessão {session_id}")
            return {}, "error", False
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter/gerar contexto da sessão {session_id}: {e}")
            return {}, "error", False
    
    async def get_or_generate_next_session(self, user_profile: Dict[str, Any], session_context: Dict[str, Any], 
                                         current_session_id: str, username: str) -> Tuple[Dict[str, Any], str, bool]:
        """
        Obter próxima sessão existente ou gerar nova, priorizando economia de tokens
        
        Args:
            user_profile: Perfil do usuário
            session_context: Contexto da sessão atual
            current_session_id: ID da sessão atual
            username: Username do usuário
            
        Returns:
            Tuple[next_session_data, source, tokens_saved] onde:
            - next_session_data: Dados da próxima sessão
            - source: "mongodb_reuse" | "redis_performance" | "openai_generated"
            - tokens_saved: True se tokens foram economizados
        """
        try:
            self.economy_stats["total_requests"] += 1
            
            # Determinar ID da próxima sessão
            next_session_id = self._get_next_session_id(current_session_id)
            
            # 1. Verificar se próxima sessão já existe no MongoDB
            if self.enable_next_session_reuse:
                logger.info(f"🔍 Buscando próxima sessão existente {next_session_id} (usuário: {username})")
                
                existing_session = await self.session_context_service.get_session_context(next_session_id, username)
                
                if existing_session:
                    context_data = existing_session.get("context")
                    if context_data and self._is_next_session_valid(context_data, session_context):
                        logger.info(f"💾 Próxima sessão {next_session_id} reutilizada do MongoDB (ECONOMIA DE TOKENS)")
                        
                        # Cachear no Redis para performance
                        self.redis_performance_service.cache_context_for_performance(next_session_id, context_data)
                        
                        # Atualizar métricas
                        self.economy_stats["next_session_reused"] += 1
                        self.economy_stats["tokens_saved"] += self._estimate_tokens_saved("next_session")
                        
                        return context_data, "mongodb_reuse", True
            
            # 2. Verificar cache de performance do Redis (se próxima sessão está sendo preparada)
            cached_next_session = self.redis_performance_service.get_cached_context(next_session_id)
            if cached_next_session:
                logger.info(f"⚡ Próxima sessão {next_session_id} obtida do cache de performance")
                return cached_next_session, "redis_performance", False
            
            # 3. Gerar nova próxima sessão usando OpenAI
            logger.info(f"🤖 Gerando nova próxima sessão {next_session_id} (usuário: {username})")
            
            next_session_data = await self.openai_service.generate_next_session(
                user_profile, 
                session_context, 
                current_session_id
            )
            
            if next_session_data:
                # Salvar no MongoDB como dados primários
                await self.session_context_service.save_session_context(
                    next_session_id, 
                    username, 
                    next_session_data, 
                    f"Generated from session {current_session_id}", 
                    []
                )
                
                # Cachear no Redis para performance
                self.redis_performance_service.cache_context_for_performance(next_session_id, next_session_data)
                
                logger.info(f"✅ Nova próxima sessão gerada e salva: {next_session_id}")
                return next_session_data, "openai_generated", False
            
            # 4. Fallback em caso de erro
            logger.error(f"❌ Falha ao gerar próxima sessão {next_session_id}")
            return {}, "error", False
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter/gerar próxima sessão: {e}")
            return {}, "error", False
    
    async def start_session_with_economy(self, session_id: str, username: str, 
                                       initial_data: Dict[str, Any] = None) -> bool:
        """
        Iniciar sessão com otimização de economia de tokens
        
        Args:
            session_id: ID da sessão
            username: Username do usuário
            initial_data: Dados iniciais da sessão
            
        Returns:
            bool: True se iniciada com sucesso
        """
        try:
            logger.info(f"🚀 Iniciando sessão com economia de tokens: {session_id} (usuário: {username})")
            
            # Iniciar sessão no Redis para performance
            redis_started = self.redis_performance_service.start_session(session_id, username, initial_data)
            
            # Verificar se há contexto existente no MongoDB
            existing_context = await self.session_context_service.get_session_context(session_id, username)
            
            if existing_context:
                logger.info(f"💾 Contexto existente encontrado para sessão {session_id} - tokens economizados")
                
                # Cachear no Redis para performance
                context_data = existing_context.get("context")
                if context_data:
                    self.redis_performance_service.cache_context_for_performance(session_id, context_data)
                
                # Atualizar métricas
                self.economy_stats["context_reused"] += 1
                self.economy_stats["tokens_saved"] += self._estimate_tokens_saved("context")
            
            # Cachear dados do usuário no Redis para performance
            if initial_data:
                self.redis_performance_service.cache_user_data(username, initial_data)
            
            logger.info(f"✅ Sessão {session_id} iniciada com economia de tokens")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sessão com economia: {e}")
            return False
    
    async def end_session_with_economy(self, session_id: str, username: str, 
                                     final_context: Dict[str, Any] = None) -> bool:
        """
        Encerrar sessão com persistência no MongoDB
        
        Args:
            session_id: ID da sessão
            username: Username do usuário
            final_context: Contexto final da sessão
            
        Returns:
            bool: True se encerrada com sucesso
        """
        try:
            logger.info(f"🔚 Encerrando sessão com economia: {session_id} (usuário: {username})")
            
            # Salvar contexto final no MongoDB se fornecido
            if final_context:
                await self.session_context_service.save_session_context(
                    session_id, 
                    username, 
                    final_context
                )
                logger.info(f"💾 Contexto final salvo no MongoDB para sessão {session_id}")
            
            # Encerrar sessão no Redis
            redis_ended = self.redis_performance_service.end_session(session_id)
            
            logger.info(f"✅ Sessão {session_id} encerrada com economia de tokens")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao encerrar sessão com economia: {e}")
            return False
    
    def get_economy_statistics(self) -> Dict[str, Any]:
        """
        Obter estatísticas de economia de tokens
        
        Returns:
            Dict com estatísticas de economia
        """
        try:
            # Calcular taxas de economia
            total_requests = self.economy_stats["total_requests"]
            context_reuse_rate = (self.economy_stats["context_reused"] / total_requests * 100) if total_requests > 0 else 0
            next_session_reuse_rate = (self.economy_stats["next_session_reused"] / total_requests * 100) if total_requests > 0 else 0
            
            # Estimativa de custo evitado (baseado em preço médio OpenAI)
            avg_cost_per_1k_tokens = 0.01  # USD
            estimated_cost_saved = (self.economy_stats["tokens_saved"] / 1000) * avg_cost_per_1k_tokens
            
            return {
                "total_requests": total_requests,
                "context_reused": self.economy_stats["context_reused"],
                "next_session_reused": self.economy_stats["next_session_reused"],
                "tokens_saved": self.economy_stats["tokens_saved"],
                "generation_avoided": self.economy_stats["generation_avoided"],
                "economy_rates": {
                    "context_reuse_rate": f"{context_reuse_rate:.1f}%",
                    "next_session_reuse_rate": f"{next_session_reuse_rate:.1f}%",
                    "overall_economy_rate": f"{((self.economy_stats['context_reused'] + self.economy_stats['next_session_reused']) / total_requests * 100):.1f}%" if total_requests > 0 else "0%"
                },
                "estimated_savings": {
                    "tokens_saved": self.economy_stats["tokens_saved"],
                    "cost_saved_usd": f"${estimated_cost_saved:.4f}",
                    "generations_avoided": self.economy_stats["generation_avoided"]
                },
                "configuration": {
                    "context_reuse_enabled": self.enable_context_reuse,
                    "next_session_reuse_enabled": self.enable_next_session_reuse,
                    "similarity_threshold": self.context_similarity_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas de economia: {e}")
            return {"error": str(e)}
    
    async def get_user_economy_stats(self, username: str) -> Dict[str, Any]:
        """
        Obter estatísticas de economia específicas do usuário
        
        Args:
            username: Username do usuário
            
        Returns:
            Dict com estatísticas do usuário
        """
        try:
            # Obter sessões do usuário
            user_sessions = await self.session_context_service.list_user_sessions(username)
            
            # Calcular métricas por usuário
            total_sessions = len(user_sessions)
            active_sessions = len([s for s in user_sessions if s.get("is_active")])
            
            # Estatísticas gerais
            session_stats = await self.session_context_service.get_session_statistics(username)
            
            return {
                "username": username,
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "sessions_with_context": len([s for s in user_sessions if s.get("context_summary", {}).get("summary")]),
                "economy_potential": {
                    "sessions_reusable": total_sessions,
                    "estimated_tokens_saved": total_sessions * self._estimate_tokens_saved("context"),
                    "description": "Tokens economizados por reutilização de contextos existentes"
                },
                "recent_activity": {
                    "sessions_last_7_days": len([s for s in user_sessions if (datetime.utcnow() - s.get("updated_at", datetime.min)).days <= 7]),
                    "latest_session": user_sessions[0] if user_sessions else None
                },
                "mongodb_stats": session_stats
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas do usuário {username}: {e}")
            return {"error": str(e)}
    
    def _is_context_valid(self, context_data: Dict[str, Any]) -> bool:
        """
        Verificar se contexto é válido para reutilização
        
        Args:
            context_data: Dados do contexto
            
        Returns:
            bool: True se válido
        """
        try:
            # Verificar estrutura básica
            required_fields = ["summary", "main_themes", "emotional_state"]
            for field in required_fields:
                if field not in context_data:
                    return False
            
            # Verificar se não está vazio
            if not context_data.get("summary", "").strip():
                return False
            
            # Verificar se temas principais não estão vazios
            if not context_data.get("main_themes", []):
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Erro na validação do contexto: {e}")
            return False
    
    def _is_next_session_valid(self, next_session_data: Dict[str, Any], 
                             current_context: Dict[str, Any]) -> bool:
        """
        Verificar se próxima sessão é válida para reutilização
        
        Args:
            next_session_data: Dados da próxima sessão
            current_context: Contexto da sessão atual
            
        Returns:
            bool: True se válida
        """
        try:
            # Verificar estrutura básica
            required_fields = ["title", "objective", "initial_prompt"]
            for field in required_fields:
                if field not in next_session_data:
                    return False
            
            # Verificar se não está vazio
            if not next_session_data.get("title", "").strip():
                return False
            
            # Verificar similaridade com contexto atual (opcional)
            # Implementar lógica de similaridade se necessário
            
            return True
            
        except Exception as e:
            logger.debug(f"Erro na validação da próxima sessão: {e}")
            return False
    
    def _get_next_session_id(self, current_session_id: str) -> str:
        """
        Gerar ID da próxima sessão baseado na atual
        
        Args:
            current_session_id: ID da sessão atual
            
        Returns:
            str: ID da próxima sessão
        """
        try:
            # Extrair número da sessão atual
            import re
            match = re.search(r'session-(\d+)', current_session_id)
            if match:
                current_number = int(match.group(1))
                next_number = current_number + 1
                return current_session_id.replace(f"session-{current_number}", f"session-{next_number}")
            
            # Fallback se não conseguir extrair número
            return f"{current_session_id}_next"
            
        except Exception as e:
            logger.debug(f"Erro ao gerar próximo session_id: {e}")
            return f"{current_session_id}_next"
    
    def _estimate_tokens_saved(self, context_type: str) -> int:
        """
        Estimar tokens economizados por tipo de contexto
        
        Args:
            context_type: "context" | "next_session"
            
        Returns:
            int: Tokens estimados economizados
        """
        # Estimativas baseadas em médias observadas
        if context_type == "context":
            return 800  # Contexto de sessão médio
        elif context_type == "next_session":
            return 600  # Próxima sessão média
        else:
            return 500  # Padrão
    
    async def close(self):
        """Fechar conexões dos serviços"""
        try:
            await self.session_context_service.close()
            self.redis_performance_service.close()
            logger.info("🔒 TokenEconomyService fechado")
        except Exception as e:
            logger.error(f"❌ Erro ao fechar TokenEconomyService: {e}") 