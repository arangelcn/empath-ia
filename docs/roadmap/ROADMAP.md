# Empat.IA Roadmap

Este roadmap registra os próximos passos imediatos do produto. O foco é aproximar a experiência do app das IAs conversacionais atuais, dar mais controle ao usuário e tornar a personalização por nome consistente sem deixar a interface pesada.

## Prioridade 1: Menu lateral no app do usuário ✅

- [x] Criar um shell autenticado com menu lateral para `/home`, `/chat` e futuras páginas do usuário.
- [x] Exibir sessões/conversas recentes no menu lateral.
- [x] Adicionar ação principal para continuar conversa, iniciar próxima sessão ou voltar à Home.
- [x] Incluir atalho para Home, acesso único de perfil/configurações e Sair.
- [x] Remover acesso a chat sem sessão; `/chat` redireciona para `/home`.
- [x] Usar sidebar fixa em desktop e drawer/overlay em mobile.
- [x] Garantir que a navegação use `chat_id` opaco e preserve isolamento por usuário no gateway/banco.

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

## Próximas etapas: Prompt Control, RAG e voz

Com a Prioridade 4 concluída e o Emotion Service estabilizado como fonte operacional de sinais emocionais, o próximo eixo do produto passa a ser controle de comportamento da IA. Antes de acelerar voz, o sistema precisa tratar prompts, versões, avaliação, curadoria de conhecimento e RAG como superfície administrativa forte, auditável e segura.

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
- `docs/TECHNICAL.md`

Critérios de aceite:

- Admin deixa claro quando um dado é real, vazio ou indisponível.
- Dashboard e páginas principais não usam dados simulados como se fossem produção.
- Falhas de API são visíveis e acionáveis, sem mascarar problemas com métricas falsas.
- Cada tela possui contrato documentado e endpoint correspondente ou tarefa técnica aberta.

## Pós-Prioridade 4: Emotion Service estabilizado ✅

- [x] Ajustar dependências e inicialização do Emotion Service para reduzir falhas de runtime.
- [x] Corrigir integração DeepFace/OpenFace e compatibilidade do processador facial.
- [x] Manter política de GPU clara: AI Service como dono padrão da GPU e Emotion Service operando em CPU quando necessário.
- [x] Preservar o Emotion Service como sinal auxiliar de experiência, não como diagnóstico clínico.
- [x] Conectar análise emocional ao histórico/contexto sem quebrar isolamento por usuário e sessão.

Critérios de aceite:

- Emotion Service sobe de forma previsível no ambiente local/containerizado.
- Falhas de análise emocional degradam a experiência de forma controlada.
- O gateway consegue registrar/consultar sinais emocionais sem depender de dados simulados.
- Documentação continua deixando claro que emoção detectada não equivale a diagnóstico.

## Prioridade 5: Controle de Prompts e LLMOps

- [ ] Separar endpoints administrativos de prompts em namespace protegido, por exemplo `/api/admin/prompts`, ou adicionar autenticação service-to-service para manter `/api/prompts` seguro.
- [ ] Criar versionamento de prompts: versão, status, autor, data de publicação, changelog, tags e motivo da alteração.
- [ ] Diferenciar estados operacionais: rascunho, em revisão, ativo, arquivado e rollback disponível.
- [ ] Registrar em cada resposta da IA: `prompt_key`, `prompt_version`, modelo, provedor, latência, fallback e flags de segurança.
- [ ] Adicionar preview/teste de prompt no Admin com variáveis reais/sintéticas controladas.
- [ ] Criar suite mínima de regressão para prompts críticos: segurança, tom Rogeriano, não diagnóstico, crise, voz e continuidade de sessão.
- [ ] Criar metadados mínimos de segurança por resposta: nível de risco, categorias, necessidade de revisão e motivo resumido.
- [ ] Permitir comparação entre versões de prompt com resultado esperado, resultado obtido e observações de revisão.
- [ ] Mapear variáveis permitidas por prompt para evitar interpolação livre e vazamento de dados sensíveis.
- [ ] Definir prompts por contexto de uso: chat, voz, geração de sessão, resumo, fallback, análise, RAG e crise.
- [ ] Criar trilha de auditoria para criação, edição, ativação, arquivamento e rollback.

Arquivos prováveis:

- `apps/admin-panel/src/pages/PromptManagement.js`
- `apps/admin-panel/src/services/api.js`
- `services/gateway-service/src/main.py`
- `services/gateway-service/src/api/admin.py`
- `services/gateway-service/src/services/prompt_service.py`
- `services/ai-service/src/services/openai_service.py`
- `services/gateway-service/src/services/chat_service.py`
- `docs/TECHNICAL.md`

Critérios de aceite:

- Admin diferencia prompt em rascunho, ativo, arquivado e versão anterior.
- Toda resposta gerada pela IA pode ser rastreada até a versão de prompt usada.
- Mudanças de prompt têm auditoria, revisão mínima e caminho de rollback.
- Prompts críticos têm testes de regressão antes de serem ativados.
- Respostas sensíveis possuem metadados suficientes para avaliação e revisão administrativa.
- O AI Service não depende de strings hardcoded para comportamento principal quando houver prompt ativo no banco.

