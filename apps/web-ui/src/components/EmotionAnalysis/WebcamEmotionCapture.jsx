import React, { useState, useRef, useEffect } from 'react';
import { Camera, CameraOff, Activity, AlertCircle, Loader2 } from 'lucide-react';

const WebcamEmotionCapture = ({ onEmotionDetected, autoStart = false, hidden = false }) => {
  const [isActive, setIsActive] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState(null);
  const [error, setError] = useState(null);
  const [stream, setStream] = useState(null);
  const [analyzeInterval, setAnalyzeInterval] = useState(null);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Mapear emoções para ícones e cores
  const emotionConfig = {
    joy: { label: '😊 Alegria', color: 'text-yellow-500', bgColor: 'bg-yellow-50' },
    sadness: { label: '😢 Tristeza', color: 'text-blue-500', bgColor: 'bg-blue-50' },
    anger: { label: '😠 Raiva', color: 'text-red-500', bgColor: 'bg-red-50' },
    fear: { label: '😨 Medo', color: 'text-purple-500', bgColor: 'bg-purple-50' },
    surprise: { label: '😮 Surpresa', color: 'text-orange-500', bgColor: 'bg-orange-50' },
    disgust: { label: '🤢 Nojo', color: 'text-green-500', bgColor: 'bg-green-50' },
    neutral: { label: '😐 Neutro', color: 'text-gray-500', bgColor: 'bg-gray-50' }
  };

  // Iniciar webcam
  const startWebcam = async () => {
    try {
      setError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false
      });
      
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        
        // Aguardar o vídeo começar a reproduzir
        videoRef.current.onplaying = () => {
          // Aguardar 2 segundos para garantir que o stream esteja estável
          setTimeout(() => {
            const interval = setInterval(analyzeFrame, 3000);
            setAnalyzeInterval(interval);
          }, 2000);
        };
      }
      setIsActive(true);
      
    } catch (err) {
      console.error('Erro ao acessar webcam:', err);
      setError('Não foi possível acessar a webcam. Verifique as permissões.');
    }
  };

  // Parar webcam
  const stopWebcam = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    
    if (analyzeInterval) {
      clearInterval(analyzeInterval);
      setAnalyzeInterval(null);
    }
    
    setIsActive(false);
    setCurrentEmotion(null);
    setError(null);
  };

  // Capturar frame atual e analisar
  const analyzeFrame = async () => {
    if (!videoRef.current || !canvasRef.current || isAnalyzing) {
      return;
    }

    const video = videoRef.current;
    
    // Verificar se o vídeo está pronto
    if (video.readyState < 2 || video.videoWidth === 0 || video.videoHeight === 0) {
      return;
    }

    // Verificar se o vídeo não está pausado
    if (video.paused || video.ended) {
      try {
        await video.play();
      } catch (playError) {
        return;
      }
    }

    try {
      setIsAnalyzing(true);
      
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      // Ajustar tamanho do canvas
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      if (canvas.width === 0 || canvas.height === 0) {
        return;
      }
      
      // Capturar frame
      context.drawImage(video, 0, 0);
      
      // Verificar se há pixels válidos
      const frameData = context.getImageData(0, 0, canvas.width, canvas.height);
      const pixelData = frameData.data;
      let hasNonZeroPixels = false;
      
      for (let i = 0; i < pixelData.length; i += 4) {
        if (pixelData[i] > 0 || pixelData[i + 1] > 0 || pixelData[i + 2] > 0) {
          hasNonZeroPixels = true;
          break;
        }
      }
      
      if (!hasNonZeroPixels) {
        return;
      }
      
      // Converter para Base64
      const imageData = canvas.toDataURL('image/jpeg', 0.8);
      
      if (imageData.length < 10000) {
        return;
      }
      
      // Enviar para análise
      const response = await fetch('/api/emotion/analyze-realtime', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image: imageData })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.status === 'success' && result.face_detected) {
        setCurrentEmotion(result);
        if (onEmotionDetected) {
          onEmotionDetected(result);
        }
      } else {
        // Sem face detectada
        const neutralResult = {
          dominant_emotion: 'neutral',
          emotions: { neutral: 1.0 },
          confidence: 0,
          face_detected: false
        };
        setCurrentEmotion(neutralResult);
        if (onEmotionDetected) {
          onEmotionDetected(neutralResult);
        }
      }
      
    } catch (err) {
      console.error('Erro na análise de emoção:', err);
      setError('Erro ao analisar emoção');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Auto-iniciar se autoStart for true
  useEffect(() => {
    if (autoStart && !isActive) {
      startWebcam();
    }
  }, [autoStart, isActive]);

  // Limpeza ao desmontar componente
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, []);

  // Se hidden for true, só renderizar elementos necessários para funcionalidade
  if (hidden) {
    return (
      <div style={{ 
        position: 'fixed', 
        top: '0px', 
        left: '0px', 
        width: '640px', 
        height: '480px',
        opacity: 0,
        pointerEvents: 'none',
        zIndex: -1
      }}>
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline 
          muted 
          style={{ width: '640px', height: '480px' }}
        />
        <canvas 
          ref={canvasRef} 
          width="640" 
          height="480" 
          style={{ position: 'absolute', top: '0', left: '0' }}
        />
      </div>
    );
  }

  // Interface completa (comentada para uso futuro)
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Análise de Emoções em Tempo Real
        </h3>
        
        <button
          onClick={isActive ? stopWebcam : startWebcam}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            isActive
              ? 'bg-red-500 hover:bg-red-600 text-white'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
        >
          {isActive ? (
            <>
              <CameraOff className="w-4 h-4" />
              Parar
            </>
          ) : (
            <>
              <Camera className="w-4 h-4" />
              Iniciar
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      <div className="space-y-4">
        {/* Área do vídeo */}
        <div className="relative">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`w-full rounded-lg ${isActive ? 'block' : 'hidden'}`}
            style={{ maxHeight: '400px' }}
          />
          
          {!isActive && (
            <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
              <div className="text-center text-gray-500">
                <Camera className="w-12 h-12 mx-auto mb-2" />
                <p>Clique em "Iniciar" para ativar a webcam</p>
              </div>
            </div>
          )}
          
          {/* Canvas oculto para captura */}
          <canvas ref={canvasRef} className="hidden" />
          
          {/* Indicador de análise */}
          {isAnalyzing && (
            <div className="absolute top-2 right-2 bg-blue-500 text-white px-2 py-1 rounded-full text-xs flex items-center gap-1">
              <Loader2 className="w-3 h-3 animate-spin" />
              Analisando...
            </div>
          )}
        </div>

        {/* Resultado da análise */}
        {currentEmotion && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-700">Emoção Detectada:</h4>
              <span className="text-sm text-gray-500">
                Confiança: {Math.round((currentEmotion.confidence || 0) * 100)}%
              </span>
            </div>
            
            {/* Emoção dominante */}
            <div className={`p-3 rounded-lg ${emotionConfig[currentEmotion.dominant_emotion]?.bgColor}`}>
              <div className={`text-lg font-semibold ${emotionConfig[currentEmotion.dominant_emotion]?.color}`}>
                {emotionConfig[currentEmotion.dominant_emotion]?.label || currentEmotion.dominant_emotion}
              </div>
            </div>
            
            {/* Gráfico de emoções */}
            {currentEmotion.emotions && (
              <div className="space-y-2">
                <h5 className="text-sm font-medium text-gray-600">Todas as Emoções:</h5>
                {Object.entries(currentEmotion.emotions)
                  .sort(([,a], [,b]) => b - a)
                  .map(([emotion, value]) => (
                    <div key={emotion} className="flex items-center gap-2">
                      <span className="w-16 text-xs text-gray-600 capitalize">
                        {emotionConfig[emotion]?.label.split(' ')[1] || emotion}
                      </span>
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${emotionConfig[emotion]?.color.replace('text-', 'bg-')}`}
                          style={{ width: `${value * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-10">
                        {Math.round(value * 100)}%
                      </span>
                    </div>
                  ))}
              </div>
            )}
            
            {!currentEmotion.face_detected && (
              <div className="text-center text-gray-500 text-sm py-2">
                ⚠️ Nenhuma face detectada no momento
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default WebcamEmotionCapture; 