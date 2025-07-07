import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { Heart, LogOut, Send, Target } from 'lucide-react';
import { sendMessage, getChatHistory, getTherapeuticSession } from '../../services/api.js';
import Button from '../Common/Button.jsx';
import Loading from '../Common/Loading.jsx';
import EmotionBadge from './EmotionBadge.jsx';
import WebcamEmotionCapture from '../EmotionAnalysis/WebcamEmotionCapture.jsx';

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
          // ✅ CORREÇÃO: Não criar mensagem inicial - deixar que a IA use o prompt da sessão
          // Quando não há histórico, simplesmente deixar a lista de mensagens vazia
          // A primeira mensagem será gerada quando o usuário enviar algo, usando o initial_prompt da sessão
          setMessages([]);
        }
      } catch (error) {
        console.error('Erro ao carregar dados da sessão:', error);
        // ✅ CORREÇÃO: Em caso de erro, também não mostrar mensagem padrão
        // Deixar vazio para que o prompt da sessão seja usado
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
          // Mostrar mensagem de sucesso por alguns segundos
          if (response.data.completion_message) {
            console.log('🎉 Cadastro finalizado:', response.data.completion_message);
          }
          
          // Redirecionar para home após 3 segundos
          setTimeout(() => {
            navigate('/home', { 
              state: { 
                message: 'Cadastro finalizado com sucesso! Agora você pode acessar todas as sessões terapêuticas.' 
              } 
            });
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
            type="submit"
            variant="primary"
            size="icon"
            disabled={isLoading || !inputValue.trim()}
            className="w-8 h-8 md:w-12 md:h-12 flex items-center justify-center"
          >
            <Send className="w-5 h-5 md:w-7 md:h-7" />
          </Button>
        </form>
      </div>
    </div>
  );
};

export default ChatScreen;
