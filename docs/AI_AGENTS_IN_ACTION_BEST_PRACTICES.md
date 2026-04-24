# Empat.IA And AI Agents In Action: Best Practices

This document maps the best practices Empat.IA already follows against the ideas from `docs/learning/_OceanofPDF.com_AI_Agents_in_Action_-_Micheal_Lanham (1).pdf`, then lists the next steps to move the application closer to the book's agent engineering practices.

Small English note: a clearer version of "best practices that iǘe followed" is "best practices I have followed" or "best practices the application already follows."

## How The Book Maps To Empat.IA

The book presents agents as systems composed of:

- Profile/persona.
- Actions/tools.
- Knowledge and memory.
- Reasoning and evaluation.
- Planning and feedback.

Empat.IA already contains the foundation for these components. The app should not jump directly into broad autonomy. For a mental-health-focused Medical AI Assistant, the safer path is a bounded assistant architecture: clear persona, explicit tools, persistent memory, systematic evaluation, and human review loops.

## Best Practices Already Present

### 1. Clear Agent Persona

Book concept: agent profiles and personas guide behavior, tone, and task scope.

Empat.IA already follows this through:

- `system_rogers` as the main assistant persona.
- Person-centered, empathetic response style inspired by Carl Rogers.
- Portuguese-first conversational behavior.
- Prompt management through the admin panel instead of hardcoding everything permanently.

Why this is strong:

- The assistant is not just a generic chatbot.
- It has a defined interaction style and domain focus.
- Prompt behavior can evolve without redeploying every change.

Next improvement:

- Evolve `system_rogers` into a mental-health Medical AI Assistant prompt with explicit safety boundaries, escalation behavior, and non-diagnosis rules.

### 2. Session-Based Memory

Book concept: agents need memory and knowledge to maintain continuity and reduce repeated context.

Empat.IA already follows this through:

- `messages` for conversation history.
- `conversations` for session metadata.
- `session_contexts` for structured summaries.
- `user_therapeutic_sessions` for progressive session state.
- `users.user_profile` for onboarding information.
- Previous session context passed into the AI service.

Why this is strong:

- The assistant can continue a user's journey instead of treating every message as isolated.
- The app already has episodic memory through sessions.
- Session summaries reduce token usage and improve continuity.

Next improvement:

- Add a more structured mental health continuity schema: presenting concern, emotional themes, coping strategies, goals, protective factors, risk indicators, and follow-up focus.

### 3. Tool-Oriented Architecture

Book concept: agents become more useful when they can call tools/actions instead of only generating text.

Empat.IA already follows this through its microservices:

- Gateway as the main orchestration boundary.
- AI service for LLM responses and session generation.
- Emotion service for facial emotion analysis.
- Voice service for text-to-speech.
- Avatar service for DID.ai integration.
- Admin endpoints for prompts, users, sessions, analytics, and conversations.

Why this is strong:

- The app's capabilities are already separated into tool-like services.
- The MCP migration plan correctly treats existing endpoints as future tools/resources.
- The architecture can expose agent actions without rewriting the whole system.

Next improvement:

- Standardize tool contracts around mental health safety, especially for chat, risk classification, session summarization, emotion analysis, and clinician handoff.

### 4. AI Interface Direction

Book concept: applications increasingly expose data and behavior through AI interfaces that agents can use.

Empat.IA already follows this through:

- `docs/MCP_MIGRATION_PLAN.md`.
- Proposed tools like `send_therapeutic_message`, `generate_session_context`, `generate_next_session`, and `analyze_facial_emotion`.
- Proposed resources like `prompt://{key}`, `context://{session_id}`, `sessions://{username}`, and `profile://{username}`.

Why this is strong:

- MCP is a natural fit because Empat.IA already has context, tools, and structured resources.
- The plan preserves existing services instead of rewriting them.
- The gateway remains the control point for auth, privacy, and validation.

Next improvement:

- Rename future tools from generic therapy language to mental-health-support language where appropriate, for example `send_support_message` and `classify_mental_health_risk`.

### 5. Prompt Management

Book concept: prompting should become systematic, testable, and profile-aware.

Empat.IA already follows this through:

- Database-backed prompts.
- Prompt initialization on gateway startup.
- Admin prompt CRUD.
- Prompt types such as system, fallback, session generation, and analysis.
- Rendered prompts with variables.

Why this is strong:

- Prompts are operational assets, not random strings hidden in code.
- Admin users can inspect and update behavior.
- The system is ready for prompt versioning and evaluation.

Next improvement:

- Add prompt evaluation status, prompt version metadata in AI responses, and regression tests for safety-critical behavior.

### 6. Context Optimization

Book concept: agents need memory compression and context management to avoid token waste.

Empat.IA already follows this through:

- `MAX_HISTORY_MESSAGES`.
- `MAX_CONTEXT_TOKENS`.
- Conversation history limiting.
- Previous session summaries.
- Token economy service.
- Redis performance service.

Why this is strong:

- The app already recognizes that full conversation history is not always the right context.
- Summaries and recent messages are combined in the AI service.
- This is aligned with the book's memory and knowledge compression direction.

Next improvement:

- Make context selection more explicit: separate user profile, current session messages, previous session summary, safety metadata, and approved knowledge retrieval.

### 7. Human Review Surface

Book concept: feedback improves agent systems over time.

Empat.IA already follows this through:

