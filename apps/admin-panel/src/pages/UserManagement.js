import React, { useState, useEffect } from 'react';
import {
  UserGroupIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  UserIcon,
  ChartBarIcon,
  CalendarIcon,
  ClockIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import apiService from '../services/api';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserDetails, setShowUserDetails] = useState(false);
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 50,
    offset: 0,
    hasNext: false
  });

  // Carregar usuários
  const loadUsers = async (params = {}) => {
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

      // Configurar active_only baseado no filtro
      if (filterStatus === 'active') {
        apiParams.active_only = true;
      } else if (filterStatus === 'inactive') {
        apiParams.active_only = false;
      }
      // Se filterStatus === 'all', não enviar active_only para buscar todos

      const response = await apiService.getUsers(apiParams);

      if (response.success) {
        setUsers(response.data.users || []);
        setPagination(prev => ({
          ...prev,
          total: response.data.pagination?.total || 0,
          hasNext: response.data.pagination?.has_next || false
        }));
      } else {
        throw new Error('Falha ao carregar usuários');
      }
    } catch (err) {
      console.error('Erro ao carregar usuários:', err);
      setError(apiService.formatError(err, 'Erro ao carregar usuários. Verifique a conexão com o servidor.'));
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  // Carregar detalhes do usuário
  const loadUserDetails = async (username) => {
    try {
      const [userResponse, statsResponse] = await Promise.all([
        apiService.getUserDetails(username),
        apiService.getUserStats(username)
      ]);

      if (userResponse.success && statsResponse.success) {
        setSelectedUser({
          ...userResponse.data.user,
          stats: statsResponse.data
        });
        setShowUserDetails(true);
      }
    } catch (err) {
      console.error('Erro ao carregar detalhes do usuário:', err);
      setError(apiService.formatError(err, 'Erro ao carregar detalhes do usuário'));
    }
  };

  // Efeitos
  useEffect(() => {
    loadUsers();
  }, []);

  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      // Reset pagination quando mudarem os filtros
      setPagination(prev => ({ ...prev, offset: 0 }));
      loadUsers({ offset: 0 });
    }, 500);

    return () => clearTimeout(delayedSearch);
  }, [searchTerm, filterStatus]);

  // Filtros locais (fallback se a API não suportar filtros)
  const filteredUsers = users.filter(user => {
    const matchesSearch = !searchTerm || 
      user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === 'all' || 
      (filterStatus === 'active' && user.is_active) ||
      (filterStatus === 'inactive' && !user.is_active);
    
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (isActive) => {
    if (isActive) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          Ativo
        </span>
      );
    }
    
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        Inativo
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Nunca';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handlePrevPage = () => {
    if (pagination.offset > 0) {
      const newOffset = Math.max(0, pagination.offset - pagination.limit);
      setPagination(prev => ({ ...prev, offset: newOffset }));
      loadUsers({ offset: newOffset });
    }
  };

  const handleNextPage = () => {
    if (pagination.hasNext) {
      const newOffset = pagination.offset + pagination.limit;
      setPagination(prev => ({ ...prev, offset: newOffset }));
      loadUsers({ offset: newOffset });
    }
  };

  if (loading && users.length === 0) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2">
            <ArrowPathIcon className="w-5 h-5 animate-spin text-primary-600" />
            <span className="text-gray-600">Carregando usuários...</span>
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
              <UserGroupIcon className="w-8 h-8 mr-3 text-primary-600" />
              Gerenciamento de Usuários
            </h1>
            <p className="text-gray-600 mt-1">
              Visualize e gerencie todos os usuários da plataforma
            </p>
          </div>
          <button className="btn-primary opacity-60 cursor-not-allowed" disabled title="Fluxo de criação aguardando contrato operacional revisado">
            <PlusIcon className="w-4 h-4 mr-2" />
            Novo Usuário
          </button>
        </div>
      </div>

      {/* Estatísticas Rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UserGroupIcon className="w-8 h-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total de Usuários</p>
              <p className="text-2xl font-bold text-gray-900">{pagination.total}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="w-8 h-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Usuários Ativos</p>
              <p className="text-2xl font-bold text-gray-900">
                {filteredUsers.filter(u => u.is_active).length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CalendarIcon className="w-8 h-8 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Novos Hoje</p>
              <p className="text-2xl font-bold text-gray-900">
                {filteredUsers.filter(u => {
                  const today = new Date().toDateString();
                  const userDate = new Date(u.created_at).toDateString();
                  return today === userDate;
                }).length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClockIcon className="w-8 h-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Login Recente</p>
              <p className="text-2xl font-bold text-gray-900">
                {filteredUsers.filter(u => {
                  if (!u.last_login) return false;
                  const lastLogin = new Date(u.last_login);
                  const now = new Date();
                  const diffHours = (now - lastLogin) / (1000 * 60 * 60);
                  return diffHours <= 24;
                }).length}
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
                placeholder="Buscar por nome de usuário ou email..."
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
              <option value="active">Apenas Ativos</option>
              <option value="inactive">Apenas Inativos</option>
            </select>
            <button 
              onClick={() => loadUsers()}
              className="btn-secondary flex items-center"
              disabled={loading}
            >
              <ArrowPathIcon className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* Mensagem de Erro */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <p className="text-red-800">{error}</p>
          <button 
            onClick={() => loadUsers()} 
            className="mt-2 text-red-600 hover:text-red-800 underline"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* Lista de Usuários */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usuário
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sessões
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Último Login
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Membro desde
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center">
                    <div className="text-gray-500">
                      <UserIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p className="text-lg font-medium">Nenhum usuário encontrado</p>
                      <p className="mt-1">
                        {searchTerm ? 
                          'Tente ajustar os filtros de busca.' : 
                          'Não há usuários cadastrados no sistema.'
                        }
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr key={user.username} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-8 w-8">
                          <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                            <UserIcon className="h-4 w-4 text-primary-600" />
                          </div>
                        </div>
                        <div className="ml-3">
                          <div className="text-sm font-medium text-gray-900">
                            {user.username}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">
                        {user.email || 'Não informado'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(user.is_active)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {user.session_count || 0}
                      </div>
                      <div className="text-sm text-gray-500">sessões</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(user.last_login)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <button 
                          onClick={() => loadUserDetails(user.username)}
                          className="text-primary-600 hover:text-primary-900"
                          title="Ver detalhes"
                        >
                          <EyeIcon className="w-4 h-4" />
                        </button>
                        <button 
                          className="text-yellow-600 hover:text-yellow-900"
                          title="Editar"
                        >
                          <PencilIcon className="w-4 h-4" />
                        </button>
                        <button 
                          className="text-red-600 hover:text-red-900"
                          title="Excluir"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Paginação */}
        {pagination.total > pagination.limit && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={handlePrevPage}
                disabled={pagination.offset === 0}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Anterior
              </button>
              <button
                onClick={handleNextPage}
                disabled={!pagination.hasNext}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Próximo
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Mostrando{' '}
                  <span className="font-medium">{pagination.offset + 1}</span> até{' '}
                  <span className="font-medium">
                    {Math.min(pagination.offset + pagination.limit, pagination.total)}
                  </span>{' '}
                  de <span className="font-medium">{pagination.total}</span> usuários
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={handlePrevPage}
                    disabled={pagination.offset === 0}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={handleNextPage}
                    disabled={!pagination.hasNext}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Próximo
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal de Detalhes do Usuário */}
      {showUserDetails && selectedUser && (
        <UserDetailsModal 
          user={selectedUser} 
          onClose={() => {
            setShowUserDetails(false);
            setSelectedUser(null);
          }}
        />
      )}
    </div>
  );
};

