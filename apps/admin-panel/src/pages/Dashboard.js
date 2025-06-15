import React, { useState, useEffect } from 'react';
import { 
  UserGroupIcon, 
  ChatBubbleLeftRightIcon, 
  FaceSmileIcon, 
  ExclamationTriangleIcon,
  ArrowUpIcon,
  ArrowDownIcon
} from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import apiService from '../services/api';

// Dados simulados para o gráfico de sessões (será substituído por dados reais posteriormente)
const sessionData = [
  { time: '00:00', sessions: 12 },
  { time: '04:00', sessions: 8 },
  { time: '08:00', sessions: 25 },
  { time: '12:00', sessions: 42 },
  { time: '16:00', sessions: 35 },
  { time: '20:00', sessions: 28 },
];

function StatsCard({ title, value, change, icon: Icon, trend, isLoading }) {
  const isPositive = trend === 'up';
  
  if (isLoading) {
    return (
      <div className="card animate-pulse">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="h-8 w-8 bg-gray-300 rounded"></div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <div className="h-4 bg-gray-300 rounded mb-2"></div>
            <div className="h-6 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="card">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Icon className="h-8 w-8 text-primary-600" />
        </div>
        <div className="ml-5 w-0 flex-1">
          <dl>
            <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
            <dd className="flex items-baseline">
              <div className="text-2xl font-semibold text-gray-900">{value}</div>
              {change && (
                <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                  isPositive ? 'text-green-600' : 'text-red-600'
                }`}>
                  {isPositive ? (
                    <ArrowUpIcon className="self-center flex-shrink-0 h-4 w-4" />
                  ) : (
                    <ArrowDownIcon className="self-center flex-shrink-0 h-4 w-4" />
                  )}
                  <span className="sr-only">{isPositive ? 'Aumentou' : 'Diminuiu'} em </span>
                  {change}
                </div>
              )}
            </dd>
          </dl>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeSessions: 0,
    emotionsAnalyzed: 0,
    systemAlerts: 0
  });

  const [emotionData, setEmotionData] = useState([]);
  const [realTimeData, setRealTimeData] = useState({
    currentEmotion: 'Neutro',
    confidence: 0,
    lastUpdate: new Date().toLocaleTimeString()
  });
  
  const [recentActivities, setRecentActivities] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Carregar estatísticas do dashboard
      const statsResponse = await apiService.getDashboardStats();
      if (statsResponse.success) {
        setStats(statsResponse.data);
      }

      // Carregar análise de emoções
      const emotionsResponse = await apiService.getEmotionsAnalysis(7);
      if (emotionsResponse.success) {
        const emotionsData = emotionsResponse.data.distribution;
        const formattedEmotions = Object.entries(emotionsData).map(([name, value]) => ({
          name: name.charAt(0).toUpperCase() + name.slice(1),
          value: value,
          color: getEmotionColor(name)
        }));
        setEmotionData(formattedEmotions);
      }

      // Carregar atividade em tempo real
      const activityResponse = await apiService.getRealTimeActivity();
      if (activityResponse.success) {
        setRecentActivities(activityResponse.data.activities);
        
        // Atualizar dados em tempo real baseado na última atividade
        if (activityResponse.data.activities.length > 0) {
          const lastActivity = activityResponse.data.activities[0];
          setRealTimeData({
            currentEmotion: lastActivity.emotion,
            confidence: lastActivity.confidence,
            lastUpdate: new Date().toLocaleTimeString()
          });
        }
      }

    } catch (error) {
      console.error('Erro ao carregar dados do dashboard:', error);
      setError('Erro ao carregar dados. Verifique se o backend está rodando.');
      
      // Fallback para dados mockados em caso de erro
      setStats({
        totalUsers: 0,
        activeSessions: 0,
        emotionsAnalyzed: 0,
        systemAlerts: 1
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getEmotionColor = (emotion) => {
    const colors = {
      alegria: '#10B981',
      tristeza: '#3B82F6',
      ansiedade: '#F59E0B',
      raiva: '#EF4444',
      neutro: '#6B7280'
    };
    return colors[emotion] || '#6B7280';
  };

  useEffect(() => {
    loadDashboardData();

    // Atualizar dados a cada 30 segundos
    const interval = setInterval(() => {
      loadDashboardData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600">
            Visão geral do sistema de análise emocional
          </p>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Erro de Conexão</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <button 
                onClick={loadDashboardData}
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
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Visão geral do sistema de análise emocional
        </p>
      </div>

      {/* Cards de estatísticas */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Usuários Totais"
          value={stats.totalUsers}
          change="12%"
          icon={UserGroupIcon}
          trend="up"
          isLoading={isLoading}
        />
        <StatsCard
          title="Sessões Ativas"
          value={stats.activeSessions}
          change="2%"
          icon={ChatBubbleLeftRightIcon}
          trend="up"
          isLoading={isLoading}
        />
        <StatsCard
          title="Emoções Analisadas"
          value={stats.emotionsAnalyzed}
          change="8%"
          icon={FaceSmileIcon}
          trend="up"
          isLoading={isLoading}
        />
        <StatsCard
          title="Alertas do Sistema"
          value={stats.systemAlerts}
          change={stats.systemAlerts > 0 ? "1" : "0"}
          icon={ExclamationTriangleIcon}
          trend={stats.systemAlerts > 0 ? "up" : "down"}
          isLoading={isLoading}
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Gráfico de Sessões */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Sessões por Horário</h3>
          {isLoading ? (
            <div className="h-64 bg-gray-100 rounded animate-pulse"></div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={sessionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="sessions" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  dot={{ fill: '#3B82F6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Gráfico de Emoções */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Distribuição de Emoções</h3>
          {isLoading ? (
            <div className="h-64 bg-gray-100 rounded animate-pulse"></div>
          ) : emotionData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={emotionData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value }) => `${name} ${value}%`}
                >
                  {emotionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              Nenhum dado de emoção disponível
            </div>
          )}
        </div>
      </div>

      {/* Seção de tempo real */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Atividade Recente</h3>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="animate-pulse py-2 border-b border-gray-100">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="h-4 w-12 bg-gray-300 rounded"></div>
                        <div className="h-4 w-24 bg-gray-300 rounded"></div>
                      </div>
                      <div className="h-4 w-16 bg-gray-300 rounded"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : recentActivities.length > 0 ? (
              <div className="space-y-3">
                {recentActivities.map((activity, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                    <div className="flex items-center space-x-3">
                      <span className="text-sm text-gray-500">{activity.time}</span>
                      <span className="text-sm font-medium text-gray-900">{activity.user}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">Emoção: {activity.emotion}</span>
                      <span className="text-xs bg-primary-100 text-primary-800 px-2 py-1 rounded-full">
                        {activity.confidence}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                Nenhuma atividade recente
              </div>
            )}
          </div>
        </div>

        <div>
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Status em Tempo Real</h3>
            {isLoading ? (
              <div className="space-y-3">
                <div className="h-4 bg-gray-300 rounded animate-pulse"></div>
                <div className="h-4 bg-gray-300 rounded animate-pulse"></div>
                <div className="h-4 bg-gray-300 rounded animate-pulse"></div>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-600">Emoção Atual:</span>
                  <span className="ml-2 font-medium text-gray-900">{realTimeData.currentEmotion}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Confiança:</span>
                  <span className="ml-2 font-medium text-gray-900">{realTimeData.confidence}%</span>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Última Atualização:</span>
                  <span className="ml-2 text-sm text-gray-500">{realTimeData.lastUpdate}</span>
                </div>
                <div className="mt-4 p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                    <span className="text-sm text-green-800">Sistema Online</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 