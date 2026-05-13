# Mapa do Código — Empat.IA

> Guia de referência rápida: onde encontrar cada pedaço do código, o que cada arquivo faz e como os módulos se relacionam.

---

## Estrutura raiz

```
empath-ia/
├── apps/
│   ├── web-ui/           # Frontend do usuário (React + Vite)
│   └── admin-panel/      # Painel do terapeuta (React + Vite)
├── services/
│   ├── gateway-service/  # API Gateway principal (FastAPI)
│   ├── ai-service/       # Integração OpenAI (FastAPI)
│   ├── emotion-service/  # Análise emocional (TensorFlow + DeepFace)
│   ├── knowledge-service/ # RAG controlado pelo Admin: lifecycle, contratos e futura indexação
│   └── voice-service/    # Text-to-Speech (Google Cloud TTS)
├── infrastructure/
│   ├── k8s/              # Manifests Kubernetes
│   ├── terraform/        # Provisionamento GCP
│   └── README.md
├── scripts/              # Utilitários: bootstrap GCP, migrações, seeds
├── data/                 # Volumes Docker (compartilhados entre serviços)
│   └── knowledge/        # Arquivos e artefatos locais do Knowledge Service
├── docs/                 # Documentação (você está aqui)
├── .github/workflows/    # CI/CD (pipeline.yml, deploy.yml)
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
└── README.md
```

---

## `services/gateway-service/`

O gateway é o coração da aplicação. É o único serviço exposto externamente — todos os outros são internos.

```
services/gateway-service/
├── src/
│   ├── main.py                          # App FastAPI, CORS, startup/shutdown e inclusão de routers
│   ├── api/
│   │   ├── auth.py                      # Router /api/auth/* (Google OAuth + JWT)
│   │   ├── chat.py                      # /api/chat/send, send-stream, history, start
│   │   ├── chat_context.py              # initial-message, context, finalize e título
│   │   ├── users.py                     # /api/user/*: perfil, preferências e login
│   │   ├── sessions.py                  # sessões terapêuticas públicas e por usuário
│   │   ├── voice.py                     # proxy para Voice Service e rewrite de audio_url
│   │   ├── emotions.py                  # emoções persistidas e proxy realtime
│   │   ├── prompts.py                   # CRUD/renderização de prompts
│   │   ├── proxy.py                     # proxy legado para AI
│   │   ├── health.py                    # health/config
│   │   ├── admin.py                     # compatibilidade/imports do admin
│   │   ├── admin_dashboard.py           # métricas e status admin
│   │   ├── admin_knowledge.py           # proxy protegido para Knowledge Service
│   │   ├── admin_conversations.py       # conversas e analytics
│   │   ├── admin_sessions.py            # CRUD de therapeutic sessions
│   │   ├── admin_users.py               # CRUD/estatísticas de usuários
│   │   └── admin_contexts.py            # session contexts e user sessions
│   ├── services/
│   │   ├── chat_service.py              # Orquestração de chat e streaming
│   │   ├── registration_service.py      # Fluxo especial da session-1/cadastro
│   │   ├── session_context_service.py   # Finalização e contexto estruturado
│   │   ├── next_session_service.py      # Criação da próxima sessão personalizada
│   │   ├── voice_synthesis_service.py   # Síntese de voz e URLs públicas do gateway
│   │   ├── chat_title_service.py        # Título/subtítulo via AI Service
│   │   ├── user_profile_service.py      # Normalização de perfil e registration_data
│   │   ├── streaming_utils.py           # Chunking de sentenças e frames SSE
│   │   ├── user_service.py              # CRUD de usuários no MongoDB
│   │   ├── therapeutic_session_service.py       # Templates globais de sessões terapêuticas
│   │   ├── user_therapeutic_session_service.py  # Sessões por usuário (unlock, start, complete)
│   │   ├── user_emotion_service.py      # Salvar e consultar emoções por usuário/sessão
│   │   └── prompt_service.py            # CRUD de prompts; fallback hardcoded se banco vazio
│   ├── domain/
│   │   └── conversation_identity.py     # chat_id, legacy_session_id, username e therapeutic_session_id
│   ├── repositories/
│   │   └── conversation_repository.py   # Persistência de conversas e mensagens
│   └── models/
│       └── database.py                  # Conexão Motor (async MongoDB), get_collection(), índices
├── requirements.txt
└── Dockerfile
```

### Arquivos críticos do gateway

**`src/main.py`**
- Cria o app FastAPI, CORS e eventos de startup/shutdown.
- Inicializa MongoDB, índices e prompts padrão.
- Inclui os routers extraídos em `src/api/`.

**`src/models/database.py`**
- `init_mongodb()` — abre conexão Motor na startup
- `get_collection(name)` — retorna coleção pelo nome
- Define índices de segurança em `messages` (compound index em `username + session_id`)

