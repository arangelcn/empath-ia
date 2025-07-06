import os
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

# Variáveis de conexão MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:password@mongodb:27017/empatia?authSource=admin")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "empatia")

# Cliente MongoDB global
client = None
database = None

def init_mongodb():
    """Inicializar conexão com MongoDB"""
    global client, database
    
    try:
        logger.info("🔌 Conectando ao MongoDB...")
        
        # Importar aqui para evitar problemas de dependência
        from motor.motor_asyncio import AsyncIOMotorClient
        from pymongo.errors import ConnectionFailure
        
        client = AsyncIOMotorClient(MONGODB_URL)
        database = client[DATABASE_NAME]
        
        # Testar conexão de forma síncrona
        try:
            # Usar o loop atual se existir
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                # Se já há um loop rodando, não podemos usar run_until_complete
                logger.info("✅ MongoDB cliente criado (loop já em execução)")
            except RuntimeError:
                # Não há loop rodando, podemos criar um
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(client.admin.command('ping'))
                    logger.info("✅ MongoDB conectado com sucesso")
                finally:
                    loop.close()
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível testar conexão MongoDB: {e}")
        
        # Criar índices necessários (será feito quando o app iniciar)
        logger.info("✅ MongoDB inicializado")
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar MongoDB: {e}")
        raise

def close_mongodb():
    """Fechar conexão com MongoDB"""
    global client
    
    if client:
        try:
            client.close()
            logger.info("✅ Conexão MongoDB fechada")
        except Exception as e:
            logger.error(f"❌ Erro ao fechar MongoDB: {e}")

def get_database():
    """Obter instância do banco de dados"""
    if database is None:
        raise RuntimeError("MongoDB não foi inicializado")
    return database

def get_collection(collection_name: str):
    """Obter coleção do MongoDB"""
    if database is None:
        raise RuntimeError("MongoDB não foi inicializado")
    return database[collection_name]

def get_therapeutic_sessions_collection():
    """Obter coleção de sessões terapêuticas"""
    if database is None:
        raise RuntimeError("MongoDB não foi inicializado")
    return database["therapeutic_sessions"]

def get_users_collection():
    """Obter coleção de usuários"""
    if database is None:
        raise RuntimeError("MongoDB não foi inicializado")
    return database["users"]

def get_user_therapeutic_sessions_collection():
    """Obter coleção de sessões terapêuticas dos usuários"""
    if database is None:
        raise RuntimeError("MongoDB não foi inicializado")
    return database["user_therapeutic_sessions"]

async def create_indexes():
    """Criar índices necessários para performance"""
    try:
        # Índices para conversas
        conversations = get_collection("conversations")
        await conversations.create_index("session_id", unique=True)
        await conversations.create_index("created_at")
        await conversations.create_index("updated_at")
        
        # Índices para mensagens
        messages = get_collection("messages")
        await messages.create_index("session_id")
        await messages.create_index("created_at")
        await messages.create_index([("session_id", 1), ("created_at", 1)])
        
        # Índices para sessões terapêuticas
        therapeutic_sessions = get_therapeutic_sessions_collection()
        await therapeutic_sessions.create_index("session_id", unique=True)
        await therapeutic_sessions.create_index("title")
        await therapeutic_sessions.create_index("is_active")
        await therapeutic_sessions.create_index("created_at")
        
        # Índices para sessões terapêuticas dos usuários
        user_therapeutic_sessions = get_user_therapeutic_sessions_collection()
        await user_therapeutic_sessions.create_index([("username", 1), ("session_id", 1)], unique=True)
        await user_therapeutic_sessions.create_index("username")
        await user_therapeutic_sessions.create_index("status")
        await user_therapeutic_sessions.create_index("created_at")
        await user_therapeutic_sessions.create_index("completed_at")
        
        # Índices para usuários
        users = get_users_collection()
        await users.create_index("username", unique=True)
        await users.create_index("email")
        await users.create_index("created_at")
        await users.create_index("last_login")
        
        logger.info("✅ Índices MongoDB criados")
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar índices: {e}")
        # Não falhar se não conseguir criar índices 