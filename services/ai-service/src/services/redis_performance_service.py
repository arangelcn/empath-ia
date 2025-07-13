"""
RedisPerformanceService - Otimização de performance para sessões ativas
Responsável por acelerar acesso aos dados do MongoDB durante sessões ativas
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError, ConnectionError

logger = logging.getLogger(__name__)


class RedisPerformanceService:
    """
    Serviço Redis para otimização de performance de sessões ativas
    
    Este serviço usa Redis apenas para acelerar acesso aos dados do MongoDB
    durante sessões ativas, não para cache de respostas OpenAI.
    """
    
    def __init__(self):
        """Inicializar serviço Redis de performance"""
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
        
        # Configurações de performance
        self.active_session_ttl = int(os.getenv("ACTIVE_SESSION_TTL", "3600"))  # 1 hora
        self.context_ttl = int(os.getenv("CONTEXT_TTL", "1800"))  # 30 minutos
        self.user_data_ttl = int(os.getenv("USER_DATA_TTL", "7200"))  # 2 horas
        
        # Prefixos para organização
        self.session_prefix = "session_active:"
        self.context_prefix = "context_perf:"
        self.user_prefix = "user_perf:"
        self.lifecycle_prefix = "lifecycle:"
        
        # Configurações de conexão
        self.max_retries = int(os.getenv("REDIS_MAX_RETRIES", "3"))
        self.socket_timeout = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
        
        # Inicializar conexão
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Inicializar conexão com Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=self.socket_timeout,
                retry_on_timeout=True,
                max_connections=50
            )
            
            # Testar conexão
            self.redis_client.ping()
            logger.info("✅ RedisPerformanceService conectado ao Redis")
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar RedisPerformanceService ao Redis: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Verificar se Redis está disponível"""
        try:
            if not self.redis_client:
                return False
            
            self.redis_client.ping()
            return True
            
        except Exception as e:
            logger.debug(f"Redis indisponível: {e}")
            return False
    
    def start_session(self, session_id: str, username: str, session_data: Dict[str, Any] = None) -> bool:
        """
        Iniciar sessão ativa no Redis para otimização de performance
        
        Args:
            session_id: ID da sessão
            username: Username do usuário
            session_data: Dados iniciais da sessão (opcional)
            
        Returns:
            bool: True se iniciada com sucesso
        """
        try:
            if not self.is_available():
                logger.debug(f"🔄 Redis indisponível - sessão {session_id} não iniciada em performance cache")
                return False
            
            key = f"{self.session_prefix}{session_id}"
            
            # Dados da sessão ativa
            active_session = {
                "session_id": session_id,
                "username": username,
                "started_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "is_active": True,
                "activity_count": 0,
                "data": session_data or {}
            }
            
            # Salvar com TTL
            self.redis_client.setex(
                key,
                self.active_session_ttl,
                json.dumps(active_session)
            )
            
            logger.info(f"🚀 Sessão {session_id} iniciada em performance cache (usuário: {username})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sessão {session_id} em performance cache: {e}")
            return False
    
    def is_session_active(self, session_id: str) -> bool:
        """
        Verificar se sessão está ativa no Redis
        
        Args:
            session_id: ID da sessão
            
        Returns:
            bool: True se sessão está ativa
        """
        try:
            if not self.is_available():
                return False
            
            key = f"{self.session_prefix}{session_id}"
            return self.redis_client.exists(key) > 0
            
        except Exception as e:
            logger.debug(f"Erro ao verificar sessão ativa {session_id}: {e}")
            return False
    
    def update_session_activity(self, session_id: str, activity_data: Dict[str, Any] = None) -> bool:
        """
        Atualizar atividade da sessão no Redis
        
        Args:
            session_id: ID da sessão
            activity_data: Dados da atividade (opcional)
            
        Returns:
            bool: True se atualizada com sucesso
        """
        try:
            if not self.is_available():
                return False
            
            key = f"{self.session_prefix}{session_id}"
            
            # Buscar dados atuais
            current_data = self.redis_client.get(key)
            if not current_data:
                return False
            
            session_data = json.loads(current_data)
            
            # Atualizar atividade
            session_data["last_activity"] = datetime.utcnow().isoformat()
            session_data["activity_count"] = session_data.get("activity_count", 0) + 1
            
            if activity_data:
                session_data["data"].update(activity_data)
            
            # Salvar com TTL renovado
            self.redis_client.setex(
                key,
                self.active_session_ttl,
                json.dumps(session_data)
            )
            
            logger.debug(f"⚡ Atividade da sessão {session_id} atualizada (atividade #{session_data['activity_count']})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar atividade da sessão {session_id}: {e}")
            return False
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obter dados da sessão ativa do Redis
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Dict com dados da sessão ou None se não encontrada
        """
        try:
            if not self.is_available():
                return None
            
            key = f"{self.session_prefix}{session_id}"
            data = self.redis_client.get(key)
            
            if data:
                session_data = json.loads(data)
                logger.debug(f"⚡ Dados da sessão {session_id} recuperados do performance cache")
                return session_data
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao obter dados da sessão {session_id}: {e}")
            return None
    
    def cache_context_for_performance(self, session_id: str, context_data: Dict[str, Any]) -> bool:
        """
        Cachear contexto para otimização de performance durante sessão ativa
        
        Args:
            session_id: ID da sessão
            context_data: Dados do contexto
            
        Returns:
            bool: True se cacheado com sucesso
        """
        try:
            if not self.is_available():
                return False
            
            key = f"{self.context_prefix}{session_id}"
            
            # Preparar dados para cache
            cache_data = {
                "context": context_data,
                "cached_at": datetime.utcnow().isoformat(),
                "session_id": session_id,
                "source": "mongodb_performance_cache"
            }
            
            # Salvar com TTL
            self.redis_client.setex(
                key,
                self.context_ttl,
                json.dumps(cache_data)
            )
            
            logger.debug(f"⚡ Contexto da sessão {session_id} cacheado para performance")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao cachear contexto para performance: {e}")
            return False
    
    def get_cached_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obter contexto cacheado para performance
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Dict com contexto ou None se não encontrado
        """
        try:
            if not self.is_available():
                return None
            
            key = f"{self.context_prefix}{session_id}"
            data = self.redis_client.get(key)
            
            if data:
                cache_data = json.loads(data)
                logger.debug(f"⚡ Contexto da sessão {session_id} recuperado do performance cache")
                return cache_data.get("context")
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao obter contexto cacheado: {e}")
            return None
    
    def cache_user_data(self, username: str, user_data: Dict[str, Any]) -> bool:
        """
        Cachear dados do usuário para otimização de performance
        
        Args:
            username: Username do usuário
            user_data: Dados do usuário
            
        Returns:
            bool: True se cacheado com sucesso
        """
        try:
            if not self.is_available():
                return False
            
            key = f"{self.user_prefix}{username}"
            
            # Preparar dados para cache
            cache_data = {
                "user_data": user_data,
                "cached_at": datetime.utcnow().isoformat(),
                "username": username,
                "source": "mongodb_performance_cache"
            }
            
            # Salvar com TTL
            self.redis_client.setex(
                key,
                self.user_data_ttl,
                json.dumps(cache_data)
            )
            
            logger.debug(f"⚡ Dados do usuário {username} cacheados para performance")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao cachear dados do usuário: {e}")
            return False
    
    def get_cached_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Obter dados do usuário cacheados para performance
        
        Args:
            username: Username do usuário
            
        Returns:
            Dict com dados do usuário ou None se não encontrado
        """
        try:
            if not self.is_available():
                return None
            
            key = f"{self.user_prefix}{username}"
            data = self.redis_client.get(key)
            
            if data:
                cache_data = json.loads(data)
                logger.debug(f"⚡ Dados do usuário {username} recuperados do performance cache")
                return cache_data.get("user_data")
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao obter dados do usuário cacheados: {e}")
            return None
    
    def end_session(self, session_id: str) -> bool:
        """
        Encerrar sessão ativa no Redis
        
        Args:
            session_id: ID da sessão
            
        Returns:
            bool: True se encerrada com sucesso
        """
        try:
            if not self.is_available():
                return False
            
            # Remover dados da sessão
            session_key = f"{self.session_prefix}{session_id}"
            context_key = f"{self.context_prefix}{session_id}"
            
            # Remover chaves
            removed_count = self.redis_client.delete(session_key, context_key)
            
            if removed_count > 0:
                logger.info(f"🔚 Sessão {session_id} encerrada no performance cache ({removed_count} chaves removidas)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao encerrar sessão {session_id}: {e}")
            return False
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Obter lista de sessões ativas
        
        Returns:
            Lista de sessões ativas
        """
        try:
            if not self.is_available():
                return []
            
            # Buscar todas as chaves de sessão
            pattern = f"{self.session_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            active_sessions = []
            for key in keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        session_data = json.loads(data)
                        active_sessions.append({
                            "session_id": session_data.get("session_id"),
                            "username": session_data.get("username"),
                            "started_at": session_data.get("started_at"),
                            "last_activity": session_data.get("last_activity"),
                            "activity_count": session_data.get("activity_count", 0)
                        })
                except Exception as e:
                    logger.debug(f"Erro ao processar sessão {key}: {e}")
                    continue
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter sessões ativas: {e}")
            return []
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Obter estatísticas de performance do Redis
        
        Returns:
            Dict com estatísticas
        """
        try:
            if not self.is_available():
                return {"available": False}
            
            # Contar chaves por tipo
            session_count = len(self.redis_client.keys(f"{self.session_prefix}*"))
            context_count = len(self.redis_client.keys(f"{self.context_prefix}*"))
            user_count = len(self.redis_client.keys(f"{self.user_prefix}*"))
            
            # Informações do Redis
            info = self.redis_client.info()
            
            return {
                "available": True,
                "active_sessions": session_count,
                "cached_contexts": context_count,
                "cached_users": user_count,
                "total_keys": session_count + context_count + user_count,
                "redis_info": {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0),
                    "uptime": info.get("uptime_in_seconds", 0)
                },
                "ttl_config": {
                    "active_session_ttl": self.active_session_ttl,
                    "context_ttl": self.context_ttl,
                    "user_data_ttl": self.user_data_ttl
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas de performance: {e}")
            return {"available": False, "error": str(e)}
    
    def clear_user_performance_cache(self, username: str) -> bool:
        """
        Limpar cache de performance de um usuário específico
        
        Args:
            username: Username do usuário
            
        Returns:
            bool: True se limpo com sucesso
        """
        try:
            if not self.is_available():
                return False
            
            # Buscar todas as chaves relacionadas ao usuário
            user_key = f"{self.user_prefix}{username}"
            
            # Buscar sessões do usuário
            session_keys = []
            for key in self.redis_client.keys(f"{self.session_prefix}*"):
                try:
                    data = self.redis_client.get(key)
                    if data:
                        session_data = json.loads(data)
                        if session_data.get("username") == username:
                            session_keys.append(key)
                            # Também remover contexto relacionado
                            session_id = session_data.get("session_id")
                            if session_id:
                                session_keys.append(f"{self.context_prefix}{session_id}")
                except Exception:
                    continue
            
            # Remover todas as chaves
            all_keys = [user_key] + session_keys
            if all_keys:
                removed_count = self.redis_client.delete(*all_keys)
                logger.info(f"🧹 Cache de performance limpo para usuário {username} ({removed_count} chaves removidas)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar cache de performance do usuário {username}: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Limpar sessões expiradas manualmente (Redis TTL já faz isso automaticamente)
        
        Returns:
            int: Número de sessões limpas
        """
        try:
            if not self.is_available():
                return 0
            
            # Buscar sessões que podem estar expiradas
            pattern = f"{self.session_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            expired_count = 0
            for key in keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        session_data = json.loads(data)
                        last_activity = datetime.fromisoformat(session_data.get("last_activity", ""))
                        
                        # Verificar se sessão está inativa há mais tempo que o TTL
                        if (datetime.utcnow() - last_activity).total_seconds() > self.active_session_ttl:
                            session_id = session_data.get("session_id")
                            if session_id:
                                self.end_session(session_id)
                                expired_count += 1
                except Exception:
                    continue
            
            if expired_count > 0:
                logger.info(f"🧹 Limpeza manual: {expired_count} sessões expiradas removidas")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza de sessões expiradas: {e}")
            return 0
    
    def close(self):
        """Fechar conexão com Redis"""
        if self.redis_client:
            self.redis_client.close()
            logger.info("🔒 Conexão RedisPerformanceService com Redis fechada") 