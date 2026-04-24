# Plano de Readequação do Empat.IA para MCP (Model Context Protocol)

> Documento gerado em Abril 2026.  
> Objetivo: transformar o Empat.IA em uma plataforma compatível com MCP, expondo suas capacidades como Tools e Resources padronizados — sem quebrar a arquitetura existente.

---

## Índice

1. [Diagnóstico: o que já existe e mapeia para MCP](#1-diagnóstico)
2. [Estratégia: MCP Server sobre o Gateway](#2-estratégia)
3. [Estrutura do novo serviço](#3-estrutura-do-novo-serviço)
4. [Tools a expor (Fase 1)](#4-tools-a-expor)
5. [Resources a expor (Fase 2)](#5-resources-a-expor)
6. [Ajustes no AI Service (Fase 3)](#6-ajustes-no-ai-service)
7. [Pontos de atenção do código atual](#7-pontos-de-atenção)
8. [Tecnologia e dependências](#8-tecnologia-e-dependências)
9. [Integração com Docker Compose](#9-integração-com-docker-compose)
10. [Checklist de implementação](#10-checklist-de-implementação)

---

## 1. Diagnóstico

O Empat.IA já é uma plataforma orientada a **ferramentas de IA com contexto persistente**. Cada microserviço é, na prática, um conjunto de capacidades que um LLM poderia invocar via MCP.

### Mapeamento atual → MCP

| Serviço / Endpoint atual | Tipo MCP | Nome sugerido |
|---|---|---|
| `POST /chat` (AI Service) | **Tool** | `send_therapeutic_message` |
| `POST /openai/generate-session-context` | **Tool** | `generate_session_context` |
| `POST /openai/generate-next-session` | **Tool** | `generate_next_session` |
| `POST /analyze-realtime` (Emotion Service) | **Tool** | `analyze_facial_emotion` |
| `POST /api/voice/speak` | **Tool** | `synthesize_speech` |
| `POST /api/chat/finalize/{session_id}` | **Tool** | `finalize_session` |
| `GET /api/prompts/{key}` | **Resource** | `prompt://{key}` |
| `GET /api/user/{username}/sessions` | **Resource** | `sessions://{username}` |
| `GET /api/emotions/{username}/summary` | **Resource** | `emotions://{username}` |
| MongoDB `session_contexts` | **Resource** | `context://{session_id}` |
| MongoDB `users.user_profile` | **Resource** | `profile://{username}` |

---

## 2. Estratégia

### Por que NÃO reescrever os microserviços

Os microserviços existentes (gateway, ai-service, emotion-service, voice-service) funcionam bem como HTTP APIs e têm lógica de negócio consolidada. Reescrevê-los seria alto risco e baixo retorno.

### A abordagem correta: MCP Server como camada de adaptação

```
┌─────────────────────────────────────────────────────────┐
│              MCP Client (Claude, Cursor, etc.)           │
└──────────────────────────┬──────────────────────────────┘
                           │ MCP Protocol (stdio / SSE)
┌──────────────────────────▼──────────────────────────────┐
│           MCP Server — services/mcp-server/              │
│   Tools: chat, emotion, voice, sessions                  │
│   Resources: context, prompts, emotions, profile         │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP (interno Docker)
┌──────────────────────────▼──────────────────────────────┐
│              API Gateway (FastAPI · Porta 8000)          │
│  Toda a lógica de negócio, auth, MongoDB, Redis          │
└──┬──────────┬──────────┬──────────┬────────────┬────────┘
   │          │          │          │            │
┌──▼──┐  ┌───▼───┐  ┌───▼───┐  ┌──▼────┐  ┌───▼────┐
│ AI  │  │ Voice │  │Emotion│  │Avatar │  │MongoDB │
│8001 │  │ 8004  │  │ 8003  │  │ 8002  │  │  +Redis│
└─────┘  └───────┘  └───────┘  └───────┘  └────────┘
```

**Vantagens desta abordagem:**
- ✅ Zero breaking change — Docker Compose continua funcionando
- ✅ O Gateway já é o ponto único de entrada — o MCP Server simplesmente o chama via HTTP
- ✅ O contexto terapêutico já está estruturado em MongoDB — vira Resources naturais
- ✅ Toda a lógica de auth, session isolation e validação permanece no Gateway
- ✅ Pode ser adicionado incrementalmente, sem parar produção

---

## 3. Estrutura do Novo Serviço

```
services/mcp-server/
├── Dockerfile
├── requirements.txt
└── src/
    ├── __init__.py
    ├── main.py                    # Ponto de entrada FastMCP
    ├── config.py                  # Variáveis de ambiente e configurações
    ├── tools/
    │   ├── __init__.py
    │   ├── chat.py                # send_therapeutic_message, finalize_session
    │   ├── emotion.py             # analyze_facial_emotion
    │   ├── voice.py               # synthesize_speech
    │   └── sessions.py            # create_session, unlock_session, get_progress
    └── resources/
        ├── __init__.py
        ├── context.py             # context://{session_id}
        ├── prompts.py             # prompt://{key}
        ├── emotions.py            # emotions://{username}
        ├── sessions.py            # sessions://{username}
        └── profile.py             # profile://{username}
```

### `requirements.txt`

```
mcp[cli]>=1.0.0
httpx>=0.27.0
python-jose[cryptography]>=3.3.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

### `src/main.py` (esqueleto)

```python
from mcp.server.fastmcp import FastMCP
from .tools import chat, emotion, voice, sessions
from .resources import context, prompts, emotions_res, sessions_res, profile

mcp = FastMCP(
    name="empatia-mcp",
    description="Empat.IA — Plataforma de Terapia Virtual com IA"
)

# Registrar Tools
mcp.tool()(chat.send_therapeutic_message)
mcp.tool()(chat.finalize_session)
mcp.tool()(emotion.analyze_facial_emotion)
mcp.tool()(voice.synthesize_speech)
mcp.tool()(sessions.get_user_sessions)
mcp.tool()(sessions.unlock_session)

# Registrar Resources
mcp.resource("context://{session_id}")(context.get_session_context)
mcp.resource("prompt://{key}")(prompts.get_prompt)
mcp.resource("emotions://{username}")(emotions_res.get_emotion_summary)
mcp.resource("sessions://{username}")(sessions_res.get_sessions)
mcp.resource("profile://{username}")(profile.get_user_profile)

if __name__ == "__main__":
    mcp.run()
```

---

## 4. Tools a Expor

### Fase 1 — Tools prioritárias

#### `send_therapeutic_message`
```python
async def send_therapeutic_message(
    username: str,
    session_id: str,       # formato: "username_session-X"
    message: str,
    is_voice_mode: bool = False
) -> dict:
    """
    Envia uma mensagem do usuário para a sessão terapêutica ativa
    e retorna a resposta da IA com áudio opcional.
    Chama: POST /api/chat/send
    """
```

#### `analyze_facial_emotion`
```python
async def analyze_facial_emotion(
    image_base64: str,     # frame da webcam em base64
    username: str,
    session_id: str
) -> dict:
    """
    Analisa a emoção facial do usuário a partir de um frame de webcam.
    Retorna: dominant_emotion, emotions dict, confidence, face_detected.
    Chama: POST /api/emotion/analyze-realtime
    """
```

#### `finalize_session`
```python
async def finalize_session(session_id: str) -> dict:
    """
    Finaliza a sessão terapêutica: gera contexto estruturado via AI Service
    e cria automaticamente a próxima sessão personalizada.
    Chama: POST /api/chat/finalize/{session_id}
    """
```

#### `synthesize_speech`
```python
async def synthesize_speech(
    text: str,
    voice: str = "pt-BR-Neural2-B"
) -> dict:
    """
    Sintetiza texto em áudio usando Google Cloud TTS.
    Retorna URL do arquivo MP3 gerado.
    Chama: POST /api/voice/speak
    """
```

#### `get_session_context`
```python
async def get_session_context(session_id: str) -> dict:
    """
    Retorna o contexto estruturado de uma sessão finalizada:
    summary, main_themes, key_insights, emotional_state.
    Chama: GET /api/chat/context/{session_id}
    """
```

---

## 5. Resources a Expor

### `context://{session_id}`
- **Fonte**: coleção MongoDB `session_contexts`
- **Conteúdo**: summary, main_themes, key_insights, emotional_state, user_progress
- **Cache TTL**: 5 minutos (contexto raramente muda após gerado)

### `prompt://{key}`
- **Fonte**: `GET /api/prompts/{key}`
- **Conteúdo**: prompt terapêutico editável pelo terapeuta (system_rogers, next_session_generation, etc.)
- **Cache TTL**: 60 segundos (terapeuta pode editar pelo Admin Panel a qualquer momento)

### `emotions://{username}`
- **Fonte**: `GET /api/emotions/{username}/summary`
- **Conteúdo**: emoção dominante, distribuição, timeline, tendências
- **Cache TTL**: 30 segundos (dados em tempo real)

### `sessions://{username}`
- **Fonte**: `GET /api/user/{username}/sessions`
- **Conteúdo**: lista de sessões, status (locked/unlocked/completed), progresso
- **Cache TTL**: 2 minutos

### `profile://{username}`
- **Fonte**: `GET /api/user/{username}` + `registration_data` da session-1
- **Conteúdo**: dados do usuário, preferências, perfil terapêutico
- **Cache TTL**: 5 minutos

---

## 6. Ajustes no AI Service (Fase 3 — opcional)

Esta fase é opcional e de maior impacto. Permite que o LLM dentro do AI Service decida autonomamente quando chamar as ferramentas de emoção, voz e sessão.

### Situação atual
```python
# ai-service/src/services/openai_service.py
response = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    max_tokens=self.max_tokens,
    temperature=self.temperature
)
```

### Situação com MCP (Fase 3)
```python
# O AI Service passa a declarar tools para o OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_facial_emotion",
            "description": "Analisa emoção facial do usuário via webcam",
            "parameters": { ... }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "get_session_context",
            "description": "Busca contexto da sessão anterior",
            "parameters": { ... }
        }
    }
]

response = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    tools=tools,
    tool_choice="auto"
)
# O LLM decide quando chamar cada tool via MCP
```

---

## 7. Pontos de Atenção do Código Atual

### 1. Parsing do `session_id` — replicar no MCP Server
O formato `{username}_session-{N}` tem lógica específica de parsing em `_extract_username_from_session_id()`. O MCP Server precisa replicar essa validação antes de expor qualquer Tool que receba `session_id`.

```python
# Lógica a replicar em services/mcp-server/src/config.py
def extract_username_from_session_id(session_id: str) -> str | None:
    if "_" in session_id:
        last_underscore = session_id.rfind("_")
        username = session_id[:last_underscore]
        session_part = session_id[last_underscore + 1:]
        if session_part.startswith("session-"):
            return username
    return None
```

### 2. Autenticação JWT
O MCP Server precisa de uma das duas estratégias:
- **Opção A (recomendada)**: usar uma service account interna com token de longa duração para chamadas internas Docker (sem expor ao cliente MCP)
- **Opção B**: receber o Bearer token do usuário como parâmetro das Tools e repassar ao Gateway

### 3. Emotion Service — timeout e graceful degradation
O `analyze_facial_emotion` é CPU/GPU intensivo. A Tool deve:
- Timeout de 30 segundos
- Retornar `{"face_detected": false, "dominant_emotion": "neutral"}` quando não há face (não lançar erro)

### 4. Prompts são dinâmicos
O Resource `prompt://{key}` deve ter TTL curto (60s) pois o terapeuta edita pelo Admin Panel sem redeploy.

### 5. Isolamento de sessões (segurança crítica)
Qualquer Tool que acesse dados de sessão deve validar que o `username` extraído do `session_id` corresponde ao usuário autenticado. Ver `SECURITY_FIX_SESSION_ISOLATION.md`.

---

## 8. Tecnologia e Dependências

### SDK MCP oficial (Python)
```bash
pip install "mcp[cli]"
```

### Estrutura do servidor com FastMCP
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("empatia-mcp")

@mcp.tool()
async def send_therapeutic_message(username: str, session_id: str, message: str) -> str:
    """Envia mensagem para sessão terapêutica"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GATEWAY_URL}/api/chat/send",
            json={"message": message, "session_id": session_id},
            headers={"Authorization": f"Bearer {INTERNAL_TOKEN}"}
        )
        return response.json()

@mcp.resource("context://{session_id}")
async def get_session_context(session_id: str) -> str:
    """Contexto estruturado da sessão terapêutica"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{GATEWAY_URL}/api/chat/context/{session_id}")
        return str(response.json())
```

### Modos de transporte suportados
| Modo | Uso |
|------|-----|
| `stdio` | Integração com Claude Desktop, Cursor, VS Code |
| `SSE` (Server-Sent Events) | Integração web, múltiplos clientes simultâneos |
| `streamable-http` | Produção, compatível com GKE |

---

## 9. Integração com Docker Compose

### Adicionar ao `docker-compose.yml`

```yaml
mcp-server:
  build:
    context: ./services/mcp-server
    dockerfile: Dockerfile
  ports:
    - "8005:8005"
  environment:
    - GATEWAY_URL=http://gateway-service:8000
    - INTERNAL_SERVICE_TOKEN=${INTERNAL_SERVICE_TOKEN}
    - MCP_TRANSPORT=sse          # ou stdio para uso local
    - MCP_PORT=8005
  depends_on:
    - gateway-service
  networks:
    - empatia-network
```

### Adicionar ao `infrastructure/k8s/`

```
infrastructure/k8s/mcp-server/
├── deployment.yaml
└── service.yaml
```

---

## 10. Checklist de Implementação

### Fase 1 — MCP Server básico (Tools de chat e sessão)
- [ ] Criar `services/mcp-server/` com estrutura de diretórios
- [ ] Instalar e configurar `mcp[cli]` + `httpx`
- [ ] Implementar Tool `send_therapeutic_message`
- [ ] Implementar Tool `finalize_session`
- [ ] Implementar Tool `get_session_context`
- [ ] Implementar Resource `context://{session_id}`
- [ ] Implementar Resource `sessions://{username}`
- [ ] Adicionar ao `docker-compose.yml`
- [ ] Testar com Claude Desktop (modo stdio)

### Fase 2 — Resources completos e Tools de emoção/voz
- [ ] Implementar Tool `analyze_facial_emotion`
- [ ] Implementar Tool `synthesize_speech`
- [ ] Implementar Resource `prompt://{key}` (com TTL 60s)
- [ ] Implementar Resource `emotions://{username}`
- [ ] Implementar Resource `profile://{username}`
- [ ] Adicionar cache em memória para Resources
- [ ] Adicionar ao K8s (`infrastructure/k8s/mcp-server/`)

### Fase 3 — AI Service com tool calling (opcional)
- [ ] Refatorar `openai_service.py` para declarar tools ao OpenAI
- [ ] Implementar handler de `tool_calls` na resposta do OpenAI
- [ ] Conectar tool calls ao MCP Server interno
- [ ] Testar fluxo completo: usuário → gateway → ai-service → mcp → emotion/voice

### Fase 4 — Produção
- [ ] Configurar autenticação de service account interna
- [ ] Adicionar rate limiting nas Tools
- [ ] Configurar transporte SSE para múltiplos clientes
- [ ] Documentar endpoints MCP no `docs/TECHNICAL.md`
- [ ] Atualizar `docs/AGENTS.md` com referência ao MCP Server

---

## Referências

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Documentation](https://gofastmcp.com)
- [MCP Specification](https://modelcontextprotocol.io/specification)
- [Documentação Técnica do Empat.IA](TECHNICAL.md)
- [Mapa do Código](CODEBASE_MAP.md)

---

*Última atualização: Abril 2026*
