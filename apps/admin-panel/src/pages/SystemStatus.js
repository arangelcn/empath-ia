import React, { useState, useEffect } from 'react';
import { 
  CpuChipIcon, 
  CircleStackIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import apiService from '../services/api';
import { DataQualityBadge, EmptyState, ErrorState, LoadingState, UnavailableState } from '../components/AdminState';

function StatusBadge({ status }) {
  const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
  
  switch (status) {
    case 'online':
      return (
        <span className={`${baseClasses} bg-green-100 text-green-800`}>
          <CheckCircleIcon className="h-3 w-3 mr-1" />
          Online
        </span>
      );
    case 'warning':
      return (
        <span className={`${baseClasses} bg-yellow-100 text-yellow-800`}>
          <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
          Aviso
        </span>
      );
    case 'error':
    case 'unreachable':
      return (
        <span className={`${baseClasses} bg-red-100 text-red-800`}>
          <XCircleIcon className="h-3 w-3 mr-1" />
          Erro
        </span>
      );
    default:
      return (
        <span className={`${baseClasses} bg-gray-100 text-gray-800`}>
          <ClockIcon className="h-3 w-3 mr-1" />
          Desconhecido
        </span>
      );
  }
}

function ProgressBar({ value, max = 100, color = 'primary' }) {
  const percentage = (value / max) * 100;
  const colorClasses = {
    primary: 'bg-primary-600',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500'
  };
  
  const bgColor = percentage > 80 ? 'red' : percentage > 60 ? 'yellow' : 'green';
  
  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div 
        className={`h-2 rounded-full ${colorClasses[bgColor]}`}
        style={{ width: `${Math.min(percentage, 100)}%` }}
      />
    </div>
  );
}

export default function SystemStatus() {
  const [servicesData, setServicesData] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [unavailableFields, setUnavailableFields] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadSystemStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getSystemStatus();
      if (!response.success) {
        throw new Error('Falha ao carregar status do sistema');
      }
      setServicesData(response.data.services || []);
      setMetrics(response.data.metrics || {});
      setAlerts(response.data.alerts || []);
      setUnavailableFields(response.data.unavailable_fields || []);
      setLastUpdate(response.data.last_updated ? new Date(response.data.last_updated) : new Date());
    } catch (err) {
      setError(apiService.formatError(err, 'Não foi possível carregar o status do sistema.'));
      setServicesData([]);
      setMetrics({});
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSystemStatus();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return undefined;
    const interval = setInterval(() => {
      loadSystemStatus();
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleRefresh = () => {
    loadSystemStatus();
  };

  const onlineServices = metrics.online_services ?? servicesData.filter(s => s.status === 'online').length;
  const totalServices = metrics.total_services ?? servicesData.length;

  if (loading && servicesData.length === 0) {
    return <LoadingState message="Carregando status real dos serviços..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Status do Sistema</h1>
          <p className="mt-1 text-sm text-gray-600">
            Monitoramento em tempo real dos serviços e recursos
          </p>
          <div className="mt-2">
            <DataQualityBadge unavailableFields={unavailableFields} />
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="autoRefresh"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="autoRefresh" className="ml-2 text-sm text-gray-700">
              Atualização automática
            </label>
          </div>
          <button
            onClick={handleRefresh}
            className="btn-secondary flex items-center"
            disabled={loading}
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Atualizar
          </button>
        </div>
      </div>

      {error && <ErrorState message={error} onRetry={loadSystemStatus} />}

      {/* Resumo Geral */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Serviços Online</p>
              <p className="text-2xl font-semibold text-gray-900">
                {onlineServices}/{totalServices}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CpuChipIcon className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Requisições Totais</p>
              <p className="text-2xl font-semibold text-gray-900">
                {(metrics.total_requests ?? 0).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClockIcon className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Tempo de Resposta</p>
              <p className="text-2xl font-semibold text-gray-900">
                {metrics.avg_response_time_ms === null || metrics.avg_response_time_ms === undefined ? 'Indisponível' : `${metrics.avg_response_time_ms}ms`}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CircleStackIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Usuários Ativos</p>
              <p className="text-2xl font-semibold text-gray-900">
                {metrics.active_users ?? 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Status dos Serviços */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-gray-900">Status dos Serviços</h2>
          <p className="text-sm text-gray-500">
            Última atualização: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Serviço
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Uptime
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  CPU
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Memória
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Requisições
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {servicesData.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8">
                    <EmptyState title="Nenhum serviço retornado" message="O endpoint de status não retornou serviços monitorados." />
                  </td>
                </tr>
              ) : servicesData.map((service) => (
                <tr key={service.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{service.name}</div>
                      <div className="text-sm text-gray-500">{service.url}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={service.status} />
                    {service.error && (
                      <div className="text-xs text-red-600 mt-1">{service.error}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {service.uptime || 'Indisponível'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {service.cpu !== undefined && service.cpu !== null ? (
                      <div className="flex items-center">
                        <div className="flex-1 mr-3">
                          <ProgressBar value={service.cpu} />
                        </div>
                        <span className="text-sm text-gray-900">{service.cpu}%</span>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-500">Indisponível</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {service.memory ? `${service.memory}MB` : 'Indisponível'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {service.requests !== undefined ? service.requests.toLocaleString() : service.response_time_ms ? `${service.response_time_ms}ms` : 'Indisponível'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <span className="text-gray-500">Sem endpoint operacional</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Métricas do Sistema */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Métricas de Performance</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">Uso de Disco</span>
                <span className="text-sm text-gray-500">{metrics.disk_usage ?? 'Indisponível'}</span>
              </div>
              {metrics.disk_usage !== null && metrics.disk_usage !== undefined ? <ProgressBar value={metrics.disk_usage} /> : <UnavailableState title="Uso de disco indisponível" />}
            </div>
            
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">Taxa de Erro</span>
                <span className="text-sm text-gray-500">{metrics.error_rate ?? 'Indisponível'}</span>
              </div>
              {metrics.error_rate !== null && metrics.error_rate !== undefined ? <ProgressBar value={metrics.error_rate} max={5} /> : <UnavailableState title="Taxa de erro indisponível" />}
            </div>
            
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">Latência de Rede</span>
                <span className="text-sm text-gray-500">{metrics.network_latency_ms ?? 'Indisponível'}</span>
              </div>
              {metrics.network_latency_ms !== null && metrics.network_latency_ms !== undefined ? <ProgressBar value={metrics.network_latency_ms} max={100} /> : <UnavailableState title="Latência de rede indisponível" />}
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Alertas Recentes</h3>
          {alerts.length > 0 ? (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div key={`${alert.service}-${alert.message}`} className="flex items-start space-x-3">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{alert.message}</p>
                    <p className="text-sm text-gray-500">{alert.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="Nenhum alerta real" message="Todos os health checks disponíveis responderam sem falhas." />
          )}
        </div>
      </div>
    </div>
  );
} 
