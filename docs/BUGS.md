# BUGS - Web UI, Gateway, and AI Service Triage

Analysis date: 2026-05-05

## Executive Summary

Logs show a chain of connected failures across frontend, gateway, AI Service, and Voice Service. The most critical issue was session finalization: Gateway calls AI Service to generate session context, AI Service returns 500, finalization aborts, and the next session starts without reliable previous context.

In parallel, voice mode was degraded: streaming TTS failed, batch fallback also failed to produce audio, and this repeated per chunk, adding latency and leaving a text-only experience. There were also smaller contract mismatches: missing `voice_short_response` prompt in prompt DB, legacy calls to `/api/sessions/session-4`, and title parsing that did not support JSON inside `text.content`.

## Current Status

- P0 session context: mitigated in code, with robust JSON parsing in AI Service and context recovery in Gateway.
- P1 `voice_short_response` prompt: fixed in Gateway bootstrap.
- P2 title parser: fixed to support `text.content`.
- P2 global session route in web-ui: mitigated with fallback to `/api/user/{username}/sessions/{sessionId}`.
- P1 TTS/streaming: still the primary open focus.

## Observed Flow

1. Session 3 finishes and tries to generate context.
2. Gateway saves or finds context but logs `Error estimating duration: unsupported operand type(s) for -: 'str' and 'str'`.
3. Session 4 is created automatically.
4. When session 4 starts, Gateway reads session 3 context, finds a document, but rejects it due to `generation_method=fallback`.
5. Web UI opens session 4, loads history, generates initial message, and sends user messages.
6. Gateway sends `previous_session_context: null` to AI Service.
7. Voice mode calls `/openai/chat/stream`, but TTS fails repeatedly.
8. When finalizing session 4, AI Service returns 500 at `/openai/generate-session-context`, and Gateway returns 500 to `/api/chat/finalize/{chat_id}`.

## P0 - Session finalization fails with 500

Status: mitigated.

Log evidence:

```text
POST http://127.0.0.1:8001/openai/generate-session-context "HTTP/1.1 500 Internal Server Error"
SessionContextService returned 500: {"detail":"Failed to generate session context"}
Finalization aborted ... Failed to generate context
POST /api/chat/finalize/chat_... HTTP/1.1" 500 Internal Server Error
```

Code references:

- `services/gateway-service/src/services/session_context_service.py:516` calls `POST {ai_service_url}/openai/generate-session-context`
- `services/ai-service/src/api/chat_routes.py:341` exposes `/generate-session-context`
- `services/ai-service/src/services/token_economy_service.py:120` calls `LLMService.generate_session_context`
- `services/ai-service/src/services/llm_service.py:1427` performs direct `json.loads(result)`

Likely cause:

AI Service required strict JSON. Another symptom already existed in logs where local model returned markdown-wrapped JSON:

````text
```json
{
  "title": ...
}
```
````

If that same shape appears in session context generation, `json.loads(result)` fails and route returns 500. Unlike other paths, this route did not attempt to extract the first `{...}` block or strip markdown fences.

Impact:

- Session cannot finalize.
- Next session has no reliable context.
- Therapeutic continuity is lost.
- Frontend gets generic finalization failure.

Recommended fix:

1. In AI Service, replace strict parse with tolerant parse handling raw JSON, `content` payloads, fenced markdown JSON, and embedded JSON.
2. Keep structural validation after parsing.
3. Log the beginning of raw LLM output when parsing fails, without exposing sensitive content.
4. Add AI Service test covering `generate_session_context` with ` ```json ... ``` ` output.

## P0 - Previous context rejected and not sent to AI Service

Status: mitigated.

Log evidence:

```text
Context found in session_contexts collection: toni.rc.neto@gmail.com_session-3
Saved context rejected ... Rejected due to generation_method=fallback
previous_session_context: ❌
DEBUG - previous_session_context is EMPTY/NULL being sent to AI Service!
```

Code references:

- `services/gateway-service/src/services/session_context_service.py:16` defines `INVALID_CONTEXT_GENERATION_METHODS`
- `services/gateway-service/src/services/session_context_service.py:371` validates saved context
- `services/gateway-service/src/services/chat_service.py:757` fetches previous context
- `services/gateway-service/src/services/chat_service.py:770` sends `previous_session_context` to AI Service

