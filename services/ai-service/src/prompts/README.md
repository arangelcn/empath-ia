# prompts

Este diretório vai receber os prompts canônicos do `ai-service` durante a migração.

Nesta fase ele existe para deixar explícito que:

- prompts nao devem ficar espalhados entre transporte HTTP e runtime;
- o novo boundary tera ownership unico para prompt pipeline;
- a origem final dos prompts sera consolidada gradualmente sem alterar o legado.
