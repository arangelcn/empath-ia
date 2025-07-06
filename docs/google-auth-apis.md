# APIs de Autenticação Google

## Visão Geral

O Google oferece várias APIs para autenticação, cada uma com diferentes características e casos de uso.

## 1. Google Identity Services (GIS) - RECOMENDADA ✅

### Características
- **Lançamento**: 2021
- **Status**: Atual e oficialmente recomendada
- **Segurança**: JWT tokens criptografados
- **UX**: Botões nativos e One Tap
- **Compatibilidade**: Todos os navegadores modernos

### Vantagens
- ✅ Mais segura com JWT tokens
- ✅ Melhor experiência do usuário
- ✅ Suporte a One Tap
- ✅ Botões nativos do Google
- ✅ Menos código para implementar
- ✅ Atualizações automáticas

### Implementação Atual
```javascript
// Carregar script
<script src="https://accounts.google.com/gsi/client"></script>

// Inicializar
google.accounts.id.initialize({
  client_id: 'YOUR_CLIENT_ID',
  callback: handleCredentialResponse
});

// Renderizar botão
google.accounts.id.renderButton(element, {
  theme: 'filled_blue',
  size: 'large',
  shape: 'pill'
});
```

## 2. Google Sign-In JavaScript API (Legacy) - DEPRECADA ❌

### Características
- **Lançamento**: 2014
- **Status**: Deprecada desde 2020
- **Segurança**: Menos segura
- **UX**: Limitada

### Desvantagens
- ❌ Não recebe mais atualizações
- ❌ Menos segura
- ❌ UX limitada
- ❌ Pode parar de funcionar

## 3. Google OAuth 2.0 REST API - Para Backends

### Características
- **Uso**: Server-side
- **Controle**: Total sobre o fluxo
- **Segurança**: Máxima
- **Complexidade**: Alta

### Casos de Uso
- Backends que precisam de controle total
- Integrações complexas
- Aplicações que precisam de tokens de acesso

## Comparação das APIs

| Característica | GIS (Atual) | Sign-In JS (Legacy) | OAuth 2.0 REST |
|----------------|-------------|---------------------|-----------------|
| **Segurança** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Facilidade** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **UX** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Manutenção** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |
| **Recomendação** | ✅ Sim | ❌ Não | ✅ Para backends |

## Recursos Avançados do GIS

### One Tap Sign-In
```javascript
// Habilitar One Tap
google.accounts.id.prompt((notification) => {
  if (notification.isNotDisplayed()) {
    console.log('One Tap não exibido');
  }
});
```

### Auto Select
```javascript
// Auto seleção para usuários logados
google.accounts.id.initialize({
  auto_select: true
});
```

### Personalização Avançada
```javascript
google.accounts.id.renderButton(element, {
  theme: 'filled_blue', // ou 'outline'
  size: 'large', // ou 'medium', 'small'
  text: 'signin_with', // ou 'signup_with'
  shape: 'pill', // ou 'rectangular'
  width: 350,
  height: 50,
  click_listener: () => {
    console.log('Botão clicado');
  }
});
```

## Configuração no Google Cloud Console

### 1. Criar Projeto
1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie um novo projeto ou selecione existente

### 2. Habilitar APIs
1. Vá para "APIs & Services" > "Library"
2. Procure por "Google Identity Services"
3. Habilite a API

### 3. Configurar OAuth
1. Vá para "APIs & Services" > "Credentials"
2. Clique em "Create Credentials" > "OAuth 2.0 Client IDs"
3. Configure as origens autorizadas:
   - `http://localhost:3000` (desenvolvimento)
   - `https://seudominio.com` (produção)

### 4. Obter Client ID
- Copie o Client ID gerado
- Configure no arquivo `.env`:
```
VITE_GOOGLE_CLIENT_ID=seu-client-id-aqui
```

## Melhores Práticas

### Segurança
- ✅ Sempre valide tokens JWT
- ✅ Verifique email_verified
- ✅ Use HTTPS em produção
- ✅ Implemente logout adequado

### UX
- ✅ Use botões nativos do Google
- ✅ Implemente loading states
- ✅ Trate erros graciosamente
- ✅ Considere One Tap para usuários recorrentes

### Performance
- ✅ Carregue script de forma assíncrona
- ✅ Implemente cleanup adequado
- ✅ Evite múltiplas inicializações

## Troubleshooting

### Erros Comuns

#### "Client ID não configurado"
```javascript
// Verifique se a variável está definida
console.log(import.meta.env.VITE_GOOGLE_CLIENT_ID);
```

#### "Origem não autorizada"
- Verifique as origens no Google Cloud Console
- Inclua localhost para desenvolvimento

#### "Token inválido"
- Verifique se o Client ID está correto
- Confirme se as origens estão configuradas

### Debug
```javascript
// Habilitar logs detalhados
google.accounts.id.initialize({
  client_id: GOOGLE_CLIENT_ID,
  callback: handleCredentialResponse,
  debug: true // Apenas em desenvolvimento
});
```

## Conclusão

A **Google Identity Services (GIS)** é a API mais moderna, segura e recomendada para autenticação Google. Nossa implementação atual já usa esta API, garantindo a melhor experiência e segurança para os usuários.

### Próximos Passos
1. ✅ Implementação atual (GIS)
2. 🔄 Considerar One Tap para usuários recorrentes
3. 🔄 Implementar logout adequado
4. 🔄 Adicionar analytics de autenticação 