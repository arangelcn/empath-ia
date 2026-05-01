import React from 'react';
import { Cog6ToothIcon, ShieldCheckIcon, WrenchScrewdriverIcon } from '@heroicons/react/24/outline';
import { DataQualityBadge, UnavailableState } from '../components/AdminState';

const pendingContracts = [
  {
    title: 'Configurações gerais',
    description: 'Nome do sistema, descrição, idioma e fuso horário.',
    icon: Cog6ToothIcon,
  },
  {
    title: 'Segurança e privacidade',
    description: 'Sessão administrativa, retenção, anonimização e políticas sensíveis.',
    icon: ShieldCheckIcon,
  },
  {
    title: 'Operações do sistema',
    description: 'Manutenção, backup, cache, relatórios e ações de emergência.',
    icon: WrenchScrewdriverIcon,
  },
];

const Settings = () => (
  <div className="space-y-6">
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Configurações do Sistema</h1>
      <p className="mt-1 text-sm text-gray-500">
        Contratos de configuração administrativa
      </p>
      <div className="mt-2">
        <DataQualityBadge unavailableFields={['settings_read', 'settings_write', 'system_actions']} />
      </div>
    </div>

    <UnavailableState
      title="Configurações ainda sem backend"
      message="Esta página não exibe valores locais ou simulados. É necessário criar endpoints de leitura, atualização e auditoria antes de habilitar edição."
    />

    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      {pendingContracts.map(({ title, description, icon: Icon }) => (
        <div key={title} className="card">
          <Icon className="h-7 w-7 text-primary-600" />
          <h2 className="mt-4 text-base font-semibold text-gray-900">{title}</h2>
          <p className="mt-2 text-sm text-gray-600">{description}</p>
          <p className="mt-4 text-xs font-medium uppercase tracking-wide text-yellow-700">
            Endpoint pendente
          </p>
        </div>
      ))}
    </div>
  </div>
);

export default Settings;
