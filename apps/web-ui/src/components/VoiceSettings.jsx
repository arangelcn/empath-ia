import React, { useState, useEffect } from 'react'
import audioService from '../services/audioService.js'

/**
 * Componente para configurações avançadas de voz
 */
const VoiceSettings = ({ onClose, className = '' }) => {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [models, setModels] = useState({})
  const [modelDescriptions, setModelDescriptions] = useState({})
  const [changingModel, setChangingModel] = useState(false)
  const [voiceSpeed, setVoiceSpeed] = useState(1.0)
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    loadConfiguration()
  }, [])

  const loadConfiguration = async () => {
    setLoading(true)
    try {
      // Obter configuração atual
      const currentConfig = audioService.getServiceConfig()
      setConfig(currentConfig)
      setVoiceSpeed(currentConfig.defaultSpeed || 1.0)

      // Obter modelos disponíveis
      const modelsData = await audioService.getAvailableModels()
      if (modelsData) {
        setModels(modelsData.available_models || {})
        setModelDescriptions(modelsData.descriptions || {})
      }

      // Obter status atualizado
      await audioService.getModelStatus()
      const updatedConfig = audioService.getServiceConfig()
      setConfig(updatedConfig)

    } catch (error) {
      console.error('Erro ao carregar configurações:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleModelChange = async (modelKey) => {
    if (changingModel || modelKey === config.currentModel) {
      return
    }

    setChangingModel(true)
    try {
      console.log(`🔄 Alterando modelo para: ${modelKey}`)
      
      const result = await audioService.changeModel(modelKey)
      
      if (result.success) {
        // Atualizar configuração local
        setConfig(prev => ({
          ...prev,
          currentModel: modelKey
        }))
        
        // Testar o novo modelo
        await testNewModel(modelKey)
        
        console.log(`✅ Modelo alterado com sucesso para: ${modelKey}`)
      } else {
        console.error('❌ Falha ao alterar modelo:', result.error)
        alert(`Erro ao alterar modelo: ${result.error}`)
      }
    } catch (error) {
      console.error('❌ Erro inesperado:', error)
      alert(`Erro inesperado: ${error.message}`)
    } finally {
      setChangingModel(false)
    }
  }

  const testNewModel = async (modelKey) => {
    try {
      const testTexts = {
        'vits_pt': 'Testando modelo VITS para português brasileiro.',
        'xtts_v2': 'Testando modelo XTTS-v2 com alta qualidade para português.',
        'your_tts': 'Testando modelo YourTTS multilíngue.'
      }

      const testText = testTexts[modelKey] || 'Testando novo modelo de voz.'
      
      await audioService.speakText(testText, { 
        speed: voiceSpeed,
        language: 'pt'
      })
    } catch (error) {
      console.warn('Erro no teste do modelo:', error)
    }
  }

  const handleSpeedChange = (newSpeed) => {
    setVoiceSpeed(newSpeed)
    // Atualizar configuração no serviço
    audioService.defaultSpeed = newSpeed
  }

  const testCurrentVoice = async () => {
    const testText = `Olá! Esta é uma demonstração do modelo ${config.currentModel} com velocidade ${voiceSpeed}. A qualidade de síntese de voz foi aprimorada significativamente.`
    
    try {
      await audioService.speakText(testText, { 
        speed: voiceSpeed,
        language: 'pt'
      })
    } catch (error) {
      console.error('Erro no teste de voz:', error)
      alert('Erro ao testar voz. Verifique se o serviço está funcionando.')
    }
  }

  const toggleSettings = () => {
    setIsOpen(!isOpen)
  }

  const ModelCard = ({ modelKey, modelName, description, isSelected, isAvailable }) => (
    <div 
      className={`
        p-4 border-2 rounded-lg cursor-pointer transition-all duration-200
        ${isSelected 
          ? 'border-blue-500 bg-blue-50 shadow-md' 
          : isAvailable 
            ? 'border-gray-300 bg-white hover:border-blue-300 hover:shadow-sm' 
            : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-50'
        }
      `}
      onClick={() => isAvailable && !changingModel && handleModelChange(modelKey)}
    >
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-semibold text-gray-800">{modelName}</h4>
        {isSelected && (
          <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded-full">
            ATIVO
          </span>
        )}
        {changingModel && isSelected && (
          <span className="text-xs bg-orange-500 text-white px-2 py-1 rounded-full animate-pulse">
            ALTERANDO...
          </span>
        )}
      </div>
      <p className="text-sm text-gray-600 mb-2">{description}</p>
      <div className="flex items-center justify-between text-xs">
        <span className={`
          px-2 py-1 rounded-full
          ${isAvailable 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
          }
        `}>
          {isAvailable ? '✅ Disponível' : '❌ Indisponível'}
        </span>
        <span className="text-gray-500">
          Qualidade: {modelKey.includes('xtts') ? 'Alta' : 'Padrão'}
        </span>
      </div>
    </div>
  )

  if (loading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-lg">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`voice-settings ${className}`}>
      {/* Botão Toggle */}
      <button 
        onClick={toggleSettings}
        className="mb-4 flex min-h-[42px] items-center gap-2 rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors duration-150 hover:bg-primary-700"
      >
        <span>🎤</span>
        Configurações de Voz
        <span className={`transform transition-transform ${isOpen ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>

      {/* Painel de Configurações */}
      {isOpen && (
        <div className="bg-white rounded-lg shadow-lg border p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-gray-800">
              🎙️ Configurações de Voz Avançadas
            </h3>
            {config && (
              <div className="text-sm text-gray-500">
                Serviço: {config.serviceInfo?.service_name || 'Voice Service'} v{config.serviceInfo?.version || '2.0.0'}
              </div>
            )}
          </div>

          {/* Status do Serviço */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold mb-2 text-gray-700">📊 Status do Serviço</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">TTS Habilitado:</span>
                <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                  config?.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {config?.enabled ? '✅ Sim' : '❌ Não'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Modelo Atual:</span>
                <span className="ml-2 font-mono text-blue-600">
                  {config?.currentModel || 'Carregando...'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Velocidade:</span>
                <span className="ml-2 font-mono text-purple-600">
                  {voiceSpeed}x
                </span>
              </div>
              <div>
                <span className="text-gray-600">Idioma:</span>
                <span className="ml-2">🇧🇷 Português</span>
              </div>
            </div>
          </div>

          {/* Controle de Velocidade */}
          <div className="space-y-3">
            <h4 className="font-semibold text-gray-700">🎚️ Velocidade da Fala</h4>
            <div className="flex items-center space-x-4">
              <label className="text-sm text-gray-600 min-w-0">Lenta</label>
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={voiceSpeed}
                onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <label className="text-sm text-gray-600 min-w-0">Rápida</label>
              <span className="min-w-0 text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                {voiceSpeed}x
              </span>
            </div>
          </div>

          {/* Seleção do Modelo */}
          <div className="space-y-4">
            <h4 className="font-semibold text-gray-700">🤖 Modelos de Voz Disponíveis</h4>
            <div className="grid gap-4">
              {Object.entries(models).length > 0 ? (
                Object.entries(models).map(([modelKey, modelName]) => (
                  <ModelCard
                    key={modelKey}
                    modelKey={modelKey}
                    modelName={modelName}
                    description={modelDescriptions[modelKey] || 'Modelo de síntese de voz'}
                    isSelected={config?.currentModel === modelKey}
                    isAvailable={true}
                  />
                ))
              ) : (
                <div className="text-center p-8 text-gray-500">
                  <div className="text-4xl mb-2">🤖</div>
                  <p>Carregando modelos disponíveis...</p>
                </div>
              )}
            </div>
          </div>

          {/* Ações */}
          <div className="flex gap-3 pt-4 border-t">
            <button
              onClick={testCurrentVoice}
              disabled={changingModel}
              className="min-h-[42px] flex-1 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors duration-150 hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              🎤 Testar Voz Atual
            </button>
            <button
              onClick={loadConfiguration}
              disabled={changingModel}
              className="min-h-[42px] rounded-lg bg-gray-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors duration-150 hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              🔄 Atualizar
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="min-h-[42px] rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-colors duration-150 hover:bg-red-700"
              >
                ✖️ Fechar
              </button>
            )}
          </div>

          {/* Info Adicional */}
          <div className="text-xs text-gray-500 bg-blue-50 p-3 rounded-lg">
            <strong>💡 Dicas:</strong>
            <ul className="mt-1 space-y-1">
              <li>• O modelo XTTS-v2 oferece a melhor qualidade para português brasileiro</li>
              <li>• Velocidades entre 0.8-1.2x são ideais para compreensão</li>
              <li>• A troca de modelo pode levar alguns segundos para carregar</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

export default VoiceSettings 
