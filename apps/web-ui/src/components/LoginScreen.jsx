import React, { useState, useEffect } from 'react';
import { Button, Card, Input, Loading } from './Common';
import { saveUserPreferences, createUser, userLogin } from '../services/api.js';
import GoogleAuth from './GoogleAuth.jsx';

const LoginScreen = ({ onComplete, sessionId }) => {
  const [selectedVoice, setSelectedVoice] = useState('pt-BR-Neural2-B');
  const [error, setError] = useState('');
  const [showAuth, setShowAuth] = useState(false);
  const [userData, setUserData] = useState(null);
  const [manualName, setManualName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Vozes do Google Cloud TTS com interface amigável
  const voiceOptions = [
    {
      id: 'pt-BR-Neural2-B',
      label: 'Voz Masculina Confiante (Recomendada)',
      emoji: '⚡',
      description: 'Tom seguro e profissional'
    },
    {
      id: 'pt-BR-Neural2-A',
      label: 'Voz Feminina Suave',
      emoji: '🌸',
      description: 'Tom suave e acolhedor'
    },
    {
      id: 'pt-BR-Wavenet-A',
      label: 'Voz Feminina Profissional',
      emoji: '💼',
      description: 'Tom claro e objetivo'
    },
    {
      id: 'pt-BR-Wavenet-B',
      label: 'Voz Masculina Amigável',
      emoji: '🎯',
      description: 'Tom caloroso e próximo'
    },
    {
      id: 'pt-BR-Wavenet-C',
      label: 'Voz Feminina Calorosa',
      emoji: '🌺',
      description: 'Tom empático e compreensivo'
    }
  ];

  useEffect(() => {
    const savedUser = localStorage.getItem('empatia_user');
    if (savedUser) {
      try {
        const user = JSON.parse(savedUser);
        setUserData(user);
      } catch (error) {
        console.error('Erro ao carregar dados do usuário:', error);
      }
    }
  }, []);

  const handleAuthSuccess = (user) => {
    setUserData(user);
    setShowAuth(false);
  };

  const handleAuthError = (error) => {
    setError('Erro na autenticação. Tente novamente.');
  };

  const handleComplete = async () => {
    if (!userData || !userData.name || !selectedVoice) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      const userInfo = {
        id: userData.id,
        email: userData.email,
        name: userData.name,
        picture: userData.picture,
        authMethod: 'google'
      };
      
      if (userData.authMethod === 'google') {
        try {
          await createUser(userData.name, userData.email, {
            selected_voice: selectedVoice,
            voice_enabled: true,
            theme: 'dark',
            language: 'pt-BR'
          });
        } catch {}
      }
      
      await saveUserPreferences(sessionId, userData.name, selectedVoice, true, userInfo);
      
      onComplete({ 
        username: userData.name, 
        voice: selectedVoice, 
        voiceEnabled: true,
        userData: userInfo
      });
    } catch {
      setError('Ocorreu um erro ao salvar suas preferências. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleContinueWithoutLogin = async () => {
    if (!manualName.trim() || !selectedVoice) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      try {
        await createUser(manualName, null, {
          selected_voice: selectedVoice,
          voice_enabled: true,
          theme: 'dark',
          language: 'pt-BR'
        });
      } catch {}
      
      // Registrar login para clonar sessões terapêuticas
      await userLogin(manualName);
      
      await saveUserPreferences(sessionId, manualName, selectedVoice, true, { authMethod: 'manual' });
      
      onComplete({ 
        username: manualName, 
        voice: selectedVoice, 
        voiceEnabled: true,
        userData: { name: manualName, authMethod: 'manual' }
      });
    } catch {
      setError('Ocorreu um erro ao salvar suas preferências. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const canProceed = userData && userData.name && !isLoading;

  return (
    <div className="min-h-screen bg-gradient-to-br from-background-light via-background-muted to-background-light dark:from-background-dark dark:via-dark-surface dark:to-background-dark">
      {/* Background com gradiente suave */}
      <div className="absolute inset-0 bg-gradient-therapy opacity-5 dark:opacity-10"></div>
      
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="mb-6">
            <div className="w-20 h-20 mx-auto mb-6 avatar-therapy-calm animate-float-gentle">
              <div className="w-full h-full bg-white rounded-full flex items-center justify-center">
                <svg className="w-10 h-10 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
          </div>
          
          <h1 className="text-3xl md:text-4xl font-heading font-bold text-text-primary dark:text-text-primary-dark mb-4">
            <span className="text-gradient-therapy">Empath</span>.IA
          </h1>
          
          <p className="text-lg text-text-secondary dark:text-text-secondary-dark max-w-md mx-auto reading-spacing">
            Seu companheiro terapêutico baseado na abordagem humanística de Carl Rogers
          </p>
        </div>

        {/* Card Principal */}
        <Card variant="glass" className="w-full max-w-md animate-slide-up">
          <div className="p-6 space-y-6">
            {/* Seção de Autenticação */}
            {!userData && (
              <div className="text-center space-y-4">
                <div className="flex items-center justify-center gap-2 text-text-primary dark:text-text-primary-dark">
                  <svg className="w-5 h-5 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  <span className="font-heading font-semibold text-lg">Identificação</span>
                </div>
                
                <p className="text-text-secondary dark:text-text-secondary-dark text-sm">
                  Digite seu nome ou faça login para personalizar sua experiência
                </p>
                
                <div className="space-y-3">
                  <Input
                    type="text"
                    placeholder="Digite seu nome para continuar"
                    value={manualName}
                    onChange={e => setManualName(e.target.value)}
                    disabled={isLoading}
                    aria-label="Nome do usuário"
                  />
                  
                  <Button
                    onClick={handleContinueWithoutLogin}
                    disabled={!manualName.trim() || isLoading}
                    loading={isLoading}
                    className="w-full"
                    size="lg"
                  >
                    Continuar sem login
                  </Button>
                  
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-white dark:bg-gray-800 px-2 text-text-secondary dark:text-text-secondary-dark">ou</span>
                    </div>
                  </div>
                  
                  <Button
                    onClick={() => setShowAuth(true)}
                    variant="outline"
                    className="w-full"
                    size="lg"
                  >
                    <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Entrar com Google
                  </Button>
                </div>
              </div>
            )}

            {/* Seção de Seleção de Voz */}
            {userData && (
              <div className="space-y-4">
                <div className="text-center space-y-2">
                  <div className="flex items-center justify-center gap-2 text-text-primary dark:text-text-primary-dark">
                    <svg className="w-5 h-5 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
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
                        w-full p-3 rounded-xl border-2 transition-all duration-200 text-left hover:scale-102
                        ${selectedVoice === voice.id
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-therapy-medium'
                          : 'border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 bg-white dark:bg-gray-800'
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
                  {isLoading ? 'Configurando...' : 'Começar minha jornada'}
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="font-medium text-text-primary dark:text-text-primary-dark">Inteligente</h3>
            <p className="text-xs text-text-secondary dark:text-text-secondary-dark">
              IA avançada para seu bem-estar
            </p>
          </div>
        </div>

        {/* Autenticação Google */}
        {showAuth && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card variant="glass" className="w-full max-w-md">
              <GoogleAuth
                onSuccess={handleAuthSuccess}
                onError={handleAuthError}
                onCancel={() => setShowAuth(false)}
              />
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginScreen; 