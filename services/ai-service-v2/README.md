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
- fachada de chat compatível em modo scaffold;
- estrutura base de application, domain, infrastructure e repositories criada.
