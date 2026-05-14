# Refactor Plan: Gateway + AI Service Fusion

> **Status: ✅ concluído (pós-migração).**
>
> O `gateway-service` e o `ai-service` legado foram fundidos em um único `ai-service` unificado (monólito modular). Este documento agora serve como registro histórico da decisão arquitetural e do processo de migração. Para a arquitetura atual, consulte `CODEBASE_MAP.md` e `TECHNICAL.md`.

## Objetivo Original

Fundir `gateway-service` e `ai-service` em um monólito organizado, simples de operar e com fronteiras internas claras, sem quebrar os contratos atuais com `web-ui` e `admin-panel`.

A direção seguida foi:

1. levar as responsabilidades do `ai-service` para dentro do `gateway-service`;
2. estabilizar o sistema unificado com compatibilidade de contratos;
3. renomear o boundary resultante para `ai-service`;
4. remover os serviços legados antigos com segurança.

## Resultado Final

- ✅ `gateway-service` removido do compose/deploy
- ✅ `ai-service` legado removido
- ✅ `ai-service-v2` renomeado para `ai-service` (porta 8001)
- ✅ Contratos externos estáveis (web-ui e admin-panel sem quebras)
- ✅ `LegacyAdapterProvider` removido da cadeia de runtime
- ✅ Trilha de `session-1` internalizada e testada
- ✅ Validação end-to-end completa em `8001`

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
- o caminho arquitetural de streaming já emite `meta`, `status`, `text_delta`, áudio e `done` a partir do `AgentService`, e já persiste pelo mesmo `PersistenceNode` do fluxo não-streaming;
- retrieval agora já chama o `knowledge-service` de forma real, aplica política normalizada, filtra resultados por confiança e produz citações no próprio grafo;
- o prompt novo já sabe incorporar contexto recuperado e instruções explícitas de grounding/citação;
- safety já tem heurística inicial própria e já consegue bloquear a resposta final quando detectar conteúdo gerado de alto risco;
- o runtime novo já expõe streaming nativo por provider quando o backend suporta isso, mas o fluxo público ainda segura a emissão final até depois da checagem de safety;
- o fluxo especial de registro `session-1` agora já roda dentro do `ai-service-v2`, persiste perfil/contexto em Mongo e cria a próxima sessão sem depender do `gateway-service`;
- o provider legado do `ai-service` antigo ainda permanece configurável como fallback temporário na cadeia de runtime;
- várias rotas públicas/admin fora do fluxo principal de chat já saíram de scaffold, mas ainda existe trabalho de endurecimento e limpeza final do legado;
- `LangGraph` e `LangChain` já governam o desenho principal, mas ainda falta validação operacional completa e decidir se haverá streaming token-a-token público com guardrails incrementais.

### Practical consequence

O documento de migração passa a considerar a fase de scaffold como concluída em termos de estrutura, e a fase atual como “foundation for orchestration/runtime”, não mais “copiar serviços legados”.

### Validated Remaining Gaps

Depois da validação do estado atual do código, as pendências reais da migração ficaram assim:

- o `ai-service-v2` já assumiu o papel de edge para `web-ui` e `admin-panel`, e o proxy temporário para o `gateway-service` foi removido do caminho HTTP do serviço;
- `chat` principal já saiu do `ai-service` legado, e o fluxo compatível `/api/chat/send-stream` já foi movido para a `StreamFacade`, com validação HTTP real de SSE no `ai-service-v2`;
- o fluxo especial de registro `session-1` já foi internalizado, mas ainda vale endurecer essa trilha com testes dedicados;
- o runtime principal agora já está respondendo com `langchain_openai` usando a key do `.env`, mas o adapter legado ainda existe no código e ainda precisa ser removido quando não houver mais necessidade de rollback;
- auth, usuários, sessões, prompts, chat-context, dashboard/admin, contextos, conversas e knowledge admin já estão servidos pelo `ai-service-v2` sem passar pelo `gateway-service`;
- voice e emotion agora saem diretamente para seus próprios downstreams, sem edge proxy para o `gateway-service`;
- os endpoints internos de health/compatibility já refletem a remoção dessa dependência temporária;
- o serviço já importa, sobe com lifespan real quando Mongo está disponível e responde bem em smoke tests com container fake;
- já houve validação HTTP end-to-end de `health`, `internal/health`, `api/chat/send`, `api/chat/send-stream`, `api/chat/stream`, `openai/chat`, `openai/chat/stream`, `/chat`, `/util/complete`, `/openai/generate-session-context`, `/api/voice/health`, `/api/user/status/*`, `/api/chat/initial-message/*`, `/api/chat/finalize/*`, `/api/auth/admin/login`, `/api/admin/stats`, `/api/admin/users`, `/api/admin/system-status`, `/api/prompts/initialize` e `/api/prompts/stats`;
- houve uma validação específica com o container `gateway-service` desligado, e as rotas críticas testadas continuaram respondendo pelo `ai-service-v2`;
- ainda falta a remoção operacional/física do `gateway-service` e do `ai-service` antigos, a limpeza do fallback legado no runtime e a comparação final de latência/telemetria com o sistema anterior.

