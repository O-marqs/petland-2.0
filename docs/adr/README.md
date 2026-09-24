# Decisões arquiteturais

Aceitas pelo pedido de P01, em 23/09/2026:

- **ADR-001:** monólito modular e hexagonal pragmática. Domain depende apenas de Python; application define ports e coordena; infrastructure implementa ports; presentation adapta HTTP; bootstrap compõe. Nenhum repositório genérico ou framework de DI.
- **ADR-002:** PostgreSQL, SQLAlchemy 2 síncrono, psycopg e Alembic. Um engine por processo e conexão contextual. Migrações como comando separado, nunca no startup de cada worker. P01 cria apenas baseline técnico, sem tabelas comerciais prematuras.
- **ADR-005:** React/TypeScript/Vite SPA, TanStack Query, React Hook Form/Zod. Tokens CSS e componentes próprios. OpenAPI exportado da aplicação real; tipos gerados e cliente tipado a partir desses tipos. Contratos futuros documentados separadamente, sem endpoints falsos.
- **ADR-007:** preservar histórico/tag e desenvolver na branch `petland-3.0`. Worktree isolado para conservar as alterações não commitadas da main. Retirar legado/dependências do estado ativo após baseline recuperável.
- **ADR-011:** `uv` + Python 3.13 e workspace `pnpm` + Node 22. Lockfiles obrigatórios. Compose de desenvolvimento com portas de loopback. Logs JSON sem payloads, SQL, credenciais ou caminho arbitrário do cliente; request ID gerado no servidor.

## Diretrizes aceitas; implementação posterior

- **ADR-004:** identidade única, sessão opaca revogável no PostgreSQL, CSRF, hash seguro. Implementar em P02; matriz operacional depende D07.
- **ADR-006:** snapshots, eventos e preservação do histórico. Implementar nos módulos/fases correspondentes.

## Propostas ainda condicionadas

- **ADR-003:** unidade de capacidade e concorrência — D02/D03/D04; o protocolo transacional do plano é referência técnica, sem parâmetros comerciais inventados.
- **ADR-008:** hospedagem/backup — D10; Compose local não é deploy de produção.
- **ADR-009:** dados e retenção — D06/D08/D12.
- **ADR-010:** parâmetros comerciais do MVP — D02 a D07.

Mudanças exigem nova decisão documentada, incluindo motivo, impacto e testes. Não alterar silenciosamente o plano.
