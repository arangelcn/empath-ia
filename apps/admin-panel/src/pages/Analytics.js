import React, { useEffect, useState } from 'react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
} from 'recharts';
import apiService from '../services/api';
import { DataQualityBadge, EmptyState, ErrorState, LoadingState, UnavailableState } from '../components/AdminState';

const EMOTION_COLORS = {
  alegria: '#10B981',
  tristeza: '#3B82F6',
  ansiedade: '#F59E0B',
  raiva: '#EF4444',
  neutro: '#6B7280',
};

const timeRangeToDays = {
  '1d': 1,
  '7d': 7,
  '30d': 30,
  '90d': 90,
};

const formatMetric = (value, suffix = '') => {
  if (value === null || value === undefined) return 'Indisponível';
  return `${value.toLocaleString('pt-BR')}${suffix}`;
};

const MetricCard = ({ title, value, unavailable }) => (
  <div className="card">
    <div>
      <p className="text-sm font-medium text-gray-600">{title}</p>
      <p className={`text-2xl font-semibold ${unavailable ? 'text-gray-500' : 'text-gray-900'}`}>
        {value}
      </p>
      <p className="text-sm text-gray-500">
        {unavailable ? 'Sem contrato backend' : 'Fonte: dados persistidos'}
      </p>
    </div>
  </div>
);

const Analytics = () => {
  const [timeRange, setTimeRange] = useState('7d');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getAnalytics(timeRangeToDays[timeRange]);
      if (!response.success) {
        throw new Error('Falha ao carregar analytics');
      }
      setData(response.data);
    } catch (err) {
      setError(apiService.formatError(err, 'Não foi possível carregar analytics.'));
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  if (loading && !data) {
    return <LoadingState message="Carregando analytics reais..." />;
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Header timeRange={timeRange} setTimeRange={setTimeRange} unavailableFields={[]} />
        <ErrorState message={error} onRetry={loadAnalytics} />
      </div>
    );
  }

  const metrics = data?.metrics || {};
  const unavailableFields = data?.unavailable_fields || [];
  const hasTrends = Boolean(data?.emotion_trends?.length);
  const hasEngagement = Boolean(data?.engagement_by_hour?.length);
  const hasTopEmotions = Boolean(data?.top_emotions?.length);

  return (
    <div className="space-y-6">
      <Header timeRange={timeRange} setTimeRange={setTimeRange} unavailableFields={unavailableFields} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Total de Sessões" value={formatMetric(metrics.total_sessions)} />
        <MetricCard
          title="Tempo Médio por Sessão"
          value={formatMetric(metrics.avg_session_duration_minutes, 'min')}
          unavailable={metrics.avg_session_duration_minutes === null || metrics.avg_session_duration_minutes === undefined}
        />
        <MetricCard title="Emoções Detectadas" value={formatMetric(metrics.emotions_detected)} />
        <MetricCard
          title="Taxa de Satisfação"
          value={formatMetric(metrics.satisfaction_rate, '%')}
          unavailable={metrics.satisfaction_rate === null || metrics.satisfaction_rate === undefined}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tendências Emocionais</h3>
          {hasTrends ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={data.emotion_trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                {Object.entries(EMOTION_COLORS).map(([emotion, color]) => (
                  <Area
                    key={emotion}
                    type="monotone"
                    dataKey={emotion}
                    stackId="1"
                    stroke={color}
                    fill={color}
                    fillOpacity={0.6}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="Sem tendência emocional" message="Nenhuma emoção real foi registrada no período selecionado." />
          )}
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Engajamento por Horário</h3>
          {hasEngagement ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.engagement_by_hour}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="sessions" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="Sem engajamento registrado" message="Nenhuma conversa real foi atualizada no período selecionado." />
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Demografia por Idade</h3>
          <UnavailableState
            title="Demografia indisponível"
            message="A base de usuários atual não possui contrato de idade ou faixa etária."
          />
        </div>

        <div className="lg:col-span-2 card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Emoções Mais Detectadas</h3>
          {hasTopEmotions ? (
            <div className="space-y-3">
              {data.top_emotions.map((emotion) => (
                <div key={emotion.emotion} className="flex items-center justify-between py-2">
                  <div className="flex items-center space-x-3">
                    <div
                      className="flex-shrink-0 w-3 h-3 rounded-full"
                      style={{ backgroundColor: EMOTION_COLORS[emotion.emotion] || '#6B7280' }}
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {emotion.emotion.charAt(0).toUpperCase() + emotion.emotion.slice(1)}
                      </p>
                      <p className="text-xs text-gray-500">{emotion.count} detecções</p>
                    </div>
                  </div>
                  <p className="text-sm font-semibold text-gray-900">{emotion.percentage}%</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="Sem emoções detectadas" message="Nenhum evento real de emoção existe para o período." />
          )}
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Duração Média das Sessões por Horário
        </h3>
        <UnavailableState
          title="Duração média indisponível"
          message="As conversas ainda não persistem duração calculada por janela de horário."
        />
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Insights Automáticos</h3>
        <UnavailableState
          title="Insights indisponíveis"
          message="Nenhum serviço backend gera insights operacionais auditáveis neste momento."
        />
      </div>
    </div>
  );
};

function Header({ timeRange, setTimeRange, unavailableFields }) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="mt-1 text-sm text-gray-500">
          Análise detalhada do uso e performance do sistema
        </p>
        <div className="mt-2">
          <DataQualityBadge unavailableFields={unavailableFields} />
        </div>
      </div>

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
    </div>
  );
}

export default Analytics;
