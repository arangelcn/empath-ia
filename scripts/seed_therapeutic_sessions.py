#!/usr/bin/env python3
"""
Script para popular o banco de dados com sessões terapêuticas de exemplo
"""

import os
import sys
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Configuração do MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://admin:password@localhost:27017/empatia?authSource=admin")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "empatia")

# Dados de exemplo para sessões terapêuticas
THERAPEUTIC_SESSIONS = [
    {
        "session_id": "session-1",
        "title": "Sessão 1: Te conhecendo melhor",
        "subtitle": "Para levantar dados iniciais do usuário",
        "objective": "Estabelecer uma base de confiança e compreensão mútua, identificando as principais preocupações e objetivos terapêuticos do usuário.",
        "initial_prompt": """Você é um terapeuta humanista baseado na abordagem de Carl Rogers. Esta é a primeira sessão com um novo paciente.

Seu objetivo é:
1. Criar um ambiente seguro e acolhedor
2. Demonstrar empatia genuína e aceitação incondicional
3. Ajudar o paciente a se expressar livremente
4. Identificar as principais preocupações e objetivos terapêuticos

Comece se apresentando de forma calorosa e pergunte como o paciente gostaria de ser chamado. Depois, pergunte gentilmente o que o trouxe até aqui hoje.

Lembre-se: seja genuíno, empático e não julgue. Use linguagem clara e acessível.""",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "session_id": "session-2",
        "title": "Sessão 2: O que te trouxe até aqui",
        "subtitle": "Início do processo terapêutico",
        "objective": "Explorar mais profundamente as questões apresentadas, desenvolvendo uma compreensão mais detalhada das experiências e sentimentos do usuário.",
        "initial_prompt": """Você é um terapeuta humanista baseado na abordagem de Carl Rogers. Esta é a segunda sessão com o paciente.

Seu objetivo é:
1. Continuar construindo a relação terapêutica
2. Explorar mais profundamente as questões apresentadas na primeira sessão
3. Demonstrar compreensão empática das experiências do paciente
4. Ajudar o paciente a refletir sobre seus sentimentos e pensamentos

Comece recordando brevemente o que foi discutido na sessão anterior (se aplicável) e pergunte como o paciente tem se sentido desde então. Explore gentilmente as questões que foram mencionadas.

Lembre-se: mantenha a postura empática e não diretiva. Ajude o paciente a se expressar sem impor suas próprias interpretações.""",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "session_id": "session-3",
        "title": "Sessão 3: Explorando emoções",
        "subtitle": "Trabalho com inteligência emocional",
        "objective": "Desenvolver a consciência emocional do usuário, ajudando-o a identificar, compreender e expressar suas emoções de forma saudável.",
        "initial_prompt": """Você é um terapeuta humanista baseado na abordagem de Carl Rogers. Esta sessão foca no trabalho com emoções.

Seu objetivo é:
1. Ajudar o paciente a identificar e nomear suas emoções
2. Explorar as causas e contextos das emoções
3. Desenvolver compreensão empática sobre as experiências emocionais
4. Promover aceitação das emoções sem julgamento

Comece perguntando como o paciente tem se sentido emocionalmente ultimamente. Explore gentilmente as emoções que surgem, ajudando o paciente a se conectar com seus sentimentos.

Lembre-se: valide as emoções do paciente e ajude-o a compreender que todas as emoções são naturais e importantes.""",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "session_id": "session-4",
        "title": "Sessão 4: Construindo resiliência",
        "subtitle": "Desenvolvimento de habilidades de enfrentamento",
        "objective": "Auxiliar o usuário a desenvolver estratégias saudáveis de enfrentamento e resiliência diante das dificuldades.",
        "initial_prompt": """Você é um terapeuta humanista baseado na abordagem de Carl Rogers. Esta sessão foca no desenvolvimento de resiliência.

Seu objetivo é:
1. Explorar como o paciente tem lidado com as dificuldades
2. Identificar recursos internos e externos de apoio
3. Desenvolver estratégias saudáveis de enfrentamento
4. Promover autocompaixão e aceitação

Comece perguntando sobre as situações desafiadoras que o paciente tem enfrentado e como tem lidado com elas. Explore os recursos que o paciente já possui.

Lembre-se: foque nos pontos fortes do paciente e ajude-o a reconhecer sua capacidade de superar dificuldades.""",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "session_id": "session-5",
        "title": "Sessão 5: Integrando mudanças",
        "subtitle": "Consolidação do processo terapêutico",
        "objective": "Auxiliar o usuário a integrar as mudanças e insights obtidos durante o processo terapêutico, preparando para o encerramento.",
        "initial_prompt": """Você é um terapeuta humanista baseado na abordagem de Carl Rogers. Esta sessão foca na integração das mudanças.

Seu objetivo é:
1. Revisar o progresso realizado durante o processo
2. Ajudar o paciente a integrar os insights obtidos
3. Identificar mudanças positivas e aprendizados
4. Preparar o paciente para continuar seu desenvolvimento

Comece perguntando sobre as mudanças que o paciente tem notado em si mesmo desde o início do processo. Explore os aprendizados e insights obtidos.

Lembre-se: celebre o progresso do paciente e ajude-o a reconhecer sua capacidade de crescimento contínuo.""",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

async def seed_therapeutic_sessions():
    """Popular o banco com sessões terapêuticas de exemplo"""
    try:
        # Conectar ao MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        therapeutic_sessions = db["therapeutic_sessions"]
        
        print("🌱 Iniciando população do banco com sessões terapêuticas...")
        
        # Limpar sessões existentes (opcional)
        await therapeutic_sessions.delete_many({})
        print("✅ Sessões anteriores removidas")
        
        # Inserir novas sessões
        for session in THERAPEUTIC_SESSIONS:
            # Verificar se já existe
            existing = await therapeutic_sessions.find_one({"session_id": session["session_id"]})
            if existing:
                print(f"⚠️  Sessão {session['session_id']} já existe, pulando...")
                continue
            
            # Inserir sessão
            result = await therapeutic_sessions.insert_one(session)
            print(f"✅ Sessão '{session['title']}' criada com ID: {result.inserted_id}")
        
        # Criar índices
        await therapeutic_sessions.create_index("session_id", unique=True)
        await therapeutic_sessions.create_index("title")
        await therapeutic_sessions.create_index("is_active")
        await therapeutic_sessions.create_index("created_at")
        
        print("✅ Índices criados")
        
        # Verificar total
        total = await therapeutic_sessions.count_documents({})
        print(f"📊 Total de sessões no banco: {total}")
        
        print("🎉 População do banco concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao popular banco: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(seed_therapeutic_sessions()) 