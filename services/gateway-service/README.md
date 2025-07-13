# Gateway Service - Empath.IA

## 📋 Visão Geral

O **Gateway Service** é o coração da arquitetura do Empath.IA, funcionando como um **API Gateway** que orquestra todos os microserviços, gerencia a persistência de dados no MongoDB, e coordena o sistema de sessões terapêuticas personalizadas por usuário.

## 🚀 **ATUALIZAÇÕES RECENTES (2025-01-13)**

### ✅ **Eliminação de Duplicação de Contextos**
- **Problema Resolvido**: Contextos eram salvos duplicadamente em `conversations.session_context` e `session_contexts`
- **Nova Arquitetura**: 
  - `session_contexts` → **Fonte principal** para contextos estruturados
  - `conversations.session_context_ref` → **Referência** ao documento em `session_contexts`
  - **Fallback** mantido para sessões antigas
- **Benefícios**: Redução significativa de espaço em disco e consistência de dados

### ✅ **Integração SessionContextService Corrigida**
- **Problema**: Gateway chamava endpoint incorreto `/chat` em vez de `/openai/generate-session-context`
- **Correção**: Integração completa com SessionContextService do AI Service
- **Formato Correto**: Envia `conversation_text` e `username` conforme esperado
- **Processamento**: Resposta estruturada processada corretamente
- **Persistência**: Contextos salvos diretamente na coleção `session_contexts`

### ✅ **Continuidade Terapêutica Aprimorada**
- **Contexto Anterior**: Método `_get_previous_session_context` otimizado
- **Busca Inteligente**: Prioriza `session_contexts`, fallback para `conversations`
- **Session-1 Preservada**: Lógica especial de cadastro mantida intacta
- **Dados Completos**: Inclui `registration_data` junto com contexto terapêutico

### ✅ **Serialização JSON Corrigida**
- **Problema**: Campos `datetime` causavam erro de serialização
- **Correção**: Conversão automática para ISO string com `isoformat()`
- **Compatibilidade**: Dados temporais preservados em formato padrão

## 🏗️ Arquitetura

### **Serviços Principais**

O Gateway Service é composto por **6 serviços principais** que gerenciam diferentes aspectos da aplicação:

#### 1. **ChatService** (`src/services/chat_service.py`)
- **Responsabilidade**: Gerencia conversas e mensagens entre usuários e IA
- **Funcionalidades**:
  - Processamento de mensagens do usuário com contexto entre sessões
  - Integração com AI Service para respostas contextualizadas
  - Persistência de histórico de conversas com isolamento por usuário
  - Gerenciamento de contexto de conversas e continuidade terapêutica
  - Sistema de onboarding (session-1) com coleta de dados pessoais
  - Finalização automática de sessões com geração de contexto
  - Criação automática de próximas sessões baseada no progresso
  - Integração com Voice Service para síntese de áudio

#### 2. **UserService** (`src/services/user_service.py`)
- **Responsabilidade**: Gerencia usuários e suas preferências
- **Funcionalidades**:
  - CRUD completo de usuários com perfis estruturados
  - Gerenciamento de preferências (voz, tema, idioma)
  - Armazenamento de dados de cadastro (demográficos, terapêuticos)
  - Estatísticas de usuários e histórico de atividade
  - Controle de sessões por usuário
  - Histórico de login e atividade

#### 3. **TherapeuticSessionService** (`src/services/therapeutic_session_service.py`)
- **Responsabilidade**: Gerencia templates de sessões terapêuticas
- **Funcionalidades**:
  - CRUD completo de sessões terapêuticas base
  - Filtros e paginação
  - Controle de sessões ativas/inativas
  - Estatísticas de sessões
  - Prompts iniciais e objetivos terapêuticos

