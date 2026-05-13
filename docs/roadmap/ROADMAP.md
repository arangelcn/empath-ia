# Empat.IA Roadmap

Este roadmap consolida a evolução do Empat.IA de uma IA conversacional com voz, emoção e sessões terapêuticas para uma plataforma de engenharia cognitiva local-first. O objetivo é elevar o projeto para um padrão de Staff AI Engineering: arquitetura agêntica, memória externa rastreável, avaliação quantitativa da empatia, segurança clínica e soberania de dados.

> Princípio de produto: o Empat.IA é uma ferramenta de apoio emocional e reflexão, não um sistema de diagnóstico, prescrição ou substituição clínica. Toda evolução técnica deve preservar segurança, privacidade, rastreabilidade e linguagem não diretiva.

## Estado Atual

Já foram entregues as bases de experiência e infraestrutura que sustentam as próximas fases:

- [x] Shell autenticado com sidebar, Home, Chat e sessões recentes.
- [x] Isolamento por usuário usando `chat_id` opaco e sessão terapêutica separada.
- [x] Perfil inicial com nome exibido e preferência de voz.
- [x] Onboarding pós-Google OAuth para capturar nome completo quando ausente.
- [x] Admin sem mocks silenciosos nas telas principais.
- [x] Emotion Service estabilizado como sinal auxiliar, não diagnóstico.
- [x] Streaming de voz v1 com SSE no Gateway, tokens em streaming no AI Service e áudio incremental no Voice Service.
- [x] Gemma/GGUF local validado como provider padrão para streaming.
- [x] Fallback operacional para OpenAI, TTS batch e respostas curtas de voz.

Arquivos centrais já afetados:

