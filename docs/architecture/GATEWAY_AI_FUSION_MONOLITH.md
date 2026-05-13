# Refactor Plan: Gateway + AI Service Fusion

Status: in progress.

## Objective

Fundir `gateway-service` e `ai-service` em um monólito organizado, simples de operar e com fronteiras internas claras, sem quebrar os contratos atuais com `web-ui` e `admin-panel`.

A direção preferida é:

1. levar as responsabilidades do `ai-service` para dentro do `gateway-service`;
2. estabilizar o sistema unificado com compatibilidade de contratos;
3. renomear o boundary resultante para `ai-service`;
4. remover os serviços legados antigos com segurança.

## Why This Refactor

Hoje existe acoplamento alto e duplicação entre `gateway-service` e `ai-service`:

- chat e streaming são orquestrados em dois lugares;
- prompts dependem de HTTP interno entre serviços;
- contexto de sessão e fallback têm ownership ambíguo;
- parte da complexidade atual existe só para sustentar a separação entre os dois serviços.

O objetivo deste refactor não é “crescer arquitetura”. É o oposto: reduzir moving parts, deixar o caminho crítico mais curto e criar uma base limpa para LangChain, LangGraph e LlamaIndex.

## Design Principles

- preservar contratos externos primeiro;
- simplificar antes de expandir capacidades;
- um único owner por responsabilidade;
- transporte HTTP separado de domínio e runtime LLM;
- migração incremental com rollback fácil;
- monólito modular, não arquivo gigante;
- bibliotecas entram para reduzir plumbing manual, não para esconder regras críticas.

## Scope

### In scope

- fusão de `gateway-service` e `ai-service`;
- compatibilidade com `web-ui` e `admin-panel`;
- unificação de chat, streaming, prompts, fallback, contexto de sessão e geração LLM;
- reorganização de diretórios e serviços internos;
- introdução planejada de `LangChain`, `LangGraph` e `LlamaIndex`.

### Out of scope

- fundir `voice-service`, `emotion-service` e `knowledge-service` neste momento;
- redesenhar UX do frontend junto com a fusão;
- reescrever todos os fluxos em uma única etapa;
- alterar o princípio clínico e de segurança do produto.

## Target Strategy

### Preferred path

Criar um novo boundary temporário: `ai-service-v2`.

Racional:

- permite migrar sem quebrar o `gateway-service` atual;
- facilita shadow testing e comparação de resposta/latência;
- reduz risco de rename prematuro;
- deixa claro o que é legado e o que é arquitetura nova.

### Final desired state

- o serviço hoje exposto como Gateway deixa de existir como conceito técnico separado;
- o monólito unificado passa a ser o único backend principal;
- o nome operacional final vira `ai-service`;
- `gateway-service` antigo e `ai-service` antigo são removidos.

## Migration Options

### Option A: direct fusion into current `gateway-service`

Prós:

- menos serviços temporários;
- rename final menor.

Contras:

- mistura legado e novo no mesmo lugar logo no começo;
- rollback mais confuso;
- aumenta risco de regressão silenciosa.

### Option B: build `ai-service-v2` first

Prós:

- rollout incremental;
- comparação controlada;
- rename final simples;
- melhor isolamento do refactor.

Contras:

- custo temporário de manutenção de três boundaries.

### Recommendation

Seguir com **Option B**: construir `ai-service-v2`, migrar contratos, validar, renomear no final.

## Contract Preservation

Durante a fusão, o contrato externo precisa continuar estável.

### Must remain stable first

- endpoints usados pelo `web-ui` em `/api/chat`, `/api/user`, `/api/voice`, `/api/prompts`, `/api/admin/*`, `/api/chat/*`;
- payloads de chat e streaming SSE;
- autenticação JWT/Google;
- formatos de histórico, contexto, sessões e preferências;
- comportamento esperado do Admin para prompts, conhecimento, usuários, sessões e analytics.

### Compatibility rule

Antes do rename final, o novo serviço deve expor:

- as rotas públicas atuais do Gateway;
- adapters internos para rotas herdadas do AI antigo, quando necessário;
- logs e métricas comparáveis com o sistema atual.

## Proposed Topology

### Current

