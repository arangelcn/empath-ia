#!/usr/bin/env python3
"""
Script para limpar todas as mensagens e sessões de usuários do MongoDB
Mantém apenas os dados de templates (therapeutic_sessions)
"""

import os
import sys
from pymongo import MongoClient
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_mongo_client():
    """Conecta ao MongoDB"""
    try:
        # Configurações do MongoDB
        mongo_host = os.getenv('MONGODB_HOST', 'localhost')
        mongo_port = int(os.getenv('MONGODB_PORT', '27017'))
        mongo_user = os.getenv('MONGODB_USER', 'admin')
        mongo_password = os.getenv('MONGODB_PASSWORD', 'admin123')
        mongo_db = os.getenv('MONGODB_DATABASE', 'empatia')
        
        # String de conexão
        if mongo_user and mongo_password:
            connection_string = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}?authSource=admin"
        else:
            connection_string = f"mongodb://{mongo_host}:{mongo_port}/{mongo_db}"
        
        logger.info(f"🔗 Conectando ao MongoDB: {mongo_host}:{mongo_port}")
        client = MongoClient(connection_string)
        
        # Testar conexão
        client.admin.command('ping')
        logger.info("✅ Conexão com MongoDB estabelecida")
        
        return client, mongo_db
        
    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao MongoDB: {e}")
        return None, None

def clear_all_user_data(confirm: bool = False):
    """
    Limpa todas as mensagens e sessões de usuários
    Mantém apenas os templates (therapeutic_sessions)
    """
    if not confirm:
        logger.warning("⚠️  ATENÇÃO: Esta operação vai apagar TODOS os dados de usuários!")
        logger.warning("⚠️  Isso inclui:")
        logger.warning("   - Todas as mensagens (messages)")
        logger.warning("   - Todas as conversas (conversations)")
        logger.warning("   - Todas as sessões de usuários (user_therapeutic_sessions)")
        logger.warning("   - Todos os usuários (users)")
        logger.warning("   - Mantém apenas os templates (therapeutic_sessions)")
        
        response = input("\n🤔 Tem certeza que deseja continuar? Digite 'CONFIRMAR' para prosseguir: ")
        if response != 'CONFIRMAR':
            logger.info("❌ Operação cancelada pelo usuário")
            return False
    
    # Conectar ao MongoDB
    client, db_name = get_mongo_client()
    if not client:
        return False
    
    try:
        db = client[db_name]
        
        # Listar coleções antes da limpeza
        collections = db.list_collection_names()
        logger.info(f"📋 Coleções encontradas: {collections}")
        
        # Contador de documentos removidos
        total_removed = 0
        
        # 1. Limpar mensagens
        if 'messages' in collections:
            messages_count = db.messages.count_documents({})
            if messages_count > 0:
                result = db.messages.delete_many({})
                logger.info(f"🗑️  Removidas {result.deleted_count} mensagens")
                total_removed += result.deleted_count
            else:
                logger.info("📭 Nenhuma mensagem encontrada")
        
        # 2. Limpar conversas
        if 'conversations' in collections:
            conversations_count = db.conversations.count_documents({})
            if conversations_count > 0:
                result = db.conversations.delete_many({})
                logger.info(f"🗑️  Removidas {result.deleted_count} conversas")
                total_removed += result.deleted_count
            else:
                logger.info("📭 Nenhuma conversa encontrada")
        
        # 3. Limpar sessões de usuários
        if 'user_therapeutic_sessions' in collections:
            user_sessions_count = db.user_therapeutic_sessions.count_documents({})
            if user_sessions_count > 0:
                result = db.user_therapeutic_sessions.delete_many({})
                logger.info(f"🗑️  Removidas {result.deleted_count} sessões de usuários")
                total_removed += result.deleted_count
            else:
                logger.info("📭 Nenhuma sessão de usuário encontrada")
        
        # 4. Limpar usuários
        if 'users' in collections:
            users_count = db.users.count_documents({})
            if users_count > 0:
                result = db.users.delete_many({})
                logger.info(f"🗑️  Removidos {result.deleted_count} usuários")
                total_removed += result.deleted_count
            else:
                logger.info("📭 Nenhum usuário encontrado")
        
        # 5. Verificar templates (não remover)
        if 'therapeutic_sessions' in collections:
            templates_count = db.therapeutic_sessions.count_documents({})
            logger.info(f"📋 Templates mantidos: {templates_count} sessões terapêuticas")
        
        logger.info(f"✅ Limpeza concluída! Total de documentos removidos: {total_removed}")
        
        # Verificar estado final
        logger.info("\n📊 Estado final das coleções:")
        for collection_name in ['messages', 'conversations', 'user_therapeutic_sessions', 'users', 'therapeutic_sessions']:
            if collection_name in collections:
                count = db[collection_name].count_documents({})
                logger.info(f"   {collection_name}: {count} documentos")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro durante a limpeza: {e}")
        return False
    
    finally:
        if client:
            client.close()
            logger.info("🔐 Conexão com MongoDB fechada")

