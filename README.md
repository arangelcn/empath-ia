# 🧠 empatIA - Psicólogo Virtual com Avatar

Um assistente de psicologia virtual empático baseado em Carl Rogers, com avatar animado usando IA.

## ✨ Funcionalidades

- 💬 **Chat com IA**: Conversas empáticas baseadas em Carl Rogers
- 🎭 **Avatar Animado**: Vídeos gerados com DID-AI
- 🔄 **Hot Reload**: Desenvolvimento com atualização automática
- 🐳 **Docker**: Ambiente containerizado

## 🚀 Configuração Rápida

### 1. Clone o projeto
```bash
git clone <seu-repo>
cd empath-ia
```

### 2. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
# OpenAI Configuration
OPENAI_API_KEY=sua_chave_openai_aqui
MODEL_NAME=gpt-4o

# DID AI Configuration (para vídeo do avatar)
DID_API_USERNAME=seu_username_aqui
DID_API_PASSWORD=sua_senha_aqui
```

**Como obter as chaves:**
- **OpenAI**: https://platform.openai.com/api-keys
- **DID-AI**: https://www.d-id.com/ → Account Settings → API Key
  - A chave fornecida no formato `API_USERNAME:API_PASSWORD`
  - **Separe** em duas variáveis: username e password

### 3. Execute o projeto
```bash
# Modo desenvolvimento (hot reload)
./dev.sh

# Ou manualmente
docker compose up --build --watch
```

### 4. Acesse a aplicação
- **Frontend**: http://localhost:7860
- **Backend**: http://localhost:8000

## 🛠️ Desenvolvimento

### Hot Reload
O projeto está configurado para hot reload automático:
- Alterações no código são sincronizadas automaticamente
- FastAPI recarrega automaticamente
- Streamlit detecta mudanças e oferece reload

### Logs
Para visualizar logs detalhados:
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

## 📁 Estrutura do Projeto

```
empath-ia/
├── backend/           # FastAPI + OpenAI + DID-AI
│   ├── Dockerfile
│   ├── app.py
│   ├── did_client.py
│   └── requirements.txt
├── frontend/          # Streamlit UI
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── docker-compose.yml # Orquestração
├── dev.sh           # Script de desenvolvimento
└── README.md
```

## ⚠️ Troubleshooting

### Vídeo do avatar não aparece
1. **Verifique se `DID_API_USERNAME` e `DID_API_PASSWORD` estão configuradas no `.env`**
   - Obtenha as credenciais em: https://www.d-id.com/ → Account Settings
   - Se a chave vier no formato `username:password`, separe em duas variáveis
2. **Verifique os logs**: `docker compose logs backend`
3. **Erros comuns:**
   - `Status 500`: Credenciais incorretas ou formato inválido
   - `Status 401/403`: Credenciais inválidas ou expiradas
   - `Status 429`: Limite de API excedido

### Backend não conecta
1. Verifique se `OPENAI_API_KEY` está configurada
2. Reinicie os containers: `docker compose restart`

### Hot reload não funciona
1. Use `docker compose up --build --watch`
2. Ou execute `./dev.sh`

## 🎯 Próximos Passos

- [ ] Interface mais avançada
- [ ] Histórico de conversas
- [ ] Diferentes avatares
- [ ] Análise de sentimentos
