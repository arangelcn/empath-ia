# Refactor Plan: Gateway + AI Service Fusion

Status: proposed execution plan.

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

### Phase 2: migrate AI runtime into v2

- mover `llm_service`, fallback, streaming LLM e políticas RAG;
- eliminar `prompt_client_service` como dependência HTTP;
- integrar prompt source local/repositório interno.

### Phase 3: migrate Gateway application logic into v2

- mover `chat_service`, `session_context_service`, `next_session_service`, `registration_service`, `chat_title_service`;
- separar em fachada + casos de uso;
- manter os contratos externos do Gateway.

### Phase 4: activate LangChain and LangGraph

- substituir montagem manual por pipelines estruturados;
- introduzir `GraphState` e nós principais;
- ligar feature flag para coexistência entre fluxo legado e fluxo novo.

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

1. criar `ai-service-v2`;
2. mover runtime LLM e prompt ownership;
3. mover orquestração de chat/contexto/sessão;
4. preservar contratos públicos do Gateway;
5. introduzir LangChain;
6. introduzir LangGraph;
7. validar frontend/Admin;
8. cortar tráfego;
9. renomear `ai-service-v2` para `ai-service`;
10. remover legado.

## Deliverables

- documento de arquitetura alvo;
- estrutura inicial de `ai-service-v2`;
- mapa de migração por módulo;
- matriz de compatibilidade de rotas e payloads;
- plano de rollout/rollback;
- checklist de remoção final do legado.
