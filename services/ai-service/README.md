# ai-service

Backend principal unificado da plataforma empatIA.

Objetivos desta primeira construção:

- centralizar chat, streaming, auth, sessões, prompts e admin em um único boundary;
- manter compatibilidade com os contratos atuais de `web-ui` e `admin-panel`;
- operar sem dependência de `gateway-service` ou do `ai-service` legado.

Estado atual:

- bootstrap FastAPI pronto;
- rotas públicas, admin e internas registradas;
- chat sync, stream compatível e compatibilidade OpenAI já apontando para a orquestração nova;
- `session-1` internalizada no próprio `ai-service`;
- estrutura base de application, domain, infrastructure e repositories criada;
- ainda faltam validação operacional ampliada, mais testes dedicados e limpeza adicional de documentação histórica.
