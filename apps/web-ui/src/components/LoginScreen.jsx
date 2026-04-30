import React, { useState, useEffect } from 'react';
import { Button, Card } from './Common';
import { saveUserPreferences } from '../services/api.js';
import GoogleAuth from './GoogleAuth.jsx';

const LoginScreen = ({ onComplete, sessionId }) => {
  const [selectedVoice, setSelectedVoice] = useState('pt-BR-Neural2-B');
  const [fullName, setFullName] = useState('');
  const [needsProfileName, setNeedsProfileName] = useState(false);
  const [error, setError] = useState('');
  const [userData, setUserData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const voiceOptions = [
    {
      id: 'pt-BR-Neural2-B',
      label: 'Voz Masculina Confiante (Recomendada)',
      emoji: '⚡',
      description: 'Tom seguro e profissional',
    },
    {
      id: 'pt-BR-Neural2-A',
      label: 'Voz Feminina Suave',
      emoji: '🌸',
      description: 'Tom suave e acolhedor',
    },
    {
      id: 'pt-BR-Wavenet-A',
      label: 'Voz Feminina Profissional',
      emoji: '💼',
      description: 'Tom claro e objetivo',
    },
    {
      id: 'pt-BR-Wavenet-B',
      label: 'Voz Masculina Amigável',
      emoji: '🎯',
      description: 'Tom caloroso e próximo',
    },
    {
      id: 'pt-BR-Wavenet-C',
      label: 'Voz Feminina Calorosa',
      emoji: '🌺',
      description: 'Tom empático e compreensivo',
    },
  ];

  // Restaurar sessão Google caso o usuário já tenha feito login antes
  useEffect(() => {
    const saved = localStorage.getItem('empatia_user');
    if (saved) {
      try {
        const user = JSON.parse(saved);
        if (user.auth_method === 'google' && localStorage.getItem('empatia_access_token')) {
          setUserData(user);
          const savedName = user.full_name || user.display_name || '';
          setFullName(savedName || user.name || '');
          setNeedsProfileName(!savedName);
        }
      } catch {
        // dado corrompido — ignorar
      }
    }
  }, []);

  const handleAuthSuccess = (user) => {
    localStorage.setItem('empatia_user', JSON.stringify(user));
    setUserData(user);
    const savedName = user.full_name || user.display_name || user.preferences?.full_name || user.preferences?.display_name || '';
    setFullName(savedName || user.name || '');
    setNeedsProfileName(user.requires_profile_name ?? !savedName);
    setError('');
  };

  const handleAuthError = () => {
    setError('Erro na autenticação com Google. Tente novamente.');
  };

  const handleComplete = async () => {
    if (!userData || !selectedVoice) return;

    const normalizedFullName = fullName.trim().replace(/\s+/g, ' ');
    if (needsProfileName && normalizedFullName.length < 2) {
      setError('Informe seu nome completo para continuar.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const displayName = normalizedFullName || userData.display_name || userData.name || userData.email;
      const userInfo = {
        id: userData.id,
        email: userData.email,
        name: displayName,
        full_name: normalizedFullName || userData.full_name || displayName,
        display_name: displayName,
        picture: userData.picture,
        username: userData.username || userData.name,
        authMethod: 'google',
      };

      await saveUserPreferences(sessionId, userInfo.username, selectedVoice, true, userInfo);

      onComplete({
        username: userInfo.username,
        voice: selectedVoice,
        voiceEnabled: true,
        displayName,
        userData: userInfo,
      });
    } catch {
      setError('Ocorreu um erro ao salvar suas preferências. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const canProceed = userData && selectedVoice && !isLoading && (!needsProfileName || fullName.trim().length >= 2);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background-light via-background-muted to-background-light dark:from-background-dark dark:via-dark-surface dark:to-background-dark">
      <div className="absolute inset-0 bg-gradient-therapy opacity-5 dark:opacity-10" />

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-6 sm:py-8">
        {/* Header — mais compacto */}
        <div className="text-center mb-5 sm:mb-6 animate-fade-in max-w-lg">
          <div className="mb-4">
            <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-4 avatar-therapy-calm animate-float-gentle">
              <div className="w-full h-full bg-white rounded-full flex items-center justify-center shadow-sm">
                <svg className="w-9 h-9 sm:w-10 sm:h-10 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
          </div>

          <h1 className="text-2xl sm:text-3xl md:text-4xl font-heading font-bold text-text-primary dark:text-text-primary-dark mb-2">
            <span className="text-gradient-therapy">Empat</span>.IA
          </h1>

          <p className="text-sm sm:text-base text-text-secondary dark:text-text-secondary-dark max-w-md mx-auto leading-relaxed px-1">
            Seu companheiro terapêutico baseado na abordagem humanística de Carl Rogers
          </p>
        </div>

        {/* Card Principal */}
        <Card variant="glass" className="w-full max-w-md animate-slide-up">
          <div className="p-5 sm:p-6">

            {/* Etapa 1 — Login Google */}
            {!userData && (
              <div className="flex flex-col gap-4">
                <div className="text-center space-y-1">
                  <h2 className="font-heading font-semibold text-base text-text-primary dark:text-text-primary-dark">
                    Acesso seguro
                  </h2>
                  <p className="text-text-secondary dark:text-text-secondary-dark text-sm leading-snug">
                    Use sua conta Google para entrar
                  </p>
                </div>

                <GoogleAuth
                  onAuthSuccess={handleAuthSuccess}
                  onAuthError={handleAuthError}
                />

                {error && (
                  <p className="text-red-600 text-sm text-center bg-red-50 border border-red-200 p-3 rounded-xl">
                    {error}
                  </p>
                )}
              </div>
            )}

            {/* Etapa 2 — Nome e Seleção de Voz */}
            {userData && (
              <div className="space-y-4">
                <div className="text-center space-y-2">
                  {userData.picture && (
                    <img
                      src={userData.picture}
                      alt={userData.name}
                      className="w-12 h-12 rounded-full mx-auto border-2 border-primary-300"
                    />
                  )}
                  <p className="text-sm font-medium text-text-primary dark:text-text-primary-dark">
                    Olá, {userData.name}!
                  </p>

                  {needsProfileName && (
                    <div className="pt-2 text-left">
                      <label className="block">
                        <span className="mb-2 block text-sm font-medium text-text-primary dark:text-text-primary-dark">
                          Nome completo
                        </span>
                        <input
                          type="text"
                          value={fullName}
                          onChange={event => setFullName(event.target.value)}
                          className="w-full rounded-lg border border-gray-200 bg-white px-3 py-3 text-sm text-gray-900 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
                          placeholder="Seu nome completo"
                          autoComplete="name"
                        />
                      </label>
                    </div>
                  )}

                  <div className="flex items-center justify-center gap-2 text-text-primary dark:text-text-primary-dark pt-2">
                    <svg className="w-5 h-5 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    </svg>
                    <span className="font-heading font-semibold text-lg">Escolha sua voz</span>
                  </div>
                  <p className="text-text-secondary dark:text-text-secondary-dark text-sm">
                    Selecione a voz que mais te faz sentir confortável
                  </p>
                </div>

                <div className="space-y-2">
                  {voiceOptions.map((voice) => (
                    <button
                      key={voice.id}
                      onClick={() => setSelectedVoice(voice.id)}
                      className={`
                        w-full p-3 rounded-lg border transition-all duration-150 text-left
                        ${selectedVoice === voice.id
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-sm'
                          : 'border-gray-200 dark:border-gray-700 hover:border-primary-300 hover:bg-gray-50 dark:hover:border-primary-600 bg-white dark:bg-gray-800 dark:hover:bg-gray-800/80'
                        }
                      `}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xl">{voice.emoji}</span>
                        <div className="flex-1">
                          <h3 className="font-medium text-text-primary dark:text-text-primary-dark">
                            {voice.label}
                          </h3>
                          <p className="text-sm text-text-secondary dark:text-text-secondary-dark">
                            {voice.description}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>

                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
                    {error}
                  </div>
                )}

                <Button
                  onClick={handleComplete}
                  disabled={!canProceed}
                  loading={isLoading}
                  className="w-full"
                  size="lg"
                >
                  {isLoading ? 'Configurando...' : 'Começar'}
                </Button>
              </div>
            )}
          </div>
        </Card>

        {/* Features */}
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4 animate-fade-in">
          <div className="text-center space-y-2">
            <div className="w-12 h-12 mx-auto bg-primary-100 dark:bg-primary-900/30 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="font-medium text-text-primary dark:text-text-primary-dark">Confidencial</h3>
            <p className="text-xs text-text-secondary dark:text-text-secondary-dark">
              Suas conversas são privadas e seguras
            </p>
          </div>

          <div className="text-center space-y-2">
            <div className="w-12 h-12 mx-auto bg-secondary-100 dark:bg-secondary-900/30 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-secondary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
            <h3 className="font-medium text-text-primary dark:text-text-primary-dark">Empático</h3>
            <p className="text-xs text-text-secondary dark:text-text-secondary-dark">
              Baseado na abordagem de Carl Rogers
            </p>
          </div>

          <div className="text-center space-y-2">
            <div className="w-12 h-12 mx-auto bg-accent-100 dark:bg-accent-900/30 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-accent-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="font-medium text-text-primary dark:text-text-primary-dark">Inteligente</h3>
            <p className="text-xs text-text-secondary dark:text-text-secondary-dark">
              IA avançada para seu bem-estar
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;