**`src/services/chat_service.py`**
- `process_user_message()` — fluxo principal: salva mensagem do usuário, chama AI Service, salva resposta, gera áudio.
- `process_user_message_stream()` — streaming SSE de texto/áudio.
- `start_or_get_conversation()` — cria/recupera conversa por `chat_id`, preservando `legacy_session_id`.
- Delega cadastro, contexto, próxima sessão, título, perfil e voz para services específicos.

**`src/services/user_therapeutic_session_service.py`**
- `ensure_registration_session()` — garante `session-1` para listagem/progresso da jornada.
- `create_session_1_for_user()` — cria a sessão de onboarding para novos usuários de forma idempotente.
- `create_dynamic_session()` — cria sessão personalizada gerada pela IA
- `can_create_next_session()` — verifica se usuário pode ter nova sessão (sem sessões pendentes)
- `complete_session()` — marca sessão como concluída e aciona geração da próxima

---

## `services/ai-service/`

```
services/ai-service/
├── src/
│   ├── main.py                    # App FastAPI, inclui router openai
│   ├── api/
│   │   └── chat_routes.py         # Chat, streaming, contexto, próxima sessão e util/complete
│   └── services/
│       ├── llm_service.py         # Orquestra OpenAI/local LLM, contexto e geração terapêutica
│       ├── local_llm_service.py   # Loader local GGUF via llama-cpp quando habilitado
│       ├── token_economy_service.py     # MongoDB como repositório + Redis como performance
│       ├── redis_performance_service.py # Cache curto de performance durante sessões ativas
│       ├── session_context_service.py  # Lógica de contexto acumulado entre sessões
│       ├── prompt_client_service.py     # Busca prompts ativos via HTTP no gateway
│       └── deps.py                # Instâncias compartilhadas dos services
├── requirements.txt
└── Dockerfile
```

**Fluxo no AI Service:**
1. Recebe request do gateway em `/chat`, `/openai/chat/stream`, `/openai/generate-session-context` ou `/openai/generate-next-session`
2. Busca prompt ativo via `prompt_client_service.py` (chama `GET /api/prompts/active/{key}` no gateway)
3. Monta contexto: histórico + perfil do usuário + dados emocionais + contexto de sessões anteriores
4. Usa LLM local quando configurado, com fallback OpenAI quando permitido
5. Retorna resposta, contexto estruturado ou próxima sessão personalizada

## `services/knowledge-service/`

Decisão arquitetural: [`docs/architecture/KNOWLEDGE_SERVICE.md`](architecture/KNOWLEDGE_SERVICE.md).

```
services/knowledge-service/
├── src/
│   ├── main.py                         # App FastAPI, health e inclusão do router principal
│   ├── api/
│   │   └── knowledge_routes.py         # Endpoints /api/v1/documents, /retrieve e /audit/events
│   ├── models/
│   │   └── knowledge.py                # Contratos Pydantic de documentos, status e retrieval
│   └── services/
│       └── document_service.py         # Regras de lifecycle e contrato inicial de retrieval
├── tests/
│   └── test_knowledge_service.py       # Testes de health, lifecycle e retrieval contract
├── requirements.txt
└── Dockerfile
```

Este serviço será dono do pipeline de RAG:

- ingestão e validação de documentos enviados pelo Admin;
- extração, normalização e chunking semântico;
- embeddings, busca vetorial, busca lexical e re-ranking;
- versionamento de documentos e índices;
- auditoria de quais chunks foram usados em cada resposta.

O AI Service deverá consumir apenas o contrato interno de recuperação, sem acessar diretamente vector store ou índice lexical.

---

## `services/voice-service/`

```
services/voice-service/
├── src/
│   ├── main.py                    # App FastAPI
│   └── api/
│       └── tts_routes.py          # POST /api/v1/synthesize — gera MP3
├── data/tts_output/               # Arquivos MP3 gerados (volume compartilhado)
├── requirements.txt
└── Dockerfile
```

**Endpoints internos (chamados pelo gateway):**
- `POST /api/v1/synthesize` — gera MP3, retorna `{ audio_url: "/api/v1/audio/{filename}" }`
- `GET /api/v1/audio/{filename}` — serve o arquivo MP3
- `GET /api/v1/model-info` — info sobre o modelo TTS em uso
- `GET /health`

---

## `services/emotion-service/`

```
services/emotion-service/
├── src/
│   ├── main.py                    # App FastAPI (imagem base TensorFlow GPU)
│   └── api/
│       └── emotion_routes.py      # Endpoints de análise emocional
├── requirements.txt
└── Dockerfile                     # FROM tensorflow/tensorflow:2.13.0-gpu
```

**Endpoints internos:**
- `POST /analyze-realtime` — analisa frame base64 com DeepFace + MediaPipe
- `POST /analyze-facial-expression` — analisa arquivo de imagem
- `POST /analyze-video` — analisa vídeo completo
- `GET /health`

---

## `apps/web-ui/`

Frontend principal do usuário.

