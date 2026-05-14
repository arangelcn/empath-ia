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
│   ├── ai-service/       # Backend unificado (FastAPI): gateway + AI + orquestração
│   ├── emotion-service/  # Análise emocional (TensorFlow + DeepFace)
│   ├── knowledge-service/ # RAG controlado pelo Admin: lifecycle, contratos e indexação
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

## `services/ai-service/`

O ai-service é o backend unificado — resultado da fusão do antigo `gateway-service` + `ai-service`. É o único serviço exposto externamente; todos os outros são internos.

```
services/ai-service/
├── src/
│   ├── main.py                          # App FastAPI, CORS, lifespan, inclusão de routers
│   ├── app/
│   │   ├── bootstrap/
│   │   │   ├── settings.py              # Configurações via env vars
│   │   │   ├── logging.py              # Setup de logging
│   │   │   ├── dependencies.py          # Container de dependências
│   │   │   └── lifespan.py             # Startup/shutdown (Mongo, índices, prompts)
│   │   ├── api/
│   │   │   ├── public/
│   │   │   │   ├── auth.py              # /api/auth/* (Google OAuth + JWT)
│   │   │   │   ├── chat.py              # /api/chat, /api/chat/stream
│   │   │   │   ├── chat_context.py      # initial-message, context, finalize, título
│   │   │   │   ├── users.py             # /api/user/*: perfil, preferências, login
│   │   │   │   ├── sessions.py          # sessões terapêuticas
│   │   │   │   ├── voice.py             # proxy direto para Voice Service
│   │   │   │   ├── emotions.py          # proxy direto para Emotion Service
│   │   │   │   └── prompts.py           # CRUD/renderização de prompts
│   │   │   ├── admin/
│   │   │   │   ├── dashboard.py         # métricas e status admin
│   │   │   │   ├── users.py             # CRUD/estatísticas de usuários
│   │   │   │   ├── sessions.py          # CRUD de therapeutic sessions
│   │   │   │   ├── conversations.py     # conversas e analytics
│   │   │   │   ├── contexts.py          # session contexts e user sessions
│   │   │   │   └── knowledge.py         # proxy protegido para Knowledge Service
│   │   │   └── internal/
│   │   │       ├── health.py            # /health, /health/all
│   │   │       ├── compatibility.py     # /openai/* (compatibilidade)
│   │   │       └── llm.py               # endpoints internos de LLM
│   │   ├── application/
│   │   │   ├── chat/
│   │   │   │   ├── chat_facade.py       # Entrypoint de chat (novo + compat)
│   │   │   │   ├── stream_facade.py     # Streaming SSE
│   │   │   │   ├── session_context_service.py  # Finalização e contexto estruturado
│   │   │   │   ├── next_session_service.py     # Próxima sessão personalizada
│   │   │   │   └── registration_service.py     # Fluxo session-1/cadastro
│   │   │   ├── llm/
│   │   │   │   ├── runtime_service.py   # Runtime LLM (LangChain providers)
│   │   │   │   ├── prompt_pipeline.py   # Construção de prompts (LangChain)
│   │   │   │   ├── structured_outputs.py # Schemas Pydantic para respostas
│   │   │   │   └── fallback_service.py  # Cadeia de fallback entre providers
│   │   │   ├── orchestration/
│   │   │   │   ├── graph_state.py       # GraphState canônico (LangGraph)
│   │   │   │   ├── agent_service.py     # Execução do grafo
│   │   │   │   ├── nodes/               # Nós do grafo (contexto, retrieval, geração, safety, persistência)
│   │   │   │   └── policies/            # Políticas de prompt, RAG, segurança
│   │   │   └── retrieval/
│   │   │       ├── rag_gateway.py       # Cliente para Knowledge Service
│   │   │       ├── retrieval_policy.py  # Política RAG por prompt/escopo
│   │   │       └── citations.py        # Formatação de citações
│   │   ├── domain/
│   │   │   ├── conversations/          # Regras de identidade e sessão
│   │   │   ├── sessions/               # Regras de sessão terapêutica
│   │   │   ├── prompts/                # Regras de prompt
│   │   │   ├── users/                  # Regras de usuário/perfil
│   │   │   └── safety/                 # Regras de segurança clínica
│   │   ├── infrastructure/
│   │   │   ├── db/                     # MongoDB (Motor), índices, repositórios
│   │   │   ├── cache/                  # Redis (performance, sessões ativas)
│   │   │   ├── http/                   # Clientes HTTP (voice, emotion, knowledge)
│   │   │   ├── llm/                    # Adapters de providers LLM
│   │   │   └── observability/          # Métricas, tracing, audit
│   │   └── repositories/
│   │       ├── conversations.py        # Persistência de conversas e mensagens
│   │       ├── prompts.py              # CRUD de prompts no Mongo
│   │       ├── users.py                # CRUD de usuários no Mongo
│   │       └── sessions.py             # Persistência de sessões terapêuticas
│   └── prompts/                        # Templates de prompt versionados
├── requirements.txt
└── Dockerfile
```

### Arquivos críticos do ai-service

**`src/main.py`**
- Cria o app FastAPI, CORS e eventos de lifespan.
- Inicializa MongoDB, índices e prompts padrão.
- Inclui todos os routers (public, admin, internal).

**`src/app/infrastructure/db/`**
- Conexão Motor (async MongoDB), `get_collection()`, índices.
- Define índices de segurança em `messages` (compound index `username + session_id`).

**`src/app/application/chat/chat_facade.py`**
- `process_user_message()` — fluxo principal: salva mensagem, orquestra via AgentService, salva resposta, gera áudio.
- `process_user_message_stream()` — streaming SSE de texto/áudio.
- `start_or_get_conversation()` — cria/recupera conversa por `chat_id`.

**`src/app/application/orchestration/agent_service.py`**
- Executa o grafo LangGraph: contexto → retrieval → geração → safety → persistência → saída.
- `GraphState` canônico com `chat_id`, `session_id`, `username`, `trace_id`, histórico, política RAG, sinal emocional e flags de segurança.

**`src/app/application/llm/runtime_service.py`**
- Cadeia de providers LLM via LangChain (local GGUF → OpenAI → fallback).
- Suporte a streaming nativo por provider.

**`src/app/application/retrieval/rag_gateway.py`**
- Cliente HTTP para o `knowledge-service` (`/api/v1/retrieve`).
- Aplica política RAG, filtra por confiança, produz citações.

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
| `users` | ai-service (users repo) | Perfil, preferências, auth Google |
| `conversations` | ai-service (conversations repo) | Metadados de sessão de chat |
| `messages` | ai-service (conversations repo) | Mensagens individuais (user/ai) |
| `session_contexts` | ai-service | Contexto estruturado gerado pela IA ao finalizar sessão |
| `user_therapeutic_sessions` | ai-service (sessions repo) | Sessões terapêuticas por usuário |
| `therapeutic_sessions` | ai-service (sessions repo) | Templates globais de sessões |
| `user_emotions` | ai-service | Registros de emoções detectadas |
| `prompts` | ai-service (prompts repo) | Prompts configuráveis da IA |

---

## Volumes Docker compartilhados

| Volume | Caminho no container | Uso |
|--------|---------------------|-----|
| `tts_output` | `/data/tts_output` | Arquivos MP3 gerados pelo voice service |
| `uploads` | `/data/uploads` | Uploads de arquivos (futuro) |
| `shared` | `/data/shared` | Dados compartilhados entre serviços |

---

*Última atualização: Abril 2026*