#### 4. **UserTherapeuticSessionService** (`src/services/user_therapeutic_session_service.py`)
- **Responsabilidade**: Gerencia sessões terapêuticas personalizadas por usuário
- **Funcionalidades**:
  - Criação de sessões personalizadas baseadas no perfil do usuário
  - Sistema de desbloqueio sequencial de sessões
  - Controle de progresso individual por sessão
  - Gerenciamento de status (locked/unlocked/started/completed)
  - Criação automática de próximas sessões
  - Histórico de progresso terapêutico

#### 5. **UserEmotionService** (`src/services/user_emotion_service.py`)
- **Responsabilidade**: Gerencia análise e armazenamento de emoções dos usuários
- **Funcionalidades**:
  - Captura de emoções via webcam em tempo real
  - Armazenamento de dados emocionais por usuário e sessão
  - Análise de timeline emocional
  - Geração de resumos e estatísticas emocionais
  - Integração com sistema de contexto de sessões

#### 6. **AdminService** (`src/api/admin.py`)
- **Responsabilidade**: Endpoints administrativos para gestão do sistema
- **Funcionalidades**:
  - Dashboard com estatísticas gerais
  - Gerenciamento de usuários e sessões
  - Análise de conversas e emoções
  - Monitoramento de atividade em tempo real

### **Orquestração de Microserviços**

O Gateway Service orquestra os seguintes microserviços:

- **AI Service** (`http://ai-service:8001`) - Processamento de linguagem natural e contexto
- **Avatar Service** (`http://avatar-service:8002`) - Geração de avatares
- **Emotion Service** (`http://emotion-service:8003`) - Análise de emoções faciais
- **Voice Service** (`http://voice-service:8004`) - Síntese de voz

## 🗄️ Persistência de Dados

### **Collections MongoDB**

#### **`conversations`** - Conversas com contexto
```json
{
  "session_id": "usuario_session-1",
  "username": "usuario",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "user_preferences": {
    "username": "João",
    "selected_voice": "pt-BR-Neural2-A",
    "voice_enabled": true
  },
  "message_count": 10,
  "session_context": {
    "summary": "Usuário completou processo de cadastro",
    "main_themes": ["autoconhecimento", "ansiedade"],
    "key_insights": ["Demonstrou abertura para terapia"],
    "future_sessions": {
      "suggested_topics": ["gestão de ansiedade"]
    }
  },
  "session_finalized": true,
  "context_generated_at": "2024-01-01T00:00:00Z"
}
```

