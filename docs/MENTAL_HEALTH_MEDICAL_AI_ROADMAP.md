# Empat.IA Mental Health Medical AI Roadmap

Empat.IA is a Medical AI Assistant focused on mental health support. It should help users reflect, organize emotional context, continue supportive sessions, and prepare for professional care when needed. It must not diagnose, prescribe medication, replace clinicians, or replace emergency services.

This roadmap is grounded in the current application:

- Session-based user journey with `session-1` onboarding.
- Progressive therapeutic sessions generated from previous context.
- Dr. Rogers/person-centered conversational assistant.
- Emotion analysis through webcam frames.
- Voice output through text-to-speech.
- Admin panel for prompts, users, sessions, conversations, analytics, and service health.
- Persistent memory in MongoDB through users, messages, conversations, session contexts, user sessions, emotions, and prompts.
- A future local-first LLM runtime where the main assistant model is served by Empat.IA infrastructure, for example Gemma or another locally hosted model.

The learning source in `docs/learning/_OceanofPDF.com_AI_Agents_in_Action_-_Micheal_Lanham (1).pdf` should be used after understanding the app and planning the steps of action.

## Product Positioning

Empat.IA should become:

> A mental-health-focused Medical AI Assistant that provides supportive conversations, emotional tracking, session continuity, psychoeducation, and clinician-ready summaries with strong safety boundaries.

The assistant should be biased toward:

- Empathy.
- Active listening.
- Reflection.
- Emotional awareness.
- Psychoeducation.
- Care continuity.
- Safety escalation.
- Human review for risk.

The assistant should avoid:

- Diagnosis.
- Medication instructions.
- Emergency medical advice beyond escalation.
- Claims of being a therapist, doctor, or emergency service.
- Overconfident medical statements.

## Local Model Strategy

Empat.IA should move toward a local-model-first architecture. The main mental health assistant should run on a model served by the project owner, such as Gemma or another self-hosted LLM. External hosted APIs can remain optional for development, comparison, or emergency fallback, but they should not be the product default.

Target principles:

- Own the runtime: serve the model locally or in private infrastructure.
- Keep the AI service as the model abstraction layer.
- Prefer an OpenAI-compatible local inference endpoint when possible, so the current `OpenAIService` can evolve instead of being replaced.
- Track model identity explicitly: provider, model name, model version, quantization, context window, serving backend, and prompt version.
- Evaluate every candidate model before promotion.
- Never assume a model is safe because it runs locally. Safety still requires prompts, risk classifiers, tests, monitoring, and review.
- Keep private user data inside controlled infrastructure whenever possible.

Candidate local serving options:

| Option | Use case |
|---|---|
| Gemma served locally | Main candidate for a self-hosted assistant model. |
| Ollama | Fast local development and model switching. |
| llama.cpp | Lightweight CPU/GPU inference and quantized models. |
| vLLM | Higher-throughput serving when GPU infrastructure is available. |
| LM Studio | Manual local experimentation and early model comparison. |

Configuration direction:

```env
LLM_PROVIDER=local
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=gemma
LOCAL_LLM_TIMEOUT_SECONDS=60
LLM_FALLBACK_PROVIDER=none
```

The exact model name should match the local serving backend. For example, Ollama, LM Studio, vLLM, and llama.cpp may expose different model identifiers.

## Current Architecture Fit

| Current capability | Medical mental health direction |
|---|---|
| `system_rogers` prompt | Evolve into a safer mental health assistant prompt with medical boundaries. |
| Session onboarding | Collect supportive context without over-collecting sensitive medical data. |
| Session context generation | Produce structured mental health continuity notes and risk indicators. |
| Next-session generation | Suggest safe follow-up sessions based on user goals and emotional state. |
| Emotion service | Use as supportive signal only, never as diagnosis. |
| Voice service | Support accessible, warm interaction while preserving privacy. |
| Admin prompt management | Add safety prompts, review prompts, and evaluation status. |
| Admin conversations | Add review workflow for high-risk sessions. |
| MCP migration plan | Expose safe app tools/resources for future agent workflows. |
| AI service | Evolve from OpenAI-specific orchestration into a provider-agnostic local-model-first LLM gateway. |

## Phase 1: Safety And Identity

Goal: make the assistant safe enough to carry a medical-adjacent mental health identity.

Actions:

- Rename product language from generic therapy replacement to mental health support assistant.
- Update system prompt boundaries:
  - Always answer in Brazilian Portuguese unless user requests English practice.
  - Provide emotional support and psychoeducation.
  - Avoid diagnosis and medication guidance.
  - Encourage professional help when appropriate.
  - Escalate self-harm, suicide, abuse, psychosis, severe panic, and urgent physical symptoms.
- Add a safety/risk metadata concept to responses:
  - `risk_level`: `low`, `medium`, `high`, `crisis`
  - `risk_categories`: self-harm, abuse, panic, psychosis, medication, physical_urgent, other
  - `escalation_required`: boolean
  - `review_required`: boolean
- Add initial evaluation cases for safety behavior.

Suggested files:

- `services/gateway-service/src/services/prompt_service.py`
- `services/ai-service/src/services/openai_service.py`
- `services/gateway-service/src/services/chat_service.py`
- `tests/evaluation/mental_health_safety_cases.jsonl`

Local model requirement:

- Run the same safety cases against the local model before using it as the default assistant model.
- Keep temperature and max-token defaults conservative for safety-critical mental health support.
- Record failed cases by model/version so the team can compare Gemma or other candidates objectively.

## Phase 1.5: Local LLM Runtime

Goal: make Empat.IA run on a self-hosted model as the default model path.

Actions:

- Add a provider abstraction in the AI service:
  - `local`
  - `openai_compatible`
  - `fallback`
