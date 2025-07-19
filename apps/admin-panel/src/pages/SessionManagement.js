import React, { useState, useEffect } from 'react';
import {
  AcademicCapIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  CalendarIcon,
  UserIcon,
  ChartBarIcon,
  ClockIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  FunnelIcon,
  CheckCircleIcon,
  XCircleIcon,
  PlayCircleIcon,
  LockClosedIcon,
  ChatBubbleLeftRightIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import apiService from '../services/api';

const SessionManagement = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [selectedSession, setSelectedSession] = useState(null);
  const [showSessionDetails, setShowSessionDetails] = useState(false);
  const [selectedContext, setSelectedContext] = useState(null);
  const [showContextDetails, setShowContextDetails] = useState(false);
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 50,
    offset: 0,
    hasNext: false
  });

  // Carregar todas as sessões dos usuários
  const loadSessions = async (params = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      // Preparar parâmetros da API evitando valores undefined
      const apiParams = {
        limit: pagination.limit,
        offset: pagination.offset,
        ...params
      };

      // Só adicionar search se tiver valor válido
      if (searchTerm && searchTerm.trim() && searchTerm !== 'undefined') {
        apiParams.search = searchTerm.trim();
      }

      // Só adicionar status se não for 'all' e tiver valor válido
      if (filterStatus && filterStatus !== 'all' && filterStatus !== 'undefined') {
        apiParams.status = filterStatus;
      }

      // Só adicionar personalized se tiver valor válido
      if (filterType && filterType !== 'all' && filterType !== 'undefined') {
        if (filterType === 'personalized') {
          apiParams.personalized = true;
        } else if (filterType === 'template') {
          apiParams.personalized = false;
        }
      }

      console.log('Chamando API de sessões com parâmetros:', apiParams);
      
      // Usar o novo endpoint administrativo que já inclui os contextos
      const response = await apiService.getAllUserSessionsWithContexts(apiParams);

      console.log('Resposta da API de sessões:', response);

      if (response.success) {
        setSessions(response.data.sessions || []);
        setPagination(prev => ({
          ...prev,
          total: response.data.pagination?.total || 0,
          hasNext: response.data.pagination?.has_next || false
        }));
      } else {
        throw new Error('Falha ao carregar sessões');
      }
    } catch (err) {
      console.error('Erro ao carregar sessões:', err);
      setError('Erro ao carregar sessões. Verifique a conexão com o servidor.');
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  // Carregar detalhes da sessão com contexto
  const loadSessionDetails = async (username, sessionId) => {
    try {
      const [sessionResponse, contextResponse] = await Promise.all([
        apiService.getUserSessionDetails(username, sessionId),
        apiService.getSessionContext(`${username}_${sessionId}`).catch(() => null)
      ]);

      const sessionDetails = {
        ...sessionResponse.data,
        context: contextResponse?.data || null
      };

      setSelectedSession(sessionDetails);
      setShowSessionDetails(true);
    } catch (err) {
      console.error('Erro ao carregar detalhes da sessão:', err);
      alert('Erro ao carregar detalhes da sessão');
    }
  };

  // Carregar e exibir contexto completo
  const loadContextDetails = (session) => {
    if (session.has_context && session.context) {
      setSelectedContext({
        session_id: `${session.username}_${session.session_id}`,
        username: session.username,
        session_title: session.title,
        context: session.context,
        context_created_at: session.context_created_at
      });
      setShowContextDetails(true);
    }
  };

  // Efeitos
  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      // Aplicar filtros locais
    }, 500);

    return () => clearTimeout(delayedSearch);
  }, [searchTerm, filterStatus, filterType]);

  // Filtros locais
  const filteredSessions = sessions.filter(session => {
    const matchesSearch = !searchTerm || 
      session.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      session.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      session.session_id?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === 'all' || session.status === filterStatus;
    
    const matchesType = filterType === 'all' || 
      (filterType === 'personalized' && session.personalized) ||
      (filterType === 'template' && !session.personalized);
    
    return matchesSearch && matchesStatus && matchesType;
  });

  const getStatusBadge = (status) => {
    const statusConfig = {
      completed: { 
        icon: CheckCircleIcon, 
        bg: 'bg-green-100', 
        text: 'text-green-800', 
        label: 'Completada' 
      },
      in_progress: { 
        icon: PlayCircleIcon, 
        bg: 'bg-blue-100', 
        text: 'text-blue-800', 
        label: 'Em Progresso' 
      },
      unlocked: { 
        icon: PlayCircleIcon, 
        bg: 'bg-yellow-100', 
        text: 'text-yellow-800', 
        label: 'Disponível' 
      },
      locked: { 
        icon: LockClosedIcon, 
        bg: 'bg-gray-100', 
        text: 'text-gray-800', 
        label: 'Bloqueada' 
      }
    };
    
    const config = statusConfig[status] || statusConfig.locked;
    const IconComponent = config.icon;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        <IconComponent className="w-3 h-3 mr-1" />
        {config.label}
      </span>
    );
  };

  const getTypeBadge = (personalized) => {
    if (personalized) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
          Personalizada
        </span>
      );
    }
    
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
        Template
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Não definido';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading && sessions.length === 0) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2">
            <ArrowPathIcon className="w-5 h-5 animate-spin text-primary-600" />
            <span className="text-gray-600">Carregando sessões...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <AcademicCapIcon className="w-8 h-8 mr-3 text-primary-600" />
              Gerenciamento de Sessões
            </h1>
            <p className="text-gray-600 mt-1">
              Visualize e gerencie todas as sessões terapêuticas dos usuários
            </p>
          </div>
          <button 
            onClick={() => loadSessions()}
            className="btn-secondary flex items-center"
            disabled={loading}
          >
            <ArrowPathIcon className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </div>
      </div>

      {/* Estatísticas Rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <AcademicCapIcon className="w-8 h-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total de Sessões</p>
              <p className="text-2xl font-bold text-gray-900">{filteredSessions.length}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="w-8 h-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Completadas</p>
              <p className="text-2xl font-bold text-gray-900">
                {filteredSessions.filter(s => s.status === 'completed').length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <PlayCircleIcon className="w-8 h-8 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Em Progresso</p>
              <p className="text-2xl font-bold text-gray-900">
                {filteredSessions.filter(s => s.status === 'in_progress' || s.status === 'unlocked').length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="w-8 h-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Personalizadas</p>
              <p className="text-2xl font-bold text-gray-900">
                {filteredSessions.filter(s => s.personalized).length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChatBubbleLeftRightIcon className="w-8 h-8 text-emerald-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Com Contexto</p>
              <p className="text-2xl font-bold text-gray-900">
                {filteredSessions.filter(s => s.has_context).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filtros e Busca */}
      <div className="card mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por título, usuário ou ID da sessão..."
                className="input pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className="flex gap-3">
            <select
              className="input"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">Todos os Status</option>
              <option value="completed">Completadas</option>
              <option value="in_progress">Em Progresso</option>
              <option value="unlocked">Disponíveis</option>
              <option value="locked">Bloqueadas</option>
            </select>
            <select
              className="input"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="all">Todos os Tipos</option>
              <option value="personalized">Personalizadas</option>
              <option value="template">Templates</option>
            </select>
          </div>
        </div>
      </div>

      {/* Mensagem de Erro */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <p className="text-red-800">{error}</p>
          <button 
            onClick={() => loadSessions()} 
            className="mt-2 text-red-600 hover:text-red-800 underline"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* Lista de Sessões */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sessão
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usuário
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Progresso
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contexto
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Criada em
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredSessions.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-12 text-center">
                    <div className="text-gray-500">
                      <AcademicCapIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p className="text-lg font-medium">Nenhuma sessão encontrada</p>
                      <p className="mt-1">
                        {searchTerm ? 
                          'Tente ajustar os filtros de busca.' : 
                          'Não há sessões cadastradas no sistema.'
                        }
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredSessions.map((session) => (
                  <tr key={`${session.username}_${session.session_id}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-8 w-8">
                          <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                            <AcademicCapIcon className="h-4 w-4 text-primary-600" />
                          </div>
                        </div>
                        <div className="ml-3">
                          <div className="text-sm font-medium text-gray-900">
                            {session.title || session.session_id}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {session.session_id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <UserIcon className="h-4 w-4 text-gray-400 mr-2" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {session.username}
                          </div>
                          <div className="text-sm text-gray-500">
                            {session.user_email || 'Sem email'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(session.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getTypeBadge(session.personalized)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div 
                            className="bg-primary-600 h-2 rounded-full" 
                            style={{ width: `${session.progress || 0}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-900">
                          {session.progress || 0}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {session.has_context ? (
                          <button
                            onClick={() => loadContextDetails(session)}
                            className="flex items-center text-green-600 hover:text-green-800 hover:bg-green-50 px-2 py-1 rounded-md transition-colors cursor-pointer"
                            title="Clique para ver o contexto completo"
                          >
                            <ChatBubbleLeftRightIcon className="w-4 h-4 mr-1" />
                            <span className="text-xs font-medium">Ver Contexto</span>
                          </button>
                        ) : (
                          <div className="flex items-center text-gray-400">
                            <XCircleIcon className="w-4 h-4 mr-1" />
                            <span className="text-xs">Sem contexto</span>
                          </div>
                        )}
                      </div>
                      {session.has_context && session.context && (
                        <div className="mt-1">
                          <div className="text-xs text-gray-500 truncate max-w-xs">
                            {session.context.summary || 'Contexto estruturado disponível'}
                          </div>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(session.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <button 
                          onClick={() => loadSessionDetails(session.username, session.session_id)}
                          className="text-primary-600 hover:text-primary-900"
                          title="Ver detalhes"
                        >
                          <EyeIcon className="w-4 h-4" />
                        </button>
                        <button 
                          className="text-green-600 hover:text-green-900"
                          title="Ver contexto"
                        >
                          <DocumentTextIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de Detalhes da Sessão */}
      {showSessionDetails && selectedSession && (
        <SessionDetailsModal 
          session={selectedSession} 
          onClose={() => {
            setShowSessionDetails(false);
            setSelectedSession(null);
          }}
        />
      )}

      {/* Modal de Detalhes do Contexto */}
      {showContextDetails && selectedContext && (
        <ContextDetailsModal 
          contextData={selectedContext} 
          onClose={() => {
            setShowContextDetails(false);
            setSelectedContext(null);
          }}
        />
      )}
    </div>
  );
};

// Componente Modal para Detalhes do Contexto
function ContextDetailsModal({ contextData, onClose }) {
  const formatContextValue = (value) => {
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return value?.toString() || 'Não especificado';
  };

  const renderContextSection = (title, content, bgColor = 'bg-blue-50', borderColor = 'border-blue-200', textColor = 'text-blue-900') => {
    if (!content) return null;

    return (
      <div className="mb-6">
        <h4 className={`text-md font-medium ${textColor} mb-3 flex items-center`}>
          <SparklesIcon className="w-5 h-5 mr-2" />
          {title}
        </h4>
        <div className={`${bgColor} p-4 rounded-md border ${borderColor}`}>
          {typeof content === 'object' && !Array.isArray(content) ? (
            <div className="space-y-3">
              {Object.entries(content).map(([key, value]) => (
                <div key={key}>
                  <dt className={`text-sm font-medium ${textColor} capitalize`}>
                    {key.replace(/_/g, ' ')}:
                  </dt>
                  <dd className={`text-sm ${textColor.replace('900', '800')} mt-1`}>
                    {formatContextValue(value)}
                  </dd>
                </div>
              ))}
            </div>
          ) : Array.isArray(content) ? (
            <ul className={`text-sm ${textColor.replace('900', '800')} space-y-1`}>
              {content.map((item, index) => (
                <li key={index} className="flex items-start">
                  <span className="w-1.5 h-1.5 bg-current rounded-full mt-2 mr-2 flex-shrink-0"></span>
                  {formatContextValue(item)}
                </li>
              ))}
            </ul>
          ) : (
            <p className={`text-sm ${textColor.replace('900', '800')}`}>
              {formatContextValue(content)}
            </p>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-6 border w-11/12 md:w-4/5 lg:w-3/4 xl:w-2/3 shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-900 flex items-center">
              <ChatBubbleLeftRightIcon className="w-6 h-6 mr-3 text-green-600" />
              Contexto da Sessão
            </h3>
            <p className="text-gray-600 mt-1">
              {contextData.session_title} - {contextData.username}
            </p>
            <p className="text-sm text-gray-500">
              ID: {contextData.session_id}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            <span className="sr-only">Fechar</span>
            ✕
          </button>
        </div>

        <div className="space-y-6">
          {/* Resumo Principal */}
          {renderContextSection(
            'Resumo da Sessão', 
            contextData.context.summary,
            'bg-green-50', 
            'border-green-200', 
            'text-green-900'
          )}

          {/* Temas Principais */}
          {renderContextSection(
            'Temas Principais', 
            contextData.context.main_themes,
            'bg-blue-50', 
            'border-blue-200', 
            'text-blue-900'
          )}

          {/* Estado Emocional */}
          {renderContextSection(
            'Estado Emocional', 
            contextData.context.emotional_state,
            'bg-purple-50', 
            'border-purple-200', 
            'text-purple-900'
          )}

          {/* Insights Principais */}
          {renderContextSection(
            'Insights Principais', 
            contextData.context.key_insights,
            'bg-amber-50', 
            'border-amber-200', 
            'text-amber-900'
          )}

          {/* Progresso Terapêutico */}
          {renderContextSection(
            'Progresso Terapêutico', 
            contextData.context.therapeutic_progress,
            'bg-indigo-50', 
            'border-indigo-200', 
            'text-indigo-900'
          )}

          {/* Recomendações para Próxima Sessão */}
          {renderContextSection(
            'Recomendações para Próxima Sessão', 
            contextData.context.next_session_recommendations,
            'bg-emerald-50', 
            'border-emerald-200', 
            'text-emerald-900'
          )}

          {/* Momentos Importantes */}
          {contextData.context.important_moments && renderContextSection(
            'Momentos Importantes', 
            contextData.context.important_moments,
            'bg-rose-50', 
            'border-rose-200', 
            'text-rose-900'
          )}

          {/* Notas Terapêuticas */}
          {contextData.context.therapeutic_notes && renderContextSection(
            'Notas Terapêuticas', 
            contextData.context.therapeutic_notes,
            'bg-cyan-50', 
            'border-cyan-200', 
            'text-cyan-900'
          )}

          {/* Futuras Sessões */}
          {contextData.context.future_sessions && renderContextSection(
            'Sugestões para Futuras Sessões', 
            contextData.context.future_sessions,
            'bg-violet-50', 
            'border-violet-200', 
            'text-violet-900'
          )}

          {/* Informações Técnicas */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <h4 className="text-md font-medium text-gray-900 mb-4">Informações Técnicas</h4>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <dt className="text-gray-500 font-medium">Método de Geração:</dt>
                  <dd className="text-gray-900 mt-1">
                    {contextData.context.generation_method || 'Não especificado'}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 font-medium">Qualidade da Sessão:</dt>
                  <dd className="text-gray-900 mt-1">
                    {contextData.context.session_quality || 'Não avaliada'}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 font-medium">Total de Mensagens:</dt>
                  <dd className="text-gray-900 mt-1">
                    {contextData.context.total_messages || 'N/A'}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 font-medium">Contexto Criado:</dt>
                  <dd className="text-gray-900 mt-1">
                    {contextData.context_created_at ? 
                      new Date(contextData.context_created_at).toLocaleString('pt-BR') : 
                      'Não especificado'
                    }
                  </dd>
                </div>
              </div>
            </div>
          </div>

          {/* JSON Raw (para debugging/dados técnicos) */}
          <div className="mt-6">
            <details className="group">
              <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 list-none flex items-center">
                <span className="mr-2">📋</span>
                Dados Técnicos (JSON)
                <span className="ml-2 transform transition-transform group-open:rotate-90">▶</span>
              </summary>
              <div className="mt-3 bg-gray-900 text-gray-100 p-4 rounded-md overflow-auto max-h-60">
                <pre className="text-xs whitespace-pre-wrap">
                  {JSON.stringify(contextData.context, null, 2)}
                </pre>
              </div>
            </details>
          </div>
        </div>

        <div className="mt-8 flex justify-end space-x-3 pt-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="btn-secondary"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}

// Componente Modal para Detalhes da Sessão
function SessionDetailsModal({ session, onClose }) {
  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-4/5 lg:w-3/4 xl:w-2/3 shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            Detalhes da Sessão: {session.title || session.session_id}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <span className="sr-only">Fechar</span>
            ✕
          </button>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Informações Básicas */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-3">Informações da Sessão</h4>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-500">ID da Sessão</dt>
                <dd className="text-sm font-medium text-gray-900">{session.session_id}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Título</dt>
                <dd className="text-sm font-medium text-gray-900">{session.title}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Subtítulo</dt>
                <dd className="text-sm font-medium text-gray-900">{session.subtitle || 'Não definido'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Usuário</dt>
                <dd className="text-sm font-medium text-gray-900">{session.username}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Status</dt>
                <dd className="text-sm font-medium text-gray-900">{session.status}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Tipo</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {session.personalized ? 'Personalizada' : 'Template'}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Progresso</dt>
                <dd className="text-sm font-medium text-gray-900">{session.progress || 0}%</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Criada em</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {new Date(session.created_at).toLocaleString('pt-BR')}
                </dd>
              </div>
              {session.completed_at && (
                <div>
                  <dt className="text-sm text-gray-500">Completada em</dt>
                  <dd className="text-sm font-medium text-gray-900">
                    {new Date(session.completed_at).toLocaleString('pt-BR')}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Objetivo e Descrição */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-3">Objetivo Terapêutico</h4>
            <div className="bg-gray-50 p-3 rounded-md mb-4">
              <p className="text-sm text-gray-700">
                {session.objective || 'Objetivo não definido'}
              </p>
            </div>

            <h4 className="text-md font-medium text-gray-900 mb-3">Áreas de Foco</h4>
            <div className="mb-4">
              {session.focus_areas && session.focus_areas.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {session.focus_areas.map((area, index) => (
                    <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {area}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">Nenhuma área de foco definida</p>
              )}
            </div>

            {session.connection_to_previous && (
              <>
                <h4 className="text-md font-medium text-gray-900 mb-3">Conexão com Sessão Anterior</h4>
                <div className="bg-gray-50 p-3 rounded-md mb-4">
                  <p className="text-sm text-gray-700">
                    {session.connection_to_previous}
                  </p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Prompt Inicial */}
        {session.initial_prompt && (
          <div className="mt-6">
            <h4 className="text-md font-medium text-gray-900 mb-3">Prompt Inicial</h4>
            <div className="bg-blue-50 p-4 rounded-md border border-blue-200">
              <p className="text-sm text-blue-900 whitespace-pre-wrap">
                {session.initial_prompt}
              </p>
            </div>
          </div>
        )}

        {/* Contexto da Sessão (se disponível) */}
        {session.has_context && session.context ? (
          <div className="mt-6">
            <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
              <SparklesIcon className="w-5 h-5 mr-2 text-green-600" />
              Contexto/Resumo da Sessão
            </h4>
            <div className="bg-green-50 p-4 rounded-md border border-green-200">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {session.context.summary && (
                  <div>
                    <h5 className="font-medium text-green-900 mb-2">Resumo</h5>
                    <p className="text-sm text-green-800">{session.context.summary}</p>
                  </div>
                )}
                {session.context.main_themes && session.context.main_themes.length > 0 && (
                  <div>
                    <h5 className="font-medium text-green-900 mb-2">Temas Principais</h5>
                    <div className="flex flex-wrap gap-1">
                      {session.context.main_themes.map((theme, index) => (
                        <span key={index} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-200 text-green-800">
                          {theme}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {session.context.emotional_state && (
                  <div className="md:col-span-2">
                    <h5 className="font-medium text-green-900 mb-2">Estado Emocional</h5>
                    <div className="bg-green-100 p-3 rounded text-sm text-green-800">
                      {typeof session.context.emotional_state === 'string' ? 
                        session.context.emotional_state :
                        session.context.emotional_state.dominant_emotion || 
                        session.context.emotional_state.final ||
                        'Estado emocional analisado'
                      }
                    </div>
                  </div>
                )}
                {session.context.key_insights && session.context.key_insights.length > 0 && (
                  <div className="md:col-span-2">
                    <h5 className="font-medium text-green-900 mb-2">Insights Principais</h5>
                    <ul className="text-sm text-green-800 space-y-1">
                      {session.context.key_insights.map((insight, index) => (
                        <li key={index} className="flex items-start">
                          <span className="w-1.5 h-1.5 bg-green-600 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {session.context.therapeutic_progress && (
                  <div className="md:col-span-2">
                    <h5 className="font-medium text-green-900 mb-2">Progresso Terapêutico</h5>
                    <div className="bg-green-100 p-3 rounded text-sm text-green-800">
                      <p><strong>Engajamento:</strong> {session.context.therapeutic_progress.engagement_level || 'Não especificado'}</p>
                      {session.context.therapeutic_progress.areas_of_focus && (
                        <p><strong>Áreas de foco:</strong> {session.context.therapeutic_progress.areas_of_focus.join(', ')}</p>
                      )}
                    </div>
                  </div>
                )}
                {session.context.next_session_recommendations && session.context.next_session_recommendations.length > 0 && (
                  <div className="md:col-span-2">
                    <h5 className="font-medium text-green-900 mb-2">Recomendações para Próxima Sessão</h5>
                    <ul className="text-sm text-green-800 space-y-1">
                      {session.context.next_session_recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start">
                          <span className="w-1.5 h-1.5 bg-green-600 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              
              {/* Metadados do contexto */}
              <div className="mt-4 pt-4 border-t border-green-200">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-green-700">
                  <div>
                    <span className="font-medium">Geração:</span>
                    <div>{session.context.generation_method || 'Não especificado'}</div>
                  </div>
                  <div>
                    <span className="font-medium">Qualidade:</span>
                    <div>{session.context.session_quality || 'Não avaliada'}</div>
                  </div>
                  {session.context_created_at && (
                    <div>
                      <span className="font-medium">Contexto criado:</span>
                      <div>{new Date(session.context_created_at).toLocaleDateString('pt-BR')}</div>
                    </div>
                  )}
                  <div>
                    <span className="font-medium">Total de mensagens:</span>
                    <div>{session.context.total_messages || 'N/A'}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : session.has_context === false ? (
          <div className="mt-6">
            <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
              <XCircleIcon className="w-5 h-5 mr-2 text-gray-400" />
              Contexto da Sessão
            </h4>
            <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
              <p className="text-sm text-gray-600">
                Esta sessão ainda não possui um contexto gerado. O contexto é criado automaticamente quando a sessão é finalizada.
              </p>
            </div>
          </div>
        ) : null}

        {/* Informações Técnicas */}
        <div className="mt-6">
          <h4 className="text-md font-medium text-gray-900 mb-3">Informações Técnicas</h4>
          <div className="bg-gray-50 p-3 rounded-md">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <dt className="text-gray-500">Geração</dt>
                <dd className="font-medium text-gray-900">
                  {session.generation_method || 'Não especificado'}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Baseada em</dt>
                <dd className="font-medium text-gray-900">
                  {session.based_on_session || 'Sessão inicial'}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Duração Estimada</dt>
                <dd className="font-medium text-gray-900">
                  {session.estimated_duration || 'Não definida'}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Ativa</dt>
                <dd className="font-medium text-gray-900">
                  {session.is_active ? 'Sim' : 'Não'}
                </dd>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="btn-secondary"
          >
            Fechar
          </button>
          <button className="btn-primary">
            Ver Conversa Completa
          </button>
        </div>
      </div>
    </div>
  );
}

export default SessionManagement; 