# Painel Administrativo - Empath IA

Este é o painel administrativo do sistema Empath IA, uma ferramenta desenvolvida para psicólogos e administradores configurarem e monitorarem o sistema de análise emocional em tempo real.

## 🎯 Funcionalidades

- **Dashboard Principal**: Visão geral com métricas e estatísticas do sistema
- **Gerenciamento de Usuários**: Visualizar e gerenciar usuários, perfis e progressos
- **Gerenciamento de Sessões**: Criar e editar templates de sessões terapêuticas
- **Análise de Conversas**: Visualizar histórico e analisar interações dos usuários
- **Gerenciamento de Prompts** ⭐ **NOVO**: Interface completa para editar prompts do sistema de IA
- **Analytics Avançado**: Métricas, relatórios e análise de tendências
- **Status do Sistema**: Monitoramento de serviços e health checks em tempo real
- **Configurações**: Parâmetros gerais do sistema e preferências administrativas
- **Autenticação**: Sistema de login seguro para acesso restrito

## 🚀 Como Executar

### Pré-requisitos
- Node.js 16+
- npm ou yarn

### Instalação

1. Navegue até o diretório do admin panel:
```bash
cd apps/admin-panel
```

2. Instale as dependências:
```bash
npm install
```

3. Inicie o servidor de desenvolvimento:
```bash
npm start
```

4. Abra o navegador em `http://localhost:3001`

### Credenciais de Acesso (Demo)
- **Email**: admin@empath-ia.com
- **Senha**: admin123

## 📱 Interface

### Páginas Principais

1. **Login** (`/login`)
   - Autenticação de administradores
   - Validação de credenciais

2. **Dashboard** (`/`)
   - Resumo de métricas gerais
   - Gráficos de uso e performance
   - Estatísticas de emoções detectadas

3. **Usuários** (`/users`)
   - Gerenciar usuários do sistema
   - Visualizar perfis e estatísticas
   - Acompanhar progresso terapêutico

4. **Sessões** (`/sessions`)
   - Gerenciar sessões terapêuticas
   - Criar e editar templates de sessão
   - Acompanhar sessões dos usuários

5. **Conversas** (`/conversations`)
   - Visualizar histórico de conversas
   - Analisar interações dos usuários
   - Exportar dados de sessões

6. **Prompts** (`/prompts`) ⭐ **NOVO**
   - Gerenciar prompts do sistema de IA
   - Criar, editar e organizar prompts por tipo
   - Ativar/desativar prompts dinamicamente
   - Estatísticas de uso e distribuição
   - Sistema de variáveis e tags

7. **Analytics** (`/analytics`)
   - Métricas avançadas do sistema
   - Relatórios de performance
   - Análise de tendências

8. **Status do Sistema** (`/system-status`)
   - Monitoramento de serviços
   - Health checks em tempo real
   - Métricas de performance

9. **Configurações** (`/settings`)
   - Configurações gerais do sistema
   - Parâmetros de funcionamento
   - Preferências administrativas

## 🎨 Design System

### Cores Principais
- **Primary**: Azul (#3B82F6)
- **Success**: Verde (#10B981)
- **Warning**: Amarelo (#F59E0B)
- **Danger**: Vermelho (#EF4444)

### Componentes
- Layout responsivo com Tailwind CSS
- Componentes reutilizáveis
- Gráficos interativos com Recharts
- Ícones do Heroicons

## 🔧 Tecnologias

- **React** 18.2.0 - Framework principal
- **Tailwind CSS** 3.4.0 - Estilização
- **Recharts** 2.8.0 - Gráficos e visualizações
- **Heroicons** 2.0.18 - Ícones
- **Axios** 1.6.0 - Requisições HTTP
- **Date-fns** 2.30.0 - Manipulação de datas

## 📊 Estrutura de Dados

### Métricas do Sistema
```javascript
{
  totalUsers: number,
  activeUsers: number,
  totalSessions: number,
  avgSessionDuration: number,
  emotionDistribution: {
    joy: number,
    sadness: number,
    anger: number,
    anxiety: number,
    neutral: number,
    surprise: number
  }
}
```

### Configurações de Emoção
```javascript
{
  sensitivity: {
    joy: number,      // 0-100
    sadness: number,  // 0-100
    anger: number,    // 0-100
    anxiety: number,  // 0-100
    neutral: number,  // 0-100
    surprise: number  // 0-100
  },
  thresholds: {
    detection: number,    // 0-100
    confidence: number    // 0-100
  }
}
```

### Configurações de Áudio
```javascript
{
  tts: {
    speed: number,     // 0.5-2.0
    pitch: number,     // 0.5-2.0
    volume: number,    // 0-100
    voice: string      // voice ID
  },
  microphone: {
    sensitivity: number,  // 0-100
    noiseReduction: boolean,
    echoCancellation: boolean
  }
}
```

## 🔐 Segurança

- Autenticação baseada em tokens
- Validação de entrada de dados
- Sanitização de parâmetros
- Controle de acesso por função

## 🚀 Deploy

### Build para Produção
```bash
npm run build
```

### Variáveis de Ambiente
```env
REACT_APP_API_URL=http://localhost:8001
REACT_APP_EMOTION_SERVICE_URL=http://localhost:8003
REACT_APP_VOICE_SERVICE_URL=http://localhost:8004
REACT_APP_AI_SERVICE_URL=http://localhost:8005
```

## 📝 Próximas Funcionalidades

- [ ] Relatórios exportáveis (PDF/Excel)
- [ ] Notificações em tempo real
- [ ] Configurações avançadas de IA
- [ ] Histórico de configurações
- [ ] Backup/Restore de dados
- [ ] Multi-idioma
- [ ] Dark mode
- [ ] Logs de auditoria

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua funcionalidade
3. Commit suas alterações
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📞 Suporte

Para suporte técnico ou dúvidas:
- Email: support@empath-ia.com
- Documentação: `/docs`
- Issues: GitHub Issues 