`web-ui/admin` -> `gateway-service` -> `ai-service`

### Transitional

`web-ui/admin` -> `gateway-service` -> `ai-service-v2`

ou, em rotas selecionadas:

`web-ui/admin` -> `ai-service-v2`

com compatibilidade controlada.

### Final

`web-ui/admin` -> `ai-service`

onde `ai-service` já é o monólito unificado.

## Target Monolith Structure

Estrutura sugerida para `services/ai-service-v2/src/`:

```text
src/
├── main.py
├── app/
│   ├── bootstrap/
│   │   ├── settings.py
│   │   ├── logging.py
│   │   ├── dependencies.py
│   │   └── lifespan.py
│   ├── api/
│   │   ├── public/
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── chat_context.py
│   │   │   ├── users.py
│   │   │   ├── sessions.py
│   │   │   ├── voice.py
│   │   │   ├── emotions.py
│   │   │   └── prompts.py
│   │   ├── admin/
│   │   │   ├── dashboard.py
│   │   │   ├── users.py
│   │   │   ├── sessions.py
│   │   │   ├── conversations.py
│   │   │   ├── contexts.py
│   │   │   └── knowledge.py
│   │   └── internal/
│   │       ├── llm.py
│   │       ├── health.py
│   │       └── compatibility.py
│   ├── domain/
│   │   ├── conversations/
│   │   ├── sessions/
│   │   ├── prompts/
│   │   ├── users/
│   │   └── safety/
│   ├── application/
│   │   ├── chat/
│   │   │   ├── chat_facade.py
│   │   │   ├── stream_facade.py
│   │   │   ├── session_context_service.py
│   │   │   ├── next_session_service.py
│   │   │   └── registration_service.py
│   │   ├── llm/
│   │   │   ├── runtime_service.py
│   │   │   ├── prompt_pipeline.py
│   │   │   ├── structured_outputs.py
│   │   │   └── fallback_service.py
│   │   ├── orchestration/
│   │   │   ├── graph_state.py
│   │   │   ├── agent_service.py
│   │   │   ├── nodes/
│   │   │   └── policies/
│   │   └── retrieval/
│   │       ├── rag_gateway.py
│   │       ├── retrieval_policy.py
│   │       └── citations.py
│   ├── infrastructure/
│   │   ├── db/
│   │   ├── cache/
│   │   ├── http/
│   │   ├── llm/
│   │   └── observability/
│   └── repositories/
│       ├── conversations.py
│       ├── prompts.py
│       ├── users.py
│       └── sessions.py
└── prompts/
```

## Current Status Of `ai-service-v2`

O novo boundary já existe em `services/ai-service-v2` e não está mais só em modo “hello world”.

### What is already built

- bootstrap FastAPI separado do legado;
- container de dependências próprio;
- rotas públicas, admin e internas registradas;
- caminhos de compatibilidade para `/api/chat/send`, `/api/chat/send-stream` e `/openai/*`;
- `GraphState` canônico para a nova orquestração;
- `AgentService` orientado a grafo com nós explícitos;
- `PromptPipeline` preparado para `LangChain`;
- prompt catalog mínimo já internalizado no próprio `ai-service-v2`;
- `RuntimeService` reposicionado como shell de runtime para `LangChain`, com cadeia explícita de providers;
- provider `LangChain/OpenAI-compatible` já modelado como backend primário;
- adapter legado já modelado como provider de fallback, não mais como caminho central;
- repositório Mongo próprio do `ai-service-v2`;
- `ContextNode` já enriquece o `GraphState` com identidade, histórico, perfil, contexto anterior, voz e prompt inicial;
- `PersistenceNode` já executa persistência real para o caminho novo não-streaming;
- `ChatFacade` com dois caminhos distintos:
  - caminho novo: `/api/chat` e `/api/chat/stream` usam a orquestração nova;
  - caminho compatível: `/api/chat/send*` preserva a borda atual.

### Important architectural decision already taken

O `ai-service-v2` não está mais sendo tratado como “gateway copiado com novos nomes”.

A direção agora é:

- o fluxo principal novo vive em `ChatFacade -> AgentService -> LangGraph nodes -> RuntimeService`;
- adapters legados existem apenas para compatibilidade e rollout;
- compatibilidade não define mais a arquitetura interna.

