# Gateway Service - Empath.IA

## 📋 Visão Geral

O **Gateway Service** é o coração da arquitetura do Empath.IA, funcionando como um **API Gateway** que orquestra todos os microserviços e gerencia a persistência de dados no MongoDB.

## 🏗️ Arquitetura

### **Serviços Principais**

O Gateway Service é composto por **3 serviços principais** que gerenciam diferentes aspectos da aplicação:

#### 1. **ChatService** (`src/services/chat_service.py`)
- **Responsabilidade**: Gerencia conversas e mensagens entre usuários e IA
- **Funcionalidades**:
  - Processamento de mensagens do usuário
  - Integração com AI Service para respostas
  - Persistência de histórico de conversas
  - Gerenciamento de contexto de conversas
  - Integração com Voice Service para síntese de áudio

#### 2. **UserService** (`src/services/user_service.py`)
- **Responsabilidade**: Gerencia usuários e suas preferências
- **Funcionalidades**:
  - CRUD completo de usuários
  - Gerenciamento de preferências (voz, tema, idioma)
  - Estatísticas de usuários
  - Controle de sessões por usuário
  - Histórico de login e atividade

#### 3. **TherapeuticSessionService** (`src/services/therapeutic_session_service.py`)
- **Responsabilidade**: Gerencia sessões terapêuticas
- **Funcionalidades**:
  - CRUD completo de sessões terapêuticas
  - Filtros e paginação
  - Controle de sessões ativas/inativas
  - Estatísticas de sessões
  - Prompts iniciais personalizados

### **Orquestração de Microserviços**

O Gateway Service orquestra os seguintes microserviços:

- **AI Service** (`http://ai-service:8001`) - Processamento de linguagem natural
- **Avatar Service** (`http://avatar-service:8002`) - Geração de avatares
- **Emotion Service** (`http://emotion-service:8003`) - Análise de emoções
- **Voice Service** (`http://voice-service:8004`) - Síntese de voz

## 🗄️ Persistência de Dados

### **Collections MongoDB**

