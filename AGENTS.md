# PetLand 3.0 — referência operacional

## Objetivo e fontes

Uma loja, demonstração de portfólio, três perfis. Leia `docs/implementation/progress.md` antes de trabalhar; não recrie entregas concluídas. Fontes oficiais: `docs/product/PetLand_3.0_Plano_Consolidado.md` (principal técnica) e `docs/ux/PetLand_3.0_Caderno_UX.pdf` (visual). Preserve esses arquivos íntegros. A autorização e o escopo P01 estão em `docs/implementation/P01-request.txt`; decisões atuais em `docs/product/decisions.md` e `docs/adr/README.md`.

## Arquitetura e código

- `apps/api`: FastAPI, Python tipado, SQLAlchemy síncrono/psycopg e Alembic; monólito modular hexagonal pragmático.
- `modules/<dominio>/domain`: Python puro; sem FastAPI, SQLAlchemy, Pydantic HTTP ou infraestrutura.
- `application`: casos de uso/autorização contextual e ports pequenas; sem SQL, HTTP ou adapters concretos.
- `infrastructure`: ORM, persistência e integrações; `presentation`: schemas/HTTP; `bootstrap` compõe tudo.
- Módulos não acessam internals alheios; colaborações por contratos públicos. Não adicionar repositório genérico, camada vazia ou abstração sem uso.
- `apps/web`: React/TS/Vite, funcionalidades em `features`, UI em `shared`, composição em `app`. UI não importa features. Dados remotos com TanStack Query, formulários RHF/Zod.
- Tokens em `shared/styles/tokens.css`; fontes locais, pt-BR na interface e contratos técnicos em inglês.
- `packages/api-contract`: OpenAPI/tipos gerados. Nunca editar arquivos gerados manualmente; `pnpm contracts:generate`, depois `pnpm contracts:check`.
- `infra` é local; `docs` guarda decisões e evidências; `scripts/dev.py` centraliza comandos.

## Execução e verificações

Da raiz: `python scripts/dev.py init`, `install`, `db`, `migrate`, `api` e `web` (terminais separados). Alternativa somente Docker: `init` e `up`. Parar com `down`, preservando volume.

Antes de entregar: `python scripts/dev.py check`; aplicação iniciada: `python scripts/dev.py e2e`. Testes de banco só com PostgreSQL efêmero, `APP_ENV=test`, nome terminando `_test`. CI exige integração, sem skip silencioso. Não usar SQLite para regras de PostgreSQL. Execute testes comportamentais proporcionais; não espelhe implementação nem esconda falhas. Não declarar aprovação sem execução.

## Segurança e histórico

- Não copiar credenciais/PII do legado, não acessar MySQL ou migrar dados reais sem autorização específica.
- `.env`, caches, venvs e node_modules nunca versionados. Use configuração validada, logs por allowlist e erros públicos seguros.
- Identidade/permissões sempre no servidor; não guardar tokens em localStorage nem usar CPF como identidade pública. Sessão/CSRF são P02, ainda não entregues.
- Nenhuma reserva fictícia para demonstrar contratos; dados sintéticos somente identificados em demo/testes.
- Preserve tag `legacy/petland-2.0-2024-11-24` e histórico. Não force push, não reescreva história, não altere main, não descarte mudanças alheias. Repositórios locais ficam em `C:\Users\LUCASMARQUESMARQUES\Documents\GitHub`.
- O worktree `petland-3.0` depende da pasta original `petland 2.0` para os metadados Git; não mova/remova a original.
- Não fazer merge automático, deploy de produção ou criar recursos pagos. PR de revisão está autorizado para P01.

## Conclusão e continuidade

Respeite roadmap/gates. D07 bloqueia a próxima fase P02; parâmetros comerciais não aprovados não podem ser inventados. Não alterar decisões aprovadas silenciosamente. Registre escopo, RF/RNF, arquivos, implementação, verificações reais, limitações e próximo card em `docs/implementation/progress.md` e `docs/evidence`. Atualize README/runbooks junto ao código. UI isolada não conclui funcionalidade de negócio. Não declarar PetLand 3.0 completo por entregar P01.