### What is still provisional

- o runtime novo já possui cadeia de providers, mas ainda precisa de validação operacional com dependências instaladas e credenciais reais;
- o `PersistenceNode` já executa persistência real no caminho não-streaming, mas o streaming arquitetural ainda precisa convergir para o mesmo modelo final;
- retrieval e safety já têm nós dedicados, porém ainda com implementação inicial;
- `LangGraph` e `LangChain` já governam o desenho principal, mas ainda não representam o caminho produtivo completo ponta a ponta.

### Practical consequence

O documento de migração passa a considerar a fase de scaffold como concluída em termos de estrutura, e a fase atual como “foundation for orchestration/runtime”, não mais “copiar serviços legados”.

## Responsibility Boundaries

### API layer

- recebe requests e valida payloads;
- não monta prompt;
- não decide fallback;
- não persiste regra de negócio diretamente.

### Application layer

- orquestra casos de uso;
- coordena chat, streaming, contexto, próxima sessão, voz e segurança;
- concentra o fluxo que hoje está quebrado entre Gateway e AI.

### Domain layer

- regras puras de identidade, sessão, política, validação e comportamento;
- sem dependência direta de FastAPI, Mongo, Redis ou HTTP.

### Infrastructure layer

- acesso a MongoDB, Redis, LLM providers e clientes HTTP;
- adapters para `voice-service`, `emotion-service` e `knowledge-service`.

## Tooling Plan

## LangChain

Usar para reduzir código manual em:

- construção de prompts;
- structured output;
- pipelines determinísticos de chat, contexto de sessão e próxima sessão;
- normalização da camada de provider/runtime.

Aplicação recomendada:

- `application/llm/prompt_pipeline.py`
- `application/llm/structured_outputs.py`
- `application/retrieval/retrieval_policy.py`

## LangGraph

Usar para a orquestração principal do chat:

- entrada;
- enriquecimento de contexto;
- retrieval;
- geração;
- safety;
- persistência;
- streaming/saída.

Aplicação recomendada:

- `application/orchestration/graph_state.py`
- `application/orchestration/agent_service.py`
- `application/orchestration/nodes/`

## LlamaIndex

Usar preferencialmente no boundary de conhecimento, não no núcleo HTTP do monólito.

Aplicação recomendada:

- manter `knowledge-service` separado;
- usar LlamaIndex como engine de ingestão, retrieval, citation e metadata filtering;
- o monólito consome isso via `rag_gateway.py`.

Regra:

- `LangChain` e `LangGraph` entram no monólito unificado;
- `LlamaIndex` fica concentrado no `knowledge-service`, salvo necessidade muito concreta.

## Migration Phases

### Phase 0: preparation

- congelar contratos públicos relevantes;
- mapear endpoints consumidos por `web-ui` e `admin-panel`;
- listar dependências cíclicas e fluxos duplicados;
- definir smoke tests obrigatórios.

### Phase 1: scaffold `ai-service-v2`

- criar nova estrutura modular;
- copiar bootstrap, config e health;
- expor rotas mínimas de compatibilidade;
- configurar observabilidade e feature flags.

Status atual:

- concluído para a estrutura base;
- concluído para rotas mínimas;
- parcialmente concluído para compatibilidade controlada.

### Phase 2: migrate AI runtime into v2

- mover `llm_service`, fallback, streaming LLM e políticas RAG;
- eliminar `prompt_client_service` como dependência HTTP;
- integrar prompt source local/repositório interno.

Status atual:

- iniciado, mas com mudança de abordagem;
- o foco deixou de ser “mover o `llm_service` como está”;
- o foco passou a ser construir `RuntimeService` e providers com abstrações `LangChain`, mantendo adapter legado apenas como fallback temporário;
- a cadeia inicial de providers já está modelada em código.

### Phase 3: migrate Gateway application logic into v2

- mover `chat_service`, `session_context_service`, `next_session_service`, `registration_service`, `chat_title_service`;
- separar em fachada + casos de uso;
- manter os contratos externos do Gateway.

Status atual:

