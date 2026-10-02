# Contratos HTTP

Fonte executável: [`packages/api-contract/openapi.json`](../../packages/api-contract/openapi.json), exportada da factory real sem conectar ao banco. `schema.d.ts` é gerado com openapi-typescript; `createApiClient` usa openapi-fetch com esses tipos. Lockfile fixa as versões; CI detecta divergência sem editar silenciosamente o contrato.

Incremento operacional: GET `/operations/dashboard` (data/minha equipe), GET/PUT `/operations/roster/{day}` e POST de prévia, GET/PUT `/operations/capacity` e POST de prévia, POST `/operations/attendances/{id}/transfer`. Todos exigem identidade/papel; mutações usam CSRF, versão e transferência usa idempotência. Agenda aceita `mine`; UI pessoal por padrão, API preserva o padrão coletivo para clientes anteriores. Início aceita `care_version` para confirmar alertas atuais; detalhe interno reúne contexto anterior/transferência/avisos, público só projeta resumo e estado da comunicação. Métricas acrescem pessoa/serviço/instantes reais e pets/clientes únicos. [Regras](../adr/0016-operational-evolution.md).

| Implementado | Resultado |
|---|---|
| GET `/api/v1/health/live` | 200 `{"status":"ok"}` independente do DB |
| GET `/api/v1/health/ready` | 200 `{"status":"ready"}` somente com revisão compatível; senão 503 |

Erros são `application/problem+json`, com `type`, `title`, `status`, `code`, `detail`, `request_id`, `errors`. Header `X-Request-ID` coincide com o corpo/log. Validação não serializa valores recebidos; 400/401/403/404/405/409/413/422/429/500/503 seguem o mesmo envelope. OpenAPI descreve apenas rotas funcionais.

## Identidade implementada em P02

Todos os caminhos abaixo recebem prefixo `/api/v1`. Mutações exigem cookie de sessão/pré-sessão, `X-CSRF-Token` obtido de `/auth/csrf` e Origin/Referer permitido. O cliente tipado centraliza essa preparação, timeout, cookies e leitura de Problem Details. Não repete automaticamente mutações.

| Método e caminho | Acesso / resultado |
|---|---|
| GET `/auth/csrf` | Emite pré-sessão quando necessário e token CSRF vinculado |
| POST `/auth/register` | Público, nome/e-mail/senha, somente CUSTOMER; 202 genérico |
| POST `/auth/login` | Credenciais, cookie opaco rotacionado e conta segura |
| POST `/auth/logout` | Revoga sessão e remove cookie; 204 |
| GET `/auth/me` | Dados básicos e permissões atuais do próprio usuário |
| POST `/auth/email-verification-requests` | Reenvio genérico 202, com rate limit |
| POST `/auth/email-verifications` | Consumo único do token de verificação |
| POST `/auth/password-reset-requests` | Resposta genérica 202 sem enumerar conta |
| POST `/auth/password-resets` | Token único, nova senha e revogação de sessões; sem login automático |
| GET `/auth/sessions` | Sessões válidas da própria conta, sem bearer/hash/IP |
| DELETE `/auth/sessions/{session_id}` | Revoga somente sessão própria; 404 para alheia |
| POST `/me/password-changes` | Senha atual + nova senha; revoga todas as sessões |
| POST `/management/employee-invitations` | ADMIN verificado + senha atual; convite EMPLOYEE, 202 |
| POST `/auth/invitations/accept` | Token controlado + nome/senha; conta existente exige senha atual |
| GET `/management/users` | ADMIN; offset/limit (máximo 50), `items` e `has_more` |
| PUT `/management/users/{user_id}/roles` | ADMIN reautenticado, roles allowlist e `expected_version`; revoga sessões |
| PATCH `/management/users/{user_id}/status` | ADMIN reautenticado, ACTIVE/DISABLED e `expected_version` |

Erros de identidade incluem `INVALID_CREDENTIALS`, `CSRF_REJECTED`, `INVALID_TOKEN`, `WEAK_PASSWORD`, `EMAIL_NOT_VERIFIED`, `FORBIDDEN`, `REAUTHENTICATION_FAILED`, `LAST_ADMIN`, `STALE_VERSION` e `RATE_LIMITED`. `429` inclui `Retry-After: 900`. Respostas não incluem senha/hash/digest/token de autenticação. Cadastro duplicado mantém mensagem genérica.

