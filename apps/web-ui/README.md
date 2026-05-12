# Web UI - Empath.IA

This is the frontend for Empath.IA. It provides the conversational interface where users interact with the virtual psychologist using a modern, reactive, and production-oriented experience.

## Overview

The main interface is a complete chat experience where the user can:

- **Chat naturally** with a Carl Rogers-inspired virtual psychologist
- **Listen to audio responses** with Brazilian Portuguese speech synthesis
- **Personalize the experience** by choosing display name and preferred voice
- **Keep persistent history** across sessions
- **See real-time emotion detection** indicators
- **Control audio playback** manually when needed

## Tech Stack

- **Framework:** [React 18](https://reactjs.org/) with Hooks
- **Build Tool:** [Vite](https://vitejs.dev/)
- **Language:** [TypeScript](https://www.typescriptlang.org/) and JavaScript
- **Styling:** [Tailwind CSS](https://tailwindcss.com/)
- **Icons:** [Lucide React](https://lucide.dev/guide/react)
- **HTTP Client:** [Axios](https://axios-http.com/)
- **Containerization:** Docker with hot reload

## Core Features

### Implemented
- Chat UI with real-time interaction
- Voice conversation mode with smart microphone behavior
- Automatic microphone muting during processing and playback
- Conversation history persistence
- Automatic AI response playback
- Speech recognition for user voice input
- Echo-cancellation settings
- Multiple neural voice options in Portuguese
- Onboarding and preference collection
- Manual play/pause controls per message
- Loading and playback visual states
- Real-time emotion badge
- Responsive design for desktop/tablet/mobile
- Local state plus backend persistence

### Planned
- Sidebar layout similar to modern conversational AI products
- Personal data page
- Full name collection/persistence in login/onboarding
- Light/dark mode
- Advanced audio settings
- Previous sessions history view
- Conversation export
- Animated avatar integration

### Next product cycle

1. **Sidebar navigation:** fixed desktop sidebar and mobile drawer with recent sessions, new session, therapeutic journey, profile, and sign-out.
2. **Personal data page:** authenticated page to view/edit full name, preferred voice, and privacy preferences.
3. **Full name at login:** after Google OAuth, ask for full name when missing and persist it as part of the user profile for UI and AI context.

## Directory Structure

```text
apps/web-ui/
├── public/                      # Static files
│   ├── index.html               # Main HTML template
│   └── favicon.ico              # App icon
├── src/
│   ├── components/              # Reusable React components
│   │   ├── Chat/                # Chat-specific components
│   │   │   ├── ChatScreen.tsx   # Main chat screen
│   │   │   └── MessageBubble.tsx
│   │   ├── Common/              # Shared UI components
│   │   │   ├── Button.tsx
│   │   │   └── Loading.tsx
│   │   ├── Avatar/              # Avatar components (future)
│   │   └── EmotionAnalysis/     # Emotion analysis components
│   ├── hooks/                   # Custom React hooks
│   │   ├── useAudioPlayer.js
│   │   └── useChat.js
│   ├── services/                # API communication layer
│   │   └── api.js
│   ├── utils/                   # Utility functions
│   │   └── formatters.js
│   ├── App.jsx                  # Root component
│   └── main.jsx                 # App entrypoint
├── .env.example                 # Environment sample
├── package.json                 # Dependencies and scripts
├── tailwind.config.js           # Tailwind config
├── vite.config.js               # Vite config
└── Dockerfile                   # Container configuration
```

## Main Components

### `ChatScreen.tsx`
Orchestrates the full chat experience:
- State management for messages, loading, and preferences
- Automatic load of previous history
- Automatic AI audio playback
- Manual playback controls for any message
- Clear loading and playback states

### `WelcomeScreen.tsx`
Onboarding for new users:
- Preference and user data collection
- Next step: collect full legal name and save it on user profile
- Voice selection interface
- Voice preview
- Validation of required onboarding fields

### `EmotionBadge.tsx`
Real-time emotion indicator:
- Auto updates every 5 seconds
- Emoji and color mapping per emotion
- Supported states: happy, sad, neutral, surprised, angry

### `VoiceConversationMode.jsx`
Real-time voice interaction:
- Automatic Brazilian Portuguese speech recognition
- Smart microphone on/off behavior during the flow
- Prevents self-listening during playback/processing
- Echo-cancellation and audio safety settings
- Live transcript display
- Explicit visual state for listening, processing, and playing

**Voice mode flow:**
1. User speaks -> microphone active
2. System processes -> microphone muted automatically
3. AI responds -> microphone stays muted during playback
4. Playback ends -> microphone becomes active again

## Custom Hooks

### `useAudioPlayer.js`
Audio playback management hook:

```javascript
const { playAudio, isPlaying, activeAudioUrl } = useAudioPlayer();

playAudio(audioUrl, onComplete);

if (isPlaying && activeAudioUrl === messageAudioUrl) {
  // show playback indicator
}
```

Features:
- Play/pause control
- Active audio tracking
- Completion callbacks
- Simultaneous playback prevention

### `useVoiceMode.js`
Voice conversation management hook:

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

activateVoiceMode();
muteMicrophone(true);
muteMicrophone(false);
setAudioPlaying(true);
setAudioPlaying(false);
```

Features:
- Continuous Brazilian Portuguese speech recognition
- Physical microphone mute/unmute control
- Echo cancellation and noise suppression
- Playback synchronization
- Automatic end-of-speech detection
- Feedback loop prevention between mic and speaker

### `useChat.js` (planned)
Future centralized chat hook for:
- Message state
- Conversation history
- User preferences
- API integration

## Services

### `api.js`
Centralized HTTP client for the Gateway service:

```javascript
const response = await sendMessage(message, sessionId);
const history = await getChatHistory(sessionId);
const status = await getUserStatus(sessionId);
await saveUserPreferences(sessionId, username, selectedVoice);
```

Integrated endpoints:
- `POST /api/chat/send` - send messages
- `GET /api/chat/history/{session_id}` - fetch history
- `GET /api/user/status/{session_id}` - user status
- `POST /api/user/preferences` - save preferences

## Environment Configuration

Create a `.env` file inside `apps/web-ui`:

```bash
VITE_API_URL=http://localhost:8000
VITE_NODE_ENV=development
VITE_VOICE_SERVICE_URL=http://localhost:8004
VITE_EMOTION_SERVICE_URL=http://localhost:8003
```

## Docker Development

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

## Available Scripts

### Development
```bash
npm install
npm run dev
npm run dev:host
```

### Build and Preview
```bash
npm run build
npm run preview
npm run build:analyze
```

### Code Quality
```bash
npm run lint
npm run lint:fix
npm run format
npm run type-check
```

### Testing (planned)
```bash
npm run test
npm run test:watch
npm run test:coverage
```

## Design System

### Main colors
```css
.primary-blue: bg-blue-500, text-blue-500
.primary-gray: bg-gray-50, text-gray-800
.success-green: bg-green-100, text-green-800
.warning-yellow: bg-yellow-100, text-yellow-800
.error-red: bg-red-100, text-red-800
```

### UI primitives
- Buttons with hover and disabled states
- Cards with soft shadows and rounded corners
- Inputs with blue focus ring and visual validation
- Semantic badges for status

## Data Flow

### State architecture
```text
User Input -> ChatScreen -> API Service -> Gateway -> Backend Services
     ↓                                                      ↓
Audio Player <- Message State <- Response Processing <- AI Response
```

### Message lifecycle
1. User writes/sends a message
2. Message is appended to local state immediately
3. Frontend calls Gateway API
4. AI generates text and audio
5. Response is appended to chat state
6. Audio plays automatically
7. Conversation persists through Gateway to MongoDB

## Performance

### Implemented optimizations
- Code splitting
- Lazy loading for expensive components
- Memoization for heavy renders
- Debounced input handling
- Optimized images/icons

### Target metrics
- First Contentful Paint: `< 1.5s`
- Time to Interactive: `< 3s`
- Bundle size: `< 500KB` (gzipped)
- Lighthouse score: `> 90`

## Troubleshooting

1. **Audio is not playing**
```bash
curl http://localhost:8004/health
# Check browser console for audio errors
```

2. **History is not loading**
```bash
curl http://localhost:8000/api/chat/history/session_test
docker logs empatia-gateway-1 -f
```

3. **UI is not refreshing**
```bash
# Hard refresh in browser: Ctrl+Shift+R
docker logs empatia-web-ui-1 -f
```

### Debug mode

```javascript
localStorage.setItem('debug', 'true');
location.reload();
```

## Backend Integration

### Gateway service
- **Base URL:** `http://localhost:8000/api`
- **Auth model:** session-based (`session_id`)
- **Payload format:** JSON
- **Error handling:** centralized

### Standard response shape
```json
{
  "success": true,
  "data": {
    "ai_response": {
      "id": "msg_123",
      "content": "How can I help you?",
      "audioUrl": "http://localhost:8004/audio/file.mp3"
    }
  }
}
```

## Contributing

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push your branch
5. Open a Pull Request

## License

MIT - see `LICENSE`.

## Support

For technical support or questions:
- Email: `support@empat-ia.io`
- Docs: `/docs`
- Issues: GitHub Issues
