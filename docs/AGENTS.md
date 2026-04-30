# Guia para Agentes de Desenvolvimento — Empat.IA

> Este é o ponto de entrada para qualquer agente que trabalhe neste repositório.  
> Leia este documento primeiro. Ele indica qual documentação consultar para cada tipo de tarefa.

---

## O que é o Empat.IA?

Plataforma de apoio terapêutico com IA conversacional baseada na abordagem humanística de Carl Rogers. Combina chat com GPT (OpenAI), análise emocional facial em tempo real (webcam), síntese de voz (Google Cloud TTS) e um sistema de sessões terapêuticas progressivas e personalizadas.

**URLs de produção:** `app.empat-ia.io` (usuário) · `admin.empat-ia.io` (terapeuta) · `api.empat-ia.io` (API)

---

## Documentação disponível

| Arquivo | O que cobre |
|---------|-------------|
| [`TECHNICAL.md`](TECHNICAL.md) | Referência técnica completa: serviços, variáveis de ambiente, API, banco de dados, infra, deploy |
| [`AGENTS.md`](AGENTS.md) | **Este arquivo** — índice de navegação para agentes |
| [`CODEBASE_MAP.md`](CODEBASE_MAP.md) | Mapa de arquivos: onde encontrar cada pedaço do código |
| [`FRONTEND.md`](FRONTEND.md) | Arquitetura React (web-ui e admin-panel): rotas, componentes, estado, localStorage |
| [`CONVENTIONS.md`](CONVENTIONS.md) | Padrões de código, como adicionar endpoints, páginas, componentes |
| [`CONTRACTS.md`](CONTRACTS.md) | Contratos internos entre microserviços (payloads, formatos, URLs) |
| [`SECURITY_FIX_SESSION_ISOLATION.md`](SECURITY_FIX_SESSION_ISOLATION.md) | Correção crítica de isolamento de sessões entre usuários |
| [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md) | Próximos passos gerais do produto e checklist de implementação |
| [`roadmap/VOICE_CONVERSATION_ROADMAP.md`](roadmap/VOICE_CONVERSATION_ROADMAP.md) | Roadmap da feature de conversação por voz |

---

## Navegação rápida por tipo de tarefa

