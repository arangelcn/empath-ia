import React, { useState, useEffect } from 'react';
import {
  ChatBubbleLeftRightIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  CalendarIcon,
  UserIcon,
  FaceSmileIcon,
  ClockIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import apiService from '../services/api';
import { ErrorState, UnavailableState } from '../components/AdminState';

function ConversationCard({ conversation, onViewDetails }) {
  const getStatusColor = (status) => {
    return status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="card hover:shadow-md transition-shadow duration-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex-shrink-0">
            <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
              <UserIcon className="w-5 h-5 text-primary-600" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium text-gray-900 truncate">
              {conversation.username}
            </h3>
            <p className="text-sm text-gray-500">
              ID: {conversation.session_id}
            </p>
            <div className="flex items-center space-x-4 mt-1">
              <div className="flex items-center text-xs text-gray-500">
                <ChatBubbleLeftRightIcon className="w-4 h-4 mr-1" />
                {conversation.message_count} mensagens
              </div>
              <div className="flex items-center text-xs text-gray-500">
                <CalendarIcon className="w-4 h-4 mr-1" />
                {formatDate(conversation.updated_at)}
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(conversation.status)}`}>
            {conversation.status === 'active' ? 'Ativa' : 'Inativa'}
          </span>
          <button 
            onClick={() => onViewDetails(conversation)}
            className="btn-secondary-sm"
          >
            <EyeIcon className="w-4 h-4 mr-1" />
            Ver Detalhes
          </button>
        </div>
      </div>
    </div>
  );
}

function ConversationDetails({ conversation, onClose }) {
  const [details, setDetails] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadDetails = async () => {
      try {
        setIsLoading(true);
        const response = await apiService.getConversationDetails(conversation.session_id);
        if (response.success) {
          setDetails(response.data);
        }
      } catch (error) {
        console.error('Erro ao carregar detalhes:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadDetails();
  }, [conversation.session_id]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getEmotionColor = (emotion) => {
    const colors = {
      alegria: 'text-green-600',
      tristeza: 'text-blue-600',
      ansiedade: 'text-yellow-600',
      raiva: 'text-red-600',
      neutro: 'text-gray-600'
    };
    return colors[emotion?.toLowerCase()] || 'text-gray-600';
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-300 rounded mb-4"></div>
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-20 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
          <div className="text-center py-8">
            <p className="text-gray-500">Erro ao carregar detalhes da conversa</p>
            <button onClick={onClose} className="mt-4 btn-primary">
              Fechar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-gray-900">
            Detalhes da Conversa - {details.username}
          </h3>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <span className="sr-only">Fechar</span>
            ✕
          </button>
        </div>

        {/* Estatísticas da Conversa */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{details.statistics.total_messages}</div>
            <div className="text-sm text-gray-600">Total de Mensagens</div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{details.statistics.duration_minutes}</div>
            <div className="text-sm text-gray-600">Duração (min)</div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{details.statistics.user_messages}</div>
            <div className="text-sm text-gray-600">Mensagens do Usuário</div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg">
            {details.statistics.emotion_analysis ? (
              <div className={`text-2xl font-bold capitalize ${getEmotionColor(details.statistics.emotion_analysis.dominant_emotion)}`}>
                {details.statistics.emotion_analysis.dominant_emotion}
              </div>
            ) : (
              <div className="text-sm font-semibold text-gray-500">Indisponível</div>
            )}
            <div className="text-sm text-gray-600">Emoção Dominante</div>
          </div>
        </div>

        {details.unavailable_fields?.includes('emotion_analysis') && (
          <div className="mb-6">
            <UnavailableState
              title="Análise emocional indisponível"
              message="O backend não retornou uma análise emocional real para esta conversa."
            />
          </div>
        )}

        {/* Informações da Conversa */}
        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="text-sm font-medium text-gray-700">ID da Sessão:</span>
              <p className="text-sm text-gray-900">{details.session_id}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-700">Usuário:</span>
              <p className="text-sm text-gray-900">{details.username}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-700">Criada em:</span>
              <p className="text-sm text-gray-900">{formatDate(details.created_at)}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-700">Última atividade:</span>
              <p className="text-sm text-gray-900">{formatDate(details.updated_at)}</p>
            </div>
          </div>
        </div>

        {/* Histórico de Mensagens */}
        <div className="max-h-96 overflow-y-auto">
          <h4 className="text-md font-medium text-gray-900 mb-3">Histórico de Mensagens</h4>
          <div className="space-y-3">
            {details.messages.map((message, index) => (
              <div 
                key={index}
                className={`p-3 rounded-lg ${
                  message.role === 'user' 
                    ? 'bg-blue-50 ml-8' 
                    : 'bg-green-50 mr-8'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-xs font-medium ${
                    message.role === 'user' 
                      ? 'text-blue-600' 
                      : 'text-green-600'
                  }`}>
                    {message.role === 'user' ? 'Usuário' : 'Assistente'}
                  </span>
                  <span className="text-xs text-gray-500">
                    {message.timestamp ? formatDate(message.timestamp) : ''}
                  </span>
                </div>
                <p className="text-sm text-gray-800">{message.content}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button onClick={onClose} className="btn-primary">
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Conversations() {
  const [conversations, setConversations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 10,
    offset: 0,
    has_next: false
  });

  const loadConversations = async (search = '', offset = 0) => {
    try {
      setIsLoading(true);
      setError(null);

      const params = {
        limit: pagination.limit,
        offset: offset,
      };

      if (search.trim()) {
        params.search = search.trim();
      }

      const response = await apiService.getConversations(params);
      
      if (response.success) {
        setConversations(response.data.conversations);
        setPagination(response.data.pagination);
      }
    } catch (error) {
      console.error('Erro ao carregar conversas:', error);
      setError(apiService.formatError(error, 'Erro ao carregar conversas. Verifique se o backend está rodando.'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadConversations(searchTerm, 0);
  };

  const handleRefresh = () => {
    loadConversations(searchTerm, pagination.offset);
  };

  const handleViewDetails = (conversation) => {
    setSelectedConversation(conversation);
  };

  const handleCloseDetails = () => {
    setSelectedConversation(null);
  };

  const handleNextPage = () => {
    if (pagination.has_next) {
      const newOffset = pagination.offset + pagination.limit;
      loadConversations(searchTerm, newOffset);
    }
  };

  const handlePrevPage = () => {
    if (pagination.offset > 0) {
      const newOffset = Math.max(0, pagination.offset - pagination.limit);
      loadConversations(searchTerm, newOffset);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Conversas</h1>
          <p className="mt-1 text-sm text-gray-600">
            Visualize e gerencie todas as conversas do sistema
          </p>
        </div>
        
        <ErrorState title="Erro de conexão" message={error} onRetry={() => loadConversations()} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Conversas</h1>
          <p className="mt-1 text-sm text-gray-600">
            Visualize e gerencie todas as conversas do sistema
          </p>
        </div>
        <button 
          onClick={handleRefresh}
          disabled={isLoading}
          className="btn-secondary flex items-center"
        >
          <ArrowPathIcon className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Atualizar
        </button>
      </div>

      {/* Barra de Pesquisa */}
      <div className="card">
        <form onSubmit={handleSearch} className="flex space-x-4">
          <div className="flex-1">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                placeholder="Pesquisar por usuário ou ID da sessão..."
              />
            </div>
          </div>
          <button 
            type="submit"
            disabled={isLoading}
            className="btn-primary"
          >
            Pesquisar
          </button>
        </form>
      </div>

      {/* Estatísticas Rápidas */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChatBubbleLeftRightIcon className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total de Conversas</dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {isLoading ? '-' : pagination.total}
                </dd>
              </dl>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UserIcon className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Conversas Ativas</dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {isLoading ? '-' : conversations.filter(c => c.status === 'active').length}
                </dd>
              </dl>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <FaceSmileIcon className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Análise Emocional</dt>
                <dd className="text-sm font-semibold text-gray-500">
                  Indisponível
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de Conversas */}
      <div className="space-y-4">
        {isLoading ? (
          // Loading skeleton
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="card animate-pulse">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-gray-300 rounded-full"></div>
                    <div className="space-y-2">
                      <div className="h-4 w-32 bg-gray-300 rounded"></div>
                      <div className="h-3 w-24 bg-gray-300 rounded"></div>
                      <div className="h-3 w-40 bg-gray-300 rounded"></div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="h-6 w-16 bg-gray-300 rounded-full"></div>
                    <div className="h-8 w-20 bg-gray-300 rounded"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="card text-center py-12">
            <ChatBubbleLeftRightIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma conversa encontrada</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm ? 'Tente ajustar os termos de pesquisa.' : 'Não há conversas para exibir no momento.'}
            </p>
          </div>
        ) : (
          conversations.map((conversation) => (
            <ConversationCard 
              key={conversation.id} 
              conversation={conversation} 
              onViewDetails={handleViewDetails}
            />
          ))
        )}
      </div>

      {/* Paginação */}
      {conversations.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-700">
            Mostrando <span className="font-medium">{pagination.offset + 1}</span> até{' '}
            <span className="font-medium">
              {Math.min(pagination.offset + pagination.limit, pagination.total)}
            </span>{' '}
            de <span className="font-medium">{pagination.total}</span> conversas
          </p>
          <div className="flex space-x-2">
            <button
              onClick={handlePrevPage}
              disabled={pagination.offset === 0}
              className="btn-secondary-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Anterior
            </button>
            <button
              onClick={handleNextPage}
              disabled={!pagination.has_next}
              className="btn-secondary-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Próxima
            </button>
          </div>
        </div>
      )}

      {/* Modal de Detalhes */}
      {selectedConversation && (
        <ConversationDetails 
          conversation={selectedConversation}
          onClose={handleCloseDetails}
        />
      )}
    </div>
  );
} 
