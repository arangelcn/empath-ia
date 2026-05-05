# BUGS - triagem web-ui, gateway e AI Service

Data da analise: 2026-05-05

## Resumo executivo

Os logs mostram uma cadeia de falhas conectadas entre front, gateway, AI Service e Voice Service. O problema mais critico hoje e a finalizacao da sessao: o Gateway chama o AI Service para gerar contexto, o AI Service retorna 500, a finalizacao aborta e a proxima sessao fica sem contexto anterior confiavel.

Em paralelo, o modo de voz esta degradado: o streaming TTS falha, o fallback batch tambem nao gera audio, e isso repete por trecho, adicionando latencia e deixando a experiencia sem voz. Ha ainda divergencias menores de contrato: prompt `voice_short_response` ausente no banco de prompts, chamadas antigas para `/api/sessions/session-4`, e parser de titulo que nao entende JSON dentro de `text.content`.

## Fluxo observado

1. Sessao 3 finaliza e tenta gerar contexto.
2. O Gateway salva ou encontra contexto, mas registra `Erro ao calcular duracao: unsupported operand type(s) for -: 'str' and 'str'`.
3. A sessao 4 e criada automaticamente.
4. Ao iniciar a sessao 4, o Gateway busca o contexto da sessao 3, encontra um documento, mas rejeita por `generation_method=fallback`.
5. A web-ui abre a sessao 4, busca historico, gera mensagem inicial e envia mensagens.
6. O Gateway envia `previous_session_context: null` para o AI Service.
7. O modo de voz chama `/openai/chat/stream`, mas o TTS falha repetidamente.
8. Ao finalizar sessao 4, o AI Service retorna 500 em `/openai/generate-session-context`, e o Gateway devolve 500 para `/api/chat/finalize/{chat_id}`.

## P0 - Finalizacao da sessao falha com 500

Evidencia nos logs:

```text
POST http://127.0.0.1:8001/openai/generate-session-context "HTTP/1.1 500 Internal Server Error"
SessionContextService retornou erro 500: {"detail":"Falha ao gerar contexto da sessão"}
Finalização abortada ... Falha ao gerar contexto
POST /api/chat/finalize/chat_... HTTP/1.1" 500 Internal Server Error
```

Pontos de codigo:

- `services/gateway-service/src/services/session_context_service.py:516` chama `POST {ai_service_url}/openai/generate-session-context`.
- `services/ai-service/src/api/chat_routes.py:341` expõe `/generate-session-context`.
- `services/ai-service/src/services/token_economy_service.py:120` chama `LLMService.generate_session_context`.
- `services/ai-service/src/services/llm_service.py:1427` faz `json.loads(result)` diretamente.

Causa provavel:

O AI Service exige JSON puro. Ja existe outro sintoma no log mostrando o modelo local retornando JSON envolvido em markdown:

````text
```json
{
  "title": ...
}
```
````

Se o mesmo acontecer no contexto de sessao, `json.loads(result)` falha e a rota retorna 500. Diferente de outros pontos do sistema, esse caminho nao tenta extrair o primeiro `{...}` nem remover fences de markdown.

Impacto:

- A sessao nao finaliza.
- A proxima sessao nao recebe contexto confiavel.
- O bot perde continuidade terapeutica.
- O front recebe erro generico e a experiencia parece quebrada no encerramento.

Correcao recomendada:

1. No AI Service, trocar o parse estrito por um parser tolerante para JSON puro, JSON em `content`, markdown fenced e texto com JSON embutido.
2. Manter a validacao estrutural apos o parse.
3. Logar o trecho inicial da resposta bruta do LLM quando o parse falhar, sem expor dados sensiveis demais.
4. Adicionar teste no AI Service cobrindo resposta ` ```json ... ``` ` para `generate_session_context`.

## P0 - Contexto anterior rejeitado e nao enviado ao AI Service

Evidencia nos logs:

```text
Contexto encontrado na coleção session_contexts: toni.rc.neto@gmail.com_session-3
Contexto salvo rejeitado ... Contexto rejeitado por generation_method=fallback
previous_session_context: ❌
DEBUG - previous_session_context está VAZIO/NULO sendo enviado para AI Service!
```

Pontos de codigo:

- `services/gateway-service/src/services/session_context_service.py:16` define `INVALID_CONTEXT_GENERATION_METHODS`.
- `services/gateway-service/src/services/session_context_service.py:371` valida o contexto salvo.
- `services/gateway-service/src/services/chat_service.py:757` busca contexto anterior.
- `services/gateway-service/src/services/chat_service.py:770` envia `previous_session_context` ao AI Service.

Causa provavel:

O sistema endureceu a validacao para rejeitar contextos genericos ou de fallback. Isso e correto para qualidade, mas revela que a sessao 3 ficou com contexto fallback salvo. Como o contexto fallback e rejeitado na leitura, a sessao 4 segue sem contexto anterior.