- `apps/web-ui/src/App.jsx`
- `apps/web-ui/src/components/Layout/AuthenticatedShell.jsx`
- `apps/web-ui/src/components/Home/HomeScreen.jsx`
- `apps/web-ui/src/components/Chat/ChatScreen.tsx`
- `apps/web-ui/src/hooks/useStreamingAudioQueue.js`
- `apps/admin-panel/src/pages/`
- `services/gateway-service/src/main.py`
- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/services/prompt_service.py`
- `services/ai-service/src/services/llm_service.py`
- `services/ai-service/src/services/local_llm_service.py`
- `services/voice-service/src/`
- `services/emotion-service/src/`
- `docs/TECHNICAL.md`
- `docs/FRONTEND.md`

## Norte Técnico

A próxima versão deve priorizar quatro linhas de evolução:

- **Memória externa e dados contextuais:** transformar o RAG básico em um backbone de conhecimento, sessão e emoção.
- **Arquitetura cognitiva:** sair de fluxo linear para grafo de estados com reflexão, checkpointing e políticas de segurança.
- **Evals-first:** validar tom Rogeriano, empatia percebida, grounding e segurança com métricas e golden sets.
- **Industrialização local-first:** servir modelos locais com baixa latência, governança, privacidade e red teaming contínuo.

## Track 0: Fundação Arquitetural do Sistema RAG

Objetivo: definir a arquitetura do novo sistema de conhecimento antes de implementar chunking, embeddings e recuperação. O RAG deve ser controlável pelo Admin, auditável por documento/chunk/versão e desacoplado o suficiente para evoluir sem tornar o AI Service um monólito de ingestão, busca e geração.

### Tarefa 0.1: Decisão de Arquitetura do Knowledge/RAG Service

- [x] Avaliar arquitetura dedicada para um novo `knowledge-service` ou `rag-service`.
- [x] Definir ownership claro entre Gateway, AI Service, Admin Panel, banco de metadados, vector store e fila de processamento.
- [x] Separar fluxos de ingestão/indexação dos fluxos de recuperação usados durante o chat.
- [x] Definir contratos internos: upload, validação, aprovação, ingestão, indexação, busca, re-ranking, auditoria e rollback.
- [x] Decidir estratégia local-first de vector store e busca lexical, priorizando operação local e rastreável.

Arquivos prováveis:

- `services/knowledge-service/`
- `services/gateway-service/src/api/admin_knowledge.py`
- `services/gateway-service/src/services/knowledge_client_service.py`
- `services/ai-service/src/services/rag_client_service.py`
- `apps/admin-panel/src/pages/`
- `apps/admin-panel/src/services/api.js`
- `docker-compose.yml`
- `docs/TECHNICAL.md`
- `docs/architecture/KNOWLEDGE_SERVICE.md`

Critérios de aceite:

- Existe decisão documentada sobre criar ou não um microserviço dedicado.
- O Admin controla documentos, versões, status, escopos, reprocessamento e ativação.
- O AI Service consome contexto recuperado por contrato interno, sem possuir o pipeline de ingestão.
- Cada uso de RAG em resposta é rastreável até documento, versão, seção, chunk e scores.

### Tarefa 0.2: Admin Control Plane para Conhecimento

- [x] Criar modelo administrativo para documentos: título, fonte, versão, idioma, tags, escopo, status, responsável e política de revisão.
- [x] Definir estados operacionais: rascunho, aguardando validação, processando, indexado, aprovado, ativo, falhou, arquivado e substituído.
- [x] Permitir ingestão inicial de TXT, Markdown e conteúdo estruturado já extraído sem ativação automática.
- [x] Expor ações administrativas de lifecycle: aprovar, ativar, desativar, arquivar e revisar chunks.
- [x] Registrar auditoria de quem alterou documento, status, escopo e política de uso.
- [x] Adicionar upload binário e extração nativa para PDF, Markdown e TXT.
- [x] Adicionar comparação visual de versões e reprocessamento assíncrono com fila.

Arquivos prováveis:

- `apps/admin-panel/src/pages/KnowledgeBase.js`
- `apps/admin-panel/src/pages/KnowledgeDocuments.js`
- `apps/admin-panel/src/services/api.js`
- `services/gateway-service/src/api/admin_knowledge.py`
- `services/gateway-service/src/models/database.py`
- `docs/TECHNICAL.md`

Critérios de aceite:

- Nenhum documento entra no escopo do assistente sem aprovação explícita no Admin.
- O Admin mostra status real de processamento, erro, warnings de baixa coesão e data de última indexação.
- Operações sensíveis têm autenticação administrativa, auditoria e rollback possível.

### Tarefa 0.3: Contratos de Recuperação para Chat e Prompts

- [x] Definir contrato interno para quando o AI Service solicita recuperação de conhecimento.
- [x] Modelar política RAG de Prompt Control: habilitado, escopos, `top_k`, confiança mínima, citações e fallback.
- [x] Definir resposta interna de retrieval com chunks, scores, metadados, trechos citáveis e motivos de recuperação.
- [x] Registrar tentativa de retrieval para auditoria administrativa.
- [x] Definir comportamento seguro quando o RAG falhar, retornar baixa confiança ou não encontrar fonte adequada.
- [x] Conectar o AI Service ao endpoint `/api/v1/retrieve` em runtime.

Arquivos prováveis:

- `services/gateway-service/src/services/prompt_service.py`
- `services/gateway-service/src/services/chat_service.py`
- `services/ai-service/src/services/llm_service.py`
- `services/ai-service/src/services/rag_client_service.py`
- `docs/TECHNICAL.md`

Critérios de aceite:

- O uso de RAG não é global nem invisível; ele depende de prompt, escopo e contexto.
- Falhas de retrieval degradam com segurança e não inventam fonte.
- Respostas com RAG incluem rastreabilidade suficiente para auditoria administrativa.

### Tarefa 0.4: Próximo passo - Refactor de Orquestração com LangGraph

Objetivo: iniciar um refactor incremental para migrar a orquestração de chat para grafo de estados, sem quebrar o fluxo atual de texto, voz e persistência.

- [ ] Criar `GraphState` canônico com `chat_id`, `session_id`, `username`, `trace_id`, histórico, política de prompt, contexto RAG, sinal emocional e flags de segurança.
- [ ] Extrair o fluxo principal do `gateway-service` para nós LangGraph: entrada, contexto, retrieval, geração, segurança, persistência e saída.
- [ ] Criar `agent_service.py` no `gateway-service` como camada de execução do grafo (mantendo `chat_service.py` como fachada).
- [ ] Encapsular chamada ao `ai-service` em nó dedicado com contrato explícito de sucesso/fallback.
- [ ] Encapsular retrieval via `knowledge-service` (`/api/v1/retrieve`) em nó separado, com degradação segura quando indisponível.
- [ ] Encapsular sinais do `emotion-service` em nó auxiliar de risco (sem diagnóstico), usado apenas como contexto de segurança.
- [ ] Encapsular síntese do `voice-service` em nó de saída para preservar streaming e latência.
- [ ] Adicionar feature flag `LANGGRAPH_ENABLED` para rollout gradual e rollback rápido.
- [ ] Adicionar checkpointing inicial (Redis/Mongo) por `chat_id` + `trace_id` para retomada e auditoria do grafo.

Serviços que mais se beneficiam:

- `services/gateway-service`: ganha orquestração explícita, testável e com transições auditáveis.
- `services/ai-service`: recebe contrato de entrada mais estável, com contexto pronto e políticas explícitas.
- `services/knowledge-service`: passa a ser chamado por um nó de retrieval dedicado, com telemetria e fallback padronizados.
- `services/emotion-service`: integração de sinal emocional fica isolada e governável em nó próprio.
- `services/voice-service`: streaming/TTS entra como etapa declarada de saída, reduzindo acoplamento.

Arquivos prováveis:

- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/services/agent_service.py`
- `services/gateway-service/src/services/graph_state.py`
- `services/gateway-service/src/services/prompt_service.py`
- `services/gateway-service/src/services/session_context_service.py`
- `services/ai-service/src/services/llm_service.py`
- `services/ai-service/src/services/rag_client_service.py`
- `services/knowledge-service/src/api/knowledge_routes.py`
- `services/emotion-service/src/`
- `services/voice-service/src/`
- `docs/TECHNICAL.md`