#### **`messages`** - Mensagens com isolamento por usuário
```json
{
  "session_id": "usuario_session-1",
  "username": "usuario",
  "type": "user|ai",
  "content": "Mensagem do usuário ou IA",
  "audio_url": "url-do-audio.mp3",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### **`users`** - Usuários com perfis estruturados
```json
{
  "username": "joao_silva",
  "email": "joao@example.com",
  "preferences": {
    "selected_voice": "pt-BR-Neural2-A",
    "voice_enabled": true
  },
  "user_profile": {
    "personal_info": {
      "idade": {"valor": 28, "categoria": "adulto_jovem"},
      "genero": {"categoria": "masculino"},
      "cor_raca": {"categoria": "pardo"},
      "localizacao": {"cidade": "São Paulo", "estado": "SP"}
    },
    "social_info": {
      "situacao_moradia": {"content": "Mora sozinho"},
      "relacao_familia": {"content": "Família próxima"},
      "ocupacao": {"content": "Desenvolvedor de software"}
    },
    "therapeutic_info": {
      "motivacao_terapia": {"content": "Preciso lidar com ansiedade"},
      "objetivos_identificados": ["gestão de ansiedade", "autoconhecimento"],
      "informacoes_adicionais": {"content": "Busco crescimento pessoal"}
    }
  },
  "profile_completed": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z"
}
```

#### **`therapeutic_sessions`** - Templates de sessões
```json
{
  "session_id": "session-1",
  "title": "Sessão 1: Te conhecendo melhor",
  "subtitle": "Cadastro e coleta de dados iniciais",
  "objective": "Conhecer o usuário e coletar dados para personalização",
  "initial_prompt": "Olá! Vou fazer algumas perguntas para te conhecer melhor...",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### **`user_therapeutic_sessions`** - Sessões personalizadas por usuário
```json
{
  "username": "joao_silva",
  "session_id": "session-2",
  "title": "Sessão 2: Explorando ansiedade",
  "subtitle": "Baseado no seu perfil pessoal",
  "objective": "Trabalhar questões de ansiedade identificadas no cadastro",
  "initial_prompt": "Olá João! Como você está se sentindo desde nossa última conversa?",
  "focus_areas": ["ansiedade", "trabalho", "autoconhecimento"],
  "status": "unlocked",
  "progress": 0,
  "personalized": true,
  "created_at": "2024-01-01T00:00:00Z",
  "based_on_session": "joao_silva_session-1",
  "connection_to_previous": "Continuação do trabalho iniciado na sessão anterior"
}
```

#### **`user_emotions`** - Emoções capturadas por usuário
```json
{
  "username": "joao_silva",
  "session_id": "session-2",
  "emotion": "ansiedade",
  "confidence": 0.85,
  "facial_features": {
    "predominant_emotion": "nervous",
    "secondary_emotions": ["worried", "focused"]
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "source": "webcam_capture"
}
```

## 🔗 Endpoints da API

### **Sistema de Sessões Personalizadas**

#### **Obter Sessões do Usuário**
```http
GET /api/user/{username}/sessions?status=unlocked
```

**Resposta:**
```json
{
  "success": true,
  "sessions": [
    {
      "session_id": "session-1",
      "title": "Sessão 1: Te conhecendo melhor",
      "status": "completed",
      "progress": 100,
      "personalized": false
    },
    {
      "session_id": "session-2", 
      "title": "Sessão 2: Explorando ansiedade",
      "status": "unlocked",
      "progress": 0,
      "personalized": true,
      "focus_areas": ["ansiedade", "trabalho"]
    }
  ]
}
```

#### **Obter Sessão Específica do Usuário**
```http
GET /api/user/{username}/sessions/{session_id}
```

#### **Desbloquear Sessão**
```http
POST /api/user/{username}/sessions/{session_id}/unlock
```

#### **Iniciar Sessão**
```http
POST /api/user/{username}/sessions/{session_id}/start
```

#### **Completar Sessão**
```http
POST /api/user/{username}/sessions/{session_id}/complete
Content-Type: application/json

{
  "progress": 100,
  "status": "completed"
}
```

#### **Progresso do Usuário**
```http
GET /api/user/{username}/progress
```

**Resposta:**
```json
{
  "success": true,
  "progress": {
    "total_sessions": 8,
    "completed_sessions": 2,
    "current_session": "session-3",
    "progress_percentage": 25,
    "next_unlocked_session": "session-3",
    "completion_streak": 2
  }
}
```

### **Sistema de Mensagens com Contexto**

#### **Enviar Mensagem com Contexto**
```http
POST /api/chat/send
Content-Type: application/json

{
  "message": "Estou me sentindo ansioso sobre o trabalho",
  "session_id": "joao_silva_session-2",
  "session_objective": {
    "title": "Sessão 2: Explorando ansiedade",
    "objective": "Trabalhar questões de ansiedade identificadas"
  }
}
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "user_message": {
      "id": "msg_123",
      "content": "Estou me sentindo ansioso sobre o trabalho"
    },
    "ai_response": {
      "id": "msg_124",
      "content": "Entendo que você está se sentindo ansioso. Na nossa sessão anterior, você mencionou que trabalha como desenvolvedor. Pode me contar mais sobre o que especificamente tem te causado ansiedade no trabalho?",
      "audioUrl": "http://voice-service:8004/audio/response_124.mp3",
      "provider": "openai",
      "model": "gpt-4o"
    }
  }
}
```

#### **Finalizar Sessão** ⭐ **ATUALIZADO**
```http
POST /api/chat/finalize/{session_id}
```

**Descrição:** Finaliza sessão e gera contexto estruturado via **SessionContextService** do AI Service. O contexto é salvo na coleção `session_contexts` e a conversa recebe apenas uma referência.

**Resposta:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "context": {
      "summary": "O usuário expressou preocupação com sua ansiedade, principalmente relacionada ao trabalho...",
      "main_themes": ["ansiedade", "trabalho", "estratégias de enfrentamento"],
      "emotional_state": {
        "dominant_emotion": "neutro",
        "emotional_journey": "O usuário apresentou neutralidade emocional...",
        "stability": "estável"
      },
      "key_insights": [
        "importância da expressão emocional",
        "impacto da ansiedade no trabalho"
      ],
      "therapeutic_progress": {
        "engagement_level": "alto",
        "communication_style": "empático e encorajador",
        "areas_of_focus": ["ansiedade no trabalho", "estratégias de enfrentamento"]
      },
      "next_session_recommendations": [
        "explorar gatilhos específicos de ansiedade",
        "praticar técnicas de relaxamento"
      ],
      "session_quality": "excelente",
      "session_id": "usuario_session-2",
      "generated_at": "2025-01-13T22:05:35.602105",
      "generation_method": "session_context_service"
    },
    "manual_termination": true,
    "next_session": {
      "success": true,
      "session_id": "session-3",
      "title": "Sessão 3: Estratégias para ansiedade no trabalho",
      "created": true
    }
  }
}
```

**Novidades na Resposta:**
- **Contexto Estruturado**: Gerado pelo SessionContextService com IA
- **Estado Emocional**: Análise detalhada da jornada emocional
- **Progresso Terapêutico**: Avaliação do engajamento e estilo de comunicação
- **Qualidade da Sessão**: Métrica automática baseada na interação
- **Persistência**: Salvo em `session_contexts`, não duplicado

#### **Contexto da Sessão**
```http
GET /api/chat/context/{session_id}
```

### **Sistema de Emoções**

#### **Emoções do Usuário**
```http
GET /api/emotions/{username}?session_id=session-2&hours_back=24
```

**Resposta:**
```json
{
  "success": true,
  "emotions": [
    {
      "emotion": "ansiedade",
      "confidence": 0.85,
      "timestamp": "2024-01-01T14:30:00Z",
      "session_id": "session-2"
    },
    {
      "emotion": "calma",
      "confidence": 0.75,
      "timestamp": "2024-01-01T14:45:00Z",
      "session_id": "session-2"
    }
  ]
}
```

#### **Resumo Emocional**
```http
GET /api/emotions/{username}/summary?hours_back=24
```

#### **Timeline Emocional**
```http
GET /api/emotions/{username}/timeline?hours_back=24&interval_minutes=5
```

### **Chat & Conversas**

#### **Mensagem Inicial da Sessão**
```http
GET /api/chat/initial-message/{session_id}
```

**Resposta:**
```json
{
  "success": true,
  "initial_message": {
    "content": "Olá João! Como você está se sentindo desde nossa última conversa sobre ansiedade no trabalho?",
    "session_info": {
      "title": "Sessão 2: Explorando ansiedade",
      "objective": "Trabalhar questões de ansiedade identificadas no cadastro",
      "focus_areas": ["ansiedade", "trabalho", "autoconhecimento"]
    }
  }
}
```

#### **Histórico de Conversa**
```http
GET /api/chat/history/{session_id}
```

#### **Conversas com Contexto**
```http
GET /api/chat/conversations-with-context?limit=10
```

### **Gerenciamento de Usuários**

#### **Criar Usuário**
```http
POST /api/user/create
Content-Type: application/json