#### **`conversations`**
```json
{
  "session_id": "user-session-123",
  "user_preferences": {
    "username": "João",
    "selected_voice": "pt-BR-Neural2-A",
    "voice_enabled": true
  },
  "message_count": 10,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### **`messages`**
```json
{
  "session_id": "user-session-123",
  "type": "user|ai",
  "content": "Mensagem do usuário ou IA",
  "audio_url": "url-do-audio.mp3",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### **`users`**
```json
{
  "username": "joao_silva",
  "email": "joao@example.com",
  "preferences": {
    "selected_voice": "pt-BR-Neural2-A",
    "voice_enabled": true,
    "theme": "dark",
    "language": "pt-BR"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z",
  "is_active": true,
  "session_count": 5
}
```

#### **`therapeutic_sessions`**
```json
{
  "session_id": "session-1",
  "title": "Sessão 1: Te conhecendo melhor",
  "subtitle": "Para levantar dados iniciais",
  "objective": "Objetivo terapêutico da sessão",
  "initial_prompt": "Prompt inicial para a IA",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## 🔗 Endpoints da API

### **Chat & Conversas**

#### **Enviar Mensagem**
```http
POST /api/chat/send
Content-Type: application/json

{
  "message": "Olá, como você está?",
  "session_id": "user-session-123"
}
```

#### **Histórico de Conversa**
```http
GET /api/chat/history/{session_id}
```

#### **Iniciar Conversa**
```http
POST /api/chat/start
Content-Type: application/json

{
  "session_id": "user-session-123"
}
```

#### **Preferências do Usuário**
```http
POST /api/user/preferences
Content-Type: application/json

{
  "session_id": "user-session-123",
  "username": "João",
  "selected_voice": "pt-BR-Neural2-A",
  "voice_enabled": true
}
```

### **Admin Panel**

#### **Usuários**
```http
# Criar usuário
POST /api/admin/users

# Listar usuários
GET /api/admin/users?limit=50&offset=0&active_only=true&search=joao

# Obter usuário
GET /api/admin/users/{username}

# Atualizar usuário
PUT /api/admin/users/{username}

# Desativar usuário
DELETE /api/admin/users/{username}

# Estatísticas do usuário
GET /api/admin/users/{username}/stats
```

#### **Sessões Terapêuticas**
```http
# Criar sessão
POST /api/admin/therapeutic-sessions

# Listar sessões
GET /api/admin/therapeutic-sessions?limit=50&offset=0&active_only=false&search=conhecendo

# Obter sessão
GET /api/admin/therapeutic-sessions/{session_id}

# Atualizar sessão
PUT /api/admin/therapeutic-sessions/{session_id}

# Deletar sessão
DELETE /api/admin/therapeutic-sessions/{session_id}
```

#### **Conversas**
```http
# Listar conversas
GET /api/admin/conversations?limit=10&offset=0&search=joao

# Detalhes da conversa
GET /api/admin/conversations/{session_id}
```

#### **Estatísticas**
```http
# Dashboard stats
GET /api/admin/stats

# Análise de emoções
GET /api/admin/emotions/analysis?days=7

# Atividade em tempo real
GET /api/admin/activity/realtime
```

### **Orquestração de Microserviços**

#### **AI Service**
```http
POST /api/ai/chat
```

#### **Avatar Service**
```http
POST /api/avatar/generate
GET /api/avatar/list
```

#### **Emotion Service**
```http
POST /api/emotion/analyze-face
POST /api/emotion/analyze-video
POST /api/emotion/analyze-realtime
```

#### **Voice Service**
```http
POST /api/voice/speak
POST /api/voice/synthesize
GET /api/voice/health
GET /api/voice/config
GET /api/voice/models
GET /api/voice/audio/{filename}
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
docker run -p 8000:8000 empath-ia-gateway
```

### **Desenvolvimento Local**

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 Monitoramento

### **Health Check**
```http
GET /health
```

### **Health All Services**
```http
GET /health/all
```

### **Configuração**
```http
GET /config
```

## 🔧 Desenvolvimento

### **Estrutura de Arquivos**
```
src/
├── api/
│   └── admin.py              # Endpoints administrativos
├── models/
│   └── database.py           # Configuração MongoDB
├── services/
│   ├── chat_service.py       # Serviço de chat
│   ├── user_service.py       # Serviço de usuários
│   └── therapeutic_session_service.py  # Serviço de sessões
└── main.py                   # Aplicação FastAPI
```

### **Logs**
O serviço utiliza logging estruturado com diferentes níveis:
- `INFO`: Operações normais
- `DEBUG`: Informações detalhadas
- `ERROR`: Erros e exceções

### **Índices MongoDB**
O serviço cria automaticamente índices para performance:
- `conversations`: session_id (unique), created_at, updated_at
- `messages`: session_id, created_at, (session_id, created_at)
- `therapeutic_sessions`: session_id (unique), title, is_active, created_at
- `users`: username (unique), email, created_at, last_login

## 🎯 Funcionalidades Principais

### **✅ Implementado**
- [x] Orquestração de microserviços
- [x] Persistência MongoDB
- [x] Gerenciamento de usuários
- [x] Gerenciamento de sessões terapêuticas
- [x] Histórico de conversas
- [x] Integração com AI Service
- [x] Integração com Voice Service
- [x] Admin Panel API
- [x] Health checks
- [x] Logging estruturado
- [x] Índices de performance

### **🔄 Em Desenvolvimento**
- [ ] Cache Redis
- [ ] Autenticação JWT
- [ ] Rate limiting
- [ ] Métricas Prometheus
- [ ] Tracing distribuído

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

**Gateway Service v2.0** - O coração da arquitetura Empath.IA 💙 