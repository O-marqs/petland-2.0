# Decisões arquiteturais

Aceitas pelo pedido de P01, em 23/09/2026:

- **ADR-001:** monólito modular e hexagonal pragmática. Domain depende apenas de Python; application define ports e coordena; infrastructure implementa ports; presentation adapta HTTP; bootstrap compõe. Nenhum repositório genérico ou framework de DI.
- **ADR-002:** PostgreSQL, SQLAlchemy 2 síncrono, psycopg e Alembic. Um engine por processo e conexão contextual. Migrações como comando separado, nunca no startup de cada worker. P01 cria apenas baseline técnico, sem tabelas comerciais prematuras.
- **ADR-005:** React/TypeScript/Vite SPA, TanStack Query, React Hook Form/Zod. Tokens CSS e componentes próprios. OpenAPI exportado da aplicação real; tipos gerados e cliente tipado a partir desses tipos. Contratos futuros documentados separadamente, sem endpoints falsos.
- **ADR-007:** preservar histórico/tag e desenvolver na branch `petland-3.0`. Worktree isolado para conservar as alterações não commitadas da main. Retirar legado/dependências do estado ativo após baseline recuperável.
- **ADR-011:** `uv` + Python 3.13 e workspace `pnpm` + Node 22. Lockfiles obrigatórios. Compose de desenvolvimento com portas de loopback. Logs JSON sem payloads, SQL, credenciais ou caminho arbitrário do cliente; request ID gerado no servidor.

## Identidade aprovada em P02

- **ADR-004:** identidade única, sessão opaca revogável no PostgreSQL, CSRF, hash seguro e D07 aprovada. [Decisões de implementação e limites](0004-identity.md).

## Agenda implementada em P04

- **ADR-003 / ADR-006:** unidade por pessoa, transação e exclusões, snapshots e eventos — [agenda, concorrência e avisos](0003-scheduling.md).
- **ADR-010:** parâmetros operacionais configuráveis, sem valores comerciais semeados; termos contratados e regras de assistência no mesmo ADR.

## Propostas ainda condicionadas

- **ADR-008:** hospedagem externa — D10; backup/restore local ensaiado no ADR-014, sem deploy de produção.
- **ADR-009:** dados e retenção — D06/D08/D12.

Mudanças exigem nova decisão documentada, incluindo motivo, impacto e testes. Não alterar silenciosamente o plano.

- [0007 — Cadastros, pets e ofertas por porte](0007-p03-customers-pets-catalog.md): decisões do pedido P03, vínculo, propriedade, preços/duração e evolução para P04.
- [0012 — Operação e gestão P05](0012-p05-operations.md): estados, atrasos, notas, privacidade, histórico, indicadores e auditoria.

- [0013 — Hardening e verificação P06](0013-p06-hardening.md): agregações, índices, proteção HTTP, foco e medições reproduzíveis.
- [0014 — Dados e recuperação P07](0014-p07-operations.md): demo isolada, servidor estático/TLS, backup autenticado e restore reconciliado; limites D08/D10/D12.
