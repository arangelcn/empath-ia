# Web UI - Empath.IA

Este é o frontend da aplicação Empath.IA, responsável por fornecer a interface de chat para que os usuários possam interagir com a psicóloga virtual. A aplicação é construída com tecnologias modernas, focando em uma experiência de usuário fluida, reativa e completamente funcional.

## ✨ Visão Geral

A interface principal consiste em uma experiência de chat completa onde o usuário pode:

- **Conversar naturalmente** com a psicóloga virtual baseada em Carl Rogers
- **Ouvir respostas em áudio** com síntese de voz em português brasileiro
- **Personalizar a experiência** escolhendo nome de usuário e voz preferida
- **Manter histórico** de conversas que persiste entre sessões
- **Visualizar emoções** detectadas em tempo real
- **Controlar reprodução** de áudio manualmente quando necessário

## 🚀 Tecnologias Utilizadas

-   **Framework:** [React 18](https://reactjs.org/) com Hooks
-   **Build Tool:** [Vite](https://vitejs.dev/) para desenvolvimento rápido
-   **Linguagem:** [TypeScript](https://www.typescriptlang.org/) & JavaScript
-   **Estilização:** [Tailwind CSS](https://tailwindcss.com/) para design moderno
-   **Ícones:** [Lucide React](https://lucide.dev/guide/react) para ícones consistentes
-   **Cliente HTTP:** [Axios](https://axios-http.com/) para comunicação com APIs
-   **Containerização:** Docker com hot reload para desenvolvimento

## 🎯 Funcionalidades Principais

### ✅ Implementado
- ✅ **Chat em Tempo Real**: Interface de chat responsiva e intuitiva
- ✅ **Modo Conversação por Voz**: Interface completa para conversação por voz com controle inteligente do microfone
- ✅ **Controle Inteligente de Microfone**: Microfone automaticamente desligado durante processamento e reprodução de áudio
- ✅ **Persistência de Histórico**: Mensagens mantidas entre sessões
- ✅ **Síntese de Voz**: Reprodução automática das respostas da IA
- ✅ **Reconhecimento de Voz**: Captura e transcrição automática da fala do usuário
- ✅ **Cancelamento de Eco**: Configuração avançada do microfone para evitar feedback
- ✅ **Seleção de Vozes**: Múltiplas opções de vozes neurais em português
- ✅ **Tela de Boas-vindas**: Onboarding com coleta de preferências
- ✅ **Controles de Áudio**: Play/pause manual para cada mensagem
- ✅ **Indicadores Visuais**: Estados de carregamento e reprodução
- ✅ **Detecção de Emoções**: Badge em tempo real com emoção detectada
- ✅ **Design Responsivo**: Funciona em desktop, tablet e mobile
- ✅ **Gerenciamento de Estado**: Estado local e persistência no backend

### 🔄 Planejado
- 🔄 Modo escuro/claro
- 🔄 Configurações avançadas de áudio
- 🔄 Histórico de sessões anteriores
- 🔄 Exportação de conversas
- 🔄 Integração com avatar animado

## 📂 Estrutura de Diretórios

A estrutura de arquivos do `web-ui` é organizada da seguinte forma para garantir escalabilidade e manutenibilidade:

```
apps/web-ui/
├── public/                      # Arquivos estáticos
│   ├── index.html              # Template HTML principal
│   └── favicon.ico             # Ícone da aplicação
├── src/
│   ├── components/             # Componentes React reutilizáveis
│   │   ├── Chat/              # Componentes específicos do chat
│   │   │   ├── ChatScreen.tsx # Tela principal do chat
│   │   │   └── MessageBubble.tsx # Bolhas de mensagem
│   │   ├── Common/            # Componentes comuns
│   │   │   ├── Button.tsx     # Botões reutilizáveis
│   │   │   └── Loading.tsx    # Indicadores de carregamento
│   │   ├── Avatar/            # Componentes do avatar (futuro)
│   │   └── EmotionAnalysis/   # Componentes de análise emocional
│   ├── hooks/                 # Hooks customizados do React
│   │   ├── useAudioPlayer.js  # Hook para reprodução de áudio
│   │   └── useChat.js         # Hook para gerenciamento do chat
│   ├── services/              # Lógica de comunicação com APIs
│   │   └── api.js            # Cliente HTTP para Gateway Service
│   ├── utils/                 # Funções utilitárias
│   │   └── formatters.js     # Formatação de dados
│   ├── App.jsx               # Componente raiz da aplicação
│   └── main.jsx              # Ponto de entrada da aplicação
├── .env.example               # Exemplo de variáveis de ambiente
├── package.json               # Dependências e scripts do projeto
├── tailwind.config.js         # Configuração do Tailwind CSS
├── vite.config.js            # Configuração do Vite
└── Dockerfile                # Container para desenvolvimento
```

## 🧩 Componentes Principais

### `ChatScreen.tsx`
O componente principal que orquestra toda a interface de chat:
- **Gerenciamento de Estado**: Controla mensagens, carregamento e preferências
- **Histórico Persistente**: Carrega automaticamente conversas anteriores
- **Integração de Áudio**: Reproduz automaticamente respostas da IA
- **Controles Manuais**: Permite reprodução manual de qualquer mensagem
- **Indicadores Visuais**: Mostra estados de carregamento e reprodução

### `WelcomeScreen.tsx`
Tela de onboarding para novos usuários:
- **Coleta de Dados**: Nome de usuário e preferências
- **Seleção de Voz**: Interface para escolher voz preferida
- **Teste de Áudio**: Preview das vozes disponíveis
- **Validação**: Garante que todos os dados necessários sejam coletados

### `EmotionBadge.tsx`
Componente para exibição de emoções em tempo real:
- **Detecção Automática**: Atualiza a cada 5 segundos
- **Indicadores Visuais**: Emoji e cor correspondente à emoção
- **Estados Suportados**: Feliz, Triste, Neutro, Surpreso, Com Raiva

### `VoiceConversationMode.jsx`
Componente para conversação por voz em tempo real:
- **Reconhecimento de Voz**: Captura automática da fala do usuário em português brasileiro
- **Controle Inteligente de Microfone**: Automaticamente liga/desliga o microfone nos momentos apropriados
- **Fluxo Seguro**: Garante que o sistema não "se ouça" durante processamento ou reprodução
- **Cancelamento de Eco**: Configurações avançadas para evitar feedback de áudio
- **Transcrição em Tempo Real**: Mostra o que está sendo capturado em tempo real
- **Estados Visuais**: Indicadores claros de quando está ouvindo, processando ou reproduzindo

**Fluxo do Modo de Voz:**
1. **Usuário fala** → Microfone ativo e capturando
2. **Sistema processa** → Microfone automaticamente desligado
3. **IA responde** → Microfone permanece desligado durante reprodução
4. **Áudio termina** → Microfone reativado para nova fala

## 🎣 Hooks Customizados

### `useAudioPlayer.js`
Hook React para gerenciar reprodução de áudio:
```javascript
const { playAudio, isPlaying, activeAudioUrl } = useAudioPlayer();

// Reproduzir áudio
playAudio(audioUrl, onComplete);

// Verificar se está reproduzindo
if (isPlaying && activeAudioUrl === messageAudioUrl) {
  // Mostrar indicador de reprodução
}
```

**Funcionalidades:**
- Controle de play/pause
- Rastreamento de áudio ativo
- Callbacks de conclusão
- Prevenção de reprodução simultânea

### `useVoiceMode.js`
Hook React para gerenciar conversação por voz:
```javascript
const {
  isVoiceModeActive,
  isListening,
  isProcessing,
  transcript,
  error,
  activateVoiceMode,
  deactivateVoiceMode,
  startListening,
  stopListening,
  muteMicrophone,
  setAudioPlaying
} = useVoiceMode(onTranscriptComplete);

// Ativar modo de voz
activateVoiceMode();

// Controlar microfone manualmente
muteMicrophone(true); // Mutar
muteMicrophone(false); // Desmutar

// Informar estado do áudio
setAudioPlaying(true); // Áudio iniciou
setAudioPlaying(false); // Áudio parou
```

**Funcionalidades:**
- Reconhecimento de voz contínuo em português brasileiro
- Controle físico do microfone (mute/unmute)
- Cancelamento de eco e supressão de ruído
- Sincronização com reprodução de áudio
- Detecção automática de fim de fala
- Prevenção de feedback entre microfone e alto-falantes

### `useChat.js` (Planejado)
Hook para gerenciamento centralizado do chat:
- Estado das mensagens
- Histórico de conversas
- Preferências do usuário
- Integração com APIs

## 🔌 Serviços

### `api.js`
Cliente HTTP centralizado para comunicação com o Gateway Service:

```javascript
// Enviar mensagem
const response = await sendMessage(message, sessionId);

// Buscar histórico
const history = await getChatHistory(sessionId);

// Verificar status do usuário
const status = await getUserStatus(sessionId);

// Salvar preferências
await saveUserPreferences(sessionId, username, selectedVoice);
```

**Endpoints Integrados:**
- `POST /api/chat/send` - Enviar mensagens
- `GET /api/chat/history/{session_id}` - Buscar histórico
- `GET /api/user/status/{session_id}` - Status do usuário
- `POST /api/user/preferences` - Salvar preferências

## ⚙️ Configuração do Ambiente

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz de `apps/web-ui`:

```bash
# URL do Gateway Service
VITE_API_URL=http://localhost:8000

# Configurações de desenvolvimento
VITE_NODE_ENV=development

# URLs de serviços (opcional, para desenvolvimento)
VITE_VOICE_SERVICE_URL=http://localhost:8004
VITE_EMOTION_SERVICE_URL=http://localhost:8003
```

### Configuração Docker

O projeto inclui configuração Docker otimizada para desenvolvimento:

```dockerfile
# Dockerfile.dev
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

## 📜 Scripts Disponíveis

No diretório do projeto, você pode executar:

### Desenvolvimento
```bash
npm install          # Instala todas as dependências
npm run dev         # Executa em modo de desenvolvimento (http://localhost:3000)
npm run dev:host    # Executa com acesso externo (0.0.0.0:3000)
```

### Build e Deploy
```bash
npm run build       # Compila o projeto para produção
npm run preview     # Visualiza a build de produção localmente
npm run build:analyze # Analisa o tamanho do bundle
```

### Qualidade de Código
```bash
npm run lint        # Executa ESLint para identificar problemas
npm run lint:fix    # Corrige automaticamente problemas do ESLint
npm run format      # Formata o código usando Prettier
npm run type-check  # Verifica tipos TypeScript
```

### Testes (Planejado)
```bash
npm run test        # Executa testes unitários
npm run test:watch  # Executa testes em modo watch
npm run test:coverage # Gera relatório de cobertura
```

## 🎨 Design System

### Cores Principais
```css
/* Tailwind CSS Classes */
.primary-blue: bg-blue-500, text-blue-500
.primary-gray: bg-gray-50, text-gray-800
.success-green: bg-green-100, text-green-800
.warning-yellow: bg-yellow-100, text-yellow-800
.error-red: bg-red-100, text-red-800
```

### Componentes de UI
- **Botões**: Consistentes com estados hover e disabled
- **Cards**: Sombras suaves e bordas arredondadas
- **Inputs**: Foco com ring azul e validação visual
- **Badges**: Cores semânticas para diferentes estados

## 🔄 Fluxo de Dados

### Arquitetura de Estado
```
User Input → ChatScreen → API Service → Gateway → Backend Services
     ↓                                                      ↓
Audio Player ← Message State ← Response Processing ← AI Response
```

### Ciclo de Vida de uma Mensagem
1. **Input do Usuário**: Digitação e envio da mensagem
2. **Estado Local**: Adição imediata à lista de mensagens
3. **API Call**: Envio para o Gateway Service
4. **Processamento**: IA gera resposta e áudio
5. **Resposta**: Mensagem da IA adicionada ao estado
6. **Áudio**: Reprodução automática da resposta
7. **Persistência**: Salvamento no MongoDB via Gateway

## 🚀 Performance

### Otimizações Implementadas
- **Code Splitting**: Carregamento sob demanda de componentes
- **Lazy Loading**: Componentes carregados quando necessário
- **Memoização**: React.memo para componentes pesados
- **Debounce**: Entrada de texto otimizada
- **Asset Optimization**: Imagens e ícones otimizados

### Métricas de Performance
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Bundle Size**: < 500KB (gzipped)
- **Lighthouse Score**: > 90

## 🐛 Troubleshooting

### Problemas Comuns

1. **Áudio não reproduz**
   ```bash
   # Verificar se o Voice Service está rodando
   curl http://localhost:8004/health
   
   # Verificar logs do navegador
   # F12 → Console → Procurar erros de áudio
   ```

2. **Histórico não carrega**
   ```bash
   # Verificar conexão com Gateway
   curl http://localhost:8000/api/chat/history/session_test
   
   # Verificar logs do Gateway
   docker logs empatia-gateway-1 -f
   ```

3. **Interface não atualiza**
   ```bash
   # Limpar cache do navegador
   # Ctrl+Shift+R (hard refresh)
   
   # Verificar hot reload
   docker logs empatia-web-ui-1 -f
   ```

### Debug Mode

Para habilitar logs detalhados:
```javascript
// No console do navegador
localStorage.setItem('debug', 'true');
location.reload();
```

## 🔗 Integração com Backend

### Gateway Service
- **Base URL**: `http://localhost:8000/api`
- **Autenticação**: Session-based (session_id)
- **Formato**: JSON requests/responses
- **Error Handling**: Tratamento centralizado de erros

### Estrutura de Resposta Padrão
```json
{
  "success": true,
  "data": {
    "ai_response": {
      "id": "msg_123",
      "content": "Como posso ajudá-lo?",
      "audioUrl": "http://localhost:8004/audio/file.mp3"
    }
  }
}
``` 