{
  "username": "joao_silva",
  "email": "joao@example.com",
  "preferences": {
    "selected_voice": "pt-BR-Neural2-A",
    "voice_enabled": true
  }
}
```

#### **Obter Usuário**
```http
GET /api/user/{username}
```

#### **Atualizar Preferências**
```http
PUT /api/user/{username}/preferences
Content-Type: application/json

{
  "selected_voice": "pt-BR-Neural2-B",
  "voice_enabled": false
}
```

#### **Login do Usuário**
```http
POST /api/user/{username}/login
```

#### **Estatísticas do Usuário**
```http
GET /api/user/{username}/stats
```

### **Orquestração de Microserviços**

#### **AI Service** - Processamento com contexto
```http
POST /api/ai/chat
Content-Type: application/json

{
  "message": "Como posso lidar com ansiedade?",
  "session_id": "joao_silva_session-2",
  "conversation_history": [...],
  "session_objective": {...},
  "previous_session_context": {...}
}
```

#### **Emotion Service** - Análise em tempo real
```http
POST /api/emotion/analyze-realtime
Content-Type: application/json

{
  "image_data": "base64_encoded_image",
  "username": "joao_silva",
  "session_id": "session-2"
}
```

#### **Voice Service** - Síntese personalizada
```http
POST /api/voice/speak
Content-Type: application/json

