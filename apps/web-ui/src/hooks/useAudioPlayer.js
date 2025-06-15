import { useState, useEffect, useCallback } from 'react';

export const useAudioPlayer = () => {
  const [audio, setAudio] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeAudioUrl, setActiveAudioUrl] = useState(null);

  useEffect(() => {
    // Limpa o objeto de áudio ao desmontar o componente
    return () => {
      if (audio) {
        audio.pause();
        setAudio(null);
      }
    };
  }, [audio]);

  const playAudio = useCallback((audioUrl, onEndCallback) => {
    if (audio) {
      audio.pause();
    }
    
    const newAudio = new Audio(audioUrl);
    setActiveAudioUrl(audioUrl);

    newAudio.onplay = () => setIsPlaying(true);
    newAudio.onpause = () => {
      setIsPlaying(false);
      setActiveAudioUrl(null);
    };
    newAudio.onended = () => {
      setIsPlaying(false);
      setActiveAudioUrl(null);
      if (onEndCallback) {
        onEndCallback();
      }
    };
    
    newAudio.play().catch(err => {
      console.error("Erro ao reproduzir áudio:", err);
      setIsPlaying(false);
      setActiveAudioUrl(null);
    });

    setAudio(newAudio);
  }, [audio]);

  const stopAudio = useCallback(() => {
    if (audio) {
      audio.pause();
    }
  }, [audio]);

  return { playAudio, stopAudio, isPlaying, activeAudioUrl };
}; 