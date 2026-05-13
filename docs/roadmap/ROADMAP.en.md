# Empat.IA Roadmap

This roadmap consolidates the evolution of Empat.IA from a conversational AI with voice, emotion, and therapeutic sessions into a local-first cognitive engineering platform. The goal is to raise the project to a Staff AI Engineering standard: agentic architecture, traceable external memory, quantitative empathy evaluation, clinical safety, and data sovereignty.

> Product principle: Empat.IA is an emotional support and reflection tool, not a diagnosis, prescription, or clinical replacement system. Every technical evolution must preserve safety, privacy, traceability, and non-directive language.

## Current State

The experience and infrastructure foundations that support the next phases are already in place:

- [x] Authenticated shell with sidebar, Home, Chat, and recent sessions.
- [x] User isolation using opaque `chat_id` and a separated therapeutic session.
- [x] Initial profile with displayed name and voice preference.
- [x] Post-Google OAuth onboarding to capture full name when missing.
- [x] Admin without silent mocks on main screens.
- [x] Emotion Service stabilized as an auxiliary signal, not diagnosis.
- [x] Voice streaming v1 with SSE in Gateway, token streaming in AI Service, and incremental audio in Voice Service.
- [x] Local Gemma/GGUF validated as the default streaming provider.
- [x] Operational fallback for OpenAI, batch TTS, and short voice responses.

Core files already affected:

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

## Technical North Star

The next version should prioritize four evolution lines:

- **External memory and contextual data:** evolve basic RAG into a knowledge, session, and emotion backbone.
- **Cognitive architecture:** move from linear flow to state graph with reflection, checkpointing, and safety policies.
- **Evals-first:** validate Rogerian tone, perceived empathy, grounding, and safety with metrics and golden sets.
- **Local-first industrialization:** serve local models with low latency, governance, privacy, and continuous red teaming.

## Track 0: Architectural Foundation of the RAG System

Goal: define the architecture of the new knowledge system before implementing chunking, embeddings, and retrieval. RAG must be Admin-controlled, auditable by document/chunk/version, and decoupled enough to evolve without turning AI Service into an ingestion/search/generation monolith.

### Task 0.1: Knowledge/RAG Service Architecture Decision

- [x] Evaluate a dedicated architecture for a new `knowledge-service` or `rag-service`.
- [x] Define clear ownership across Gateway, AI Service, Admin Panel, metadata DB, vector store, and processing queue.
- [x] Separate ingestion/indexing flows from chat-time retrieval flows.
- [x] Define internal contracts: upload, validation, approval, ingestion, indexing, search, re-ranking, audit, and rollback.
- [x] Decide a local-first vector store and lexical search strategy, prioritizing local and traceable operation.

Likely files:

- `services/knowledge-service/`
- `services/gateway-service/src/api/admin_knowledge.py`
- `services/gateway-service/src/services/knowledge_client_service.py`
- `services/ai-service/src/services/rag_client_service.py`
- `apps/admin-panel/src/pages/`
- `apps/admin-panel/src/services/api.js`
- `docker-compose.yml`
- `docs/TECHNICAL.md`
- `docs/architecture/KNOWLEDGE_SERVICE.md`

Acceptance criteria:

- A documented decision exists on whether to create a dedicated microservice.
- Admin controls documents, versions, status, scopes, reprocessing, and activation.
- AI Service consumes retrieved context via internal contract and does not own the ingestion pipeline.
- Every RAG usage in responses is traceable to document, version, section, chunk, and scores.

### Task 0.2: Admin Control Plane for Knowledge

- [x] Create an admin document model: title, source, version, language, tags, scope, status, owner, and review policy.
- [x] Define operational states: draft, awaiting validation, processing, indexed, approved, active, failed, archived, superseded.
- [x] Allow initial ingestion of TXT, Markdown, and already-extracted structured content without automatic activation.
- [x] Expose admin lifecycle actions: approve, activate, deactivate, archive, and review chunks.
- [x] Log audit events for who changed document, status, scope, and usage policy.
- [x] Add binary upload and native extraction for PDF, Markdown, and TXT.
- [x] Add visual version comparison and async queue-based reprocessing.

Likely files:

- `apps/admin-panel/src/pages/KnowledgeBase.js`
- `apps/admin-panel/src/pages/KnowledgeDocuments.js`
- `apps/admin-panel/src/services/api.js`
- `services/gateway-service/src/api/admin_knowledge.py`
- `services/gateway-service/src/models/database.py`
- `docs/TECHNICAL.md`

