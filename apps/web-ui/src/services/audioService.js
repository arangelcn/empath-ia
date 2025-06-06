/**
 * Serviço de áudio para Text-to-Speech
 */

class AudioService {
  constructor() {
    this.isEnabled = true
    this.currentAudio = null
    this.baseURL = '/api'
  }

  /**
   * Sintetiza e reproduz texto em áudio
   * @param {string} text - Texto para converter em áudio
   * @param {Object} options - Opções de configuração
   */
  async speakText(text, options = {}) {
    try {
      // Parar áudio atual se estiver tocando
      this.stopCurrentAudio()

      if (!this.isEnabled) {
        console.log('TTS desabilitado')
        return { success: false, message: 'TTS desabilitado' }
      }

      const requestData = {
        text: text.substring(0, 500), // Limitar tamanho para performance
        voice_speed: options.speed || 1.0,
        language: options.language || 'pt'
      }

      console.log('Solicitando TTS para:', text.substring(0, 50) + '...')

      // Fazer request para o gateway
      const response = await fetch(`${this.baseURL}/voice/speak`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
        timeout: 30000
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      if (data.success && data.audio_url) {
        console.log('TTS gerado com sucesso:', data.filename)
        await this.playAudioFromUrl(data.audio_url)
        return { success: true, data }
      } else {
        throw new Error(data.message || 'Falha na geração de áudio')
      }

    } catch (error) {
      console.error('Erro no TTS:', error)
      return { 
        success: false, 
        message: `Erro TTS: ${error.message}`,
        error 
      }
    }
  }

  /**
   * Reproduz áudio a partir de uma URL
   * @param {string} audioUrl - URL do arquivo de áudio
   */
  async playAudioFromUrl(audioUrl) {
    return new Promise((resolve, reject) => {
      try {
        // Converter URL do voice service para usar a porta 8004 se necessário
        let finalAudioUrl = audioUrl
        if (audioUrl.includes('localhost:8000/api/voice')) {
          finalAudioUrl = audioUrl.replace('localhost:8000/api/voice', 'localhost:8004')
        }
        
        this.currentAudio = new Audio(finalAudioUrl)
        
        this.currentAudio.onloadeddata = () => {
          console.log('Áudio carregado, iniciando reprodução')
        }

        this.currentAudio.onplay = () => {
          console.log('Reprodução de áudio iniciada')
        }

        this.currentAudio.onended = () => {
          console.log('Reprodução de áudio finalizada')
          this.currentAudio = null
          resolve()
        }

        this.currentAudio.onerror = (error) => {
          console.error('Erro na reprodução:', error)
          this.currentAudio = null
          reject(error)
        }

        // Tentar reproduzir
        this.currentAudio.play().catch(error => {
          console.error('Erro ao iniciar reprodução:', error)
          reject(error)
        })

      } catch (error) {
        console.error('Erro ao criar áudio:', error)
        reject(error)
      }
    })
  }

  /**
   * Para o áudio atual
   */
  stopCurrentAudio() {
    if (this.currentAudio) {
      this.currentAudio.pause()
      this.currentAudio.currentTime = 0
      this.currentAudio = null
      console.log('Áudio interrompido')
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
    console.log(`TTS ${this.isEnabled ? 'ativado' : 'desativado'}`)
    return this.isEnabled
  }

  /**
   * Verifica se TTS está habilitado
   */
  isTTSEnabled() {
    return this.isEnabled
  }

  /**
   * Testa o serviço de voz
   */
  async testVoiceService() {
    try {
      const response = await fetch(`${this.baseURL}/voice/config`, {
        method: 'GET',
        timeout: 10000
      })

      if (response.ok) {
        const config = await response.json()
        console.log('Voice service disponível:', config)
        
        // Verificar se o modelo está carregado
        if (config.model_loaded === false) {
          console.warn('Voice service online, mas modelo TTS ainda carregando...')
          
          // Tentar novamente após alguns segundos
          setTimeout(() => {
            this.testVoiceService()
          }, 5000)
          
          return { available: true, modelLoading: true, config }
        }
        
        return { available: true, modelLoading: false, config }
      } else {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.warn('Voice service não disponível:', error.message)
      
      // Retry após 10 segundos se for erro de rede
      if (error.message.includes('fetch') || error.message.includes('timeout')) {
        setTimeout(() => {
          this.testVoiceService()
        }, 10000)
      }
      
      return { available: false, error: error.message }
    }
  }
}

// Singleton
const audioService = new AudioService()

export default audioService 