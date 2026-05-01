# Admin Contract Audit

Auditoria da Prioridade 4 do roadmap. O objetivo é impedir que o Admin apresente dados locais ou simulados como se fossem produção.

## Contratos por tela

| Tela | Endpoint principal | Estado atual | Observações |
|---|---|---|---|
| Dashboard | `GET /api/admin/stats`, `GET /api/admin/emotions/analysis`, `GET /api/admin/activity/realtime`, `GET /api/admin/analytics` | Dados reais com lacunas explícitas | Série de sessões usa agregação real quando houver conversa no período. |
| Usuários | `GET /api/admin/users`, `GET /api/admin/users/{username}`, `GET /api/admin/users/{username}/stats` | Dados reais | Criação manual de usuário ficou desabilitada até revisar fluxo operacional. |
| Sessões | `GET /api/admin/user-sessions`, `GET /api/user/{username}/sessions/{session_id}`, `GET /api/admin/session-contexts/{session_id}` | Dados reais | Contexto pode retornar vazio/404 sem mascaramento. |
| Conversas | `GET /api/admin/conversations`, `GET /api/admin/conversations/{session_id}` | Dados reais | Análise emocional por texto foi removida; campo retorna indisponível até existir fonte real. |
| Prompts | `GET/POST/PUT/DELETE /api/prompts...` | Dados reais, lacuna de autorização backend | O cliente já envia bearer token, mas os endpoints ainda são compartilhados com serviços internos. |
| Analytics | `GET /api/admin/analytics?days=` | Dados reais com lacunas explícitas | Demografia, satisfação, insights e duração média ainda não têm fonte persistida. |
| Status | `GET /api/admin/system-status` | Health checks reais | CPU, memória, uptime e ações operacionais ainda não têm coletor/endpoint. |
| Configurações | Pendente | Indisponível explícito | A página deixou de editar estado local e lista contratos pendentes. |

## Autenticação e permissões

- `POST /api/auth/admin/login` emite JWT próprio no mesmo padrão `Authorization: Bearer <token>`.
- O Admin Web guarda `admin_access_token` e anexa o header em todas as chamadas.
- Rotas `/api/admin/*` exigem permissão `read`.
- Criação/edição administrativa exige `write`.
- Exclusões e desativações exigem `sensitive`.
- Credenciais locais vêm de `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL` e `ADMIN_ALLOWED_EMAILS`.

## Lacunas técnicas registradas

1. Proteger ou separar endpoints de prompts: criar namespace administrativo (`/api/admin/prompts`) ou autenticação service-to-service para manter `/api/prompts` seguro sem quebrar o AI Service.
2. Criar contrato de configurações: `GET /api/admin/settings`, `PUT /api/admin/settings`, trilha de auditoria e validação por permissão sensível.
3. Adicionar coletor operacional para status: CPU, memória, uptime, latência média, taxa de erro e fila por serviço.
4. Persistir duração calculada de sessão/conversa para Analytics e Dashboard.
5. Definir fonte real para satisfação e insights; até lá, a UI deve continuar marcando esses blocos como indisponíveis.
6. Substituir ações operacionais visuais por endpoints auditáveis antes de habilitar reinício, backup, cache ou modo de emergência.

## Arquivos alterados

- `apps/admin-panel/src/contexts/AuthContext.js`
- `apps/admin-panel/src/services/api.js`
- `apps/admin-panel/src/components/AdminState.js`
- `apps/admin-panel/src/pages/Dashboard.js`
- `apps/admin-panel/src/pages/Analytics.js`
- `apps/admin-panel/src/pages/SystemStatus.js`
- `apps/admin-panel/src/pages/Settings.js`
- `apps/admin-panel/src/pages/Conversations.js`
- `services/gateway-service/src/api/auth.py`
- `services/gateway-service/src/api/admin.py`
