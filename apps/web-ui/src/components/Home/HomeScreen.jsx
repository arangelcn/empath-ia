import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  Settings, 
  LogOut, 
  RefreshCw,
  TrendingUp,
  Target,
  CheckCircle,
  Eye
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getUserSessions, getUserProgress, startUserSession } from '../../services/api.js';
import SessionCard from './SessionCard';
import ProgressBar from './ProgressBar';

const HomeScreen = ({ username, onLogout }) => {
  
  const [userSessions, setUserSessions] = useState([]);
  const [userProgress, setUserProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [startingSession, setStartingSession] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  // ✅ NOVO: Detectar se voltou de uma sessão finalizada
  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      
      // Limpar mensagem após 8 segundos
      setTimeout(() => {
        setSuccessMessage(null);
      }, 8000);
      
      // ✅ IMPORTANTE: Recarregar sessões quando volta de sessão finalizada
      if (username) {
        console.log('🔄 Recarregando sessões após retorno de sessão finalizada...');
        loadSessions();
      }
      
      // Limpar o state da navegação
      navigate(location.pathname, { replace: true });
    }
  }, [location.state, username]);

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

      console.log(`🔄 Carregando sessões para usuário: ${username}`);

      // ✅ NOVA LÓGICA: Buscar apenas user_therapeutic_sessions
      // Agora cada usuário tem suas próprias sessões personalizadas
      const userSessionsResponse = await getUserSessions(username);
      const userSessionsData = userSessionsResponse.data?.sessions || [];

      console.log(`✅ ${userSessionsData.length} sessões carregadas:`, userSessionsData.map(s => ({
        id: s.session_id,
        title: s.title,
        status: s.status
      })));

      setUserSessions(userSessionsData);

      // Progresso geral
      const progressResponse = await getUserProgress(username);
      const progressData = progressResponse.data;
      setUserProgress(progressData);
      
      console.log(`📊 Progresso do usuário:`, progressData);
    } catch (err) {
      console.error('❌ Erro ao carregar sessões:', err);
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
      
      console.log(`🎯 Selecionando sessão:`, {
        sessionId: session.session_id,
        title: session.title,
        status: session.status
      });

      // ✅ SIMPLIFICADO: session já contém todas as informações necessárias
      // Verificar se a sessão está desbloqueada
      if (session.status === 'locked') {
        setError('Esta sessão ainda está bloqueada. Complete as sessões anteriores primeiro.');
        return;
      }

      // Se a sessão está desbloqueada mas não foi iniciada, marcar como iniciada
      if (session.status === 'unlocked') {
        try {
          console.log(`🚀 Marcando sessão ${session.session_id} como iniciada...`);
          const startResult = await startUserSession(username, session.session_id);
          if (startResult.success) {
            // Atualizar a lista de sessões para refletir o novo status
            await loadSessions();
          }
        } catch (error) {
          console.error('⚠️ Erro ao iniciar sessão:', error);
          setError('Erro ao marcar sessão como iniciada. Continuando para o chat...');
          // Continua para o chat mesmo se falhar ao marcar como iniciada
        }
      }

      // 🔒 Criar session_id único por usuário
      // Combinando username com session_id para garantir isolamento total
      const uniqueSessionId = `${username}_${session.session_id}`;

      console.log(`🔗 Navegando para chat com ID único: ${uniqueSessionId}`);

      // Navegar para o chat com a sessão usando ID único
      navigate(`/chat/${uniqueSessionId}`, { 
        state: { 
          username,
          sessionTitle: session.title,
          originalSessionId: session.session_id, // Manter referência original
          userSession: {
            ...session,
            status: session.status === 'unlocked' ? 'in_progress' : session.status
          }
        } 
      });

    } catch (err) {
      console.error('❌ Erro ao selecionar sessão:', err);
      setError('Erro ao iniciar sessão. Tente novamente.');
    } finally {
      setStartingSession(null);
    }
  };

  // ✅ SIMPLIFICADAS: Funções agora trabalham diretamente com userSessions
  const isSessionUnlocked = (session) => {
    return session?.status === 'unlocked' || session?.status === 'in_progress';
  };

  const isSessionCompleted = (session) => {
    return session?.status === 'completed';
  };

  const isSessionCurrent = (session) => {
    return session?.status === 'in_progress';
  };



  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Carregando sua jornada terapêutica...</p>
        </motion.div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadSessions}
            className="px-6 py-4 md:px-4 md:py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors min-h-[52px] md:min-h-[44px] text-base md:text-sm font-medium"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50">
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
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900 font-manrope">
                Empat.IA
              </h1>
            </div>
            
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/settings')}
                className="p-3 md:p-2 text-gray-500 hover:text-primary-600 transition-colors min-h-[44px] flex items-center justify-center"
              >
                <Settings className="w-6 h-6 md:w-5 md:h-5" />
              </button>
              
              <button
                onClick={onLogout}
                className="p-3 md:p-2 text-gray-500 hover:text-red-600 transition-colors min-h-[44px] flex items-center justify-center"
              >
                <LogOut className="w-6 h-6 md:w-5 md:h-5" />
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
                    <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
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
                    <div className="text-2xl font-bold text-primary-600">
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
                    <div className="text-lg font-bold text-green-600">
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
                className="p-3 md:p-2 text-gray-500 hover:text-primary-600 transition-colors min-h-[44px] flex items-center justify-center"
                title="Atualizar sessões"
              >
                <RefreshCw className="w-6 h-6 md:w-5 md:h-5" />
              </button>
            </div>

            {/* Exibir mensagem de sucesso se existir */}
            {successMessage && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg"
              >
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                    <CheckCircle className="w-3 h-3 text-white" />
                  </div>
                  <p className="text-green-700 text-sm font-medium">{successMessage}</p>
                </div>
              </motion.div>
            )}

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
              <div className="absolute left-6 sm:left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary-200 to-secondary-200"></div>
              
              {/* Sessões ordenadas por nome */}
              {userSessions
                .sort((a, b) => a.title.localeCompare(b.title))
                .map((session, index) => {
                  const isUnlocked = isSessionUnlocked(session);
                  const isCompleted = isSessionCompleted(session);
                  const isCurrent = isSessionCurrent(session);
                  
                  return (
                    <motion.div
                      key={session.session_id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="relative mb-8 last:mb-0"
                    >
                      {/* Ponto da timeline */}
                      <div className="absolute left-3 sm:left-5 top-6 w-6 h-6 rounded-full border-2 border-white shadow-sm z-10">
                        {isCompleted ? (
                          <div className="w-full h-full bg-green-500 rounded-full flex items-center justify-center">
                            <CheckCircle className="w-8 h-8 text-white -m-1" />
                          </div>
                        ) : isCurrent ? (
                          <div className="w-full h-full bg-orange-500 rounded-full flex items-center justify-center">
                            <div className="w-2.5 h-2.5 bg-white rounded-full animate-pulse"></div>
                          </div>
                        ) : isUnlocked ? (
                          <div className="w-full h-full bg-blue-500 rounded-full"></div>
                        ) : (
                          <div className="w-full h-full bg-gray-300 rounded-full"></div>
                        )}
                      </div>

                      {/* Card da sessão */}
                      <div className="ml-12 sm:ml-16">
                        <div className={`
                          bg-white rounded-xl border-2 p-4 sm:p-6 shadow-sm transition-all duration-300 hover:shadow-md
                          ${isCompleted ? 'border-green-200 bg-green-50' : 
                            isCurrent ? 'border-orange-200 bg-orange-50' :
                            isUnlocked ? 'border-blue-200 bg-blue-50 cursor-pointer hover:border-blue-300' : 
                            'border-gray-200 bg-gray-50'}
                        `}
                        onClick={() => (isUnlocked || isCompleted) && handleSessionSelect(session)}
                        >
                          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-4">
                            <div className="flex-1 mb-4 sm:mb-0">
                              <div className="flex items-center gap-3 mb-2">
                                <h3 className="text-lg font-bold text-gray-900 font-manrope">
                                  {session.title}
                                </h3>
                                {isCompleted && (
                                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
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
                                {session.description}
                              </p>

                              {/* Duração estimada */}
                              <div className="flex items-center gap-2 text-xs text-gray-500">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span>{session.estimated_duration || '15-20 min'}</span>
                              </div>
                            </div>

                            {/* Botão de ação */}
                            <div className="sm:ml-4 flex flex-col sm:items-end gap-2 w-full sm:w-auto">
                              {isCompleted ? (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleSessionSelect(session);
                                  }}
                                  className="px-6 py-3 md:px-6 md:py-3 rounded-xl font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-md hover:shadow-lg bg-green-500 hover:bg-green-600 text-white hover:scale-105 min-h-[48px] w-full sm:w-auto"
                                >
                                  <Eye className="w-4 h-4" />
                                  <span className="sm:hidden">Ver conversa</span>
                                  <span className="hidden sm:inline">Visualizar conversa</span>
                                </button>
                              ) : isUnlocked ? (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleSessionSelect(session);
                                  }}
                                  disabled={startingSession === session.session_id}
                                  className={`
                                    px-6 py-3 rounded-xl font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-md hover:shadow-lg text-white hover:scale-105 min-h-[48px] w-full sm:w-auto
                                    ${isCurrent ? 
                                      'bg-orange-500 hover:bg-orange-600' :
                                      'bg-blue-500 hover:bg-blue-600'
                                    }
                                    ${startingSession === session.session_id ? 'opacity-70 cursor-not-allowed' : ''}
                                  `}
                                >
                                  {startingSession === session.session_id ? (
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
                                  className="px-6 py-3 bg-gray-300 text-gray-600 rounded-xl font-bold text-sm cursor-not-allowed opacity-60 min-h-[48px] w-full sm:w-auto"
                                >
                                  Bloqueada
                                </button>
                              )}
                              
                              {/* Indicador visual para sessão disponível */}
                              {isUnlocked && !isCurrent && !isCompleted && (
                                <div className="text-xs text-blue-600 font-medium animate-pulse text-center sm:text-right">
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
              {userSessions.length === 0 && (
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