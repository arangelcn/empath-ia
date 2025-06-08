import React, { useState } from 'react';
import { 
  FaceSmileIcon, 
  FaceFrownIcon, 
  ExclamationTriangleIcon,
  HeartIcon,
  FireIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const emotionTypes = [
  { id: 'joy', name: 'Alegria', icon: FaceSmileIcon, color: 'text-green-600', bgColor: 'bg-green-50' },
  { id: 'sadness', name: 'Tristeza', icon: FaceFrownIcon, color: 'text-blue-600', bgColor: 'bg-blue-50' },
  { id: 'anxiety', name: 'Ansiedade', icon: ExclamationTriangleIcon, color: 'text-yellow-600', bgColor: 'bg-yellow-50' },
  { id: 'anger', name: 'Raiva', icon: FireIcon, color: 'text-red-600', bgColor: 'bg-red-50' },
  { id: 'love', name: 'Amor', icon: HeartIcon, color: 'text-pink-600', bgColor: 'bg-pink-50' },
  { id: 'surprise', name: 'Surpresa', icon: SparklesIcon, color: 'text-purple-600', bgColor: 'bg-purple-50' },
];

export default function EmotionSettings() {
  const [settings, setSettings] = useState({
    joy: { threshold: 75, sensitivity: 80, enabled: true },
    sadness: { threshold: 65, sensitivity: 70, enabled: true },
    anxiety: { threshold: 60, sensitivity: 85, enabled: true },
    anger: { threshold: 70, sensitivity: 75, enabled: true },
    love: { threshold: 80, sensitivity: 60, enabled: false },
    surprise: { threshold: 55, sensitivity: 90, enabled: true },
  });

  const [globalSettings, setGlobalSettings] = useState({
    autoDetection: true,
    realTimeAnalysis: true,
    confidenceThreshold: 70,
    analysisInterval: 2000, // ms
    maxEmotionsPerAnalysis: 3,
  });

  const handleEmotionSettingChange = (emotionId, field, value) => {
    setSettings(prev => ({
      ...prev,
      [emotionId]: {
        ...prev[emotionId],
        [field]: value
      }
    }));
  };

  const handleGlobalSettingChange = (field, value) => {
    setGlobalSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = () => {
    // Aqui você salvaria as configurações
    alert('Configurações salvas com sucesso!');
  };

  const handleReset = () => {
    if (window.confirm('Tem certeza que deseja restaurar as configurações padrão?')) {
      setSettings({
        joy: { threshold: 75, sensitivity: 80, enabled: true },
        sadness: { threshold: 65, sensitivity: 70, enabled: true },
        anxiety: { threshold: 60, sensitivity: 85, enabled: true },
        anger: { threshold: 70, sensitivity: 75, enabled: true },
        love: { threshold: 80, sensitivity: 60, enabled: false },
        surprise: { threshold: 55, sensitivity: 90, enabled: true },
      });
      setGlobalSettings({
        autoDetection: true,
        realTimeAnalysis: true,
        confidenceThreshold: 70,
        analysisInterval: 2000,
        maxEmotionsPerAnalysis: 3,
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Configurações de Emoção</h1>
        <p className="mt-1 text-sm text-gray-600">
          Configure como o sistema detecta e processa diferentes emoções
        </p>
      </div>

      {/* Configurações Globais */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Configurações Globais</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={globalSettings.autoDetection}
                onChange={(e) => handleGlobalSettingChange('autoDetection', e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">Detecção Automática</span>
            </label>
            <p className="mt-1 text-sm text-gray-500">Ativar detecção automática de emoções</p>
          </div>

          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={globalSettings.realTimeAnalysis}
                onChange={(e) => handleGlobalSettingChange('realTimeAnalysis', e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">Análise em Tempo Real</span>
            </label>
            <p className="mt-1 text-sm text-gray-500">Processar emoções em tempo real</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Limite de Confiança Global: {globalSettings.confidenceThreshold}%
            </label>
            <input
              type="range"
              min="50"
              max="95"
              value={globalSettings.confidenceThreshold}
              onChange={(e) => handleGlobalSettingChange('confidenceThreshold', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>50%</span>
              <span>95%</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Intervalo de Análise: {globalSettings.analysisInterval}ms
            </label>
            <input
              type="range"
              min="500"
              max="5000"
              step="500"
              value={globalSettings.analysisInterval}
              onChange={(e) => handleGlobalSettingChange('analysisInterval', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0.5s</span>
              <span>5s</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Máximo de Emoções por Análise
            </label>
            <select
              value={globalSettings.maxEmotionsPerAnalysis}
              onChange={(e) => handleGlobalSettingChange('maxEmotionsPerAnalysis', parseInt(e.target.value))}
              className="input-field"
            >
              <option value={1}>1 emoção</option>
              <option value={2}>2 emoções</option>
              <option value={3}>3 emoções</option>
              <option value={4}>4 emoções</option>
              <option value={5}>5 emoções</option>
            </select>
          </div>
        </div>
      </div>

      {/* Configurações por Emoção */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Configurações por Tipo de Emoção</h2>
        <div className="space-y-6">
          {emotionTypes.map((emotion) => {
            const setting = settings[emotion.id];
            const Icon = emotion.icon;
            
            return (
              <div key={emotion.id} className={`p-4 rounded-lg border-2 ${emotion.bgColor} border-gray-200`}>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${emotion.bgColor}`}>
                      <Icon className={`h-6 w-6 ${emotion.color}`} />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">{emotion.name}</h3>
                      <p className="text-sm text-gray-600">ID: {emotion.id}</p>
                    </div>
                  </div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={setting.enabled}
                      onChange={(e) => handleEmotionSettingChange(emotion.id, 'enabled', e.target.checked)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="ml-2 text-sm font-medium text-gray-700">Ativado</span>
                  </label>
                </div>

                <div className={`grid grid-cols-1 md:grid-cols-2 gap-4 ${!setting.enabled ? 'opacity-50 pointer-events-none' : ''}`}>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Limite de Detecção: {setting.threshold}%
                    </label>
                    <input
                      type="range"
                      min="30"
                      max="95"
                      value={setting.threshold}
                      onChange={(e) => handleEmotionSettingChange(emotion.id, 'threshold', parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      disabled={!setting.enabled}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>30%</span>
                      <span>95%</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Confiança mínima para detectar esta emoção
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Sensibilidade: {setting.sensitivity}%
                    </label>
                    <input
                      type="range"
                      min="30"
                      max="100"
                      value={setting.sensitivity}
                      onChange={(e) => handleEmotionSettingChange(emotion.id, 'sensitivity', parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      disabled={!setting.enabled}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>30%</span>
                      <span>100%</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Quão sensível é a detecção para micro-expressões
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Botões de Ação */}
      <div className="flex justify-end space-x-3">
        <button
          onClick={handleReset}
          className="btn-secondary"
        >
          Restaurar Padrão
        </button>
        <button
          onClick={handleSave}
          className="btn-primary"
        >
          Salvar Configurações
        </button>
      </div>

      {/* Preview das Configurações */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Resumo das Configurações</h3>
        <div className="bg-gray-50 rounded-lg p-4">
          <pre className="text-sm text-gray-700 whitespace-pre-wrap">
            {JSON.stringify({ globalSettings, emotionSettings: settings }, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
} 