#!/usr/bin/env python3
"""
Script de migração para corrigir isolamento de sessões entre usuários
Corrige o problema crítico onde mensagens de diferentes usuários eram misturadas

PROBLEMA IDENTIFICADO:
- Usuários diferentes usando mesmo session_id (ex: "session-1") 
- Mensagens misturadas entre usuários
- Violação grave de privacidade

SOLUÇÃO:
- Migrar dados existentes para formato seguro
- Adicionar campo username em mensagens e conversas
- Criar backup antes da migração

Uso: python migrate_session_isolation.py [--dry-run] [--force]
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from typing import Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorClient
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuração do MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:admin123@mongodb:27017/empatia_db?authSource=admin")
DATABASE_NAME = os.getenv("DATABASE_NAME", "empatia_db")

class SessionIsolationMigrator:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Conectar ao MongoDB"""
        try:
            self.client = AsyncIOMotorClient(MONGODB_URL)
            self.db = self.client[DATABASE_NAME]
            # Testar conexão
            await self.client.admin.command('ping')
            logger.info("✅ Conectado ao MongoDB")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar MongoDB: {e}")
            raise
    
    async def close(self):
        """Fechar conexão"""
        if self.client:
            self.client.close()
            logger.info("🔌 Conexão MongoDB fechada")
    
    async def create_backup(self):
        """Criar backup das coleções que serão modificadas"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup messages
            messages = self.db["messages"]
            backup_messages = self.db[f"messages_backup_{timestamp}"]
            async for msg in messages.find():
                await backup_messages.insert_one(msg)
            
            # Backup conversations  
            conversations = self.db["conversations"]
            backup_conversations = self.db[f"conversations_backup_{timestamp}"]
            async for conv in conversations.find():
                await backup_conversations.insert_one(conv)
            
            logger.info(f"✅ Backup criado: messages_backup_{timestamp}, conversations_backup_{timestamp}")
            return timestamp
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            raise
    
    async def analyze_current_state(self) -> Dict[str, Any]:
        """Analisar estado atual para detectar problemas"""
        try:
            messages = self.db["messages"]
            conversations = self.db["conversations"]
            
            # Contar mensagens por session_id
            pipeline = [
                {"$group": {
                    "_id": "$session_id",
                    "message_count": {"$sum": 1},
                    "users_detected": {"$addToSet": "$username"}
                }}
            ]
            
            session_stats = []
            async for stat in messages.aggregate(pipeline):
                session_stats.append(stat)
            
            # Identificar sessões problemáticas (sem username ou com múltiplos usuários)
            problematic_sessions = []
            for stat in session_stats:
                session_id = stat["_id"]
                users = [u for u in stat["users_detected"] if u is not None]
                
                if len(users) == 0:
                    problematic_sessions.append({
                        "session_id": session_id,
                        "issue": "missing_username",
                        "message_count": stat["message_count"]
                    })
                elif len(users) > 1:
                    problematic_sessions.append({
                        "session_id": session_id,
                        "issue": "multiple_users",
                        "users": users,
                        "message_count": stat["message_count"]
                    })
            
            total_messages = await messages.count_documents({})
            total_conversations = await conversations.count_documents({})
            
            analysis = {
                "total_messages": total_messages,
                "total_conversations": total_conversations,
                "total_sessions": len(session_stats),
                "problematic_sessions": problematic_sessions,
                "issues_found": len(problematic_sessions)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise: {e}")
            raise
    
    async def migrate_messages(self, dry_run: bool = True) -> int:
        """Migrar mensagens para adicionar username onde ausente"""
        try:
            messages = self.db["messages"]
            conversations = self.db["conversations"]
            
            # Buscar mensagens sem username
            cursor = messages.find({"username": {"$in": [None, ""]}})
            
            updated_count = 0
            
            async for msg in cursor:
                session_id = msg["session_id"]
                
                # Tentar extrair username do session_id
                username = None
                if "_" in session_id:
                    username = session_id.split("_", 1)[0]
                else:
                    # Buscar username na conversa correspondente
                    conv = await conversations.find_one({"session_id": session_id})
                    if conv and conv.get("user_preferences", {}).get("username"):
                        username = conv["user_preferences"]["username"]
                
                if username and not dry_run:
                    # Atualizar mensagem com username
                    await messages.update_one(
                        {"_id": msg["_id"]},
                        {"$set": {"username": username}}
                    )
                
                if username:
                    updated_count += 1
                    logger.info(f"{'[DRY-RUN] ' if dry_run else ''}Atualizando mensagem {msg['_id']} com username: {username}")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"❌ Erro na migração de mensagens: {e}")
            raise
    
    async def migrate_conversations(self, dry_run: bool = True) -> int:
        """Migrar conversas para adicionar username onde ausente"""
        try:
            conversations = self.db["conversations"]
            
            # Buscar conversas sem username
            cursor = conversations.find({"username": {"$in": [None, ""]}})
            
            updated_count = 0
            
            async for conv in cursor:
                session_id = conv["session_id"]
                
                # Tentar extrair username do session_id ou user_preferences
                username = None
                if "_" in session_id:
                    username = session_id.split("_", 1)[0]
                elif conv.get("user_preferences", {}).get("username"):
                    username = conv["user_preferences"]["username"]
                
                if username and not dry_run:
                    # Atualizar conversa com username
                    await conversations.update_one(
                        {"_id": conv["_id"]},
                        {"$set": {"username": username}}
                    )
                
                if username:
                    updated_count += 1
                    logger.info(f"{'[DRY-RUN] ' if dry_run else ''}Atualizando conversa {conv['_id']} com username: {username}")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"❌ Erro na migração de conversas: {e}")
            raise
    
    async def create_security_indexes(self):
        """Criar índices de segurança"""
        try:
            messages = self.db["messages"]
            conversations = self.db["conversations"]
            
            # Índices para messages
            await messages.create_index("username")
            await messages.create_index([("session_id", 1), ("username", 1)])
            await messages.create_index([("username", 1), ("created_at", 1)])
            
            # Índices para conversations
            await conversations.create_index("username")
            await conversations.create_index("user_preferences.username")
            
            logger.info("✅ Índices de segurança criados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar índices: {e}")
            raise
    
    async def run_migration(self, dry_run: bool = True, force: bool = False):
        """Executar migração completa"""
        try:
            logger.info("🚀 Iniciando migração de isolamento de sessões")
            logger.info(f"Modo: {'DRY-RUN' if dry_run else 'EXECUÇÃO REAL'}")
            
            # 1. Análise inicial
            logger.info("\n📊 Analisando estado atual...")
            analysis = await self.analyze_current_state()
            
            logger.info(f"Total de mensagens: {analysis['total_messages']}")
            logger.info(f"Total de conversas: {analysis['total_conversations']}")
            logger.info(f"Total de sessões: {analysis['total_sessions']}")
            logger.info(f"Sessões problemáticas: {analysis['issues_found']}")
            
            if analysis['issues_found'] > 0:
                logger.warning("⚠️ Problemas encontrados:")
                for issue in analysis['problematic_sessions']:
                    logger.warning(f"  - {issue['session_id']}: {issue['issue']}")
            
            # 2. Confirmar execução
            if not dry_run and not force:
                response = input("\n⚠️ Confirma execução da migração? (digite 'MIGRAR' para confirmar): ")
                if response != "MIGRAR":
                    logger.info("❌ Migração cancelada pelo usuário")
                    return
            
            # 3. Criar backup (apenas em execução real)
            if not dry_run:
                logger.info("\n💾 Criando backup...")
                backup_timestamp = await self.create_backup()
                logger.info(f"✅ Backup criado: {backup_timestamp}")
            
            # 4. Migrar mensagens
            logger.info("\n📝 Migrando mensagens...")
            msg_count = await self.migrate_messages(dry_run)
            logger.info(f"✅ Mensagens processadas: {msg_count}")
            
            # 5. Migrar conversas
            logger.info("\n💬 Migrando conversas...")
            conv_count = await self.migrate_conversations(dry_run)
            logger.info(f"✅ Conversas processadas: {conv_count}")
            
            # 6. Criar índices (apenas em execução real)
            if not dry_run:
                logger.info("\n🔍 Criando índices de segurança...")
                await self.create_security_indexes()
            
            # 7. Análise final
            logger.info("\n📊 Análise pós-migração...")
            final_analysis = await self.analyze_current_state()
            
            logger.info(f"✅ Migração {'simulada' if dry_run else 'concluída'} com sucesso!")
            logger.info(f"Problemas restantes: {final_analysis['issues_found']}")
            
            if not dry_run and final_analysis['issues_found'] == 0:
                logger.info("🎉 Isolamento de sessões corrigido completamente!")
            
        except Exception as e:
            logger.error(f"❌ Erro na migração: {e}")
            raise

async def main():
    parser = argparse.ArgumentParser(description="Migração de isolamento de sessões")
    parser.add_argument("--dry-run", action="store_true", help="Simular migração sem alterações")
    parser.add_argument("--force", action="store_true", help="Executar sem confirmação")
    
    args = parser.parse_args()
    
    migrator = SessionIsolationMigrator()
    
    try:
        await migrator.connect()
        await migrator.run_migration(dry_run=args.dry_run, force=args.force)
    finally:
        await migrator.close()

if __name__ == "__main__":
    asyncio.run(main()) 