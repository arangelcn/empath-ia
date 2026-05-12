# Development Agent Guide — Empat.IA

> This is the entry point for any agent working in this repository.  
> Read this document first. It tells you which docs to use for each task type.

---

## What is Empat.IA?

Empat.IA is a therapeutic support platform with conversational AI inspired by Carl Rogers' humanistic approach. It combines GPT-based chat (OpenAI-compatible), real-time facial emotion analysis (webcam), voice synthesis (Google Cloud TTS), and a progressive, personalized therapeutic session system.

**Production URLs:** `app.empat-ia.io` (user) · `admin.empat-ia.io` (therapist) · `api.empat-ia.io` (API)

---

## Available Documentation

| File | What it covers |
|---------|-------------|
| [`README.md`](README.md) | Short index for active documentation |
| [`TECHNICAL.md`](TECHNICAL.md) | Technical reference: services, env vars, API, database, prompts, and deploy |
| [`AGENTS.md`](AGENTS.md) | **This file** — navigation index for agents |
| [`CODEBASE_MAP.md`](CODEBASE_MAP.md) | File map: where each part of the code lives |
| [`FRONTEND.md`](FRONTEND.md) | React architecture (web-ui and admin-panel): routes, components, state, localStorage |
| [`CONVENTIONS.md`](CONVENTIONS.md) | Code standards and how to add endpoints, pages, and components |
| [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md) | Living roadmap: priorities, Prompt Control, RAG, and voice |

---

## Quick Navigation by Task Type

### Add or change an API endpoint
1. Read the endpoint section in [`CONVENTIONS.md`](CONVENTIONS.md)
2. Check the gateway map in [`CODEBASE_MAP.md`](CODEBASE_MAP.md)
3. Review API Gateway details in [`TECHNICAL.md`](TECHNICAL.md)

### Work on frontend (web-ui)
1. Read the Web UI section in [`FRONTEND.md`](FRONTEND.md)
2. Use [`CODEBASE_MAP.md`](CODEBASE_MAP.md) to locate files
3. Follow React standards in [`CONVENTIONS.md`](CONVENTIONS.md)

### Work on admin panel
1. Read the Admin Panel section in [`FRONTEND.md`](FRONTEND.md)
2. Use [`CODEBASE_MAP.md`](CODEBASE_MAP.md)

### Modify AI logic or prompts
1. Read the prompts section in [`TECHNICAL.md`](TECHNICAL.md)
2. Review Priority 5 in [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md)
3. Main files: `services/gateway-service/src/services/prompt_service.py`, `services/gateway-service/src/services/chat_service.py`, `services/gateway-service/src/services/chat_title_service.py`, and `services/ai-service/src/services/llm_service.py`

### Work with therapeutic sessions
1. Read the therapeutic sessions section in [`TECHNICAL.md`](TECHNICAL.md)
2. Read the "Chat Identity" section in this file before touching `chat_id` or `session_id`
3. Owner service: `services/gateway-service/src/services/user_therapeutic_session_service.py`

### Work with emotion analysis
1. Read the emotion analysis section in [`TECHNICAL.md`](TECHNICAL.md)
2. Service: `services/emotion-service/src/`

### Work with voice synthesis
1. Read the voice synthesis section in [`TECHNICAL.md`](TECHNICAL.md)
2. Review Priority 7 in [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md)
3. Be careful with URL rewrite: `_rewrite_audio_url()` in `gateway-service/src/api/voice.py` and `VoiceSynthesisService.gateway_audio_url()` in `gateway-service/src/services/voice_synthesis_service.py`

### Change database schema/queries
1. Read the database schema section in [`TECHNICAL.md`](TECHNICAL.md)
2. Collections and connection: `services/gateway-service/src/models/database.py`

### Deploy and infrastructure
1. Read [`TECHNICAL.md`](TECHNICAL.md) and [`../infrastructure/README.md`](../infrastructure/README.md)
2. K8s manifests: `infrastructure/k8s/`
3. Terraform: `infrastructure/terraform/`
4. CI/CD: `.github/workflows/`

