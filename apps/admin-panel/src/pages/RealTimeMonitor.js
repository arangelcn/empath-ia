import React, { useState, useEffect } from 'react';
import { ChartBarIcon, UserIcon, FaceSmileIcon, PlayIcon, PauseIcon } from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const emotions = ['joy', 'sadness', 'anxiety', 'anger', 'neutral', 'surprise'];
const emotionColors = {
  joy: '#10B981',
  sadness: '#3B82F6', 
  anxiety: '#F59E0B',
  anger: '#EF4444',
  neutral: '#6B7280',
  surprise: '#8B5CF6'
};

export default function RealTimeMonitor() {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [currentSession, setCurrentSession] = useState(null);
  const [emotionData, setEmotionData] = useState([]);
  const [sessions, setSessions] = useState([
    { id: 1, user: 'Usuário #1247', startTime: new Date(Date.now() - 300000), status: 'active' },
    { id: 2, user: 'Usuário #1246', startTime: new Date(Date.now() - 600000), status: 'active' },
    { id: 3, user: 'Usuário #1245', startTime: new Date(Date.now() - 900000), status: 'ended' },
  ]);

  const [realTimeStats, setRealTimeStats] = useState({
    currentEmotion: 'neutral',
    confidence: 0,
    avgConfidence: 0,
    emotionChanges: 0,
    sessionDuration: 0
  });

  useEffect(() => {
    let interval;
    
    if (isMonitoring && currentSession) {
      interval = setInterval(() => {
        const now = new Date();
        const emotion = emotions[Math.floor(Math.random() * emotions.length)];
        const confidence = Math.floor(Math.random() * 40) + 60; // 60-100%
        
        const newDataPoint = {
          time: now.toLocaleTimeString(),
          timestamp: now.getTime(),
          [emotion]: confidence,
          emotion,
          confidence
        };

        setEmotionData(prev => {
          const newData = [...prev, newDataPoint];
          return newData.slice(-20); // Manter apenas os últimos 20 pontos
        });

        setRealTimeStats(prev => ({
          currentEmotion: emotion,
          confidence,
          avgConfidence: Math.round((prev.avgConfidence + confidence) / 2),
          emotionChanges: prev.emotionChanges + (prev.currentEmotion !== emotion ? 1 : 0),
          sessionDuration: Math.floor((now - currentSession.startTime) / 1000)
        }));
      }, 2000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isMonitoring, currentSession]);

  const handleStartMonitoring = (session) => {
    setCurrentSession(session);
    setIsMonitoring(true);
    setEmotionData([]);
    setRealTimeStats({
      currentEmotion: 'neutral',
      confidence: 0,
      avgConfidence: 0,
      emotionChanges: 0,
      sessionDuration: 0
    });
  };

  const handleStopMonitoring = () => {
    setIsMonitoring(false);
    setCurrentSession(null);
  };

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getEmotionIcon = (emotion) => {
    switch (emotion) {
      case 'joy': return '😊';
      case 'sadness': return '😢';
      case 'anxiety': return '😰';
      case 'anger': return '😠';
      case 'surprise': return '😲';
      default: return '😐';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Monitor em Tempo Real</h1>
        <p className="mt-1 text-sm text-gray-600">
          Acompanhe as emoções dos usuários em tempo real
        </p>
      </div>

      {/* Sessões Ativas */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Sessões Ativas</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sessions.filter(s => s.status === 'active').map(session => (
            <div key={session.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <UserIcon className="h-5 w-5 text-gray-500" />
                  <span className="text-sm font-medium">{session.user}</span>
                </div>
                <span className="text-xs text-gray-500">
                  {Math.floor((Date.now() - session.startTime) / 60000)}min
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">
                  Iniciado às {session.startTime.toLocaleTimeString()}
                </span>
                {currentSession?.id === session.id ? (
                  <button
                    onClick={handleStopMonitoring}
                    className="flex items-center px-3 py-1 bg-red-100 text-red-700 rounded-md text-xs hover:bg-red-200"
                  >
                    <PauseIcon className="h-3 w-3 mr-1" />
                    Parar
                  </button>
                ) : (
                  <button
                    onClick={() => handleStartMonitoring(session)}
                    className="flex items-center px-3 py-1 bg-primary-100 text-primary-700 rounded-md text-xs hover:bg-primary-200"
                  >
                    <PlayIcon className="h-3 w-3 mr-1" />
                    Monitorar
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {isMonitoring && currentSession && (
        <>
          {/* Status da Sessão Atual */}
          <div className="card bg-primary-50">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">
                Monitorando: {currentSession.user}
              </h2>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600">Ao vivo</span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-2xl mb-1">{getEmotionIcon(realTimeStats.currentEmotion)}</div>
                <div className="text-sm font-medium text-gray-900">Emoção Atual</div>
                <div className="text-xs text-gray-600 capitalize">{realTimeStats.currentEmotion}</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-primary-600 mb-1">
                  {realTimeStats.confidence}%
                </div>
                <div className="text-sm font-medium text-gray-900">Confiança</div>
                <div className="text-xs text-gray-600">Atual</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600 mb-1">
                  {realTimeStats.avgConfidence}%
                </div>
                <div className="text-sm font-medium text-gray-900">Confiança Média</div>
                <div className="text-xs text-gray-600">Sessão</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600 mb-1">
                  {realTimeStats.emotionChanges}
                </div>
                <div className="text-sm font-medium text-gray-900">Mudanças</div>
                <div className="text-xs text-gray-600">Emocionais</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 mb-1">
                  {formatDuration(realTimeStats.sessionDuration)}
                </div>
                <div className="text-sm font-medium text-gray-900">Duração</div>
                <div className="text-xs text-gray-600">Sessão</div>
              </div>
            </div>
          </div>

          {/* Gráfico de Emoções em Tempo Real */}
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Fluxo Emocional</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={emotionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="time"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis 
                    domain={[0, 100]}
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip 
                    formatter={(value, name) => [`${value}%`, `Confiança`]}
                    labelFormatter={(time) => `Horário: ${time}`}
                  />
                  <Area
                    type="monotone"
                    dataKey="confidence"
                    stroke="#3B82F6"
                    fill="#3B82F6"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Timeline de Emoções */}
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Timeline de Emoções</h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {emotionData.slice().reverse().map((point, index) => (
                <div key={index} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <span className="text-xl">{getEmotionIcon(point.emotion)}</span>
                    <div>
                      <span className="text-sm font-medium capitalize">{point.emotion}</span>
                      <div className="text-xs text-gray-500">{point.time}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">{point.confidence}%</div>
                    <div className="text-xs text-gray-500">confiança</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {!isMonitoring && (
        <div className="card text-center py-12">
          <ChartBarIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Nenhuma sessão sendo monitorada
          </h3>
          <p className="text-gray-600 mb-4">
            Selecione uma sessão ativa acima para começar o monitoramento em tempo real
          </p>
        </div>
      )}

      {/* Histórico de Sessões */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Histórico de Sessões</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usuário
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Início
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duração
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Emoção Dominante
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sessions.map((session) => (
                <tr key={session.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {session.user}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {session.startTime.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {Math.floor((Date.now() - session.startTime) / 60000)}min
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      session.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {session.status === 'active' ? 'Ativa' : 'Finalizada'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex items-center space-x-2">
                      <span>{getEmotionIcon('joy')}</span>
                      <span>Alegria (78%)</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
} 