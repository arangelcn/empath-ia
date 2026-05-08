# LM Studio + Gemma: diagnostico de latencia

Data: 2026-05-08

## Resumo

O gargalo principal nao esta no Docker nem no `gateway-service`.
O `LM Studio` esta usando a GPU corretamente, mas o `gemma-4-e4b` ficou lento quando recebeu o prompt terapeutico completo do `ai-service`, com contexto de usuario, historico e instrucao longa.

Em outras palavras:

- chamada direta e curta ao LM Studio: rapida
- chamada real da aplicacao: lenta
- causa principal: `prompt grande + contexto rico + resposta longa`

## O que foi verificado

### 1. GPU do LM Studio esta sendo usada

Com `nvidia-smi`, o processo do LM Studio apareceu usando a GPU:

- GPU: `NVIDIA GeForce RTX 3050 6GB Laptop GPU`
- VRAM em uso pelo LM Studio: cerca de `3.3 GB`
- Utilizacao observada: cerca de `55%`

Conclusao: o problema nao era fallback silencioso para CPU.

### 2. Modelos expostos no LM Studio

`GET http://127.0.0.1:1234/v1/models`

Modelos visiveis:

- `google/gemma-4-e4b`
- `deepseek/deepseek-r1-0528-qwen3-8b`
- `text-embedding-nomic-embed-text-v1.5`

### 3. O `ai-service` estava apontando corretamente

`GET http://127.0.0.1:8001/openai/status`

Configuracao relevante:

- `provider`: `openai`
- `active_provider`: `openai`
- `model`: `gemma-4-e4b`
- `openai_base_url`: `http://127.0.0.1:1234/v1`

Observacao:

- o provider continua sendo `openai` porque o app usa a API OpenAI-compatible do LM Studio
- isso nao significa que esta chamando a OpenAI real

## Medicoes feitas

### Chamada direta curta ao LM Studio

Prompt simples, sem contexto terapeutico pesado:

- non-stream: cerca de `1.37s`
- primeiro chunk no stream: cerca de `0.86s`

Isso mostrou que o servidor local e a GPU estavam saudaveis.

### Chamada via `ai-service`

Teste simples pelo endpoint da aplicacao:

- `POST /openai/chat`: cerca de `48.3s`
- `POST /openai/chat/stream`: primeiro texto visivel em cerca de `38.3s`

### Reproducao direta com prompt grande

Quando enviamos um prompt parecido com o da aplicacao direto para o LM Studio:

- prompt de entrada: cerca de `1059 prompt_tokens`
- stream com primeiro texto visivel: cerca de `38.3s`

Conclusao:

- o comportamento lento vem do tamanho/complexidade do payload enviado ao Gemma
- isso reproduziu mesmo sem `gateway-service` e sem `Docker` no caminho

## Causa principal

O `ai-service` montava um prompt pesado demais para um modelo local desse porte:

- prompt de sistema longo
- bloco grande de perfil do usuario
- contexto anterior da sessao
- historico recente
- respostas permitidas com `MAX_TOKENS=700`

Nos logs, um teste simples sem historico ja chegou perto de:

- `~1019 tokens` antes da resposta

Para um modelo local pequeno/medio, isso aumentou bastante o tempo de prefill e o tempo total de geracao.

## Problemas secundarios observados

### 1. Geracao de contexto da sessao estourando janela

Em `generate-session-context`, houve erro:

- `Context size has been exceeded`

Isso indica que os prompts de analise/resumo de sessao tambem podem ultrapassar o limite do modelo local.

### 2. Streaming do Gemma pode ser sensivel ao payload

Com prompts pequenos, o stream respondeu bem.
Com prompts grandes, o tempo ate o primeiro texto aumentou drasticamente.

## Otimizacoes aplicadas

Foi implementado um perfil automatico mais compacto para runtime local OpenAI-compatible no `ai-service`.

### Ajustes feitos

Arquivo principal:

- `services/ai-service/src/services/llm_service.py`

Novo prompt compacto:

- `services/ai-service/src/prompts/system_rogers_local.txt`

Mudancas:

- quando o endpoint e local (`localhost`, `127.0.0.1`, `host.docker.internal`), o app usa um prompt de sistema mais curto
- `MAX_TOKENS` padrao para local caiu de `700` para `220`
- `VOICE_MAX_TOKENS` padrao para local caiu de `180` para `120`
- `MAX_HISTORY_MESSAGES` padrao para local caiu de `6` para `4`
- blocos de contexto passaram a ter versao compactada para runtime local

Objetivo:

- reduzir o tempo ate o primeiro token
- reduzir respostas longas demais
- preservar a experiencia de prod, que continua configuravel via env

## Recomendacoes para continuar

### Prioridade alta

1. Re-testar a latencia apos o prompt compacto local
2. Medir novamente:
   - tempo do `POST /openai/chat`
   - tempo ate o primeiro `text_delta` no `POST /openai/chat/stream`
3. Se ainda estiver lento, reduzir mais:
   - `MAX_TOKENS=160`
   - `MAX_HISTORY_MESSAGES=2`

### Prioridade media

1. Criar um modo `fast-local` explicito via env
2. Compactar tambem os prompts de:
   - `session_context_analysis`
   - geracao de proxima sessao
3. Limitar o tamanho do `previous_session_context` antes de mandar ao modelo local

### Prioridade opcional

1. Testar um modelo mais rapido para chat normal
2. Deixar `Gemma` para conversa geral e outro modelo para tarefas de analise
3. Adicionar metricas persistidas de:
   - `prompt_tokens`
   - `completion_tokens`
   - `first_text_delta_ms`
   - `gateway_total_ms`

## Configuracao recomendada no LM Studio

Para a RTX 3050 6 GB observada neste notebook:

- `GPU`: `ON`
- `Limit Model Offload to Dedicated GPU Memory`: `ON`
- `Offload KV Cache to GPU Memory`: `ON` inicialmente

Se houver erro de memoria ou degradacao com contexto grande:

- primeiro teste: desligar apenas `Offload KV Cache to GPU Memory`

## Conclusao final

O diagnostico mais importante desta investigacao foi:

> o Gemma local nao estava lento "sozinho"; ele ficou lento com o prompt terapeutico grande que a aplicacao montava.

Isso nos da um caminho claro:

- manter LM Studio + GPU
- simplificar prompt/contexto para ambiente local
- deixar respostas mais curtas
- reservar prompts mais ricos para endpoints/modelos com mais folga
