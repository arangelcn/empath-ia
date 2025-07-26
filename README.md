# Empath.IA - Plataforma de Terapia Virtual Inteligente

Uma plataforma completa de terapia virtual baseada na abordagem humanística de Carl Rogers, com sistema de sessões personalizadas, análise emocional em tempo real, contexto entre sessões e geração automática de próximas sessões terapêuticas.

## 🚀 **ATUALIZAÇÕES RECENTES (2025-07-26)**

### ✅ **Sistema de Gerenciamento de Prompts via Admin Panel** ⭐ **NOVO**
- **Funcionalidade**: Interface completa para gerenciar prompts do sistema de IA
- **Implementação Completa**:
  - Auto-inicialização de prompts padrão no startup dos serviços
  - API RESTful completa para CRUD de prompts
  - Interface administrativa moderna com React + Tailwind CSS
  - Estatísticas em tempo real (Total, Ativos, por Tipo)
  - Sistema de fallback inteligente para prompts hardcodados
- **Benefícios**: 
  - Prompts editáveis via interface web sem necessidade de redeploy
  - Controle granular de ativação/desativação de prompts
  - Organização por tipos (Sistema, Fallback, Geração de Sessão)
  - Backup automático com fallbacks hardcodados
- **Acesso**: Admin Panel → Menu "Prompts" → http://localhost:3001/prompts

## 🚀 **ATUALIZAÇÕES ANTERIORES (2025-01-13)**

### ✅ **SessionContextService - Sistema de Contextos Totalmente Funcional**
- **Problema Resolvido**: SessionContextService não estava persistindo dados no MongoDB
- **Correção Completa**: 
  - Variáveis de ambiente MongoDB e Redis configuradas
  - Coleções `session_contexts`, `user_session_data`, `session_lifecycle` criadas
  - Rotas OpenAI expostas no FastAPI principal
  - Problemas async/await e Motor driver resolvidos
  - Conflitos de upsert MongoDB corrigidos
- **Resultado**: Contextos estruturados salvos corretamente na coleção `session_contexts`

### ✅ **Eliminação de Duplicação de Dados**
- **Problema**: Contexto duplicado em `conversations.session_context` E `session_contexts`
- **Nova Arquitetura**:
  - `session_contexts` → **Fonte principal** de contextos estruturados
  - `conversations.session_context_ref` → **Referência** ao documento
  - **Fallback** mantido para sessões antigas
- **Benefícios**: Redução significativa de espaço em disco e consistência de dados

### ✅ **Integração Front-end ↔ Backend Corrigida**
- **Gateway Service**: Usa endpoint correto `/openai/generate-session-context`
- **Formato de Dados**: Ajustado para `conversation_text` e `username`
- **Serialização JSON**: Campos datetime convertidos para ISO string
- **Resultado**: Popup de finalização funcionando perfeitamente

### ✅ **Continuidade Terapêutica Aprimorada**
- **Contexto Anterior**: Sessões subsequentes carregam contexto da sessão anterior
- **Session-1 Especial**: Lógica de cadastro preservada com `registration_data`
- **AI Service**: Recebe contexto completo incluindo dados de registro do usuário
- **Busca Inteligente**: Prioriza `session_contexts`, fallback para `conversations`

### ✅ **Documentação Técnica Atualizada**
- **AI Service README**: Endpoints documentados, correções detalhadas
- **Gateway Service README**: Nova arquitetura de contextos explicada
- **Resultado**: Documentação técnica completa e atualizada

## 🎯 Visão Geral

**Empath.IA** é uma solução inovadora que combina inteligência artificial avançada, análise emocional em tempo real e continuidade terapêutica para criar uma experiência terapêutica virtual personalizada e progressiva. O sistema oferece:

### 🌟 Principais Diferenciais

- **🧠 Terapia Personalizada**: Sistema de sessões adaptadas ao perfil individual do usuário
- **🔄 Continuidade Terapêutica**: Contexto mantido entre sessões para progressão natural
- **📊 Análise Emocional**: Detecção de emoções via webcam e análise textual em tempo real
- **🎯 Geração Automática**: Próximas sessões criadas automaticamente baseadas no progresso
- **🔒 Isolamento Seguro**: Dados completamente isolados por usuário para privacidade
- **🎵 Síntese de Voz Neural**: Vozes naturais em português brasileiro via Google Cloud
- **📱 Interface Moderna**: Experiência responsiva otimizada para todos os dispositivos