Acceptance criteria:

- No document enters assistant scope without explicit Admin approval.
- Admin shows real processing state, errors, low-cohesion warnings, and last indexing timestamp.
- Sensitive operations have admin authentication, audit, and rollback support.

### Task 0.3: Retrieval Contracts for Chat and Prompts

- [x] Define the internal contract for AI Service knowledge retrieval requests.
- [x] Model Prompt Control RAG policy: enabled, scopes, `top_k`, minimum confidence, citations, and fallback.
- [x] Define internal retrieval response with chunks, scores, metadata, citable excerpts, and retrieval reasons.
- [x] Log retrieval attempts for admin auditing.
- [x] Define safe behavior when RAG fails, returns low confidence, or finds no suitable source.
- [x] Connect AI Service to `/api/v1/retrieve` at runtime.

Likely files:

- `services/gateway-service/src/services/prompt_service.py`
- `services/gateway-service/src/services/chat_service.py`
- `services/ai-service/src/services/llm_service.py`
- `services/ai-service/src/services/rag_client_service.py`
- `docs/TECHNICAL.md`

Acceptance criteria:

- RAG usage is not global or invisible; it depends on prompt, scope, and context.
- Retrieval failures degrade safely and do not invent sources.
- RAG responses include enough traceability for admin audit.

### Task 0.4: Next Step - LangGraph Orchestration Refactor

Goal: start an incremental refactor that migrates chat orchestration to a state graph without breaking current text, voice, and persistence behavior.

- [ ] Create a canonical `GraphState` with `chat_id`, `session_id`, `username`, `trace_id`, history, prompt policy, RAG context, emotional signal, and safety flags.
- [ ] Extract the core `gateway-service` flow into LangGraph nodes: input, context, retrieval, generation, safety, persistence, and output.
- [ ] Create `agent_service.py` in `gateway-service` as the graph execution layer (while keeping `chat_service.py` as facade).
- [ ] Encapsulate `ai-service` calls in a dedicated node with explicit success/fallback contract.
- [ ] Encapsulate `knowledge-service` retrieval (`/api/v1/retrieve`) in its own node with safe degradation.
- [ ] Encapsulate `emotion-service` signals in an auxiliary risk node (non-diagnostic), used only as safety context.
- [ ] Encapsulate `voice-service` synthesis in an output node to preserve streaming and latency.
- [ ] Add `LANGGRAPH_ENABLED` feature flag for gradual rollout and fast rollback.
- [ ] Add initial checkpointing (Redis/Mongo) by `chat_id` + `trace_id` for graph resume and auditing.

Services that benefit the most:

- `services/gateway-service`: explicit orchestration, testable transitions, and auditable state flow.
- `services/ai-service`: more stable input contract with pre-assembled context and explicit policies.
- `services/knowledge-service`: dedicated retrieval node with standardized telemetry and fallback behavior.
- `services/emotion-service`: emotional-signal integration becomes isolated and governable.
- `services/voice-service`: streaming/TTS becomes a declared output stage with lower coupling.

Likely files:

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

Acceptance criteria:

- LangGraph flow runs behind a feature flag with no functional regression in the current path.
- Every response has a state trail with `trace_id`, traversed nodes, and fallback reason.
- Crisis, low confidence, retrieval failure, and TTS failure are explicit transitions.
- Text and voice streaming preserve perceived quality and current latency budget.
- Legacy flow remains available until eval validation is complete.

## Track 1: Context Engineering and Data Backbone

Goal: turn RAG into an external memory system that respects the theoretical density of humanistic psychology while preserving traceability.

### Task 1.1: Adaptive Semantic Chunking

- [x] Replace fixed character-count splitting with hierarchical, semantically cohesive chunking.
- [x] Use `RecursiveCharacterTextSplitter` via `langchain-text-splitters`, with section/paragraph/sentence/word separators.
- [x] Validate chunk cohesion with local heuristics before indexing.
- [x] Avoid obvious cuts in the middle of quotes and sentences via local heuristics.
- [x] Record per-chunk metadata: document, version, source, section, language, hash, and ingestion timestamp.
- [ ] Add specific validation for sensitive concepts and Carl Rogers theoretical explanations.

Likely files:

- `services/knowledge-service/src/services/chunking_service.py`
- `services/knowledge-service/src/services/document_service.py`
- `services/knowledge-service/src/models/knowledge.py`
- `services/gateway-service/src/api/admin_knowledge.py`
- `apps/admin-panel/src/pages/`
- `docs/TECHNICAL.md`