Critérios de aceite:

- Fluxo LangGraph roda por feature flag sem regressão funcional no fluxo atual.
- Cada resposta possui trilha de estados com `trace_id`, nós percorridos e motivo de fallback.
- Crise, baixa confiança, falha de retrieval e falha de TTS têm transições explícitas.
- Streaming de texto e voz mantém qualidade percebida e latência dentro dos limites atuais.
- O fluxo legado permanece disponível até a validação completa dos evals.

## Track 1: Engenharia de Contexto e Backbone de Dados

Objetivo: transformar o RAG em um sistema de memória externa que respeite a densidade teórica da psicologia humanista e preserve rastreabilidade.

### Tarefa 1.1: Chunking Semântico Adaptativo

- [x] Substituir divisão por contagem fixa de caracteres por chunking hierárquico e semanticamente coeso.
- [x] Usar `RecursiveCharacterTextSplitter` via `langchain-text-splitters`, com separadores por seção, parágrafo, frase e palavra.
- [x] Validar coesão de chunks com heurística local antes da indexação.
- [x] Evitar cortes óbvios no meio de citações e frases por heurística local.
- [x] Registrar metadados por chunk: documento, versão, fonte, seção, idioma, hash e data de ingestão.
- [ ] Adicionar validação específica para conceitos sensíveis e explicações teóricas de Carl Rogers.

Arquivos prováveis:

- `services/knowledge-service/src/services/chunking_service.py`
- `services/knowledge-service/src/services/document_service.py`
- `services/knowledge-service/src/models/knowledge.py`
- `services/gateway-service/src/api/admin_knowledge.py`
- `apps/admin-panel/src/pages/`
- `docs/TECHNICAL.md`

