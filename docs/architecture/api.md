# Contratos HTTP

Fonte executável: [`packages/api-contract/openapi.json`](../../packages/api-contract/openapi.json), exportada da factory real sem conectar ao banco. `schema.d.ts` é gerado com openapi-typescript; `createApiClient` usa openapi-fetch com esses tipos. Lockfile fixa as versões; CI detecta divergência sem editar silenciosamente o contrato.

| Implementado | Resultado |
|---|---|
| GET `/api/v1/health/live` | 200 `{"status":"ok"}` independente do DB |
| GET `/api/v1/health/ready` | 200 `{"status":"ready"}` somente com revisão compatível; senão 503 |

Erros são `application/problem+json`, com `type`, `title`, `status`, `code`, `detail`, `request_id`, `errors`. Header `X-Request-ID` coincide com o corpo/log. Validação não serializa valores recebidos; 404/405/422/500/503 seguem o mesmo envelope. OpenAPI descreve apenas rotas funcionais.

```sh
pnpm contracts:generate
pnpm contracts:check
```

## Contratos futuros — não executáveis

Referência normativa para P02/P04: Plano §§13–14. Identidade: POST `/api/v1/auth/register`, `/auth/login`, `/auth/logout`; GET `/auth/me`, `/auth/csrf`. Sessão opaca em cookie HttpOnly/Secure no ambiente HTTPS, proteção CSRF, sem atribuição pública de role. D07 permanece gate.

Reserva: POST `/api/v1/appointments` com `Idempotency-Key`, `pet_id`, `service_id`, `starts_at`, `offer_version`. Servidor deriva dono, preço, duração e recurso; confirmação após commit. Reagendar/cancelar recebem `expected_version`; conflito retorna 409 (`SLOT_UNAVAILABLE`, `OFFER_CHANGED`, `STALE_VERSION`). D02–D05 precisam de decisão antes de fechar schemas executáveis. Nenhuma dessas rotas faz parte do OpenAPI gerado da P01.

UUIDs externos; timestamps RFC3339; datas locais ISO; dinheiro string decimal + moeda. Paginação/cursor e permissões serão implementados com suas coleções. Não há contrato fictício de reserva para dar aparência de funcionalidade entregue.
