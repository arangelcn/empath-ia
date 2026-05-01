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
| [`README.md`](README.md) | Índice curto da documentação ativa |
| [`TECHNICAL.md`](TECHNICAL.md) | Referência técnica: serviços, variáveis de ambiente, API, banco de dados, prompts e deploy |
| [`AGENTS.md`](AGENTS.md) | **Este arquivo** — índice de navegação para agentes |
| [`CODEBASE_MAP.md`](CODEBASE_MAP.md) | Mapa de arquivos: onde encontrar cada pedaço do código |
| [`FRONTEND.md`](FRONTEND.md) | Arquitetura React (web-ui e admin-panel): rotas, componentes, estado, localStorage |
| [`CONVENTIONS.md`](CONVENTIONS.md) | Padrões de código, como adicionar endpoints, páginas, componentes |
| [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md) | Roadmap vivo: prioridades, Prompt Control, RAG e voz |

---

## Navegação rápida por tipo de tarefa

### Adicionar ou modificar um endpoint de API
1. Leia a seção de endpoints em [`CONVENTIONS.md`](CONVENTIONS.md)
2. Veja o mapa do gateway em [`CODEBASE_MAP.md`](CODEBASE_MAP.md)
3. Consulte a API Gateway em [`TECHNICAL.md`](TECHNICAL.md)

### Trabalhar no frontend (web-ui)
1. Leia a seção Web UI em [`FRONTEND.md`](FRONTEND.md)
2. Consulte [`CODEBASE_MAP.md`](CODEBASE_MAP.md) para encontrar arquivos
3. Veja padrões React em [`CONVENTIONS.md`](CONVENTIONS.md)

### Trabalhar no admin panel
1. Leia a seção Admin Panel em [`FRONTEND.md`](FRONTEND.md)
2. Consulte [`CODEBASE_MAP.md`](CODEBASE_MAP.md)

### Modificar lógica de IA ou prompts
1. Leia a seção de prompts em [`TECHNICAL.md`](TECHNICAL.md)
2. Consulte a Prioridade 5 em [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md)
3. Arquivos principais: `services/gateway-service/src/services/prompt_service.py`, `services/gateway-service/src/services/chat_service.py` e `services/ai-service/src/services/openai_service.py`

### Trabalhar com sessões terapêuticas
1. Leia a seção de sessões terapêuticas em [`TECHNICAL.md`](TECHNICAL.md)
2. Leia a seção "Identidade de Chat" neste arquivo antes de tocar em `chat_id` ou `session_id`
3. Serviço responsável: `services/gateway-service/src/services/user_therapeutic_session_service.py`

### Trabalhar com análise emocional
1. Leia a seção de análise emocional em [`TECHNICAL.md`](TECHNICAL.md)
2. Serviço: `services/emotion-service/src/`

### Trabalhar com síntese de voz
1. Leia a seção de síntese de voz em [`TECHNICAL.md`](TECHNICAL.md)
2. Consulte a Prioridade 7 em [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md)
3. Atenção ao rewrite de URL: `_rewrite_audio_url()` em `gateway-service/src/main.py`

### Modificar banco de dados (schema/queries)
1. Leia a seção de schema do banco em [`TECHNICAL.md`](TECHNICAL.md)
2. Conexão e coleções: `services/gateway-service/src/models/database.py`

### Deploy e infraestrutura
1. Leia [`TECHNICAL.md`](TECHNICAL.md) e [`../infrastructure/README.md`](../infrastructure/README.md)
2. Manifests K8s: `infrastructure/k8s/`
3. Terraform: `infrastructure/terraform/`
4. CI/CD: `.github/workflows/`

### Setup local
1. Leia a seção de desenvolvimento local em [`TECHNICAL.md`](TECHNICAL.md)
2. Copie `.env.example` → `.env` e preencha `OPENAI_API_KEY`, `GOOGLE_CLIENT_ID`, `SECRET_KEY`
3. `docker compose up -d`

---

## Coisas críticas para saber antes de escrever qualquer código

### 1. Identidade de Chat
A PK pública do chat é `chat_id`, um identificador opaco salvo em `conversations.chat_id` e usado nas rotas `/chat/{chat_id}`.

```
chat_4f0d...
```

`session_id` continua representando a sessão terapêutica (`session-2`) e `username` fica em campo separado. O formato legado `{username}_session-N` ainda é aceito pelo gateway como `legacy_session_id` para migração/compatibilidade; se precisar separar esse legado, use `rfind("_session-")`, nunca `split('_')` simples.

### 2. Isolamento de sessões (segurança crítica)
Qualquer query nas coleções `messages` ou `conversations` deve preferir `chat_id`. Quando filtrar por sessão terapêutica, use o par `username + therapeutic_session_id`. Sem isso, um usuário pode ver mensagens de outro. O resumo atualizado fica na seção de sessões terapêuticas em [`TECHNICAL.md`](TECHNICAL.md).

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
