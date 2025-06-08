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

// Dados simulados para demonstração
const emotionData = [
  { name: 'Alegria', value: 35, color: '#10B981' },
  { name: 'Tristeza', value: 25, color: '#3B82F6' },
  { name: 'Ansiedade', value: 20, color: '#F59E0B' },
  { name: 'Raiva', value: 12, color: '#EF4444' },
  { name: 'Neutro', value: 8, color: '#6B7280' },
];

const sessionData = [
  { time: '00:00', sessions: 12 },
  { time: '04:00', sessions: 8 },
  { time: '08:00', sessions: 25 },
  { time: '12:00', sessions: 42 },
  { time: '16:00', sessions: 35 },
  { time: '20:00', sessions: 28 },
];

function StatsCard({ title, value, change, icon: Icon, trend }) {
  const isPositive = trend === 'up';
  
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
            </dd>
          </dl>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalUsers: 1247,
    activeSessions: 23,
    emotionsAnalyzed: 8924,
    systemAlerts: 2
  });

  const [realTimeData, setRealTimeData] = useState({
    currentEmotion: 'Neutro',
    confidence: 85,
    lastUpdate: new Date().toLocaleTimeString()
  });

  useEffect(() => {
    // Simular dados em tempo real
    const interval = setInterval(() => {
      const emotions = ['Alegria', 'Tristeza', 'Ansiedade', 'Neutro', 'Raiva'];
      const randomEmotion = emotions[Math.floor(Math.random() * emotions.length)];
      const randomConfidence = Math.floor(Math.random() * 40) + 60; // 60-100%
      
      setRealTimeData({
        currentEmotion: randomEmotion,
        confidence: randomConfidence,
        lastUpdate: new Date().toLocaleTimeString()
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

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
        />
        <StatsCard
          title="Sessões Ativas"
          value={stats.activeSessions}
          change="2%"
          icon={ChatBubbleLeftRightIcon}
          trend="up"
        />
        <StatsCard
          title="Emoções Analisadas"
          value={stats.emotionsAnalyzed}
          change="8%"
          icon={FaceSmileIcon}
          trend="up"
        />
        <StatsCard
          title="Alertas do Sistema"
          value={stats.systemAlerts}
          change="1"
          icon={ExclamationTriangleIcon}
          trend="down"
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Gráfico de Sessões */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Sessões por Horário</h3>
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
        </div>

        {/* Gráfico de Emoções */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Distribuição de Emoções</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={emotionData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {emotionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Seção de tempo real */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Atividade Recente</h3>
            <div className="space-y-3">
              {[
                { time: '14:23', user: 'Usuário #1247', emotion: 'Alegria', confidence: 92 },
                { time: '14:22', user: 'Usuário #1246', emotion: 'Ansiedade', confidence: 78 },
                { time: '14:21', user: 'Usuário #1245', emotion: 'Tristeza', confidence: 85 },
                { time: '14:20', user: 'Usuário #1244', emotion: 'Neutro', confidence: 67 },
                { time: '14:19', user: 'Usuário #1243', emotion: 'Alegria', confidence: 88 },
              ].map((activity, index) => (
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
          </div>
        </div>

        <div className="space-y-6">
          {/* Status em tempo real */}
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Status em Tempo Real</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Emoção Atual:</span>
                <span className="text-sm font-medium text-gray-900">{realTimeData.currentEmotion}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Confiança:</span>
                <span className="text-sm font-medium text-gray-900">{realTimeData.confidence}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Última Atualização:</span>
                <span className="text-sm font-medium text-gray-900">{realTimeData.lastUpdate}</span>
              </div>
            </div>
          </div>

          {/* Status do sistema */}
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Status do Sistema</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Gateway Service</span>
                <span className="status-online">Online</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Emotion Service</span>
                <span className="status-online">Online</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">AI Service</span>
                <span className="status-online">Online</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Avatar Service</span>
                <span className="status-online">Online</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Voice Service</span>
                <span className="status-error">Erro</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 