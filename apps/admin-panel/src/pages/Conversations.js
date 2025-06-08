import React, { useState } from 'react';
import {
  ChatBubbleLeftRightIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  CalendarIcon,
  UserIcon,
  FaceSmileIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

const Conversations = () => {
  const [conversations, setConversations] = useState([
    {
      id: 1,
      userId: 'user_1247',
      userName: 'João Silva',
      startTime: '2024-01-15 14:30:00',
      endTime: '2024-01-15 14:55:00',
      duration: '25min',
      messageCount: 18,
      primaryEmotion: 'Alegria',
      emotionConfidence: 85,
      status: 'completed',
      lastMessage: 'Muito obrigado pela conversa, me sinto muito melhor agora!',
      tags: ['positiva', 'terapêutica'],
    },
    {
      id: 2,
      userId: 'user_1246',
      userName: 'Maria Santos',
      startTime: '2024-01-15 14:15:00',
      endTime: '2024-01-15 14:42:00',
      duration: '27min',
      messageCount: 23,
      primaryEmotion: 'Ansiedade',
      emotionConfidence: 78,
      status: 'completed',
      lastMessage: 'Entendi, vou tentar praticar essas técnicas de respiração.',
      tags: ['ansiedade', 'técnicas'],
    },
    {
      id: 3,
      userId: 'user_1245',
      userName: 'Pedro Costa',
      startTime: '2024-01-15 14:00:00',
      endTime: null,
      duration: '15min (ativa)',
      messageCount: 8,
      primaryEmotion: 'Tristeza',
      emotionConfidence: 92,
      status: 'active',
      lastMessage: 'Não sei mais o que fazer com essa situação...',
      tags: ['ativa', 'apoio'],
    },
    {
      id: 4,
      userId: 'user_1244',
      userName: 'Ana Lima',
      startTime: '2024-01-15 13:45:00',
      endTime: '2024-01-15 14:20:00',
      duration: '35min',
      messageCount: 31,
      primaryEmotion: 'Raiva',
      emotionConfidence: 74,
      status: 'completed',
      lastMessage: 'Preciso de um tempo para processar tudo isso.',
      tags: ['longa', 'complexa'],
    },
    {
      id: 5,
      userId: 'user_1243',
      userName: 'Carlos Oliveira',
      startTime: '2024-01-15 13:30:00',
      endTime: '2024-01-15 13:48:00',
      duration: '18min',
      messageCount: 12,
      primaryEmotion: 'Neutro',
      emotionConfidence: 67,
      status: 'completed',
      lastMessage: 'Obrigado pelas informações, foram muito úteis.',
      tags: ['informativa'],
    },
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [emotionFilter, setEmotionFilter] = useState('all');
  const [selectedConversation, setSelectedConversation] = useState(null);

  const filteredConversations = conversations.filter(conv => {
    const matchesSearch = conv.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         conv.userId.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         conv.lastMessage.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || conv.status === statusFilter;
    const matchesEmotion = emotionFilter === 'all' || conv.primaryEmotion === emotionFilter;
    
    return matchesSearch && matchesStatus && matchesEmotion;
  });

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { bg: 'bg-green-100', text: 'text-green-800', label: 'Ativa', dot: 'bg-green-400' },
      completed: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Finalizada', dot: 'bg-blue-400' },
      interrupted: { bg: 'bg-red-100', text: 'text-red-800', label: 'Interrompida', dot: 'bg-red-400' },
    };
    
    const config = statusConfig[status] || statusConfig.completed;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        <div className={`w-1.5 h-1.5 ${config.dot} rounded-full mr-1.5`}></div>
        {config.label}
      </span>
    );
  };

  const getEmotionBadge = (emotion, confidence) => {
    const emotionConfig = {
      'Alegria': { bg: 'bg-green-100', text: 'text-green-800', emoji: '😊' },
      'Tristeza': { bg: 'bg-blue-100', text: 'text-blue-800', emoji: '😢' },
      'Ansiedade': { bg: 'bg-yellow-100', text: 'text-yellow-800', emoji: '😰' },
      'Raiva': { bg: 'bg-red-100', text: 'text-red-800', emoji: '😠' },
      'Neutro': { bg: 'bg-gray-100', text: 'text-gray-800', emoji: '😐' },
    };
    
    const config = emotionConfig[emotion] || emotionConfig.Neutro;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        <span className="mr-1">{config.emoji}</span>
        {emotion} ({confidence}%)
      </span>
    );
  };

  const formatTime = (timeString) => {
    if (!timeString) return '-';
    const date = new Date(timeString);
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (timeString) => {
    const date = new Date(timeString);
    return date.toLocaleDateString('pt-BR');
  };

  const handleViewConversation = (conversation) => {
    setSelectedConversation(conversation);
  };

  // Simulação de mensagens da conversa
  const getConversationMessages = (conversationId) => {
    const sampleMessages = [
      {
        id: 1,
        sender: 'user',
        message: 'Oi, estou me sentindo um pouco ansioso hoje.',
        timestamp: '14:30:15',
        emotion: 'Ansiedade',
        confidence: 78
      },
      {
        id: 2,
        sender: 'ai',
        message: 'Olá! Entendo que você está se sentindo ansioso. Pode me contar um pouco mais sobre o que está acontecendo?',
        timestamp: '14:30:45'
      },
      {
        id: 3,
        sender: 'user',
        message: 'Tenho uma apresentação importante amanhã e não consigo parar de pensar no que pode dar errado.',
        timestamp: '14:31:20',
        emotion: 'Ansiedade',
        confidence: 85
      },
      {
        id: 4,
        sender: 'ai',
        message: 'É natural sentir ansiedade antes de eventos importantes. Que tal praticarmos algumas técnicas de respiração para te ajudar a se acalmar?',
        timestamp: '14:31:50'
      },
    ];
    
    return sampleMessages;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Conversas</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitore e analise as interações dos usuários com o sistema
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button className="btn-secondary flex items-center space-x-2">
            <CalendarIcon className="h-4 w-4" />
            <span>Exportar Relatório</span>
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por usuário, ID ou mensagem..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 input-field"
              />
            </div>
          </div>
          
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field"
            >
              <option value="all">Todos os status</option>
              <option value="active">Ativas</option>
              <option value="completed">Finalizadas</option>
              <option value="interrupted">Interrompidas</option>
            </select>
          </div>

          <div>
            <select
              value={emotionFilter}
              onChange={(e) => setEmotionFilter(e.target.value)}
              className="input-field"
            >
              <option value="all">Todas as emoções</option>
              <option value="Alegria">Alegria</option>
              <option value="Tristeza">Tristeza</option>
              <option value="Ansiedade">Ansiedade</option>
              <option value="Raiva">Raiva</option>
              <option value="Neutro">Neutro</option>
            </select>
          </div>
        </div>
      </div>

      {/* Lista de conversas */}
      <div className="card">
        <div className="space-y-4">
          {filteredConversations.map((conversation) => (
            <div
              key={conversation.id}
              className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:shadow-sm transition-all duration-200"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-primary-600 flex items-center justify-center">
                      <UserIcon className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center space-x-2">
                      <p className="text-sm font-medium text-gray-900">{conversation.userName}</p>
                      <span className="text-xs text-gray-500">#{conversation.userId}</span>
                      {getStatusBadge(conversation.status)}
                    </div>
                    
                    <div className="mt-1 flex items-center space-x-4 text-xs text-gray-500">
                      <span className="flex items-center">
                        <ClockIcon className="h-3 w-3 mr-1" />
                        {formatDate(conversation.startTime)} {formatTime(conversation.startTime)}
                      </span>
                      <span>Duração: {conversation.duration}</span>
                      <span>{conversation.messageCount} mensagens</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {getEmotionBadge(conversation.primaryEmotion, conversation.emotionConfidence)}
                  <button
                    onClick={() => handleViewConversation(conversation)}
                    className="text-primary-600 hover:text-primary-900"
                    title="Ver conversa"
                  >
                    <EyeIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div className="mt-3">
                <p className="text-sm text-gray-600 line-clamp-2">
                  <strong>Última mensagem:</strong> {conversation.lastMessage}
                </p>
              </div>

              <div className="mt-2 flex flex-wrap gap-1">
                {conversation.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        {filteredConversations.length === 0 && (
          <div className="text-center py-8">
            <ChatBubbleLeftRightIcon className="mx-auto h-12 w-12 text-gray-300" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma conversa encontrada</h3>
            <p className="mt-1 text-sm text-gray-500">
              Tente ajustar os filtros de busca.
            </p>
          </div>
        )}
      </div>

      {/* Estatísticas rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card text-center">
          <div className="text-2xl font-bold text-primary-600">{conversations.length}</div>
          <div className="text-sm text-gray-500">Total de Conversas</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-green-600">
            {conversations.filter(c => c.status === 'active').length}
          </div>
          <div className="text-sm text-gray-500">Conversas Ativas</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-blue-600">
            {Math.round(conversations.reduce((acc, c) => acc + c.messageCount, 0) / conversations.length)}
          </div>
          <div className="text-sm text-gray-500">Mensagens por Conversa</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-purple-600">
            {Math.round(conversations.reduce((acc, c) => acc + c.emotionConfidence, 0) / conversations.length)}%
          </div>
          <div className="text-sm text-gray-500">Confiança Média</div>
        </div>
      </div>

      {/* Modal de visualização da conversa */}
      {selectedConversation && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center pb-3 border-b">
              <h3 className="text-lg font-semibold">
                Conversa: {selectedConversation.userName}
              </h3>
              <button
                onClick={() => setSelectedConversation(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="mt-4 max-h-96 overflow-y-auto">
              <div className="space-y-3">
                {getConversationMessages(selectedConversation.id).map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs px-3 py-2 rounded-lg ${
                        msg.sender === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-200 text-gray-900'
                      }`}
                    >
                      <p className="text-sm">{msg.message}</p>
                      <div className="flex justify-between items-center mt-1">
                        <span className="text-xs opacity-75">{msg.timestamp}</span>
                        {msg.emotion && (
                          <span className="text-xs opacity-75">
                            {msg.emotion} ({msg.confidence}%)
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Conversations; 