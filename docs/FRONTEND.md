# Frontend — Empat.IA

> Documentação de arquitetura dos dois frontends React: **web-ui** (app do usuário) e **admin-panel** (painel do terapeuta).

---

## Índice

1. [Web UI — App do Usuário](#1-web-ui--app-do-usuário)
2. [Admin Panel — Painel do Terapeuta](#2-admin-panel--painel-do-terapeuta)
3. [Comunicação com a API](#3-comunicação-com-a-api)
4. [Autenticação Google no Frontend](#4-autenticação-google-no-frontend)
5. [localStorage — Chaves utilizadas](#5-localstorage--chaves-utilizadas)
6. [Variáveis de ambiente](#6-variáveis-de-ambiente)
7. [Build e desenvolvimento](#7-build-e-desenvolvimento)

---

## 1. Web UI — App do Usuário

**Porta:** 7860 (dev) · `app.empat-ia.io` (prod)  
**Stack:** React 18, Vite, TypeScript (parcial), Tailwind CSS, MUI, Framer Motion, Lucide

### Rotas

```
/             → LandingScreen     (não autenticado)
/login        → ComingSoonScreen  (placeholder — login via Google está na LandingScreen)
/home         → HomeScreen        (autenticado — Home da jornada terapêutica)
/profile      → ProfileVoicePage  (autenticado — perfil, dados básicos e voz)
/chat         → redireciona para /home (chat exige sessão)
/chat/:sessionId → ChatScreen     (autenticado — chat de sessão específica)
```

**Shell autenticado:** as rotas `/home`, `/profile`, `/chat` e `/chat/:sessionId` renderizam dentro de um layout com menu lateral, aproximando o app das IAs conversacionais atuais. O menu reúne sessões/conversas recentes, ação de continuidade, Home e logout; dados pessoais e configurações ficam consolidados em um único acesso de perfil/voz no rodapé. Em mobile, funciona como drawer. A rota `/chat` sem `sessionId` redireciona para `/home`.

**Lógica de guarda:** `App.jsx` controla o estado `isOnboarded`. Quando `false`, apenas `/` e `/login` estão disponíveis. Quando `true`, apenas `/home`, `/profile`, `/chat` e `/chat/:sessionId`. Qualquer rota fora do grupo redireciona para `/home`.

### Estado global (App.jsx)

O estado vive em `AppRoutes` dentro de `App.jsx`. Não há Redux nem Context API — props drilling para os componentes filhos.

| Estado | Tipo | Descrição |
|--------|------|-----------|
| `sessionId` | string | ID de sessão legado (gerado localmente, armazenado em localStorage) |
| `username` | string | Email do usuário Google |
| `displayName` | string | Nome humano usado na interface e personalização da IA |
| `selectedVoice` | string | ID da voz TTS selecionada |
| `isOnboarded` | boolean | Se o usuário completou o onboarding |
| `isLoading` | boolean | Carregando estado inicial da sessão |

**Inicialização (useEffect em App.jsx):**
1. Verifica/gera `empatia_session_id` no localStorage
2. Chama `GET /api/user/status/{session_id}` para checar se já tem onboarding
3. Define `isOnboarded`, `username`, `displayName` e `selectedVoice` conforme resposta

### Componentes principais

#### `LandingScreen.jsx`
- Tela de apresentação com CTA de login
- Contém ou aciona o fluxo de login Google (GIS SDK)
- Ao concluir login bem-sucedido, chama `handleLoginComplete` em App.jsx

#### `LoginScreen.jsx`
- Fluxo de onboarding pós-login Google:
  1. Valida ID Token do Google via `POST /api/auth/google`
  2. Registra login via `POST /api/user/{username}/login`
  3. Quando `full_name`/`display_name` ainda não existe, solicita nome completo
  4. Coleta preferências: seleção de voz
  5. Salva via `POST /api/user/preferences`
  6. Chama `onLoginComplete({ username, displayName, voice, voiceEnabled, userData })`

O `username`/email continua sendo o identificador técnico. O nome salvo é usado como `displayName` na interface e no contexto enviado à IA.

#### `AuthenticatedShell.jsx` (`components/Layout/`)
- Layout autenticado compartilhado entre `/home`, `/profile`, `/chat` e `/chat/:chatId`
- Sidebar fixa em desktop e drawer no mobile
- Carrega sessões e progresso via `GET /api/user/{username}/sessions` e `GET /api/user/{username}/progress`
- Abre sessões usando `POST /api/user/{username}/sessions/{session_id}/start` quando necessário
- Abre `/chat/{chat_id}` usando o identificador opaco retornado por `POST /api/chat/start`
- Exibe `displayName` quando disponível, sem alterar o identificador técnico

#### `HomeScreen.jsx` (`components/Home/`)
- Home da jornada terapêutica na rota existente `/home`
- Exibe progresso detalhado e sessões terapêuticas do usuário
- Estados visuais por sessão: `locked`, `unlocked`, `in_progress`, `completed`
- Usa os dados carregados pelo `AuthenticatedShell`
- Botão "Iniciar/Continuar/Ver conversa" navega para `/chat/{username}_{session_id}`
- Usa `displayName` no cabeçalho quando disponível

#### `ProfileVoicePage.jsx` (`components/Profile/`)
- Página autenticada `/profile` para dados básicos e voz.
- Exibe email/username técnico, nome exibido e voz preferida.
- Permite editar `preferences.display_name` e `preferences.selected_voice`.
- Salva via `PUT /api/user/{username}/preferences`.
- Mantém email/username como identificador técnico somente leitura.

#### `ChatScreen.tsx` (`components/Chat/`)
- Tela principal de conversa com a IA
- Obtém `sessionId` via `useParams()` (rota `/chat/:sessionId`) ou via props
- **Mensagem inicial:** chama `GET /api/chat/initial-message/{session_id}` quando a sessão não tem mensagens
- **Envio de mensagem:** `POST /api/chat/send`
- **Histórico:** `GET /api/chat/history/{session_id}`
- **Análise emocional:** captura webcam → `POST /api/emotion/analyze-realtime` periodicamente
- **Áudio:** quando `audio_url` vem na resposta, usa `audioService.js` para reproduzir
- **Finalizar sessão:** botão ou detecção de fim → `POST /api/chat/finalize/{session_id}` → redireciona para `/home`
- Exibe `EmotionBadge` com a emoção detectada em tempo real
- Recebe `displayName` para textos de interface, mantendo `username` apenas para isolamento e queries

### Fluxo completo do usuário

```
1. Acessa / (LandingScreen)
2. Clica "Fazer Login com Google" → popup Google → retorna ID Token
3. POST /api/auth/google → recebe JWT de sessão
4. JWT armazenado em localStorage ("empatia_access_token")
5. Se necessário, informa nome completo
6. POST /api/user/{username}/login → cria session-1
7. Seleção de voz + nome completo → POST /api/user/preferences
8. Redireciona para /home
9. AuthenticatedShell carrega progresso e sessões; HomeScreen exibe a Home
10. POST /api/user/{username}/sessions/{session_id}/start
11. Navega para /chat/{username}_{session_id}
12. ChatScreen carrega → GET /api/chat/initial-message/{full_session_id}
13. Conversa... POST /api/chat/send (vai e volta)
14. Análise emocional em background (webcam → POST /api/emotion/analyze-realtime)
15. Clica "Finalizar sessão" → POST /api/chat/finalize/{full_session_id}
16. AI gera contexto + próxima sessão → redireciona para /home
```

---

## 2. Admin Panel — Painel do Terapeuta

**Porta:** 3001 (dev) · `admin.empat-ia.io` (prod)  
**Stack:** React 18, Vite, Tailwind CSS, MUI, Headless UI, Heroicons, Lucide, Recharts

### Rotas

```
/             → Dashboard
/system       → SystemStatus       (health dos microserviços)
/users        → UserManagement     (listar, ver, gerenciar usuários)
/sessions     → SessionManagement  (listar, editar sessões terapêuticas)
/analytics    → Analytics          (gráficos: emoções, engajamento, tendências)
/conversations → Conversations     (visualizar conversas dos usuários)
/prompts      → PromptManagement   (CRUD de prompts da IA)
/settings     → Settings
```

### AuthContext (`contexts/AuthContext.js`)

Provê contexto de autenticação para todo o admin panel.

```js
const { user, isAuthenticated, login, logout } = useAuth();
```

- `user` — dados do usuário autenticado (email, name, picture)
- `isAuthenticated` — boolean
- `login(idToken)` — chama `POST /api/auth/google`, armazena JWT
- `logout()` — limpa estado e localStorage

### Páginas principais

#### `Dashboard.js`
- Métricas gerais: usuários ativos, sessões completadas, total de emoções detectadas, taxa de satisfação
- Chama `GET /api/admin/stats`
- Gráficos com Recharts

#### `PromptManagement.js`
- Lista todos os prompts: `GET /api/prompts?active_only=false`
- Criar: `POST /api/prompts`
- Editar: `PUT /api/prompts/{key}`
- Ativar/desativar: `PUT /api/prompts/{key}` com `{ is_active: true/false }`
- Deletar (soft): `DELETE /api/prompts/{key}`
- Preview de renderização: `POST /api/prompts/render/{key}`

#### `SessionManagement.js`
- Lista sessões terapêuticas de todos os usuários: `GET /api/admin/user-sessions`
- Visualiza status: locked, unlocked, in_progress, completed
- Pode criar/editar sessões template: `CRUD /api/admin/therapeutic-sessions`

#### `Analytics.js`
- Timeline emocional: `GET /api/admin/emotions/analysis`
- Stats em tempo real: `GET /api/admin/emotions/realtime-stats`
- Atividade em tempo real: `GET /api/admin/activity/realtime`
- Renderiza gráficos com Recharts

#### `Conversations.js`
- Lista conversas: `GET /api/admin/conversations`
- Detalhe de conversa: `GET /api/admin/conversations/{session_id}`

#### `SystemStatus.js`
- Verifica saúde de todos os serviços: `GET /health/all`
- Exibe status individual de cada microserviço

---

## 3. Comunicação com a API

### `apps/web-ui/src/services/api.js`

Funções exportadas principais:

```js
getUserStatus(sessionId)          // GET /api/user/status/{session_id}
googleLogin(idToken)              // POST /api/auth/google
registerUserLogin(username)       // POST /api/user/{username}/login
saveUserPreferences(data)         // POST /api/user/preferences
getUserSessions(username)         // GET /api/user/{username}/sessions
startSession(username, sessionId) // POST /api/user/{username}/sessions/{session_id}/start
sendMessage(data)                 // POST /api/chat/send
getChatHistory(sessionId)         // GET /api/chat/history/{session_id}
getInitialMessage(sessionId)      // GET /api/chat/initial-message/{session_id}
finalizeSession(sessionId)        // POST /api/chat/finalize/{session_id}
analyzeEmotion(data)              // POST /api/emotion/analyze-realtime
```

**Base URL:** `import.meta.env.VITE_API_URL` (configurado via `.env.production` ou env no Docker)

**Autenticação:** header `Authorization: Bearer ${localStorage.getItem('empatia_access_token')}` é adicionado automaticamente em todas as requisições via interceptor Axios.

### `apps/admin-panel/src/services/api.js`

Similar ao web-ui mas com endpoints de admin. Base URL via `VITE_API_URL`.

### `apps/web-ui/src/services/audioService.js`

Serviço de reprodução de áudio TTS.

```js
playAudio(audioUrl)   // Reproduz MP3 do URL fornecido
stopAudio()           // Para reprodução atual
isPlaying()           // boolean
```

---

## 4. Autenticação Google no Frontend

**Biblioteca:** Google Identity Services (GIS) — `accounts.google.com/gsi/client`

**Fluxo:**
1. Frontend chama `GET /api/auth/google/status` para confirmar que `GOOGLE_CLIENT_ID` está configurado no servidor
2. Carrega script GIS dinamicamente
3. Inicializa `google.accounts.id.initialize({ client_id, callback })`
4. Renderiza botão Google ou aciona one-tap
5. Callback recebe `{ credential: "<id_token_jwt>" }`
6. Envia para `POST /api/auth/google { credential }`
7. Recebe JWT de sessão e armazena em `localStorage['empatia_access_token']`

**Não usar:** `GOOGLE_CLIENT_SECRET` — o fluxo GIS não usa redirect URI nem troca de código.

---

## 5. localStorage — Chaves utilizadas

| Chave | Onde é definida | Conteúdo |
|-------|----------------|----------|
| `empatia_access_token` | LoginScreen / AuthContext | JWT de sessão emitido pelo gateway |
| `empatia_session_id` | App.jsx | ID de sessão legado (gerado localmente) |
| `empatia_selected_voice` | App.jsx (handleLoginComplete) | ID da voz TTS selecionada |
| `empatia_user_data` | App.jsx (handleLoginComplete) | JSON com dados do usuário Google |

**Logout** limpa: `empatia_user_data`, `empatia_selected_voice` (e redireciona para `/`).  
`empatia_session_id` e `empatia_access_token` persistem intencionalmente entre sessões.

---

## 6. Variáveis de ambiente

### web-ui

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `VITE_API_URL` | ⚠️ | URL base da API. Dev: `http://localhost:8000`. Prod: `https://api.empat-ia.io` |
| `VITE_GOOGLE_CLIENT_ID` | ⚠️ | OAuth Client ID para GIS. Em Docker, derivado de `GOOGLE_CLIENT_ID` via build arg |
| `VITE_GOOGLE_REDIRECT_URI` | — | URI de redirect OAuth. Dev: `http://localhost:7860` |

### admin-panel

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `VITE_API_URL` | ⚠️ | URL base da API. Dev: `http://localhost:8000`. Prod: `https://api.empat-ia.io` |
| `VITE_GOOGLE_CLIENT_ID` | ⚠️ | OAuth Client ID para GIS |

> **Atenção:** variáveis `VITE_*` são embutidas no bundle em tempo de build. Mudar o `.env` exige recompilar com `docker compose build`.

---

## 7. Build e desenvolvimento

### Desenvolvimento local (sem Docker)

```bash
# web-ui
cd apps/web-ui
npm install
npm run dev        # http://localhost:5173 (Vite dev server)

# admin-panel
cd apps/admin-panel
npm install
npm run dev        # http://localhost:5174 (ou porta configurada)
```

Criar arquivo `.env.local` com:
```
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
```

### Com Docker Compose

```bash
# Stack completa com hot reload
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d web-ui admin-panel
```

O `docker-compose.dev.yml` monta `src/` como volume para hot reload.

### Build de produção

```bash
docker compose build web-ui
docker compose build admin-panel
```

As imagens usam multi-stage build:
1. Stage `build` — Node 18, `npm run build`, gera `dist/`
2. Stage final — nginx, serve `dist/` estático, proxy `/api/*` para o gateway

### nginx no container

O nginx de cada frontend faz proxy de `/api/*` para o gateway. Configuração típica:
```nginx
location /api/ {
    proxy_pass http://gateway:8000;
}
```

Isso significa que o frontend não precisa de CORS configurado — todas as chamadas de API passam pelo mesmo origin.

---

*Última atualização: Abril 2026*
