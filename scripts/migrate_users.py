#!/usr/bin/env python3
"""
Script para migrar dados de conversas para a nova collection de usuários
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.gateway_service.src.models.database import init_mongodb, get_collection, get_users_collection
from services.gateway_service.src.services.user_service import UserService

async def migrate_users():
    """Migrar dados de conversas para a collection de usuários"""
    try:
        print("🔄 Iniciando migração de usuários...")
        
        # Inicializar MongoDB
        init_mongodb()
        
        # Obter collections
        conversations_collection = get_collection("conversations")
        users_collection = get_users_collection()
        user_service = UserService()
        
        # Buscar todas as conversas
        cursor = conversations_collection.find({})
        conversations = await cursor.to_list(length=None)
        
        print(f"📊 Encontradas {len(conversations)} conversas para migrar")
        
        migrated_users = 0
        skipped_users = 0
        
        for conversation in conversations:
            session_id = conversation.get("session_id", "")
            user_preferences = conversation.get("user_preferences", {})
            username = user_preferences.get("username")
            
            if not username:
                # Tentar extrair username do session_id
                if session_id and "-" in session_id:
                    username = session_id.split("-")[0]
                else:
                    print(f"⚠️  Conversa sem username: {session_id}")
                    skipped_users += 1
                    continue
            
            # Verificar se usuário já existe
            existing_user = await user_service.get_user(username)
            if existing_user:
                print(f"⏭️  Usuário já existe: {username}")
                skipped_users += 1
                continue
            
            # Criar novo usuário
            try:
                # Extrair preferências da conversa
                preferences = {
                    "selected_voice": user_preferences.get("selected_voice", "pt-BR-Neural2-A"),
                    "voice_enabled": user_preferences.get("voice_enabled", True),
                    "theme": user_preferences.get("theme", "dark"),
                    "language": user_preferences.get("language", "pt-BR"),
                    "completed_welcome": user_preferences.get("completed_welcome", False)
                }
                
                # Criar usuário
                await user_service.create_user(
                    username=username,
                    email=user_preferences.get("email"),
                    preferences=preferences
                )
                
                # Atualizar contador de sessões
                await user_service.increment_session_count(username)
                
                print(f"✅ Usuário migrado: {username}")
                migrated_users += 1
                
            except Exception as e:
                print(f"❌ Erro ao migrar usuário {username}: {e}")
                skipped_users += 1
        
        print(f"\n📈 Resumo da migração:")
        print(f"   ✅ Usuários migrados: {migrated_users}")
        print(f"   ⏭️  Usuários ignorados: {skipped_users}")
        print(f"   📊 Total processado: {len(conversations)}")
        
        # Verificar usuários criados
        total_users = await user_service.list_users(limit=1000, active_only=False)
        print(f"   👥 Total de usuários no sistema: {len(total_users)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        return False

async def create_sample_users():
    """Criar alguns usuários de exemplo"""
    try:
        print("🆕 Criando usuários de exemplo...")
        
        init_mongodb()
        user_service = UserService()
        
        sample_users = [
            {
                "username": "joao_silva",
                "email": "joao@example.com",
                "preferences": {
                    "selected_voice": "pt-BR-Neural2-A",
                    "voice_enabled": True,
                    "theme": "dark",
                    "language": "pt-BR"
                }
            },
            {
                "username": "maria_santos",
                "email": "maria@example.com",
                "preferences": {
                    "selected_voice": "pt-BR-Neural2-B",
                    "voice_enabled": False,
                    "theme": "light",
                    "language": "pt-BR"
                }
            },
            {
                "username": "pedro_oliveira",
                "email": "pedro@example.com",
                "preferences": {
                    "selected_voice": "pt-BR-Neural2-A",
                    "voice_enabled": True,
                    "theme": "dark",
                    "language": "pt-BR"
                }
            }
        ]
        
        created_count = 0
        for user_data in sample_users:
            try:
                await user_service.create_user(
                    username=user_data["username"],
                    email=user_data["email"],
                    preferences=user_data["preferences"]
                )
                print(f"✅ Usuário criado: {user_data['username']}")
                created_count += 1
            except ValueError as e:
                print(f"⚠️  Usuário já existe: {user_data['username']}")
            except Exception as e:
                print(f"❌ Erro ao criar usuário {user_data['username']}: {e}")
        
        print(f"📊 Usuários de exemplo criados: {created_count}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar usuários de exemplo: {e}")
        return False

async def main():
    """Função principal"""
    print("🚀 Iniciando script de migração de usuários")
    print("=" * 50)
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "migrate":
            success = await migrate_users()
        elif command == "sample":
            success = await create_sample_users()
        else:
            print("❌ Comando inválido. Use 'migrate' ou 'sample'")
            return
    else:
        # Executar migração por padrão
        success = await migrate_users()
    
    if success:
        print("\n✅ Script executado com sucesso!")
    else:
        print("\n❌ Script falhou!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 