Likely cause:

Validation was tightened to reject generic/fallback contexts, which is correct for quality. But this exposed that session 3 had fallback context saved. Since fallback context is now rejected, session 4 proceeds without previous context.

There was also a secondary bug in duration calculation:

```text
unsupported operand type(s) for -: 'str' and 'str'
```

In `services/gateway-service/src/services/session_context_service.py:654`, `created_at` may be a string; code subtracts as if it were `datetime`.

Impact:

- Session chain loses previous-session memory.
- Session 4 initial message and responses become less personalized.
- Logs include noisy errors during expected flow.

Recommended fix:

1. Fix `_estimate_conversation_duration` to accept `datetime`, ISO strings, and missing timestamps.
2. Define explicit strategy for legacy fallback context:
   - migrate/delete `generation_method=fallback` contexts, or
   - keep rejection but regenerate context when fallback is found, or
   - allow fallback only for historical UI and never for AI prompts.
3. During finalization, avoid saving fallback context as valid therapeutic context.
4. Add tests for `generation_method=fallback` and string timestamps.

## P1 - TTS fails in streaming and batch fallback

Status: open.

Log evidence:

```text
Streaming TTS failure:
Generating audio for VoiceMode - Optimized timeout: 15.0s
Audio generation failed (VoiceMode):
Streaming TTS failed and per-chunk batch fallback produced no audio
```

Code references:

- `services/gateway-service/src/services/voice_synthesis_service.py:80` calls `/api/v1/synthesize-stream`
- `services/gateway-service/src/services/voice_synthesis_service.py:25` calls `/api/v1/synthesize`
- `services/gateway-service/src/services/chat_service.py:665` does per-chunk fallback
- `apps/web-ui/src/components/Chat/VoiceConversationMode.jsx:178` uses `sendMessageStream`

Likely cause:

Gateway was not receiving valid audio from Voice Service. Exception log was empty, so the issue may be timeout, aborted connection, missing `audio_url`, silent voice-service failure, or reload interruption. Because fallback was per chunk, the same failure repeated and consumed time.

Impact:

- Voice mode receives text but no playable audio.
- Voice conversations stall or contain long pauses.
- System performs many consecutive fallback attempts.

Recommended fix:

1. Improve `VoiceSynthesisService` logs with `type(exc).__name__`, request URL, HTTP status, and a short response body snippet.
2. Validate Voice Service health/config and expected routes: `/api/v1/synthesize-stream` and `/api/v1/synthesize`.
3. If streaming TTS fails once in a response, disable streaming for remaining chunks of that response and try one final batch synthesis for full text.
4. Consider `voice_enabled=False` outside VoiceMode, or generate audio only when UI explicitly requests it.
5. Add metrics: `tts_stream_failed`, `tts_batch_failed`, `voice_service_status`, `audio_chunks`.

## P1 - Missing `voice_short_response` prompt in Gateway

Status: fixed.

Log evidence:

```text
Active prompt not found: voice_short_response
GET /api/prompts/active/voice_short_response HTTP/1.1" 404 Not Found
```

Code references:

- `services/ai-service/src/services/llm_service.py:736` requests prompt from Gateway
- `services/ai-service/src/prompts/voice_short_response.txt` exists as local fallback
- `services/gateway-service/src/main.py:93` only initializes defaults when `system_rogers` is missing
- `services/gateway-service/src/services/prompt_service.py:352` creates defaults, but previous list did not include `voice_short_response`

Likely cause:

File existed in AI Service, but prompt DB in Gateway had no active version. Since `auto_initialize_prompts` stops when `system_rogers` exists, newly introduced prompts were not inserted automatically.

Impact:

- Does not break responses due to local fallback.
- Produces 404 and warnings for every voice response.
- Prevents voice prompt tuning via admin/DB.

Recommended fix:

1. Add `voice_short_response` to Gateway default prompts.
2. Change `auto_initialize_prompts` to upsert missing prompts, not all-or-nothing based on `system_rogers`.
3. Create script/migration to insert new prompts in existing databases.

