import React, { useState, useEffect } from 'react';
import { 
  CpuChipIcon, 
  CircleStackIcon, 
  CloudIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

const services = [
  { 
    id: 'gateway', 
    name: 'Gateway Service', 
    status: 'online', 
    url: 'http://localhost:8000',
    uptime: '2d 14h 32m',
    lastCheck: new Date().toLocaleTimeString(),
    cpu: 15,
    memory: 342,
    requests: 1247
  },
  { 
    id: 'emotion', 
    name: 'Emotion Service', 
    status: 'online', 
    url: 'http://localhost:8003',
    uptime: '2d 14h 30m',
    lastCheck: new Date().toLocaleTimeString(),
    cpu: 45,
    memory: 512,
    requests: 892
  },
  { 
    id: 'ai', 
    name: 'AI Service', 
    status: 'online', 
    url: 'http://localhost:8001',
    uptime: '2d 14h 28m',
    lastCheck: new Date().toLocaleTimeString(),
    cpu: 65,
    memory: 1024,
    requests: 2134
  },
  { 
    id: 'avatar', 
    name: 'Avatar Service', 
    status: 'online', 
    url: 'http://localhost:8002',
    uptime: '2d 14h 25m',
    lastCheck: new Date().toLocaleTimeString(),
    cpu: 25,
    memory: 256,
    requests: 567
  },
  { 
    id: 'voice', 
    name: 'Voice Service', 
    status: 'error', 
    url: 'http://localhost:8004',
    uptime: '0d 0h 0m',
    lastCheck: new Date().toLocaleTimeString(),
    cpu: 0,
    memory: 0,
    requests: 0,
    error: 'Connection refused'
  }
];

const systemMetrics = {
  totalRequests: 4840,
  avgResponseTime: 245,
  errorRate: 0.8,
  activeUsers: 23,
  diskUsage: 67,
  networkLatency: 12
};

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
  const [servicesData, setServicesData] = useState(services);
  const [metrics, setMetrics] = useState(systemMetrics);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Simular atualizações em tempo real
      setServicesData(prev => prev.map(service => ({
        ...service,
        lastCheck: new Date().toLocaleTimeString(),
        cpu: service.status === 'online' ? Math.max(5, Math.min(95, service.cpu + (Math.random() - 0.5) * 10)) : 0,
        memory: service.status === 'online' ? Math.max(50, Math.min(2048, service.memory + (Math.random() - 0.5) * 50)) : 0,
        requests: service.status === 'online' ? service.requests + Math.floor(Math.random() * 10) : 0
      })));

      setMetrics(prev => ({
        ...prev,
        totalRequests: prev.totalRequests + Math.floor(Math.random() * 20),
        avgResponseTime: Math.max(100, Math.min(1000, prev.avgResponseTime + (Math.random() - 0.5) * 50)),
        activeUsers: Math.max(0, Math.min(100, prev.activeUsers + Math.floor((Math.random() - 0.5) * 3)))
      }));

      setLastUpdate(new Date());
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleRefresh = () => {
    setLastUpdate(new Date());
    // Simular refresh manual
  };

  const handleServiceAction = (serviceId, action) => {
    setServicesData(prev => prev.map(service => 
      service.id === serviceId 
        ? { 
            ...service, 
            status: action === 'restart' ? 'online' : (action === 'stop' ? 'offline' : service.status),
            lastCheck: new Date().toLocaleTimeString()
          }
        : service
    ));
  };

  const onlineServices = servicesData.filter(s => s.status === 'online').length;
  const totalServices = servicesData.length;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Status do Sistema</h1>
          <p className="mt-1 text-sm text-gray-600">
            Monitoramento em tempo real dos serviços e recursos
          </p>
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
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Atualizar
          </button>
        </div>
      </div>

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
                {metrics.totalRequests.toLocaleString()}
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
                {metrics.avgResponseTime}ms
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
                {metrics.activeUsers}
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
              {servicesData.map((service) => (
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
                    {service.uptime}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-1 mr-3">
                        <ProgressBar value={service.cpu} />
                      </div>
                      <span className="text-sm text-gray-900">{service.cpu}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{service.memory}MB</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {service.requests.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      {service.status === 'online' && (
                        <button
                          onClick={() => handleServiceAction(service.id, 'restart')}
                          className="text-yellow-600 hover:text-yellow-900"
                        >
                          Reiniciar
                        </button>
                      )}
                      {service.status === 'error' && (
                        <button
                          onClick={() => handleServiceAction(service.id, 'start')}
                          className="text-green-600 hover:text-green-900"
                        >
                          Iniciar
                        </button>
                      )}
                    </div>
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
                <span className="text-sm text-gray-500">{metrics.diskUsage}%</span>
              </div>
              <ProgressBar value={metrics.diskUsage} />
            </div>
            
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">Taxa de Erro</span>
                <span className="text-sm text-gray-500">{metrics.errorRate}%</span>
              </div>
              <ProgressBar value={metrics.errorRate} max={5} />
            </div>
            
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">Latência de Rede</span>
                <span className="text-sm text-gray-500">{metrics.networkLatency}ms</span>
              </div>
              <ProgressBar value={metrics.networkLatency} max={100} />
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Alertas Recentes</h3>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-900">Alto uso de CPU no AI Service</p>
                <p className="text-sm text-gray-500">há 5 minutos</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <XCircleIcon className="h-5 w-5 text-red-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-900">Voice Service offline</p>
                <p className="text-sm text-gray-500">há 2 horas</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <CheckCircleIcon className="h-5 w-5 text-green-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-gray-900">Sistema de backup executado com sucesso</p>
                <p className="text-sm text-gray-500">há 6 horas</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 