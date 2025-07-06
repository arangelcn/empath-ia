# Conversação por Voz - Empath.IA

## Visão Geral
Implementar um modo de comunicação exclusivamente por voz na aplicação web, permitindo alternar entre chat textual e conversação por voz.

## Funcionalidades Principais

### 1. Interface de Usuário
- **Toggle de Modo**: Botão para alternar entre "Chat" e "Voz"
- **Indicador Visual**: Mostrar qual modo está ativo
- **Controles de Voz**:
  - Botão de gravação (microfone)
  - Indicador de gravação ativa (animação/cores)
  - Botão de parar gravação
  - Indicador de processamento
- **Feedback Visual**:
  - Status da gravação
  - Nível de áudio em tempo real
  - Indicador de reconhecimento de fala

### 2. Captura de Áudio
- **Web Audio API**: Para captura do microfone
- **MediaRecorder API**: Para gravação de áudio
- **Formatos Suportados**:
  - WAV (preferencial para processamento)
  - MP3 (alternativa)
  - WebM (navegador)
- **Configurações de Áudio**:
  - Sample rate: 16kHz ou 44.1kHz
  - Bit depth: 16-bit
  - Channels: Mono
  - Qualidade: Otimizada para reconhecimento de fala

### 3. Reconhecimento de Fala (Speech-to-Text)
- **Opções de Implementação**:
  - **Web Speech API** (nativo do navegador)
    - Vantagens: Gratuito, sem dependências externas
    - Desvantagens: Limitado a alguns navegadores, sem controle de idioma
  - **Google Cloud Speech-to-Text**
    - Vantagens: Alta precisão, múltiplos idiomas
    - Desvantagens: Requer API key, custo
  - **Azure Speech Services**
    - Vantagens: Boa precisão, integração com outros serviços Azure
    - Desvantagens: Requer conta Azure, custo
  - **OpenAI Whisper**
    - Vantagens: Open source, boa precisão
    - Desvantagens: Requer processamento local ou servidor

### 4. Processamento de Áudio
- **Pré-processamento**:
  - Normalização de volume
  - Redução de ruído
  - Detecção de silêncio
  - Compressão de áudio
- **Validações**:
  - Duração mínima/máxima
  - Qualidade do áudio
  - Detecção de fala vs. ruído

### 5. Integração com Backend

#### 5.1 Gateway Service
- **Novo Endpoint**: `/api/voice/process`
- **Funcionalidades**:
  - Receber áudio do frontend
  - Coordenar processamento entre serviços
  - Retornar resposta de áudio

#### 5.2 Voice Service (Expandir)
- **Novas Funcionalidades**:
  - **Speech-to-Text**: Integração com serviço de reconhecimento
  - **Text-to-Speech**: Já implementado
  - **Processamento de Áudio**: Validação e otimização
- **APIs Adicionais**:
  - `/api/speech-to-text`: Converter áudio para texto
  - `/api/audio/validate`: Validar qualidade do áudio
  - `/api/audio/process`: Processar áudio recebido

#### 5.3 AI Service
- **Manter Funcionalidade**: Processar texto e gerar resposta
- **Otimizações**:
  - Respostas mais concisas para voz
  - Contexto de conversação por voz
  - Detecção de comandos de voz

### 6. Fluxo de Comunicação

#### 6.1 Modo Voz Ativo
1. **Usuário ativa gravação**
2. **Frontend captura áudio** via Web Audio API
3. **Áudio é enviado** para `/api/voice/process`
4. **Gateway coordena**:
   - Envia áudio para Voice Service (Speech-to-Text)
   - Recebe texto e envia para AI Service
   - Recebe resposta e envia para Voice Service (Text-to-Speech)
5. **Frontend reproduz** áudio de resposta
6. **Ciclo se repete**

#### 6.2 Modo Chat (Existente)
- Manter funcionalidade atual
- Adicionar toggle para alternar

### 7. Componentes Frontend

#### 7.1 VoiceRecorder Component
```javascript
// Funcionalidades:
- Iniciar/parar gravação
- Visualizar nível de áudio
- Mostrar status da gravação
- Validar qualidade do áudio
```

#### 7.2 VoicePlayer Component
```javascript
// Funcionalidades:
- Reproduzir áudio de resposta
- Controles de playback
- Indicador de progresso
- Controle de volume
```

#### 7.3 VoiceToggle Component
```javascript
// Funcionalidades:
- Alternar entre chat e voz
- Indicador visual do modo ativo
- Configurações de voz
```

### 8. Configurações e Preferências

#### 8.1 Configurações de Voz
- **Idioma**: Português (padrão)
- **Velocidade de Fala**: Ajustável
- **Tom de Voz**: Masculino/Feminino
- **Qualidade de Áudio**: Alta/Média/Baixa
- **Sensibilidade do Microfone**: Ajustável

#### 8.2 Configurações de Interface
- **Modo Ativo**: Chat/Voz/Auto
- **Auto-switch**: Alternar automaticamente baseado em entrada
- **Feedback Visual**: Nível de detalhe
- **Notificações**: Sons de feedback

### 9. Tratamento de Erros

#### 9.1 Erros de Captura
- Microfone não disponível
- Permissões negadas
- Qualidade de áudio insuficiente
- Duração muito curta/longa

#### 9.2 Erros de Processamento
- Falha no reconhecimento de fala
- Erro na geração de resposta
- Falha na síntese de voz
- Timeout de processamento

#### 9.3 Erros de Rede
- Conexão perdida
- Serviços indisponíveis
- Latência alta

### 10. Considerações de Performance

#### 10.1 Otimizações de Áudio
- **Compressão**: Reduzir tamanho dos arquivos
- **Streaming**: Processar em chunks
- **Cache**: Cachear respostas comuns
- **Compressão de Rede**: Gzip para transferência

