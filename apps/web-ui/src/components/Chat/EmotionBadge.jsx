import React from 'react';
const EmotionBadge = ({ emotion, isDetecting = false }) => {
  const normalizeEmotion = (value) => {
    const aliases = {
      happy: 'joy',
      sad: 'sadness',
      angry: 'anger',
    };
    return aliases[value] || value || 'neutral';
  };

  const emotionConfig = {
    joy: { label: 'Alegria', emoji: '😊', color: 'text-amber-600 dark:text-amber-300' },
    sadness: { label: 'Tristeza', emoji: '😢', color: 'text-blue-600 dark:text-blue-300' },
    anger: { label: 'Raiva', emoji: '😠', color: 'text-orange-600 dark:text-orange-300' },
    fear: { label: 'Medo', emoji: '😨', color: 'text-purple-600 dark:text-purple-300' },
    surprise: { label: 'Surpresa', emoji: '😮', color: 'text-yellow-600 dark:text-yellow-300' },
    disgust: { label: 'Nojo', emoji: '🤢', color: 'text-green-600 dark:text-green-300' },
    neutral: { label: 'Neutro', emoji: '😐', color: 'text-gray-500 dark:text-gray-300' }
  };

  const currentEmotion = normalizeEmotion(emotion?.dominant_emotion);
  const config = emotionConfig[currentEmotion] || emotionConfig.neutral;
  const confidence = emotion?.confidence || 0;
  const faceDetected = emotion?.face_detected !== false;

  if (!faceDetected && !isDetecting) {
    return null; // Não mostrar se não há detecção
  }

  return (
    <div
      className={`flex min-w-[76px] items-center justify-end gap-1.5 text-right text-xs ${isDetecting ? 'opacity-70' : ''}`}
      aria-live="polite"
      title={`${config.label}${confidence > 0 ? ` (${Math.round(confidence * 100)}%)` : ''}`}
    >
      <span className="text-sm leading-none" aria-hidden="true">{config.emoji}</span>
      <div className="flex flex-col leading-tight">
        <span className={`font-medium ${config.color}`}>{config.label}</span>
        {faceDetected && confidence > 0 && (
          <span className="text-[10px] text-gray-400 dark:text-gray-500">
            {Math.round(confidence * 100)}%
          </span>
        )}
      </div>
    </div>
  );
};

export default EmotionBadge; 
