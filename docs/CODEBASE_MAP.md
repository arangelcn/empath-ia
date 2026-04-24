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
│   ├── avatar-service/   # Proxy DID.ai (FastAPI)
│   ├── emotion-service/  # Análise emocional (TensorFlow + DeepFace)
│   └── voice-service/    # Text-to-Speech (Google Cloud TTS)
├── infrastructure/
│   ├── k8s/              # Manifests Kubernetes
│   ├── terraform/        # Provisionamento GCP
│   └── README.md
├── scripts/              # Utilitários: bootstrap GCP, migrações, seeds
├── data/                 # Volumes Docker (compartilhados entre serviços)
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
│   ├── main.py                          # App FastAPI, todos os endpoints inline, proxies para microserviços
│   ├── api/
│   │   ├── auth.py                      # Router /api/auth/* (Google OAuth + JWT)
│   │   └── admin.py                     # Router /api/admin/* (painel administrativo)
│   ├── services/
│   │   ├── chat_service.py              # Lógica de chat: salvar/recuperar mensagens, processar input
│   │   ├── user_service.py              # CRUD de usuários no MongoDB
│   │   ├── therapeutic_session_service.py       # Templates globais de sessões terapêuticas
│   │   ├── user_therapeutic_session_service.py  # Sessões por usuário (unlock, start, complete)
│   │   ├── user_emotion_service.py      # Salvar e consultar emoções por usuário/sessão
│   │   └── prompt_service.py            # CRUD de prompts; fallback hardcoded se banco vazio
│   └── models/
│       └── database.py                  # Conexão Motor (async MongoDB), get_collection(), índices
├── requirements.txt
└── Dockerfile
```

### Arquivos críticos do gateway

**`src/main.py`**
- Instancia todos os services na startup
- Define `SERVICE_URLS` (URLs dos microserviços via env)
- Chama `auto_initialize_prompts()` na startup
- Contém `_rewrite_audio_url()` — reescreve URLs de áudio do voice service
- Extrai `username` e `session_id` de `full_session_id` usando `rfind("_session-")`

**`src/models/database.py`**
- `init_mongodb()` — abre conexão Motor na startup
- `get_collection(name)` — retorna coleção pelo nome
- Define índices de segurança em `messages` (compound index em `username + session_id`)

**`src/services/chat_service.py`**
- `process_user_message()` — fluxo principal: salva mensagem do usuário, chama AI Service, salva resposta, gera áudio
- `finalize_session_context()` — ao finalizar sessão: chama AI Service para gerar contexto estruturado
- `_save_message()` — salva mensagem na coleção `messages`
- `_generate_audio_if_available()` — chama voice service se voz habilitada

**`src/services/user_therapeutic_session_service.py`**
- `create_session_1_for_user()` — cria a sessão de onboarding para novos usuários
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
│   │   └── openai_routes.py       # POST /openai/chat — geração de resposta terapêutica
│   └── services/
│       ├── openai_service.py      # Wrapper OpenAI SDK (chat completions)
│       ├── redis_service.py       # Cache de contexto de sessão no Redis
│       ├── session_context_service.py  # Lógica de contexto acumulado entre sessões
│       ├── prompt_client.py       # Busca prompts ativos via HTTP no gateway
│       └── token_service.py       # Controle de tokens (contexto cabe no modelo)
├── requirements.txt
└── Dockerfile
```

**Fluxo no AI Service:**
1. Recebe request de `/openai/chat` do gateway
2. Busca prompt ativo via `prompt_client.py` (chama `GET /api/prompts/active/{key}` no gateway)
3. Monta contexto: histórico + perfil do usuário + dados emocionais + contexto de sessões anteriores
4. Chama OpenAI API via `openai_service.py`
5. Retorna resposta estruturada

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

## `services/avatar-service/`

```
services/avatar-service/
├── src/
│   ├── main.py
│   └── api/
│       └── avatar_routes.py       # Proxy para DID.ai
├── requirements.txt
└── Dockerfile
```

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
│   │   ├── ComingSoonScreen.jsx   # Placeholder /login
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
│   ├── avatar-service/
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
- `OPENAI_API_KEY`, `DID_API_USERNAME`, `DID_API_PASSWORD` — sincronizados para Secret Manager
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
