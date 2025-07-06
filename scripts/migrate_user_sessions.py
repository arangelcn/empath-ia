#!/usr/bin/env python3
"""
Script para migrar sessões de usuários existentes
Adiciona os campos 'objective' e 'initial_prompt' das sessões template
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuração do MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:admin123@mongodb:27017/empathia?authSource=admin")
DATABASE_NAME = "empathia"

async def migrate_user_sessions():
    """Migrar sessões de usuários para incluir objective e initial_prompt"""
    client = None
    try:
        # Conectar ao MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        # Collections
        user_sessions_collection = db["user_therapeutic_sessions"]
        template_sessions_collection = db["therapeutic_sessions"]
        
        logger.info("🔄 Iniciando migração de sessões de usuários...")
        
        # Buscar todas as sessões template
        template_sessions = {}
        async for template in template_sessions_collection.find({}):
            session_id = template["session_id"]
            template_sessions[session_id] = {
                "objective": template.get("objective", ""),
                "initial_prompt": template.get("initial_prompt", "")
            }
        
        logger.info(f"📋 Encontradas {len(template_sessions)} sessões template")
        
        # Buscar sessões de usuários que precisam ser migradas
        user_sessions_cursor = user_sessions_collection.find({
            "$or": [
                {"objective": {"$exists": False}},
                {"initial_prompt": {"$exists": False}}
            ]
        })
        
        updated_count = 0
        async for user_session in user_sessions_cursor:
            session_id = user_session["session_id"]
            
            if session_id in template_sessions:
                update_data = {
                    "objective": template_sessions[session_id]["objective"],
                    "initial_prompt": template_sessions[session_id]["initial_prompt"],
                    "updated_at": datetime.utcnow()
                }
                
                # Atualizar sessão do usuário
                result = await user_sessions_collection.update_one(
                    {"_id": user_session["_id"]},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    updated_count += 1
                    logger.info(f"✅ Migrada sessão {session_id} para usuário {user_session.get('username', 'unknown')}")
                else:
                    logger.warning(f"⚠️ Falha ao migrar sessão {session_id}")
            else:
                logger.warning(f"⚠️ Template não encontrado para sessão {session_id}")
        
        logger.info(f"✅ Migração concluída! {updated_count} sessões de usuários atualizadas")
        
        # Verificar resultado
        total_user_sessions = await user_sessions_collection.count_documents({})
        migrated_sessions = await user_sessions_collection.count_documents({
            "objective": {"$exists": True},
            "initial_prompt": {"$exists": True}
        })
        
        logger.info(f"📊 Resultado: {migrated_sessions}/{total_user_sessions} sessões têm os novos campos")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro durante migração: {e}")
        return False
        
    finally:
        if client:
            client.close()
            logger.info("🔌 Conexão MongoDB fechada")

async def main():
    """Função principal"""
    logger.info("🚀 Iniciando script de migração de sessões de usuários")
    
    success = await migrate_user_sessions()
    
    if success:
        logger.info("✅ Script executado com sucesso!")
        sys.exit(0)
    else:
        logger.error("❌ Script falhou!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 