Acceptance criteria:

- Chunks preserve minimum semantic unity in long materials.
- Each chunk is traceable to source document, version, and section.
- Pipeline rejects or flags low-cohesion chunks.

### Task 1.2: Multimodal Data with Pixeltable

- [ ] Evaluate Pixeltable as a declarative layer to connect text logs, embeddings, and emotional vectors.
- [ ] Create a conversational events table with `chat_id`, `message_id`, text, timestamp, detected emotion, and confidence.
- [ ] Connect `emotion-service` signals to history without treating emotion as diagnosis.
- [ ] Allow queries such as "high anxiety moments," "venting," or "emotional shift across the session."
- [ ] Define retention and consent policy for multimodal emotional data.

Likely files:

- `services/emotion-service/src/`
- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/models/database.py`
- `services/ai-service/src/services/`
- `docs/TECHNICAL.md`

Acceptance criteria:

- Emotional events are linked to messages without breaking per-user isolation.
- Emotion queries use metadata, confidence, and time window.
- Emotion Service failure degrades safely and does not block chat.

### Task 1.3: Hybrid Retrieval and Local Re-ranking

- [ ] Combine vector search with BM25 to balance semantics and exact terms.
- [ ] Add local re-ranking with Sentence-Transformers Cross-Encoder.
- [ ] Filter top-k before injecting context into prompt.
- [ ] Record vector score, lexical score, final score, and used sources.
- [ ] Create grounding evaluation to measure correct citations and absence of fabricated responses.

Likely files:

- `services/ai-service/src/services/rag_service.py`
- `services/ai-service/src/services/embedding_service.py`
- `services/gateway-service/src/services/prompt_service.py`
- `services/gateway-service/src/services/chat_service.py`

Acceptance criteria:

- Hybrid retrieval improves responses for both semantic concepts and specific terms.
- RAG responses include source, version, and retrieval reason.
- Prompt Control defines when RAG is enabled and which scope can be queried.

## Track 2: Cognitive Architecture and Agentic Orchestration

Goal: migrate from a linear flow to a state graph capable of decision-making, reflection, safety, and continuity across sessions.

### Task 2.1: Migration to LangGraph

- [ ] Model the conversation as a state graph in `gateway-service`.
- [ ] Define `GraphState` with history, `chat_id`, therapeutic session, latest emotional state, detected risk, and prompt metadata.
- [ ] Create nodes for triage, Rogerian support, crisis, memory retrieval, voice response, and closing.
- [ ] Add explicit transitions for crisis input, medical requests, low confidence, and fallback.
- [ ] Keep compatibility with current chat and streaming flow.

Likely files:

- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/services/agent_service.py`
- `services/gateway-service/src/services/prompt_service.py`
- `services/gateway-service/src/api/`
- `docs/TECHNICAL.md`

Acceptance criteria:

- Every response passes through a traceable graph state.
- Graph preserves text and voice streaming.
- Crisis and safety states are explicit and testable.

### Task 2.2: Actor-Critic Reflection Loop

- [ ] Create an "Actor Agent" to generate the initial Rogerian response.
- [ ] Create a "Critic Agent" with non-directiveness, emotional validation, non-judgment, and clinical safety rubrics.
- [ ] Rewrite responses when internal evaluation is below configured threshold.
- [ ] Record internal critique, score, rubric version, and rewrite reason.
- [ ] Prevent critic from exposing internal reasoning to end users.

Likely files:

- `services/ai-service/src/services/local_llm_service.py`
- `services/ai-service/src/services/llm_service.py`
- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/services/eval_service.py`
- `services/gateway-service/src/services/prompt_service.py`

Acceptance criteria:

- Judgmental, overly instructive, or prescriptive responses are detected before reaching the user.
- Rewrite improves score without excessive latency impact.
- Audit trail shows prompt, model, score, and rubric version.

### Task 2.3: Persistent Memory and Checkpointing

- [ ] Implement graph checkpointing in SQLite, Redis, or MongoDB according to final design.
- [ ] Allow conversation resume from relevant points without exposing other users' data.
- [ ] Persist aggregated emotional patterns across sessions with consent and data minimization.
- [ ] Add admin "time travel" for authorized therapeutic review.
- [ ] Define memory expiration, anonymization, and deletion policy.

Likely files:

- `services/gateway-service/src/models/database.py`
- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/services/user_therapeutic_session_service.py`
- `services/gateway-service/src/services/agent_checkpoint_service.py`
- `apps/admin-panel/src/pages/Conversations.js`

