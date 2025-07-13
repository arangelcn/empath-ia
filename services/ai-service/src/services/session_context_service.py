"""
SessionContextService - Gerencia contextos de sessão no MongoDB como repositório principal
Responsável por armazenar e recuperar contextos de sessão como dados primários (sem TTL)
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import pymongo
from pymongo import IndexModel

logger = logging.getLogger(__name__)


class SessionContextService:
    """
    Serviço de contexto de sessão usando MongoDB como repositório principal
    
    Este serviço gerencia contextos de sessão como dados primários (sem TTL),
    proporcionando economia de tokens OpenAI através da reutilização de contextos existentes.
    """
    
    def __init__(self):
        """Inicializar serviço de contexto de sessão"""
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "empath_ia")
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        
        # Coleções para dados primários de sessão
        self.session_contexts_collection = "session_contexts"  # Contextos de sessão
        self.user_session_data_collection = "user_session_data"  # Dados de sessão por usuário
        self.session_lifecycle_collection = "session_lifecycle"  # Ciclo de vida de sessões
        
        # Configurações
        self.max_retries = int(os.getenv("MONGODB_MAX_RETRIES", "3"))
        self.timeout = int(os.getenv("MONGODB_TIMEOUT", "5000"))
        
        # Inicializar conexão
        self._initialize_connection()
        
    def _initialize_connection(self):
        """Inicializar conexão com MongoDB"""
        try:
            self.client = AsyncIOMotorClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=self.timeout,
                maxPoolSize=50
            )
            self.database = self.client[self.database_name]
            logger.info("✅ SessionContextService conectado ao MongoDB")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar SessionContextService ao MongoDB: {e}")
            self.client = None
            self.database = None
    
    async def is_available(self) -> bool:
        """Verificar se MongoDB está disponível"""
        try:
            if self.client is None:
                logger.error(f"❌ DEBUG: client é None")
                return False
            
            if self.database is None:
                logger.error(f"❌ DEBUG: database é None")
                return False
            
            # Testar conexão
            logger.debug(f"🔍 DEBUG: Testando conexão MongoDB...")
            await self.client.admin.command("ping")
            logger.debug(f"✅ DEBUG: MongoDB ping bem-sucedido")
            return True
            
        except Exception as e:
            logger.error(f"❌ DEBUG: MongoDB indisponível - {type(e).__name__}: {e}")
            return False
    
    async def initialize_indexes(self):
        """Criar índices necessários para performance"""
        try:
            if not await self.is_available():
                logger.warning("⚠️ MongoDB indisponível - índices não criados")
                return
            
            # Índices para session_contexts
            contexts_collection = self.database[self.session_contexts_collection]
            await contexts_collection.create_index("session_id", unique=True)
            await contexts_collection.create_index("username")
            await contexts_collection.create_index("created_at")
            await contexts_collection.create_index("updated_at")
            await contexts_collection.create_index([("username", 1), ("session_id", 1)])
            
            # Índices para user_session_data
            user_data_collection = self.database[self.user_session_data_collection]
            await user_data_collection.create_index("username")
            await user_data_collection.create_index("session_id")
            await user_data_collection.create_index([("username", 1), ("session_id", 1)], unique=True)
            await user_data_collection.create_index("last_activity")
            
            # Índices para session_lifecycle
            lifecycle_collection = self.database[self.session_lifecycle_collection]
            await lifecycle_collection.create_index("session_id")
            await lifecycle_collection.create_index("username")
            await lifecycle_collection.create_index("status")
            await lifecycle_collection.create_index("created_at")
            
            logger.info("✅ Índices do SessionContextService criados com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar índices do SessionContextService: {e}")
    
    async def save_session_context(self, session_id: str, username: str, context_data: Dict[str, Any], 
                                 conversation_text: str = "", emotions_data: List[Dict] = None) -> bool:
        """
        Salvar contexto de sessão no MongoDB como dados primários
        
        Args:
            session_id: ID da sessão
            username: Username do usuário
            context_data: Dados do contexto gerado
            conversation_text: Texto da conversa original
            emotions_data: Dados de emoções capturadas
            
        Returns:
            bool: True se salvo com sucesso
        """
        try:
            if not await self.is_available():
                logger.warning(f"⚠️ MongoDB indisponível - contexto da sessão {session_id} não salvo")
                return False
            
            collection = self.database[self.session_contexts_collection]
            now = datetime.utcnow()
            
            # Preparar documento para $set (sem created_at para evitar conflito)
            set_document = {
                "session_id": session_id,
                "username": username,
                "context": context_data,
                "conversation_text": conversation_text,
                "emotions_data": emotions_data or [],
                "updated_at": now,
                "version": 1,
                "is_active": True,
                "source": "ai_service_generation"
            }
            
            # Upsert (inserir ou atualizar)
            result = await collection.update_one(
                {"session_id": session_id},
                {
                    "$set": set_document,
                    "$setOnInsert": {"created_at": now}
                },
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"✅ Contexto da sessão {session_id} salvo no repositório principal (usuário: {username})")
                return True
            else:
                logger.warning(f"⚠️ Contexto da sessão {session_id} não foi alterado")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar contexto da sessão {session_id}: {e}")
            return False
    
    async def get_session_context(self, session_id: str, username: str = None) -> Optional[Dict[str, Any]]:
        """
        Recuperar contexto de sessão do repositório principal
        
        Args:
            session_id: ID da sessão
            username: Username do usuário (opcional para validação)
            
        Returns:
            Dict com contexto da sessão ou None se não encontrado
        """
        try:
            if not await self.is_available():
                logger.debug(f"🔄 MongoDB indisponível - contexto da sessão {session_id} não encontrado")
                return None
            
            collection = self.database[self.session_contexts_collection]
            
            # Preparar filtro
            filter_query = {"session_id": session_id, "is_active": True}
            if username:
                filter_query["username"] = username
            
            # Buscar documento
            document = await collection.find_one(filter_query)
            
            if document:
                logger.info(f"✅ Contexto da sessão {session_id} recuperado do repositório principal")
                return {
                    "context": document.get("context"),
                    "username": document.get("username"),
                    "created_at": document.get("created_at"),
                    "updated_at": document.get("updated_at"),
                    "conversation_text": document.get("conversation_text"),
                    "emotions_data": document.get("emotions_data", [])
                }
            
            logger.debug(f"📄 Contexto da sessão {session_id} não encontrado no repositório principal")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar contexto da sessão {session_id}: {e}")
            return None
    
    async def update_session_context(self, session_id: str, username: str, 
                                   context_updates: Dict[str, Any]) -> bool:
        """
        Atualizar contexto de sessão existente
        
        Args:
            session_id: ID da sessão
            username: Username do usuário
            context_updates: Atualizações a serem aplicadas
            
        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            if not await self.is_available():
                logger.warning(f"⚠️ MongoDB indisponível - contexto da sessão {session_id} não atualizado")
                return False
            
            collection = self.database[self.session_contexts_collection]
            
            # Preparar atualização
            update_document = {
                "$set": {
                    "updated_at": datetime.utcnow(),
                    **context_updates
                },
                "$inc": {"version": 1}
            }
            
            # Atualizar documento
            result = await collection.update_one(
                {"session_id": session_id, "username": username, "is_active": True},
                update_document
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Contexto da sessão {session_id} atualizado (usuário: {username})")
                return True
            else:
                logger.warning(f"⚠️ Contexto da sessão {session_id} não encontrado para atualização")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar contexto da sessão {session_id}: {e}")
            return False
    
    async def list_user_sessions(self, username: str, limit: int = 50, 
                               include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Listar sessões de um usuário
        
        Args:
            username: Username do usuário
            limit: Limite de resultados
            include_inactive: Incluir sessões inativas
            
        Returns:
            Lista de sessões do usuário
        """
        try:
            if not await self.is_available():
                logger.debug(f"🔄 MongoDB indisponível - sessões do usuário {username} não encontradas")
                return []
            
            collection = self.database[self.session_contexts_collection]
            
            # Preparar filtro
            filter_query = {"username": username}
            if not include_inactive:
                filter_query["is_active"] = True
            
            # Buscar documentos
            cursor = collection.find(filter_query).sort("updated_at", -1).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            # Formatar resultados
            sessions = []
            for doc in documents:
                sessions.append({
                    "session_id": doc["session_id"],
                    "username": doc["username"],
                    "created_at": doc["created_at"],
                    "updated_at": doc["updated_at"],
                    "version": doc.get("version", 1),
                    "is_active": doc.get("is_active", True),
                    "context_summary": self._summarize_context(doc.get("context", {}))
                })
            
            logger.info(f"✅ Encontradas {len(sessions)} sessões para usuário {username}")
            return sessions
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar sessões do usuário {username}: {e}")
            return []
    
    async def get_session_statistics(self, username: str = None) -> Dict[str, Any]:
        """
        Obter estatísticas de sessões
        
        Args:
            username: Username específico (opcional)
            
        Returns:
            Dict com estatísticas
        """
        try:
            if not await self.is_available():
                logger.debug("🔄 MongoDB indisponível - estatísticas não disponíveis")
                return {}
            
            collection = self.database[self.session_contexts_collection]
            
            # Preparar filtro
            filter_query = {}
            if username:
                filter_query["username"] = username
            
            # Agregações
            pipeline = [
                {"$match": filter_query},
                {"$group": {
                    "_id": None,
                    "total_sessions": {"$sum": 1},
                    "active_sessions": {"$sum": {"$cond": [{"$eq": ["$is_active", True]}, 1, 0]}},
                    "unique_users": {"$addToSet": "$username"},
                    "oldest_session": {"$min": "$created_at"},
                    "newest_session": {"$max": "$updated_at"}
                }}
            ]
            
            cursor = collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                stats = result[0]
                return {
                    "total_sessions": stats.get("total_sessions", 0),
                    "active_sessions": stats.get("active_sessions", 0),
                    "unique_users": len(stats.get("unique_users", [])),
                    "oldest_session": stats.get("oldest_session"),
                    "newest_session": stats.get("newest_session"),
                    "username_filter": username
                }
            
            return {"total_sessions": 0, "active_sessions": 0, "unique_users": 0}
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas de sessões: {e}")
            return {}
    
    async def archive_session(self, session_id: str, username: str) -> bool:
        """
        Arquivar sessão (marcar como inativa)
        
        Args:
            session_id: ID da sessão
            username: Username do usuário
            
        Returns:
            bool: True se arquivada com sucesso
        """
        try:
            if not await self.is_available():
                logger.warning(f"⚠️ MongoDB indisponível - sessão {session_id} não arquivada")
                return False
            
            collection = self.database[self.session_contexts_collection]
            
            # Atualizar documento
            result = await collection.update_one(
                {"session_id": session_id, "username": username},
                {
                    "$set": {
                        "is_active": False,
                        "archived_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    },
                    "$inc": {"version": 1}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Sessão {session_id} arquivada (usuário: {username})")
                return True
            else:
                logger.warning(f"⚠️ Sessão {session_id} não encontrada para arquivamento")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao arquivar sessão {session_id}: {e}")
            return False
    
    def _summarize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Criar resumo do contexto para listagem
        
        Args:
            context: Contexto completo
            
        Returns:
            Dict com resumo do contexto
        """
        return {
            "summary": context.get("summary", "")[:100] + "..." if len(context.get("summary", "")) > 100 else context.get("summary", ""),
            "main_themes": context.get("main_themes", [])[:3],
            "emotional_state": context.get("emotional_state", {}).get("dominant_emotion", ""),
            "session_quality": context.get("session_quality", ""),
            "has_insights": len(context.get("key_insights", [])) > 0
        }
    
    async def cleanup_old_sessions(self, days_old: int = 365) -> int:
        """
        Limpar sessões muito antigas (opcional - apenas para manutenção)
        
        Args:
            days_old: Idade em dias para considerar "antiga"
            
        Returns:
            int: Número de sessões limpas
        """
        try:
            if not await self.is_available():
                logger.warning("⚠️ MongoDB indisponível - limpeza não executada")
                return 0
            
            collection = self.database[self.session_contexts_collection]
            
            # Calcular data limite
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Buscar sessões antigas inativas
            result = await collection.delete_many({
                "is_active": False,
                "updated_at": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"🧹 Limpeza: {deleted_count} sessões antigas removidas")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza de sessões antigas: {e}")
            return 0
    
    async def close(self):
        """Fechar conexão com MongoDB"""
        if self.client:
            self.client.close()
            logger.info("🔒 Conexão SessionContextService com MongoDB fechada") 