import React, { useState, useEffect } from 'react';
import ChatScreen from './components/Chat/ChatScreen.tsx';
import WelcomeScreen from './components/WelcomeScreen.jsx';
import { Brain, Loader2 } from 'lucide-react';
import { getUserStatus } from './services/api.js';

const generateSessionId = () => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

function App() {
  const [sessionId, setSessionId] = useState('');
  const [username, setUsername] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('');
  const [isOnboarded, setIsOnboarded] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeSession = async () => {
      let currentSessionId = localStorage.getItem('empatia_session_id');
      if (!currentSessionId) {
        currentSessionId = generateSessionId();
        localStorage.setItem('empatia_session_id', currentSessionId);
      }
      setSessionId(currentSessionId);

      try {
        const response = await getUserStatus(currentSessionId);
        if (response.success) {
          const { is_onboarded, username: fetchedUsername, selected_voice } = response.data;
          setIsOnboarded(is_onboarded);
          if (fetchedUsername) {
            setUsername(fetchedUsername);
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

  const handleWelcomeComplete = ({ username: newUsername, voice }) => {
    setUsername(newUsername);
    setSelectedVoice(voice);
    setIsOnboarded(true);
    
    // Armazenar a voz selecionada no localStorage para uso do audioService
    localStorage.setItem('empatia_selected_voice', voice);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex flex-col justify-center items-center">
        <Loader2 className="w-12 h-12 animate-spin text-blue-500" />
        <p className="mt-4 text-gray-600">Carregando sua sessão...</p>
      </div>
    );
  }

  if (!isOnboarded) {
    return <WelcomeScreen onComplete={handleWelcomeComplete} sessionId={sessionId} />;
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-4xl">
        <header className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Brain className="w-12 h-12 text-blue-500" />
            <h1 className="text-4xl font-bold text-gray-800">empatIA</h1>
          </div>
          <p className="text-gray-600 text-lg">
            Sessão de chat com seu psicólogo virtual.
          </p>
        </header>

        <main>
          <ChatScreen sessionId={sessionId} username={username} />
        </main>
        
        <footer className="text-center mt-8">
          <p className="text-gray-500 text-sm">
            Todas as conversas são privadas e seguras.
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App; 