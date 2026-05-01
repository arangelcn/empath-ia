import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import ChatScreen from './components/Chat/ChatScreen.tsx';
import LoginScreen from './components/LoginScreen.jsx';
import HomeScreen from './components/Home/HomeScreen.jsx';
import LandingScreen from './components/LandingScreen.jsx';
import AuthenticatedShell from './components/Layout/AuthenticatedShell.jsx';
import ProfileVoicePage from './components/Profile/ProfileVoicePage.jsx';
import { Brain, Loader2 } from 'lucide-react';
import { getUserStatus } from './services/api.js';

const generateSessionId = () => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

function AppRoutes() {
  const [sessionId, setSessionId] = useState('');
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('');
  // const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);  // Comentado temporariamente
  const [isOnboarded, setIsOnboarded] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const initializeSession = async () => {
      let currentSessionId = localStorage.getItem('empatia_session_id');
      if (!currentSessionId) {
        currentSessionId = generateSessionId();
        localStorage.setItem('empatia_session_id', currentSessionId);
      }
      setSessionId(currentSessionId);

      // Carregar preferência de voz do localStorage - COMENTADO TEMPORARIAMENTE
      // const savedVoiceEnabled = localStorage.getItem('empatia_voice_enabled');
      // if (savedVoiceEnabled !== null) {
      //   setIsVoiceEnabled(savedVoiceEnabled === 'true');
      // }

      try {
        const savedUserRaw = localStorage.getItem('empatia_user');
        const accessToken = localStorage.getItem('empatia_access_token');
        if (accessToken && savedUserRaw) {
          const savedUser = JSON.parse(savedUserRaw);
          const restoredUsername = savedUser.username || savedUser.email;
          if (restoredUsername) {
            setUsername(restoredUsername);
            setDisplayName(savedUser.display_name || savedUser.full_name || savedUser.name || restoredUsername);
            setSelectedVoice(savedUser.preferences?.selected_voice || localStorage.getItem('empatia_selected_voice') || '');
            setIsOnboarded(true);
            return;
          }
        }

        const response = await getUserStatus(currentSessionId);
        if (response.success) {
          const { is_onboarded, username: fetchedUsername, selected_voice, display_name, full_name } = response.data;
          setIsOnboarded(is_onboarded);
          if (fetchedUsername) {
            setUsername(fetchedUsername);
          }
          if (display_name || full_name) {
            setDisplayName(display_name || full_name);
          }
          if (selected_voice) {
            setSelectedVoice(selected_voice);
          }
        }
      } catch (error) {
        // Permite que o usuário prossiga mesmo se a verificação falhar
      } finally {
        setIsLoading(false);
      }
    };

    initializeSession();
  }, []);

  const handleLoginComplete = ({ username: newUsername, voice, voiceEnabled, displayName: newDisplayName, userData }) => {
    setUsername(newUsername);
    setDisplayName(newDisplayName || userData?.display_name || userData?.full_name || userData?.name || newUsername);
    setSelectedVoice(voice);
    // setIsVoiceEnabled(voiceEnabled);  // Comentado temporariamente
    setIsOnboarded(true);
    
    // Armazenar as preferências no localStorage
    localStorage.setItem('empatia_selected_voice', voice);
    // localStorage.setItem('empatia_voice_enabled', voiceEnabled.toString());  // Comentado temporariamente
    
    // Armazenar dados do usuário se disponíveis
    if (userData) {
      localStorage.setItem('empatia_user_data', JSON.stringify(userData));
    }
    navigate('/home');
  };

  const handleLogout = () => {
    setIsOnboarded(false);
    setUsername('');
    setDisplayName('');
    setSelectedVoice('');
    localStorage.removeItem('empatia_user_data');
    localStorage.removeItem('empatia_selected_voice');
    navigate('/');
  };

  // const handleVoiceToggle = (enabled) => {  // Comentado temporariamente
  //   setIsVoiceEnabled(enabled);
  //   localStorage.setItem('empatia_voice_enabled', enabled.toString());
  // };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex flex-col justify-center items-center">
        <Loader2 className="w-12 h-12 animate-spin text-blue-500" />
        <p className="mt-4 text-gray-600">Carregando sua sessão...</p>
      </div>
    );
  }

  return (
    <Routes>
      {!isOnboarded && (
        <>
          <Route path="/" element={<LandingScreen />} />
          <Route path="/login" element={
            <LoginScreen
              onComplete={handleLoginComplete}
              sessionId={sessionId}
            />
          } />
          <Route path="/*" element={<Navigate to="/" replace />} />
        </>
      )}
      {isOnboarded && (
        <Route element={
          <AuthenticatedShell
            username={username}
            displayName={displayName}
            setDisplayName={setDisplayName}
            selectedVoice={selectedVoice}
            setSelectedVoice={setSelectedVoice}
            onLogout={handleLogout}
          />
        }>
          <Route path="/home" element={<HomeScreen />} />
          <Route path="/profile" element={<ProfileVoicePage />} />
          <Route path="/chat/:chatId" element={
            <ChatScreen
              username={username}
              displayName={displayName}
            />
          } />
          <Route path="/chat" element={<Navigate to="/home" replace />} />
          <Route path="/*" element={<Navigate to="/home" replace />} />
        </Route>
      )}
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AppRoutes />
    </Router>
  );
}

export default App; 