#### 10.2 Otimizações de Interface
- **Feedback Imediato**: Indicadores visuais instantâneos
- **Lazy Loading**: Carregar componentes sob demanda
- **Debounce**: Evitar múltiplas requisições
- **Queue**: Gerenciar múltiplas gravações

### 11. Segurança e Privacidade

#### 11.1 Proteção de Dados
- **Criptografia**: HTTPS para todas as comunicações
- **Temporização**: Deletar áudios após processamento
- **Anonimização**: Não armazenar dados pessoais
- **Consentimento**: Permissão explícita para uso do microfone

#### 11.2 Validações
- **Tamanho de Arquivo**: Limitar uploads
- **Formato**: Validar tipos de áudio
- **Conteúdo**: Detectar áudio válido
- **Rate Limiting**: Limitar requisições por usuário

### 12. Acessibilidade

#### 12.1 Suporte a Pessoas com Deficiência
- **Navegação por Teclado**: Controles acessíveis
- **Screen Readers**: Compatibilidade com leitores de tela
- **Controles de Voz**: Comandos de voz para navegação
- **Alternativas Visuais**: Para usuários com deficiência auditiva

#### 12.2 Configurações de Acessibilidade
- **Tamanho de Fonte**: Ajustável
- **Contraste**: Alto contraste disponível
- **Animações**: Opção de desabilitar
- **Feedback Tátil**: Vibração para feedback

### 13. Testes Necessários

#### 13.1 Testes Unitários
- Componentes de gravação
- Processamento de áudio
- Integração com APIs
- Validações de entrada

#### 13.2 Testes de Integração
- Fluxo completo de voz
- Comunicação entre serviços
- Tratamento de erros
- Performance sob carga

#### 13.3 Testes de Usabilidade
- Interface intuitiva
- Feedback claro
- Transições suaves
- Experiência consistente

### 14. Monitoramento e Analytics

#### 14.1 Métricas de Performance
- Tempo de resposta
- Taxa de sucesso
- Qualidade do reconhecimento
- Uso de recursos

#### 14.2 Métricas de Uso
- Frequência de uso do modo voz
- Duração das sessões
- Preferências de configuração
- Padrões de uso

### 15. Roadmap de Implementação

#### Fase 1: Base (1-2 semanas)
- [ ] Componente de gravação básico
- [ ] Integração com Web Audio API
- [ ] Endpoint básico no Gateway
- [ ] Toggle entre chat e voz

#### Fase 2: Reconhecimento (2-3 semanas)
- [ ] Integração com Speech-to-Text
- [ ] Processamento de áudio
- [ ] Validações básicas
- [ ] Tratamento de erros

#### Fase 3: Otimização (1-2 semanas)
- [ ] Melhorias de performance
- [ ] Configurações avançadas
- [ ] Testes completos
- [ ] Documentação

#### Fase 4: Polimento (1 semana)
- [ ] Acessibilidade
- [ ] Analytics
- [ ] Monitoramento
- [ ] Deploy em produção

### 16. Dependências Externas

#### 16.1 APIs Necessárias
- **Google Cloud Speech-to-Text** (recomendado)
- **Google Cloud Text-to-Speech** (já implementado)
- **Web Audio API** (nativo do navegador)

#### 16.2 Bibliotecas JavaScript
- **MediaRecorder API** (nativo)
- **Web Audio API** (nativo)
- **Possivelmente**: Biblioteca para processamento de áudio

#### 16.3 Bibliotecas Python
- **SpeechRecognition** (para fallback local)
- **PyAudio** (para processamento local)
- **Librosa** (já implementado)

### 17. Considerações de Infraestrutura

#### 17.1 Recursos de Servidor
- **Processamento de Áudio**: CPU intensivo
- **Armazenamento Temporário**: Para áudios em processamento
- **Bandwidth**: Transferência de áudio
- **Latência**: Otimizar para tempo real

#### 17.2 Escalabilidade
- **Load Balancing**: Distribuir carga
- **Caching**: Cache de respostas
- **Queue System**: Para processamento assíncrono
- **Monitoring**: Alertas de performance

### 18. Custos Estimados

#### 18.1 APIs Externas
- **Google Speech-to-Text**: ~$0.006 por minuto
- **Google Text-to-Speech**: ~$0.004 por 1K caracteres
- **Estimativa**: ~$0.01 por conversação de 1 minuto

#### 18.2 Infraestrutura
- **Processamento**: CPU adicional
- **Storage**: Áudio temporário
- **Bandwidth**: Transferência de dados
- **Monitoring**: Ferramentas de observabilidade

### 19. Alternativas e Fallbacks

#### 19.1 Fallback para Chat
- Se reconhecimento falhar → Sugerir digitação
- Se síntese falhar → Mostrar texto
- Se rede falhar → Modo offline básico

#### 19.2 Alternativas de STT
- **Web Speech API**: Para navegadores compatíveis
- **Azure Speech**: Como alternativa ao Google
- **Whisper Local**: Para processamento offline

### 20. Documentação Necessária

#### 20.1 Para Desenvolvedores
- Guia de implementação
- Documentação de APIs
- Exemplos de código
- Troubleshooting

#### 20.2 Para Usuários
- Guia de uso
- Configurações recomendadas
- Solução de problemas
- FAQ

---

## Próximos Passos

1. **Definir Stack Tecnológica**: Escolher entre Web Speech API vs Google Cloud
2. **Criar Protótipo**: Implementar gravação básica
3. **Testar APIs**: Validar qualidade do reconhecimento
4. **Planejar Arquitetura**: Detalhar integração com serviços existentes
5. **Estimar Timeline**: Definir cronograma realista
6. **Alocar Recursos**: Definir equipe e infraestrutura necessária 