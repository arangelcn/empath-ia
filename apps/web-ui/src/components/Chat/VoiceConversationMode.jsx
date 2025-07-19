import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X, Mic, MicOff, Volume2, AlertCircle } from 'lucide-react';
import { useVoiceMode } from '../../hooks/useVoiceMode.js';
import { useAudioPlayer } from '../../hooks/useAudioPlayer.js';
import { sendMessage } from '../../services/api.js';

const VoiceConversationMode = ({ sessionId, username, isOpen, onClose, onNewMessage, lastAIMessage }) => {
  const { playAudio, isPlaying, stopAudio } = useAudioPlayer();

  // ✅ PRIMEIRO: Declarar o hook useVoiceMode
  const {
    isVoiceModeActive,
    isListening,
    isProcessing,
    transcript,
    error,
    isSupported,
    activateVoiceMode,
    deactivateVoiceMode,
    startListening,
    stopListening,
    muteMicrophone,
    resetProcessing
  } = useVoiceMode((transcript) => {
    if (!transcript.trim()) return;

    console.log('🎯 Transcrição recebida:', transcript);
    console.log('📋 SessionId:', sessionId);
    console.log('👤 Username:', username);
    
    // ✅ CRÍTICO: Parar reconhecimento IMEDIATAMENTE ao receber transcrição
    console.log('🎤 Reconhecimento parado');
    stopListening();
    
    // ✅ Processar mensagem
    console.log('📤 Enviando mensagem para IA...');
    sendMessage(transcript, sessionId, null, true)
      .then(response => {
        console.log('📨 Resposta da API recebida:', response);
        
        if (response && response.success && response.data && response.data.ai_response) {
          console.log('✅ Resposta válida da IA:', response.data.ai_response.content);
          console.log('🔊 AudioUrl:', response.data.ai_response.audioUrl);
          
          // Chamar callback para atualizar a UI
          if (onNewMessage) {
            onNewMessage({
              id: response.data.user_message.id,
              type: 'user',
              content: response.data.user_message.content
            });
            
            onNewMessage({
              id: response.data.ai_response.id,
              type: 'ai',
              content: response.data.ai_response.content,
              audioUrl: response.data.ai_response.audioUrl
            });
          }
          
          // ✅ CRÍTICO: Se tem áudio, pausar reconhecimento e reproduzir
          if (response.data.ai_response.audioUrl) {
            // 🛑 PASSO 1: Pausar o microfone para reprodução
            console.log("🛑 Microfone pausado para reprodução");
            stopListening();
            muteMicrophone(true);
            
            // ▶️ PASSO 2: Reproduzir resposta da IA
            console.log("▶️ Tocando resposta da IA");
            
            // ✅ USAR playAudio com callback para aguardar término completo
            playAudio(response.data.ai_response.audioUrl, () => {
              // 🎤 PASSO 3: Reativar microfone após reprodução
              console.log("🎤 Microfone reativado - resetando estado de processamento");
              
              // ✅ CRÍTICO: Resetar estado de processamento PRIMEIRO
              resetProcessing();
              
              // ✅ Aguardar um tempo para evitar capturar eco residual
              setTimeout(() => {
                if (isVoiceModeActive) {
                  console.log('🎙️ Desmutando microfone e reiniciando escuta');
                  muteMicrophone(false);
                  
                  // ✅ Pequeno delay adicional para garantir estabilidade
                  setTimeout(() => {
                    if (isVoiceModeActive) {
                      startListening();
                    }
                  }, 500);
                }
              }, 1500); // 1.5 segundos para garantir que não há áudio residual
            });
          } else {
            // ✅ Sem áudio, reiniciar reconhecimento diretamente
            console.log('🎧 Sem áudio na resposta - resetando estado e reiniciando reconhecimento');
            
            // ✅ CRÍTICO: Resetar estado de processamento
            resetProcessing();
            
            setTimeout(() => {
              if (isVoiceModeActive) {
                startListening();
              }
            }, 1000);
          }
        } else {
          console.log('❌ Resposta inválida da API:', response);
          
          // 🛑 Garantir que microfone seja reativado mesmo com resposta inválida
          console.log('🔧 Reativando microfone após resposta inválida');
          resetProcessing(); // ✅ CRÍTICO: Resetar estado
          muteMicrophone(false);
          
          setTimeout(() => {
            if (isVoiceModeActive) {
              startListening();
            }
          }, 2000);
        }
      })
      .catch(error => {
        console.error('❌ Erro ao processar mensagem:', error);
        
        // 🛑 Garantir que microfone seja reativado mesmo com erro
        console.log('🔧 Reativando microfone após erro');
        resetProcessing(); // ✅ CRÍTICO: Resetar estado
        muteMicrophone(false);
        
        // ✅ Em caso de erro, reiniciar reconhecimento
        console.log('🎤 Microfone reativado (após erro)');
        setTimeout(() => {
          if (isVoiceModeActive) {
            startListening();
          }
        }, 2000);
      });
  });

  // ✅ CORRIGIDO: useRef para evitar loop infinito
  const isInitializedRef = useRef(false);
  
  // ✅ Ativar modo apenas quando abrir
  useEffect(() => {
    if (isOpen && isSupported && !isInitializedRef.current) {
      console.log('🎯 Ativando modo conversacional (primeira vez)');
      isInitializedRef.current = true;
      activateVoiceMode();
    } else if (!isOpen && isInitializedRef.current) {
      console.log('🎯 Desativando modo conversacional');
      isInitializedRef.current = false;
      
      // 🛑 Parar tudo ao fechar
      if (isPlaying) {
        console.log('🔇 Parando áudio ao fechar');
        stopAudio();
      }
      
      console.log('🎤 Microfone desligado (modo fechado)');
      stopListening();
      deactivateVoiceMode();
    }
  }, [isOpen, isSupported]); // ✅ APENAS essas dependências

  // ✅ Iniciar escuta quando modo estiver ativo
  useEffect(() => {
    if (isVoiceModeActive && isOpen && !isListening && !isPlaying) {
      console.log('🎤 Microfone ativado - pronto para escutar');
      const timer = setTimeout(() => {
        startListening();
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [isVoiceModeActive, isOpen, isListening, isPlaying]);

  // ✅ MELHORADO: Fechar modo de voz com limpeza completa
  const handleClose = () => {
    console.log('🚪 Fechando modo de voz...');
    
    try {
      // 🛑 PASSO 1: Resetar flag de inicialização
      isInitializedRef.current = false;
      
      // 🛑 PASSO 2: Interromper áudio imediatamente
      if (isPlaying) {
        console.log('🔇 Interrompendo reprodução de áudio');
        stopAudio();
      }
      
      // 🛑 PASSO 3: Parar reconhecimento de voz
      console.log('🎤 Microfone desligado (fechamento manual)');
      stopListening();
      
      // 🛑 PASSO 4: Desativar modo de voz
      deactivateVoiceMode();
      
      console.log('✅ Modo de voz totalmente limpo');
      
      // ✅ Chamar callback de fechamento
      if (onClose) {
        onClose();
      }
    } catch (error) {
      console.error('❌ Erro ao fechar modo de voz:', error);
      // ✅ Forçar fechamento mesmo com erro
      if (onClose) {
        onClose();
      }
    }
  };

  // ✅ IMPORTANTE: Não renderizar se não estiver aberto
  if (!isOpen) {
    return null;
  }

  // Se não suportado
  if (!isSupported) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
        <div className="bg-white dark:bg-dark-surface rounded-xl p-8 max-w-md mx-4 text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-gray-100">
            Recurso não disponível
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Seu navegador não suporta reconhecimento de voz. Tente usar Chrome, Edge ou Firefox.
          </p>
          <button
            onClick={handleClose}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Entendi
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay com gradiente */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-800/90 via-blue-900/80 to-indigo-900/90 backdrop-blur-md" />
      
      {/* Conteúdo principal */}
      <div className="relative z-10 flex flex-col items-center justify-center h-full w-full px-8">
        
        {/* Botão fechar */}
        <button
          onClick={handleClose}
          className="absolute top-6 right-6 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all duration-200 group"
          title="Fechar modo de voz"
        >
          <X className="w-6 h-6 group-hover:rotate-90 transition-transform duration-200" />
        </button>

        {/* Título e status */}
        <div className="text-center mb-12">
          <h2 className="text-3xl font-semibold text-white mb-4">
            Modo Conversacional
          </h2>
          <div className="flex items-center justify-center gap-3">
            {isListening ? (
              <Mic className="w-5 h-5 text-green-400" />
            ) : (
              <MicOff className="w-5 h-5 text-gray-400" />
            )}
            <p className="text-xl text-white/80">
              {isPlaying
                ? "IA está respondendo..."
                : isProcessing 
                  ? "Processando sua mensagem..." 
                  : isListening 
                    ? "Estou ouvindo você..." 
                    : "Preparando para ouvir..."
              }
            </p>
          </div>
        </div>

        {/* Bola pulsante central */}
        <div className="relative mb-12">
          {/* Ondas de pulso externas */}
          {isListening && (
            <>
              <div className="absolute inset-0 w-32 h-32 rounded-full bg-blue-400/30 animate-ping" 
                   style={{ animationDuration: '2s' }} />
              <div className="absolute inset-2 w-28 h-28 rounded-full bg-blue-400/40 animate-ping" 
                   style={{ animationDuration: '1.5s', animationDelay: '0.3s' }} />
              <div className="absolute inset-4 w-24 h-24 rounded-full bg-blue-400/50 animate-ping" 
                   style={{ animationDuration: '1s', animationDelay: '0.6s' }} />
            </>
          )}
          
          {/* Bola principal */}
          <div 
            className={`relative w-32 h-32 rounded-full bg-gradient-to-br shadow-2xl flex items-center justify-center transition-all duration-500 ${
              isPlaying
                ? 'scale-105 shadow-green-400/50 from-green-400 to-green-600'
                : isListening 
                  ? 'scale-100 shadow-blue-400/50 from-blue-400 to-blue-600' 
                  : isProcessing 
                    ? 'scale-110 shadow-purple-400/50 from-purple-400 to-purple-600' 
                    : 'scale-95 shadow-gray-400/30 from-blue-400 to-blue-600'
            }`}
          >
            {/* Ícone central */}
            {isPlaying ? (
              <Volume2 className="w-12 h-12 text-white animate-pulse" />
            ) : isProcessing ? (
              <div className="w-8 h-8 border-4 border-white/30 border-t-white rounded-full animate-spin" />
            ) : isListening ? (
              <Mic className="w-12 h-12 text-white animate-pulse" />
            ) : (
              <MicOff className="w-12 h-12 text-white/70" />
            )}
          </div>
        </div>

        {/* Instruções de uso */}
        <div className="text-center text-white/60 max-w-md mx-auto">
          <p className="text-sm leading-relaxed">
            {isPlaying
              ? "Ouça minha resposta. Voltarei a escutar você em seguida."
              : isProcessing 
                ? "Processando sua mensagem..." 
                : isListening 
                  ? "Fale naturalmente. Farei uma pausa quando você terminar." 
                  : "Aguardando ativação do microfone..."
            }
          </p>
        </div>

        {/* Área de transcript */}
        {transcript && (
          <div className="mt-8 max-w-2xl mx-auto">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
              <p className="text-white text-center italic">
                "{transcript}"
              </p>
            </div>
          </div>
        )}

        {/* Exibir erro se houver */}
        {error && (
          <div className="fixed bottom-6 left-6 right-6 max-w-md mx-auto">
            <div className="bg-red-500/90 backdrop-blur-sm text-white p-4 rounded-lg border border-red-400/50 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
              <div className="flex-1">
                <p className="font-medium">Erro no reconhecimento de voz</p>
                <p className="text-sm text-red-200 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceConversationMode; 