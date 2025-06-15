import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Brain, Volume2 } from 'lucide-react';
import { sendMessage } from '../../services/api.js';
import { useAudioPlayer } from '../../hooks/useAudioPlayer.js';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  audioUrl?: string;
}

const fetchEmotion = async () => {
  await new Promise(resolve => setTimeout(resolve, 1000));
  if (Math.random() > 0.9) throw new Error('Falha ao buscar emoção');
  const emotions = ['Feliz', 'Triste', 'Neutro', 'Surpreso', 'Com Raiva'];
  return { emotion: emotions[Math.floor(Math.random() * emotions.length)] };
};

const EmotionBadge = ({ emotion }) => {
  const emotionMap = {
    'Feliz': { emoji: '😊', style: 'bg-green-100 text-green-800' },
    'Triste': { emoji: '😢', style: 'bg-blue-100 text-blue-800' },
    'Neutro': { emoji: '😐', style: 'bg-gray-100 text-gray-800' },
    'Surpreso': { emoji: '😮', style: 'bg-yellow-100 text-yellow-800' },
    'Com Raiva': { emoji: '😠', style: 'bg-red-100 text-red-800' },
  };
  const current = emotionMap[emotion] || emotionMap['Neutro'];
  return (
    <div className={`absolute top-4 right-4 flex items-center gap-2 rounded-full px-3 py-1 shadow-md text-sm font-medium ${current.style}`}>
      <span>{current.emoji}</span>
      <span>{emotion}</span>
    </div>
  );
};

const ChatScreen = ({ sessionId, username }) => {
  const [messages, setMessages] = useState<Message[]>([
    { id: `initial-${Date.now()}`, type: 'ai', content: `Olá, ${username}! Como posso te ajudar hoje?` }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState('Neutro');
  const messagesEndRef = useRef(null);
  const { playAudio, isPlaying, activeAudioUrl } = useAudioPlayer();

  useEffect(() => {
    const intervalId = setInterval(async () => {
      try {
        const response = await fetchEmotion();
        setCurrentEmotion(response.emotion);
      } catch (error) {
        setCurrentEmotion('Neutro');
      }
    }, 5000);
    return () => clearInterval(intervalId);
  }, []);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.type === 'ai' && lastMessage.audioUrl) {
      setTimeout(() => {
        playAudio(lastMessage.audioUrl, () => {});
      }, 100);
    }
  }, [messages]);

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
      const response = await sendMessage(currentInput, sessionId);
      if (response.success) {
        const { ai_response } = response.data;
        const aiMessage: Message = {
          id: ai_response.id,
          type: 'ai',
          content: ai_response.content,
          audioUrl: ai_response.audioUrl,
        };
        setMessages(prev => [...prev, aiMessage]);

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
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="relative flex flex-col h-[80vh] bg-gray-50 p-4 rounded-2xl shadow-lg">
      <EmotionBadge emotion={currentEmotion} />
      
      <div className="flex-1 overflow-y-auto mb-4 p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex items-start gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
             {message.type === 'ai' && (
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white flex-shrink-0">
                <Brain size={20} />
              </div>
            )}
            <div className={`max-w-lg p-3 rounded-lg flex items-center ${
                message.type === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-800 border border-gray-200'
              }`}>
              <p className="flex-1">{message.content}</p>
              {message.type === 'ai' && message.audioUrl && (
                <button
                  onClick={() => playAudio(message.audioUrl, () => {})}
                  className={`ml-2 text-gray-500 hover:text-blue-700`}
                >
                  <Volume2 size={16} className={activeAudioUrl === message.audioUrl && isPlaying ? 'animate-pulse text-blue-500' : ''} />
                </button>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-start gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white flex-shrink-0">
              <Brain size={20} />
            </div>
            <div className="max-w-lg p-3 rounded-lg bg-white text-gray-800 border border-gray-200">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                <span>Pensando...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="mt-auto flex gap-3 p-4 bg-white border-t border-gray-200 rounded-b-2xl">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Digite sua mensagem..."
          disabled={isLoading}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSendMessage}
          disabled={isLoading || !inputValue.trim()}
          className="px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 flex items-center gap-2"
        >
          {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          <span>Enviar</span>
        </button>
      </div>
    </div>
  );
};

export default ChatScreen;