Critérios de aceite:

- Chunks preservam unidade semântica mínima em materiais longos.
- Cada chunk é rastreável até documento, versão e seção de origem.
- O pipeline rejeita ou marca chunks com baixa coesão.

### Tarefa 1.2: Dados Multimodais com Pixeltable

- [ ] Avaliar Pixeltable como camada declarativa para vincular logs textuais, embeddings e vetores emocionais.
- [ ] Criar uma tabela de eventos conversacionais com `chat_id`, `message_id`, texto, timestamp, emoção detectada e confiança.
- [ ] Conectar sinais do `emotion-service` ao histórico sem tratar emoção como diagnóstico.
- [ ] Permitir consultas como "momentos de alta ansiedade", "desabafo" ou "mudança emocional na sessão".
- [ ] Definir política de retenção e consentimento para dados emocionais multimodais.

Arquivos prováveis:

- `services/emotion-service/src/`
- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/models/database.py`
- `services/ai-service/src/services/`
- `docs/TECHNICAL.md`

Critérios de aceite:

- Eventos emocionais são associados a mensagens sem quebrar isolamento por usuário.
- Consultas por emoção usam metadados, confiança e janela temporal.
- Falha no Emotion Service degrada com segurança e não bloqueia o chat.

### Tarefa 1.3: Recuperação Híbrida e Re-ranking Local

- [ ] Combinar busca vetorial com BM25 para equilibrar semântica e termos exatos.
- [ ] Adicionar re-ranking local com Cross-Encoder do Sentence-Transformers.
- [ ] Filtrar top-k antes de inserir contexto no prompt.
- [ ] Registrar score vetorial, score lexical, score final e fontes usadas.
- [ ] Criar avaliação de grounding para medir citações corretas e ausência de resposta inventada.

Arquivos prováveis:

- `services/ai-service/src/services/rag_service.py`
- `services/ai-service/src/services/embedding_service.py`
- `services/gateway-service/src/services/prompt_service.py`
- `services/gateway-service/src/services/chat_service.py`

Critérios de aceite:

- Recuperação híbrida melhora respostas para conceitos semânticos e termos específicos.
- Respostas com RAG incluem fonte, versão e motivo de recuperação.
- Prompt Control define quando RAG está habilitado e qual escopo pode ser consultado.

## Track 2: Arquitetura Cognitiva e Orquestração Agêntica

Objetivo: migrar o sistema de um fluxo linear para um grafo de estados capaz de decisão, reflexão, segurança e continuidade entre sessões.

### Tarefa 2.1: Migração para LangGraph

- [ ] Modelar a conversa como grafo de estados no `gateway-service`.
- [ ] Definir `GraphState` com histórico, `chat_id`, sessão terapêutica, último estado emocional, risco detectado e metadados de prompt.
- [ ] Criar nós para triagem, suporte Rogeriano, crise, recuperação de memória, resposta de voz e encerramento.
- [ ] Adicionar transições explícitas para entradas de crise, pedidos médicos, baixa confiança e fallback.
- [ ] Manter compatibilidade com o fluxo atual de chat e streaming.

Arquivos prováveis:

- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/services/agent_service.py`
- `services/gateway-service/src/services/prompt_service.py`
- `services/gateway-service/src/api/`
- `docs/TECHNICAL.md`

Critérios de aceite:

- Cada resposta passa por um estado rastreável do grafo.
- O grafo preserva streaming de texto e voz.
- Estados de crise e segurança são explícitos e testáveis.

### Tarefa 2.2: Loop de Reflexão Actor-Critic

- [ ] Criar um "Agente Ator" para gerar resposta Rogeriana inicial.
- [ ] Criar um "Agente Crítico" com rubricas de não diretividade, validação emocional, ausência de julgamento e segurança clínica.
- [ ] Reescrever respostas quando a avaliação interna ficar abaixo do limiar configurado.
- [ ] Registrar crítica interna, score, versão de rubrica e motivo do rewrite.
- [ ] Impedir que o crítico exponha raciocínio interno ao usuário final.

