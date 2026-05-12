# Administrative Panel - Empath.IA

This is the administrative panel for the Empath.IA system, built for psychologists and administrators to configure and monitor the real-time emotional analysis platform.

## Features

- **Main Dashboard**: High-level metrics and system statistics
- **User Management**: View and manage users, profiles, and progress
- **Session Management**: Create and edit therapeutic session templates
- **Conversation Analysis**: Inspect chat history and user interactions
- **Prompt Management**: Full interface to edit AI system prompts
- **Advanced Analytics**: Metrics, reports, and trend analysis
- **System Status**: Real-time service monitoring and health checks
- **Settings**: Global system parameters and administrative preferences
- **Authentication**: Secure restricted-access login

## Run Locally

### Prerequisites
- Node.js 16+
- npm or yarn

### Installation

1. Go to the admin panel directory:
```bash
cd apps/admin-panel
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

4. Open `http://localhost:3001`

### Demo credentials
- **Email**: admin@empat-ia.io
- **Password**: admin123

## Interface

### Main pages

1. **Login** (`/login`)
   - Admin authentication
   - Credential validation

2. **Dashboard** (`/`)
   - Overall metrics summary
   - Usage and performance charts
   - Detected emotion statistics

3. **Users** (`/users`)
   - Manage system users
   - View profiles and stats
   - Track therapeutic progress

4. **Sessions** (`/sessions`)
   - Manage therapeutic sessions
   - Create and edit session templates
   - Track user sessions

5. **Conversations** (`/conversations`)
   - View conversation history
   - Analyze user interactions
   - Export session data

6. **Prompts** (`/prompts`)
   - Manage AI system prompts
   - Create, edit, and organize prompts by type
   - Enable/disable prompts dynamically
   - Usage and distribution stats
   - Variable and tags system

7. **Analytics** (`/analytics`)
   - Advanced system metrics
   - Performance reports
   - Trend analysis

8. **System Status** (`/system-status`)
   - Service monitoring
   - Real-time health checks
   - Performance indicators

9. **Settings** (`/settings`)
   - General system settings
   - Runtime parameters
   - Admin preferences

## Design System

### Core colors
- **Primary**: Blue (`#3B82F6`)
- **Success**: Green (`#10B981`)
- **Warning**: Amber (`#F59E0B`)
- **Danger**: Red (`#EF4444`)

### Components
- Responsive layout with Tailwind CSS
- Reusable components
- Interactive charts with Recharts
- Heroicons icon set

## Tech Stack

- **React** 18.2.0 - Main framework
- **Tailwind CSS** 3.4.0 - Styling
- **Recharts** 2.8.0 - Charts and visualizations
- **Heroicons** 2.0.18 - Icons
- **Axios** 1.6.0 - HTTP client
- **date-fns** 2.30.0 - Date utilities

## Data Structures

### System metrics
```javascript
{
  totalUsers: number,
  activeUsers: number,
  totalSessions: number,
  avgSessionDuration: number,
  emotionDistribution: {
    joy: number,
    sadness: number,
    anger: number,
    anxiety: number,
    neutral: number,
    surprise: number
  }
}
```

### Emotion settings
```javascript
{
  sensitivity: {
    joy: number,      // 0-100
    sadness: number,  // 0-100
    anger: number,    // 0-100
    anxiety: number,  // 0-100
    neutral: number,  // 0-100
    surprise: number  // 0-100
  },
  thresholds: {
    detection: number,    // 0-100
    confidence: number    // 0-100
  }
}
```

### Audio settings
```javascript
{
  tts: {
    speed: number,     // 0.5-2.0
    pitch: number,     // 0.5-2.0
    volume: number,    // 0-100
    voice: string      // voice ID
  },
  microphone: {
    sensitivity: number,  // 0-100
    noiseReduction: boolean,
    echoCancellation: boolean
  }
}
```

## Security

- Token-based authentication
- Input validation
- Parameter sanitization
- Role-based access control

## Deployment

### Production build
```bash
npm run build
```

### Environment variables
```env
REACT_APP_API_URL=http://localhost:8001
REACT_APP_EMOTION_SERVICE_URL=http://localhost:8003
REACT_APP_VOICE_SERVICE_URL=http://localhost:8004
REACT_APP_AI_SERVICE_URL=http://localhost:8005
```

## Next features

- [ ] Exportable reports (PDF/Excel)
- [ ] Real-time notifications
- [ ] Advanced AI settings
- [ ] Settings history
- [ ] Data backup/restore
- [ ] Multi-language support
- [ ] Dark mode
- [ ] Audit logs

## Contributing

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push the branch
5. Open a Pull Request

## License

This project is licensed under MIT. See `LICENSE` for details.

## Support

For technical support or questions:
- Email: `support@empat-ia.io`
- Docs: `/docs`
- Issues: GitHub Issues