Ha tambem um bug secundario no calculo de duracao:

```text
unsupported operand type(s) for -: 'str' and 'str'
```

Em `services/gateway-service/src/services/session_context_service.py:654`, `created_at` pode chegar como string; o codigo subtrai como se fossem `datetime`.

Impacto:

- A cadeia de sessoes perde memoria da sessao anterior.
- Mensagem inicial e respostas da sessao 4 ficam menos personalizadas.
- Logs marcam erro em fluxo esperado, aumentando ruido operacional.

Correcao recomendada:

1. Corrigir `_estimate_conversation_duration` para aceitar `datetime`, ISO string e ausencia de timestamp.
2. Criar uma estrategia explicita para contexto fallback antigo:
   - ou migrar/deletar contextos `generation_method=fallback`;
   - ou manter rejeicao, mas gerar novamente o contexto quando encontrar fallback;
   - ou permitir fallback apenas para UI historica, nunca para prompt do AI Service.
3. Na finalizacao, nao salvar contexto fallback como se fosse contexto terapeutico valido.
4. Adicionar teste para contexto salvo com `generation_method=fallback` e para timestamps string.

## P1 - TTS falha no streaming e no fallback batch

Evidencia nos logs:

```text
Falha no streaming TTS:
Gerando áudio para VoiceMode - Timeout otimizado: 15.0s
Falha ao gerar áudio(VoiceMode):
Streaming TTS falhou e fallback batch por trecho não gerou áudio
```

Pontos de codigo:

- `services/gateway-service/src/services/voice_synthesis_service.py:80` chama `/api/v1/synthesize-stream`.
- `services/gateway-service/src/services/voice_synthesis_service.py:25` chama `/api/v1/synthesize`.
- `services/gateway-service/src/services/chat_service.py:665` faz fallback por trecho.
- `apps/web-ui/src/components/Chat/VoiceConversationMode.jsx:178` usa `sendMessageStream`.

Causa provavel:

O Gateway nao esta recebendo audio valido do Voice Service. O log de excecao esta vazio, entao pode ser timeout, conexao abortada, resposta sem `audio_url`, erro silencioso no serviço de voz ou cancelamento causado por reload. Como o fallback batch roda por trecho, a falha se repete muitas vezes e consome tempo.

Impacto:

- Modo voz recebe texto mas nao toca audio.
- A conversa por voz fica travada ou com pausas longas.
- O sistema tenta muitos fallbacks consecutivos.

Correcao recomendada:

1. Melhorar logs em `VoiceSynthesisService`: incluir `type(exc).__name__`, URL chamada, status HTTP e corpo curto da resposta quando houver.
2. Validar health/config do Voice Service e a rota real esperada: `/api/v1/synthesize-stream` e `/api/v1/synthesize`.
3. Se streaming TTS falhar uma vez na resposta, desabilitar streaming para os proximos trechos daquela resposta e tentar um unico batch no texto final.
4. Considerar `voice_enabled=False` fora de VoiceMode, ou gerar audio normal apenas quando a UI pedir explicitamente.
5. Adicionar metricas: `tts_stream_failed`, `tts_batch_failed`, `voice_service_status`, `audio_chunks`.

## P1 - Prompt `voice_short_response` ausente no Gateway

Evidencia nos logs:

```text
Prompt ativo não encontrado: voice_short_response
GET /api/prompts/active/voice_short_response HTTP/1.1" 404 Not Found
```

Pontos de codigo:

- `services/ai-service/src/services/llm_service.py:736` busca o prompt no Gateway.
- `services/ai-service/src/prompts/voice_short_response.txt` existe como fallback local.
- `services/gateway-service/src/main.py:93` so inicializa prompts default se `system_rogers` nao existir.
- `services/gateway-service/src/services/prompt_service.py:352` cria defaults, mas a lista atual nao inclui `voice_short_response`.

Causa provavel:

O arquivo existe no AI Service, mas o banco de prompts do Gateway nao tem uma versao ativa. Como `auto_initialize_prompts` para quando `system_rogers` existe, novos prompts adicionados depois nao sao inseridos automaticamente.

Impacto:

- Nao quebra a resposta, porque ha fallback local.
- Gera 404 e warning em toda resposta de voz.
- Dificulta ajuste do prompt de voz via admin/banco.

Correcao recomendada:

1. Adicionar `voice_short_response` aos prompts padrao do Gateway.
2. Mudar `auto_initialize_prompts` para upsert por prompt faltante, nao "tudo ou nada" baseado em `system_rogers`.
3. Criar script/migracao para inserir prompts novos em bancos ja existentes.

## P2 - web-ui chama rota global de sessao dinamica e recebe 404

Evidencia nos logs:

