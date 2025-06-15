import React from 'react';
import { Activity } from 'lucide-react';

const EmotionBadge = ({ emotion, isDetecting = false }) => {
  const emotionConfig = {
    joy: { label: 'Alegria', emoji: '😊', color: 'from-yellow-400 to-orange-500' },
    sadness: { label: 'Tristeza', emoji: '😢', color: 'from-blue-400 to-blue-600' },
    anger: { label: 'Raiva', emoji: '😠', color: 'from-red-400 to-red-600' },
    fear: { label: 'Medo', emoji: '😨', color: 'from-purple-400 to-purple-600' },
    surprise: { label: 'Surpresa', emoji: '😮', color: 'from-orange-400 to-yellow-500' },
    disgust: { label: 'Nojo', emoji: '🤢', color: 'from-green-400 to-green-600' },
    neutral: { label: 'Neutro', emoji: '😐', color: 'from-gray-400 to-gray-600' }
  };

  const currentEmotion = emotion?.dominant_emotion || 'neutral';
  const config = emotionConfig[currentEmotion] || emotionConfig.neutral;
  const confidence = emotion?.confidence || 0;
  const faceDetected = emotion?.face_detected !== false;

  if (!faceDetected && !isDetecting) {
    return null; // Não mostrar se não há detecção
  }

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className={`
        relative overflow-hidden rounded-full p-1 
        bg-gradient-to-r ${config.color} 
        shadow-lg transform transition-all duration-300 
        ${isDetecting ? 'animate-pulse' : 'hover:scale-110'}
      `}>
        <div className="bg-white/90 backdrop-blur-sm rounded-full px-3 py-2 flex items-center gap-2 min-w-[120px]">
          {/* Emoji da emoção */}
          <span className="text-lg">{config.emoji}</span>
          
          {/* Informações da emoção */}
          <div className="flex flex-col">
            <span className="text-sm font-medium text-gray-800">
              {config.label}
            </span>
            {faceDetected && confidence > 0 && (
              <span className="text-xs text-gray-600">
                {Math.round(confidence * 100)}%
              </span>
            )}
          </div>

          {/* Indicador de atividade */}
          {isDetecting && (
            <div className="absolute top-1 right-1">
              <Activity className="w-3 h-3 text-gray-600 animate-spin" />
            </div>
          )}
        </div>

        {/* Efeito de brilho quando detectando */}
        {isDetecting && (
          <div className="absolute inset-0 rounded-full bg-white/20 animate-ping"></div>
        )}
      </div>

      {/* Tooltip com informações detalhadas */}
      {emotion?.emotions && faceDetected && (
        <div className="absolute top-full right-0 mt-2 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 opacity-0 hover:opacity-100 transition-opacity duration-200 min-w-[200px]">
          <h4 className="text-sm font-medium text-gray-800 mb-2">Detalhes da Análise:</h4>
          <div className="space-y-1">
            {Object.entries(emotion.emotions)
              .sort(([,a], [,b]) => b - a)
              .slice(0, 3)
              .map(([emotionKey, value]) => {
                const emotionInfo = emotionConfig[emotionKey] || { label: emotionKey, emoji: '❓' };
                return (
                  <div key={emotionKey} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1">
                      <span>{emotionInfo.emoji}</span>
                      <span className="text-gray-700">{emotionInfo.label}</span>
                    </span>
                    <span className="text-gray-600">{Math.round(value * 100)}%</span>
                  </div>
                );
              })}
          </div>
          <div className="mt-2 pt-2 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Análise em tempo real via webcam
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmotionBadge; 