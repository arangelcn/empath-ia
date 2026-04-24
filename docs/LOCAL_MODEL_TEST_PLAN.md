# Local Model Test Plan

This plan is based on the current notebook hardware detected locally:

| Component | Detected config |
|---|---|
| GPU | NVIDIA GeForce RTX 3050 Laptop GPU |
| VRAM | 6GB |
| Driver | 570.211.01 |
| CPU | Intel Core i5-12450HX, 12 threads |
| RAM | 15GiB |
| Storage | 476.9GB NVMe |
| Ollama | Not installed |

## Recommendation

Start tests with **Gemma 3 4B Instruct**, preferably a quantized/QAT variant when available in the serving backend.

Why:

- The RTX 3050 Laptop has 6GB VRAM, which is a better fit for 3B-4B local models.
- 12B models are possible only as slow experiments with heavy quantization and CPU/RAM offload.
- Mental health support needs more nuance than 1B-class models, so 1B should be used only for smoke tests.
- Gemma 3 has official small sizes and long-context variants, making it a good first family for Empat.IA.

## Model Ladder

| Priority | Model | Role | Why |
|---|---|---|---|
| 1 | `gemma3:4b` or `gemma3:4b-it-qat` | Main first assistant test | Best balance for 6GB VRAM. |
| 2 | `qwen3:4b` | Comparator model | Useful to compare reasoning, Portuguese, and instruction following. |
| 3 | `smollm3:3b` or Hugging Face `HuggingFaceTB/SmolLM3-3B` | Fast baseline | Lightweight enough for quick iteration. |
| 4 | `gemma3:1b` | Smoke test only | Good for checking integration, not final assistant quality. |
| 5 | `gemma3:12b` | Stretch experiment | Try only after 4B tests pass; expect slower generation. |

## First Test Path

Use this order:

1. Install Ollama or another local OpenAI-compatible model server.
2. Run a tiny smoke test model to verify local serving.
3. Run Gemma 3 4B as the first serious assistant candidate.
4. Run Qwen3 4B as a comparator.
5. Run the mental health safety dataset against both.
6. Promote the best model only after evaluation.

Suggested Ollama commands:

```bash
ollama pull gemma3:4b
ollama run gemma3:4b
```

If the QAT tag is available in your Ollama install:

```bash
ollama pull gemma3:4b-it-qat
ollama run gemma3:4b-it-qat
```

Comparator:

```bash
ollama pull qwen3:4b
ollama run qwen3:4b
```

## Empat.IA Configuration Target

```env
LLM_PROVIDER=local
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=gemma3:4b
LOCAL_LLM_TIMEOUT_SECONDS=60
LLM_FALLBACK_PROVIDER=none
TEMPERATURE=0.3
MAX_TOKENS=700
MAX_HISTORY_MESSAGES=6
```

For voice mode, consider shorter responses:

```env
VOICE_MODE_MAX_TOKENS=350
VOICE_MODE_TEMPERATURE=0.25
```

## Evaluation Criteria

Do not choose the model only by speed. For Empat.IA, the first useful model must pass:

- Empathy in Brazilian Portuguese.
- Non-diagnosis behavior.
- Medication refusal behavior.
- Crisis escalation behavior.
- Stable tone in sadness, anxiety, panic, anger, and grief.
- Ability to use session context without inventing facts.
- Short, clear responses for voice mode.

## Practical Expectations

With 6GB VRAM:

- 4B quantized models should be the daily development target.
- 7B/8B models may run, but they can be slower or force CPU offload.
- 12B models are quality experiments, not the default dev loop.
- 27B models are not realistic on this notebook for interactive Empat.IA use.

## Promotion Rule

A model can become the default only when it:

1. Runs locally with acceptable latency.
2. Passes the mental health safety test dataset.
3. Produces acceptable Portuguese responses.
4. Handles crisis cases safely.
5. Does not hallucinate diagnoses or medication instructions.
6. Preserves the Empat.IA support identity.

## Suggested First Winner

Start with:

```env
LOCAL_LLM_MODEL=gemma3:4b
```

Then compare against:

```env
LOCAL_LLM_MODEL=qwen3:4b
```

If Gemma 3 4B is more empathetic and safer, keep it as the first local default. If Qwen3 4B follows instructions better in Portuguese and safety cases, use Qwen3 4B as the first default and keep Gemma as the baseline.

