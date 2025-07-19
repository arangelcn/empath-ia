import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { Heart, LogOut, Send, Target, Mic } from 'lucide-react';
import { sendMessage, getChatHistory, getTherapeuticSession, getInitialMessage } from '../../services/api.js';
import Button from '../Common/Button.jsx';
import Loading from '../Common/Loading.jsx';
import EmotionBadge from './EmotionBadge.jsx';
import WebcamEmotionCapture from '../EmotionAnalysis/WebcamEmotionCapture.jsx';
import VoiceConversationMode from './VoiceConversationMode.jsx';
import { useAudioPlayer } from '../../hooks/useAudioPlayer.js';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  audioUrl?: string;
}

interface SessionObjective {
  title: string;
  subtitle: string;
  objective: string;
  initial_prompt: string;
}

// Função removida - usando WebcamEmotionCapture para análise em tempo real

const MessageBubble = ({ message, isTyping = false }) => {
  const isUser = message.type === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      <div className={`max-w-[80%] px-4 py-3 rounded-2xl shadow-therapy-soft text-sm transition-all duration-200
        ${isUser 
          ? 'bg-blue-500 text-white rounded-br-md hover:shadow-lg' 
          : 'bg-white dark:bg-dark-surface border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100 rounded-bl-md hover:shadow-lg'
        }
      `}>
        {isTyping ? (
          <div className="flex items-center gap-2">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-current rounded-full animate-pulse"></div>
              <div className="w-2 h-2 bg-current rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-2 h-2 bg-current rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
            </div>
            <span className="text-xs opacity-70">Digitando...</span>
          </div>
        ) : (
          <p className="leading-relaxed reading-spacing">{message.content}</p>
        )}
      </div>
    </div>
  );
};