## ✨ Funcionalidades Principais

### ✅ Sistema de Sessões Personalizadas
- ✅ **Onboarding Estruturado**: Session-1 coleta dados demográficos e terapêuticos
- ✅ **Perfil Padronizado**: Dados organizados em categorias (pessoal, social, terapêutico)
- ✅ **Geração Automática**: IA cria próximas sessões baseadas no contexto e perfil
- ✅ **Desbloqueio Sequencial**: Sessões liberadas conforme progresso do usuário
- ✅ **Objetivos Dinâmicos**: Foco terapêutico adaptado ao desenvolvimento pessoal

### ✅ Inteligência Artificial Avançada
- ✅ **Contexto entre Sessões**: Continuidade terapêutica com memória de conversas anteriores
- ✅ **Prompts Especializados**: Sistema de prompts específicos para abordagem Rogers
- ✅ **Personalização Profunda**: Respostas adaptadas ao perfil e histórico do usuário
- ✅ **Análise de Progresso**: Avaliação contínua do desenvolvimento terapêutico
- ✅ **Fallback Inteligente**: Respostas empáticas quando serviços externos não estão disponíveis

### ✅ Gerenciamento de Prompts ⭐ **NOVO**
- ✅ **Interface Administrativa**: Painel completo para gerenciar prompts via web
- ✅ **CRUD Completo**: Criar, editar, ativar/desativar e excluir prompts
- ✅ **Auto-inicialização**: Prompts padrão criados automaticamente no startup
- ✅ **Organização por Tipos**: Sistema, Fallback, Geração de Sessão, Análise
- ✅ **Estatísticas em Tempo Real**: Métricas de uso e distribuição de prompts
- ✅ **Sistema de Fallback**: Prompts hardcodados como backup automático
- ✅ **Variáveis Dinâmicas**: Suporte a substituição de variáveis nos prompts
- ✅ **Versionamento**: Controle de atualizações com timestamps

### ✅ Análise Emocional em Tempo Real
- ✅ **Captura via Webcam**: Detecção de emoções faciais durante conversas
- ✅ **Timeline Emocional**: Histórico completo das emoções por sessão
- ✅ **Análise Textual**: Identificação de emoções através das mensagens
- ✅ **Integração com Contexto**: Dados emocionais influenciam geração de próximas sessões
- ✅ **Relatórios Detalhados**: Resumos e estatísticas emocionais por usuário

### ✅ Persistência e Segurança
- ✅ **Isolamento Total**: Dados completamente separados por usuário
- ✅ **Histórico Completo**: Todas as conversas e contextos mantidos
- ✅ **Backup Automático**: Contexto de sessões salvo para continuidade
- ✅ **Auditoria Completa**: Logs detalhados de todas as ações
- ✅ **Validação Dupla**: Segurança adicional com validação por username

### �� Em Desenvolvimento
- 🔄 **Análise Preditiva**: Previsão de necessidades terapêuticas
- 🔄 **Avatar 3D Inteligente**: Animação sincronizada com análise emocional
- 🔄 **Métricas Avançadas**: Dashboard completo de progresso terapêutico
- 🔄 **Integração com Wearables**: Dados biométricos para personalização
- 🔄 **Sistema de Notificações**: Lembretes e acompanhamento proativo

## 🏗️ Arquitetura do Sistema

### Visão Geral da Arquitetura