```
apps/web-ui/
├── src/
│   ├── main.jsx                   # Entry point React
│   ├── App.jsx                    # Router principal, estado de sessão e autenticação
│   ├── components/
│   │   ├── LandingScreen.jsx      # Tela inicial (não autenticado)
│   │   ├── LoginScreen.jsx        # Login com Google + seleção de voz
│   │   ├── Home/
│   │   │   └── HomeScreen.jsx     # Jornada terapêutica: lista de sessões, progresso
│   │   └── Chat/
│   │       └── ChatScreen.tsx     # Tela de chat: mensagens, áudio, análise emocional
│   └── services/
│       ├── api.js                 # Funções de chamada à API (axios)
│       └── audioService.js        # Reprodução de áudio TTS
├── package.json
├── vite.config.js
├── tailwind.config.js
├── .env.production
└── Dockerfile
```

---

## `apps/admin-panel/`

Painel do terapeuta.

```
apps/admin-panel/
├── src/
│   ├── index.js                   # Entry point React
│   ├── App.js                     # Router + AuthProvider
│   ├── contexts/
│   │   └── AuthContext.js         # Contexto de autenticação global
│   ├── pages/
│   │   ├── Dashboard.js           # Visão geral com métricas
│   │   ├── SystemStatus.js        # Health dos microserviços
│   │   ├── UserManagement.js      # Gerenciar usuários
│   │   ├── SessionManagement.js   # Gerenciar sessões terapêuticas
│   │   ├── Analytics.js           # Gráficos de emoções e uso
│   │   ├── Conversations.js       # Visualizar conversas
│   │   ├── PromptManagement.js    # Editar prompts da IA
│   │   └── Settings.js            # Configurações
│   └── services/
│       └── api.js                 # Funções de chamada à API
├── package.json
├── vite.config.js (ou webpack)
├── .env.production
└── Dockerfile
```

---

## `infrastructure/`

```
infrastructure/
├── k8s/
│   ├── namespace.yaml
│   ├── configmap.yaml             # Variáveis não-secretas (GOOGLE_CLIENT_ID, URLs)
│   ├── serviceaccount.yaml        # Workload Identity para GCP
│   ├── ingress.yaml               # GCE Ingress + ManagedCertificate HTTPS
│   ├── gateway/                   # Deployment + Service + HPA
│   ├── ai-service/
│   ├── voice-service/
│   ├── emotion-service/
│   ├── web-ui/
│   ├── admin-panel/
│   ├── mongodb/                   # StatefulSet + PVC
│   └── redis/
├── terraform/
│   ├── main.tf                    # VPC, GKE Autopilot, Artifact Registry
│   ├── secrets.tf                 # GCP Secret Manager
│   ├── dns.tf                     # Cloud DNS (empat-ia.io)
│   ├── iam.tf                     # Service accounts + Workload Identity
│   └── terraform.tfvars.example
└── README.md
```

---

## `scripts/`

```
scripts/
├── bootstrap-gcp.sh               # Setup inicial do projeto GCP (roles, APIs, secrets)
├── migrate-*.py                   # Scripts de migração de schema MongoDB
├── seed-*.py                      # Seeds de dados iniciais (prompts, sessões template)
└── README-models.md               # Instruções para download de modelos (emotion service)
```

---

## `.github/workflows/`

```
.github/workflows/
├── pipeline.yml    # Validação (lint, testes), build de imagens Docker, push para Artifact Registry
└── deploy.yml      # Deploy no GKE: sync secrets, apply k8s manifests, rollout
```

**Secrets necessários nos workflows:**
- `GCP_PROJECT_ID`, `GCP_SA_KEY` — autenticação GCP
- `OPENAI_API_KEY` — sincronizado para Secret Manager
- `VITE_GOOGLE_CLIENT_ID`, `VITE_API_URL` — build args para frontends

---

## Coleções MongoDB

| Coleção | Serviço responsável | Propósito |
|---------|---------------------|-----------|
| `users` | gateway (user_service) | Perfil, preferências, auth Google |
| `conversations` | gateway (chat_service) | Metadados de sessão de chat |
| `messages` | gateway (chat_service) | Mensagens individuais (user/ai) |
| `session_contexts` | gateway/ai-service | Contexto estruturado gerado pela IA ao finalizar sessão |
| `user_therapeutic_sessions` | gateway (user_therapeutic_session_service) | Sessões terapêuticas por usuário |
| `therapeutic_sessions` | gateway (therapeutic_session_service) | Templates globais de sessões |
| `user_emotions` | gateway (user_emotion_service) | Registros de emoções detectadas |
| `prompts` | gateway (prompt_service) | Prompts configuráveis da IA |

---

## Volumes Docker compartilhados

| Volume | Caminho no container | Uso |
|--------|---------------------|-----|
| `tts_output` | `/data/tts_output` | Arquivos MP3 gerados pelo voice service |
| `uploads` | `/data/uploads` | Uploads de arquivos (futuro) |
| `shared` | `/data/shared` | Dados compartilhados entre serviços |

---

*Última atualização: Abril 2026*
