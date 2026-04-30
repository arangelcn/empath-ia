# Documentação Técnica — Empat.IA

> Referência técnica completa: arquitetura, APIs, banco de dados, variáveis de ambiente, infra e decisões de design.
> Para a visão geral do produto, acesse o [README principal](../README.md).

---

## Índice

1. [Serviços e Responsabilidades](#1-serviços-e-responsabilidades)
2. [Variáveis de Ambiente](#2-variáveis-de-ambiente)
3. [API Reference — Gateway](#3-api-reference--gateway)
4. [Schema do Banco de Dados](#4-schema-do-banco-de-dados)
5. [Autenticação Google + JWT](#5-autenticação-google--jwt)
6. [Sistema de Análise Emocional](#6-sistema-de-análise-emocional)
7. [Síntese de Voz](#7-síntese-de-voz)
8. [Sessões Terapêuticas e Contexto](#8-sessões-terapêuticas-e-contexto)
9. [Gerenciamento de Prompts](#9-gerenciamento-de-prompts)
10. [Infraestrutura e Deploy](#10-infraestrutura-e-deploy)
11. [Desenvolvimento Local](#11-desenvolvimento-local)

---

## 1. Serviços e Responsabilidades

| Serviço | Porta | Runtime | Responsabilidade |
|---------|-------|---------|------------------|
| `gateway-service` | 8000 | Python 3.11 + FastAPI | Ponto único de entrada: roteamento, auth, chat, sessões, proxy para microserviços |
| `ai-service` | 8001 | Python 3.11 + FastAPI | Integração OpenAI: respostas terapêuticas, geração de contexto, geração de próxima sessão |
| `avatar-service` | 8002 | Python 3.11 + FastAPI | Proxy para DID.ai (avatares animados) |
| `emotion-service` | 8003 | TensorFlow 2.13 GPU | Análise emocional facial (DeepFace, MediaPipe) e de vídeo |
| `voice-service` | 8004 | Python 3.11 + FastAPI | Text-to-Speech via Google Cloud TTS; arquivos de áudio servidos via gateway |
| `web-ui` | 3000→7860 | Node 18 → nginx | Frontend principal do usuário (React + Vite) |
| `admin-panel` | 3000→3001 | Node 18 → nginx | Painel administrativo do terapeuta (React + Vite) |
| `mongodb` | 27017 | MongoDB 7 | Banco de dados principal |
| `redis` | 6379 | Redis 7 | Cache e filas (AI service) |

### Dependências entre serviços

```
browser → web-ui (nginx) → /api/* proxy → gateway:8000
browser → admin-panel (nginx) → /api/* proxy → gateway:8000
gateway → ai-service:8001
gateway → voice-service:8004
gateway → emotion-service:8003
gateway → avatar-service:8002
gateway → mongodb:27017
ai-service → mongodb:27017
ai-service → redis:6379
```

---

## 2. Variáveis de Ambiente

Copie `.env.example` para `.env`. Variáveis marcadas com ⚠️ são obrigatórias para o funcionamento básico.

### Autenticação e Segurança

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `GOOGLE_CLIENT_ID` | ⚠️ | OAuth 2.0 Client ID (console.cloud.google.com → APIs & Credentials) |
| `SECRET_KEY` | ⚠️ | Chave para assinar JWTs. Gere com: `openssl rand -hex 32` |
| `ALGORITHM` | — | Algoritmo JWT. Padrão: `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | Validade do token. Padrão: `10080` (7 dias) |

### OpenAI

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `OPENAI_API_KEY` | ⚠️ | Chave da API OpenAI |
| `MODEL_NAME` | — | Modelo a usar. Padrão: `gpt-3.5-turbo`. Recomendado: `gpt-4o` |

### MongoDB

| Variável | Descrição |
|----------|-----------|
| `MONGO_INITDB_ROOT_USERNAME` | Usuário admin do MongoDB. Padrão: `admin` |
| `MONGO_INITDB_ROOT_PASSWORD` | Senha do admin. Padrão: `admin123` (mude em produção) |
| `MONGODB_URL` | URL completa. Padrão: `mongodb://admin:admin123@mongodb:27017/empatia?authSource=admin` |
| `DATABASE_NAME` | Nome do banco. Padrão: `empatia` |

### Google Cloud (Síntese de Voz)

| Variável | Descrição |
|----------|-----------|
| `CREDENTIALS_JSON` | Conteúdo do JSON da Service Account GCP (para TTS) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Caminho para o arquivo JSON dentro do container |

### Frontend

| Variável | Descrição |
|----------|-----------|
| `VITE_API_URL` | URL da API para o browser. Dev: `http://localhost:8000`. Prod: `https://api.empat-ia.io` |
| `VITE_GOOGLE_CLIENT_ID` | Client ID no bundle do Vite. **Definido automaticamente a partir de `GOOGLE_CLIENT_ID`** |
| `VITE_GOOGLE_REDIRECT_URI` | URI de redirecionamento OAuth. Dev: `http://localhost:7860` |
| `WEB_UI_PORT` | Porta exposta do Web UI. Padrão: `7860` |
| `ADMIN_PANEL_PORT` | Porta exposta do Admin. Padrão: `3001` |

### Gateway

| Variável | Descrição |
|----------|-----------|
| `GATEWAY_PORT` | Porta do gateway. Padrão: `8000` |
| `ALLOWED_ORIGINS` | CORS. Ex.: `https://app.empat-ia.io,https://admin.empat-ia.io` |
| `LOG_LEVEL` | Nível de log. Padrão: `INFO` |
| `DEBUG` | Modo debug. Padrão: `false` |
| `AI_SERVICE_URL` | URL interna do AI service. Padrão: `http://ai-service:8001` |
| `VOICE_SERVICE_URL` | URL interna do Voice service. Padrão: `http://voice-service:8004` |
| `EMOTION_SERVICE_URL` | URL interna do Emotion service. Padrão: `http://emotion-service:8003` |

### DID (Avatares — opcional)

| Variável | Descrição |
|----------|-----------|
| `DID_API_USERNAME` | Usuário DID.ai |
| `DID_API_PASSWORD` | Senha DID.ai |

---

## 3. API Reference — Gateway

Base URL: `http://localhost:8000` (dev) · `https://api.empat-ia.io` (prod)

Documentação interativa: `GET /docs` (Swagger) · `GET /redoc`

### Autenticação — `/api/auth`

```
GET  /api/auth/google/status
     → { "available": true|false }
     Verifica se GOOGLE_CLIENT_ID está configurado no servidor.
     O frontend chama isso antes de carregar o SDK do Google.

POST /api/auth/google
     Body: { "credential": "<id_token_jwt>" }
     → { "access_token": "...", "token_type": "bearer", "user": { ... } }
     Valida o ID Token com as chaves públicas do Google,
     faz upsert do usuário no MongoDB e retorna JWT de sessão.
```

O JWT retornado deve ser enviado em todas as requisições subsequentes:
```
Authorization: Bearer <access_token>
```

### Chat — `/api/chat`

```
POST /api/chat/send
     Body: { "message": "...", "session_id": "...", "session_objective": {...}, "is_voice_mode": false }
     → { "response": "...", "audio_url": "...", "session_id": "..." }

GET  /api/chat/history/{session_id}
     → { "history": [{ "type": "user|ai", "content": "...", "timestamp": "..." }] }

GET  /api/chat/initial-message/{session_id}
     → { "success": true, "data": { "message": {...}, "is_initial_message": true } }
     Gera a primeira mensagem de uma sessão (sem input do usuário).

POST /api/chat/finalize/{session_id}
     Finaliza a sessão: gera contexto estruturado via AI Service e cria próxima sessão.
     → { "success": true, "data": { "context": {...}, "session_completed": true } }

GET  /api/chat/context/{session_id}
     → { "success": true, "data": { "context": {...} } }
```

### Usuário — `/api/user`

```
POST /api/user/create              Body: { "username", "email", "preferences" }
GET  /api/user/{username}
PUT  /api/user/{username}/preferences
POST /api/user/{username}/login    Registra login e cria session-1 automaticamente
GET  /api/user/{username}/stats
GET  /api/user/status/{session_id}
POST /api/user/preferences         Body: { "session_id", "username", "selected_voice", "voice_enabled" }
```

### Sessões Terapêuticas — `/api/user/{username}/sessions`

```
GET  /api/user/{username}/sessions                         → lista sessões
GET  /api/user/{username}/sessions/{session_id}            → detalhe
POST /api/user/{username}/sessions/{session_id}/start      → inicia
POST /api/user/{username}/sessions/{session_id}/complete   → conclui (body: { "progress": 100 })
POST /api/user/{username}/sessions/{session_id}/unlock     → desbloqueia
GET  /api/user/{username}/progress                         → progresso geral
GET  /api/user/{username}/sessions/info                    → estatísticas detalhadas
```

### Emoções — `/api/emotions`

```
GET  /api/emotions/{username}?session_id=...&limit=100&hours_back=24
GET  /api/emotions/{username}/summary?session_id=...&hours_back=24
GET  /api/emotions/{username}/timeline?hours_back=24&interval_minutes=5
POST /api/emotion/analyze-realtime   Body: { "image": "<base64>", "username": "...", "session_id": "..." }
```

### Voz — `/api/voice`

```
POST /api/voice/speak        Body: { "text": "...", "voice": "pt-BR-Neural2-B" }
POST /api/voice/synthesize   Alias de /speak
GET  /api/voice/audio/{filename}   Serve o arquivo MP3 gerado
GET  /api/voice/health
GET  /api/voice/models
```

### Prompts — `/api/prompts`

```
GET    /api/prompts?prompt_type=...&active_only=true
POST   /api/prompts              Body: { "key", "name", "content", "prompt_type", ... }
GET    /api/prompts/{key}
GET    /api/prompts/active/{key}
PUT    /api/prompts/{key}
DELETE /api/prompts/{key}        Soft delete
GET    /api/prompts/type/{type}
POST   /api/prompts/initialize   Cria prompts padrão do sistema
GET    /api/prompts/stats
POST   /api/prompts/render/{key} Body: { "variavel": "valor" } → renderiza com substituição
```

### Admin — `/api/admin`

```
GET /api/admin/stats
GET /api/admin/conversations
GET /api/admin/conversations/{session_id}
GET /api/admin/emotions/analysis
GET /api/admin/emotions/realtime-stats
GET /api/admin/activity/realtime
CRUD /api/admin/therapeutic-sessions
CRUD /api/admin/users
GET /api/admin/session-contexts
GET /api/admin/user-sessions
```

---

## 4. Schema do Banco de Dados

### Coleções principais

#### `users`
```json
{
  "username": "email@exemplo.com",
  "email": "email@exemplo.com",
  "google_id": "sub do Google",
  "name": "Nome Completo",
  "full_name": "Nome Completo informado pelo usuário",
  "display_name": "Nome usado na interface e nos prompts",
  "picture": "https://...",
  "email_verified": true,
  "auth_method": "google",
  "preferences": {
    "selected_voice": "pt-BR-Neural2-B",
    "voice_enabled": true,
    "full_name": "Nome Completo informado pelo usuário",
    "display_name": "Nome usado na interface e nos prompts",
    "theme": "dark",
    "language": "pt-BR"
  },
  "user_profile": { ... },
  "profile_completed": false,
  "created_at": "ISO8601",
  "last_login": "ISO8601",
  "is_active": true,
  "login_count": 1,
  "session_count": 0
}
```

#### `conversations`
```json
{
  "session_id": "usuario@email.com_session-2",
  "username": "usuario@email.com",
  "message_count": 15,
  "session_context_ref": "ObjectId → session_contexts",
  "session_finalized": false,
  "user_preferences": { "username": "...", "selected_voice": "...", "completed_welcome": true },
  "registration_data": { ... },
  "registration_step": 5,
  "is_registration_complete": true,
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

#### `session_contexts` _(fonte única de contextos)_
```json
{
  "session_id": "usuario@email.com_session-2",
  "username": "usuario@email.com",
  "context": {
    "summary": "...",
    "main_themes": ["ansiedade", "trabalho"],
    "key_insights": ["..."],
    "emotional_state": { "dominant": "neutro", "progression": "melhora" },
    "user_progress": "...",
    "next_session_focus": "..."
  },
  "conversation_text": "texto completo da conversa",
  "emotions_data": [ { "emotion": "alegria", "confidence": 0.87, "timestamp": "..." } ],
  "source": "ai_service | gateway_fallback",
  "version": 1,
  "is_active": true,
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

#### `user_therapeutic_sessions`
```json
{
  "username": "usuario@email.com",
  "session_id": "session-2",
  "title": "Aprofundando nosso conhecimento",
  "subtitle": "...",
  "objective": "...",
  "initial_prompt": "...",
  "focus_areas": ["autoconhecimento", "relacionamentos"],
  "status": "unlocked | in_progress | completed | locked",
  "progress": 100,
  "personalized": true,
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

#### `user_emotions`
```json
{
  "username": "usuario@email.com",
  "session_id": "usuario@email.com_session-2",
  "dominant_emotion": "alegria",
  "emotions": { "alegria": 0.87, "neutro": 0.10, "surpresa": 0.03 },
  "confidence": 0.87,
  "face_detected": true,
  "source": "webcam | text_analysis",
  "timestamp": "ISO8601"
}
```

#### `prompts`
```json
{
  "key": "next_session_generation",
  "name": "Geração de Próxima Sessão",
  "description": "...",
  "content": "Você é um terapeuta... {context} {user_profile}",
  "prompt_type": "session_generation | system | fallback | analysis",
  "variables": ["context", "user_profile"],
  "is_active": true,
  "version": 2,
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

---

## 5. Autenticação Google + JWT

**Fluxo:**

```
1. Frontend carrega Google Identity Services SDK
2. Usuário clica "Fazer Login com o Google" → popup Google
3. Google retorna ID Token (JWT assinado pelo Google)
4. Frontend envia: POST /api/auth/google { "credential": "<id_token>" }
5. Gateway verifica assinatura com chaves públicas Google (google-auth lib)
6. Gateway faz upsert do usuário no MongoDB (por google_id ou email)
7. Gateway emite JWT próprio assinado com SECRET_KEY
8. Frontend armazena JWT em localStorage ("empatia_access_token")
9. Todas as requisições seguintes incluem: Authorization: Bearer <jwt>
```

**Por que não usar GOOGLE_CLIENT_SECRET?**
O fluxo usa Google Identity Services (GIS), não o fluxo de autorização OAuth clássico. O servidor verifica o ID Token diretamente com as chaves públicas do Google — sem client secret.

**Configuração no Google Cloud Console:**
- APIs & Services → Credentials → OAuth 2.0 Client ID
- Authorized JavaScript origins: `http://localhost:7860`, `https://app.empat-ia.io`
- Authorized redirect URIs: não necessário para GIS popup

---

## 6. Sistema de Análise Emocional

### Pipeline de detecção

```
Webcam frame (base64)
    ↓
POST /api/emotion/analyze-realtime
    ↓
Gateway → Emotion Service (porta 8003)
    ↓
DeepFace.analyze(frame, actions=["emotion"])   ← detecção facial
    +
MediaPipe FaceMesh                              ← landmarks
    ↓
{ dominant_emotion, emotions: {alegria: 0.87, ...}, confidence, face_detected }
    ↓
Gateway salva em user_emotions (async, não bloqueia resposta)
    ↓
Frontend exibe EmotionBadge na interface
```

### Dados disponíveis

- **Por sessão**: `GET /api/emotions/{username}?session_id=...`
- **Resumo agregado**: `GET /api/emotions/{username}/summary`
- **Timeline temporal**: `GET /api/emotions/{username}/timeline?interval_minutes=5`
- **Analytics admin**: `GET /api/admin/emotions/analysis` (todos os usuários)

### Integração com IA

O contexto enviado ao AI Service inclui os dados emocionais da sessão:
```python
# em chat_service.py
context["emotions_summary"] = await get_emotion_summary(username, session_id)
```

---

## 7. Síntese de Voz

**Tecnologia:** Google Cloud Text-to-Speech (Neural2 e WaveNet)

### Vozes disponíveis (português brasileiro)

| ID | Tipo | Descrição |
|----|------|-----------|
| `pt-BR-Neural2-B` | Neural2 | Masculina — tom confiante (padrão recomendado) |
| `pt-BR-Neural2-A` | Neural2 | Feminina — tom natural |
| `pt-BR-Wavenet-A` | WaveNet | Feminina profissional |
| `pt-BR-Wavenet-B` | WaveNet | Masculina amigável |
| `pt-BR-Wavenet-C` | WaveNet | Feminina calorosa |

### Fluxo de geração

```
POST /api/voice/speak { "text": "...", "voice": "pt-BR-Neural2-B" }
    ↓
Gateway → Voice Service
    ↓
Google Cloud TTS API
    ↓
Arquivo MP3 salvo em /data/tts_output/output_{hash}.mp3
    ↓
Voice Service retorna: { "audio_url": "/api/v1/audio/output_{hash}.mp3" }
    ↓
Gateway reescreve para: { "audio_url": "/api/voice/audio/output_{hash}.mp3" }
    ↓
Frontend faz GET /api/voice/audio/{filename} e reproduz
```

**Por que reescrever a URL?** O browser não tem acesso direto à porta 8004 do Voice Service — o gateway atua como proxy para o arquivo de áudio.

---

## 8. Sessões Terapêuticas e Contexto

### Ciclo de vida de uma sessão

```
1. POST /api/user/{username}/login
   → cria session-1 (template "Cadastro e Apresentação")
   → desbloqueia session-1

2. Usuário completa session-1 (onboarding com perguntas)
   → perfil estruturado salvo em users.user_profile

3. POST /api/chat/finalize/{session_id}
   → AI Service gera contexto estruturado (summary, temas, insights, estado emocional)
   → salvo em session_contexts
   → AI Service gera session-2 personalizada
   → session-2 desbloqueada

4. Sessões 2+ repetem o ciclo com contexto acumulado
```

### Geração automática de sessões

O AI Service recebe:
- Contexto da sessão anterior (`session_contexts`)
- Perfil do usuário (`users.user_profile`)
- Dados emocionais (`user_emotions`)

E gera:
```json
{
  "title": "Aprofundando nosso conhecimento",
  "subtitle": "...",
  "objective": "...",
  "initial_prompt": "Olá {username}! Na nossa última conversa...",
  "focus_areas": ["autoconhecimento", "relacionamentos"],
  "connection_to_previous": "..."
}
```

### formato de session_id

```
{username}_{session_id_original}
Ex: toni.rc.neto@gmail.com_session-2
```

O gateway extrai `username` e `session_id` a partir do separador `_session-`.

---

## 9. Gerenciamento de Prompts

O sistema de prompts permite que o terapeuta configure o comportamento da IA via Admin Panel sem tocar no código.

### Tipos de prompts

| Tipo | Chave padrão | Uso |
|------|-------------|-----|
| `system` | `system_rogers` | Prompt principal do terapeuta (abordagem Rogers, tom, limites) |
| `session_generation` | `next_session_generation` | Instrução para gerar próximas sessões |
| `session_generation` | `session_context_analysis` | Instrução para gerar contexto estruturado |
| `fallback` | `fallback_default` | Resposta quando OpenAI não está disponível |
| `fallback` | `fallback_goodbye` | Resposta automática para despedidas |
| `fallback` | `fallback_anger` | Resposta automática para raiva |
| `fallback` | `fallback_gratitude` | Resposta automática para gratidão |

### Variáveis dinâmicas

Os prompts suportam substituição de variáveis com `{variavel}`:
```
"Olá {username}! Na nossa última sessão, conversamos sobre {themes}..."
```

Renderização: `POST /api/prompts/render/{key}` com `{ "username": "Toni", "themes": "ansiedade" }`

### Sistema de fallback

Se o prompt ativo não for encontrado no banco, o sistema usa o prompt hardcoded em `prompt_service.py`. Isso garante que a plataforma nunca fique sem resposta.

---

## 10. Infraestrutura e Deploy

### Kubernetes (GKE Autopilot)

Todos os manifests em `infrastructure/k8s/`:

```
namespace.yaml          → namespace "empatia"
configmap.yaml          → variáveis de configuração (inclui GOOGLE_CLIENT_ID)
serviceaccount.yaml     → Workload Identity para acesso ao GCP
gateway/                → deployment + service + HPA
ai-service/
voice-service/
emotion-service/
avatar-service/
web-ui/
admin-panel/
mongodb/                → StatefulSet + PVC
redis/
ingress.yaml            → GCE Ingress + ManagedCertificate (HTTPS)
```

### ConfigMap vs Secrets

| Tipo | O que contém |
|------|-------------|
| **ConfigMap** `empatia-config` | `GOOGLE_CLIENT_ID`, URLs de serviços, `ALLOWED_ORIGINS`, `DATABASE_NAME`, `LOG_LEVEL` |
| **K8s Secret** `empatia-secrets` | `OPENAI_API_KEY`, `MONGO_ROOT_PASSWORD`, `REDIS_PASSWORD`, `JWT_SECRET_KEY`, `DID_API_*` |

Os secrets são sincronizados do **GCP Secret Manager** no pipeline de deploy.

### Pipeline CI/CD (`.github/workflows/deploy.yml`)

Trigger: push para `main` ou `workflow_dispatch`

```
1. Build & Push → imagens Docker para Artifact Registry (us-central1)
   - Build args: VITE_GOOGLE_CLIENT_ID, VITE_API_URL, VITE_VOICE_URL

2. Deploy → GKE Autopilot
   - Sincroniza K8s Secret do GCP Secret Manager
   - Aplica ConfigMap, deployments, ingress
   - Aguarda rollout de todos os deployments
```

### Terraform (`infrastructure/terraform/`)

Provisiona:
- VPC + subnets
- GKE Autopilot cluster
- Artifact Registry
- GCP Secret Manager (secrets)
- Cloud DNS (zona `empat-ia.io`, registos A)
- IAM + Workload Identity

```bash
cd infrastructure/terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply
```

### Domínios e Ingress

```yaml
# ingress.yaml
app.empat-ia.io    → web-ui:3000
admin.empat-ia.io  → admin-panel:3000
api.empat-ia.io    → gateway:8000
api.empat-ia.io/voice-service/* → voice-service:8004
```

HTTPS provisionado via **Google Managed Certificate** (auto-renovação).

---

## 11. Desenvolvimento Local

### Subir stack completa

```bash
docker compose up -d
```

### Subir com dev overrides (hot reload + Mongo Express)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Perfis opcionais

```bash
# OpenFace (análise facial avançada)
docker compose --profile tools up -d

# PostgreSQL (futuro)
docker compose --profile database up -d
```

### Recompilar imagem específica

```bash
docker compose build gateway-service --no-cache
docker compose up -d gateway-service
```

### Acessar MongoDB diretamente (dev)

```bash
# Mongo Express: http://localhost:8081
# Credenciais: admin / admin123

# Ou via mongosh:
docker exec -it empatia-mongodb mongosh -u admin -p admin123 --authenticationDatabase admin
```

### Verificar saúde dos serviços

```bash
curl http://localhost:8000/health/all
```

### Variáveis de build do frontend

As variáveis `VITE_*` são **embutidas no bundle** em tempo de build — não em runtime. Para mudá-las, é necessário recompilar:

```bash
docker compose build web-ui
```

No Docker Compose, `VITE_GOOGLE_CLIENT_ID` é passado como build arg a partir de `GOOGLE_CLIENT_ID` (definido no `.env`).

---

*Última atualização: Abril 2026*