// Componente Modal para Detalhes do Usuário
function UserDetailsModal({ user, onClose }) {
  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            Detalhes do Usuário: {user.username}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <span className="sr-only">Fechar</span>
            ✕
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Informações Básicas */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-3">Informações Básicas</h4>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-500">Username</dt>
                <dd className="text-sm font-medium text-gray-900">{user.username}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Email</dt>
                <dd className="text-sm font-medium text-gray-900">{user.email || 'Não informado'}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Status</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {user.is_active ? 'Ativo' : 'Inativo'}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Membro desde</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {new Date(user.created_at).toLocaleDateString('pt-BR')}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Último login</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {user.last_login ? new Date(user.last_login).toLocaleString('pt-BR') : 'Nunca'}
                </dd>
              </div>
            </dl>
          </div>

          {/* Estatísticas */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-3">Estatísticas</h4>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-500">Total de sessões</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {user.stats?.total_sessions || user.session_count || 0}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Sessões completadas</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {user.stats?.completed_sessions || 0}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Mensagens enviadas</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {user.stats?.total_messages || 0}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Tempo total (minutos)</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {user.stats?.total_time_minutes || 0}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Perfil completo</dt>
                <dd className="text-sm font-medium text-gray-900">
                  {user.profile_completed ? 'Sim' : 'Não'}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Preferências */}
        {user.preferences && (
          <div className="mt-6">
            <h4 className="text-md font-medium text-gray-900 mb-3">Preferências</h4>
            <div className="bg-gray-50 p-3 rounded-md">
              <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                {JSON.stringify(user.preferences, null, 2)}
              </pre>
            </div>
          </div>
        )}

        <div className="mt-6 flex justify-end">
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

export default UserManagement; 
