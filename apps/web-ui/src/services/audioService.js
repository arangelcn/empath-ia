/**
 * Serviço de áudio para Text-to-Speech - Integração com Voice Service Aprimorado v2.0.0
 */

class AudioService {
  constructor() {
    this.isEnabled = true
    this.currentAudio = null
    this.baseURL = '/api'
    
    // Detectar ambiente - se em Docker, usar proxy, senão usar URL direta
    this.voiceServiceURL = window.location.hostname === 'localhost' 
      ? 'http://localhost:8004' 
      : '/voice-service' // Proxy do Vite
      
    this.currentModel = 'vits_pt' // Modelo padrão
    this.availableModels = {}
    this.serviceInfo = null
    
    // Configurações de qualidade
    this.defaultSpeed = 1.0
    this.defaultLanguage = 'pt'
    
    console.log('🎤 AudioService Enhanced v2.0.0 inicializado')
    console.log('🔗 Voice Service URL:', this.voiceServiceURL)
  }

  /**
   * Inicializa o serviço e carrega informações dos modelos
   */
  async initialize() {
    try {
      const serviceInfo = await this.getServiceInfo()
      if (serviceInfo) {
        this.serviceInfo = serviceInfo
        this.currentModel = serviceInfo.current_model
        this.availableModels = serviceInfo.models_available || []
        console.log('🎯 Voice Service conectado:', {
          modelo: this.currentModel,
          modelos_disponíveis: this.availableModels
        })
      }
    } catch (error) {
      console.warn('⚠️ Falha ao conectar com Voice Service:', error.message)
    }
  }

  /**
   * Obtém informações do serviço de voz
   */
  async getServiceInfo() {
    try {
      const response = await fetch(`${this.voiceServiceURL}/`, {
        method: 'GET',
        timeout: 10000
      })

      if (response.ok) {
        return await response.json()
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      // Fallback para gateway se voice service direto falhar
      try {
        const response = await fetch(`${this.baseURL}/voice/info`, {
          method: 'GET',
          timeout: 10000
        })
        
        if (response.ok) {
          return await response.json()
        }
      } catch (fallbackError) {
        console.warn('Gateway também falhou:', fallbackError.message)
      }
      
      throw error
    }
  }

  /**
   * Verifica status do modelo TTS
   */
  async getModelStatus() {
    try {
      const response = await fetch(`${this.voiceServiceURL}/api/voice/models/status`, {
        method: 'GET',
        timeout: 10000
      })

      if (response.ok) {
        const status = await response.json()
        this.currentModel = status.current_model
        return status
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.warn('Erro ao obter status do modelo:', error.message)
      return null
    }
  }

  /**
   * Lista modelos disponíveis
   */
  async getAvailableModels() {
    try {
      const response = await fetch(`${this.voiceServiceURL}/api/voice/models/available`, {
        method: 'GET',
        timeout: 10000
      })

      if (response.ok) {
        const data = await response.json()
        this.availableModels = data.available_models || {}
        return data
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.warn('Erro ao obter modelos disponíveis:', error.message)
      return { available_models: {}, descriptions: {} }
    }
  }

  /**
   * Troca o modelo TTS
   */
  async changeModel(modelKey) {
    try {
      const response = await fetch(`${this.voiceServiceURL}/api/voice/models/change`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_key: modelKey }),
        timeout: 30000
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success) {
          this.currentModel = modelKey
          console.log(`✅ Modelo alterado para: ${modelKey}`)
          return { success: true, data: result }
        } else {
          throw new Error(result.message || 'Falha ao trocar modelo')
        }
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.error('❌ Erro ao trocar modelo:', error.message)
      return { success: false, error: error.message }
    }
  }

  /**
   * Sintetiza e reproduz texto em áudio com suporte aprimorado
   * @param {string} text - Texto para converter em áudio
   * @param {Object} options - Opções de configuração
   */
  async speakText(text, options = {}) {
    try {
      // Parar áudio atual se estiver tocando
      this.stopCurrentAudio()

      if (!this.isEnabled) {
        console.log('🔇 TTS desabilitado')
        return { success: false, message: 'TTS desabilitado' }
      }

      const requestData = {
        text: text.substring(0, 1000), // Aumentar limite para melhor experiência
        voice_speed: options.speed || this.defaultSpeed,
        language: options.language || this.defaultLanguage
      }

      console.log('🎤 Solicitando TTS para:', `"${text.substring(0, 50)}..."`)
      console.log('📊 Configurações:', {
        modelo: this.currentModel,
        velocidade: requestData.voice_speed,
        idioma: requestData.language
      })

      // Tentar voice service direto primeiro (melhor performance)
      let response
      let data

      try {
        response = await fetch(`${this.voiceServiceURL}/speak`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData),
          timeout: 30000
        })

        if (response.ok) {
          data = await response.json()
        } else {
          throw new Error(`Voice Service HTTP ${response.status}`)
        }
      } catch (directError) {
        console.warn('⚠️ Voice service direto falhou, tentando via gateway:', directError.message)
        
        // Fallback para gateway
        response = await fetch(`${this.baseURL}/voice/speak`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData),
          timeout: 30000
        })