```mermaid
graph TB
    subgraph "Frontend Applications"
        WebUI[Web UI<br/>React + TypeScript]
        AdminPanel[Admin Panel<br/>React Dashboard]
    end
    
    subgraph "Gateway & Orchestration"
        Gateway[Gateway Service<br/>FastAPI + Python<br/>- Session Management<br/>- User Isolation<br/>- Context Generation]
    end
    
    subgraph "AI & Processing Services"
        AI[AI Service<br/>OpenAI GPT-4<br/>- Therapeutic Responses<br/>- Context Between Sessions<br/>- Next Session Generation]
        
        Emotion[Emotion Service<br/>OpenFace + MediaPipe<br/>- Facial Analysis<br/>- Real-time Capture<br/>- Emotion Timeline]
        
        Voice[Voice Service<br/>Google Cloud TTS<br/>- Neural Voices<br/>- Portuguese BR<br/>- Audio Synthesis]
        
        Avatar[Avatar Service<br/>DID-AI Integration<br/>- 3D Animation<br/>- Lip Sync<br/>- Expressions]
    end
    
    subgraph "Data Layer"
        MongoDB[(MongoDB<br/>- User Sessions<br/>- Conversations<br/>- Emotions<br/>- User Profiles)]
    end
    
    WebUI --> Gateway
    AdminPanel --> Gateway
    Gateway --> AI
    Gateway --> Emotion
    Gateway --> Voice
    Gateway --> Avatar
    Gateway --> MongoDB
    
    AI --> MongoDB
    Emotion --> MongoDB
    Voice --> MongoDB
```

### Fluxo de Dados e Sessões

```mermaid
graph LR
    subgraph "Session Flow"
        A[User Login] --> B[Load Profile]
        B --> C{Session-1<br/>Completed?}
        C -->|No| D[Onboarding<br/>Session]
        C -->|Yes| E[Load Personal<br/>Sessions]
        
        D --> F[Generate<br/>User Profile]
        F --> G[Create Next<br/>Session]
        
        E --> H[Select<br/>Session]
        H --> I[Load Session<br/>Context]
        I --> J[Start<br/>Conversation]
        
        J --> K[Process<br/>Messages]
        K --> L[Capture<br/>Emotions]
        L --> M[Generate<br/>AI Response]
        M --> N{Session<br/>Complete?}
        
        N -->|No| K
        N -->|Yes| O[Finalize<br/>Context]
        O --> P[Generate<br/>Next Session]
        P --> Q[Unlock<br/>Next Session]
    end
```

## 🚀 Fluxogramas dos Principais Processos

### 1. Processo de Onboarding (Session-1)

```mermaid
sequenceDiagram
    participant U as User
    participant W as Web UI
    participant G as Gateway
    participant A as AI Service
    participant DB as MongoDB
    
    U->>W: Acessa aplicação
    W->>G: GET /api/chat/initial-message/user_session-1
    G->>DB: Verifica se session-1 existe
    DB-->>G: Session-1 não encontrada
    G->>G: Gera primeira pergunta do cadastro
    G-->>W: Primeira pergunta (idade)
    W-->>U: Exibe primeira pergunta
    
    loop Questionário de Cadastro
        U->>W: Responde pergunta
        W->>G: POST /api/chat/send
        G->>DB: Salva resposta do usuário
        G->>G: Gera próxima pergunta
        G-->>W: Próxima pergunta ou finalização
        W-->>U: Exibe próxima pergunta
    end
    
    U->>W: Completa cadastro
    W->>G: POST /api/chat/send (última resposta)
    G->>DB: Salva perfil estruturado
    G->>G: Marca session-1 como completa
    G->>A: Gera contexto da sessão
    A-->>G: Contexto gerado
    G->>A: Gera próxima sessão (session-2)
    A-->>G: Session-2 personalizada
    G->>DB: Salva session-2 e desbloqueia
    G-->>W: Cadastro finalizado + próxima sessão
    W-->>U: Redirecionamento para home
```

### 2. Fluxo de Sessão Terapêutica