- Support a configurable local base URL and model name.
- Keep chat-completions-style request/response contracts where possible.
- Add a `/openai/status` or equivalent status response that reports:
  - active provider
  - model name
  - model version when available
  - base URL host only, not secrets
  - timeout settings
  - fallback provider
- Add local model health checks to gateway/system status.
- Add documentation for serving Gemma or another local model in development.

Suggested files:

- `services/ai-service/src/services/openai_service.py`
- `services/ai-service/src/api/openai_routes.py`
- `services/ai-service/README.md`
- `.env.example`
- `docker-compose.dev.yml`
- `docs/TECHNICAL.md`

## Phase 2: Session Continuity For Mental Health

Goal: improve the existing session engine so each session feels clinically organized without pretending to be clinical care.

Actions:

- Extend session context with:
  - presenting concerns
  - emotional themes
  - coping strategies discussed
  - user goals
  - protective factors
  - risk indicators
  - suggested follow-up focus
- Improve next-session generation so it uses:
  - user profile
  - previous session context
  - emotional trend
  - safety metadata
- Add admin visibility for risk indicators and follow-up focus.

Suggested files:

- `services/ai-service/src/services/session_context_service.py`
- `services/ai-service/src/services/openai_service.py`
- `services/gateway-service/src/api/admin.py`
- `apps/admin-panel/src/pages/Conversations.js`
- `apps/admin-panel/src/pages/Analytics.js`

## Phase 3: LLMOps Evaluation

Goal: stop relying only on manual prompt intuition and make local model selection measurable.

Actions:

- Create a regression dataset for mental health conversations.
- Add prompt/version metadata to AI responses.
- Track provider, model name, model version, quantization, serving backend, prompt key, prompt version, latency, token usage or token estimate, and fallback usage.
- Add evaluation rubrics:
  - empathy
  - safety
  - non-diagnosis
  - escalation correctness
  - Portuguese clarity
  - grounding when knowledge is used
- Create a local evaluation runner.
- Compare local model candidates before promotion.
- Save evaluation results by model and prompt version.

Suggested files:

- `tests/evaluation/`
- `scripts/`
- `services/ai-service/src/services/openai_service.py`
- `services/gateway-service/src/services/chat_service.py`

Local model promotion rule:

- A local model can become the default only after it passes the mental health safety dataset and basic response-quality rubrics.
- If a local model fails crisis or medication cases, it must stay behind a development flag.

## Phase 4: Knowledge And RAG

Goal: add approved mental health educational content without turning the assistant into an unchecked medical source.

Actions:

- Create an approved document ingestion path.
- Store source metadata:
  - source name
  - review owner
  - reviewed date
  - expiration date
  - jurisdiction/language
- Use retrieval only for psychoeducation and support content.
- Require the assistant to distinguish between:
  - supportive reflection
  - general psychoeducation
  - professional-care recommendation
  - crisis escalation

Suggested architecture:

- Keep the gateway as API boundary.
- Add retrieval under AI service or a dedicated knowledge service.
- Later expose knowledge resources through MCP.
- Keep retrieval model-agnostic so local LLMs and future model candidates can use the same approved knowledge layer.

## Phase 5: Voice Conversation

Goal: make voice mode emotionally useful and safe.

Actions:

- Implement voice input using the existing voice roadmap.
- Keep voice responses shorter and calmer than text responses.
- Add privacy language for microphone use.
- Detect silence, distress language, and interruption.
- Ensure crisis responses are clear in both text and audio.

Reference:

- `docs/todos/TODOVOICECONVERSATION.md`

## Phase 6: Agent Platform And MCP

Goal: expose Empat.IA capabilities as safe tools/resources.

Potential agent profiles:

- `mental_health_support_assistant`: main user conversation.
- `safety_reviewer`: classifies risk and escalation needs.
- `session_summarizer`: creates continuity summaries.
- `clinician_handoff_writer`: prepares human-readable summaries.
- `english_learning_coach`: helps the user practice English while building the project.

Potential tools:

- `send_support_message`
- `classify_mental_health_risk`
- `generate_session_context`
- `generate_next_session`
- `summarize_for_review`
- `analyze_facial_emotion`
- `synthesize_speech`

Potential resources:

- `prompt://{key}`
- `context://{session_id}`
- `sessions://{username}`
- `emotions://{username}`
- `profile://{username}`

Reference:

- `docs/MCP_MIGRATION_PLAN.md`
- Book chapters on agent profiles, actions/tools, memory, evaluation, planning, and feedback.

## Learning Plan

Use the book and the project together.

| Topic | Book concept | Empat.IA practice |
|---|---|---|
| Agents | Profiles/personas | Refine the mental health support assistant identity. |
| Tools | Agent actions | Convert gateway capabilities into safe tools. |
| Memory | RAG and session memory | Improve session contexts and approved knowledge retrieval. |
| Evaluation | Rubrics and grounding | Build safety and quality evaluation datasets. |
| Planning | Feedback loops | Use admin review and evaluations to improve prompts. |
| Local LLMs | Self-hosted model serving | Serve Gemma or another local model through the AI service. |
| LLMOps | Prompt/model tracking | Track prompt versions, local model usage, latency, evaluation score, and fallback rate. |
| MLOps | Emotion model monitoring | Track confidence, no-face rate, and model limitations. |

## First Concrete Implementation Slice

Start small:
So
1. Update prompt identity and boundaries.
2. Add mental health safety evaluation cases.
3. Add local model configuration to the AI service.
4. Run the safety cases against the selected local model.
5. Add risk metadata shape to the AI response path.
6. Store risk metadata with messages.
7. Show high-risk conversations in the admin panel.

This first slice improves product safety, creates an LLMOps foundation, and keeps the work aligned with the current app architecture.
