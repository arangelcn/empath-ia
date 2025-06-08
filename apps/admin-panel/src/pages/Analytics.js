import React, { useState } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';

const Analytics = () => {
  const [timeRange, setTimeRange] = useState('7d');

  // Dados simulados
  const emotionTrends = [
    { date: '2024-01-09', alegria: 35, tristeza: 20, ansiedade: 15, raiva: 10, neutro: 20 },
    { date: '2024-01-10', alegria: 42, tristeza: 18, ansiedade: 12, raiva: 8, neutro: 20 },
    { date: '2024-01-11', alegria: 38, tristeza: 22, ansiedade: 18, raiva: 12, neutro: 10 },
    { date: '2024-01-12', alegria: 45, tristeza: 15, ansiedade: 20, raiva: 5, neutro: 15 },
    { date: '2024-01-13', alegria: 52, tristeza: 12, ansiedade: 16, raiva: 8, neutro: 12 },
    { date: '2024-01-14', alegria: 48, tristeza: 18, ansiedade: 14, raiva: 6, neutro: 14 },
    { date: '2024-01-15', alegria: 55, tristeza: 10, ansiedade: 18, raiva: 7, neutro: 10 },
  ];

  const userEngagement = [
    { hour: '00:00', sessions: 5, duration: 12 },
    { hour: '02:00', sessions: 3, duration: 8 },
    { hour: '04:00', sessions: 2, duration: 15 },
    { hour: '06:00', sessions: 8, duration: 20 },
    { hour: '08:00', sessions: 25, duration: 25 },
    { hour: '10:00', sessions: 42, duration: 30 },
    { hour: '12:00', sessions: 58, duration: 22 },
    { hour: '14:00', sessions: 65, duration: 28 },
    { hour: '16:00', sessions: 48, duration: 18 },
    { hour: '18:00', sessions: 35, duration: 24 },
    { hour: '20:00', sessions: 28, duration: 32 },
    { hour: '22:00', sessions: 15, duration: 26 },
  ];

  const demographicData = [
    { name: '18-25', value: 25, color: '#3B82F6' },
    { name: '26-35', value: 35, color: '#10B981' },
    { name: '36-45', value: 20, color: '#F59E0B' },
    { name: '46-55', value: 15, color: '#EF4444' },
    { name: '55+', value: 5, color: '#8B5CF6' },
  ];

  const topEmotions = [
    { emotion: 'Alegria', count: 1247, percentage: 35.2, trend: '+12%' },
    { emotion: 'Tristeza', count: 892, percentage: 25.1, trend: '-3%' },
    { emotion: 'Ansiedade', count: 678, percentage: 19.1, trend: '+8%' },
    { emotion: 'Neutro', count: 456, percentage: 12.8, trend: '+2%' },
    { emotion: 'Raiva', count: 278, percentage: 7.8, trend: '-15%' },
  ];

  const MetricCard = ({ title, value, change, trend }) => {
    const isPositive = trend === 'up';
    
    return (
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-semibold text-gray-900">{value}</p>
            <p className={`text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {change} vs. período anterior
            </p>
          </div>
          <div className="h-8 w-8 bg-primary-600 rounded-full flex items-center justify-center">
            <span className="text-white text-xs">📊</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Análise detalhada do uso e performance do sistema
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="input-field w-auto"
          >
            <option value="1d">Hoje</option>
            <option value="7d">Últimos 7 dias</option>
            <option value="30d">Últimos 30 dias</option>
            <option value="90d">Últimos 90 dias</option>
          </select>
          <button className="btn-secondary flex items-center space-x-2">
            <span>📅</span>
            <span>Exportar Relatório</span>
          </button>
        </div>
      </div>

      {/* Métricas principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total de Sessões"
          value="3,542"
          change="+18.2%"
          trend="up"
        />
        <MetricCard
          title="Tempo Médio por Sessão"
          value="24.5min"
          change="+4.1%"
          trend="up"
        />
        <MetricCard
          title="Emoções Detectadas"
          value="12,847"
          change="+22.3%"
          trend="up"
        />
        <MetricCard
          title="Taxa de Satisfação"
          value="94.2%"
          change="+2.1%"
          trend="up"
        />
      </div>

      {/* Gráficos principais */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tendências de emoções */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Tendências Emocionais
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={emotionTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="alegria" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.6} />
              <Area type="monotone" dataKey="tristeza" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.6} />
              <Area type="monotone" dataKey="ansiedade" stackId="1" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.6} />
              <Area type="monotone" dataKey="raiva" stackId="1" stroke="#EF4444" fill="#EF4444" fillOpacity={0.6} />
              <Area type="monotone" dataKey="neutro" stackId="1" stroke="#6B7280" fill="#6B7280" fillOpacity={0.6} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Engajamento por horário */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Engajamento por Horário
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={userEngagement}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="sessions" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Segunda linha de gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Demografia dos usuários */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Demografia por Idade
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={demographicData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              >
                {demographicData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top emoções */}
        <div className="lg:col-span-2 card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Emoções Mais Detectadas
          </h3>
          <div className="space-y-3">
            {topEmotions.map((emotion, index) => (
              <div key={emotion.emotion} className="flex items-center justify-between py-2">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-3 h-3 rounded-full bg-primary-600"></div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{emotion.emotion}</p>
                    <p className="text-xs text-gray-500">{emotion.count} detecções</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">{emotion.percentage}%</p>
                  <p className={`text-xs ${
                    emotion.trend.startsWith('+') ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {emotion.trend}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Duração de sessões */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Duração Média das Sessões por Horário
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={userEngagement}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip formatter={(value) => [`${value} min`, 'Duração']} />
            <Line 
              type="monotone" 
              dataKey="duration" 
              stroke="#8B5CF6" 
              strokeWidth={3}
              dot={{ fill: '#8B5CF6', strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Insights automáticos */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Insights Automáticos
        </h3>
        <div className="space-y-3">
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">
              📈 <strong>Crescimento positivo:</strong> As sessões aumentaram 18.2% esta semana comparado à semana anterior.
            </p>
          </div>
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              😊 <strong>Emoção dominante:</strong> Alegria é a emoção mais detectada (35.2%), indicando um bom bem-estar geral dos usuários.
            </p>
          </div>
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              ⏰ <strong>Pico de uso:</strong> O horário de maior engajamento é às 14:00, com 65 sessões simultâneas.
            </p>
          </div>
          <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
            <p className="text-sm text-purple-800">
              👥 <strong>Demografia:</strong> A faixa etária de 26-35 anos representa 35% dos usuários ativos.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics; 