# Empat.IA Next Steps TODO

Este checklist registra os próximos passos imediatos do roadmap de produto. O foco é aproximar a experiência do app das IAs conversacionais atuais, dar mais controle ao usuário e tornar a personalização por nome consistente.

## Prioridade 1: Menu lateral no app do usuário

- [ ] Criar um shell autenticado com menu lateral para `/home`, `/chat` e futuras páginas do usuário.
- [ ] Exibir sessões/conversas recentes no menu lateral.
- [ ] Adicionar ação de nova sessão ou retorno à jornada terapêutica, conforme a regra de sessões do produto.
- [ ] Incluir atalhos para Jornada terapêutica, Dados pessoais, Configurações e Sair.
- [ ] Usar sidebar fixa em desktop e drawer/overlay em mobile.
- [ ] Garantir que a navegação preserve o `session_id` composto e o isolamento por usuário.

Arquivos prováveis:

- `apps/web-ui/src/App.jsx`
- `apps/web-ui/src/components/Home/HomeScreen.jsx`
- `apps/web-ui/src/components/Chat/ChatScreen.tsx`
- `apps/web-ui/src/services/api.js`
- `docs/FRONTEND.md`

## Prioridade 2: Página de Dados pessoais

- [ ] Criar rota autenticada `/personal-data` ou `/dados-pessoais`.
- [ ] Exibir nome completo, email/username técnico, voz preferida e preferências básicas.
- [ ] Permitir edição do nome completo e da voz preferida.
- [ ] Preparar espaço para consentimentos, exportação de dados e exclusão de conta.
- [ ] Salvar alterações no perfil do usuário via gateway.
- [ ] Mostrar feedback de carregamento, sucesso e erro.

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
- `apps/web-ui/src/components/PersonalData/`
- `apps/web-ui/src/services/api.js`
- `services/gateway-service/src/api/`
- `services/gateway-service/src/services/`
- `docs/TECHNICAL.md`

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
- [ ] Atualização de dados pessoais.
- [ ] Navegação desktop com sidebar.
- [ ] Navegação mobile com menu recolhido.
- [ ] Abertura de sessão existente via sidebar.
- [ ] Início/finalização de sessão pela jornada terapêutica.
- [ ] Histórico e mensagens continuam isolados por usuário.