def verify_cleanup():
    """Verifica se a limpeza foi bem-sucedida"""
    client, db_name = get_mongo_client()
    if not client:
        return False
    
    try:
        db = client[db_name]
        
        logger.info("\n🔍 Verificando limpeza...")
        
        # Verificar se as coleções estão vazias
        empty_collections = ['messages', 'conversations', 'user_therapeutic_sessions', 'users']
        all_clean = True
        
        for collection_name in empty_collections:
            count = db[collection_name].count_documents({})
            if count > 0:
                logger.warning(f"⚠️  {collection_name}: {count} documentos restantes")
                all_clean = False
            else:
                logger.info(f"✅ {collection_name}: limpo")
        
        # Verificar se os templates estão preservados
        templates_count = db.therapeutic_sessions.count_documents({})
        if templates_count > 0:
            logger.info(f"✅ therapeutic_sessions: {templates_count} templates preservados")
        else:
            logger.warning("⚠️  Nenhum template encontrado em therapeutic_sessions")
        
        if all_clean:
            logger.info("\n🎉 Limpeza verificada com sucesso!")
            logger.info("💡 Agora você pode testar o frontend com dados limpos")
        else:
            logger.warning("\n⚠️  Alguns dados podem não ter sido removidos completamente")
        
        return all_clean
        
    except Exception as e:
        logger.error(f"❌ Erro durante a verificação: {e}")
        return False
    
    finally:
        if client:
            client.close()

def main():
    """Função principal"""
    logger.info("🧹 Script de Limpeza de Dados - Empath.IA")
    logger.info("=" * 50)
    
    # Verificar se está rodando em ambiente Docker
    if os.path.exists('/.dockerenv'):
        logger.info("🐳 Detectado ambiente Docker")
        # Configurações para Docker
        os.environ.setdefault('MONGODB_HOST', 'mongodb')
        os.environ.setdefault('MONGODB_PORT', '27017')
        os.environ.setdefault('MONGODB_USER', 'admin')
        os.environ.setdefault('MONGODB_PASSWORD', 'admin123')
        os.environ.setdefault('MONGODB_DATABASE', 'empatia')
    else:
        logger.info("💻 Detectado ambiente local")
        # Configurações para ambiente local
        os.environ.setdefault('MONGODB_HOST', 'localhost')
        os.environ.setdefault('MONGODB_PORT', '27017')
        os.environ.setdefault('MONGODB_USER', 'admin')
        os.environ.setdefault('MONGODB_PASSWORD', 'admin123')
        os.environ.setdefault('MONGODB_DATABASE', 'empatia')
    
    # Verificar argumentos
    confirm = len(sys.argv) > 1 and sys.argv[1] == '--confirm'
    
    # Executar limpeza
    if clear_all_user_data(confirm=confirm):
        # Verificar limpeza
        verify_cleanup()
        
        logger.info("\n🚀 Próximos passos:")
        logger.info("1. Acesse o frontend: http://localhost:7860")
        logger.info("2. Teste o onboarding e criação de usuários")
        logger.info("3. Teste as sessões terapêuticas")
        logger.info("4. Verifique se os objetivos das sessões estão funcionando")
        
        return True
    else:
        logger.error("❌ Falha na limpeza dos dados")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 