### Local setup
1. Read the local development section in [`TECHNICAL.md`](TECHNICAL.md)
2. Copy `.env.example` to `.env` and fill `OPENAI_API_KEY`, `GOOGLE_CLIENT_ID`, `SECRET_KEY`
3. Run `docker compose up -d`

---

## Critical Things to Know Before Writing Code

### 1. Chat Identity
The public chat primary key is `chat_id`, an opaque identifier stored in `conversations.chat_id` and used by `/chat/{chat_id}` routes.

```
chat_4f0d...
```

`session_id` still represents the therapeutic session (`session-2`), and `username` is stored separately. The legacy format `{username}_session-N` is still accepted by the gateway as `legacy_session_id` for migration/compatibility. If you must split it, use `rfind("_session-")`, never a simple `split('_')`.

### 2. Session isolation (critical security)
Any query against `messages` or `conversations` must prefer `chat_id`. When filtering by therapeutic session, use `username + therapeutic_session_id`. Without this, users can see other users' messages. The latest session isolation summary is in the therapeutic sessions section of [`TECHNICAL.md`](TECHNICAL.md).

### 3. Audio URL rewrite
The voice service returns URLs like `/api/v1/audio/{filename}` (internal port 8004). The gateway must rewrite to `/api/voice/audio/{filename}` before returning to the browser. After refactor, rewrite logic lives in `src/api/voice.py` for HTTP proxy paths and in `src/services/voice_synthesis_service.py` for chat-generated responses. **Never return the internal URL directly to the frontend.**

### 4. `VITE_*` variables are build-time only
Frontend `VITE_*` vars (`VITE_API_URL`, `VITE_GOOGLE_CLIENT_ID`, etc.) are injected into the bundle during `docker compose build`. Updating `.env` without rebuilding has no effect.

### 5. JWT authentication
JWT is issued by the gateway after Google ID token verification. All protected routes require `Authorization: Bearer <token>`. The token is stored in `localStorage` with key `empatia_access_token`.

### 6. Prompts auto-bootstrap on startup
On gateway startup, `auto_initialize_prompts()` checks whether `system_rogers` exists. If missing, it creates all default prompts. This ensures platform startup even on an empty database.

### 7. MongoDB is async (Motor)
Gateway uses Motor (async MongoDB driver). All DB operations must use `await`. Collections are fetched via `get_collection("collection_name")` in `models/database.py`.

### 8. `session-1` is guaranteed by gateway
`UserTherapeuticSessionService.ensure_registration_session()` creates `session-1` idempotently when user journey data is requested. Do not assume Home must create it in frontend.

---

## Stack Summary

| Layer | Technology |
|--------|-----------|
| User frontend | React 18 + Vite + Tailwind + MUI + Framer Motion |
| Admin frontend | React 18 + Vite + Tailwind + MUI + Recharts |
| API Gateway | Python 3.11 + FastAPI + Motor (async MongoDB) |
| AI Service | Python 3.11 + FastAPI + OpenAI SDK |
| Voice Service | Python 3.11 + FastAPI + Google Cloud TTS |
| Emotion Service | TensorFlow 2.13 GPU + DeepFace + MediaPipe + OpenCV |
| Avatar Service | Python 3.11 + FastAPI + DID.ai proxy |
| Database | MongoDB 7 + Redis 7 |
| Infra | Docker Compose (dev) + GKE Autopilot (prod) + Terraform + GitHub Actions |

---

## Local Ports

| Service | Port |
|---------|-------|
| Web UI | 7860 |
| Admin Panel | 3001 |
| Gateway API | 8000 |
| AI Service | 8001 |
| Avatar Service | 8002 |
| Emotion Service | 8003 |
| Voice Service | 8004 |
| MongoDB | 27017 |
| Redis | 6379 |
| Mongo Express (dev) | 8081 |

---

*Last updated: April 2026*
