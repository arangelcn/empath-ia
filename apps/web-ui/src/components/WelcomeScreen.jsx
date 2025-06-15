import React, { useState } from 'react';
import { Brain, ChevronRight } from 'lucide-react';
import { saveUserPreferences } from '../services/api.js';

const WelcomeScreen = ({ onComplete, sessionId }) => {
  const [username, setUsername] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const voiceOptions = [
    {
      id: 'suave',
      label: 'Voz Suave',
      description: 'Calma e relaxante',
      emoji: '🌸',
      color: 'from-pink-400 to-purple-500'
    },
    {
      id: 'energica',
      label: 'Voz Enérgica',
      description: 'Animada e motivadora',
      emoji: '⚡',
      color: 'from-orange-400 to-red-500'
    },
    {
      id: 'neutra',
      label: 'Voz Neutra',
      description: 'Equilibrada e profissional',
      emoji: '🎯',
      color: 'from-blue-400 to-indigo-500'
    }
  ];

  const handleComplete = async () => {
    if (!username.trim() || !selectedVoice) return;

    setIsLoading(true);
    setError('');

    try {
      await saveUserPreferences(sessionId, username.trim(), selectedVoice);
      onComplete({ username: username.trim(), voice: selectedVoice });
    } catch (err) {
      setError('Ocorreu um erro ao salvar suas preferências. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const canProceed = username.trim().length >= 2 && selectedVoice && !isLoading;

  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8 animate-fade-in">
          <Brain className="w-16 h-16 text-white mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-white mb-2">Bem-vindo!</h1>
          <p className="text-white/80">Vamos personalizar sua experiência</p>
        </div>
        <div className="glass-effect rounded-2xl p-6 space-y-6 animate-slide-up">
          <div>
            <label className="block text-gray-800 text-sm font-medium mb-2">
              Como gostaria de ser chamado?
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Digite seu nome"
              className="w-full px-4 py-3 rounded-xl border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              maxLength={30}
              disabled={isLoading}
            />
          </div>
          <div>
            <label className="block text-gray-800 text-sm font-medium mb-3">
              Escolha o estilo de voz:
            </label>
            <div className="space-y-3">
              {voiceOptions.map((voice) => (
                <div
                  key={voice.id}
                  onClick={() => !isLoading && setSelectedVoice(voice.id)}
                  className={`p-4 rounded-xl cursor-pointer transition-all transform hover:scale-105 ${
                    selectedVoice === voice.id ? 'bg-white/40 ring-2 ring-blue-500 shadow-lg' : 'bg-white/20 hover:bg-white/30'
                  } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-full bg-gradient-to-r ${voice.color} flex items-center justify-center text-xl`}>
                      {voice.emoji}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{voice.label}</h3>
                      <p className="text-sm text-gray-600">{voice.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          {error && <p className="text-red-700 text-sm text-center bg-red-100 p-3 rounded-md">{error}</p>}
          <button
            onClick={handleComplete}
            disabled={!canProceed}
            className={`w-full py-4 rounded-xl font-medium transition-all flex items-center justify-center gap-2 ${
              canProceed
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            {isLoading ? 'Salvando...' : 'Começar conversa'}
            {!isLoading && <ChevronRight className="w-5 h-5" />}
          </button>
          <div className="text-center">
            <p className="text-xs text-gray-600">
              Suas preferências serão salvas para próximas sessões
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen; 