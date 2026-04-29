import React from 'react';
import { Activity } from 'lucide-react';

const EmotionBadge = ({ emotion, isDetecting = false }) => {
  const emotionConfig = {
    joy: { label: 'Alegria', emoji: '😊', color: 'from-yellow-400 to-orange-500' },
    sadness: { label: 'Tristeza', emoji: '😢', color: 'from-blue-400 to-blue-600' },
    anger: { label: 'Raiva', emoji: '😠', color: 'from-orange-400 to-orange-600' },
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
    <div className="relative">
      <div className={`
        relative overflow-hidden rounded-full p-0.5 
        bg-gradient-to-r ${config.color} 
        shadow-sm transform transition-all duration-300 
        ${isDetecting ? 'animate-pulse' : 'hover:shadow-md'}
      `}>
        <div className="bg-white/90 backdrop-blur-sm rounded-full px-2 py-1 flex items-center gap-1.5 min-w-[80px]">
          {/* Emoji da emoção */}
          <span className="text-sm">{config.emoji}</span>
          
          {/* Informações da emoção */}
          <div className="flex flex-col">
            <span className="text-xs font-medium text-gray-800">
              {config.label}
            </span>
            {faceDetected && confidence > 0 && (
              <span className="text-[10px] text-gray-600">
                {Math.round(confidence * 100)}%
              </span>
            )}
          </div>

          {/* Indicador de atividade */}
          {isDetecting && (
            <div className="absolute top-0.5 right-0.5">
              <Activity className="w-2 h-2 text-gray-600 animate-spin" />
            </div>
          )}
        </div>

        {/* Efeito de brilho quando detectando */}
        {isDetecting && (
          <div className="absolute inset-0 rounded-full bg-white/20 animate-ping"></div>
        )}
      </div>


    </div>
  );
};

export default EmotionBadge; 
