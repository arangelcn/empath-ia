import { useState, useCallback, useRef, useEffect } from 'react';

export const useVoiceMode = (onTranscriptComplete) => {
  const [isVoiceModeActive, setIsVoiceModeActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState(null);
  
  const recognitionRef = useRef(null);
  const mediaStreamRef = useRef(null); // ✅ NOVO: Controle direto do microfone
  const audioContextRef = useRef(null); // ✅ NOVO: AudioContext para controle avançado
  const silenceTimeoutRef = useRef(null);
  const onTranscriptCompleteRef = useRef(onTranscriptComplete);
  const isVoiceModeActiveRef = useRef(isVoiceModeActive); // ✅ NOVO: Ref para valor atual
  const isProcessingRef = useRef(isProcessing); // ✅ NOVO: Ref para valor atual
  const isPlayingRef = useRef(false); // ✅ NOVO: Ref para controle de áudio

  // Atualizar referências
  useEffect(() => {
    onTranscriptCompleteRef.current = onTranscriptComplete;
    isVoiceModeActiveRef.current = isVoiceModeActive;
    isProcessingRef.current = isProcessing;
  }, [onTranscriptComplete, isVoiceModeActive, isProcessing]);

  // Configurações de reconhecimento
  // ⚙️ TIMEOUT PERSONALIZADO: Tempo em milissegundos que aguarda após o usuário parar de falar
  // antes de enviar a mensagem para o gateway/ai-service
  // Valores sugeridos: 2000-5000ms (2-5 segundos)
  // 🔧 FUNCIONALIDADE: Agora SEMPRE usa este timeout, ignorando detecção automática do navegador
  const SILENCE_THRESHOLD = 2000; // 4 segundos de silêncio para processar

  // ✅ NOVA função para configurar microfone com cancelamento de eco
  const setupMicrophoneWithEchoCancellation = useCallback(async () => {
    try {
      console.log('🎙️ Configurando microfone com cancelamento de eco...');
      
      // ✅ CONFIGURAÇÕES AVANÇADAS: Como a OpenAI faz
      const constraints = {
        audio: {
          echoCancellation: true,        // ✅ CRÍTICO: Cancelamento de eco
          noiseSuppression: true,        // ✅ Supressão de ruído
          autoGainControl: true,         // ✅ Controle automático de ganho
          sampleRate: 16000,            // ✅ Taxa de amostragem otimizada
          channelCount: 1,              // ✅ Mono para melhor performance
          volume: 0.8                   // ✅ Volume controlado
        }
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      mediaStreamRef.current = stream;
      
      console.log('✅ Microfone configurado com sucesso');
      console.log('🔧 Configurações aplicadas:', constraints.audio);
      
      return stream;
    } catch (error) {
      console.error('❌ Erro ao configurar microfone:', error);
      setError('Erro ao acessar microfone com cancelamento de eco');
      throw error;
    }
  }, []);

  // ✅ NOVA função para mutar/desmutar fisicamente o microfone
  const muteMicrophone = useCallback((mute = true) => {
    if (mediaStreamRef.current) {
      const audioTracks = mediaStreamRef.current.getAudioTracks();
      audioTracks.forEach(track => {
        track.enabled = !mute; // ✅ FÍSICO: Liga/desliga o track do microfone
      });
      console.log(`🎙️ Microfone ${mute ? 'MUTADO' : 'ATIVADO'} fisicamente`);
    }
  }, []);

  // Inicializar Web Speech API com configurações avançadas
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = true;  // ✅ MUDANÇA: Mantém escuta contínua
        recognitionRef.current.interimResults = true;
        recognitionRef.current.lang = 'pt-BR';
        recognitionRef.current.maxAlternatives = 1;
        
        // Configurar eventos
        recognitionRef.current.onstart = () => {
          console.log('🎤 Reconhecimento de voz iniciado COM cancelamento de eco');
          setIsListening(true);
          setError(null);
        };

        recognitionRef.current.onresult = (event) => {
          let finalTranscript = '';
          let interimTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              finalTranscript += transcript;
            } else {
              interimTranscript += transcript;
            }
          }

          const currentTranscript = finalTranscript || interimTranscript;
          
          // ✅ Sempre atualizar transcript para feedback visual
          setTranscript(currentTranscript);

          // ✅ NOVO: SEMPRE usar timeout personalizado para dar tempo ao usuário
          // Limpar timeout anterior se existir
          if (silenceTimeoutRef.current) {
            clearTimeout(silenceTimeoutRef.current);
          }

          // ✅ CORREÇÃO: SEMPRE aguardar SILENCE_THRESHOLD, independente de ser final ou interim
          if (currentTranscript.trim()) {
            const isFinale = finalTranscript.trim().length > 0;
            console.log(`🎙️ ${isFinale ? 'Transcript final' : 'Resultado intermediário'} recebido: "${currentTranscript.substring(0, 30)}..."`);
            console.log(`⏰ Aguardando ${SILENCE_THRESHOLD}ms antes de processar...`);
            
            silenceTimeoutRef.current = setTimeout(() => {
              if (currentTranscript.trim()) {
                console.log('⏰ Timeout de silêncio atingido, processando transcrição');
                processTranscript(currentTranscript.trim());
              }
            }, SILENCE_THRESHOLD);
          }
        };

        recognitionRef.current.onerror = (event) => {
          console.error('❌ Erro no reconhecimento de voz:', event.error);
          setError(`Erro de reconhecimento: ${event.error}`);
          setIsListening(false);
        };

        recognitionRef.current.onend = () => {
          console.log('🔇 Reconhecimento de voz finalizado');
          setIsListening(false);
          
          // ✅ CORREÇÃO: Não reiniciar se estiver processando OU reproduzindo áudio
          setTimeout(() => {
            if (isVoiceModeActiveRef.current && !isProcessingRef.current && !isPlayingRef.current) {
              console.log('🔄 Reiniciando reconhecimento automaticamente...');
              // Tentar reiniciar
              try {
                if (recognitionRef.current && mediaStreamRef.current) {
                  muteMicrophone(false);
                  setTranscript('');
                  setError(null);
                  recognitionRef.current.start();
                }
              } catch (error) {
                console.warn('⚠️ Não foi possível reiniciar reconhecimento:', error);
              }
            } else {
              console.log('🛑 Não reiniciando reconhecimento - processando ou reproduzindo áudio');
            }
          }, 200); // Delay um pouco maior para estabilidade
        };
      } else {
        setError('Web Speech API não suportada neste navegador');
      }
    }

    return () => {
      clearTimeout(silenceTimeoutRef.current);
      // ✅ CLEANUP: Limpar stream do microfone
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const processTranscript = useCallback((finalText) => {
    // ✅ PROTEÇÃO SIMPLIFICADA: Só verificar se tem texto e não está processando
    if (!finalText.trim() || isProcessing) {
      console.log('⚠️ Ignorando transcrição:', {
        texto: finalText.substring(0, 20),
        isProcessing,
        hasText: !!finalText.trim()
      });
      return;
    }

    // ✅ NOVO: Limpar timeout de silêncio ao processar
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }

    console.log('📝 Transcript completo ACEITO:', finalText);
    setIsProcessing(true);
    setIsListening(false); // ✅ CRÍTICO: Parar escuta imediatamente
    setTranscript('');

    // ✅ CRÍTICO: Mutar microfone IMEDIATAMENTE após capturar fala e durante processamento
    console.log('🔇 MUTANDO microfone após capturar transcrição e durante processamento');
    muteMicrophone(true);

    // Chamar callback externo se disponível
    if (onTranscriptCompleteRef.current) {
      onTranscriptCompleteRef.current(finalText);
    }
  }, [isProcessing, muteMicrophone]);

  const startListening = useCallback(async () => {
    if (!recognitionRef.current || !isVoiceModeActive) {
      console.log('⚠️ Reconhecimento não disponível ou modo inativo');
      return;
    }

    // ✅ CORREÇÃO: Verificar se já está escutando para evitar erro
    if (isListening) {
      console.log('⚠️ Reconhecimento já está ativo, ignorando start');
      return;
    }

    try {
      // ✅ NOVO: Configurar microfone antes de iniciar reconhecimento
      if (!mediaStreamRef.current) {
        await setupMicrophoneWithEchoCancellation();
      }

      // ✅ CRÍTICO: Desmutar microfone para escutar
      console.log('🎙️ DESMUTANDO microfone para escutar');
      muteMicrophone(false);

      setTranscript('');
      setError(null);
      console.log('🎤 Iniciando reconhecimento com cancelamento de eco...');
      recognitionRef.current.start();
    } catch (error) {
      console.error('❌ Erro ao iniciar reconhecimento:', error);
      setError('Erro ao iniciar reconhecimento de voz');
      setIsListening(false);
    }
  }, [isListening, isVoiceModeActive, setupMicrophoneWithEchoCancellation, muteMicrophone]);

  const stopListening = useCallback(() => {
    console.log('🛑 Parando escuta...');
    
    // ✅ CRÍTICO: Setar estado IMEDIATAMENTE para UI responsiva
    setIsListening(false);
    setTranscript('');
    
    // ✅ CRÍTICO: Mutar microfone FISICAMENTE
    console.log('🔇 MUTANDO microfone ao parar escuta');
    muteMicrophone(true);
    
    // ✅ CRÍTICO: Parar Web Speech API (assíncrono)
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
        console.log('🎤 Web Speech API stop() chamado');
      } catch (error) {
        console.warn('⚠️ Erro ao parar reconhecimento:', error);
      }
    }
    
    clearTimeout(silenceTimeoutRef.current);
  }, [muteMicrophone]);

  const activateVoiceMode = useCallback(async () => {
    console.log('🎤 Ativando modo de voz COM cancelamento de eco');
    setIsVoiceModeActive(true);
    setError(null);
    
    try {
      // ✅ NOVO: Configurar microfone ao ativar modo
      await setupMicrophoneWithEchoCancellation();
      console.log('ℹ️ Modo de voz ativo - microfone configurado e mutado');
    } catch (error) {
      console.error('❌ Erro ao configurar microfone no modo de voz:', error);
      setError('Erro ao configurar microfone');
    }
  }, [setupMicrophoneWithEchoCancellation]);

  const deactivateVoiceMode = useCallback(() => {
    console.log('🔇 Desativando modo de voz');
    setIsVoiceModeActive(false);
    stopListening();
    setIsProcessing(false);
    setTranscript('');
    setError(null);
    
    // ✅ CLEANUP: Liberar stream do microfone
    if (mediaStreamRef.current) {
      console.log('🧹 Liberando stream do microfone');
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
  }, [stopListening]);

  const resumeListening = useCallback(() => {
    console.log('▶️ Retomando escuta após resposta da IA');
    setIsProcessing(false);
    // Aguardar um pouco e iniciar nova escuta manualmente
    setTimeout(() => {
      if (isVoiceModeActive) {
        startListening();
      }
    }, 1500);
  }, [isVoiceModeActive, startListening]);

  // ✅ NOVA função para resetar estado de processamento
  const resetProcessing = useCallback(() => {
    console.log('🔄 Resetando estado de processamento');
    setIsProcessing(false);
  }, []);

  // ✅ NOVA função para ativar escuta após reprodução de áudio
  const resumeListeningAfterAudio = useCallback(() => {
    console.log('🎵➡️🎤 Retomando escuta após reprodução de áudio');
    
    // ✅ CRÍTICO: Aguardar um tempo para áudio parar completamente
    setTimeout(() => {
      if (isVoiceModeActive) {
        console.log('🎙️ Reativando microfone após áudio');
        startListening();
      }
    }, 2000); // 2 segundos para garantir que não há áudio residual
  }, [isVoiceModeActive, startListening]);

  // ✅ NOVA função para controlar estado do áudio
  const setAudioPlaying = useCallback((playing) => {
    console.log(`🎵 Atualizando estado do áudio: ${playing ? 'TOCANDO' : 'PARADO'}`);
    isPlayingRef.current = playing;
  }, []);

  // Verificar suporte à Web Speech API
  const isSupported = typeof window !== 'undefined' && 
    (window.SpeechRecognition || window.webkitSpeechRecognition);

  return {
    // Estados
    isVoiceModeActive,
    isListening,
    isProcessing,
    transcript,
    error,
    isSupported,
    
    // Ações
    activateVoiceMode,
    deactivateVoiceMode,
    resumeListening,
    resetProcessing,
    resumeListeningAfterAudio, // ✅ NOVA função específica para após áudio
    setAudioPlaying, // ✅ NOVA função para controle de áudio
    
    // Utilitários
    startListening,
    stopListening,
    muteMicrophone // ✅ NOVA função para controle manual do microfone
  };
}; 