### Adicionar ou modificar um endpoint de API
1. Leia [`CONVENTIONS.md#endpoints-fastapi`](CONVENTIONS.md#endpoints-fastapi)
2. Veja exemplos em [`CODEBASE_MAP.md#gateway-service`](CODEBASE_MAP.md#gateway-service)
3. Consulte o schema de request/response em [`TECHNICAL.md#3-api-reference--gateway`](TECHNICAL.md#3-api-reference--gateway)

### Trabalhar no frontend (web-ui)
1. Leia [`FRONTEND.md#web-ui`](FRONTEND.md#web-ui)
2. Consulte [`CODEBASE_MAP.md#web-ui`](CODEBASE_MAP.md#web-ui) para encontrar arquivos
3. Veja padrões de componentes em [`CONVENTIONS.md#react`](CONVENTIONS.md#react)

### Trabalhar no admin panel
1. Leia [`FRONTEND.md#admin-panel`](FRONTEND.md#admin-panel)
2. Consulte [`CODEBASE_MAP.md#admin-panel`](CODEBASE_MAP.md#admin-panel)

### Modificar lógica de IA ou prompts
1. Leia [`TECHNICAL.md#9-gerenciamento-de-prompts`](TECHNICAL.md#9-gerenciamento-de-prompts)
2. Consulte [`CONTRACTS.md#gateway-ai-service`](CONTRACTS.md#gateway-ai-service)
3. Arquivo principal: `services/ai-service/src/api/openai_routes.py`

### Trabalhar com sessões terapêuticas
1. Leia [`TECHNICAL.md#8-sessões-terapêuticas-e-contexto`](TECHNICAL.md#8-sessões-terapêuticas-e-contexto)
2. Leia [`SECURITY_FIX_SESSION_ISOLATION.md`](SECURITY_FIX_SESSION_ISOLATION.md) — **obrigatório** antes de tocar em session_id
3. Serviço responsável: `services/gateway-service/src/services/user_therapeutic_session_service.py`

### Trabalhar com análise emocional
1. Leia [`TECHNICAL.md#6-sistema-de-análise-emocional`](TECHNICAL.md#6-sistema-de-análise-emocional)
2. Consulte [`CONTRACTS.md#gateway-emotion-service`](CONTRACTS.md#gateway-emotion-service)
3. Serviço: `services/emotion-service/src/`

### Trabalhar com síntese de voz
1. Leia [`TECHNICAL.md#7-síntese-de-voz`](TECHNICAL.md#7-síntese-de-voz)
2. Consulte [`CONTRACTS.md#gateway-voice-service`](CONTRACTS.md#gateway-voice-service)
3. Atenção ao rewrite de URL: `_rewrite_audio_url()` em `gateway-service/src/main.py`

### Modificar banco de dados (schema/queries)
1. Leia [`TECHNICAL.md#4-schema-do-banco-de-dados`](TECHNICAL.md#4-schema-do-banco-de-dados)
2. Leia [`SECURITY_FIX_SESSION_ISOLATION.md`](SECURITY_FIX_SESSION_ISOLATION.md)
3. Conexão e coleções: `services/gateway-service/src/models/database.py`

### Deploy e infraestrutura
1. Leia [`TECHNICAL.md#10-infraestrutura-e-deploy`](TECHNICAL.md#10-infraestrutura-e-deploy)
2. Manifests K8s: `infrastructure/k8s/`
3. Terraform: `infrastructure/terraform/`
4. CI/CD: `.github/workflows/`

### Setup local
1. Leia [`TECHNICAL.md#11-desenvolvimento-local`](TECHNICAL.md#11-desenvolvimento-local)
2. Copie `.env.example` → `.env` e preencha `OPENAI_API_KEY`, `GOOGLE_CLIENT_ID`, `SECRET_KEY`
3. `docker compose up -d`

---

## Coisas críticas para saber antes de escrever qualquer código

### 1. Formato do `session_id`
O `session_id` que circula entre serviços é **composto**: `{username}_{session_id_original}`.

```
toni.rc.neto@gmail.com_session-2
```

O gateway separa os dois componentes usando `rfind("_session-")` para extrair `username` e `original_session_id`. **Nunca use `split('_')` simples** — o username pode conter underscore.

### 2. Isolamento de sessões (segurança crítica)
Qualquer query nas coleções `messages` ou `conversations` **deve** incluir o campo `username` no filtro, além do `session_id`. Sem isso, um usuário pode ver mensagens de outro. Ver [`SECURITY_FIX_SESSION_ISOLATION.md`](SECURITY_FIX_SESSION_ISOLATION.md) para o histórico completo.

### 3. Audio URL rewrite
O voice service retorna URLs no formato `/api/v1/audio/{filename}` (porta 8004, interna). O gateway reescreve para `/api/voice/audio/{filename}` antes de retornar ao browser. A função `_rewrite_audio_url()` em `main.py` faz isso. **Nunca retorne a URL interna diretamente ao frontend.**

### 4. Variáveis VITE_* são embutidas em build time
As variáveis `VITE_*` do frontend (como `VITE_API_URL`, `VITE_GOOGLE_CLIENT_ID`) são injetadas no bundle durante o `docker compose build`. Mudar o `.env` sem recompilar não tem efeito.

### 5. Autenticação JWT
O JWT é gerado pelo gateway após verificação do ID Token do Google. Todas as rotas protegidas esperam `Authorization: Bearer <token>`. O token é armazenado em `localStorage` com a chave `empatia_access_token`.

### 6. Prompts são auto-inicializados na startup
Na startup do gateway, `auto_initialize_prompts()` verifica se o prompt `system_rogers` existe. Se não existir, cria todos os prompts padrão. Isso garante que a plataforma funcione mesmo sem dados iniciais.

### 7. MongoDB é async (Motor)
O gateway usa Motor (driver MongoDB assíncrono). Todas as operações de banco usam `await`. O objeto de coleção é obtido via `get_collection("nome_colecao")` de `models/database.py`.

---

## Stack resumida

| Camada | Tecnologia |
|--------|-----------|
| Frontend usuário | React 18 + Vite + Tailwind + MUI + Framer Motion |
| Frontend admin | React 18 + Vite + Tailwind + MUI + Recharts |
| API Gateway | Python 3.11 + FastAPI + Motor (MongoDB async) |
| AI Service | Python 3.11 + FastAPI + OpenAI SDK |
| Voice Service | Python 3.11 + FastAPI + Google Cloud TTS |
| Emotion Service | TensorFlow 2.13 GPU + DeepFace + MediaPipe + OpenCV |
| Avatar Service | Python 3.11 + FastAPI + proxy DID.ai |
| Banco de dados | MongoDB 7 + Redis 7 |
| Infra | Docker Compose (dev) + GKE Autopilot (prod) + Terraform + GitHub Actions |

---

## Portas locais

| Serviço | Porta |
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

*Última atualização: Abril 2026*
