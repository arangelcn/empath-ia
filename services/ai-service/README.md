# EmpathIA AI Service

Serviço de Inteligência Artificial para conversas terapêuticas do EmpathIA, integrando OpenAI GPT para respostas personalizadas e contextualizadas com sistema avançado de continuidade entre sessões.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Funcionalidades](#funcionalidades)
- [Configuração](#configuração)
- [API Endpoints](#api-endpoints)
- [Integração OpenAI](#integração-openai)
- [Sistema de Contexto](#sistema-de-contexto)
- [Desenvolvimento](#desenvolvimento)
- [Deploy](#deploy)
- [Monitoramento](#monitoramento)

## 🎯 Visão Geral

O AI Service é o componente central de inteligência artificial do EmpathIA, responsável por:

- Processar mensagens dos usuários em sessões terapêuticas
- Gerar respostas terapêuticas contextualizadas baseadas na abordagem de Carl Rogers
- Integrar com OpenAI GPT para conversas avançadas
- Manter contexto entre sessões terapêuticas
- Gerar automaticamente próximas sessões baseadas no progresso do usuário
- Analisar perfil do usuário para personalização
- Processar contexto histórico para continuidade terapêutica

## 🏗️ Arquitetura

```
AI Service
├── FastAPI (Framework Web)
├── OpenAI Integration (GPT-4/GPT-3.5)
├── Therapeutic Response Engine
├── Session Context Management
├── Next Session Generation
├── User Profile Analysis
└── Conversation History Processing
```

### Componentes Principais

- **FastAPI**: Framework web para APIs REST
- **OpenAI Client**: Integração com GPT-4/GPT-3.5
- **Response Engine**: Lógica para respostas terapêuticas Rogers
- **Context Manager**: Gerenciamento de contexto entre sessões
- **Session Generator**: Geração automática de próximas sessões
- **Profile Analyzer**: Análise de perfil do usuário para personalização

## 🚀 Funcionalidades

### ✅ Implementadas

- [x] **Respostas Terapêuticas Contextualizadas**: Baseadas na abordagem de Carl Rogers
- [x] **Sistema de Contexto entre Sessões**: Continuidade terapêutica entre sessões
- [x] **Geração Automática de Próximas Sessões**: Baseada no progresso do usuário
- [x] **Integração com Perfil do Usuário**: Personalização baseada em dados coletados
- [x] **Otimização de Contexto**: Histórico otimizado com compressão inteligente
- [x] **Sistema de Fallback**: Respostas empáticas quando OpenAI não está disponível
- [x] **Análise de Contexto de Sessão**: Geração de resumos e insights terapêuticos
- [x] **Histórico de Conversas**: Processamento de conversas anteriores
- [x] **Integração OpenAI**: Conexão com GPT-4/GPT-3.5
- [x] **Health Check**: Endpoint de status do serviço
- [x] **Logging Estruturado**: Sistema de logs detalhado
- [x] **CORS**: Suporte a requisições cross-origin

### 🔄 Em Desenvolvimento

- [ ] **Fine-tuning Personalizado**: Modelos específicos para cada usuário
- [ ] **Análise de Emoções Avançada**: Integração com emotion service
- [ ] **Métricas de Progresso**: Avaliação quantitativa do progresso terapêutico
- [ ] **Cache Inteligente**: Respostas em cache para performance
- [ ] **Testes Automatizados**: Suíte completa de testes

### 📋 Planejadas

- [ ] **Multilíngue**: Suporte a múltiplos idiomas
- [ ] **Análise Preditiva**: Previsão de necessidades terapêuticas
- [ ] **Integração com Wearables**: Dados biométricos para personalização
- [ ] **A/B Testing**: Testes de diferentes abordagens terapêuticas

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4o  # ou gpt-3.5-turbo
MAX_TOKENS=1000
TEMPERATURE=0.7

# Service Configuration
AI_SERVICE_PORT=8001
DEBUG=false
LOG_LEVEL=INFO

# Context Optimization
MAX_HISTORY_MESSAGES=6      # Máximo mensagens no histórico
MAX_CONTEXT_TOKENS=2000     # Máximo tokens de contexto
ENABLE_CONTEXT_COMPRESSION=true  # Comprimir conversas longas

# Session Management
ENABLE_SESSION_CONTEXT=true      # Contexto entre sessões
ENABLE_NEXT_SESSION_GENERATION=true  # Geração automática
```

### Instalação Local

```bash
# 1. Clone o repositório
git clone <repository-url>
cd services/ai-service

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# 4. Execute o serviço
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

### Docker

```bash
# Build da imagem
docker build -t empath-ia-ai-service .

# Execução
docker run -p 8001:8001 \
  -e OPENAI_API_KEY=your_key \
  -e MODEL_NAME=gpt-4o \
  empath-ia-ai-service
```

## 🔌 API Endpoints

### Health Check
```http
GET /health
```

**Resposta:**
```json
{
  "status": "healthy",
  "service": "ai-service",
  "timestamp": "2025-01-10T17:45:18.694927",
  "version": "2.0.0",
  "openai_status": "connected",
  "features": {
    "context_between_sessions": true,
    "next_session_generation": true,
    "user_profile_integration": true
  }
}
```

### Chat com Contexto
```http
POST /chat
```

**Request:**
```json
{
  "message": "Estou me sentindo ansioso sobre o trabalho",
  "session_id": "usuario_session-2",
  "conversation_history": [
    {
      "type": "user",
      "content": "Olá, preciso de ajuda"
    },
    {
      "type": "assistant", 
      "content": "Olá! Como posso te ajudar hoje?"
    }
  ],
  "session_objective": {
    "title": "Sessão 2: Explorando ansiedade",
    "objective": "Trabalhar questões de ansiedade relacionadas ao trabalho"
  },
  "initial_prompt": "Continuando nossa conversa sobre ansiedade...",
  "previous_session_context": {
    "summary": "Usuário relatou ansiedade no trabalho",
    "main_themes": ["ansiedade", "trabalho", "stress"],
    "key_insights": ["Dificuldade em gerenciar pressão"]
  }
}
```

**Resposta:**
```json
{
  "response": "Entendo que você está se sentindo ansioso sobre o trabalho. Na nossa sessão anterior, você mencionou dificuldades em gerenciar a pressão. Pode me contar mais sobre o que especificamente tem te causado essa ansiedade?",
  "model": "gpt-4o",
  "session_id": "usuario_session-2",
  "timestamp": "2025-01-10T17:45:18.694927",
  "provider": "openai",
  "success": true,
  "context_used": {
    "previous_session_included": true,
    "history_messages": 2,
    "tokens_used": 450,
    "personalization_applied": true
  }
}
```

### Geração de Contexto de Sessão
```http
POST /generate-session-context
```

**Request:**
```json
{
  "conversation_text": "Usuário: Estou ansioso...\nTerapeuta: Entendo como você está se sentindo...",
  "session_id": "usuario_session-1",
  "emotions_data": [
    {
      "emotion": "ansiedade",
      "confidence": 0.85,
      "timestamp": "2025-01-10T17:30:00Z"
    }
  ]
}
```

**Resposta:**
```json
{
  "success": true,
  "context": {
    "summary": "Usuário relatou ansiedade significativa relacionada ao trabalho",
    "main_themes": ["ansiedade", "trabalho", "stress"],
    "emotional_state": {
      "initial": "ansioso",
      "final": "mais calmo",
      "progression": "Mostrou abertura para conversar"
    },
    "key_insights": [
      "Dificuldade em gerenciar pressão no trabalho",
      "Busca por estratégias de enfrentamento"
    ],
    "therapeutic_notes": {
      "techniques_used": ["escuta ativa", "validação emocional"],
      "user_response": "Engajado e receptivo",
      "engagement_level": "Alto"
    },
    "future_sessions": {
      "suggested_topics": ["técnicas de relaxamento", "gestão de tempo"],
      "areas_to_explore": ["origem da ansiedade", "padrões de pensamento"],
      "therapeutic_goals": ["redução da ansiedade", "melhoria do bem-estar"]
    }
  }
}
```

### Geração de Próxima Sessão
```http
POST /generate-next-session
```

**Request:**
```json
{
  "user_profile": {
    "personal_info": {
      "idade": {"valor": 28, "categoria": "adulto_jovem"},
      "ocupacao": {"content": "Desenvolvedor de software"}
    },
    "therapeutic_info": {
      "motivacao_terapia": {"content": "Preciso lidar com ansiedade no trabalho"},
      "objetivos_identificados": ["gestão de ansiedade", "melhoria no trabalho"]
    }
  },
  "session_context": {
    "summary": "Usuário trabalhou questões de ansiedade no trabalho",
    "main_themes": ["ansiedade", "trabalho", "stress"],
    "therapeutic_notes": {
      "engagement_level": "Alto",
      "techniques_used": ["escuta ativa", "validação emocional"]
    }
  },
  "current_session_id": "usuario_session-1"
}
```

**Resposta:**
```json
{
  "success": true,
  "next_session": {
    "session_id": "session-2",
    "title": "Sessão 2: Estratégias para ansiedade no trabalho",
    "subtitle": "Desenvolvendo ferramentas práticas",
    "objective": "Ensinar técnicas de gestão de ansiedade específicas para o ambiente profissional",
    "initial_prompt": "Olá! Como você está se sentindo desde nossa última conversa sobre ansiedade no trabalho? Hoje vamos focar em desenvolver estratégias práticas para gerenciar esses sentimentos.",
    "focus_areas": ["técnicas de relaxamento", "gestão de tempo", "mindfulness"],
    "therapeutic_approach": "Abordagem centrada na pessoa + técnicas cognitivo-comportamentais",
    "expected_outcomes": [
      "Aprender 3 técnicas de relaxamento",
      "Desenvolver estratégias de gestão de tempo",
      "Praticar mindfulness no trabalho"
    ],
    "connection_to_previous": "Continuação do trabalho sobre ansiedade iniciado na sessão anterior",
    "personalized": true
  }
}
```

### Configuração
```http
GET /config
```

**Resposta:**
```json
{
  "openai_configured": true,
  "model": "gpt-4o",
  "service_port": "8001",
  "debug": false,
  "provider": "openai",
  "context_optimization": {
    "max_history_messages": 6,
    "max_context_tokens": 2000,
    "enable_compression": true
  },
  "session_features": {
    "context_between_sessions": true,
    "next_session_generation": true,
    "user_profile_integration": true
  }
}
```

## 🤖 Integração OpenAI

### Funcionalidades Avançadas

#### ✅ **Contexto entre Sessões**
- Mantém continuidade terapêutica entre diferentes sessões
- Referencia conversas anteriores para personalização
- Adaptação baseada no progresso do usuário

#### ✅ **Geração Automática de Sessões**
- Cria próximas sessões baseadas no contexto atual
- Personalização baseada no perfil do usuário
- Objetivos terapêuticos sequenciais

#### ✅ **Prompts Especializados**
- Sistema de prompts específicos para psicologia Rogers
- Adaptação para diferentes tipos de sessão
- Personalização baseada em dados demográficos

### Exemplo de Prompt Terapêutico

```
Você é um psicólogo especializado na abordagem centrada na pessoa de Carl Rogers.

CONTEXTO DO USUÁRIO:
- Idade: 28 anos (adulto jovem)
- Ocupação: Desenvolvedor de software
- Motivação: Preciso lidar com ansiedade no trabalho

SESSÃO ANTERIOR:
- Usuário relatou ansiedade significativa no trabalho
- Mostrou abertura para conversar sobre o tema
- Técnicas utilizadas: escuta ativa, validação emocional

SESSÃO ATUAL:
- Objetivo: Desenvolver estratégias práticas para ansiedade
- Foco: Técnicas de relaxamento e gestão de tempo

Responda de forma empática, validando os sentimentos e oferecendo insights terapêuticos apropriados.
```

## 🔄 Sistema de Contexto

### Processamento de Contexto entre Sessões

1. **Análise da Sessão Anterior**: Extração de temas, emoções e insights
2. **Geração de Resumo**: Criação de resumo estruturado para próxima sessão
3. **Personalização**: Adaptação baseada no perfil do usuário
4. **Continuidade**: Referência ao progresso nas sessões seguintes

### Otimização de Performance

- **Compressão Inteligente**: Resumo de conversas longas
- **Priorização**: Informações mais relevantes primeiro
- **Cache**: Contextos frequentemente usados
- **Otimização de Tokens**: Redução de ~50% no uso de tokens

## 🛠️ Desenvolvimento

### Estrutura do Projeto

```
services/ai-service/
├── src/
│   ├── main.py                    # Aplicação FastAPI
│   ├── api/
│   │   └── openai_routes.py       # Endpoints da API
│   ├── services/
│   │   └── openai_service.py      # Serviço principal OpenAI
│   ├── models/
│   │   ├── chat.py                # Modelos de dados
│   │   ├── context.py             # Modelos de contexto
│   │   └── session.py             # Modelos de sessão
│   └── utils/
│       ├── prompts.py             # Templates de prompts
│       ├── context_processor.py   # Processamento de contexto
│       └── session_generator.py   # Geração de sessões
├── tests/
│   ├── test_openai.py
│   ├── test_context.py
│   └── test_session_generation.py
├── requirements.txt
├── Dockerfile
└── README.md
```

### Testando Funcionalidades

```bash
# Testar chat com contexto
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Estou ansioso",
    "session_id": "teste_session-1",
    "conversation_history": [],
    "previous_session_context": {
      "summary": "Usuário demonstrou ansiedade",
      "main_themes": ["ansiedade", "trabalho"]
    }
  }'

# Testar geração de contexto
curl -X POST http://localhost:8001/generate-session-context \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_text": "Usuário: Estou ansioso\nTerapeuta: Entendo",
    "session_id": "teste_session-1"
  }'

# Testar geração de próxima sessão
curl -X POST http://localhost:8001/generate-next-session \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {"therapeutic_info": {"motivacao_terapia": {"content": "ansiedade"}}},
    "session_context": {"main_themes": ["ansiedade"]},
    "current_session_id": "teste_session-1"
  }'
```

## 🚀 Deploy

### Docker Compose

```yaml
# docker-compose.yml
ai-service:
  build: ./services/ai-service
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - MODEL_NAME=${MODEL_NAME:-gpt-4o}
    - AI_SERVICE_PORT=8001
    - ENABLE_SESSION_CONTEXT=true
    - ENABLE_NEXT_SESSION_GENERATION=true
  ports:
    - "8001:8001"
  depends_on:
    - gateway-service
  networks:
    - empathia-network
```

## 📊 Monitoramento

### Métricas Importantes

- **Latência de Resposta**: Tempo médio de resposta da OpenAI
- **Uso de Tokens**: Consumo de tokens por sessão
- **Contexto Efficiency**: Taxa de compressão de contexto
- **Session Generation**: Sucessos na geração de próximas sessões
- **Personalização**: Taxa de personalização aplicada
- **Continuidade**: Uso de contexto entre sessões

### Alertas Importantes

- Falha na geração de contexto de sessão
- Erro na geração de próxima sessão
- Uso excessivo de tokens (>3000 por sessão)
- Falha na personalização baseada em perfil
- Problemas de continuidade entre sessões

## 🔒 Segurança

### Dados Sensíveis

- **Perfil do Usuário**: Dados demográficos e terapêuticos
- **Contexto de Sessões**: Informações terapêuticas históricas
- **Conversas**: Conteúdo das sessões terapêuticas
- **API Keys**: Chaves de acesso OpenAI

### Proteções Implementadas

- ✅ Não logging de dados sensíveis
- ✅ Validação de entrada
- ✅ Sanitização de contexto
- ✅ Criptografia de dados em trânsito
- ✅ Controle de acesso baseado em sessão

## 🐛 Troubleshooting

### Problemas Comuns

1. **Contexto não carregado**
   ```bash
   # Verificar logs
   docker logs empath-ia-ai-service-1 | grep "context"
   
   # Verificar variáveis
   curl http://localhost:8001/config | jq '.session_features'
   ```

2. **Geração de sessão falha**
   ```bash
   # Verificar perfil do usuário
   curl http://localhost:8001/generate-next-session \
     -H "Content-Type: application/json" \
     -d '{"user_profile": {...}}'
   ```

3. **Tokens excessivos**
   ```bash
   # Verificar configuração
   curl http://localhost:8001/config | jq '.context_optimization'
   ```

---

**AI Service v2.0** - Inteligência Artificial Terapêutica Avançada 🤖💙 