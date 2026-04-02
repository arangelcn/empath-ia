<div align="center">

<img src="docs/screenshots/landing.png" alt="Empat.IA Landing Page" width="100%"/>

# Empat.IA

### Terapia virtual inteligente, baseada na abordagem humanística de Carl Rogers

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://mongodb.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![GKE](https://img.shields.io/badge/GKE-Autopilot-4285F4?style=flat-square&logo=google-cloud&logoColor=white)](https://cloud.google.com/kubernetes-engine)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

**[🌐 App](https://app.empat-ia.io) · [⚙️ Admin](https://admin.empat-ia.io) · [📖 API Docs](https://api.empat-ia.io/docs)**

</div>

---

## O que é o Empat.IA?

**Empat.IA** é uma plataforma de apoio terapêutico que combina IA conversacional, análise emocional em tempo real e continuidade entre sessões para criar uma experiência personalizada e progressiva — inspirada na abordagem centrada na pessoa de Carl Rogers.

> *A Empat.IA existe para **potencializar** o trabalho terapêutico, não para substituí-lo.*

---

## Screenshots

<table>
  <tr>
    <td align="center">
      <img src="docs/screenshots/login.png" alt="Tela de Login" width="100%"/>
      <b>Login com Google</b>
    </td>
    <td align="center">
      <img src="docs/screenshots/admin.png" alt="Painel Admin" width="100%"/>
      <b>Painel Administrativo</b>
    </td>
  </tr>
</table>

---

## Funcionalidades

### Experiência do Usuário
- **Sessões terapêuticas progressivas** — desbloqueio sequencial com geração automática via IA
- **Contexto entre sessões** — a IA lembra o que foi dito, garantindo continuidade terapêutica real
- **Análise emocional em tempo real** — detecção de emoções via webcam e análise textual
- **Síntese de voz neural** — vozes naturais em português brasileiro (Google Cloud TTS)
- **Onboarding estruturado** — perfil completo coletado na sessão inicial (Session-1)
- **Login seguro com Google** — autenticação OAuth 2.0 com JWT de sessão

### Painel Administrativo
- **Gestão de prompts** — editor para customizar o comportamento da IA sem redeploy
- **Dashboard em tempo real** — conversas ativas, emoções capturadas, estatísticas de uso
- **Gerenciamento de usuários** — perfis, históricos e progresso terapêutico
- **Sessões terapêuticas** — catálogo de templates e sessões personalizadas geradas

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
│   app.empat-ia.io (Web UI)   admin.empat-ia.io (Admin)  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────┐
│              API Gateway (FastAPI · Porta 8000)          │
│  api.empat-ia.io — orquestração, chat, auth, sessões    │
└──┬──────────┬──────────┬──────────┬────────────┬────────┘
   │          │          │          │            │
┌──▼──┐  ┌───▼───┐  ┌───▼───┐  ┌──▼────┐  ┌───▼────┐
│ AI  │  │ Voice │  │Emotion│  │Avatar │  │MongoDB │
│8001 │  │ 8004  │  │ 8003  │  │ 8002  │  │  +Redis│
└─────┘  └───────┘  └───────┘  └───────┘  └────────┘
OpenAI    GCloud     DeepFace     DID.ai
 GPT       TTS       MediaPipe
```

### Stack

| Camada | Tecnologia |
|--------|-----------|
| **Frontend (Web UI)** | React 18, Vite, Tailwind CSS, Framer Motion, MUI |
| **Frontend (Admin)** | React 18, Vite, Tailwind CSS, Recharts, Headless UI |
| **API Gateway** | Python 3.11, FastAPI, Motor (async MongoDB), google-auth, python-jose |
| **AI Service** | Python 3.11, FastAPI, OpenAI SDK |
| **Voice Service** | Python 3.11, FastAPI, Google Cloud TTS, librosa |
| **Emotion Service** | TensorFlow 2.13 GPU, DeepFace, MediaPipe, OpenCV |
| **Banco de dados** | MongoDB 7, Redis 7 |
| **Infra** | Docker Compose (local), GKE Autopilot (produção), Terraform, GitHub Actions |

---

## Começando

### Pré-requisitos

- **Docker** 20.10+ e **Docker Compose** 2.0+
- Chave de API **OpenAI**
- **Google OAuth Client ID** (para login)
- Credenciais **Google Cloud** (para síntese de voz — opcional)

### Instalação rápida

```bash
# 1. Clone o repositório
git clone https://github.com/arangelcn/empath-ia.git
cd empath-ia

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas chaves (veja seção Configuração)

# 3. Suba todos os serviços
docker compose up -d

# 4. Acesse
# Web UI:     http://localhost:7860
# Admin:      http://localhost:3001
# API:        http://localhost:8000
# API Docs:   http://localhost:8000/docs
```

### Modo de desenvolvimento (hot reload)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Inclui Mongo Express em `http://localhost:8081`.

---

## Configuração

Copie `.env.example` para `.env` e preencha as chaves abaixo.

### Obrigatórias

```bash
# OpenAI
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o

# Google OAuth (Client ID do console.cloud.google.com)
GOOGLE_CLIENT_ID=xxxxxxx.apps.googleusercontent.com

# JWT (gere com: openssl rand -hex 32)
SECRET_KEY=seu_secret_aqui
```

### Opcionais

```bash
# Google Cloud TTS (coloque o JSON em services/voice-service/credentials/)
CREDENTIALS_JSON=conteudo_do_json_ou_caminho

# DID (avatares animados)
DID_API_USERNAME=seu_usuario
DID_API_PASSWORD=sua_senha

# MongoDB (padrão já funciona com docker compose)
MONGODB_URL=mongodb://admin:admin123@mongodb:27017/empatia?authSource=admin
```

> **Nota:** `VITE_GOOGLE_CLIENT_ID` é definido automaticamente pelo Docker Compose a partir de `GOOGLE_CLIENT_ID`. Não é necessário duplicar.

---

## Serviços e Portas

| Serviço | Porta | URL |
|---------|-------|-----|
| Web UI | `7860` | http://localhost:7860 |
| Admin Panel | `3001` | http://localhost:3001 |
| Gateway API | `8000` | http://localhost:8000 |
| AI Service | `8001` | http://localhost:8001 |
| Emotion Service | `8003` | http://localhost:8003 |
| Voice Service | `8004` | http://localhost:8004 |
| MongoDB *(dev)* | `27017` | — |
| Mongo Express *(dev)* | `8081` | http://localhost:8081 |

---

## API — Endpoints Principais

### Autenticação

```
GET  /api/auth/google/status    → verifica se auth Google está disponível
POST /api/auth/google           → valida ID Token Google, retorna JWT
```

### Chat

```
POST /api/chat/send                         → envia mensagem, recebe resposta IA
GET  /api/chat/history/{session_id}         → histórico da conversa
GET  /api/chat/initial-message/{session_id} → mensagem inicial personalizada
POST /api/chat/finalize/{session_id}        → finaliza sessão e gera contexto
GET  /api/chat/context/{session_id}         → contexto salvo da sessão
```

### Usuário e Sessões

```
GET  /api/user/{username}/sessions                         → lista sessões
GET  /api/user/{username}/sessions/{session_id}            → detalhe
POST /api/user/{username}/sessions/{session_id}/start      → inicia
POST /api/user/{username}/sessions/{session_id}/complete   → conclui
GET  /api/user/{username}/progress                         → progresso geral
POST /api/user/{username}/login                            → registra login + cria session-1
```

### Emoções

```
GET /api/emotions/{username}           → histórico de emoções
GET /api/emotions/{username}/summary   → resumo
GET /api/emotions/{username}/timeline  → linha do tempo
POST /api/emotion/analyze-realtime     → análise via webcam (base64)
```

### Prompts (Admin)

```
GET    /api/prompts                 → lista prompts
POST   /api/prompts                 → cria prompt
GET    /api/prompts/{key}           → busca por chave
PUT    /api/prompts/{key}           → atualiza
DELETE /api/prompts/{key}           → remove (soft delete)
GET    /api/prompts/active/{key}    → prompt ativo
POST   /api/prompts/initialize      → inicializa prompts padrão
```

Documentação interativa completa: [`http://localhost:8000/docs`](http://localhost:8000/docs)

---

## Fluxo das Sessões

```mermaid
graph LR
    Login --> Session1["Session 1\n(Onboarding)"]
    Session1 --> Perfil["Perfil do\nUsuário"]
    Perfil --> Session2["Session 2\n(Personalizada)"]
    Session2 -->|"Finaliza"| Contexto["Contexto\nGerado"]
    Contexto --> Session3["Session 3\n(Auto-gerada\npela IA)"]
    Session3 -->|"..."| SessionN["Session N"]
```

Cada sessão é gerada automaticamente pela IA com base no perfil do usuário e no contexto da sessão anterior — garantindo continuidade terapêutica real.

---

## Banco de Dados

O sistema usa **MongoDB** com as seguintes coleções principais:

| Coleção | Conteúdo |
|---------|----------|
| `users` | Perfis, preferências, dados de autenticação Google |
| `conversations` | Sessões de conversa e metadados |
| `messages` | Mensagens individuais com URLs de áudio |
| `session_contexts` | Contextos estruturados gerados pela IA (fonte única) |
| `user_therapeutic_sessions` | Sessões personalizadas por usuário |
| `user_emotions` | Dados de análise emocional |
| `therapeutic_sessions` | Templates de sessões terapêuticas |
| `prompts` | Prompts do sistema gerenciados pelo admin |

---

## Deploy em Produção (GKE)

O projeto roda em **Google Kubernetes Engine Autopilot** com deploy automático via GitHub Actions.

**Domínios:**
- `app.empat-ia.io` — Web UI
- `admin.empat-ia.io` — Painel Admin
- `api.empat-ia.io` — API Gateway

**Pipeline:**
1. Push para `main` → GitHub Actions builda e publica imagens no Artifact Registry
2. Secrets sincronizados do GCP Secret Manager para K8s Secrets
3. ConfigMap atualizado (inclui `GOOGLE_CLIENT_ID`)
4. Rollout dos Deployments no namespace `empatia`

```bash
# Deploy manual (via workflow_dispatch no GitHub Actions)
# Ou faça push para a branch main

# Verificar pods em produção (requer kubectl configurado)
kubectl get pods -n empatia
```

---

## Monitoramento

```bash
# Health check de todos os serviços
curl http://localhost:8000/health/all

# Logs do gateway
docker logs empatia-gateway --follow

# Logs do AI service
docker logs empatia-ai-service --follow
```

---

## Estrutura do Projeto

```
empath-ia/
├── apps/
│   ├── web-ui/              # Frontend principal (React + Vite)
│   └── admin-panel/         # Painel administrativo (React + Vite)
├── services/
│   ├── gateway-service/     # API Gateway (FastAPI) — ponto central
│   │   └── src/
│   │       ├── api/         # Rotas: auth.py, admin.py
│   │       ├── services/    # chat, user, session, prompt, emotion...
│   │       └── models/      # database.py
│   ├── ai-service/          # IA conversacional (OpenAI)
│   ├── voice-service/       # Text-to-Speech (Google Cloud)
│   ├── emotion-service/     # Análise facial (DeepFace + MediaPipe)
│   └── avatar-service/      # Avatares animados (DID.ai)
├── infrastructure/
│   ├── k8s/                 # Manifests Kubernetes (GKE)
│   └── terraform/           # IaC: GCP, GKE, DNS, Secret Manager
├── docs/
│   └── screenshots/         # Screenshots da aplicação
├── .github/workflows/       # CI/CD (deploy.yml, pipeline.yml)
├── docker-compose.yml        # Stack completa (produção local)
├── docker-compose.dev.yml    # Overrides de desenvolvimento
├── .env.example             # Template de variáveis de ambiente
└── Makefile                 # Atalhos de desenvolvimento
```

---

## Atualizações Recentes

### Abril 2026
- **Login Google em produção corrigido** — endpoint `GET /api/auth/google/status` e `GOOGLE_CLIENT_ID` agora disponíveis no gateway de produção via ConfigMap do K8s
- **Correção de proxy Nginx** — reescrita de `audio_url` para servir áudio pelo gateway
- **Pipeline CI/CD estabilizado** — HTTPS provisionado, certificados gerenciados

### Histórico Anterior
- Sistema completo de gerenciamento de prompts via Admin Panel
- SessionContextService com persistência no MongoDB
- Eliminação de duplicação de contextos (referências em vez de cópia)
- Integração frontend ↔ backend para finalização de sessões
- Continuidade terapêutica com contexto entre sessões
- Desbloqueio gradual e geração automática de sessões

---

## Contribuindo

```bash
# Fork → crie sua branch
git checkout -b feature/minha-feature

# Commit com Conventional Commits
git commit -m "feat: adicionar nova funcionalidade"

# Abra um Pull Request para main
```

**Padrões:** Python — PEP 8 + Black · JavaScript/TypeScript — ESLint + Prettier

---

## Licença

MIT — veja [LICENSE](LICENSE) para detalhes.

---

## Agradecimentos

- **Carl Rogers** — pela abordagem terapêutica centrada na pessoa que inspira o projeto
- **OpenAI** — GPT para respostas terapêuticas
- **Google Cloud** — síntese de voz neural e OAuth
- **MongoDB** — persistência flexível de dados terapêuticos

---

<div align="center">

**Empat.IA** — *Inteligência artificial a serviço do bem-estar humano* 💙

[app.empat-ia.io](https://app.empat-ia.io) · [suporte@empat-ia.io](mailto:suporte@empat-ia.io)

</div>