        if (!response.ok) {
          throw new Error(`Gateway HTTP ${response.status}: ${response.statusText}`)
        }

        data = await response.json()
      }

      if (data.success && data.audio_url) {
        console.log('✅ TTS gerado com sucesso:', {
          arquivo: data.filename,
          duração: `${data.duration?.toFixed(2)}s`,
          modelo: this.currentModel,
          url: data.audio_url
        })
        
        await this.playAudioFromUrl(data.audio_url)
        return { success: true, data }
      } else {
        throw new Error(data.message || 'Falha na geração de áudio')
      }

    } catch (error) {
      console.error('❌ Erro no TTS:', error)
      return { 
        success: false, 
        message: `Erro TTS: ${error.message}`,
        error 
      }
    }
  }

  /**
   * Sintetiza texto com clonagem de voz (se suportado)
   * @param {string} text - Texto para converter
   * @param {File|string} voiceReference - Arquivo ou URL de referência de voz
   * @param {Object} options - Opções adicionais
   */
  async speakWithVoiceCloning(text, voiceReference, options = {}) {
    try {
      if (!this.isEnabled) {
        return { success: false, message: 'TTS desabilitado' }
      }

      // Verificar se o modelo atual suporta clonagem
      if (!['xtts_v2', 'your_tts'].includes(this.currentModel)) {
        console.warn('⚠️ Modelo atual não suporta clonagem de voz')
        return this.speakText(text, options) // Fallback para síntese normal
      }

      this.stopCurrentAudio()

      const formData = new FormData()
      formData.append('text', text.substring(0, 1000))
      formData.append('voice_speed', options.speed || this.defaultSpeed)
      
      if (voiceReference instanceof File) {
        formData.append('voice_file', voiceReference)
      } else {
        // Se for URL, baixar primeiro (implementação futura)
        throw new Error('URL de referência não implementada ainda')
      }

      console.log('🎭 Solicitando TTS com clonagem de voz:', {
        texto: `"${text.substring(0, 50)}..."`,
        modelo: this.currentModel,
        arquivo_referencia: voiceReference.name || 'arquivo'
      })

      const response = await fetch(`${this.voiceServiceURL}/api/voice/clone-voice`, {
        method: 'POST',
        body: formData,
        timeout: 60000 // Mais tempo para clonagem
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      if (data.success && data.audio_url) {
        console.log('✅ TTS com clonagem gerado:', {
          arquivo: data.filename,
          duração: `${data.duration?.toFixed(2)}s`
        })
        
        await this.playAudioFromUrl(data.audio_url)
        return { success: true, data }
      } else {
        throw new Error(data.message || 'Falha na clonagem de voz')
      }

    } catch (error) {
      console.error('❌ Erro na clonagem de voz:', error)
      // Fallback para síntese normal
      return this.speakText(text, options)
    }
  }

  /**
   * Reproduz áudio a partir de uma URL com melhor tratamento de erros
   * @param {string} audioUrl - URL do arquivo de áudio
   */
  async playAudioFromUrl(audioUrl) {
    return new Promise((resolve, reject) => {
      try {
        // Processar URL para garantir acesso correto
        let finalAudioUrl = this.processAudioUrl(audioUrl)
        
        this.currentAudio = new Audio(finalAudioUrl)
        
        // Configurar eventos
        this.currentAudio.onloadstart = () => {
          console.log('📥 Carregando áudio...')
        }

        this.currentAudio.onloadeddata = () => {
          console.log('📁 Áudio carregado, iniciando reprodução')
        }

        this.currentAudio.onplay = () => {
          console.log('▶️ Reprodução iniciada')
        }

        this.currentAudio.onended = () => {
          console.log('✅ Reprodução finalizada')
          this.currentAudio = null
          resolve()
        }

        this.currentAudio.onerror = (error) => {
          console.error('❌ Erro na reprodução:', error)
          this.currentAudio = null
          reject(error)
        }

        this.currentAudio.onpause = () => {
          console.log('⏸️ Reprodução pausada')
        }

        // Configurar volume e qualidade
        this.currentAudio.volume = 0.8
        this.currentAudio.preload = 'auto'

        // Tentar reproduzir
        this.currentAudio.play().catch(error => {
          console.error('❌ Erro ao iniciar reprodução:', error)
          reject(error)
        })

      } catch (error) {
        console.error('❌ Erro ao criar áudio:', error)
        reject(error)
      }
    })
  }

  /**
   * Processa URL do áudio para garantir acesso correto
   */
  processAudioUrl(audioUrl) {
    // Se for URL completa do voice service, manter
    if (audioUrl.includes('http://localhost:8004')) {
      return audioUrl
    }
    
    // Se estivermos usando proxy, converter para usar proxy
    if (this.voiceServiceURL === '/voice-service') {
      if (audioUrl.includes('localhost:8004')) {
        return audioUrl.replace('http://localhost:8004', '/voice-service')
      }
      if (audioUrl.startsWith('/audio/')) {
        return `/voice-service${audioUrl}`
      }
    }
    
    // Se for do gateway, converter para voice service direto para melhor performance
    if (audioUrl.includes('localhost:8000/api/voice')) {
      if (this.voiceServiceURL === '/voice-service') {
        return audioUrl.replace('localhost:8000/api/voice', '/voice-service')
      } else {
        return audioUrl.replace('localhost:8000/api/voice', 'localhost:8004')
      }
    }
    
    // Caso contrário, tentar construir URL correta
    if (audioUrl.startsWith('/api/voice/audio/')) {
      return audioUrl.replace('/api/voice', this.voiceServiceURL)
    }
    
    return audioUrl
  }

  /**
   * Para o áudio atual
   */
  stopCurrentAudio() {
    if (this.currentAudio) {
      this.currentAudio.pause()
      this.currentAudio.currentTime = 0
      this.currentAudio = null
      console.log('⏹️ Áudio interrompido')
    }
  }

  /**
   * Verifica se há áudio tocando
   */
  isPlaying() {
    return this.currentAudio && !this.currentAudio.paused
  }

  /**
   * Ativa/desativa TTS
   */
  toggleTTS() {
    this.isEnabled = !this.isEnabled
    console.log(`🔊 TTS ${this.isEnabled ? 'ativado' : 'desativado'}`)
    return this.isEnabled
  }

  /**
   * Verifica se TTS está habilitado
   */
  isTTSEnabled() {
    return this.isEnabled
  }

  /**
   * Testa o serviço de voz aprimorado
   */
  async testVoiceService() {
    try {
      // Testar health check primeiro
      const healthResponse = await fetch(`${this.voiceServiceURL}/health`, {
        method: 'GET',
        timeout: 10000
      })

      if (healthResponse.ok) {
        const health = await healthResponse.json()
        console.log('💚 Voice Service Health:', health)
        
        if (health.tts_model_loaded) {
          // Obter informações detalhadas
          await this.initialize()
          
          return { 
            available: true, 
            modelLoading: false, 
            health,
            service: 'direct',
            version: health.version || '2.0.0'
          }
        } else {
          console.warn('⚠️ Voice service online, mas modelo TTS ainda carregando...')
          
          // Retry em alguns segundos
          setTimeout(() => {
            this.testVoiceService()
          }, 5000)
          
          return { 
            available: true, 
            modelLoading: true, 
            health,
            service: 'direct'
          }
        }
      } else {
        throw new Error(`Health check falhou: HTTP ${healthResponse.status}`)
      }
    } catch (error) {
      console.warn('❌ Voice service direto não disponível:', error.message)
      
      // Fallback para gateway
      try {
        const response = await fetch(`${this.baseURL}/voice/config`, {
          method: 'GET',
          timeout: 10000
        })

        if (response.ok) {
          const config = await response.json()
          console.log('🔄 Usando gateway como fallback:', config)
          return { 
            available: true, 
            modelLoading: false, 
            config,
            service: 'gateway'
          }
        } else {
          throw new Error(`Gateway HTTP ${response.status}`)
        }
      } catch (gatewayError) {
        console.error('❌ Gateway também falhou:', gatewayError.message)
        
        // Retry após tempo se for erro de rede
        if (error.message.includes('fetch') || error.message.includes('timeout')) {
          setTimeout(() => {
            this.testVoiceService()
          }, 10000)
        }
        
        return { 
          available: false, 
          error: error.message,
          gatewayError: gatewayError.message 
        }
      }
    }
  }

  /**
   * Obtém configurações atuais do serviço
   */
  getServiceConfig() {
    return {
      enabled: this.isEnabled,
      currentModel: this.currentModel,
      availableModels: this.availableModels,
      defaultSpeed: this.defaultSpeed,
      defaultLanguage: this.defaultLanguage,
      voiceServiceURL: this.voiceServiceURL,
      serviceInfo: this.serviceInfo
    }
  }

  /**
   * Limpa arquivos antigos (útil para manutenção)
   */
  async cleanupOldFiles(maxAgeHours = 24) {
    try {
      const response = await fetch(`${this.voiceServiceURL}/api/voice/cleanup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ max_age_hours: maxAgeHours }),
        timeout: 10000
      })

      if (response.ok) {
        const result = await response.json()
        console.log('🧹 Limpeza concluída:', result)
        return result
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.warn('⚠️ Erro na limpeza de arquivos:', error.message)
      return { success: false, error: error.message }
    }
  }
}

// Singleton com inicialização automática
const audioService = new AudioService()

// Inicializar quando possível
audioService.testVoiceService().then(() => {
  console.log('🎉 AudioService Enhanced pronto para uso!')
})

export default audioService 