Acceptance criteria:

- Checkpoints are resumable by `chat_id` and authenticated user.
- Admin review respects permissions.
- Persistent data has documented retention and deletion.

## Track 3: Evaluation Framework and Scientific Rigor

Goal: replace manual validation with quantitative metrics, regression tests, and safety-aligned evaluation.

### Task 3.1: DeepEval and HEART Rubric

- [ ] Implement DeepEval for tone, safety, grounding, voice, and continuity tests.
- [ ] Define an internal HEART rubric: Human Alignment, Empathic Responsiveness, Attunement, Resonance, and Task-Following.
- [ ] Penalize responses that invalidate feelings, provide improper medical advice, diagnose, or ignore risk.
- [ ] Run evals in CI for critical prompts before activation.
- [ ] Publish minimum score by context: chat, voice, crisis, summary, RAG, and fallback.

Likely files:

- `tests/evals/`
- `services/gateway-service/src/services/prompt_service.py`
- `services/gateway-service/src/services/chat_service.py`
- `services/ai-service/src/services/`
- `.github/workflows/`

Acceptance criteria:

- Critical prompts have an automated suite.
- Prompt changes fail CI when they reduce safety or empathy.
- Scores are linked to `prompt_key`, `prompt_version`, model, and provider.

### Task 3.2: LLM-as-a-Judge Calibration

- [ ] Create a golden set with at least 50 dialogues reviewed by qualified humans.
- [ ] Define a human scale for empathy, non-directiveness, safety, grounding, and clarity.
- [ ] Tune judge prompts until Spearman correlation is above `0.85` against human scores.
- [ ] Compare remote judge and local judge when possible.
- [ ] Version golden set, judge prompts, and results.

Likely files:

- `tests/evals/golden_sets/`
- `tests/evals/judges/`
- `services/gateway-service/src/services/eval_service.py`
- `docs/TECHNICAL.md`

Acceptance criteria:

- A calibration report exists with correlation, sample, and limitations.
- The judge is not promoted without minimum agreement with human evaluation.
- Sensitive cases are manually reviewed before becoming golden-set examples.

### Task 3.3: BLRI-Inspired Empathy Score

- [ ] Implement a perceived empathic understanding metric inspired by the Barrett-Lennard Relationship Inventory.
- [ ] Model 12 dimensions on a `-3` to `+3` scale.
- [ ] Compute aggregate score:

```text
E_score = sum(V_i for i in 1..12)
```

- [ ] Record dimension, value, short justification, and rubric version.
- [ ] Use this score as a quality signal, not as clinical diagnosis.

Likely files:

- `tests/evals/rubrics/`
- `services/gateway-service/src/services/eval_service.py`
- `apps/admin-panel/src/pages/Analytics.js`
- `docs/TECHNICAL.md`

Acceptance criteria:

- Score is reproducible for the same dialogue and same judge version.
- Metric appears in internal reports without labeling the user.
- The system documents limitations and non-clinical usage.

## Track 4: Operations, Governance, and Scale

Goal: prepare Empat.IA for reliable, safe, efficient, and auditable production usage.

### Task 4.1: Model Serving with vLLM

- [ ] Evaluate vLLM with PagedAttention to serve multiple users with low latency.
- [ ] Compare vLLM, `llama-cpp-python`, and OpenAI fallback on cost, privacy, and latency.
- [ ] Define quantization strategy compatible with available hardware (for example AWQ or GGUF).
- [ ] Add throughput, time-to-first-token, tokens-per-second, and memory usage metrics.
- [ ] Keep local provider as default when quality and latency are acceptable.

Likely files:

- `services/ai-service/src/services/local_llm_service.py`
- `services/ai-service/src/main.py`
- `infrastructure/`
- `docker-compose.yml`
- `docs/TECHNICAL.md`

Acceptance criteria:

- AI Service supports real concurrency without severe UX degradation.
- Local model configuration is documented by hardware profile.
- Remote fallback remains available and auditable.

### Task 4.2: Privacy Gateway and PII Masking

- [ ] Create privacy middleware in `gateway-service`.
- [ ] Detect and mask PII before any external fallback.
- [ ] Combine Regex for obvious patterns with local NER for names, addresses, and sensitive entities.
- [ ] Log when masking happens without persisting sensitive data in logs.
- [ ] Evaluate LiteLLM Proxy only if it helps governance without reducing local control.

