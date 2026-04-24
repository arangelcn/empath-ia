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

Goal: stop relying only on manual prompt intuition.

Actions:

- Create a regression dataset for mental health conversations.
- Add prompt/version metadata to AI responses.
- Track model, prompt key, prompt version, latency, token usage, provider, and fallback usage.
- Add evaluation rubrics:
  - empathy
  - safety
  - non-diagnosis
  - escalation correctness
  - Portuguese clarity
  - grounding when knowledge is used
- Create a local evaluation runner.

Suggested files:

- `tests/evaluation/`
- `scripts/`
- `services/ai-service/src/services/openai_service.py`
- `services/gateway-service/src/services/chat_service.py`

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
| LLMOps | Prompt/model tracking | Track prompt versions, model usage, latency, and fallback rate. |
| MLOps | Emotion model monitoring | Track confidence, no-face rate, and model limitations. |

## First Concrete Implementation Slice

Start small:

1. Update prompt identity and boundaries.
2. Add mental health safety evaluation cases.
3. Add risk metadata shape to the AI response path.
4. Store risk metadata with messages.
5. Show high-risk conversations in the admin panel.

This first slice improves product safety, creates an LLMOps foundation, and keeps the work aligned with the current app architecture.
