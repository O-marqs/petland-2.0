# PetLand 3.0 — referência operacional

## Objetivo e fontes

Uma loja, demonstração de portfólio, três perfis. Leia `docs/implementation/progress.md` antes de trabalhar; não recrie entregas concluídas. Fontes oficiais: `docs/product/PetLand_3.0_Plano_Consolidado.md` (principal técnica) e `docs/ux/PetLand_3.0_Caderno_UX.pdf` (visual). Preserve esses arquivos íntegros. Autorizações em `docs/implementation/P01-request.txt` a `P08-request.txt`; decisões atuais em `docs/product/decisions.md` e `docs/adr/README.md`.

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
- Identidade/permissões sempre no servidor; não guardar tokens em localStorage nem usar CPF como identidade pública. Sessão/CSRF, convites e papéis são implementados em `identity`; não substituir por autenticação simulada. A matriz D07 está em `docs/architecture/authorization.md`.
- Nenhuma reserva fictícia para demonstrar contratos; dados sintéticos somente identificados em demo/testes.
- Preserve tag `legacy/petland-2.0-2024-11-24` e histórico. Não force push, não reescreva história, não altere main, não descarte mudanças alheias. Repositórios locais ficam em `C:\Users\LUCASMARQUESMARQUES\Documents\GitHub`.
- O worktree `petland-3.0` depende da pasta original `petland 2.0` para os metadados Git; não mova/remova a original.
- Não fazer merge automático, deploy de produção ou criar recursos pagos. PRs de revisão estão autorizados. P06 parte do merge `679eae5` em `petland-3.0-p06`, com base de PR `petland-3.0-p04`, onde P05 foi integrada pelo usuário.

## Conclusão e continuidade

Respeite roadmap/gates. Decisões D01–D11 e recomendações complementares aprovadas no pedido P03; P04 autorizada em P04-request.txt. Leia docs/product/decisions.md e ADR-003 antes de alterar agenda. Estabelecimento é sempre o primeiro lock em mutações críticas; não retirar exclusões de recurso/pet nem idempotência. Agenda começa desabilitada, sem horários/funcionários comerciais. P05 implementa a operação; leia também ADR-012. P06 está autorizada e revisa qualidade, segurança, desempenho e UX; não iniciar P07 automaticamente. Não alterar decisões aprovadas silenciosamente. Registre escopo, RF/RNF, arquivos, implementação, verificações reais, limitações e próximo card em `docs/implementation/progress.md` e `docs/evidence`. Atualize README/runbooks junto ao código. UI isolada não conclui funcionalidade de negócio.

P07 expressamente autorizada após merge P06 `e90e17a`; trabalho em `petland-3.0-p07`, base do PR `petland-3.0-p04`. Leia `P07-request.txt`, ADR-014 e runbook operations-recovery antes de alterar ferramentas offline. A autorização de avanço prevalece sobre a orientação anterior de não iniciar P07 automaticamente. Aceite humano com leitor de tela permanece pendente; não inventar aprovação. D08/D12 dispensam importação histórica; D10 adia publicação/provedor externo. Demo somente em namespace/banco/volume isolados, nunca semear desenvolvimento ou produção. Reset/restore não sobrescrevem origem; ativar cópia somente após reconciliação. Não imprimir/versionar senhas, chaves, tokens ou dump em claro. P08 não começa automaticamente.

Em caso de problema de Docker, a orientação inicial era parar e informar o ajuste. O usuário posteriormente autorizou expressamente a recuperação local do Docker/WSL e o reinício do computador para retomar o trabalho. Essa autorização prevalece: diagnosticar e recuperar os serviços preservando volumes, imagens e dados; não fazer reset de fábrica ou apagar dados.

P08 expressamente autorizada após merge P07 `3dde06b`; branch `petland-3.0-p08`, base do PR P04. Autorização prevalece sobre a orientação anterior de não começar P08 automaticamente. Candidata 3.0.0-rc.1 para revisão, conforme ADR-015: ler case, candidate.json e runbook release. Preservar proveniência histórica e distinguir template isolado de fluxo legado; depois/vídeo somente da aplicação real com dados fictícios identificados. Preview serve só pasta pública no loopback; não expor raiz/.local. Ferramentas de release não concedem aceite. Gates humano final/leitor de tela e D10 permanecem pendentes, sem tag/release estável/publicação automática ou expansão de escopo presumida.
