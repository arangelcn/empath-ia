import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  Settings, 
  LogOut, 
  RefreshCw,
  TrendingUp,
  Target
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getSessions, getUserSessions, getUserProgress, startUserSession } from '../../services/api.js';
import SessionCard from './SessionCard';
import ProgressBar from './ProgressBar';

const HomeScreen = ({ username, onLogout }) => {
  
  const [sessions, setSessions] = useState([]);
  const [userSessions, setUserSessions] = useState([]);
  const [userProgress, setUserProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [startingSession, setStartingSession] = useState(null);
  const navigate = useNavigate();

  // Limpar erro após 5 segundos
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const loadSessions = async () => {
    try {
      setLoading(true);
      setError(null);

      // Buscar templates (TherapeuticSessions)
      const templatesResponse = await getSessions();
      const templateSessions = templatesResponse.data?.sessions || [];

      // Buscar UserSessions
      const userSessionsResponse = await getUserSessions(username);
      const userSessionsData = userSessionsResponse.data?.sessions || [];

      setSessions(templateSessions); // sessions = templates
      setUserSessions(userSessionsData); // userSessions = progresso/status

      // Progresso geral
      const progressResponse = await getUserProgress(username);
      const progressData = progressResponse.data;
      setUserProgress(progressData);
    } catch (err) {
      console.error('Erro ao carregar sessões:', err);
      setError('Erro ao carregar sessões. ' + (err?.message || 'Tente novamente.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (username) {
      loadSessions();
    } else {
      setError('Username não fornecido');
      setLoading(false);
    }
  }, [username]);

  const handleSessionSelect = async (session) => {
    try {
      // Indica que está iniciando esta sessão
      setStartingSession(session.session_id);
      
      // Buscar a sessão do usuário correspondente
      const userSession = userSessions.find(us => us.session_id === session.session_id);
      
      if (!userSession) {
        console.error('Sessão do usuário não encontrada');
        setError('Sessão não encontrada. Tente recarregar a página.');
        return;
      }

      // Verificar se a sessão está desbloqueada
      if (userSession.status === 'locked') {
        setError('Esta sessão ainda está bloqueada. Complete as sessões anteriores primeiro.');
        return;
      }

      // Se a sessão está desbloqueada mas não foi iniciada, marcar como iniciada
      if (userSession.status === 'unlocked') {
        try {
          const startResult = await startUserSession(username, session.session_id);
          if (startResult.success) {
            // Atualizar a lista de sessões para refletir o novo status
            await loadSessions();
          }
        } catch (error) {
          console.error('Erro ao iniciar sessão:', error);
          setError('Erro ao marcar sessão como iniciada. Continuando para o chat...');
          // Continua para o chat mesmo se falhar ao marcar como iniciada
        }
      }

      // Navegar para o chat com a sessão
      navigate(`/chat/${session.session_id}`, { 
        state: { 
          username,
          sessionTitle: session.title,
          userSession: {
            ...userSession,
            status: userSession.status === 'unlocked' ? 'in_progress' : userSession.status
          }
        } 
      });

    } catch (err) {
      console.error('Erro ao selecionar sessão:', err);
      setError('Erro ao iniciar sessão. Tente novamente.');
    } finally {
      setStartingSession(null);
    }
  };

  const isSessionUnlocked = (sessionId) => {
    const userSession = userSessions.find(us => us.session_id === sessionId);
    const unlocked = userSession?.status === 'unlocked' || userSession?.status === 'in_progress';
    return unlocked;
  };

  const isSessionCompleted = (sessionId) => {
    const userSession = userSessions.find(us => us.session_id === sessionId);
    return userSession?.status === 'completed';
  };

  const isSessionCurrent = (sessionId) => {
    const userSession = userSessions.find(us => us.session_id === sessionId);
    return userSession?.status === 'in_progress';
  };



  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-serenity-50 via-white to-turquoise-50 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="w-16 h-16 border-4 border-serenity-200 border-t-serenity-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Carregando sua jornada terapêutica...</p>
        </motion.div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-serenity-50 via-white to-turquoise-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadSessions}
            className="px-4 py-2 bg-serenity-500 text-white rounded-lg hover:bg-serenity-600 transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-serenity-50 via-white to-turquoise-50">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="bg-white shadow-sm border-b border-gray-100"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-serenity-500 to-turquoise-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900 font-manrope">
                Empath.IA
              </h1>
            </div>
            
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/settings')}
                className="p-2 text-gray-500 hover:text-serenity-600 transition-colors"
              >
                <Settings className="w-5 h-5" />
              </button>
              
              <button
                onClick={onLogout}
                className="p-2 text-gray-500 hover:text-red-600 transition-colors"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Conteúdo Principal */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {/* Progresso Geral */}
          {userProgress && (
            <div className="mb-8">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-serenity-500 to-turquoise-500 rounded-lg flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900 font-manrope">
                        Seu Progresso
                      </h2>
                      <p className="text-gray-600 text-sm">
                        Continue sua jornada de autoconhecimento
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-2xl font-bold text-serenity-600">
                      {userProgress.overall_progress}%
                    </div>
                    <div className="text-sm text-gray-500">
                      Progresso Geral
                    </div>
                  </div>
                </div>
                
                <ProgressBar 
                  progress={userProgress.overall_progress} 
                  className="mb-4"
                />
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-lg font-bold text-serenity-600">
                      {userProgress.completed_sessions}
                    </div>
                    <div className="text-xs text-gray-500">Concluídas</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-orange-600">
                      {userProgress.in_progress_sessions}
                    </div>
                    <div className="text-xs text-gray-500">Em Andamento</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-blue-600">
                      {userProgress.unlocked_sessions}
                    </div>
                    <div className="text-xs text-gray-500">Disponíveis</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-gray-400">
                      {userProgress.locked_sessions}
                    </div>
                    <div className="text-xs text-gray-500">Bloqueadas</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Timeline de Sessões */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            {/* Header da timeline */}
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 font-manrope mb-2">
                  Sua Jornada Terapêutica
                </h2>
                <p className="text-gray-600">
                  Explore as sessões disponíveis e continue seu desenvolvimento pessoal
                </p>
              </div>
              
              <button
                onClick={loadSessions}
                className="p-2 text-gray-500 hover:text-serenity-600 transition-colors"
                title="Atualizar sessões"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>

            {/* Exibir erro se existir */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg"
              >
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs font-bold">!</span>
                  </div>
                  <p className="text-red-700 text-sm font-medium">{error}</p>
                </div>
              </motion.div>
            )}

            {/* Timeline de sessões */}
            <div className="relative">
              {/* Linha da timeline */}
              <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-serenity-200 to-turquoise-200"></div>
              
              {/* Sessões ordenadas por nome */}
              {sessions
                .sort((a, b) => a.title.localeCompare(b.title))
                .map((template, index) => {
                  const userSession = userSessions.find(us => us.session_id === template.session_id);
                  const isUnlocked = userSession?.status === 'unlocked' || userSession?.status === 'in_progress';
                  const isCompleted = userSession?.status === 'completed';
                  const isCurrent = userSession?.status === 'in_progress';
                  
                  return (
                    <motion.div
                      key={template.session_id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="relative mb-8 last:mb-0"
                    >
                      {/* Ponto da timeline */}
                      <div className="absolute left-6 top-6 w-4 h-4 rounded-full border-2 border-white shadow-sm z-10">
                        {isCompleted ? (
                          <div className="w-full h-full bg-serenity-500 rounded-full flex items-center justify-center">
                            <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </div>
                        ) : isCurrent ? (
                          <div className="w-full h-full bg-orange-500 rounded-full flex items-center justify-center">
                            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                          </div>
                        ) : isUnlocked ? (
                          <div className="w-full h-full bg-blue-500 rounded-full"></div>
                        ) : (
                          <div className="w-full h-full bg-gray-300 rounded-full"></div>
                        )}
                      </div>

                      {/* Card da sessão */}
                      <div className="ml-16">
                        <div className={`
                          bg-white rounded-xl border-2 p-6 shadow-sm transition-all duration-300 hover:shadow-md
                          ${isCompleted ? 'border-serenity-200 bg-serenity-50' : 
                            isCurrent ? 'border-orange-200 bg-orange-50' :
                            isUnlocked ? 'border-blue-200 bg-blue-50 cursor-pointer hover:border-blue-300' : 
                            'border-gray-200 bg-gray-50'}
                        `}
                        onClick={() => isUnlocked && handleSessionSelect(template)}
                        >
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <h3 className="text-lg font-bold text-gray-900 font-manrope">
                                  {template.title}
                                </h3>
                                {isCompleted && (
                                  <span className="px-2 py-1 bg-serenity-100 text-serenity-700 text-xs font-medium rounded-full">
                                    Concluída
                                  </span>
                                )}
                                {isCurrent && (
                                  <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs font-medium rounded-full">
                                    Em Andamento
                                  </span>
                                )}
                                {!isUnlocked && !isCompleted && !isCurrent && (
                                  <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">
                                    Bloqueada
                                  </span>
                                )}
                              </div>
                              
                              <p className="text-gray-600 text-sm mb-4">
                                {template.description}
                              </p>

                              {/* Duração estimada */}
                              <div className="flex items-center gap-2 text-xs text-gray-500">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span>{template.estimated_duration || '15-20 min'}</span>
                              </div>
                            </div>

                            {/* Botão de ação */}
                            <div className="ml-4 flex flex-col items-end gap-2">
                              {isUnlocked ? (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleSessionSelect(template);
                                  }}
                                  disabled={startingSession === template.session_id}
                                  className={`
                                    px-6 py-3 rounded-xl font-bold text-sm transition-all duration-200 flex items-center gap-2 shadow-md hover:shadow-lg
                                    ${isCurrent ? 
                                      'bg-orange-500 hover:bg-orange-600 text-white hover:scale-105' :
                                      'bg-serenity-500 hover:bg-serenity-600 text-white hover:scale-105'
                                    }
                                    ${startingSession === template.session_id ? 'opacity-70 cursor-not-allowed' : ''}
                                  `}
                                >
                                  {startingSession === template.session_id ? (
                                    <>
                                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                      Iniciando...
                                    </>
                                  ) : (
                                    <>{isCurrent ? 'Continuar' : 'Iniciar'}</>
                                  )}
                                </button>
                              ) : (
                                <button
                                  disabled
                                  className="px-6 py-3 bg-gray-300 text-gray-500 rounded-xl font-bold text-sm cursor-not-allowed opacity-60"
                                >
                                  Bloqueada
                                </button>
                              )}
                              
                              {/* Indicador visual para sessão disponível */}
                              {isUnlocked && !isCurrent && !isCompleted && (
                                <div className="text-xs text-blue-600 font-medium animate-pulse">
                                  ✨ Disponível para iniciar
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}

              {/* Mensagem quando não há sessões */}
              {sessions.length === 0 && (
                <div className="text-center py-12">
                  <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Nenhuma sessão disponível
                  </h3>
                  <p className="text-gray-500">
                    As sessões terapêuticas serão carregadas em breve.
                  </p>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default HomeScreen; 