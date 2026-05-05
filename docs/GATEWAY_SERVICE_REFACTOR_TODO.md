# Gateway Service Refactor TODO

Branch de trabalho: `refactor/gateway-service-simplify`

Objetivo: simplificar e otimizar o `services/gateway-service` preservando os contratos HTTP, o schema MongoDB existente e a compatibilidade entre `chat_id` novo e `session_id` legado.

## Status

- [x] Criar branch dedicada para o refactor.
- [x] Mapear arquivos grandes, responsabilidades misturadas e riscos de produção.
- [x] Centralizar configuração inicial em `src/config.py`.
- [x] Corrigir leitura de segredo JWT para aceitar `JWT_SECRET_KEY` e `SECRET_KEY`.
- [x] Remover `--reload` do Dockerfile de produção.
- [x] Corrigir chamada de áudio para usar Voice Service direto, sem loop pelo próprio gateway.
- [x] Remover incremento duplicado de `message_count` no streaming.
- [x] Dividir `src/main.py` em routers menores.
- [x] Dividir `src/api/admin.py` em routers/admin services menores.
- [x] Quebrar `ChatService` em orquestradores, services, clients e repositories.
- [x] Adicionar testes de regressão antes de cada extração de maior risco.
- [ ] Limpar comentários históricos e logs de debug depois que os fluxos estiverem cobertos.

## Mapa Atual

Arquivos com maior concentração de responsabilidade:

- `src/services/chat_service.py`: chat, identidade de conversa, persistência, AI Service, Voice Service, SSE, cadastro `session-1`, contexto de sessão, próxima sessão, título de chat e perfil de usuário.
- `src/main.py`: rotas públicas de chat, user, sessão, proxy AI/avatar/emotion/voice, prompts, config e health.
- `src/api/admin.py`: dashboard, knowledge proxy, conversas, analytics, sessões terapêuticas, usuários, contexto e user sessions.
- `src/models/database.py`: conexão MongoDB e criação de todos os índices.

## Alvos de Arquitetura

Configuração:

- `src/config.py`: fonte única para env vars, URLs, JWT/admin, MongoDB e timeouts.

Clients HTTP:

- `src/clients/ai_client.py`: `/chat`, `/openai/chat/stream`, `/openai/generate-session-context`, `/util/complete`.
- `src/clients/voice_client.py`: `/api/v1/synthesize`, `/api/v1/synthesize-stream`, `/api/v1/audio`.
- `src/clients/knowledge_client.py`: proxy admin para Knowledge Service.
- `src/clients/service_health_client.py`: health checks de serviços internos.

Repositories:

- `src/repositories/conversation_repository.py`
- `src/repositories/message_repository.py`
- `src/repositories/user_repository.py`
- `src/repositories/user_session_repository.py`
- `src/repositories/session_context_repository.py`
- `src/repositories/prompt_repository.py`

Domínio e services:

- `src/domain/conversation_identity.py`: parse e resolução de `chat_id`, `legacy_session_id`, `username`, `therapeutic_session_id`.
- `ChatService` -> `ChatOrchestrator`.
- `RegistrationService`: fluxo de cadastro `session-1`.
- `SessionContextService`: finalização, geração e leitura de contexto.
- `NextSessionService`: criação/desbloqueio da próxima sessão do usuário.
- `VoiceStreamingService`: SSE, chunking e TTS streaming/batch.
- `ChatTitleService`: geração e persistência de título/subtítulo.
- `UserProfileService`: normalização de perfil e dados de cadastro.
- `TherapeuticSessionService` -> `SessionTemplateService`.
- `UserTherapeuticSessionService` -> `UserSessionService` ou `TherapeuticPlanService`.

Routers:

- `src/api/health.py`
- `src/api/chat.py`
- `src/api/users.py`
- `src/api/sessions.py`
- `src/api/voice.py`
- `src/api/emotions.py`
- `src/api/prompts.py`
- `src/api/proxy.py` ou clients dedicados para AI/avatar/emotion.
- `src/api/admin/dashboard.py`
- `src/api/admin/knowledge.py`
- `src/api/admin/conversations.py`
- `src/api/admin/analytics.py`
- `src/api/admin/users.py`
- `src/api/admin/sessions.py`
- `src/api/admin/session_contexts.py`

## Ordem de Execução

1. Baixo risco, já iniciado:
   - Centralizar settings.
   - Corrigir env vars divergentes.
   - Corrigir chamadas internas desnecessárias.
   - Remover duplicações óbvias.

2. `main.py`:
   - [x] Extrair rotas de prompts para `src/api/prompts.py`.
   - [x] Extrair health/config para `src/api/health.py`.
   - [x] Extrair proxy de Voice Service para `src/api/voice.py`.
   - [x] Extrair rotas de emotions para `src/api/emotions.py`.
   - [x] Extrair proxies legados de AI/avatar para `src/api/proxy.py`.
   - [x] Extrair rotas de contexto, título, finalização e mensagem inicial para `src/api/chat_context.py`.
   - [x] Extrair rotas de user/sessions para `src/api/users.py` e `src/api/sessions.py`.
   - [x] Extrair rotas de sessões terapêuticas e user sessions para `src/api/sessions.py`.
   - [x] Extrair rotas de usuário, preferências e login para `src/api/users.py`.
   - [x] Extrair rotas de chat para `src/api/chat.py`.

3. `admin.py`:
   - [x] Extrair Knowledge Service proxy.
   - [x] Extrair dashboard/system-status/analytics.
   - [x] Extrair CRUD de usuários.
   - [x] Extrair CRUD de therapeutic sessions.
   - [x] Extrair session contexts e user sessions.

4. `ChatService`:
   - [x] Extrair helpers puros de identidade de conversa.
   - [x] Extrair repositories de conversations/messages.
   - [x] Extrair `VoiceStreamingService`.
   - [x] Extrair `RegistrationService`.
   - [x] Extrair `SessionContextService`.
   - [x] Extrair `ChatTitleService`.
   - [x] Extrair `UserProfileService`.
   - [x] Extrair `NextSessionService`.
   - [x] Reduzir `ChatService` para orquestração de alto nível.

5. Otimização:
   - [ ] Reutilizar clients HTTP com keep-alive onde fizer sentido.
   - [ ] Rever índices MongoDB e alinhar `message_count` ao significado desejado.
   - [ ] Remover imports circulares e instanciações ad hoc de services.
   - [ ] Remover dependências não usadas em `requirements.txt`.
   - [ ] Padronizar datas para UTC consistente.

6. Testes:
   - [x] Instalar/ativar `pytest` no ambiente local ou container.
   - [x] Testar `SentenceChunker`/SSE.
   - [x] Testar `ConversationIdentity`.
   - [x] Testar geração de título.
   - [x] Testar fluxo `session-1` com mocks.
   - [x] Testar streaming sem duplicar contador.
   - [ ] Testar routers extraídos com `TestClient` e services mockados.

## Critérios de Done

- `main.py` fica apenas com criação do app, middleware, lifespan/startup e `include_router`.
- Nenhum router deve conhecer detalhes de URL interna de microsserviço além dos clients/config.
- `ChatService` fica abaixo de 500 linhas ou vira um orquestrador fino.
- Caminhos HTTP públicos continuam iguais.
- Collections MongoDB e campos legados continuam compatíveis.
- `pytest` roda no gateway e cobre os fluxos de maior risco.