{
  "text": "Resposta personalizada para o usuário",
  "voice": "pt-BR-Neural2-A",
  "speed": 1.0
}
```

## 🚀 Configuração

### **Variáveis de Ambiente**

```bash
# MongoDB
MONGODB_URL=mongodb://admin:admin123@mongodb:27017/empatia_db?authSource=admin
DATABASE_NAME=empatia_db

# Microserviços
AI_SERVICE_URL=http://ai-service:8001
AVATAR_SERVICE_URL=http://avatar-service:8002
EMOTION_SERVICE_URL=http://emotion-service:8003
VOICE_SERVICE_URL=http://voice-service:8004

# Funcionalidades
ENABLE_SESSION_ISOLATION=true
ENABLE_CONTEXT_GENERATION=true
ENABLE_EMOTION_CAPTURE=true
ENABLE_AUTO_SESSION_CREATION=true

# Configurações
DEBUG=true
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=http://localhost:7860,http://localhost:3000
HOT_RELOAD=true
```

### **Docker**

```bash
# Build
docker build -t empath-ia-gateway .

# Run
docker run -p 8000:8000 \
  -e MONGODB_URL=mongodb://localhost:27017/empatia_db \
  -e ENABLE_SESSION_ISOLATION=true \
  empath-ia-gateway
