# ADR 004 — identidade e autorização

P02 mantém o monólito modular. D07 foi aprovada no [pedido de continuidade](../implementation/P02-request.txt); [matriz efetiva](../architecture/authorization.md). Plano §§9, 12–15 e 18 continuam sendo referência.

## Implementação

- Domínio: conta, papéis fixos, permissões e invariantes. Aplicação: casos de uso e ports de transação/senhas/tokens/relógio/e-mail. PostgreSQL, Argon2 e SMTP ficam nos adapters; HTTP/Pydantic na apresentação; bootstrap compõe tudo.
- Persistência: `users`, `user_roles`, `sessions`, `account_tokens`, `audit_events`, `identity_rate_limits`. Nome exibido é dado de identidade. O perfil comercial `Customer`, pets e funcionário operacional entram em P03/P05, sem antecipar D06.
- Senhas: 15–128 caracteres, sem trim ou composição obrigatória; Argon2id, 64 MiB, 3 iterações, paralelismo 1, salt aleatório e rehash quando necessário. Verificação dummy para conta ausente. Lista local de senhas comuns e bloqueio de padrões triviais; nenhuma senha enviada a terceiros.
- Lista SecLists `Passwords/Common-Credentials/10k-most-common.txt`, obtida em 24/09/2026; SHA-256 `68782d6a4a19a4768d5f15dd66bd534e7a33055cc755411e33f16d18c50fdcce`. Licença MIT preservada junto ao arquivo. Não representa a totalidade de senhas comprometidas.
- Sessão opaca de 32 bytes aleatórios, somente SHA-256 persistido. Ociosidade 30 minutos, máximo absoluto 8 horas. Cookie HttpOnly/SameSite=Lax/Path=/; produção usa `__Host-petland_session`, Secure e sem Domain; HTTP local usa `petland_dev_session`. Login rotaciona; logout/reset/alteração de senha/papéis/desativação revogam. Atualizar atividade não pode desfazer revogação concorrente.
- Pré-sessão anônima protege também login/cadastro. CSRF é HMAC-SHA256 específico do bearer secreto HttpOnly; header e sessão válida são exigidos junto a Origin/Referer exato. `/auth/csrf` não divulga o bearer. Nenhum token vai ao browser storage.
- Rate limit compartilhado no PostgreSQL, janela de 15 minutos: login 10 por identificador/50 por IP; cadastro/reenvios 5/25; reautenticação 10/50; consumo de tokens 100 por IP; emissão CSRF 600 por IP. Chaves são digests. `429` inclui `Retry-After`. Uvicorn ignora headers de proxy não confiáveis; com Vite, limite por IP é conservador por proxy. Proxy confiável e quotas finais dependem de D10/P06.
- Tokens: digest/purpose, consumo atômico e uso único. Verificação/convite: 24 h; reset/bootstrap: 30 min. Origem do link é configurada. Token fica no fragmento, removido pela UI, e só é consumido por confirmação explícita. Reset não autentica automaticamente.
- SMTP com timeout de 5 segundos, envio após commit. Mailpit captura mensagens locais sem relay externo. Falha gera evento seguro `identity_mail_delivery_failed`; resposta pública continua genérica e reenvio é explícito. Não há promessa de entrega durável, outbox ou tarefa volátil em memória. SMTP externo exige STARTTLS/configuração futura.
- Gestão: ADMIN verificado, senha atual por ação, versão esperada e auditoria atômica. Lock PostgreSQL compartilhado serializa administração/bootstrap e protege o último administrador ativo e verificado. Convite só concede EMPLOYEE; bootstrap só via CLI. Conta existente exige senha atual ao aceitar convite e preserva papéis anteriores.
- Banco runtime sem DDL/superuser, auditoria sem UPDATE/DELETE. CLI limpa sessões/tokens expirados há mais de 24 h e contadores antigos. Auditoria permanece até política D08; frequência da limpeza deve ser configurada antes de publicação.
- HTTP limita corpo a 16 KiB, inclusive chunked. Schemas rejeitam campos extras. Logs e erros não incluem senha, token, hash ou payload pessoal. UI não apresenta dados comerciais fictícios.

## Referências técnicas

[Argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/), [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [OWASP CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html), [Mailpit API](https://mailpit.axllent.org/docs/api-v1/), [SecLists](https://github.com/danielmiessler/SecLists).
