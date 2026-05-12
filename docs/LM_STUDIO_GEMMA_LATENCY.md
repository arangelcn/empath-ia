# LM Studio + Gemma: Latency Diagnosis

Date: 2026-05-08

## Summary

The main bottleneck is not Docker or `gateway-service`.
`LM Studio` is using GPU correctly, but `gemma-4-e4b` became slow when it received the full therapeutic prompt from `ai-service`, including user context, message history, and long instructions.

In short:

- direct short request to LM Studio: fast
- real app request: slow
- root cause: `large prompt + rich context + long output`

## What was validated

### 1. LM Studio GPU usage is active

With `nvidia-smi`, LM Studio process was visible on GPU:

- GPU: `NVIDIA GeForce RTX 3050 6GB Laptop GPU`
- VRAM used by LM Studio: around `3.3 GB`
- Observed utilization: around `55%`

Conclusion: this was not a silent CPU fallback.

### 2. Models exposed by LM Studio

`GET http://127.0.0.1:1234/v1/models`

Visible models:

- `google/gemma-4-e4b`
- `deepseek/deepseek-r1-0528-qwen3-8b`
- `text-embedding-nomic-embed-text-v1.5`

### 3. `ai-service` target configuration was correct

`GET http://127.0.0.1:8001/openai/status`

Relevant configuration:

- `provider`: `openai`
- `active_provider`: `openai`
- `model`: `gemma-4-e4b`
- `openai_base_url`: `http://127.0.0.1:1234/v1`

Note:

- provider is still called `openai` because the app uses LM Studio through an OpenAI-compatible API
- this does not mean requests are going to OpenAI cloud

## Measurements

### Direct short request to LM Studio

Simple prompt, no heavy therapeutic context:

- non-stream: around `1.37s`
- first stream chunk: around `0.86s`

This confirmed local server and GPU were healthy.

### Request through `ai-service`

Simple app-level endpoint tests:

- `POST /openai/chat`: around `48.3s`
- `POST /openai/chat/stream`: first visible text around `38.3s`

### Direct reproduction with large prompt

Sending an app-like prompt directly to LM Studio:

- input size: around `1059 prompt_tokens`
- stream first visible text: around `38.3s`

Conclusion:

- slow behavior comes from payload size/complexity sent to Gemma
- same behavior reproduced without `gateway-service` and without Docker in path

## Root cause

`ai-service` was building prompts that are too heavy for this local model size:

- long system prompt
- large user-profile block
- previous-session context
- recent conversation history
- allowed outputs with `MAX_TOKENS=700`

In logs, even a simple test without history reached:

- `~1019 tokens` before output

For small/medium local models, this significantly increased prefill and total generation time.

## Secondary issues observed

### 1. Session context generation exceeded context window

In `generate-session-context`, the error was:

- `Context size has been exceeded`

This indicates analysis/session-summary prompts can also exceed local model limits.

### 2. Gemma streaming is payload-sensitive

With small prompts, stream behaved well.
With large prompts, time-to-first-token increased dramatically.

## Applied optimizations

A compact automatic profile was implemented for local OpenAI-compatible runtime in `ai-service`.

### Changes made

Main file:

- `services/ai-service/src/services/llm_service.py`

New compact prompt:

- `services/ai-service/src/prompts/system_rogers_local.txt`

Behavior changes:

- when endpoint is local (`localhost`, `127.0.0.1`, `host.docker.internal`), app uses a shorter system prompt
- default local `MAX_TOKENS` reduced from `700` to `220`
- default local `VOICE_MAX_TOKENS` reduced from `180` to `120`
- default local `MAX_HISTORY_MESSAGES` reduced from `6` to `4`
- context blocks now have compact versions for local runtime

Goal:

- reduce time to first token
- reduce overly long replies
- keep production behavior intact and env-configurable

## Recommended next steps

### High priority

1. Re-test latency after compact local prompt
2. Measure again:
   - `POST /openai/chat` total time
   - first `text_delta` timing in `POST /openai/chat/stream`
3. If still slow, reduce further:
   - `MAX_TOKENS=160`
   - `MAX_HISTORY_MESSAGES=2`

### Medium priority

1. Add explicit `fast-local` mode via env
2. Compact prompts for:
   - `session_context_analysis`
   - next-session generation
3. Limit `previous_session_context` size before sending to local model

### Optional

1. Test a faster model for regular chat
2. Keep Gemma for general chat and use another model for analysis tasks
3. Persist metrics for:
   - `prompt_tokens`
   - `completion_tokens`
   - `first_text_delta_ms`
   - `gateway_total_ms`

## LM Studio config recommendation

For this laptop (RTX 3050 6 GB):

- `GPU`: `ON`
- `Limit Model Offload to Dedicated GPU Memory`: `ON`
- `Offload KV Cache to GPU Memory`: `ON` initially

If memory errors or degraded behavior appear with large context:

- first test: turn off only `Offload KV Cache to GPU Memory`

## Final conclusion

Most important finding from this investigation:

> local Gemma was not slow by itself; it became slow with the large therapeutic prompt assembled by the application.

This gives a clear path:

- keep LM Studio + GPU
- simplify prompt/context for local runtime
- keep responses shorter
- reserve richer prompts for endpoints/models with more headroom
