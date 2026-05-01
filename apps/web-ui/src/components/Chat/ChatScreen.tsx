import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { Bot, CheckCircle2, ChevronLeft, Heart, Mic, Send, Sparkles, Target, X } from 'lucide-react';
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
  authorName?: string;
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
    <div className={`group flex w-full animate-fade-in ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[94%] gap-3 sm:max-w-[86%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div
          className={`mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border shadow-sm
            ${isUser
              ? 'border-primary-200 bg-primary-50 text-primary-600 dark:border-primary-700/60 dark:bg-primary-900/30 dark:text-primary-200'
              : 'border-gray-200 bg-white text-primary-500 dark:border-gray-700 dark:bg-dark-surface dark:text-secondary-300'
            }
          `}
          aria-hidden="true"
        >
          {isUser ? (
            <span className="text-xs font-semibold">{(message.authorName || 'Você').charAt(0).toUpperCase()}</span>
          ) : (
            <Bot className="h-4 w-4" strokeWidth={2} />
          )}
        </div>

        <div className={`flex min-w-0 flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <span className="mb-1 px-1 text-[11px] font-medium uppercase tracking-[0.08em] text-gray-400 dark:text-gray-500">
            {isUser ? 'Você' : 'Empat.IA'}
          </span>
          <div className={`rounded-2xl px-4 py-3 text-[15px] leading-7 transition-all duration-200
            ${isUser 
              ? 'rounded-tr-md bg-primary-600 text-white shadow-sm shadow-primary-500/20' 
              : 'rounded-tl-md border border-gray-200/80 bg-white text-gray-900 shadow-sm dark:border-gray-700/80 dark:bg-dark-surface dark:text-gray-100'
            }
          `}>
            {isTyping ? (
              <div className="flex items-center gap-3 text-gray-500 dark:text-gray-300">
                <div className="flex space-x-1.5">
                  <div className="h-2 w-2 rounded-full bg-current animate-pulse"></div>
                  <div className="h-2 w-2 rounded-full bg-current animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                  <div className="h-2 w-2 rounded-full bg-current animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                </div>
                <span className="text-xs font-medium">Digitando...</span>
              </div>
            ) : (
              <p className="whitespace-pre-wrap break-words">{message.content}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const EmptyConversation = ({ sessionTitle }) => (
  <div className="mx-auto flex max-w-xl flex-1 flex-col items-center justify-center px-6 py-16 text-center">
    <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-full border border-primary-100 bg-white text-primary-500 shadow-sm dark:border-primary-800/60 dark:bg-dark-surface">
      <Sparkles className="h-6 w-6" strokeWidth={2} />
    </div>
    <h2 className="text-xl font-semibold text-text-primary dark:text-text-primary-dark">
      {sessionTitle || 'Vamos começar com calma'}
    </h2>
    <p className="mt-3 text-sm leading-6 text-text-secondary dark:text-text-secondary-dark">
      Respire um instante. Sem pressa.
    </p>
  </div>
);

const ChatComposer = ({
  inputRef,
  inputValue,
  isLoading,
  onChange,
  onKeyDown,
  onSubmit,
  onVoiceModeToggle,
}) => {
  const canSend = inputValue.trim().length > 0 && !isLoading;

  return (
    <div className="border-t border-gray-200/80 bg-background-light/95 px-4 py-4 backdrop-blur-xl dark:border-gray-800 dark:bg-background-dark/95">
      <form
        className="chat-composer mx-auto flex max-w-4xl items-end gap-2 rounded-[1.35rem] border border-gray-200 bg-white p-2 shadow-lg shadow-primary-900/5 transition-colors dark:border-gray-700 dark:bg-dark-surface dark:shadow-black/20"
        onSubmit={e => {
          e.preventDefault();
          if (canSend) {
            onSubmit();
            requestAnimationFrame(() => {
              if (inputRef.current) {
                inputRef.current.style.height = '44px';
              }
            });
          }
        }}
      >
        <textarea
          ref={inputRef}
          className="max-h-40 min-h-[44px] flex-1 resize-none overflow-y-auto rounded-2xl border-0 bg-transparent px-3 py-3 text-[15px] leading-6 text-text-primary placeholder:text-gray-400 focus:ring-0 dark:text-text-primary-dark dark:placeholder:text-gray-500"
          rows={1}
          placeholder="Mensagem para Empat.IA"
          value={inputValue}
          onChange={e => {
            onChange(e.target.value);
            e.currentTarget.style.height = '44px';
            e.currentTarget.style.height = `${Math.min(e.currentTarget.scrollHeight, 160)}px`;
          }}
          onKeyDown={onKeyDown}
          disabled={isLoading}
        />
        <Button
          type="button"
          variant="ghost"
          size="icon-lg"
          onClick={onVoiceModeToggle}
          disabled={isLoading}
          className="shrink-0 text-gray-500 hover:bg-gray-100 hover:text-primary-600 dark:text-gray-300 dark:hover:bg-gray-800"
          title="Modo de voz"
        >
          <Mic className="h-5 w-5" />
        </Button>
        <Button
          type="submit"
          variant="primary"
          size="icon-lg"
          disabled={!canSend}
          className="shrink-0 rounded-full bg-primary-600 shadow-none hover:bg-primary-700"
          title="Enviar mensagem"
        >
          <Send className="h-5 w-5" />
        </Button>
      </form>
      <p className="mx-auto mt-2 max-w-4xl px-3 text-center text-[11px] text-gray-400 dark:text-gray-500">
        Empat.IA pode cometer erros. Use a conversa como apoio, não como substituto de cuidado profissional.
      </p>
    </div>
  );
};

const ChatScreen = ({ username, displayName, sessionId: fallbackSessionId }) => {
  const { chatId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { playAudio } = useAudioPlayer();
  
  // Usar chat_id opaco da URL. sessionId legado ainda é aceito como fallback.
  const currentChatId = chatId || fallbackSessionId;
  const participantName = displayName || username || 'você';
  
  // Obter informações da sessão do state (passado pelo navigate)
  const sessionInfo = location.state || {};
  const { sessionTitle, originalSessionId: stateOriginalSessionId } = sessionInfo;
  const originalSessionId = useMemo(() => {
    if (stateOriginalSessionId) {
      return stateOriginalSessionId;
    }

    if (!currentChatId) {
      return '';
    }

    if (username && currentChatId.startsWith(`${username}_`)) {
      return currentChatId.slice(username.length + 1);
    }

    const sessionMatch = currentChatId.match(/session-.+$/);
    return sessionMatch?.[0] || '';
  }, [currentChatId, stateOriginalSessionId, username]);
  
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
        if (currentChatId) {
          try {
            console.log('🔍 Buscando sessão - currentChatId:', currentChatId, 'originalSessionId:', originalSessionId);
            
            if (originalSessionId) {
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
            }
          } catch (error) {
            console.warn('Erro ao carregar objetivo da sessão:', error);
          }
        }
        
        // Carregar histórico de mensagens
        const response = await getChatHistory(currentChatId);
        
        if (response.success && response.data.history && response.data.history.length > 0) {
          // Converter histórico do backend para o formato do frontend
          const historyMessages: Message[] = response.data.history.map((msg: any) => ({
            id: msg.id,
            type: msg.type === 'user' ? 'user' : 'ai',
            content: msg.content,
            audioUrl: msg.audio_url || undefined,
            authorName: msg.type === 'user' ? participantName : undefined,
          }));
          
          setMessages(historyMessages);
        } else {
          // ✅ NOVO: Se não há histórico, tentar gerar mensagem inicial automática
          console.log('🤖 Sessão sem histórico, gerando mensagem inicial automática...');
          
          try {
            const initialMessageResponse = await getInitialMessage(currentChatId);
            console.log('🔍 DEBUG - Resposta inicial:', initialMessageResponse);
            
            if (initialMessageResponse.success && initialMessageResponse.data) {
              // ✅ CORREÇÃO: Aguardar um pouco para garantir que o backend salvou a mensagem
              console.log('⏳ Aguardando backend finalizar salvamento...');
              await new Promise(resolve => setTimeout(resolve, 1000));
              
              // ✅ CORREÇÃO: Recarregar histórico DIRETAMENTE após gerar mensagem inicial
              console.log('🔄 Recarregando histórico após mensagem inicial...');
              const updatedHistory = await getChatHistory(currentChatId);
              console.log('🔍 DEBUG - Histórico atualizado:', updatedHistory);
              
              if (updatedHistory.success && updatedHistory.data.history && updatedHistory.data.history.length > 0) {
                const historyMessages: Message[] = updatedHistory.data.history.map((msg: any) => ({
                  id: msg.id,
                  type: msg.type === 'user' ? 'user' : 'ai',
                  content: msg.content,
                  audioUrl: msg.audio_url || undefined,
                  authorName: msg.type === 'user' ? participantName : undefined,
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

    if (currentChatId && username) {
      loadSessionData();
    }
  }, [currentChatId, originalSessionId, participantName, username]);

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
      authorName: participantName,
    };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      // ✅ CORREÇÃO: Para session-1 (cadastro), não passar sessionObjective 
      // Para outras sessões, passar apenas se for a primeira mensagem
      const isFirstMessage = messages.length === 0;
      
      // session-1 é a sessão de cadastro, não deve receber título/objetivo
      const isRegistrationSession = originalSessionId === 'session-1';
      
      let objectiveToSend = null;
      if (isFirstMessage && !isRegistrationSession) {
        // Apenas para sessões que NÃO são de cadastro
        objectiveToSend = sessionObjective;
      }
      
      console.log(`🔍 Session Info: originalSessionId=${originalSessionId}, isRegistrationSession=${isRegistrationSession}, isFirstMessage=${isFirstMessage}, willSendObjective=${objectiveToSend !== null}`);
      
      const response = await sendMessage(currentInput, currentChatId, objectiveToSend);
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
      requestAnimationFrame(() => {
        if (inputRef.current) {
          inputRef.current.style.height = '44px';
        }
      });
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
    console.log('🔚 Iniciando finalização da sessão:', currentChatId);
    
    try {
      const response = await fetch(`/api/chat/finalize/${currentChatId}`, {
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
      const response = await fetch(`/api/chat/context/${currentChatId}`);
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

  const displaySessionTitle = sessionTitle || sessionObjective?.title || 'Sessão terapêutica';
  const displaySessionSubtitle = sessionObjective?.subtitle || `Conversando com ${participantName}`;

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col overflow-hidden bg-background-light text-text-primary transition-colors duration-300 dark:bg-background-dark dark:text-text-primary-dark lg:h-screen">
      {/* Header */}
      <div className="relative z-10 border-b border-gray-200/80 bg-white/90 px-4 py-3 backdrop-blur-xl dark:border-gray-800 dark:bg-dark-surface/90">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/home')}
              title="Voltar"
              className="shrink-0 text-gray-500 hover:text-primary-600 dark:text-gray-300"
            >
              <ChevronLeft className="h-5 w-5" />
            </Button>
            <div className="avatar-therapy-calm hidden p-1 sm:block">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white">
                <Heart className="h-5 w-5 text-primary-500" strokeWidth={2} />
              </div>
            </div>
            <div className="min-w-0">
              <h1 className="truncate font-heading text-base font-semibold text-text-primary dark:text-text-primary-dark">
                {displaySessionTitle}
              </h1>
              <p className="truncate text-xs text-text-secondary dark:text-text-secondary-dark">
                {displaySessionSubtitle}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <EmotionBadge emotion={currentEmotion} />
            {showFinalizeButton && !isConversationEnded && (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={finalizeSession}
                  disabled={isFinalizing}
                  className="hidden bg-green-600 text-white hover:bg-green-700 sm:inline-flex"
                >
                  {isFinalizing ? 'Finalizando...' : 'Finalizar Sessão'}
                </Button>
                <Button
                  variant="primary"
                  size="icon"
                  onClick={finalizeSession}
                  disabled={isFinalizing}
                  className="bg-green-600 text-white hover:bg-green-700 sm:hidden"
                  title="Finalizar sessão"
                >
                  <CheckCircle2 className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* WebcamEmotionCapture invisível - análise automática em background */}
      <WebcamEmotionCapture 
        onEmotionDetected={handleWebcamEmotion} 
        autoStart={true} 
        hidden={true}
        username={username}
        sessionId={currentChatId}
      />

      {/* Objetivo da Sessão */}
      {sessionObjective && showObjective && (
        <div className="border-b border-primary-100 bg-primary-50/70 px-4 py-3 dark:border-primary-900/50 dark:bg-primary-900/15">
          <div className="mx-auto max-w-4xl">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="mb-1.5 flex items-center gap-2">
                  <Target className="h-4 w-4 shrink-0 text-primary-600 dark:text-primary-300" />
                  <h3 className="truncate text-sm font-semibold text-primary-900 dark:text-primary-100">
                    {sessionObjective.title}
                  </h3>
                </div>
                {sessionObjective.subtitle && (
                  <p className="mb-1 text-sm text-primary-700 dark:text-primary-200">
                    {sessionObjective.subtitle}
                  </p>
                )}
                <p className="text-sm leading-6 text-primary-800 dark:text-primary-100/90">
                  <strong>Objetivo:</strong> {sessionObjective.objective}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowObjective(false)}
                className="shrink-0 text-primary-600 hover:bg-primary-100 hover:text-primary-800 dark:text-primary-200 dark:hover:bg-primary-900/40"
                title="Ocultar objetivo"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Área de mensagens */}
      <div className="flex-1 overflow-y-auto px-4">
        {isLoadingHistory ? (
          <div className="flex h-full items-center justify-center">
            <Loading size="lg" text="Carregando conversa..." />
          </div>
        ) : (
          <div className="mx-auto flex min-h-full max-w-4xl flex-col gap-5 py-6">
            {messages.length === 0 && !isLoading ? (
              <EmptyConversation sessionTitle={displaySessionTitle} />
            ) : (
              messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))
            )}
            {isLoading && <MessageBubble message={{ id: 'typing', type: 'ai', content: '' }} isTyping />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input fixo no rodapé */}
      <ChatComposer
        inputRef={inputRef}
        inputValue={inputValue}
        isLoading={isLoading}
        onChange={setInputValue}
        onKeyDown={handleKeyPress}
        onSubmit={handleSendMessage}
        onVoiceModeToggle={handleVoiceModeToggle}
      />
      
      {/* Modal de resumo da sessão */}
      <SessionSummaryModal />
      
      {/* Modo conversacional de voz */}
      <VoiceConversationMode
        sessionId={currentChatId}
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
