# Empat.IA Roadmap

Este roadmap registra os próximos passos imediatos do produto. O foco é aproximar a experiência do app das IAs conversacionais atuais, dar mais controle ao usuário e tornar a personalização por nome consistente sem deixar a interface pesada.

## Prioridade 1: Menu lateral no app do usuário ✅

- [x] Criar um shell autenticado com menu lateral para `/home`, `/chat` e futuras páginas do usuário.
- [x] Exibir sessões/conversas recentes no menu lateral.
- [x] Adicionar ação principal para continuar conversa, iniciar próxima sessão ou voltar à Home.
- [x] Incluir atalho para Home, acesso único de perfil/configurações e Sair.
- [x] Remover acesso a chat sem sessão; `/chat` redireciona para `/home`.
- [x] Usar sidebar fixa em desktop e drawer/overlay em mobile.
- [x] Garantir que a navegação preserve o `session_id` composto e o isolamento por usuário.

Arquivos principais:

- `apps/web-ui/src/App.jsx`
- `apps/web-ui/src/components/Layout/AuthenticatedShell.jsx`
- `apps/web-ui/src/components/Home/HomeScreen.jsx`
- `apps/web-ui/src/components/Chat/ChatScreen.tsx`
- `docs/FRONTEND.md`

## Prioridade 2: Dados pessoais e configurações rápidas ✅

- [x] Trocar os placeholders inferiores da sidebar por uma área compacta de conta.
- [x] Exibir na parte inferior da sidebar: avatar/inicial, nome exibido ou email, um único botão de ícone para "Perfil e voz" e botão "Sair".
- [x] Criar uma experiência simples para "Perfil e voz" em página leve autenticada.
- [x] Exibir email/username técnico, nome de exibição e voz preferida.
- [x] Permitir editar nome de exibição e voz preferida.
- [x] Manter configurações avançadas fora desta etapa; foco em identidade e voz.
- [x] Salvar alterações no perfil/preferências do usuário via gateway.
- [x] Mostrar feedback de carregamento, sucesso e erro.

Direção de UX:

- A sidebar deve continuar limpa: navegação e sessões em cima/meio, conta e saída no rodapé, sem bloco de progresso.
- "Dados pessoais" e "Configurações" podem ser consolidados em um único acesso inicial chamado "Perfil e voz".
- O acesso a "Perfil e voz" pode ser apenas um botão de ícone no rodapé da sidebar.
- A escolha de voz deve ser uma lista simples com estado selecionado, sem fluxo longo de onboarding.
- Em mobile, o acesso deve abrir bem como drawer/tela curta, sem quebrar a navegação do chat.

Campos iniciais sugeridos:

| Campo | Uso |
|---|---|
| `username` | Identificador técnico, hoje baseado no email/Google. |
| `email` | Conta autenticada via Google, quando disponível. |
| `full_name` | Nome completo informado pelo usuário. |
| `display_name` | Nome usado na interface e na personalização da IA. Pode derivar de `full_name`. |
| `selected_voice` | Voz TTS preferida. |

Arquivos prováveis:

- `apps/web-ui/src/App.jsx`
- `apps/web-ui/src/components/Layout/AuthenticatedShell.jsx`
- `apps/web-ui/src/components/Profile/ProfileVoicePage.jsx`
- `apps/web-ui/src/services/api.js`
- `services/gateway-service/src/api/`
- `services/gateway-service/src/services/`
- `docs/TECHNICAL.md`

Critérios de aceite:

- Usuário acessa "Perfil e voz" pela parte inferior da sidebar.
- A sidebar mostra uma identidade mínima do usuário sem ocupar espaço das sessões.
- Usuário vê o email/username técnico, mas edita apenas nome exibido e voz.
- Alterar voz atualiza a preferência usada nas próximas conversas.
- Feedback de sucesso/erro aparece sem redirecionar o usuário para fora do fluxo atual.

## Prioridade 3: Nome completo no login/onboarding

- [ ] Depois do Google OAuth, verificar se o perfil já possui `full_name` ou `display_name`.
- [ ] Se estiver ausente, pedir o nome completo antes de concluir o onboarding.
- [ ] Persistir o nome completo no perfil do usuário.
- [ ] Manter `username`/email como identificador técnico e não usar nome completo em `session_id`.
- [ ] Passar `display_name` para Home e Chat.
- [ ] Incluir `display_name` no contexto enviado à IA para que ela chame o usuário pelo nome.
- [ ] Tratar usuários existentes sem quebrar sessões antigas.

Critérios de aceite:

- Usuário novo faz login, informa nome completo e chega à Home com o nome correto.
- Usuário existente sem nome completo recebe o pedido uma única vez.
- Usuário existente com nome salvo não repete o fluxo.
- Chat usa o nome salvo em textos de interface e contexto de personalização.
- Email/username continua sendo usado para autenticação, queries e isolamento de sessão.

## Checklist de validação

- [ ] Login Google para usuário novo.
- [ ] Login Google para usuário existente.
- [x] Atualização de dados pessoais e voz.
- [x] Navegação desktop com sidebar.
- [x] Navegação mobile com menu recolhido.
- [x] Abertura de sessão existente via sidebar.
- [x] Início/finalização de sessão pela jornada terapêutica.
- [x] Histórico e mensagens continuam isolados por usuário.