```mermaid
sequenceDiagram
    participant U as User
    participant W as Web UI
    participant G as Gateway
    participant A as AI Service
    participant E as Emotion Service
    participant V as Voice Service
    participant DB as MongoDB
    
    U->>W: Seleciona sessão terapêutica
    W->>G: GET /api/user/{username}/sessions/{session_id}
    G->>DB: Busca sessão personalizada
    DB-->>G: Dados da sessão
    G-->>W: Informações da sessão
    
    W->>G: GET /api/chat/initial-message/{session_id}
    G->>DB: Busca initial_prompt personalizado
    G->>DB: Busca contexto da sessão anterior
    DB-->>G: Contexto + prompt personalizado
    G-->>W: Mensagem inicial contextualizada
    
    loop Conversa Terapêutica
        U->>W: Envia mensagem
        W->>E: Captura emoção via webcam
        E-->>W: Emoção detectada
        W->>G: POST /api/chat/send (mensagem + emoção)
        
        G->>DB: Salva mensagem e emoção
        G->>A: Processa com contexto completo
        Note right of A: - Mensagem atual<br/>- Histórico da sessão<br/>- Contexto sessão anterior<br/>- Perfil do usuário<br/>- Dados emocionais
        
        A-->>G: Resposta terapêutica personalizada
        G->>V: Gera áudio da resposta
        V-->>G: URL do áudio
        G->>DB: Salva resposta com áudio
        G-->>W: Resposta + áudio + emoção
        W-->>U: Exibe resposta e reproduz áudio
    end
    
    U->>W: Finaliza sessão
    W->>G: POST /api/chat/finalize/{session_id}
    G->>A: Gera contexto da sessão
    A-->>G: Contexto estruturado
    G->>A: Gera próxima sessão
    A-->>G: Próxima sessão personalizada
    G->>DB: Salva contexto e próxima sessão
    G-->>W: Sessão finalizada + próxima desbloqueada
    W-->>U: Retorna para home com progresso
```

### 3. Sistema de Contexto Entre Sessões

```mermaid
graph TB
    subgraph "Previous Session Context"
        PS[Previous Session]
        PS --> PC[Session Context]
        PC --> Summary[Summary]
        PC --> Themes[Main Themes]
        PC --> Insights[Key Insights]
        PC --> Emotional[Emotional State]
        PC --> Progress[User Progress]
    end
    
    subgraph "User Profile"
        UP[User Profile]
        UP --> Personal[Personal Info]
        UP --> Social[Social Info]
        UP --> Therapeutic[Therapeutic Info]
        UP --> Keywords[Keywords]
        UP --> Strengths[Strengths]
    end
    
    subgraph "Current Session"
        CS[Current Session]
        CS --> Objective[Session Objective]
        CS --> InitialPrompt[Initial Prompt]
        CS --> FocusAreas[Focus Areas]
        CS --> Connection[Connection to Previous]
    end
    
    subgraph "AI Processing"
        AI[AI Service]
        AI --> ContextPrompt[Context Generation]
        AI --> PersonalizedResponse[Personalized Response]
        AI --> NextSession[Next Session Generation]
    end
    
    Summary --> AI
    Themes --> AI
    Insights --> AI
    Personal --> AI
    Therapeutic --> AI
    Objective --> AI
    
    AI --> PersonalizedResponse
    AI --> NextSession
    
    NextSession --> NewSession[New Personalized Session]
    NewSession --> NewObjective[New Objective]
    NewSession --> NewPrompt[New Initial Prompt]
    NewSession --> NewFocus[New Focus Areas]
```

### 4. Análise Emocional em Tempo Real

```mermaid
graph LR
    subgraph "Emotion Capture"
        Webcam[Webcam Stream] --> Frame[Frame Capture]
        Frame --> Process[Process Image]
        Process --> Detect[Emotion Detection]
    end
    
    subgraph "Text Analysis"
        UserMsg[User Message] --> TextAnalysis[Text Analysis]
        TextAnalysis --> Sentiment[Sentiment Detection]
    end
    
    subgraph "Emotion Service"
        Detect --> EmotionAPI[Emotion API]
        Sentiment --> EmotionAPI
        EmotionAPI --> Confidence[Confidence Score]
        EmotionAPI --> Primary[Primary Emotion]
        EmotionAPI --> Secondary[Secondary Emotions]
    end
    
    subgraph "Storage & Analysis"
        Confidence --> MongoDB[(MongoDB)]
        Primary --> MongoDB
        Secondary --> MongoDB
        MongoDB --> Timeline[Emotion Timeline]
        MongoDB --> Summary[Emotion Summary]
        MongoDB --> Trends[Emotion Trends]
    end
    
    subgraph "Context Integration"
        Timeline --> Context[Session Context]
        Summary --> Context
        Context --> NextSession[Next Session Gen]
        Context --> AIResponse[AI Response]
    end
```