- Admin conversation viewer.
- Prompt management.
- Analytics.
- Session management.
- Emotion analytics.

Why this is strong:

- The app has the beginning of a human feedback loop.
- Therapists/admins can inspect conversations and prompts.
- This can become the review layer for safety, quality, and prompt improvement.

Next improvement:

- Add explicit review states for high-risk sessions: `pending_review`, `reviewed`, `needs_follow_up`, and `escalated`.

## Gaps Compared With The Book

### 1. Evaluation Is Not Systematic Yet

The book emphasizes evaluation, rubrics, grounding, and consistency. Empat.IA has tests for some services, but it does not yet have a strong LLM evaluation suite.

Needed:

- Mental health safety test cases.
- Prompt regression tests.
- Response quality rubrics.
- Grounding checks for future RAG.
- Evaluation reports saved per prompt version.

### 2. Safety Is Mostly Prompt-Based

The assistant currently has broad prompt guidance like "do not offer medical diagnoses or prescriptions", but a medical mental health assistant needs stronger runtime safety.

Needed:

- Risk classifier.
- Safety metadata stored with messages.
- Crisis escalation response templates.
- Admin review queue.
- Tests for suicide, self-harm, abuse, panic, psychosis, medication, and urgent physical symptoms.

### 3. Tool Boundaries Need Safety Contracts

The app has tool-like services, but future agent tools need explicit input/output contracts and safety rules.

Needed:

- Tool schemas.
- Auth and session ownership validation.
- Per-tool safety notes.
- Tool outputs designed for agent consumption.
- No direct access to raw sensitive data unless needed.

### 4. RAG Is Not Implemented Yet

The book's memory and knowledge chapters point toward RAG and semantic memory. Empat.IA has session memory, but not approved external knowledge retrieval.

Needed:

- Approved mental health document library.
- Embeddings and vector search.
- Source metadata.
- Review/expiration metadata.
- Grounding evaluation.

### 5. Planning And Feedback Are Not Formalized

Empat.IA generates next sessions, but planning is not yet a formal, inspectable workflow.

Needed:

- Structured plan objects for next-session reasoning.
- Human review for suggested care paths.
- Feedback from admin review into prompt improvements.
- Evaluation-triggered prompt rollback or review.

## Recommended Next Steps

### Step 1: Add A Mental Health Safety Layer

Implement a lightweight risk metadata shape:

```json
{
  "risk_level": "low | medium | high | crisis",
  "risk_categories": ["self_harm", "panic", "abuse"],
  "escalation_required": true,
  "review_required": true,
  "reason": "Short explanation for audit/review"
}
```

Store this metadata with AI messages. This creates the base for safety, admin review, and LLMOps evaluation.

### Step 2: Create An Evaluation Dataset

Add `tests/evaluation/mental_health_safety_cases.jsonl`.

Each case should include:

- user message
- expected risk level
- expected escalation behavior
- forbidden behavior
- rubric notes

Start with 20 cases:

- suicidal ideation
- self-harm ambiguity
- panic attack
- medication dosage
- abuse disclosure
- psychosis-like experience
- severe sadness
- general anxiety
- normal emotional support
- urgent physical symptom

### Step 3: Improve The Main System Prompt

Update `system_rogers` so it becomes a mental-health-focused Medical AI Assistant prompt.

It should include:

- Role.
- Scope.
- Safety boundaries.
- Crisis behavior.
- Medication/diagnosis refusal style.
- Professional-care encouragement.
- Tone and language rules.
- Voice-mode response style.

### Step 4: Add Prompt Version Tracking

Every AI response should record:

- model
- provider
- prompt key
- prompt version
- latency
- fallback used
- safety metadata

This is one of the most important LLMOps upgrades for the project.

### Step 5: Add Admin Review Workflow

Extend the admin panel to show:

- conversations requiring review
- risk level
- risk categories
- last message
- escalation status
- review status

This turns the admin panel into a real feedback loop.

### Step 6: Start Approved Knowledge/RAG

Only after safety and evaluation are in place, add approved mental health knowledge retrieval.

Start small:

- one document collection
- source metadata
- embeddings
- retrieval endpoint
- grounding rubric

### Step 7: Convert Capabilities Into MCP Tools

After safety contracts exist, implement the MCP server from `docs/MCP_MIGRATION_PLAN.md`.

Prioritize:

- `classify_mental_health_risk`
- `generate_session_context`
- `summarize_for_review`
- `send_support_message`
- `synthesize_speech`

## Priority Order

1. Safety metadata and risk classification.
2. Evaluation dataset and local runner.
3. Safer `system_rogers` prompt.
4. Prompt/model observability.
5. Admin review queue.
6. Structured session continuity schema.
7. Approved knowledge/RAG.
8. MCP tools/resources.
9. More advanced multi-agent workflows.

## What To Avoid For Now

- Do not build a fully autonomous medical agent.
- Do not let an agent independently decide care plans without review.
- Do not add broad medical RAG before safety evaluation exists.
- Do not treat emotion detection as clinical diagnosis.
- Do not add multiple agents until the single assistant is safe, observable, and testable.

## Summary

Empat.IA already follows several strong practices from *AI Agents in Action*: clear persona, tool-like services, memory, prompt management, context compression, and an MCP direction. The next maturity step is not more autonomy. The next step is disciplined agent engineering: safety contracts, evaluation, observability, review loops, and approved knowledge.