Likely files:

- `services/gateway-service/src/main.py`
- `services/gateway-service/src/middleware/`
- `services/gateway-service/src/services/privacy_service.py`
- `services/ai-service/src/services/llm_service.py`
- `docs/TECHNICAL.md`

Acceptance criteria:

- No external fallback receives raw PII when masking is enabled.
- Logs preserve auditability without leaking sensitive data.
- User keeps control over persisted data and deletion.

### Task 4.3: Clinical Safety Red Teaming

- [ ] Automate prompt-injection attacks against persona, safety, and clinical boundaries.
- [ ] Test diagnosis requests, prescriptions, self-harm, violence, emotional manipulation, and illegal content.
- [ ] Validate that responses preserve neutrality, welcoming tone, and safe guidance.
- [ ] Integrate red-team cases into regression evals.
- [ ] Create admin panel for critical failures, severity, and remediation status.

Likely files:

- `tests/evals/red_team/`
- `services/gateway-service/src/services/chat_service.py`
- `services/gateway-service/src/services/prompt_service.py`
- `apps/admin-panel/src/pages/Analytics.js`
- `.github/workflows/`

Acceptance criteria:

- Red-team cases run before activating new prompts or models.
- Critical failures block deploy or prompt activation.
- Every safety exception has severity, owner, and status.

## Immediate Operational Priorities

Recommended execution order:

### Primary Focus (next 2 sprints)

1. **LangGraph (next step):** execute Task 0.4 with incremental `gateway-service` refactor behind a feature flag.
2. **Prompt Control + runtime RAG:** finalize prompt-scoped RAG policy contract and end-to-end audit trail.
3. **Mandatory minimum evals:** enable safety/empathy gate for critical prompts before new rollouts.

Minimum deliverables for the primary focus:

- [ ] `gateway-service` running both legacy flow and LangGraph flow with `LANGGRAPH_ENABLED`.
- [ ] Versioned `GraphState` with `trace_id`, state, fallback_reason, and traversed nodes.
- [ ] Prompt policy (`enabled`, `allowed_scopes`, `top_k`, `min_confidence`, `require_citations`) enforced at runtime.
- [ ] Retrieval audit and source-usage records connected to response lifecycle.
- [ ] Minimum eval suite running in CI for critical prompts (blocking safety regressions).

### Secondary Backlog (after primary focus)

1. **RAG/Admin:** consolidate approved ingestion, cohesive chunking, embeddings, and source traceability.
2. **Privacy and PII:** protect external fallback before increasing remote model/tool usage.
3. **Local model serving:** evaluate vLLM and concurrency after evals and safety are measurable.

## Success Metrics

- Time to first voice token below `1s` in optimized local environment.
- Time to first audio below `1.5s` as initial target, with future target below `800ms`.
- Spearman correlation above `0.85` between automatic judge and human evaluation on the golden set.
- Zero responses with diagnosis, medical prescription, or dangerous instruction in critical tests.
- RAG responses always traceable by source, version, and chunk.
- Critical prompts always versioned, audited, and regression-covered.
- External fallback always preceded by privacy policy and PII masking.

## Safety and Governance Notes

- Assistant must keep Rogerian stance: welcoming, listening, reflection, and non-directiveness.
- System must not infer clinical diagnosis from text, voice, face, or detected emotion.
- Emotion Service is an auxiliary experience signal, never an autonomous clinical decision source.
- RAG must use only approved, versioned, citable knowledge.
- Persistent memory requires consent, defined retention, and deletion mechanism.
- Agents, MCPs, and tools should be exposed only after authentication, authorization, and per-user/session isolation contracts exist.

## Living Validation Checklist

- [x] Google login for new user.
- [x] Google login for existing user.
- [x] `session-1` guaranteed in the journey even when user lands directly on Home.
- [x] Personal data and voice settings update.
- [x] Desktop navigation with sidebar.
- [x] Mobile navigation with collapsed menu.
- [x] Opening an existing session via sidebar.
- [x] Session start/end through therapeutic journey.
- [x] History and messages remain user-isolated.
- [x] Local text streaming with Gemma/GGUF.
- [x] Audio streaming via Gateway and Voice Service.
- [ ] Manual baseline with 5 real interactions before/after.
- [ ] Minimum eval suite for critical prompts.
- [ ] Initial golden set with 50 dialogues.
- [ ] RAG pipeline with approval and sources.
- [ ] PII masking before external fallback.