```

### **Desenvolvimento Local**

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar com hot reload
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 Monitoramento

### **Health Check Completo**
```http
GET /health/all
```

**Resposta:**
```json
{
  "gateway": "healthy",
  "database": "connected",
  "services": {
    "ai-service": "healthy",
    "voice-service": "healthy",
    "emotion-service": "healthy",
    "avatar-service": "healthy"
  },
  "features": {
    "session_isolation": "enabled",
    "context_generation": "enabled",
    "emotion_capture": "enabled",
    "auto_session_creation": "enabled"
  }
}
```

### **Configuração do Sistema**
```http
GET /config
```

### **Métricas em Tempo Real**
```http
GET /api/admin/activity/realtime
```

## 🔧 Desenvolvimento

### **Estrutura de Arquivos**
```
src/
├── api/
│   └── admin.py                           # Endpoints administrativos
├── models/
│   └── database.py                        # Configuração MongoDB
├── services/
│   ├── chat_service.py                    # Serviço de chat com contexto
│   ├── user_service.py                    # Serviço de usuários
│   ├── therapeutic_session_service.py     # Templates de sessões
│   ├── user_therapeutic_session_service.py  # Sessões personalizadas
│   └── user_emotion_service.py            # Emoções dos usuários
└── main.py                                # Aplicação FastAPI
```

### **Fluxo de Sessão Completo**

1. **Cadastro (session-1)**:
   - Usuário completa questionário de cadastro
   - Sistema gera perfil estruturado do usuário
   - Sessão é finalizada com contexto

2. **Geração Automática**:
   - AI Service gera próxima sessão baseada no perfil
   - Sessão personalizada é criada no banco
   - Sessão é desbloqueada automaticamente

3. **Conversa Contextualizada**:
   - Usuário inicia conversa com contexto da sessão anterior
   - AI responde com personalização baseada no perfil
   - Emoções são capturadas durante a conversa

4. **Finalização e Continuidade**:
   - Sessão é finalizada automaticamente
   - Contexto é gerado para próxima sessão
   - Ciclo se repete com evolução terapêutica

### **Logs Estruturados**
O serviço utiliza logging estruturado com diferentes níveis:
- `INFO`: Operações normais e fluxo de sessões
- `DEBUG`: Informações detalhadas sobre contexto e personalização
- `WARNING`: Problemas não críticos (AI Service indisponível)
- `ERROR`: Erros e exceções

### **Índices MongoDB**
O serviço cria automaticamente índices para performance:
- `conversations`: session_id (unique), username, created_at
- `messages`: session_id, username, created_at
- `users`: username (unique), email, created_at
- `user_therapeutic_sessions`: (username, session_id) (unique), status, created_at
- `user_emotions`: username, session_id, timestamp

## 🎯 Funcionalidades Principais

### **✅ Implementado**
- [x] Sistema de sessões personalizadas por usuário
- [x] Isolamento de sessões por usuário (`username_session-id`)
- [x] Contexto entre sessões com continuidade terapêutica
- [x] Sistema de onboarding estruturado (session-1)
- [x] Geração automática de próximas sessões
- [x] Perfil estruturado do usuário (pessoal, social, terapêutico)
- [x] Captura de emoções via webcam em tempo real
- [x] Sistema de progresso e desbloqueio sequencial
- [x] Finalização automática com geração de contexto
- [x] Orquestração de microserviços
- [x] Persistência MongoDB com isolamento
- [x] Admin Panel API com análise de emoções
- [x] Health checks completos
- [x] Logging estruturado

### **🔄 Em Desenvolvimento**
- [ ] Cache Redis para contexto e sessões
- [ ] Sistema de notificações push
- [ ] Análise preditiva de progresso
- [ ] Métricas avançadas de engajamento
- [ ] Sistema de recomendações

### **📋 Planejado**
- [ ] Autenticação JWT avançada
- [ ] Rate limiting inteligente
- [ ] Integração com wearables
- [ ] Sistema de backup automático
- [ ] Alertas de regressão terapêutica

## 🔒 Segurança

### **Isolamento de Dados**
- **Sessões**: Cada usuário tem acesso apenas às suas próprias sessões
- **Mensagens**: Filtro duplo por `session_id` e `username`
- **Emoções**: Dados emocionais isolados por usuário
- **Contexto**: Contexto de sessões protegido por usuário

### **Proteções Implementadas**
- ✅ Validação de entrada em todos os endpoints
- ✅ Sanitização de dados sensíveis
- ✅ Logs sem dados pessoais
- ✅ Isolamento de sessões por usuário
- ✅ Validação de propriedade de sessão
- ✅ Controle de acesso baseado em username

## 🐛 Troubleshooting

### **Problemas Comuns**

1. **Sessão não desbloqueada automaticamente**
   ```bash
   # Verificar se a sessão anterior foi finalizada
   curl http://localhost:8000/api/chat/context/usuario_session-1
   
   # Desbloquear manualmente
   curl -X POST http://localhost:8000/api/user/usuario/sessions/session-2/unlock
   ```

2. **Contexto não gerado entre sessões**
   ```bash
   # Verificar logs de finalização
   docker logs empath-ia-gateway-1 | grep "finalize"
   
   # Verificar AI Service
   curl http://localhost:8001/health
   ```

3. **Emoções não sendo capturadas**
   ```bash
   # Verificar Emotion Service
   curl http://localhost:8003/health
   
   # Verificar logs de captura
   docker logs empath-ia-gateway-1 | grep "emotion"
   ```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

**Gateway Service v3.0** - Orquestração Inteligente com Sessões Personalizadas 🚀💙 