### 5. Geração Automática de Próximas Sessões

```mermaid
graph TB
    subgraph "Session Completion"
        Complete[Session Complete] --> Analyze[Analyze Session]
        Analyze --> ExtractThemes[Extract Themes]
        Analyze --> ExtractInsights[Extract Insights]
        Analyze --> ExtractEmotions[Extract Emotions]
        Analyze --> ExtractProgress[Extract Progress]
    end
    
    subgraph "User Profile Analysis"
        Profile[User Profile] --> Demographics[Demographics]
        Profile --> Therapeutic[Therapeutic Goals]
        Profile --> History[Session History]
        Profile --> Preferences[Preferences]
    end
    
    subgraph "AI Generation"
        AI[AI Service] --> GenerateTitle[Generate Title]
        AI --> GenerateObjective[Generate Objective]
        AI --> GeneratePrompt[Generate Initial Prompt]
        AI --> GenerateFocus[Generate Focus Areas]
        AI --> GenerateConnection[Generate Connection]
    end
    
    ExtractThemes --> AI
    ExtractInsights --> AI
    Demographics --> AI
    Therapeutic --> AI
    History --> AI
    
    GenerateTitle --> NewSession[New Personalized Session]
    GenerateObjective --> NewSession
    GeneratePrompt --> NewSession
    GenerateFocus --> NewSession
    GenerateConnection --> NewSession
    
    NewSession --> SaveDB[(Save to MongoDB)]
    SaveDB --> UnlockSession[Unlock Session]
    UnlockSession --> NotifyUser[Notify User]
```

## 📊 Estrutura de Dados ⭐ **ATUALIZADA**

### Visão Geral do Banco de Dados

O sistema utiliza **MongoDB** como banco de dados principal, com coleções especializadas para diferentes aspectos da aplicação. A arquitetura de dados foi projetada para garantir **isolamento total por usuário**, **continuidade terapêutica** e **eliminação de duplicação**.

### 🆕 **Nova Arquitetura de Contextos (2025-01-13)**

#### **Antes (Duplicação)**
```
conversations.session_context → Dados duplicados
session_contexts → Dados duplicados
```

#### **Depois (Referência)**
```
conversations.session_context_ref → Referência ObjectId
session_contexts → Fonte única de contextos
```

### **Benefícios da Nova Arquitetura**
- ✅ **Eliminação de Duplicação**: Contextos salvos apenas uma vez
- ✅ **Consistência**: Dados sempre atualizados
- ✅ **Performance**: Redução significativa de espaço em disco
- ✅ **Manutenibilidade**: Estrutura mais limpa e organizada

### Collections MongoDB

#### **Coleções Principais**

**users** - Perfis de usuários e preferências
**conversations** - Sessões de conversa com referência a contextos
**session_contexts** - Contextos estruturados de sessões (fonte única)
**messages** - Mensagens individuais das conversas
**user_therapeutic_sessions** - Sessões terapêuticas personalizadas
**user_emotions** - Dados de análise emocional
**therapeutic_sessions** - Templates de sessões terapêuticas
**user_session_data** - Métricas e progresso de sessões
**session_lifecycle** - Ciclo de vida das sessões

#### **Diagrama de Relacionamentos**

