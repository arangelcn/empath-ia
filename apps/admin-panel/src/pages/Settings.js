import React, { useState } from 'react';

const Settings = () => {
  const [settings, setSettings] = useState({
    // Configurações gerais
    systemName: 'Empath IA',
    systemDescription: 'Sistema de análise emocional em tempo real',
    timezone: 'America/Sao_Paulo',
    language: 'pt-BR',
    
    // Configurações de segurança
    sessionTimeout: 30,
    maxLoginAttempts: 5,
    requireTwoFactor: false,
    passwordExpiry: 90,
    
    // Configurações de notificação
    emailNotifications: true,
    systemAlerts: true,
    errorReports: true,
    maintenanceMode: false,
    
    // Configurações de performance
    maxConcurrentSessions: 100,
    cacheDuration: 3600,
    logLevel: 'info',
    backupFrequency: 'daily',
    
    // Configurações de privacidade
    dataRetention: 30,
    anonymizeData: true,
    shareAnalytics: false,
    
    // Configurações de API
    apiRateLimit: 1000,
    apiTimeout: 30,
    enableCors: true,
  });

  const [saved, setSaved] = useState(false);

  const handleInputChange = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleToggle = (key) => {
    setSettings(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleSave = () => {
    // Simular salvamento
    console.log('Configurações salvas:', settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const SettingCard = ({ emoji, title, children }) => (
    <div className="card">
      <div className="flex items-center space-x-3 mb-6">
        <span className="text-2xl">{emoji}</span>
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  );

  const InputField = ({ label, value, onChange, type = "text", ...props }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input-field"
        {...props}
      />
    </div>
  );

  const SelectField = ({ label, value, onChange, options }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="input-field"
      >
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );

  const ToggleField = ({ label, description, checked, onChange }) => (
    <div className="flex items-center justify-between">
      <div>
        <h4 className="text-sm font-medium text-gray-900">{label}</h4>
        {description && (
          <p className="text-sm text-gray-500">{description}</p>
        )}
      </div>
      <button
        type="button"
        className={`${
          checked ? 'bg-primary-600' : 'bg-gray-200'
        } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2`}
        onClick={onChange}
      >
        <span
          className={`${
            checked ? 'translate-x-5' : 'translate-x-0'
          } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
        />
      </button>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Configurações do Sistema</h1>
          <p className="mt-1 text-sm text-gray-500">
            Configure as opções gerais do sistema Empath IA
          </p>
        </div>
        <button
          onClick={handleSave}
          className={`btn-primary flex items-center space-x-2 ${
            saved ? 'bg-green-600 hover:bg-green-700' : ''
          }`}
        >
          {saved ? (
            <>
              <span>✅</span>
              <span>Salvo!</span>
            </>
          ) : (
            <span>Salvar Configurações</span>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configurações Gerais */}
        <SettingCard emoji="⚙️" title="Configurações Gerais">
          <InputField
            label="Nome do Sistema"
            value={settings.systemName}
            onChange={(value) => handleInputChange('general', 'systemName', value)}
          />
          <InputField
            label="Descrição"
            value={settings.systemDescription}
            onChange={(value) => handleInputChange('general', 'systemDescription', value)}
          />
          <SelectField
            label="Fuso Horário"
            value={settings.timezone}
            onChange={(value) => handleInputChange('general', 'timezone', value)}
            options={[
              { value: 'America/Sao_Paulo', label: 'São Paulo (GMT-3)' },
              { value: 'America/New_York', label: 'Nova York (GMT-5)' },
              { value: 'Europe/London', label: 'Londres (GMT+0)' },
              { value: 'UTC', label: 'UTC' },
            ]}
          />
          <SelectField
            label="Idioma"
            value={settings.language}
            onChange={(value) => handleInputChange('general', 'language', value)}
            options={[
              { value: 'pt-BR', label: 'Português (Brasil)' },
              { value: 'en-US', label: 'English (US)' },
              { value: 'es-ES', label: 'Español' },
            ]}
          />
        </SettingCard>

        {/* Configurações de Segurança */}
        <SettingCard emoji="🔒" title="Segurança">
          <InputField
            label="Timeout de Sessão (minutos)"
            type="number"
            value={settings.sessionTimeout}
            onChange={(value) => handleInputChange('security', 'sessionTimeout', parseInt(value))}
          />
          <InputField
            label="Máximo de Tentativas de Login"
            type="number"
            value={settings.maxLoginAttempts}
            onChange={(value) => handleInputChange('security', 'maxLoginAttempts', parseInt(value))}
          />
          <ToggleField
            label="Autenticação de Dois Fatores"
            description="Requer verificação adicional no login"
            checked={settings.requireTwoFactor}
            onChange={() => handleToggle('requireTwoFactor')}
          />
          <InputField
            label="Expiração de Senha (dias)"
            type="number"
            value={settings.passwordExpiry}
            onChange={(value) => handleInputChange('security', 'passwordExpiry', parseInt(value))}
          />
        </SettingCard>

        {/* Configurações de Notificação */}
        <SettingCard emoji="🔔" title="Notificações">
          <ToggleField
            label="Notificações por Email"
            description="Receber alertas por email"
            checked={settings.emailNotifications}
            onChange={() => handleToggle('emailNotifications')}
          />
          <ToggleField
            label="Alertas do Sistema"
            description="Mostrar alertas na interface"
            checked={settings.systemAlerts}
            onChange={() => handleToggle('systemAlerts')}
          />
          <ToggleField
            label="Relatórios de Erro"
            description="Enviar relatórios automáticos de erro"
            checked={settings.errorReports}
            onChange={() => handleToggle('errorReports')}
          />
          <ToggleField
            label="Modo de Manutenção"
            description="Bloquear acesso durante manutenção"
            checked={settings.maintenanceMode}
            onChange={() => handleToggle('maintenanceMode')}
          />
        </SettingCard>

        {/* Configurações de Performance */}
        <SettingCard emoji="⚡" title="Performance">
          <InputField
            label="Sessões Simultâneas Máximas"
            type="number"
            value={settings.maxConcurrentSessions}
            onChange={(value) => handleInputChange('performance', 'maxConcurrentSessions', parseInt(value))}
          />
          <InputField
            label="Duração do Cache (segundos)"
            type="number"
            value={settings.cacheDuration}
            onChange={(value) => handleInputChange('performance', 'cacheDuration', parseInt(value))}
          />
          <SelectField
            label="Nível de Log"
            value={settings.logLevel}
            onChange={(value) => handleInputChange('performance', 'logLevel', value)}
            options={[
              { value: 'debug', label: 'Debug' },
              { value: 'info', label: 'Info' },
              { value: 'warn', label: 'Warning' },
              { value: 'error', label: 'Error' },
            ]}
          />
          <SelectField
            label="Frequência de Backup"
            value={settings.backupFrequency}
            onChange={(value) => handleInputChange('performance', 'backupFrequency', value)}
            options={[
              { value: 'hourly', label: 'A cada hora' },
              { value: 'daily', label: 'Diário' },
              { value: 'weekly', label: 'Semanal' },
              { value: 'monthly', label: 'Mensal' },
            ]}
          />
        </SettingCard>

        {/* Configurações de Privacidade */}
        <SettingCard emoji="🔐" title="Privacidade">
          <InputField
            label="Retenção de Dados (dias)"
            type="number"
            value={settings.dataRetention}
            onChange={(value) => handleInputChange('privacy', 'dataRetention', parseInt(value))}
          />
          <ToggleField
            label="Anonimizar Dados"
            description="Remover informações pessoais dos logs"
            checked={settings.anonymizeData}
            onChange={() => handleToggle('anonymizeData')}
          />
          <ToggleField
            label="Compartilhar Analytics"
            description="Enviar dados de uso anonimizados"
            checked={settings.shareAnalytics}
            onChange={() => handleToggle('shareAnalytics')}
          />
        </SettingCard>

        {/* Configurações de API */}
        <SettingCard emoji="🔌" title="API">
          <InputField
            label="Rate Limit (requests/min)"
            type="number"
            value={settings.apiRateLimit}
            onChange={(value) => handleInputChange('api', 'apiRateLimit', parseInt(value))}
          />
          <InputField
            label="Timeout da API (segundos)"
            type="number"
            value={settings.apiTimeout}
            onChange={(value) => handleInputChange('api', 'apiTimeout', parseInt(value))}
          />
          <ToggleField
            label="Habilitar CORS"
            description="Permitir requests cross-origin"
            checked={settings.enableCors}
            onChange={() => handleToggle('enableCors')}
          />
        </SettingCard>
      </div>

      {/* Seção de Informações do Sistema */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
          <span>💻</span>
          <span>Informações do Sistema</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm font-medium text-gray-500">Versão</p>
            <p className="text-lg font-semibold text-gray-900">v2.1.0</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm font-medium text-gray-500">Última Atualização</p>
            <p className="text-lg font-semibold text-gray-900">15/01/2024</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm font-medium text-gray-500">Status</p>
            <p className="text-lg font-semibold text-green-600">Operacional</p>
          </div>
        </div>
      </div>

      {/* Ações de Sistema */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
          <span>🛠️</span>
          <span>Ações do Sistema</span>
        </h3>
        <div className="flex flex-wrap gap-3">
          <button className="btn-secondary">
            🔄 Reiniciar Serviços
          </button>
          <button className="btn-secondary">
            🗄️ Fazer Backup
          </button>
          <button className="btn-secondary">
            🧹 Limpar Cache
          </button>
          <button className="btn-secondary">
            📊 Gerar Relatório
          </button>
          <button className="btn-danger">
            🚨 Modo de Emergência
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings; 