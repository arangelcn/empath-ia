#!/usr/bin/env python3
"""
Script para limpar histórico de mensagens de uma sessão específica
Uso: python scripts/clear_chat_history.py --session_id session-1
"""

import argparse
import sys
import os
from datetime import datetime
from typing import Optional

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar diretamente do módulo correto
try:
    from src.models.database import init_mongodb, get_collection, close_mongodb
except ImportError:
    sys.path.append('services/gateway-service')
    from src.models.database import init_mongodb, get_collection, close_mongodb

def clear_session_messages_sync(session_id: str, confirm: bool = False) -> bool:
    try:
        # Inicializar conexão com MongoDB
        init_mongodb()
        
        # Obter coleções
        messages_collection = get_collection("messages")
        conversations_collection = get_collection("conversations")
        
        # Verificar se a sessão existe
        conversation = conversations_collection.find_one({"session_id": session_id})
        if not conversation:
            print(f"❌ Sessão '{session_id}' não encontrada!")
            return False
        
        # Contar mensagens existentes
        message_count = messages_collection.count_documents({"session_id": session_id})
        
        if message_count == 0:
            print(f"ℹ️  Sessão '{session_id}' não possui mensagens para deletar.")
            return True
        
        # Pedir confirmação se não foi forçada
        if not confirm:
            print(f"⚠️  ATENÇÃO: Você está prestes a deletar {message_count} mensagens da sessão '{session_id}'")
            response = input("Tem certeza? Digite 'yes' para confirmar: ")
            if response.lower() != 'yes':
                print("❌ Operação cancelada pelo usuário.")
                return False
        
        # Deletar mensagens
        result = messages_collection.delete_many({"session_id": session_id})
        
        # Atualizar contador na conversa
        conversations_collection.update_one(
            {"session_id": session_id},
            {"$set": {"message_count": 0, "updated_at": datetime.utcnow()}}
        )
        
        print(f"✅ Sucesso! {result.deleted_count} mensagens deletadas da sessão '{session_id}'")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao limpar mensagens: {e}")
        return False
    finally:
        close_mongodb()

def list_user_sessions_sync(username: str) -> None:
    try:
        init_mongodb()
        conversations_collection = get_collection("conversations")
        cursor = conversations_collection.find({"user_preferences.username": username}).sort("created_at", -1)
        sessions = list(cursor)
        if not sessions:
            print(f"ℹ️  Nenhuma sessão encontrada para o usuário '{username}'")
            return
        print(f"📋 Sessões do usuário '{username}':")
        print("-" * 80)
        for session in sessions:
            session_id = session.get("session_id", "N/A")
            created_at = session.get("created_at", "N/A")
            message_count = session.get("message_count", 0)
            username_pref = session.get("user_preferences", {}).get("username", "N/A")
            print(f"Session ID: {session_id}")
            print(f"Username: {username_pref}")
            print(f"Criada em: {created_at}")
            print(f"Mensagens: {message_count}")
            print("-" * 40)
    except Exception as e:
        print(f"❌ Erro ao listar sessões: {e}")
    finally:
        close_mongodb()

def main():
    parser = argparse.ArgumentParser(description="Limpar histórico de mensagens de uma sessão")
    parser.add_argument("--session_id", help="ID da sessão para limpar")
    parser.add_argument("--username", help="Nome do usuário para listar sessões")
    parser.add_argument("--force", action="store_true", help="Forçar limpeza sem confirmação")
    args = parser.parse_args()
    if args.username:
        list_user_sessions_sync(args.username)
        return
    if not args.session_id:
        print("❌ Você deve especificar --session_id ou --username")
        parser.print_help()
        return
    success = clear_session_messages_sync(args.session_id, args.force)
    if success:
        print("🎉 Limpeza concluída com sucesso!")
    else:
        print("💥 Falha na limpeza!")
        sys.exit(1)

if __name__ == "__main__":
    main() 