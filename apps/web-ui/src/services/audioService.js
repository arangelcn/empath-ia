/**
 * Serviço de áudio para Text-to-Speech - Integração com Voice Service F5-TTS v3.0.0
 */

class AudioService {
  constructor() {
    this.isEnabled = true
    this.currentAudio = null
    this.baseURL = '/api'
    
    // Forçar uso do gateway para garantir compatibilidade
    // O gateway já está configurado para rotear corretamente
    this.voiceServiceURL = '/api' // Sempre usar gateway
      
    this.currentModel = 'F5-TTS-pt-br' // Modelo F5-TTS
    this.availableModels = {}
    this.serviceInfo = null
    
    // Configurações de qualidade
    this.defaultSpeed = 1.0
    this.defaultLanguage = 'pt'
    
    console.log('🎤 AudioService F5-TTS v3.0.0 inicializado')
    console.log('🔗 Voice Service URL:', this.voiceServiceURL)
    console.log('🐳 Usando gateway para máxima compatibilidade')
  }

  /**
   * Inicializa o serviço e carrega informações dos modelos
   */
  async initialize() {
    try {
      const serviceInfo = await this.getServiceInfo()
      if (serviceInfo) {
        this.serviceInfo = serviceInfo
        this.currentModel = serviceInfo.model_name || 'F5-TTS-pt-br'
        console.log('🎯 Voice Service F5-TTS conectado:', {
          modelo: this.currentModel,
          status: serviceInfo.status,
          device: serviceInfo.device
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
      const response = await fetch(`${this.voiceServiceURL}/health`, {
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
        const response = await fetch(`${this.baseURL}/voice/health`, {
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
   * Verifica status do modelo F5-TTS
   */
  async getModelStatus() {
    try {
      const response = await fetch(`${this.voiceServiceURL}/api/v1/model-info`, {
        method: 'GET',
        timeout: 10000
      })

      if (response.ok) {
        const status = await response.json()
        this.currentModel = status.model_name
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
   * Lista modelos disponíveis (F5-TTS)
   */
  async getAvailableModels() {
    try {
      const response = await fetch(`${this.voiceServiceURL}/api/v1/model-info`, {
        method: 'GET',
        timeout: 10000
      })

      if (response.ok) {
        const data = await response.json()
        this.availableModels = { [data.model_name]: data }
        return { available_models: this.availableModels, descriptions: { [data.model_name]: 'F5-TTS Português Brasileiro' } }
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.warn('Erro ao obter modelos disponíveis:', error.message)
      return { available_models: {}, descriptions: {} }
    }
  }

  /**
   * Troca o modelo TTS (F5-TTS é fixo)
   */
  async changeModel(modelKey) {
    try {
      // F5-TTS é um modelo fixo, mas mantemos compatibilidade
      if (modelKey === 'F5-TTS-pt-br' || modelKey === 'firstpixel/F5-TTS-pt-br') {
        this.currentModel = 'F5-TTS-pt-br'
        console.log(`✅ Modelo confirmado: ${this.currentModel}`)
        return { success: true, data: { model_name: this.currentModel } }
      } else {
        console.warn(`⚠️ Modelo ${modelKey} não suportado, mantendo F5-TTS-pt-br`)
        return { success: false, error: 'Apenas F5-TTS-pt-br é suportado' }
      }
    } catch (error) {
      console.error('❌ Erro ao trocar modelo:', error.message)
      return { success: false, error: error.message }
    }
  }

  /**
   * Sintetiza e reproduz texto em áudio com F5-TTS
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

      // Obter a voz selecionada pelo usuário
      const selectedVoice = localStorage.getItem('empatia_selected_voice') || 'pt-BR-Neural2-A'

      const requestData = {
        text: text.substring(0, 1000), // Limite de caracteres
        voice_name: selectedVoice, // Usar a voz selecionada pelo usuário
        voice_speed: options.speed || this.defaultSpeed
      }

      console.log('🎤 Solicitando síntese de voz para:', `"${text.substring(0, 50)}..."`)
      console.log('📊 Configurações:', {
        voz: selectedVoice,
        velocidade: requestData.voice_speed,
        caracteres: text.length
      })

      // Tentar voice service direto primeiro (melhor performance)
      let response
      let data

      try {
        response = await fetch(`${this.voiceServiceURL}/api/v1/synthesize`, {
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
        response = await fetch(`${this.baseURL}/voice/synthesize`, {
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
        console.log('✅ F5-TTS gerado com sucesso:', {
          arquivo: data.filename,
          duração: `${data.duration?.toFixed(2)}s`,
          modelo: this.currentModel,
          url: data.audio_url,
          caracteres: data.text_length
        })
        
        await this.playAudioFromUrl(data.audio_url)
        return { success: true, data }
      } else {
        throw new Error(data.message || 'Falha na geração de áudio')
      }

    } catch (error) {
      console.error('❌ Erro no F5-TTS:', error)
      return { 
        success: false, 
        message: `Erro F5-TTS: ${error.message}`,
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
        
        console.log('🎵 Tentando reproduzir áudio:', {
          original: audioUrl,
          processada: finalAudioUrl,
          voiceServiceURL: this.voiceServiceURL
        })
        
        this.currentAudio = new Audio(finalAudioUrl)
        
        // Configurar eventos
        this.currentAudio.onloadstart = () => {
          console.log('📥 Carregando áudio...', finalAudioUrl)
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
          console.error('❌ Erro na reprodução:', {
            error,
            url: finalAudioUrl,
            networkState: this.currentAudio.networkState,
            readyState: this.currentAudio.readyState,
            errorCode: this.currentAudio.error?.code,
            errorMessage: this.currentAudio.error?.message
          })
          this.currentAudio = null
          reject(error)
        }

        this.currentAudio.onpause = () => {
          console.log('⏸️ Reprodução pausada')
        }

        this.currentAudio.oncanplay = () => {
          console.log('✅ Áudio pronto para reprodução')
        }

        this.currentAudio.oncanplaythrough = () => {
          console.log('✅ Áudio totalmente carregado')
        }

        this.currentAudio.onstalled = () => {
          console.warn('⚠️ Carregamento do áudio travou')
        }

        this.currentAudio.onsuspend = () => {
          console.warn('⚠️ Carregamento do áudio suspenso')
        }

        // Configurar volume e qualidade
        this.currentAudio.volume = 0.8
        this.currentAudio.preload = 'auto'

        // Tentar reproduzir
        console.log('🚀 Iniciando reprodução...')
        this.currentAudio.play().catch(error => {
          console.error('❌ Erro ao iniciar reprodução:', {
            error: error.message,
            name: error.name,
            url: finalAudioUrl
          })
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
    console.log('🔗 Processando URL do áudio:', audioUrl)
    
    // Sempre converter URLs do F5-TTS para o gateway
    if (audioUrl.startsWith('/api/v1/audio/')) {
      const newUrl = audioUrl.replace('/api/v1/audio/', '/api/voice/audio/')
      console.log('🔄 F5-TTS para gateway:', newUrl)
      return newUrl
    }
    
    // Se já for do gateway, manter
    if (audioUrl.startsWith('/api/voice/audio/')) {
      console.log('✅ URL do gateway detectada')
      return audioUrl
    }
    
    // Se for URL completa, extrair apenas o filename e usar gateway
    if (audioUrl.includes('/audio/')) {
      const filename = audioUrl.split('/audio/').pop()
      const newUrl = `/api/voice/audio/${filename}`
      console.log('🔄 URL completa convertida para gateway:', newUrl)
      return newUrl
    }
    
    console.log('⚠️ URL não processada, retornando original:', audioUrl)
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
  console.log('🎉 AudioService F5-TTS pronto para uso!')
})

export default audioService 