Arquivos prováveis:

- `services/ai-service/src/services/local_llm_service.py`
- `services/ai-service/src/services/llm_service.py`
- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/services/eval_service.py`
- `services/gateway-service/src/services/prompt_service.py`

Critérios de aceite:

- Respostas julgadoras, instrutivas ou prescritivas são detectadas antes de chegar ao usuário.
- O rewrite melhora o score sem aumentar demais a latência.
- A trilha de auditoria mostra prompt, modelo, score e versão da rubrica.

### Tarefa 2.3: Memória Persistente e Checkpointing

- [ ] Implementar checkpointing do grafo em SQLite, Redis ou MongoDB, conforme o desenho final.
- [ ] Permitir retomada de conversa a partir de pontos relevantes sem expor dados de outro usuário.
- [ ] Persistir padrões emocionais agregados entre sessões com consentimento e minimização de dados.
- [ ] Adicionar "time travel" administrativo para revisão terapêutica autorizada.
- [ ] Definir política de expiração, anonimização e exclusão de memória.

Arquivos prováveis:

- `services/gateway-service/src/models/database.py`
- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/services/user_therapeutic_session_service.py`
- `services/gateway-service/src/services/agent_checkpoint_service.py`
- `apps/admin-panel/src/pages/Conversations.js`

Critérios de aceite:

- Checkpoints são retomáveis por `chat_id` e usuário autenticado.
- Revisão administrativa respeita permissões.
- Dados persistentes têm retenção e exclusão documentadas.

## Track 3: Framework de Avaliação e Rigor Científico

Objetivo: substituir validação manual por métricas quantitativas, testes de regressão e avaliação alinhada com segurança clínica.

### Tarefa 3.1: Evals com DeepEval e Rubrica HEART

- [ ] Implementar DeepEval para testes de tom, segurança, grounding, voz e continuidade.
- [ ] Definir uma rubrica HEART interna: Human Alignment, Empathic Responsiveness, Attunement, Resonance e Task-Following.
- [ ] Penalizar respostas que invalidam sentimentos, dão conselhos médicos indevidos, diagnosticam ou ignoram risco.
- [ ] Rodar evals no CI para prompts críticos antes de ativação.
- [ ] Publicar score mínimo por contexto: chat, voz, crise, resumo, RAG e fallback.

Arquivos prováveis:

- `tests/evals/`
- `services/gateway-service/src/services/prompt_service.py`
- `services/gateway-service/src/services/chat_service.py`
- `services/ai-service/src/services/`
- `.github/workflows/`

Critérios de aceite:

- Prompts críticos têm suíte automatizada.
- Mudanças de prompt falham no CI quando reduzem segurança ou empatia.
- Scores ficam ligados a `prompt_key`, `prompt_version`, modelo e provedor.

### Tarefa 3.2: Calibração de LLM-as-a-Judge

- [ ] Criar golden set com pelo menos 50 diálogos revisados por humanos qualificados.
- [ ] Definir escala humana para empatia, não diretividade, segurança, grounding e clareza.
- [ ] Ajustar prompts do juiz até atingir correlação de Spearman maior que `0.85` com notas humanas.
- [ ] Comparar juiz remoto e juiz local quando possível.
- [ ] Versionar golden set, prompts de juiz e resultados.

Arquivos prováveis:

- `tests/evals/golden_sets/`
- `tests/evals/judges/`
- `services/gateway-service/src/services/eval_service.py`
- `docs/TECHNICAL.md`

Critérios de aceite:

- Existe relatório de calibração com correlação, amostra e limitações.
- O juiz não é promovido sem concordância mínima com avaliação humana.
- Casos sensíveis são revisados manualmente antes de virar golden set.

