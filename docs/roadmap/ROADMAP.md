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

## Prioridade 3: Nome completo no login/onboarding ✅

- [x] Depois do Google OAuth, verificar se o perfil já possui `full_name` ou `display_name`.
- [x] Se estiver ausente, pedir o nome completo antes de concluir o onboarding.
- [x] Persistir o nome completo no perfil do usuário.
- [x] Manter `username`/email como identificador técnico e não usar nome completo em `session_id`.
- [x] Passar `display_name` para Home e Chat.
- [x] Incluir `display_name` no contexto enviado à IA para que ela chame o usuário pelo nome.
- [x] Tratar usuários existentes sem quebrar sessões antigas.

Critérios de aceite:

- Usuário novo faz login, informa nome completo e chega à Home com o nome correto.
- Usuário existente sem nome completo recebe o pedido uma única vez.
- Usuário existente com nome salvo não repete o fluxo.
- Chat usa o nome salvo em textos de interface e contexto de personalização.
- Email/username continua sendo usado para autenticação, queries e isolamento de sessão.

## Próximas etapas: Admin, RAG e voz

As próximas prioridades devem transformar o Admin em uma ferramenta operacional real para configuração, curadoria de conhecimento e observabilidade, enquanto o Voice Service evolui para menor latência e opções locais.

## Prioridade 4: Ajustes do Admin ✅

- [x] Auditar telas do Admin para identificar dados mockados, fallbacks silenciosos e endpoints ainda inexistentes.
- [x] Mapear cada tela para contrato real de API: Dashboard, Usuários, Sessões, Conversas, Prompts, Analytics, Status e Configurações.
- [x] Substituir mocks por estados explícitos de carregamento, vazio, erro e indisponibilidade do backend.
- [x] Garantir autenticação consistente no Admin usando o mesmo padrão de token/headers das rotas protegidas.
- [x] Validar permissões mínimas para separar ações administrativas de leitura, edição e operação sensível.
- [x] Registrar lacunas de backend em issues/tarefas pequenas antes de iniciar grandes refactors de UI.

Arquivos prováveis:

- `apps/admin-panel/src/pages/Dashboard.js`
- `apps/admin-panel/src/pages/UserManagement.js`
- `apps/admin-panel/src/pages/SessionManagement.js`
- `apps/admin-panel/src/pages/Conversations.js`
- `apps/admin-panel/src/pages/PromptManagement.js`
- `apps/admin-panel/src/pages/Analytics.js`
- `apps/admin-panel/src/pages/SystemStatus.js`
- `apps/admin-panel/src/services/api.js`
- `services/gateway-service/src/api/`
- `docs/admin/ADMIN_CONTRACT_AUDIT.md`

Critérios de aceite:

- Admin deixa claro quando um dado é real, vazio ou indisponível.
- Dashboard e páginas principais não usam dados simulados como se fossem produção.
- Falhas de API são visíveis e acionáveis, sem mascarar problemas com métricas falsas.
- Cada tela possui contrato documentado e endpoint correspondente ou tarefa técnica aberta.

## Prioridade 5: Pipeline RAG pelo Admin

- [ ] Definir modelo de dados para base de conhecimento: documento, versão, fonte, status, tags, idioma, escopo e responsável.
- [ ] Criar fluxo de upload no Admin para PDFs, Markdown, TXT e materiais estruturados.
- [ ] Implementar validação de arquivo: tipo, tamanho, duplicidade, metadados mínimos e política de privacidade.
- [ ] Criar pipeline de ingestão: extração de texto, limpeza, chunking, embeddings, indexação vetorial e auditoria.
- [ ] Expor status do processamento no Admin: pendente, processando, indexado, falhou, arquivado.
- [ ] Permitir revisão/ativação manual de materiais antes de ficarem disponíveis para o assistente.
- [ ] Integrar recuperação ao AI Service de forma model-agnostic, para funcionar com OpenAI ou modelo local.
- [ ] Registrar citações/metadados de origem nas respostas quando conhecimento aprovado for usado.
- [ ] Adicionar avaliação mínima de grounding para evitar respostas desconectadas dos documentos.

Arquivos prováveis:

- `apps/admin-panel/src/pages/`
- `apps/admin-panel/src/services/api.js`
- `services/gateway-service/src/api/admin.py`
- `services/ai-service/src/services/`
- `docs/MENTAL_HEALTH_MEDICAL_AI_ROADMAP.md`
- `docs/TECHNICAL.md`

Critérios de aceite:

- Admin consegue cadastrar e acompanhar documentos da base de conhecimento.
- Documentos só entram no índice após validação e aprovação explícita.
- Assistente consegue recuperar conhecimento aprovado sem depender do provedor do LLM.
- Respostas que usam RAG preservam fonte, versão e rastreabilidade.

## Prioridade 6: Voice Service e baixa latência

- [ ] Medir latência atual ponta a ponta: captura no frontend, gateway, geração LLM, TTS e reprodução.
- [ ] Separar métricas de TTS, STT, rede, tamanho da resposta e tempo de primeira reprodução.
- [ ] Estudar opções locais para voz: STT local, TTS local e modelos híbridos com fallback para Google Cloud.
- [ ] Comparar candidatos locais por idioma pt-BR, qualidade, privacidade, custo, CPU/GPU e tempo de resposta.
- [ ] Implementar modo de resposta curta para voz no AI Service, com limites de tokens e frases mais naturais para áudio.
- [ ] Avaliar streaming ou chunking de áudio para reduzir tempo até o usuário ouvir a primeira frase.
- [ ] Adicionar cache seguro para TTS de frases comuns quando não houver dado pessoal sensível.
- [ ] Criar health/status do Voice Service com provedor ativo, fila, latência média e fallback.
- [ ] Documentar trade-offs entre local, cloud e híbrido antes de promover um modelo local como padrão.

Arquivos prováveis:

- `services/voice-service/src/`
- `services/voice-service/README.md`
- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/main.py`
- `services/ai-service/src/services/openai_service.py`
- `docs/roadmap/VOICE_CONVERSATION_ROADMAP.md`
- `docs/LOCAL_MODEL_TEST_PLAN.md`

Critérios de aceite:

- Existe baseline de latência antes de alterar arquitetura.
- Voice mode tem respostas mais curtas e adequadas à fala.
- Pelo menos uma opção local ou híbrida é testada com métricas comparáveis.
- O serviço expõe status suficiente para diagnosticar lentidão e falhas.

## Checklist de validação

- [x] Login Google para usuário novo.
- [x] Login Google para usuário existente.
- [x] Atualização de dados pessoais e voz.
- [x] Navegação desktop com sidebar.
- [x] Navegação mobile com menu recolhido.
- [x] Abertura de sessão existente via sidebar.
- [x] Início/finalização de sessão pela jornada terapêutica.
- [x] Histórico e mensagens continuam isolados por usuário.