## Prioridade 6: Pipeline RAG pelo Admin

- [ ] Definir modelo de dados para base de conhecimento: documento, versão, fonte, status, tags, idioma, escopo e responsável.
- [ ] Criar fluxo de upload no Admin para PDFs, Markdown, TXT e materiais estruturados.
- [ ] Implementar validação de arquivo: tipo, tamanho, duplicidade, metadados mínimos e política de privacidade.
- [ ] Criar pipeline de ingestão: extração de texto, limpeza, chunking, embeddings, indexação vetorial e auditoria.
- [ ] Expor status do processamento no Admin: pendente, processando, indexado, falhou, arquivado.
- [ ] Permitir revisão/ativação manual de materiais antes de ficarem disponíveis para o assistente.
- [ ] Integrar recuperação ao AI Service de forma model-agnostic, para funcionar com OpenAI ou modelo local.
- [ ] Registrar citações/metadados de origem nas respostas quando conhecimento aprovado for usado.
- [ ] Adicionar avaliação mínima de grounding para evitar respostas desconectadas dos documentos.
- [ ] Conectar RAG ao Prompt Control: prompts devem declarar quando podem recuperar conhecimento, qual escopo podem consultar e como citar fontes.
- [ ] Definir política de expiração/revisão de documentos para impedir conhecimento obsoleto em respostas sensíveis.

Arquivos prováveis:

- `apps/admin-panel/src/pages/`
- `apps/admin-panel/src/services/api.js`
- `services/gateway-service/src/api/admin.py`
- `services/ai-service/src/services/`
- `services/ai-service/src/services/rag_service.py`
- `services/ai-service/src/services/embedding_service.py`
- `docs/TECHNICAL.md`

Critérios de aceite:

- Admin consegue cadastrar e acompanhar documentos da base de conhecimento.
- Documentos só entram no índice após validação e aprovação explícita.
- Assistente consegue recuperar conhecimento aprovado sem depender do provedor do LLM.
- Respostas que usam RAG preservam fonte, versão e rastreabilidade.
- Recuperação é desativável por prompt/contexto e não vira comportamento global invisível.
- Existe avaliação mínima para medir grounding, citação correta e ausência de resposta inventada.

## Prioridade 7: Voice Service e baixa latência

- [ ] Medir latência atual ponta a ponta: captura no frontend, gateway, geração LLM, TTS e reprodução.
- [ ] Separar métricas de TTS, STT, rede, tamanho da resposta e tempo de primeira reprodução.
- [ ] Estudar opções locais para voz: STT local, TTS local e modelos híbridos com fallback para Google Cloud.
- [ ] Comparar candidatos locais por idioma pt-BR, qualidade, privacidade, custo, CPU/GPU e tempo de resposta.
- [ ] Implementar modo de resposta curta para voz no AI Service via Prompt Control, com limites de tokens e frases mais naturais para áudio.
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
- `docs/TECHNICAL.md`

Critérios de aceite:

- Existe baseline de latência antes de alterar arquitetura.
- Voice mode tem respostas mais curtas e adequadas à fala.
- Pelo menos uma opção local ou híbrida é testada com métricas comparáveis.
- O serviço expõe status suficiente para diagnosticar lentidão e falhas.
- Otimizações de voz respeitam as versões de prompt, regras de segurança e rastreabilidade já definidas.

## Notas consolidadas

- Segurança mental: manter o assistente como apoio, sem diagnóstico, prescrição ou plano clínico autônomo. Casos de crise precisam de resposta segura, metadados de risco e revisão quando aplicável.
- Avaliação: criar casos de regressão para prompts, segurança, grounding de RAG, voz e continuidade entre sessões antes de promover mudanças sensíveis.
- RAG: usar somente conhecimento aprovado, versionado, revisável e citável. Recuperação deve ser escopo de prompt/contexto, não comportamento global invisível.
- Voz: medir latência antes de trocar arquitetura. Testar STT/TTS local ou híbrido somente com comparação de qualidade, custo, privacidade e tempo de primeira reprodução.
- Modelos locais: promover modelo local apenas se passar em qualidade, segurança, latência e fallback. OpenAI continua sendo fallback operacional enquanto isso.
- MCP/agentes: tratar como etapa futura. Só expor tools/resources depois de existir contrato de segurança, autenticação interna e isolamento por usuário/sessão.

## Checklist de validação

- [x] Login Google para usuário novo.
- [x] Login Google para usuário existente.
- [x] Atualização de dados pessoais e voz.
- [x] Navegação desktop com sidebar.
- [x] Navegação mobile com menu recolhido.
- [x] Abertura de sessão existente via sidebar.
- [x] Início/finalização de sessão pela jornada terapêutica.
- [x] Histórico e mensagens continuam isolados por usuário.
