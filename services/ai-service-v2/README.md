# ai-service-v2

Boundary temporário para a fusão de `gateway-service` + `ai-service`.

Objetivos desta primeira construção:

- manter o legado intacto;
- oferecer um serviço novo, bootável e organizado por camadas;
- preparar fachadas compatíveis para migração incremental por ownership;
- permitir shadow testing antes do rename final para `ai-service`.

Estado atual:

- bootstrap FastAPI pronto;
- rotas públicas, admin e internas registradas;
- chat sync, stream compatível e compatibilidade OpenAI já apontando para a orquestração nova;
- `session-1` internalizada no próprio `ai-service-v2`, sem dependência do `gateway-service`;
- estrutura base de application, domain, infrastructure e repositories criada;
- ainda faltam validação operacional com provider real, testes adicionais e substituição de rotas admin ainda em scaffold.
