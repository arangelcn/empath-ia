import React, { useState, useEffect } from 'react';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import apiService from '../services/api';

function SessionForm({ session, onSave, onCancel, isEditing = false }) {
  const [formData, setFormData] = useState({
    session_id: session?.session_id || '',
    title: session?.title || '',
    subtitle: session?.subtitle || '',
    objective: session?.objective || '',
    initial_prompt: session?.initial_prompt || '',
    is_active: session?.is_active ?? true
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      if (isEditing) {
        await apiService.updateTherapeuticSession(session.session_id, formData);
      } else {
        await apiService.createTherapeuticSession(formData);
      }
      onSave();
    } catch (error) {
      setError(error.message || 'Erro ao salvar sessão');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-gray-900">
            {isEditing ? 'Editar Sessão Terapêutica' : 'Nova Sessão Terapêutica'}
          </h3>
          <button 
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ID da Sessão *
              </label>
              <input
                type="text"
                name="session_id"
                value={formData.session_id}
                onChange={handleChange}
                required
                disabled={isEditing}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                placeholder="session-1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Título *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Sessão 1: Te conhecendo melhor"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Subtítulo
            </label>
            <input
              type="text"
              name="subtitle"
              value={formData.subtitle}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Para levantar dados iniciais do usuário"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Objetivo *
            </label>
            <textarea
              name="objective"
              value={formData.objective}
              onChange={handleChange}
              required
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Objetivo terapêutico desta sessão..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Prompt Inicial *
            </label>
            <textarea
              name="initial_prompt"
              value={formData.initial_prompt}
              onChange={handleChange}
              required
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Prompt inicial para a IA iniciar a sessão..."
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              name="is_active"
              checked={formData.is_active}
              onChange={handleChange}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label className="ml-2 block text-sm text-gray-900">
              Sessão ativa
            </label>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
            >
              {isLoading ? 'Salvando...' : (isEditing ? 'Atualizar' : 'Criar')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SessionDetails({ session, onClose }) {
  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-gray-900">
            Detalhes da Sessão: {session.title}
          </h3>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ID da Sessão
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                {session.session_id}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <div className="flex items-center">
                {session.is_active ? (
                  <CheckIcon className="w-5 h-5 text-green-600 mr-2" />
                ) : (
                  <XMarkIcon className="w-5 h-5 text-red-600 mr-2" />
                )}
                <span className={`text-sm font-medium ${
                  session.is_active ? 'text-green-800' : 'text-red-800'
                }`}>
                  {session.is_active ? 'Ativa' : 'Inativa'}
                </span>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Título
            </label>
            <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
              {session.title}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Subtítulo
            </label>
            <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
              {session.subtitle || 'Não informado'}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Objetivo
            </label>
            <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
              {session.objective}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Prompt Inicial
            </label>
            <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md whitespace-pre-wrap">
              {session.initial_prompt}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Criada em
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                {new Date(session.created_at).toLocaleString('pt-BR')}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Atualizada em
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                {new Date(session.updated_at).toLocaleString('pt-BR')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SessionCard({ session, onEdit, onDelete, onView }) {
  return (
    <div className="card hover:shadow-md transition-shadow duration-200">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex-1">
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 mb-3">
            <h3 className="text-lg font-medium text-gray-900">
              {session.title}
            </h3>
            {session.is_active ? (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                <CheckIcon className="w-3 h-3 mr-1" />
                Ativa
              </span>
            ) : (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                <XMarkIcon className="w-3 h-3 mr-1" />
                Inativa
              </span>
            )}
          </div>
          
          <div className="space-y-2">
            <p className="text-sm text-gray-600">
              {session.subtitle || 'Sem subtítulo'}
            </p>
            
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-sm text-gray-500">
              <span className="font-medium">ID: {session.session_id}</span>
              {session.objective && (
                <span className="line-clamp-2 max-w-md">
                  Objetivo: {session.objective}
                </span>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center justify-end lg:justify-start gap-2">
          <button
            onClick={() => onView(session)}
            className="btn-secondary-sm"
            title="Ver detalhes"
          >
            <EyeIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => onEdit(session)}
            className="btn-secondary-sm"
            title="Editar"
          >
            <PencilIcon className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(session)}
            className="btn-danger-sm"
            title="Deletar"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SessionManagement() {
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeOnly, setActiveOnly] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingSession, setEditingSession] = useState(null);
  const [viewingSession, setViewingSession] = useState(null);
  const [sortBy, setSortBy] = useState('title');
  const [sortOrder, setSortOrder] = useState('asc');
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 20,
    offset: 0,
    has_next: false
  });

  const loadSessions = async (search = '', offset = 0) => {
    try {
      setIsLoading(true);
      setError(null);

      const params = {
        limit: pagination.limit,
        offset: offset,
        active_only: activeOnly
      };

      if (search.trim()) {
        params.search = search.trim();
      }

      const response = await apiService.getTherapeuticSessions(params);
      
      if (response.success) {
        setSessions(response.data.sessions);
        setPagination(response.data.pagination);
      }
    } catch (error) {
      console.error('Erro ao carregar sessões:', error);
      setError('Erro ao carregar sessões. Verifique se o backend está rodando.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadSessions(searchTerm, 0);
  };

  const handleRefresh = () => {
    loadSessions(searchTerm, pagination.offset);
  };

  const handleCreateSession = () => {
    setEditingSession(null);
    setShowForm(true);
  };

  const handleEditSession = (session) => {
    setEditingSession(session);
    setShowForm(true);
  };

  const handleDeleteSession = async (session) => {
    if (!window.confirm(`Tem certeza que deseja deletar a sessão "${session.title}"?`)) {
      return;
    }

    try {
      await apiService.deleteTherapeuticSession(session.session_id);
      loadSessions(searchTerm, pagination.offset);
    } catch (error) {
      console.error('Erro ao deletar sessão:', error);
      alert('Erro ao deletar sessão: ' + error.message);
    }
  };

  const handleViewSession = (session) => {
    setViewingSession(session);
  };

  const handleSaveSession = () => {
    setShowForm(false);
    setEditingSession(null);
    loadSessions(searchTerm, pagination.offset);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingSession(null);
  };

  const handleCloseDetails = () => {
    setViewingSession(null);
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const sortSessions = (sessions) => {
    return [...sessions].sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];
      
      if (sortBy === 'title' || sortBy === 'subtitle') {
        aValue = (aValue || '').toLowerCase();
        bValue = (bValue || '').toLowerCase();
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  };

  useEffect(() => {
    loadSessions();
  }, [activeOnly]);

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Gerenciamento de Sessões</h1>
          <p className="mt-1 text-sm text-gray-600">
            Crie e gerencie sessões terapêuticas do sistema
          </p>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Erro de Conexão</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <button 
                onClick={() => loadSessions()}
                className="mt-2 text-sm text-red-600 hover:text-red-500 font-medium"
              >
                Tentar novamente
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Gerenciamento de Sessões</h1>
          <p className="mt-1 text-sm text-gray-600">
            Crie e gerencie sessões terapêuticas do sistema
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button 
            onClick={handleRefresh}
            disabled={isLoading}
            className="btn-secondary flex items-center"
          >
            <MagnifyingGlassIcon className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
          <button 
            onClick={handleCreateSession}
            className="btn-primary flex items-center"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Nova Sessão
          </button>
        </div>
      </div>

      {/* Filtros e Ordenação */}
      <div className="card">
        <form onSubmit={handleSearch} className="flex flex-col lg:flex-row gap-4">
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
                placeholder="Pesquisar por título, subtítulo ou ID..."
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button 
              type="submit"
              disabled={isLoading}
              className="btn-primary"
            >
              Pesquisar
            </button>
            <button 
              type="button"
              onClick={() => setSearchTerm('')}
              className="btn-secondary"
            >
              Limpar
            </button>
          </div>
        </form>
        
        <div className="mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={activeOnly}
                onChange={(e) => setActiveOnly(e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">Mostrar apenas sessões ativas</span>
            </label>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-700">Ordenar por:</span>
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-');
                setSortBy(field);
                setSortOrder(order);
              }}
              className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="title-asc">Título (A-Z)</option>
              <option value="title-desc">Título (Z-A)</option>
              <option value="session_id-asc">ID (A-Z)</option>
              <option value="session_id-desc">ID (Z-A)</option>
              <option value="is_active-desc">Ativas primeiro</option>
              <option value="is_active-asc">Inativas primeiro</option>
            </select>
          </div>
        </div>
      </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <FunnelIcon className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total de Sessões</dt>
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
              <CheckIcon className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Sessões Ativas</dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {isLoading ? '-' : sessions.filter(s => s.is_active).length}
                </dd>
              </dl>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <XMarkIcon className="h-8 w-8 text-red-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Sessões Inativas</dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {isLoading ? '-' : sessions.filter(s => !s.is_active).length}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de Sessões */}
      <div className="space-y-4">
        {isLoading ? (
          // Loading skeleton
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="card animate-pulse">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="h-5 w-48 bg-gray-300 rounded mb-2"></div>
                    <div className="h-4 w-32 bg-gray-300 rounded"></div>
                  </div>
                  <div className="space-x-2">
                    <div className="h-8 w-8 bg-gray-300 rounded"></div>
                    <div className="h-8 w-8 bg-gray-300 rounded"></div>
                    <div className="h-8 w-8 bg-gray-300 rounded"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="card text-center py-12">
            <FunnelIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma sessão encontrada</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm ? 'Tente ajustar os termos de pesquisa.' : 'Não há sessões para exibir no momento.'}
            </p>
            <div className="mt-6">
              <button
                onClick={handleCreateSession}
                className="btn-primary"
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                Criar Primeira Sessão
              </button>
            </div>
          </div>
        ) : (
          sortSessions(sessions).map((session) => (
            <SessionCard 
              key={session.id} 
              session={session} 
              onEdit={handleEditSession}
              onDelete={handleDeleteSession}
              onView={handleViewSession}
            />
          ))
        )}
      </div>

      {/* Paginação */}
      {!isLoading && sessions.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Mostrando {sessions.length} de {pagination.total} sessões
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => loadSessions(searchTerm, Math.max(0, pagination.offset - pagination.limit))}
                disabled={pagination.offset === 0}
                className="btn-secondary-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Anterior
              </button>
              <span className="text-sm text-gray-700">
                Página {Math.floor(pagination.offset / pagination.limit) + 1}
              </span>
              <button
                onClick={() => loadSessions(searchTerm, pagination.offset + pagination.limit)}
                disabled={!pagination.has_next}
                className="btn-secondary-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Próxima
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modais */}
      {showForm && (
        <SessionForm
          session={editingSession}
          onSave={handleSaveSession}
          onCancel={handleCancelForm}
          isEditing={!!editingSession}
        />
      )}

      {viewingSession && (
        <SessionDetails
          session={viewingSession}
          onClose={handleCloseDetails}
        />
      )}
    </div>
  );
} 