```mermaid
erDiagram
    users {
        string username PK
        string email
        object preferences
        object user_profile
        boolean profile_completed
        datetime created_at
        datetime last_login
    }
    
    conversations {
        string session_id PK
        string username FK
        object user_preferences
        int message_count
        objectid session_context_ref FK
        boolean session_finalized
        datetime created_at
        datetime updated_at
        object registration_data
        int registration_step
        boolean is_registration_complete
    }
    
    session_contexts {
        objectid _id PK
        string session_id
        string username FK
        object context
        string conversation_text
        array emotions_data
        string source
        int version
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    messages {
        string id PK
        string session_id FK
        string username FK
        string type
        string content
        string audio_url
        datetime created_at
    }
    
    user_therapeutic_sessions {
        string username FK
        string session_id
        string title
        string objective
        string initial_prompt
        array focus_areas
        string status
        int progress
        boolean personalized
        datetime created_at
    }
    
    user_emotions {
        string username FK
        string session_id
        string emotion
        float confidence
        object facial_features
        datetime timestamp
        string source
    }
    
    therapeutic_sessions {
        string session_id PK
        string title
        string objective
        string initial_prompt
        boolean is_active
        datetime created_at
    }
    
    user_session_data {
        string username FK
        string session_id
        object session_metrics
        object therapeutic_progress
        datetime created_at
        datetime updated_at
    }
    
    session_lifecycle {
        string session_id PK
        string username FK
        string status
        datetime started_at
        datetime completed_at
        object lifecycle_events
    }
    
    users ||--o{ conversations : "has"
    users ||--o{ messages : "sends"
    users ||--o{ user_therapeutic_sessions : "participates"
    users ||--o{ user_emotions : "expresses"
    users ||--o{ session_contexts : "generates"
    users ||--o{ user_session_data : "tracks"
    users ||--o{ session_lifecycle : "manages"
    conversations ||--o{ messages : "contains"
    conversations ||--|| session_contexts : "references"
    therapeutic_sessions ||--o{ user_therapeutic_sessions : "based_on"
```

#### **Detalhes das Coleções Atualizadas**

##### **conversations** ⭐ **ATUALIZADA**
- `session_context_ref`: Referência ObjectId para `session_contexts`
- `registration_data`: Dados de cadastro (session-1)
- `registration_step`: Progresso do cadastro
- `is_registration_complete`: Status de conclusão

##### **session_contexts** 🆕 **NOVA COLEÇÃO**
- `context`: Contexto estruturado gerado pelo SessionContextService
- `conversation_text`: Texto completo da conversa
- `emotions_data`: Dados emocionais capturados
- `source`: Origem da geração (ai_service, gateway_fallback)
- `version`: Controle de versão do contexto

##### **user_session_data** 🆕 **NOVA COLEÇÃO**
- `session_metrics`: Métricas de performance da sessão
- `therapeutic_progress`: Progresso terapêutico estruturado

##### **session_lifecycle** 🆕 **NOVA COLEÇÃO**
- `status`: Status atual da sessão
- `lifecycle_events`: Eventos do ciclo de vida
- `started_at` / `completed_at`: Timestamps de controle
```

## 🛠️ Instalação e Configuração

### Pré-requisitos
- **Docker** 20.10+ e **Docker Compose** 2.0+
- **Node.js** 18+ (para desenvolvimento frontend)
- **Python** 3.11+ (para desenvolvimento backend)
- **Git** para controle de versão

### Configuração Rápida

1. **Clone o repositório**
   ```bash
   git clone https://github.com/seu-usuario/empath-ia.git
   cd empath-ia
   ```

2. **Configure as variáveis de ambiente**
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

3. **Inicie todos os serviços**
   ```bash
   docker compose up -d
   ```

4. **Acesse a aplicação**
   - Interface principal: http://localhost:7860
   - Painel admin: http://localhost:7861  
   - API Gateway: http://localhost:8000
   - Documentação API: http://localhost:8000/docs

### Configuração de Desenvolvimento

Para desenvolvimento com hot reload:

```bash
# Inicie apenas os serviços de infraestrutura
docker compose up -d mongodb

# Execute os serviços em modo desenvolvimento
make dev-all

