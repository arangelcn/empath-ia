import React, { useState } from 'react';
import { 
  SpeakerWaveIcon, 
  MicrophoneIcon, 
  MusicalNoteIcon,
  PlayIcon,
  PauseIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline';

const voiceOptions = [
  { id: 'pt-BR-AntonioNeural', name: 'Antonio (M)', gender: 'Masculino', language: 'pt-BR' },
  { id: 'pt-BR-FranciscaNeural', name: 'Francisca (F)', gender: 'Feminino', language: 'pt-BR' },
  { id: 'pt-BR-BrendaNeural', name: 'Brenda (F)', gender: 'Feminino', language: 'pt-BR' },
  { id: 'pt-BR-DonatoNeural', name: 'Donato (M)', gender: 'Masculino', language: 'pt-BR' },
];

const emotionVoices = {
  joy: { pitch: 'higher', speed: 'faster', tone: 'cheerful' },
  sadness: { pitch: 'lower', speed: 'slower', tone: 'gentle' },
  anxiety: { pitch: 'higher', speed: 'faster', tone: 'concerned' },
  anger: { pitch: 'lower', speed: 'normal', tone: 'firm' },
  neutral: { pitch: 'normal', speed: 'normal', tone: 'calm' },
};

export default function AudioSettings() {
  const [settings, setSettings] = useState({
    defaultVoice: 'pt-BR-FranciscaNeural',
    volume: 75,
    speed: 1.0,
    pitch: 0,
    pauseBetweenSentences: 500,
    enableEmotionalTone: true,
    backgroundMusic: false,
    backgroundMusicVolume: 20,
    noiseReduction: true,
    audioQuality: 'high',
  });

  const [testing, setTesting] = useState(false);
  const [selectedEmotion, setSelectedEmotion] = useState('neutral');

  const handleSettingChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleTestVoice = async () => {
    setTesting(true);
    // Simular teste de voz
    setTimeout(() => {
      setTesting(false);
    }, 3000);
  };

  const handleSave = () => {
    alert('Configurações de áudio salvas com sucesso!');
  };

  const handleReset = () => {
    if (window.confirm('Tem certeza que deseja restaurar as configurações padrão?')) {
      setSettings({
        defaultVoice: 'pt-BR-FranciscaNeural',
        volume: 75,
        speed: 1.0,
        pitch: 0,
        pauseBetweenSentences: 500,
        enableEmotionalTone: true,
        backgroundMusic: false,
        backgroundMusicVolume: 20,
        noiseReduction: true,
        audioQuality: 'high',
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Configurações de Áudio</h1>
        <p className="mt-1 text-sm text-gray-600">
          Configure as opções de síntese de voz e processamento de áudio
        </p>
      </div>

      {/* Configurações de Voz */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <SpeakerWaveIcon className="h-5 w-5 mr-2" />
          Configurações de Voz
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Voz Padrão
            </label>
            <select
              value={settings.defaultVoice}
              onChange={(e) => handleSettingChange('defaultVoice', e.target.value)}
              className="input-field"
            >
              {voiceOptions.map(voice => (
                <option key={voice.id} value={voice.id}>
                  {voice.name} - {voice.gender} ({voice.language})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Volume: {settings.volume}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={settings.volume}
              onChange={(e) => handleSettingChange('volume', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Velocidade: {settings.speed}x
            </label>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={settings.speed}
              onChange={(e) => handleSettingChange('speed', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0.5x</span>
              <span>2.0x</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tom: {settings.pitch > 0 ? '+' : ''}{settings.pitch}
            </label>
            <input
              type="range"
              min="-10"
              max="10"
              value={settings.pitch}
              onChange={(e) => handleSettingChange('pitch', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>-10</span>
              <span>+10</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Pausa entre frases: {settings.pauseBetweenSentences}ms
            </label>
            <input
              type="range"
              min="0"
              max="2000"
              step="100"
              value={settings.pauseBetweenSentences}
              onChange={(e) => handleSettingChange('pauseBetweenSentences', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0ms</span>
              <span>2000ms</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Qualidade do Áudio
            </label>
            <select
              value={settings.audioQuality}
              onChange={(e) => handleSettingChange('audioQuality', e.target.value)}
              className="input-field"
            >
              <option value="low">Baixa (mais rápido)</option>
              <option value="medium">Média</option>
              <option value="high">Alta (melhor qualidade)</option>
            </select>
          </div>
        </div>

        <div className="mt-6 flex items-center space-x-4">
          <button
            onClick={handleTestVoice}
            disabled={testing}
            className="btn-primary flex items-center"
          >
            {testing ? (
              <>
                <PauseIcon className="h-4 w-4 mr-2" />
                Testando...
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4 mr-2" />
                Testar Voz
              </>
            )}
          </button>
          <span className="text-sm text-gray-600">
            Frase de teste: "Olá, como você está se sentindo hoje?"
          </span>
        </div>
      </div>

      {/* Configurações Emocionais */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <AdjustmentsHorizontalIcon className="h-5 w-5 mr-2" />
          Configurações Emocionais
        </h2>

        <div className="mb-6">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.enableEmotionalTone}
              onChange={(e) => handleSettingChange('enableEmotionalTone', e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="ml-2 text-sm font-medium text-gray-700">
              Ativar adaptação emocional da voz
            </span>
          </label>
          <p className="mt-1 text-sm text-gray-500">
            Ajusta automaticamente o tom, velocidade e entonação baseado na emoção detectada
          </p>
        </div>

        <div className={`${!settings.enableEmotionalTone ? 'opacity-50 pointer-events-none' : ''}`}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(emotionVoices).map(([emotion, config]) => (
              <div key={emotion} className="p-4 border rounded-lg">
                <h3 className="font-medium text-gray-900 capitalize mb-2">{emotion}</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tom:</span>
                    <span className="font-medium">{config.pitch}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Velocidade:</span>
                    <span className="font-medium">{config.speed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Entonação:</span>
                    <span className="font-medium">{config.tone}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Configurações de Áudio Ambiente */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <MusicalNoteIcon className="h-5 w-5 mr-2" />
          Áudio Ambiente
        </h2>

        <div className="space-y-6">
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={settings.backgroundMusic}
                onChange={(e) => handleSettingChange('backgroundMusic', e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">
                Ativar música de fundo
              </span>
            </label>
            <p className="mt-1 text-sm text-gray-500">
              Reproduz música ambiente suave durante as conversas
            </p>
          </div>

          <div className={`${!settings.backgroundMusic ? 'opacity-50 pointer-events-none' : ''}`}>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Volume da música de fundo: {settings.backgroundMusicVolume}%
            </label>
            <input
              type="range"
              min="0"
              max="50"
              value={settings.backgroundMusicVolume}
              onChange={(e) => handleSettingChange('backgroundMusicVolume', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              disabled={!settings.backgroundMusic}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0%</span>
              <span>50%</span>
            </div>
          </div>

          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={settings.noiseReduction}
                onChange={(e) => handleSettingChange('noiseReduction', e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">
                Redução de ruído
              </span>
            </label>
            <p className="mt-1 text-sm text-gray-500">
              Aplica filtros para reduzir ruídos de fundo
            </p>
          </div>
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
        <h3 className="text-lg font-medium text-gray-900 mb-4">Configurações Atuais</h3>
        <div className="bg-gray-50 rounded-lg p-4">
          <pre className="text-sm text-gray-700 whitespace-pre-wrap">
            {JSON.stringify(settings, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
} 