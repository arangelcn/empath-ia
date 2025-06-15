# Web UI - Empath.IA

Este é o frontend da aplicação Empath.IA, responsável por fornecer a interface de chat para que os usuários possam interagir com a psicóloga virtual. A aplicação é construída com tecnologias modernas, focando em uma experiência de usuário fluida e reativa.

## ✨ Visão Geral

A interface principal consiste em uma tela de chat onde o usuário pode enviar mensagens de texto. As respostas da inteligência artificial são acompanhadas pela síntese de voz, que é reproduzida automaticamente. A aplicação também detecta e exibe a emoção do usuário em tempo real.

## 🚀 Tecnologias Utilizadas

-   **Framework:** [React](https://reactjs.org/)
-   **Build Tool:** [Vite](https://vitejs.dev/)
-   **Linguagem:** [TypeScript](https://www.typescriptlang.org/) & JavaScript
-   **Estilização:** [Tailwind CSS](https://tailwindcss.com/)
-   **Ícones:** [Lucide React](https://lucide.dev/guide/react)
-   **Cliente HTTP:** [Axios](https://axios-http.com/)

## 📂 Estrutura de Diretórios

A estrutura de arquivos do `web-ui` é organizada da seguinte forma para garantir escalabilidade e manutenibilidade:

```
apps/web-ui/
├── public/              # Arquivos estáticos
├── src/
│   ├── assets/          # Imagens, fontes, etc.
│   │   ├── components/      # Componentes React reutilizáveis
│   │   └── Common/
│   ├── hooks/           # Hooks customizados do React
│   ├── services/        # Lógica de comunicação com APIs
│   └── utils/           # Funções utilitárias
├── .env.example         # Exemplo de variáveis de ambiente
└── package.json         # Dependências e scripts do projeto
```

### Componentes Principais

-   `src/components/ChatScreen.tsx`: Orquestra toda a interface de chat. Gerencia o estado das mensagens, a entrada do usuário, o status de carregamento e a interação com os serviços de backend.

### Hooks Customizados

-   `src/hooks/useAudioPlayer.js`: Um hook React para gerenciar a reprodução de áudio. Ele encapsula a lógica de play, pause, e rastreia o estado de reprodução (`isPlaying`, `activeAudioUrl`).

### Serviços

-   `src/services/api.js`: Contém as funções para interagir com o `gateway-service`. Atualmente, possui a função `sendMessage` que envia a mensagem do usuário para o backend.

## ⚙️ Configuração do Ambiente

Para executar este projeto localmente, você precisará configurar as variáveis de ambiente. Crie um arquivo `.env` na raiz de `apps/web-ui` a partir do `.env.example`.

```bash
# URL do Gateway Service que o frontend irá se comunicar
VITE_API_URL=http://localhost:8000
```

## 📜 Scripts Disponíveis

No diretório do projeto, você pode executar:

-   `npm install`: Instala todas as dependências do projeto.
-   `npm run dev`: Executa a aplicação em modo de desenvolvimento.
-   `npm run build`: Compila o projeto para produção.
-   `npm run lint`: Executa o linter para identificar problemas no código.
-   `npm run format`: Formata o código usando o Prettier.
-   `npm run preview`: Inicia um servidor local para visualizar a build de produção. 