const ChatScreen = ({ username }) => {
  const { sessionId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { playAudio } = useAudioPlayer();
  
  // Usar sessionId da URL
  const currentSessionId = sessionId;
  
  // Obter informações da sessão do state (passado pelo navigate)
  const sessionInfo = location.state || {};
  const { sessionTitle, userSession } = sessionInfo;
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [currentEmotion, setCurrentEmotion] = useState(null);
  const [sessionObjective, setSessionObjective] = useState<SessionObjective | null>(null);
  const [showObjective, setShowObjective] = useState(true);
  const [showFinalizeButton, setShowFinalizeButton] = useState(false);
  const [isConversationEnded, setIsConversationEnded] = useState(false);
  const [isFinalizing, setIsFinalizing] = useState(false);
  const [sessionContext, setSessionContext] = useState(null);
  const [showSessionSummary, setShowSessionSummary] = useState(false);
  const [isVoiceModeOpen, setIsVoiceModeOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Carregar objetivo da sessão e histórico de mensagens quando o componente for montado
  useEffect(() => {
    const loadSessionData = async () => {
      try {
        setIsLoadingHistory(true);
        
        // Carregar objetivo da sessão
        if (currentSessionId) {
          try {
            // ✅ CORREÇÃO: Extrair o session_id original (remover prefix do username)
            // currentSessionId formato: "teste_01_session-1"
            // Precisamos de: "session-1" para buscar na coleção de templates
            const originalSessionId = currentSessionId.includes('_') 
              ? currentSessionId.split('_').slice(1).join('_')  // Remove primeiro elemento (username)
              : currentSessionId; // Fallback se não tiver underscore
              
            console.log('🔍 Buscando sessão - currentSessionId:', currentSessionId, 'originalSessionId:', originalSessionId);
            
            const sessionResponse = await getTherapeuticSession(originalSessionId);
            if (sessionResponse.success && sessionResponse.data) {
              console.log('✅ Session Objective carregado:', sessionResponse.data);
              setSessionObjective({
                title: sessionResponse.data.title,
                subtitle: sessionResponse.data.subtitle,
                objective: sessionResponse.data.objective,
                initial_prompt: sessionResponse.data.initial_prompt
              });
            } else {
              console.warn('⚠️ Session não encontrada para ID:', originalSessionId);
            }
          } catch (error) {
            console.warn('Erro ao carregar objetivo da sessão:', error);
          }
        }
        
        // Carregar histórico de mensagens
        const response = await getChatHistory(currentSessionId);
        
        if (response.success && response.data.history && response.data.history.length > 0) {
          // Converter histórico do backend para o formato do frontend
          const historyMessages: Message[] = response.data.history.map((msg: any) => ({
            id: msg.id,
            type: msg.type === 'user' ? 'user' : 'ai',
            content: msg.content,
            audioUrl: msg.audio_url || undefined,
          }));
          
          setMessages(historyMessages);
        } else {
          // ✅ NOVO: Se não há histórico, tentar gerar mensagem inicial automática
          console.log('🤖 Sessão sem histórico, gerando mensagem inicial automática...');
          
          try {
            const initialMessageResponse = await getInitialMessage(currentSessionId);
            console.log('🔍 DEBUG - Resposta inicial:', initialMessageResponse);
            
            if (initialMessageResponse.success && initialMessageResponse.data) {
              // ✅ CORREÇÃO: Aguardar um pouco para garantir que o backend salvou a mensagem
              console.log('⏳ Aguardando backend finalizar salvamento...');
              await new Promise(resolve => setTimeout(resolve, 1000));
              
              // ✅ CORREÇÃO: Recarregar histórico DIRETAMENTE após gerar mensagem inicial
              console.log('🔄 Recarregando histórico após mensagem inicial...');
              const updatedHistory = await getChatHistory(currentSessionId);
              console.log('🔍 DEBUG - Histórico atualizado:', updatedHistory);
              
              if (updatedHistory.success && updatedHistory.data.history && updatedHistory.data.history.length > 0) {
                const historyMessages: Message[] = updatedHistory.data.history.map((msg: any) => ({
                  id: msg.id,
                  type: msg.type === 'user' ? 'user' : 'ai',
                  content: msg.content,
                  audioUrl: msg.audio_url || undefined,
                }));
                
                setMessages(historyMessages);
                console.log('✅ Histórico carregado com sucesso após mensagem inicial:', historyMessages.length, 'mensagens');
                
                // ✅ NOVO: Reproduzir áudio se disponível para a mensagem inicial
                const initialMessage = historyMessages.find(msg => msg.type === 'ai');
                if (initialMessage && initialMessage.audioUrl) {
                  // Aguardar um pouco antes de reproduzir
                  setTimeout(() => {
                    console.log('🔊 Reproduzindo áudio da mensagem inicial...');
                    playAudio(initialMessage.audioUrl);
                  }, 500);
                }
              } else {
                // ✅ FALLBACK: Se histórico ainda não foi atualizado, usar dados da resposta inicial
                console.warn('⚠️ Histórico ainda não atualizado, usando dados da resposta inicial');
                
                if (initialMessageResponse.data.message) {
                  const fallbackMessage: Message = {
                    id: initialMessageResponse.data.message.id,
                    type: 'ai',
                    content: initialMessageResponse.data.message.content,
                    audioUrl: initialMessageResponse.data.message.audioUrl || undefined,
                  };
                  
                  setMessages([fallbackMessage]);
                  console.log('🔄 Usando mensagem inicial como fallback');
                  
                  // Reproduzir áudio se disponível
                  if (fallbackMessage.audioUrl) {
                    setTimeout(() => {
                      playAudio(fallbackMessage.audioUrl);
                    }, 500);
                  }
                } else {
                  setMessages([]);
                }
              }
            } else {
              console.warn('⚠️ Falha ao gerar mensagem inicial:', initialMessageResponse.error || 'Resposta inválida');
              setMessages([]);
            }
          } catch (error) {
            console.error('❌ Erro ao gerar mensagem inicial:', error);
            setMessages([]);
          }
        }
      } catch (error) {
        console.error('Erro ao carregar dados da sessão:', error);
        setMessages([]);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    if (currentSessionId && username) {
      loadSessionData();
    }
  }, [currentSessionId, username]);

  // useEffect removido - emoção agora é atualizada via WebcamEmotionCapture
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focar no input quando o componente carregar
  useEffect(() => {
    if (!isLoadingHistory && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 300);
    }
  }, [isLoadingHistory]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: inputValue,
    };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      // ✅ CORREÇÃO: Para session-1 (cadastro), não passar sessionObjective 
      // Para outras sessões, passar apenas se for a primeira mensagem
      const isFirstMessage = messages.length === 0;
      
      // Extrair o session_id original para verificar se é session-1
      const originalSessionId = currentSessionId.includes('_') 
        ? currentSessionId.split('_').slice(1).join('_')
        : currentSessionId;
      
      // session-1 é a sessão de cadastro, não deve receber título/objetivo
      const isRegistrationSession = originalSessionId === 'session-1';
      
      let objectiveToSend = null;
      if (isFirstMessage && !isRegistrationSession) {
        // Apenas para sessões que NÃO são de cadastro
        objectiveToSend = sessionObjective;
      }
      
      console.log(`🔍 Session Info: originalSessionId=${originalSessionId}, isRegistrationSession=${isRegistrationSession}, isFirstMessage=${isFirstMessage}, willSendObjective=${objectiveToSend !== null}`);
      
      const response = await sendMessage(currentInput, currentSessionId, objectiveToSend);
      if (response.success) {
        const { ai_response } = response.data;
        const aiMessage: Message = {
          id: ai_response.id,
          type: 'ai',
          content: ai_response.content,
          audioUrl: ai_response.audioUrl,
        };
        setMessages(prev => [...prev, aiMessage]);
        
        // ✅ NOVO: Verificar se o cadastro foi finalizado
        if (response.data.registration_completed && response.data.redirect_to_home) {
          console.log('🎉 CADASTRO FINALIZADO - Processando redirecionamento...');
          
          // Mostrar mensagem de sucesso
          if (response.data.completion_message) {
            console.log('📋 Mensagem de finalização:', response.data.completion_message);
          }
          
          // Usar tempo de redirecionamento definido pelo backend (padrão 3 segundos)
          const redirectDelay = response.data.auto_redirect_delay || 3000;
          console.log(`⏳ Redirecionamento automático em ${redirectDelay}ms`);
          
          // Redirecionar para home após tempo especificado
          setTimeout(() => {
            console.log('🏠 Redirecionando para home...');
            navigate('/home', { 
              state: { 
                message: 'Cadastro finalizado com sucesso! Agora você pode acessar todas as sessões terapêuticas.',
                fromRegistration: true,
                finalize_success: response.data.finalize_success
              } 
            });
          }, redirectDelay);
        }
        
        // ✅ NOVO: Verificar se a conversa foi finalizada automaticamente
        if (response.data.conversation_ended) {
          console.log('🔚 Conversa finalizada automaticamente');
          setIsConversationEnded(true);
          setShowFinalizeButton(false);
          
          // Aguardar um pouco antes de mostrar o resumo
          setTimeout(() => {
            finalizeSession();
          }, 2000);
        }
        
        // Detectar fim de conversa baseado na mensagem do usuário
        if (checkConversationEnd(currentInput)) {
          console.log('🔚 Fim de conversa detectado pela mensagem do usuário');
          setTimeout(() => {
            finalizeSession();
          }, 3000);
        }
      }
    } catch (error) {
      const errorMessage = {
        id: `error-${Date.now()}`,
        type: 'ai',
        content: "Desculpe, não consegui processar sua mensagem. Tente novamente mais tarde.",
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      
      // Manter foco no input após enviar mensagem
      // Usar setTimeout para garantir que o DOM seja atualizado antes de focar
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
          // Garantir que o cursor fique no final do texto (se houver)
          const textLength = inputRef.current.value.length;
          inputRef.current.setSelectionRange(textLength, textLength);
        }
      }, 100);
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Handler para receber emoção da webcam
  const handleWebcamEmotion = (result) => {
    if (result && result.dominant_emotion) {
      // Passar o objeto completo para o EmotionBadge
      setCurrentEmotion(result);
    }
  };

  // Lógica para detectar fim de conversa
  useEffect(() => {
    if (messages.length >= 6) { // Mostrar botão após 6 mensagens
      setShowFinalizeButton(true);
    }
  }, [messages.length]);

  // Função para finalizar sessão
  const finalizeSession = async () => {
    if (isFinalizing) return;
    
    setIsFinalizing(true);
    console.log('🔚 Iniciando finalização da sessão:', currentSessionId);
    
    try {
      const response = await fetch(`/api/chat/finalize/${currentSessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      console.log('📋 Resultado da finalização:', result);
      
      if (result.success) {
        console.log('✅ Sessão finalizada com sucesso');
        console.log('📄 Contexto da sessão:', result.data.context);
        
        setIsConversationEnded(true);
        setSessionContext(result.data.context);
        setShowSessionSummary(true);
        setShowFinalizeButton(false);
        
        console.log('🎯 States atualizados - Modal deve aparecer agora');
      } else {
        console.error('❌ Erro ao finalizar sessão:', result);
      }
    } catch (error) {
      console.error('❌ Erro na finalização da sessão:', error);
    } finally {
      setIsFinalizing(false);
    }
  };

  // Verificar se mensagem indica fim de conversa
  const checkConversationEnd = (message) => {
    const endings = ['tchau', 'bye', 'adeus', 'até logo', 'até mais', 'obrigado', 'obrigada', 'valeu'];
    const messageLower = message.toLowerCase();
    return endings.some(ending => messageLower.includes(ending));
  };

  // Funções do modo de voz
  const handleVoiceModeToggle = () => {
    setIsVoiceModeOpen(true);
  };

  const handleVoiceModeClose = () => {
    setIsVoiceModeOpen(false);
  };

  const handleVoiceMessage = (message) => {
    // Adicionar mensagem ao estado
    setMessages(prev => [...prev, message]);
  };

  // Função para obter contexto da sessão
  const getSessionContext = async () => {
    try {
      const response = await fetch(`/api/chat/context/${currentSessionId}`);
      const result = await response.json();
      
      if (result.success) {
        setSessionContext(result.data.context);
      }
    } catch (error) {
      console.error('Erro ao obter contexto da sessão:', error);
    }
  };

  // Função para obter a última mensagem da IA
  const getLastAIMessage = () => {
    // Encontrar a última mensagem da IA na lista de mensagens
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].type === 'ai' && messages[i].audioUrl) {
        return messages[i];
      }
    }
    return null;
  };

  // Modal de resumo da sessão
  const SessionSummaryModal = () => {
    console.log('🔍 SessionSummaryModal - States:', {
      showSessionSummary,
      sessionContext,
      hasContext: !!sessionContext
    });
    
    if (!showSessionSummary || !sessionContext) {
      console.log('⚠️ Modal não será mostrado - showSessionSummary:', showSessionSummary, 'sessionContext:', !!sessionContext);
      return null;
    }
    
    console.log('✅ Modal será mostrado com contexto:', sessionContext);
    
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
        <div className="bg-white dark:bg-dark-surface rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
          <div className="p-6">
            <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">
              Resumo da Sessão
            </h2>
            
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">Resumo</h3>
                <p className="text-gray-600 dark:text-gray-400">{sessionContext.summary}</p>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">Temas Principais</h3>
                <div className="flex flex-wrap gap-2">
                  {sessionContext.main_themes?.map((theme, index) => (
                    <span key={index} className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full text-sm">
                      {theme}
                    </span>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">Estado Emocional</h3>
                <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    <strong>Emoção Dominante:</strong> {sessionContext.emotional_state?.dominant_emotion}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    <strong>Jornada:</strong> {sessionContext.emotional_state?.emotional_journey}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    <strong>Estabilidade:</strong> {sessionContext.emotional_state?.stability}
                  </p>
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">Insights Principais</h3>
                <ul className="list-disc list-inside text-gray-600 dark:text-gray-400 space-y-1">
                  {sessionContext.key_insights?.map((insight, index) => (
                    <li key={index} className="text-sm">{insight}</li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">Recomendações</h3>
                <ul className="list-disc list-inside text-gray-600 dark:text-gray-400 space-y-1">
                  {sessionContext.next_session_recommendations?.map((rec, index) => (
                    <li key={index} className="text-sm">{rec}</li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">Qualidade da Sessão</h3>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                  sessionContext.session_quality === 'excelente' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                  sessionContext.session_quality === 'boa' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                  sessionContext.session_quality === 'regular' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                  'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                }`}>
                  {sessionContext.session_quality}
                </span>
              </div>
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <Button
                variant="secondary"
                onClick={() => setShowSessionSummary(false)}
              >
                Fechar
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  setShowSessionSummary(false);
                  navigate('/home', {
                    state: {
                      message: 'Sessão finalizada com sucesso! Sua próxima sessão pode já estar disponível.'
                    }
                  });
                }}
              >
                Voltar ao Início
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-background-light dark:bg-background-dark transition-colors duration-300">
      {/* Header */}
      <div className="relative z-10 bg-white/95 dark:bg-dark-surface/95 backdrop-blur-xl border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="avatar-therapy-calm p-1">
              <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center">
                <Heart className="w-5 h-5 text-primary-500" strokeWidth={2} />
              </div>
            </div>
            <div>
              <h1 className="font-heading font-semibold text-text-primary dark:text-text-primary-dark">
                <span className="text-gradient-therapy">Empath</span>.IA
              </h1>
              <p className="text-sm text-text-secondary dark:text-text-secondary-dark">
                Seu companheiro terapêutico
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <EmotionBadge emotion={currentEmotion} />
            {showFinalizeButton && !isConversationEnded && (
              <Button
                variant="primary"
                size="sm"
                onClick={finalizeSession}
                disabled={isFinalizing}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                {isFinalizing ? 'Finalizando...' : 'Finalizar Sessão'}
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/home')}
              title="Sair da sessão"
            >
              <LogOut className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>

      {/* WebcamEmotionCapture invisível - análise automática em background */}
      <WebcamEmotionCapture 
        onEmotionDetected={handleWebcamEmotion} 
        autoStart={true} 
        hidden={true}
        username={username}
        sessionId={currentSessionId}
      />

      {/* Objetivo da Sessão */}
      {sessionObjective && showObjective && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-b border-blue-200 dark:border-blue-800 px-4 py-3">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <h3 className="font-medium text-blue-900 dark:text-blue-100">
                    {sessionObjective.title}
                  </h3>
                </div>
                {sessionObjective.subtitle && (
                  <p className="text-sm text-blue-700 dark:text-blue-300 mb-2">
                    {sessionObjective.subtitle}
                  </p>
                )}
                <p className="text-sm text-blue-800 dark:text-blue-200 leading-relaxed">
                  <strong>Objetivo:</strong> {sessionObjective.objective}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowObjective(false)}
                className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
              >
                ✕
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Área de mensagens */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-2 sm:px-0 py-4 overflow-y-auto">
        {isLoadingHistory ? (
          <div className="flex-1 flex items-center justify-center">
            <Loading size="lg" text="Carregando conversa..." />
          </div>
        ) : (
          <div className="flex-1 flex flex-col gap-4 pb-4">
            {messages.map((msg, idx) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && <MessageBubble message={{ id: 'typing', type: 'ai', content: '' }} isTyping />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input fixo no rodapé */}
      <div className="w-full max-w-4xl mx-auto px-2 sm:px-0 pb-4 sticky bottom-0 z-20 bg-background-light dark:bg-background-dark">
        <form
          className="flex items-center gap-2 bg-white dark:bg-dark-surface border border-gray-200 dark:border-gray-700 rounded-2xl shadow-md px-4 py-2"
          onSubmit={e => { e.preventDefault(); handleSendMessage(); }}
        >
          <textarea
            ref={inputRef}
            className="flex-1 resize-none bg-transparent outline-none text-sm text-text-primary dark:text-text-primary-dark placeholder-gray-400 py-2"
            rows={1}
            placeholder="Digite sua mensagem..."
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={isLoading}
          />
          <Button
            type="button"
            variant="primary"
            size="icon-lg"
            onClick={handleVoiceModeToggle}
            disabled={isLoading}
            className="mr-2"
            title="Modo de Voz"
          >
            <Mic className="w-5 h-5 md:w-6 md:h-6" />
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="icon-lg"
            disabled={isLoading || !inputValue.trim()}
          >
            <Send className="w-5 h-5 md:w-6 md:h-6" />
          </Button>
        </form>
      </div>
      
      {/* Modal de resumo da sessão */}
      <SessionSummaryModal />
      
      {/* Modo conversacional de voz */}
      <VoiceConversationMode
        sessionId={currentSessionId}
        username={username}
        isOpen={isVoiceModeOpen}
        onClose={handleVoiceModeClose}
        onNewMessage={handleVoiceMessage}
        lastAIMessage={messages.filter(msg => msg.type === 'ai').pop() || null}
      />
    </div>
  );
};

export default ChatScreen;
