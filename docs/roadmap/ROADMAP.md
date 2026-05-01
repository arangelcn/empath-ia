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

## Próximas etapas: voz primeiro, depois Prompt Control e RAG

Com a Prioridade 4 concluída e o Emotion Service estabilizado, a ordem prática foi ajustada: antes de avançar no RAG e em LLMOps completos, priorizamos o modo de voz de baixa latência. A razão foi de produto: a experiência conversacional depende primeiro de a IA responder e falar sem esperar o texto inteiro.

O que mudou na ordem:

- **Prioridade 7 foi antecipada e implementada em v1**: streaming SSE no Gateway, tokens em streaming no AI Service, Gemma local como provider padrão, GCP Chirp 3 HD para áudio PCM em streaming e fallback batch por trecho.
- **Prioridade 5 continua necessária**: Prompt Control ainda precisa de versionamento forte, auditoria e testes, mas já existe fallback seguro para `voice_short_response`.
- **Prioridade 6 segue pendente**: RAG/Admin foi deliberadamente pulado nesta rodada. Ele continua importante, mas não deve bloquear a estabilização do fluxo de voz.

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

> Status: pendente. Esta prioridade foi adiada para permitir a entrega do fluxo de voz em baixa latência primeiro.

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

## Prioridade 7 - Voice Service e Baixa Latência ✅ v1

Esta prioridade foi antecipada em relação ao RAG. A v1 moveu o modo de voz de um fluxo síncrono (`LLM completo → MP3 completo → download → play`) para um fluxo incremental com SSE, Gemma local em streaming, chunking por frase no Gateway e GCP Chirp 3 HD para áudio PCM em streaming.

## 🎯 Objetivo
Reduzir a latência percebida, permitindo que texto e áudio comecem antes do fim da resposta completa da IA. A meta ideal de primeiro áudio `< 800ms` continua como alvo de otimização, mas a validação local atual confirmou streaming funcional ponta a ponta.

Validação local registrada:

- AI Service `/openai/chat/stream` com Gemma local: `provider=local`, `model=gemma4:e4b`, múltiplos `text_delta`, primeiro delta em ~993ms.
- Gateway `/api/chat/send-stream`: `provider=local`, `model=gemma4:e4b`, `text_delta` + `audio_chunk`, primeiro texto em ~1070ms, primeiro áudio em ~1742ms.
- Voice Service `/api/v1/synthesize-stream`: GCP Chirp 3 HD funcionando com `x-voice-used: pt-BR-Chirp3-HD-Orus`, PCM 24kHz.

---

### 🛠️ Prioridade 7

- [x] **Medição de Baseline**
    - [x] Instrumentar latência ponta a ponta com `trace_id` no frontend, gateway, geração LLM, TTS e reprodução.
    - [x] Separar métricas de TTS, STT/reconhecimento no frontend, rede, tamanho da resposta e tempo de primeira reprodução.
    - [x] Registrar baseline técnico inicial em ambiente local com credenciais GCP.
    - [ ] Registrar baseline manual antes/depois com 5 interações reais de produto.

- [x] **Otimização de Prompt e Contexto**
    - [x] Implementar modo de resposta curta para voz no AI Service via Prompt Control (`voice_short_response`) com fallback hardcoded seguro.
    - [x] Configurar limites de tokens e frases mais naturais para áudio (menos listas, mais prosa).
    - [x] Ajustar personalização para usar somente primeiro nome como forma de tratamento, nunca nome completo/sobrenome.

- [x] **Arquitetura de Streaming (GCP TTS)**
    - [x] **AI Service:** Habilitar `stream=True` na OpenAI e no modelo local `llama-cpp-python`, usando `Async Generators`.
    - [x] **Chunking:** Criar buffer no Gateway para agrupar tokens em sentenças completas (antes de enviar ao TTS).
    - [x] **Voice Service:** Implementar `StreamingResponse` utilizando a API de streaming do Google Cloud TTS.
    - [x] **Gateway:** Criar endpoint paralelo de chat por Server-Sent Events (SSE) para entrega de texto/áudio em tempo real.
    - [x] Corrigir fallback para não falar palavra por palavra: flush por tempo agora exige trecho mínimo falável.

- [x] **Hibridismo e Modelos Locais**
    - [x] Adicionar Piper como fallback local opcional por CLI (`TTS_LOCAL_PROVIDER=piper`).
    - [x] Validar Gemma local como provider padrão do AI Service no streaming.
    - [ ] Comparar candidatos TTS/LLM por idioma pt-BR, qualidade, privacidade e tempo de resposta em ambiente real.
    - [x] Documentar trade-offs entre local, cloud e híbrido.

- [x] **Resiliência e Performance**
    - [x] Adicionar cache seguro (Redis) para TTS de frases de acolhimento comuns e genéricas em allowlist.
    - [x] Criar health/status do Voice Service com monitoramento de provedor ativo, streaming disponível e fallback local.
    - [x] Garantir fallback seguro: se Chirp streaming falhar, áudio batch é gerado por trecho/frase e enfileirado no frontend.

---

## 📂 Arquivos Impactados

| Serviço | Caminho do Arquivo | Descrição da Alteração |
| :--- | :--- | :--- |
| **Voice Service** | `services/voice-service/src/` | Implementação do gRPC streaming do GCP. |
| **Gateway** | `services/gateway-service/src/services/chat_service.py` | Lógica de chunking de texto e gestão de fluxo SSE. |
| **AI Service** | `services/ai-service/src/services/openai_service.py` | Refatoração para suporte a stream de tokens. |
| **AI Service** | `services/ai-service/src/services/local_llm_service.py` | Streaming real com Gemma/GGUF via `llama-cpp-python`. |
| **Frontend** | `apps/web-ui/src/hooks/useStreamingAudioQueue.js` | Fila de reprodução (Audio Queue) para chunks PCM. |
| **Docs** | `docs/TECHNICAL.md` | Atualização da arquitetura de eventos. |

---

## ✅ Critérios de Aceite
1. [x] Existe baseline técnico de latência documentado para o fluxo local.
2. [x] Voice mode utiliza respostas curtas e adequadas à fala rítmica.
3. [x] Gemma local foi validado como provider funcional em streaming.
4. [x] O sistema não aguarda o fim da geração do LLM para iniciar texto/áudio.
5. [x] Otimizações de voz respeitam regras de segurança e fallback de prompt.
6. [ ] Medição manual com 5 interações reais antes/depois ainda precisa ser registrada.

## Notas consolidadas

- Segurança mental: manter o assistente como apoio, sem diagnóstico, prescrição ou plano clínico autônomo. Casos de crise precisam de resposta segura, metadados de risco e revisão quando aplicável.
- Avaliação: criar casos de regressão para prompts, segurança, grounding de RAG, voz e continuidade entre sessões antes de promover mudanças sensíveis.
- RAG: usar somente conhecimento aprovado, versionado, revisável e citável. Recuperação deve ser escopo de prompt/contexto, não comportamento global invisível.
- Voz: o fluxo streaming v1 já está implementado; próximas mudanças devem melhorar latência, qualidade e confiabilidade sem quebrar o fallback síncrono.
- Modelos locais: Gemma local é o provider padrão validado para streaming; OpenAI continua como fallback operacional.
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