### Resume Snapshot

Se a migração for retomada depois, este e o ponto mais rapido para reorientacao.

Ultimo corte concluido:

- o `ai-service-v2` passou a ocupar a porta e o papel do `ai-service` em `8001`;
- o runtime OpenAI do boundary novo foi endurecido para aceitar `LLM_PROVIDER=openai` e ignorar `OPENAI_BASE_URL` vazio, permitindo boot real com `.env` atual;
- o `web-ui` e o `admin-panel` foram repontados para `8001` nos defaults de Vite e nos arquivos de compose;
- o proxy temporário para o `gateway-service` foi removido do `ai-service-v2`;
- auth, usuários, sessões, prompts, chat-context, dashboard/admin, contextos, conversas e knowledge admin agora respondem localmente no boundary novo;
- `voice-service` e `emotion-service` passaram a ser consumidos diretamente pelo `ai-service-v2`, sem passagem pelo `gateway-service`;
- o fluxo síncrono `/chat`, o helper `/util/complete` e `/openai/generate-session-context` já estavam internalizados e agora convivem com um edge totalmente sem proxy para o gateway legado.

Arquivos-chave deste corte:

- `services/ai-service-v2/src/app/api/public/auth.py`
- `services/ai-service-v2/src/app/api/public/users.py`
- `services/ai-service-v2/src/app/api/public/sessions.py`
- `services/ai-service-v2/src/app/api/public/prompts.py`
- `services/ai-service-v2/src/app/api/public/chat.py`
- `services/ai-service-v2/src/app/api/public/voice.py`
- `services/ai-service-v2/src/app/api/public/emotions.py`
- `services/ai-service-v2/src/app/api/admin/dashboard.py`
- `services/ai-service-v2/src/app/api/admin/users.py`
- `services/ai-service-v2/src/app/api/admin/sessions.py`
- `services/ai-service-v2/src/app/api/admin/contexts.py`
- `services/ai-service-v2/src/app/api/admin/conversations.py`
- `services/ai-service-v2/src/app/api/admin/knowledge.py`
- `services/ai-service-v2/src/app/api/security.py`
- `services/ai-service-v2/src/app/api/internal/health.py`
- `services/ai-service-v2/src/app/api/internal/compatibility.py`
- `services/ai-service-v2/src/app/bootstrap/settings.py`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docker-compose.host.yml`

Validacao feita nesta etapa:

- `python3 -m compileall src` passou em `services/ai-service-v2`;
- o container `empatia-ai-service` subiu a partir do código do `ai-service-v2` em `8001`;
- requests HTTP reais passaram para `/chat`, `/api/chat/send`, `/api/chat/send-stream`, `/api/voice/health`, `/api/user/status/*`, `/api/chat/initial-message/*`, `/api/chat/finalize/*`, `/api/auth/admin/login`, `/api/admin/stats`, `/api/admin/users`, `/api/admin/system-status`, `/api/prompts/initialize` e `/api/prompts/stats` via novo edge;
- o runtime respondeu com `provider=langchain_openai` e `model=gpt-4` em chamadas reais;
- os downstreams `voice`, `emotion` e `knowledge` responderam corretamente via integração direta;
- as mesmas rotas críticas seguiram funcionando com o container `empatia-gateway` desligado durante a validação.

O que ainda nao esta fechado:

- o fallback `LegacyAdapterProvider` ainda existe na cadeia de runtime, mesmo nao sendo mais necessario para o caminho principal validado;
- a trilha nova de `session-1` ainda precisa de testes dedicados;
- ainda falta uma rodada final de validacao navegando `web-ui` e `admin-panel` completos contra `8001`;
- ainda falta remover operacionalmente do compose e do deploy os serviços legados `gateway-service` e `ai-service`.

Proximo passo recomendado ao retomar:

1. navegar `web-ui` e `admin-panel` completos apontando para `8001` para capturar qualquer quebra fina de payload/UI;
2. eliminar o `LegacyAdapterProvider` se não houver mais necessidade de rollback;
3. remover `gateway-service` e `ai-service` antigos do compose/deploy;
4. renomear `ai-service-v2` para `ai-service` quando o cutover operacional estiver encerrado.

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
- a cadeia inicial de providers já está modelada em código;
- o caminho compatível síncrono já não depende mais do `ai-service` legado para gerar resposta;
- o stream compatível interno `/openai/chat/stream` também já foi redirecionado para a orquestração nova;
- o `ai-service` legado saiu do caminho crítico de chat e permanece apenas como fallback temporário de provider;
- o runtime ainda não foi validado operacionalmente com providers reais como caminho único.

### Phase 3: migrate Gateway application logic into v2

- mover `chat_service`, `session_context_service`, `next_session_service`, `registration_service`, `chat_title_service`;
- separar em fachada + casos de uso;
- manter os contratos externos do Gateway.

Status atual:

- iniciado para `chat` e `session context`;
- `ChatFacade` já existe como entrypoint novo;
- contratos públicos de chat já têm divisão entre caminho novo e caminho compatível;
- parte da persistência de chat já foi movida da fachada para o grafo;
- o fluxo síncrono compatível `/api/chat/send` já passa pela orquestração nova sem delegar geração ao `ai-service` antigo;
- o fluxo compatível interno `/openai/chat/stream` também já usa o `AgentService` como fonte de resposta;
- o fluxo compatível `/api/chat/send-stream` foi simplificado e movido para a `StreamFacade`, deixando de concentrar a maior parte da adaptação dentro da `ChatFacade`;
- o fluxo especial de registro `session-1` agora também já roda totalmente dentro do `ai-service-v2`, incluindo persistência de perfil, contexto em `session_contexts` e criação determinística da próxima sessão;
- `next_session_service` e `registration_service` deixaram de ser scaffold, mas ainda precisam de testes dedicados e refinamento de contratos para rollout.

### Phase 4: activate LangChain and LangGraph

- substituir montagem manual por pipelines estruturados;
- introduzir `GraphState` e nós principais;
- ligar feature flag para coexistência entre fluxo legado e fluxo novo.

Status atual:

- iniciado;
- `GraphState`, `AgentService`, `nodes/` e `PromptPipeline` já existem;
- a cadeia de providers já existe;
- prompt ownership inicial já existe localmente no `ai-service-v2`;
- retrieval real, grounding e citações já existem no caminho novo;
- safety inicial independente do legado já existe no caminho novo;
- o streaming arquitetural já converge para a mesma persistência e saída final do caminho novo;
- o runtime já suporta streaming nativo por provider no caminho novo;
- falta validar operacionalmente com providers reais e decidir a estratégia final de streaming público sob safety.

### Phase 5: compatibility and shadow validation

- rodar `web-ui` e `admin-panel` contra `ai-service-v2`;
- validar contratos de payload e SSE;
- comparar respostas, latência, logs e fallbacks com o sistema atual.

Status atual:

- ainda não concluído;
- as rotas principais de chat já foram validadas por HTTP real no `ai-service-v2`;
- falta validar as rotas admin/públicas que ainda estão em scaffold;
- smoke tests de rotas principais já existem e passam localmente com container fake;
- o boot real já foi validado com Mongo operacional;
- falta validar rollout com provider real e fallback desabilitado ou restrito para medir maturidade do runtime novo.

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

1. decidir a estratégia final de streaming público sob safety, incluindo se haverá guardrails incrementais para liberar deltas ao vivo;
2. validar o fluxo compatível `/api/chat/send-stream` com consumidores reais agora que ele foi migrado para a `StreamFacade`;
3. consolidar prompt ownership além do catálogo file-backed inicial;
4. validar `web-ui` e `admin-panel` contra o `ai-service-v2`, com atenção a SSE, payloads e telemetria;
5. testar o runtime novo com provider real como caminho preferencial e endurecer o uso do fallback legado;
6. endurecer a trilha de `session-1` com testes dedicados;
7. remover `gateway-service` e `ai-service` antigos do compose/deploy;
8. renomear `ai-service-v2` para `ai-service`;
9. remover legado restante.

## Deliverables

- documento de arquitetura alvo;
- estrutura inicial de `ai-service-v2`;
- estado atual documentado da fundação arquitetural do `ai-service-v2`;
- checklist validado do que ainda falta para a migração completa;
- mapa de migração por módulo;
- matriz de compatibilidade de rotas e payloads;
- plano de rollout/rollback;
- checklist de remoção final do legado.