# Ou execute serviços individuais
make dev-frontend    # Web UI
make dev-gateway     # Gateway Service
make dev-ai          # AI Service
make dev-emotion     # Emotion Service
make dev-voice       # Voice Service
```

## 🔧 Configuração de Serviços

### OpenAI API

Configure sua chave da OpenAI no arquivo `.env`:
```bash
OPENAI_API_KEY=sk-sua-chave-aqui
MODEL_NAME=gpt-4o
```

### Google Cloud Text-to-Speech

1. **Crie um projeto no Google Cloud Console**
2. **Ative a API Text-to-Speech**
3. **Crie uma Service Account e baixe o JSON**
4. **Configure as credenciais**:
   ```bash
   # Coloque o arquivo JSON em services/voice-service/credentials/
   cp sua-service-account.json services/voice-service/credentials/google-cloud-key.json
   ```

### MongoDB

O MongoDB é configurado automaticamente via Docker:
```bash
MONGODB_URL=mongodb://admin:admin123@mongodb:27017/empatia_db?authSource=admin
DATABASE_NAME=empatia_db
```

## 📚 Documentação das APIs

### Gateway Service (Porta 8000)

#### Sistema de Sessões Personalizadas
- **GET** `/api/user/{username}/sessions` - Listar sessões do usuário
- **GET** `/api/user/{username}/sessions/{session_id}` - Obter sessão específica
- **POST** `/api/user/{username}/sessions/{session_id}/unlock` - Desbloquear sessão
- **POST** `/api/user/{username}/sessions/{session_id}/start` - Iniciar sessão
- **POST** `/api/user/{username}/sessions/{session_id}/complete` - Completar sessão
- **GET** `/api/user/{username}/progress` - Progresso do usuário

#### Chat com Contexto ⭐ **ATUALIZADO**
- **POST** `/api/chat/send` - Enviar mensagem com contexto
- **GET** `/api/chat/history/{session_id}` - Buscar histórico
- **GET** `/api/chat/initial-message/{session_id}` - Mensagem inicial personalizada
- **POST** `/api/chat/finalize/{session_id}` - Finalizar sessão com **SessionContextService**
- **GET** `/api/chat/context/{session_id}` - Contexto da sessão (busca em `session_contexts`)

#### Análise Emocional
- **GET** `/api/emotions/{username}` - Emoções do usuário
- **GET** `/api/emotions/{username}/summary` - Resumo emocional
- **GET** `/api/emotions/{username}/timeline` - Timeline emocional
- **POST** `/api/emotion/analyze-realtime` - Análise em tempo real

### AI Service (Porta 8001) ⭐ **ATUALIZADO**
- **POST** `/chat` - Conversa com contexto entre sessões
- **POST** `/openai/generate-session-context` - Gerar contexto estruturado de sessão
- **POST** `/generate-next-session` - Gerar próxima sessão
- **GET** `/health` - Status do serviço

### Voice Service (Porta 8004)
- **POST** `/api/voice/speak` - Sintetizar áudio
- **GET** `/api/voice/voices` - Listar vozes disponíveis
- **GET** `/health` - Status do serviço

### Emotion Service (Porta 8003)
- **POST** `/api/emotion/analyze-face` - Análise facial
- **POST** `/api/emotion/analyze-video` - Análise de vídeo
- **POST** `/api/emotion/analyze-realtime` - Análise em tempo real
- **GET** `/health` - Status do serviço

## 🎨 Vozes Disponíveis

### Vozes Neurais (Recomendadas)
- **pt-BR-Neural2-A** - Voz feminina natural
- **pt-BR-Neural2-B** - Voz masculina natural
- **pt-BR-Neural2-C** - Voz feminina expressiva

### Vozes WaveNet
- **pt-BR-Wavenet-A** - Voz feminina de alta qualidade
- **pt-BR-Wavenet-B** - Voz masculina de alta qualidade
- **pt-BR-Wavenet-C** - Voz feminina alternativa

### Vozes Standard
- **pt-BR-Standard-A** - Voz feminina padrão
- **pt-BR-Standard-B** - Voz masculina padrão

## 🧪 Testes

### Executar todos os testes
```bash
make test-all
```

### Testes por serviço
```bash
make test-gateway    # Gateway Service
make test-ai         # AI Service
make test-emotion    # Emotion Service
make test-voice      # Voice Service
```

### Testes E2E
```bash
make test-e2e
```

## 📊 Monitoramento

### Health Check Completo
```bash
curl http://localhost:8000/health/all
```

### Logs Estruturados
```bash
# Logs do Gateway
docker logs empath-ia-gateway-service-1

# Logs do AI Service
docker logs empath-ia-ai-service-1