```text
GET /api/sessions/session-4 HTTP/1.1" 404 Not Found
GET /api/user/toni.rc.neto%40gmail.com/sessions/session-4 HTTP/1.1" 200 OK
```

Pontos de codigo:

- `apps/web-ui/src/services/api.js:419` ainda expõe `getTherapeuticSession(sessionId)` via `/sessions/{sessionId}`.
- `apps/web-ui/src/services/api.js:465` expõe a rota correta de sessao do usuario.
- `apps/web-ui/src/components/Chat/ChatScreen.tsx:221` ja comenta que sessoes dinamicas nao ficam no catalogo global.
- `services/gateway-service/src/api/sessions.py:33` busca apenas o catalogo terapeutico global.

Causa provavel:

Existe bundle antigo, fluxo paralelo ou chamada remanescente usando `/api/sessions/{sessionId}` para `session-4`. Essa rota so serve para catalogo global; sessoes dinamicas criadas para usuario estao em `/api/user/{username}/sessions/{sessionId}`.

Impacto:

- 404 benigno, mas ruidoso.
- Pode acionar estado visual falso de "sessao nao disponivel" se a chamada antiga vencer a corrida.
- Confunde diagnostico porque logo depois a rota correta retorna 200.

Correcao recomendada:

1. Remover uso de `getTherapeuticSession` para sessoes `session-N` do usuario.
2. Auditar bundle/deploy para garantir que a web-ui servida contem a versao que usa `getUserSession`.
3. Se a rota global continuar necessaria, renomear no front para `getCatalogTherapeuticSession` e deixar claro que nao serve para sessoes dinamicas.

## P2 - Parser de titulo nao entende `text.content`

Evidencia nos logs:

```text
Não foi possível extrair JSON do título gerado ... {'success': True, 'text': {'content': '```json ... ```', 'provider': 'local', 'model': 'gemma4:e4b'}}
```

Pontos de codigo:

- `services/gateway-service/src/services/chat_title_service.py:82` tenta parsear `text`, `data`, `result`.
- `services/gateway-service/src/services/chat_title_service.py:94` percorre chaves aninhadas, mas nao inclui `content`.

Causa provavel:

O AI Service retornou `text` como objeto contendo `content`. O parser trata dicts com `title/subtitle` ou chaves `text/data/result/response`, mas ignora `content`, onde estava o JSON em markdown.

Impacto:

- Titulo/subtitulo dinamico nao e persistido.
- A conversa segue, mas com metadados pobres.

Correcao recomendada:

1. Incluir `content` nas chaves aninhadas aceitas pelo parser.
2. Adicionar teste com payload no formato:

````json
{
  "success": true,
  "text": {
    "content": "```json\n{\"title\":\"...\",\"subtitle\":\"...\"}\n```"
  }
}
````

## P2 - Reloads de desenvolvimento interrompem fluxos longos

Evidencia nos logs:

```text
StatReload detected changes ... Reloading
Waiting for connections to close
Falha ao gerar áudio:
```

Causa provavel:

Durante a investigacao houve varias alteracoes em arquivos observados pelo Uvicorn. Isso reinicia o Gateway enquanto requests longos de TTS/contexto ainda estao em andamento.

Impacto:

- Pode amplificar falhas de audio e finalizacao.
- Pode gerar sintomas falsos em ambiente local.

Correcao recomendada:

1. Para reproduzir bugs de voz/finalizacao, rodar sem `--reload` ou evitar salvar arquivos durante o teste.
2. Excluir `tests/` e docs do watcher no ambiente dev, se possivel.

## Ordem sugerida de ataque

1. Corrigir parse robusto de contexto no AI Service.
2. Corrigir estrategia de contexto fallback antigo no Gateway.
3. Corrigir `_estimate_conversation_duration` para timestamps string.
4. Instrumentar Voice Service/Gateway TTS para descobrir se e timeout, rota errada ou resposta invalida.
5. Inserir/upsert `voice_short_response` no Gateway.
6. Limpar chamada front antiga para `/api/sessions/{sessionId}`.
7. Ajustar parser de titulo para `text.content`.

## Testes recomendados

- AI Service: `generate_session_context` aceita JSON puro e fenced JSON.
- Gateway: `_estimate_conversation_duration` aceita `datetime`, ISO string e timestamp ausente.
- Gateway: contexto salvo com `generation_method=fallback` dispara regeneracao ou retorno controlado, sem enviar `previous_session_context=None` como erro ruidoso.
- Gateway: `ChatTitleService` extrai titulo de `text.content`.
- Web-ui: abrir `session-4` dinamica chama apenas `/api/user/{username}/sessions/session-4`.
- Voz: quando `/synthesize-stream` falha, o Gateway tenta apenas um fallback final por resposta, nao um fallback por trecho.