- iniciado para `chat` e `session context`;
- `ChatFacade` já existe como entrypoint novo;
- contratos públicos de chat já têm divisão entre caminho novo e caminho compatível;
- parte da persistência de chat já foi movida da fachada para o grafo.

### Phase 4: activate LangChain and LangGraph

- substituir montagem manual por pipelines estruturados;
- introduzir `GraphState` e nós principais;
- ligar feature flag para coexistência entre fluxo legado e fluxo novo.

Status atual:

- iniciado;
- `GraphState`, `AgentService`, `nodes/` e `PromptPipeline` já existem;
- a cadeia de providers já existe;
- prompt ownership inicial já existe localmente no `ai-service-v2`;
- falta transformar esse runtime em caminho produtivo completo com persistência final, retrieval real e validação operacional.

### Phase 5: compatibility and shadow validation

- rodar `web-ui` e `admin-panel` contra `ai-service-v2`;
- validar contratos de payload e SSE;
- comparar respostas, latência, logs e fallbacks com o sistema atual.

### Phase 6: switch traffic

- apontar frontend e Admin para o novo boundary;
- manter aliases/compat shims por janela limitada;
- congelar escrita no legado se necessário.

### Phase 7: rename and cleanup

- renomear `ai-service-v2` para `ai-service`;
- remover `gateway-service` legado;
- remover `ai-service` antigo;
- atualizar documentação, compose, infra e mapas do código.

## Frontend Transition Plan

### Stage 1

Não mudar contrato do frontend. O novo backend se adapta ao frontend atual.

### Stage 2

Quando o monólito estiver estável:

- revisar nomes de rotas e namespaces;
- remover endpoints herdados que só existiam por compatibilidade;
- atualizar `web-ui` e `admin-panel` para o naming final.

### Rule

Primeiro preservar compatibilidade. Depois limpar naming.

## Routing and Contract Policy

### During migration

- manter `/api/chat/*`, `/api/user/*`, `/api/voice/*`, `/api/prompts/*`, `/api/admin/*`;
- manter payloads SSE existentes;
- manter formatos de sessão/contexto usados hoje;
- adicionar endpoints internos de compatibilidade só onde necessário.

### After cutover

- revisar nomes ligados à separação antiga;
- remover contratos obsoletos;
- documentar mapa “route old -> route new”.

## Risks

### Main risks

- regressão silenciosa em streaming SSE;
- quebra de contratos usados pelo Admin;
- mistura prematura de legacy com arquitetura nova;
- perda de telemetria durante o cutover;
- aumento de latência se LangGraph entrar cedo demais sem medir.

### Mitigations

- `ai-service-v2` separado;
- feature flags para orquestração;
- smoke tests por endpoint público;
- comparação de payloads reais;
- rollback operacional claro por boundary.

## Acceptance Criteria

- `web-ui` funciona sem regressão relevante nos fluxos de login, chat, streaming, sessões e preferências.
- `admin-panel` funciona sem regressão relevante em prompts, usuários, sessões, contextos, conhecimento e dashboard.
- o caminho crítico de chat deixa de depender de HTTP interno entre Gateway e AI.
- prompts, fallback e contexto têm ownership único.
- o monólito fica organizado por camadas e não por acúmulo em um único service.
- LangChain reduz montagem manual de prompt e structured parsing.
- LangGraph governa o fluxo principal por feature flag antes de virar padrão.
- o rename final para `ai-service` acontece só depois de validação operacional.

## Recommended Execution Sequence

1. concluir a convergência do streaming arquitetural para o mesmo modelo de persistência do caminho novo;
2. consolidar prompt ownership além do catálogo file-backed inicial;
3. plugar retrieval real e safety real ao fluxo principal;
4. expandir compatibilidade pública só onde o frontend/Admin realmente exigirem;
5. validar frontend/Admin;
6. cortar tráfego;
7. renomear `ai-service-v2` para `ai-service`;
8. remover legado.

## Deliverables

- documento de arquitetura alvo;
- estrutura inicial de `ai-service-v2`;
- estado atual documentado da fundação arquitetural do `ai-service-v2`;
- mapa de migração por módulo;
- matriz de compatibilidade de rotas e payloads;
- plano de rollout/rollback;
- checklist de remoção final do legado.
