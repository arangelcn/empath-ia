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

  // Atualizar referência do callback
  useEffect(() => {
    onTranscriptCompleteRef.current = onTranscriptComplete;
  }, [onTranscriptComplete]);

  // Configurações de reconhecimento
  const SILENCE_THRESHOLD = 2000; // 2 segundos de silêncio para processar

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
        recognitionRef.current.continuous = false;
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

          // Se temos texto final, processar imediatamente
          if (finalTranscript.trim()) {
            console.log('📝 Transcript final recebido:', finalTranscript.substring(0, 30));
            processTranscript(finalTranscript.trim());
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

    console.log('📝 Transcript completo ACEITO:', finalText);
    setIsProcessing(true);
    setIsListening(false); // ✅ CRÍTICO: Parar escuta imediatamente
    setTranscript('');

    // ✅ CRÍTICO: Mutar microfone IMEDIATAMENTE após capturar fala
    console.log('🔇 MUTANDO microfone após capturar transcrição');
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
    
    // Utilitários
    startListening,
    stopListening,
    muteMicrophone // ✅ NOVA função para controle manual do microfone
  };
}; 