import React, { useState } from 'react';
import {
  UserGroupIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  UserIcon,
} from '@heroicons/react/24/outline';

const UserManagement = () => {
  const [users, setUsers] = useState([
    {
      id: 1,
      name: 'João Silva',
      email: 'joao@example.com',
      role: 'admin',
      status: 'active',
      lastLogin: '2024-01-15 10:30',
      sessionsCount: 45,
      joinedAt: '2023-12-01',
    },
    {
      id: 2,
      name: 'Maria Santos',
      email: 'maria@example.com',
      role: 'user',
      status: 'active',
      lastLogin: '2024-01-15 14:22',
      sessionsCount: 23,
      joinedAt: '2024-01-10',
    },
    {
      id: 3,
      name: 'Pedro Costa',
      email: 'pedro@example.com',
      role: 'moderator',
      status: 'inactive',
      lastLogin: '2024-01-10 09:15',
      sessionsCount: 12,
      joinedAt: '2024-01-05',
    },
    {
      id: 4,
      name: 'Ana Lima',
      email: 'ana@example.com',
      role: 'user',
      status: 'active',
      lastLogin: '2024-01-15 16:45',
      sessionsCount: 67,
      joinedAt: '2023-11-20',
    },
  ]);

  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = filterRole === 'all' || user.role === filterRole;
    const matchesStatus = filterStatus === 'all' || user.status === filterStatus;
    
    return matchesSearch && matchesRole && matchesStatus;
  });

  const getRoleBadge = (role) => {
    const roleConfig = {
      admin: { bg: 'bg-red-100', text: 'text-red-800', label: 'Admin' },
      moderator: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Moderador' },
      user: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Usuário' },
    };
    
    const config = roleConfig[role] || roleConfig.user;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  const getStatusBadge = (status) => {
    if (status === 'active') {
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

  const handleDeleteUser = (userId) => {
    if (window.confirm('Tem certeza que deseja excluir este usuário?')) {
      setUsers(users.filter(user => user.id !== userId));
    }
  };

  const handleEditUser = (userId) => {
    // Implementar edição de usuário
    console.log('Editar usuário:', userId);
  };

  const handleViewUser = (userId) => {
    // Implementar visualização detalhada do usuário
    console.log('Ver usuário:', userId);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gerenciamento de Usuários</h1>
          <p className="mt-1 text-sm text-gray-500">
            Gerencie usuários do sistema Empath IA
          </p>
        </div>
        <button className="btn-primary flex items-center space-x-2">
          <PlusIcon className="h-4 w-4" />
          <span>Novo Usuário</span>
        </button>
      </div>

      {/* Filtros e busca */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por nome ou email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 input-field"
              />
            </div>
          </div>
          
          <div>
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              className="input-field"
            >
              <option value="all">Todas as funções</option>
              <option value="admin">Admin</option>
              <option value="moderator">Moderador</option>
              <option value="user">Usuário</option>
            </select>
          </div>

          <div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input-field"
            >
              <option value="all">Todos os status</option>
              <option value="active">Ativo</option>
              <option value="inactive">Inativo</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tabela de usuários */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usuário
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Função
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Último Login
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sessões
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-full bg-primary-600 flex items-center justify-center">
                          <UserIcon className="h-6 w-6 text-white" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{user.name}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getRoleBadge(user.role)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(user.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.lastLogin}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.sessionsCount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleViewUser(user.id)}
                        className="text-primary-600 hover:text-primary-900"
                        title="Ver detalhes"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleEditUser(user.id)}
                        className="text-yellow-600 hover:text-yellow-900"
                        title="Editar"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteUser(user.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Excluir"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredUsers.length === 0 && (
          <div className="text-center py-8">
            <UserGroupIcon className="mx-auto h-12 w-12 text-gray-300" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhum usuário encontrado</h3>
            <p className="mt-1 text-sm text-gray-500">
              Tente ajustar os filtros de busca.
            </p>
          </div>
        )}
      </div>

      {/* Estatísticas rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card text-center">
          <div className="text-2xl font-bold text-primary-600">{users.length}</div>
          <div className="text-sm text-gray-500">Total de Usuários</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-green-600">
            {users.filter(u => u.status === 'active').length}
          </div>
          <div className="text-sm text-gray-500">Usuários Ativos</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-red-600">
            {users.filter(u => u.role === 'admin').length}
          </div>
          <div className="text-sm text-gray-500">Administradores</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-yellow-600">
            {users.filter(u => u.role === 'moderator').length}
          </div>
          <div className="text-sm text-gray-500">Moderadores</div>
        </div>
      </div>
    </div>
  );
};

export default UserManagement; 