### Tarefa 3.3: Score de Empatia Inspirado no BLRI

- [ ] Implementar métrica de compreensão empática percebida inspirada no Barrett-Lennard Relationship Inventory.
- [ ] Modelar 12 dimensões avaliadas em escala de `-3` a `+3`.
- [ ] Calcular score agregado:

```text
E_score = sum(V_i for i in 1..12)
```

- [ ] Registrar dimensão, valor, justificativa curta e versão da rubrica.
- [ ] Usar o score como sinal de qualidade, não como diagnóstico clínico.

Arquivos prováveis:

- `tests/evals/rubrics/`
- `services/gateway-service/src/services/eval_service.py`
- `apps/admin-panel/src/pages/Analytics.js`
- `docs/TECHNICAL.md`

Critérios de aceite:

- O score é reproduzível para o mesmo diálogo e mesma versão de juiz.
- A métrica aparece em relatórios internos sem rotular o usuário.
- O sistema documenta limitações e uso não clínico da métrica.

## Track 4: Operações, Governança e Escala

Objetivo: preparar o Empat.IA para uso confiável, seguro, eficiente e auditável em produção.

### Tarefa 4.1: Model Serving com vLLM

- [ ] Avaliar vLLM com PagedAttention para servir múltiplos usuários com baixa latência.
- [ ] Comparar vLLM, `llama-cpp-python` e OpenAI fallback para custo, privacidade e latência.
- [ ] Definir estratégia de quantização compatível com o hardware disponível, como AWQ ou GGUF.
- [ ] Adicionar métricas de throughput, tempo até primeiro token, tokens por segundo e uso de memória.
- [ ] Manter provider local como padrão quando qualidade e latência forem aceitáveis.

Arquivos prováveis:

- `services/ai-service/src/services/local_llm_service.py`
- `services/ai-service/src/main.py`
- `infrastructure/`
- `docker-compose.yml`
- `docs/TECHNICAL.md`

Critérios de aceite:

- O AI Service suporta concorrência real sem degradar drasticamente a experiência.
- A configuração de modelo local é documentada por hardware.
- Fallback remoto continua disponível e auditável.

### Tarefa 4.2: Gateway de Privacidade e Mascaramento de PII

- [ ] Criar middleware de privacidade no `gateway-service`.
- [ ] Detectar e mascarar PII antes de qualquer fallback externo.
- [ ] Combinar Regex para padrões óbvios com NER local para nomes, endereços e entidades sensíveis.
- [ ] Registrar quando houve mascaramento sem persistir o dado sensível em logs.
- [ ] Avaliar LiteLLM Proxy apenas se ajudar governança sem reduzir controle local.

Arquivos prováveis:

- `services/gateway-service/src/main.py`
- `services/gateway-service/src/middleware/`
- `services/gateway-service/src/services/privacy_service.py`
- `services/ai-service/src/services/llm_service.py`
- `docs/TECHNICAL.md`

Critérios de aceite:

- Nenhum fallback externo recebe PII bruta quando mascaramento está habilitado.
- Logs preservam auditoria sem vazar dados sensíveis.
- O usuário mantém controle sobre dados persistidos e exclusão.

### Tarefa 4.3: Red Teaming de Segurança Clínica

- [ ] Automatizar ataques de prompt injection contra persona, segurança e limites clínicos.
- [ ] Testar pedidos de diagnóstico, prescrição, automutilação, violência, manipulação emocional e conteúdo ilegal.
- [ ] Validar que respostas preservam neutralidade, acolhimento e orientação segura.
- [ ] Integrar casos de red team aos evals de regressão.
- [ ] Criar painel administrativo de falhas críticas, severidade e status de correção.

Arquivos prováveis:

- `tests/evals/red_team/`
- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/services/prompt_service.py`
- `apps/admin-panel/src/pages/Analytics.js`
- `.github/workflows/`

Critérios de aceite:

- Casos de red team rodam antes de ativar prompts ou modelos novos.
- Falhas críticas bloqueiam deploy ou ativação de prompt.
- Toda exceção de segurança tem severidade, dono e status.

## Prioridades Operacionais Imediatas

Ordem recomendada para execução:

### Foco Primário (próximos 2 sprints)

1. **LangGraph (próximo passo):** executar a Tarefa 0.4 com refactor incremental no `gateway-service` e feature flag.
2. **Prompt Control + RAG runtime:** fechar contrato de política RAG por prompt e trilha de auditoria fim-a-fim.
3. **Evals mínimos obrigatórios:** ativar gate de segurança/empatia para prompts críticos antes de novos rollouts.

Entregáveis mínimos do foco primário:

- [ ] `gateway-service` com fluxo legado + fluxo LangGraph com `LANGGRAPH_ENABLED`.
- [ ] `GraphState` versionado com `trace_id`, estado, fallback_reason e nós percorridos.
- [ ] Política de prompt (`enabled`, `allowed_scopes`, `top_k`, `min_confidence`, `require_citations`) aplicada em runtime.
- [ ] Auditoria de retrieval e uso de fontes conectada ao ciclo de resposta.
- [ ] Suite mínima de evals executando no CI para prompts críticos (bloqueando regressão de segurança).

### Backlog Secundário (após foco primário)

1. **RAG/Admin:** consolidar ingestão aprovada, chunking coeso, embeddings e rastreabilidade de fontes.
2. **Privacidade e PII:** proteger fallback externo antes de aumentar uso de modelos remotos ou ferramentas.
3. **Model serving local:** avaliar vLLM e concorrência depois que evals e segurança estiverem mensuráveis.

## Métricas de Sucesso

- Tempo até primeiro token em voz abaixo de `1s` em ambiente local otimizado.
- Tempo até primeiro áudio abaixo de `1.5s` como meta inicial, com alvo futuro menor que `800ms`.
- Correlação de Spearman maior que `0.85` entre juiz automático e avaliação humana no golden set.
- Zero respostas com diagnóstico, prescrição médica ou instrução perigosa em testes críticos.
- Respostas com RAG sempre rastreáveis por fonte, versão e chunk.
- Prompts críticos sempre versionados, auditados e cobertos por regressão.
- Fallback externo sempre precedido por política de privacidade e mascaramento de PII.

## Notas de Segurança e Governança

- O assistente deve manter postura Rogeriana: acolhimento, escuta, reflexão e não diretividade.
- O sistema não deve inferir diagnóstico clínico a partir de texto, voz, rosto ou emoção detectada.
- Emotion Service é sinal auxiliar de experiência, nunca fonte de decisão clínica autônoma.
- RAG deve usar somente conhecimento aprovado, versionado e citável.
- Memória persistente exige consentimento, retenção definida e mecanismo de exclusão.
- Agentes, MCPs e tools só devem ser expostos depois de existir contrato de autenticação, autorização e isolamento por usuário/sessão.

## Checklist Vivo de Validação

- [x] Login Google para usuário novo.
- [x] Login Google para usuário existente.
- [x] `session-1` garantida na jornada mesmo quando o usuário chega direto na Home.
- [x] Atualização de dados pessoais e voz.
- [x] Navegação desktop com sidebar.
- [x] Navegação mobile com menu recolhido.
- [x] Abertura de sessão existente via sidebar.
- [x] Início/finalização de sessão pela jornada terapêutica.
- [x] Histórico e mensagens continuam isolados por usuário.
- [x] Streaming local de texto com Gemma/GGUF.
- [x] Streaming de áudio via Gateway e Voice Service.
- [ ] Baseline manual com 5 interações reais antes/depois.
- [ ] Suite mínima de evals para prompts críticos.
- [ ] Golden set inicial com 50 diálogos.
- [ ] Pipeline RAG com aprovação e fontes.
- [ ] Mascaramento de PII antes de fallback externo.
