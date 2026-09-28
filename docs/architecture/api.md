# Contratos HTTP

Fonte executável: [`packages/api-contract/openapi.json`](../../packages/api-contract/openapi.json), exportada da factory real sem conectar ao banco. `schema.d.ts` é gerado com openapi-typescript; `createApiClient` usa openapi-fetch com esses tipos. Lockfile fixa as versões; CI detecta divergência sem editar silenciosamente o contrato.

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

## Contratos futuros — não executáveis

Referência normativa: Plano §§13–14. Perfil comercial e troca de e-mail ainda não estão implementados. D07 foi aprovada para P02; as políticas comerciais continuam nos gates seguintes.

Reserva: POST `/api/v1/appointments` com `Idempotency-Key`, `pet_id`, `service_id`, `starts_at`, `offer_version`. Servidor deriva dono, preço, duração e recurso; confirmação após commit. Reagendar/cancelar recebem `expected_version`; conflito retorna 409 (`SLOT_UNAVAILABLE`, `OFFER_CHANGED`, `STALE_VERSION`). D02–D05 precisam de decisão antes de fechar schemas executáveis. Nenhuma dessas rotas faz parte do OpenAPI gerado da P01.

UUIDs externos; timestamps RFC3339; datas locais ISO; dinheiro string decimal + moeda. Paginação/cursor e permissões serão implementados com suas coleções. Não há contrato fictício de reserva para dar aparência de funcionalidade entregue.