# Logs específicos por sessão
docker logs empath-ia-gateway-service-1 | grep "session_id"
```

## 🚀 Deploy em Produção

### Docker Compose (Recomendado)
```bash
docker compose -f docker-compose.yml up -d
```

### Variáveis de Ambiente de Produção
```bash
# Produção
DEBUG=false
HOT_RELOAD=false
ENABLE_SESSION_ISOLATION=true
ENABLE_CONTEXT_GENERATION=true
ENABLE_EMOTION_CAPTURE=true
ENABLE_AUTO_SESSION_CREATION=true

# Segurança
ALLOWED_ORIGINS=https://seu-dominio.com
CORS_ALLOW_CREDENTIALS=true
```

## 🔒 Segurança

### Isolamento de Dados
- **Sessões por Usuário**: Formato `username_session-id`
- **Validação Dupla**: Filtro por `session_id` e `username`
- **Contexto Protegido**: Apenas dados do próprio usuário
- **Emoções Isoladas**: Dados emocionais completamente separados
- **Eliminação de Duplicação**: Contextos salvos apenas em `session_contexts` com referências

### Proteções Implementadas
- ✅ **Rate Limiting**: Proteção contra spam
- ✅ **CORS**: Configuração segura para produção
- ✅ **Sanitização**: Limpeza de todos os inputs
- ✅ **Logs Seguros**: Sem dados sensíveis em logs
- ✅ **Validação**: Verificação de propriedade de sessões

## 📋 Estrutura do Projeto

```
empath-ia/
├── apps/                          # Aplicações frontend
│   ├── web-ui/                   # Interface principal (React)
│   └── admin-panel/              # Painel administrativo
├── services/                      # Microserviços backend
│   ├── gateway-service/          # API Gateway e orquestração
│   │   └── src/services/
│   │       ├── chat_service.py   # ✅ Chat com SessionContextService
│   │       └── user_service.py   # Gestão de usuários
│   ├── ai-service/               # Inteligência artificial
│   │   └── src/services/
│   │       ├── session_context_service.py  # ✅ Contextos estruturados
│   │       └── openai_service.py # Integração OpenAI
│   ├── emotion-service/          # Análise emocional
│   ├── voice-service/            # Síntese de voz
│   └── avatar-service/           # Avatar 3D (em desenvolvimento)
├── data/                         # Dados e uploads
│   ├── shared/                   # Dados compartilhados
│   ├── uploads/                  # Arquivos enviados
│   └── tts_output/               # Arquivos de áudio
├── docs/                         # Documentação
│   ├── api/                      # Documentação das APIs
│   ├── architecture/             # Diagramas e arquitetura
│   └── user-guide/               # Guia do usuário
├── scripts/                      # Scripts de automação
│   ├── setup_models.sh           # Configuração de modelos
│   ├── migrate_*.py              # Scripts de migração
│   └── cleanup.sh                # Limpeza de dados
├── infrastructure/               # Configurações de infraestrutura
│   └── docker/                   # Dockerfiles base
├── docker-compose.yml            # Orquestração completa
└── Makefile                      # Comandos de automação
```

## 🤝 Contribuição

1. **Fork** o projeto
2. **Crie** uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. **Abra** um Pull Request

### Padrões de Código
- **Python**: PEP 8, Black, isort
- **JavaScript/TypeScript**: ESLint, Prettier
- **Commits**: Conventional Commits
- **Documentação**: Markdown com Mermaid para diagramas

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/empath-ia/issues)
- **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/empath-ia/discussions)
- **Email**: suporte@empath-ia.com

## 🙏 Agradecimentos

- **Carl Rogers** - Inspiração para a abordagem terapêutica centrada na pessoa
- **OpenAI** - Tecnologia de IA conversacional avançada
- **Google Cloud** - Síntese de voz neural de alta qualidade
- **MongoDB** - Banco de dados flexível para dados complexos
- **Comunidade Open Source** - Ferramentas e bibliotecas utilizadas

---

**Empath.IA v2.0** - Terapia Virtual Inteligente com Continuidade e Personalização 🧠💙