```sh
pnpm contracts:generate
pnpm contracts:check
```

## Cadastros P03 e agenda P04

Cadastros próprios em `/me/customer` e `/me/pets`; assistidos em `/operations/customers` e pets subordinados ao cliente. Catálogo público em `/catalog/services`; equipe mantém ofertas em `/operations/services`. Schemas completos e paginação estão no OpenAPI.

Disponibilidade: GET `/me/availability` e `/operations/availability` (este exige customer_id). Recebe pet_id, service_id e data local ISO; appointment_id opcional consulta reagendamento com condições contratadas. Resposta inclui slots, timezone, preço/duração/buffers, prazo de alteração, offer.version e configuration_version, sem identificar o profissional.

Reservas: GET/POST `/me/appointments` e `/operations/appointments`, GET por ID e POST por ID com sufixos `/cancel` ou `/reschedule`. Criação exige Idempotency-Key UUID, pet_id, service_id, starts_at RFC3339 com timezone, offer_version e configuration_version; operação assistida acrescenta customer_id. Cancelar exige version/motivo; reagendar também novo início/versão da configuração. Campos extras são rejeitados. Reserva só é confirmada após commit.

Calendário: GET/PUT `/operations/calendar`, POST `/operations/calendar/impact-preview`, POST `/operations/resources` e PUT por resource_id. Calendário representa minutos desde meia-noite e dias da semana 0=segunda a 6=domingo; datas especiais substituem o dia. Versões evitam salvar sobre mudanças de outra pessoa. Configuração e recursos têm limite HTTP de 64 KiB; outras mutações mantêm 16 KiB.

Conflitos: SLOT_UNAVAILABLE, OFFER_CHANGED, STALE_VERSION, CALENDAR_IMPACT, FUTURE_BOOKINGS, RESOURCE_EXISTS, IDEMPOTENCY_MISMATCH. Política: CHANGE_WINDOW_CLOSED/BOOKING_CLOSED. Transiente: SCHEDULE_BUSY (503), repetição explícita com mesma chave. Erros públicos não expõem SQL, conta alheia ou parâmetros internos.

UUIDs externos; timestamps RFC3339; datas locais ISO; dinheiro string decimal + moeda BRL. Listagens paginam offset/limit, máximo 100. Pagamento e troca de e-mail continuam fora do escopo.

## Operação e gestão P05

- GET `/operations/agenda`: hoje por padrão; date_from/date_to inclusivas, até 31 dias, status/resource_id/search, offset/limit. Projeção mínima de cliente e pessoa; ações permitidas e alerta de atraso.
- GET `/operations/attendances/{appointment_id}`: contexto de cuidado/contato, pessoa, notas protegidas e eventos com autores.
- POST no mesmo prefixo, `/transitions`: version, operation (arrive/start/complete/no_show/cancel_exception), reason e summary opcional na conclusão. `/notes`: version/body/visibility INTERNAL ou PUBLIC. `/extensions`: version/reason/until RFC3339, resource_id opcional. Todos exigem Idempotency-Key e CSRF; retorno somente após commit.
- GET `/me/appointments` e lista assistida: period all/upcoming/history, pet_id/status, customer_id somente na assistida. Detalhe público acrescenta summaries explicitamente PUBLIC; nunca notas internas ou dados de autores/recursos.
- GET `/management/metrics`: ADMIN, date_from/date_to inclusivas no fuso da loja. Fórmulas e limites no ADR-012.
- GET `/management/audit`: ADMIN, start/end RFC3339 semiabertos, até 31 dias, action/actor_id/target_id e paginação. Sem corpos ou credenciais.
- GET `/establishment`: nome/telefone/e-mail/endereço/fuso públicos. Campos vêm da configuração versionada, com tolerância de falta adicional e preview de calendário preservado.

Novos conflitos seguros: INVALID_TRANSITION, RESOURCE_IN_PROGRESS, INVALID_EXTENSION, EXTENSION_UNAVAILABLE. REASON_REQUIRED/INVALID_PERIOD orientam correção. Campos extras e instantes fornecidos como supostos horários reais são rejeitados.
