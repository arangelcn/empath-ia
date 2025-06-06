import React, { useState, useRef, useEffect } from 'react'
import { Brain, Send, Loader2, AlertCircle, Info, Settings, Video, MessageCircle, Volume2, VolumeX } from 'lucide-react'
import axios from 'axios'
import AvatarDog from './components/AvatarDog'
import audioService from './services/audioService'

// API service
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

function App() {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showConfig, setShowConfig] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [conversationId, setConversationId] = useState(null)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const [voiceServiceAvailable, setVoiceServiceAvailable] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Inicializar conversa e testar voice service ao carregar componente
  useEffect(() => {
    initializeConversation()
    testVoiceService()
  }, [])

  const testVoiceService = async () => {
    const result = await audioService.testVoiceService()
    setVoiceServiceAvailable(result.available)
    if (result.available) {
      console.log('Voice service configurado e disponível')
    } else {
      console.warn('Voice service não está disponível')
    }
  }

  const generateSessionId = () => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  const initializeConversation = async () => {
    try {
      setIsLoadingHistory(true)
      
      // Gerar ou recuperar session_id do localStorage
      let currentSessionId = localStorage.getItem('empatia_session_id')
      if (!currentSessionId) {
        currentSessionId = generateSessionId()
        localStorage.setItem('empatia_session_id', currentSessionId)
      }
      
      setSessionId(currentSessionId)

      // Tentar recuperar conversa existente
      const response = await api.post('/chat/start', {
        session_id: currentSessionId
      })

      if (response.data.success) {
        const { conversation_id, history, is_new } = response.data.data
        setConversationId(conversation_id)
        
        if (!is_new && history && history.length > 0) {
          // Converter histórico para formato do frontend
          const formattedHistory = history.map(msg => ({
            id: msg.id,
            type: msg.type,
            content: msg.content,
            timestamp: msg.timestamp,
            hasVideo: msg.hasVideo || false,
            videoUrl: msg.videoUrl || null
          }))
          setMessages(formattedHistory)
        }
      }
    } catch (err) {
      console.error('Erro ao inicializar conversa:', err)
      // Se falhar, continuar sem histórico
      const fallbackSessionId = generateSessionId()
      setSessionId(fallbackSessionId)
    } finally {
      setIsLoadingHistory(false)
    }
  }

  const playResponseAudio = async (text) => {
    if (!ttsEnabled || !voiceServiceAvailable || !text) {
      return
    }

    try {
      setIsPlayingAudio(true)
      const result = await audioService.speakText(text, {
        speed: 1.0,
        language: 'pt'
      })

      if (!result.success) {
        console.warn('Falha no TTS:', result.message)
      }
    } catch (error) {
      console.error('Erro ao reproduzir áudio:', error)
    } finally {
      setIsPlayingAudio(false)
    }
  }

  const sendMessage = async (retryCount = 0) => {
    if (!inputValue.trim() || !sessionId) return

    const userMessage = {
      id: `temp_${Date.now()}`,
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setError(null)

    try {
      const response = await api.post('/chat/send', {
        message: inputValue,
        session_id: sessionId
      })

      if (response.data.success) {
        const { user_message, ai_response } = response.data.data
        
        // Atualizar mensagem do usuário com ID real
        setMessages(prev => 
          prev.map(msg => 
            msg.id === userMessage.id 
              ? { ...msg, id: user_message.id, timestamp: user_message.timestamp }
              : msg
          )
        )

        // Adicionar resposta da IA
        const aiMessage = {
          id: ai_response.id,
          type: 'ai',
          content: ai_response.content,
          timestamp: ai_response.timestamp,
          hasVideo: ai_response.hasVideo || false,
          videoUrl: ai_response.videoUrl || null
        }

        setMessages(prev => [...prev, aiMessage])

        // REPRODUZIR ÁUDIO AUTOMATICAMENTE
        if (ai_response.content && ttsEnabled && voiceServiceAvailable) {
          setTimeout(() => {
            playResponseAudio(ai_response.content)
          }, 500) // Aguardar um pouco para garantir que a mensagem foi renderizada
        }

      } else {
        throw new Error(response.data.message || 'Erro desconhecido')
      }
    } catch (err) {
      if (err.code === 'ECONNABORTED' || err.response?.status === 503) {
        if (retryCount < 2) {
          setTimeout(() => sendMessage(retryCount + 1), 2000)
          return
        }
      }

      const errorMessage = {
        id: `error_${Date.now()}`,
        type: 'error',
        content: getErrorMessage(err),
        timestamp: new Date().toISOString(),
      }

      setMessages(prev => [...prev, errorMessage])
      setError(err)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleTTS = () => {
    const newState = audioService.toggleTTS()
    setTtsEnabled(newState)
    
    // Parar áudio atual se desativando TTS
    if (!newState) {
      audioService.stopCurrentAudio()
      setIsPlayingAudio(false)
    }
  }

  const getErrorMessage = (err) => {
    if (err.code === 'ECONNABORTED') {
      return '⏱️ Timeout na conexão com o backend.'
    }
    if (err.response?.status === 503) {
      return '❌ Serviço temporariamente indisponível. Tentando novamente...'
    }
    if (!navigator.onLine) {
      return '📶 Verifique sua conexão com a internet.'
    }
    return `❌ Erro inesperado: ${err.response?.data?.detail || err.message || 'Falha na comunicação'}`
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const startNewConversation = () => {
    // Limpar dados da conversa atual
    localStorage.removeItem('empatia_session_id')
    setMessages([])
    setSessionId(null)
    setConversationId(null)
    
    // Inicializar nova conversa
    initializeConversation()
  }

  const MessageBubble = ({ message }) => {
    const isUser = message.type === 'user'
    const isError = message.type === 'error'
    const isAI = message.type === 'ai'

    return (
      <div className={`flex mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
        <div
          className={`message-bubble ${
            isUser
              ? 'user-message'
              : isError
              ? 'bg-red-100 text-red-800 border border-red-300'
              : 'ai-message'
          }`}
        >
          <div className="flex items-start gap-2">
            {!isUser && !isError && (
              <Brain className="w-5 h-5 text-primary-600 mt-0.5 flex-shrink-0" />
            )}
            <div className="flex-1">
              <div className="flex items-start justify-between">
                <p className="text-sm flex-1">{message.content}</p>
                
                {/* Audio Indicator for AI messages */}
                {isAI && ttsEnabled && voiceServiceAvailable && (
                  <div className="ml-2 flex items-center gap-1">
                    {isPlayingAudio ? (
                      <div className="flex items-center gap-1 text-blue-500">
                        <Volume2 className="w-3 h-3 animate-pulse" />
                        <span className="text-xs">♪</span>
                      </div>
                    ) : (
                      <Volume2 className="w-3 h-3 text-gray-400" />
                    )}
                  </div>
                )}
              </div>
              
              {message.hasVideo && message.videoUrl && (
                <div className="mt-3">
                  <div className="flex items-center gap-2 text-green-600 text-sm mb-2">
                    <Video className="w-4 h-4" />
                    Vídeo do avatar gerado com sucesso!
                  </div>
                  <video
                    controls
                    className="w-full max-w-sm rounded-lg"
                    src={message.videoUrl}
                  >
                    Seu navegador não suporta vídeos.
                  </video>
                </div>
              )}
              
              {message.videoUrl === null && message.type === 'ai' && (
                <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
                  <div className="flex items-center gap-2">
                    <MessageCircle className="w-4 h-4" />
                    Resposta em texto{ttsEnabled && voiceServiceAvailable ? ' + áudio' : ''}
                  </div>
                  <p className="text-xs mt-1 text-blue-600">
                    {!voiceServiceAvailable 
                      ? '🔧 Voice service offline - apenas texto'
                      : '🔧 Verifique se a DID_API_KEY está configurada para vídeos'
                    }
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isLoadingHistory) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center">
        <div className="text-center text-white">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4" />
          <p className="text-lg">Carregando conversa...</p>
          <p className="text-sm opacity-80">Recuperando seu histórico</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen gradient-bg">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <AvatarDog />
          <div className="flex items-center justify-center gap-3 mb-4 mt-4">
            <Brain className="w-10 h-10 text-white" />
            <h1 className="text-4xl font-bold text-white">empatIA</h1>
          </div>
          <p className="text-white/80 text-lg">
            Converse com um psicólogo virtual animado e empático.
          </p>
          
          {/* Session Info */}
          {sessionId && (
            <div className="mt-4 flex items-center justify-center gap-4">
              <p className="text-white/60 text-sm">
                Sessão: {sessionId.slice(-8)}
              </p>
              <button
                onClick={startNewConversation}
                className="text-white/80 hover:text-white text-sm underline"
              >
                Nova conversa
              </button>
            </div>
          )}

          {/* TTS Controls */}
          <div className="mt-4 flex items-center justify-center gap-4">
            <button
              onClick={toggleTTS}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                ttsEnabled 
                  ? 'bg-green-600/20 text-green-300 hover:bg-green-600/30' 
                  : 'bg-gray-600/20 text-gray-400 hover:bg-gray-600/30'
              }`}
              title={ttsEnabled ? 'Desativar áudio automático' : 'Ativar áudio automático'}
            >
              {ttsEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              {ttsEnabled ? 'Áudio ON' : 'Áudio OFF'}
            </button>

            {voiceServiceAvailable && (
              <div className="flex items-center gap-2 text-green-400 text-xs">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                Voice Service Online
              </div>
            )}

            {!voiceServiceAvailable && (
              <div className="flex items-center gap-2 text-orange-400 text-xs">
                <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
                Voice Service Offline
              </div>
            )}

            {isPlayingAudio && (
              <div className="flex items-center gap-2 text-blue-400 text-xs">
                <Loader2 className="w-3 h-3 animate-spin" />
                Reproduzindo...
              </div>
            )}
          </div>
        </div>

        {/* Chat Container */}
        <div className="glass-effect rounded-2xl p-6 shadow-2xl">
          {/* Messages */}
          <div className="h-96 overflow-y-auto mb-4 pr-2">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 mt-20">
                <Brain className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p>Olá! Como posso ajudá-lo hoje?</p>
                <p className="text-sm mt-2">
                  Digite sua mensagem abaixo para começar nossa conversa.
                </p>
                <p className="text-xs mt-4 text-gray-400">
                  💾 Suas conversas são salvas automaticamente
                </p>
              </div>
            )}
            
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            
            {isLoading && (
              <div className="flex justify-start mb-4">
                <div className="ai-message message-bubble">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
                    <span className="text-gray-600">Pensando...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="flex gap-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Digite sua mensagem..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button
              onClick={() => sendMessage()}
              disabled={isLoading || !inputValue.trim()}
              className="px-6 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
              Enviar
            </button>
          </div>
        </div>

        {/* Config Info */}
        <div className="mt-6">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center gap-2 text-white/80 hover:text-white transition-colors"
          >
            <Info className="w-4 h-4" />
            Informações sobre configuração
          </button>
          
          {showConfig && (
            <div className="mt-4 glass-effect rounded-xl p-4 text-sm">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Sistema com persistência MongoDB:
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="bg-green-50 p-3 rounded-lg">
                  <h4 className="font-medium text-green-800 mb-2">✅ Recursos Ativos:</h4>
                  <ul className="text-xs text-green-700 space-y-1">
                    <li>• Histórico de conversas salvo</li>
                    <li>• Persistência em MongoDB</li>
                    <li>• Session management</li>
                    <li>• Recuperação automática</li>
                  </ul>
                </div>
                
                <div className="bg-blue-50 p-3 rounded-lg">
                  <h4 className="font-medium text-blue-800 mb-2">🔧 Para avatares em vídeo:</h4>
                  <ul className="text-xs text-blue-700 space-y-1">
                    <li>• Configure DID_API_USERNAME</li>
                    <li>• Configure DID_API_PASSWORD</li>
                    <li>• Reinicie os containers</li>
                  </ul>
                </div>
              </div>
              
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <h4 className="font-medium mb-2">Arquivo .env exemplo:</h4>
                <pre className="text-xs bg-gray-800 text-green-400 p-2 rounded overflow-x-auto">
{`OPENAI_API_KEY=sua_chave_openai
DID_API_USERNAME=seu_username
DID_API_PASSWORD=sua_senha
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=empatia_db`}
                </pre>
              </div>
              
              <div className="mt-3 space-y-1 text-xs">
                <p><strong>💾 Dados persistidos:</strong> Conversas e mensagens salvos automaticamente</p>
                <p><strong>🔄 Session ID:</strong> {sessionId || 'Carregando...'}</p>
                <p><strong>📝 Total de mensagens:</strong> {messages.length}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App 