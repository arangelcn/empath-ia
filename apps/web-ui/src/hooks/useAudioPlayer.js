import { useState, useEffect, useCallback, useRef } from 'react';

export const useAudioPlayer = () => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeAudioUrl, setActiveAudioUrl] = useState(null);
  const audioRef = useRef(null);
  const isLoadingRef = useRef(false);
  const callbackRef = useRef(null); // ✅ NOVO: Guardar callback para chamada segura
  const timeoutRef = useRef(null); // ✅ NOVO: Timeout de segurança

  useEffect(() => {
    // Limpa o objeto de áudio ao desmontar o componente
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // ✅ NOVA função para finalizar áudio com segurança
  const finishAudio = useCallback((reason = 'ended') => {
    console.log(`🏁 FINALIZANDO ÁUDIO: ${reason}`);
    
    setIsPlaying(false);
    setActiveAudioUrl(null);
    isLoadingRef.current = false;
    
    // Limpar timeout de segurança
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    
    // Chamar callback se existir
    if (callbackRef.current) {
      console.log(`🎯 CHAMANDO CALLBACK: ${reason}`);
      const callback = callbackRef.current;
      callbackRef.current = null; // Limpar para evitar múltiplas chamadas
      callback();
    }
    
    // Limpar referência do áudio
    if (audioRef.current) {
      audioRef.current = null;
    }
  }, []);

  const playAudio = useCallback((audioUrl, onEndCallback) => {
    // Prevenir múltiplas chamadas simultâneas
    if (isLoadingRef.current) {
      console.log('🔄 Áudio já carregando, ignorando nova solicitação');
      return;
    }

    console.log('🎵 ÁUDIO PLAYER: Reproduzindo áudio:', audioUrl);
    console.log('🎯 ÁUDIO PLAYER: Callback recebido:', onEndCallback ? 'SIM' : 'NÃO');
    
    // Finalizar áudio anterior se existir
    if (audioRef.current) {
      console.log('🛑 ÁUDIO PLAYER: Finalizando áudio anterior');
      finishAudio('replaced');
    }

    // Resetar estados
    setIsPlaying(false);
    setActiveAudioUrl(null);
    isLoadingRef.current = true;
    callbackRef.current = onEndCallback; // ✅ GUARDAR callback para uso seguro
    
    try {
      const newAudio = new Audio(audioUrl);
      audioRef.current = newAudio;
      setActiveAudioUrl(audioUrl);

      // ✅ TIMEOUT DE SEGURANÇA: Se não terminar em 60s, forçar finalização
      timeoutRef.current = setTimeout(() => {
        console.log('⏰ TIMEOUT DE SEGURANÇA: Forçando finalização do áudio');
        finishAudio('timeout');
      }, 60000); // 60 segundos de segurança

      // Configurar eventos
      newAudio.onloadstart = () => {
        console.log('📥 ÁUDIO PLAYER: Carregando áudio...');
      };

      newAudio.oncanplay = () => {
        console.log('✅ ÁUDIO PLAYER: Áudio pronto para reprodução');
        isLoadingRef.current = false;
      };

      newAudio.onplay = () => {
        console.log('▶️ ÁUDIO PLAYER: Reprodução iniciada');
        setIsPlaying(true);
      };

      newAudio.onpause = () => {
        console.log('⏸️ ÁUDIO PLAYER: Reprodução pausada');
        setIsPlaying(false);
      };

      newAudio.onended = () => {
        console.log('🏁 ÁUDIO PLAYER: EVENTO ONENDED disparado!');
        finishAudio('ended');
      };

      newAudio.onerror = (error) => {
        console.error('❌ ÁUDIO PLAYER: Erro na reprodução:', error);
        finishAudio('error');
      };

      // ✅ MONITORAMENTO ADICIONAL: Verificar periodicamente se terminou
      const checkAudioStatus = () => {
        if (audioRef.current && !audioRef.current.paused) {
          // ✅ VERIFICAÇÃO: Se chegou ao final mas onended não foi chamado
          if (audioRef.current.currentTime >= audioRef.current.duration - 0.1) {
            console.log('🔍 DETECTADO: Áudio terminou mas onended não foi chamado');
            finishAudio('detected_end');
          } else {
            // Continuar verificando a cada 500ms
            setTimeout(checkAudioStatus, 500);
          }
        }
      };

      // Iniciar reprodução
      newAudio.play().then(() => {
        console.log('✅ ÁUDIO PLAYER: Play iniciado com sucesso');
        // Iniciar monitoramento
        setTimeout(checkAudioStatus, 1000);
      }).catch(err => {
        console.error("❌ ÁUDIO PLAYER: Erro ao reproduzir áudio:", err);
        finishAudio('play_error');
      });

    } catch (error) {
      console.error('❌ ÁUDIO PLAYER: Erro ao criar áudio:', error);
      finishAudio('creation_error');
    }
  }, [finishAudio]);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    finishAudio('stopped');
  }, [finishAudio]);

  return { playAudio, stopAudio, isPlaying, activeAudioUrl };
}; 