## P2 - web-ui calls global route for dynamic session and gets 404

Status: mitigated.

Log evidence:

```text
GET /api/sessions/session-4 HTTP/1.1" 404 Not Found
GET /api/user/toni.rc.neto%40gmail.com/sessions/session-4 HTTP/1.1" 200 OK
```

Code references:

- `apps/web-ui/src/services/api.js:419` still exposes `getTherapeuticSession(sessionId)` via `/sessions/{sessionId}`
- `apps/web-ui/src/services/api.js:465` exposes correct user-session route
- `apps/web-ui/src/components/Chat/ChatScreen.tsx:221` already notes dynamic sessions are not in global catalog
- `services/gateway-service/src/api/sessions.py:33` only serves global therapeutic catalog

Likely cause:

An old bundle, parallel flow, or leftover call path still used `/api/sessions/{sessionId}` for `session-4`. That route only serves global session catalog. Dynamic user sessions are in `/api/user/{username}/sessions/{sessionId}`.

Impact:

- Benign but noisy 404.
- Can trigger false "session unavailable" UI state if old call wins race.
- Makes diagnosis harder because correct route returns 200 right after.

Recommended fix:

1. Remove `getTherapeuticSession` usage for user `session-N` flows.
2. Audit bundle/deploy to ensure served web-ui uses `getUserSession` path.
3. If global route stays needed, rename in frontend to `getCatalogTherapeuticSession` to avoid misuse.

## P2 - Title parser did not support `text.content`

Status: fixed.

Log evidence:

```text
Could not extract JSON from generated title ... {'success': True, 'text': {'content': '```json ... ```', 'provider': 'local', 'model': 'gemma4:e4b'}}
```

Code references:

- `services/gateway-service/src/services/chat_title_service.py:82` parsed `text`, `data`, `result`
- `services/gateway-service/src/services/chat_title_service.py:94` traversed nested keys but did not include `content`

Likely cause:

AI Service returned `text` as object containing `content`. Parser accepted dicts with `title/subtitle` or keys `text/data/result/response`, but ignored `content`, where markdown JSON lived.

Impact:

- Dynamic title/subtitle was not persisted.
- Conversation continued, but metadata quality dropped.

Recommended fix:

1. Include `content` in accepted nested parse keys.
2. Add test with payload format:

````json
{
  "success": true,
  "text": {
    "content": "```json\n{\"title\":\"...\",\"subtitle\":\"...\"}\n```"
  }
}
````

## P2 - Dev reload interrupts long-running flows

Log evidence:

```text
StatReload detected changes ... Reloading
Waiting for connections to close
Audio generation failed:
```

Likely cause:

During investigation, multiple file saves triggered Uvicorn reload while long TTS/context requests were still running.

Impact:

- Can amplify audio/finalization failures.
- Can create false symptoms in local dev.

Recommended fix:

1. For voice/finalization bug reproduction, run without `--reload` or avoid saving files during test.
2. Exclude `tests/` and docs from watcher in dev where possible.

## Suggested Execution Order

1. Fix robust context parsing in AI Service.
2. Fix fallback-context strategy in Gateway.
3. Fix `_estimate_conversation_duration` for string timestamps.
4. Add TTS instrumentation in Voice Service/Gateway to identify timeout, route, or invalid-response root cause.
5. Insert/upsert `voice_short_response` in Gateway.
6. Remove old frontend `/api/sessions/{sessionId}` usage.
7. Update title parser for `text.content`.

## Recommended Tests

- AI Service: `generate_session_context` accepts raw JSON and fenced JSON.
- Gateway: `_estimate_conversation_duration` accepts `datetime`, ISO string, and missing timestamp.
- Gateway: saved context with `generation_method=fallback` triggers regeneration or controlled return, without noisy `previous_session_context=None` failure path.
- Gateway: `ChatTitleService` extracts title from `text.content`.
- Web UI: opening dynamic `session-4` calls only `/api/user/{username}/sessions/session-4`.
- Voice: when `/synthesize-stream` fails, Gateway attempts one final batch fallback per response, not per chunk.
