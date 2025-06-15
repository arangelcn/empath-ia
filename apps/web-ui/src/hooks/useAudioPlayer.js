import { useState, useEffect, useCallback, useRef } from 'react';

export const useAudioPlayer = () => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeAudioUrl, setActiveAudioUrl] = useState(null);
  const audioRef = useRef(null);
  const isLoadingRef = useRef(false);

  useEffect(() => {
    // Limpa o objeto de áudio ao desmontar o componente
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const playAudio = useCallback((audioUrl, onEndCallback) => {
    // Prevenir múltiplas chamadas simultâneas
    if (isLoadingRef.current) {
      console.log('🔄 Áudio já carregando, ignorando nova solicitação');
      return;
    }

    console.log('🎵 Reproduzindo áudio:', audioUrl);
    
    // Parar áudio atual se existir
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }

    // Resetar estados
    setIsPlaying(false);
    setActiveAudioUrl(null);
    isLoadingRef.current = true;
    
    try {
      const newAudio = new Audio(audioUrl);
      audioRef.current = newAudio;
      setActiveAudioUrl(audioUrl);

      // Configurar eventos
      newAudio.onloadstart = () => {
        console.log('📥 Carregando áudio...');
      };

      newAudio.oncanplay = () => {
        console.log('✅ Áudio pronto para reprodução');
        isLoadingRef.current = false;
      };

      newAudio.onplay = () => {
        console.log('▶️ Reprodução iniciada');
        setIsPlaying(true);
      };

      newAudio.onpause = () => {
        console.log('⏸️ Reprodução pausada');
        setIsPlaying(false);
      };

      newAudio.onended = () => {
        console.log('✅ Reprodução finalizada');
        setIsPlaying(false);
        setActiveAudioUrl(null);
        audioRef.current = null;
        isLoadingRef.current = false;
        if (onEndCallback) {
          onEndCallback();
        }
      };

      newAudio.onerror = (error) => {
        console.error('❌ Erro na reprodução:', error);
        setIsPlaying(false);
        setActiveAudioUrl(null);
        audioRef.current = null;
        isLoadingRef.current = false;
      };

      // Iniciar reprodução
      newAudio.play().catch(err => {
        console.error("❌ Erro ao reproduzir áudio:", err);
        setIsPlaying(false);
        setActiveAudioUrl(null);
        audioRef.current = null;
        isLoadingRef.current = false;
      });

    } catch (error) {
      console.error('❌ Erro ao criar áudio:', error);
      setIsPlaying(false);
      setActiveAudioUrl(null);
      audioRef.current = null;
      isLoadingRef.current = false;
    }
  }, []); // Remover dependência circular

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setIsPlaying(false);
    setActiveAudioUrl(null);
    isLoadingRef.current = false;
  }, []);

  return { playAudio, stopAudio, isPlaying, activeAudioUrl };
}; 