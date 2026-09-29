# Progresso PetLand 3.0

## Estado desta entrega

**Fase:** P03 — Clientes, pets e catálogo, implementada em 28/09/2026. P01/P02 preservadas; P04–P08 continuam pendentes. Veja evidências P03 para validações e limites.

**Branch:** `petland-3.0-p03`, criada de `b1b023e` da `petland-3.0-p02`. PR incremental com base P02; sem merge. **Baseline:** `3cc3f898cde896b80fed587bf8c06f4aa46742f6`; tag `legacy/petland-2.0-2024-11-24`.

| Card | Escopo / requisitos | Estado e evidência |
|---|---|---|
| PL3-01 | Histórico, fontes oficiais, ADRs e gates | Concluído, commit `80afeaa`; docs/product, ux, adr, migration |
| PL3-02 | API/web/DB/Compose/contratos/CI, RF13, RNF05/07/09 | Concluído; verificações locais, CI e clone limpo aprovados |
| PL3-03 | Tokens, navegação e campos acessíveis, RF13/RNF04 | Concluído; galeria funcional, 4 testes React e 6 E2E aprovados |
| PL3-04 | Sessão/login/logout e CSRF; RF01/RNF01 | Concluído; revogação/CSRF/propriedade, React/API/PostgreSQL e E2E aprovados |
| PL3-05 | Cadastro/verificação/reset; RF01/RNF01 | Concluído; SMTP/Mailpit real, uso único e consumo concorrente verificados |
| PL3-06 | Convites/papéis/bootstrap; RF01/RNF01 | Concluído; D07, reautenticação, versão, auditoria e último admin sob concorrência |
| PL3-07 | Perfil mínimo, cadastro assistido e associação verificada; RF02 | Implementado; vínculo de uso único, e-mail confirmado e isolamento |
| PL3-08 | Pets, referências, edição/arquivo; RF03/RNF01/04 | Implementado; propriedade A/B, FK raça/espécie, versão, preservação |
| PL3-09 | Serviços/ofertas por porte e catálogo público; RF04/RF12 | Implementado; Decimal BRL, duração, compatibilidade, ativo/inativo, catálogo/landing/dashboard |
| PL3-10 a PL3-21 | P04–P08 | Pendentes; agenda/atendimento/publicação não antecipados |

Arquivos principais: `apps/api/src/petland/bootstrap/app.py`, módulo técnico `system`, `apps/api/migrations`, `apps/web/src/features`, `apps/web/src/shared`, `packages/api-contract`, `infra`, `.github/workflows/ci.yml`, `scripts/dev.py`, README e AGENTS.md.

## Aceite da primeira entrega

1. Histórico preservado por tag e mesmo repositório.
2. Monorepo na estrutura aprovada, sem legado/venv no código ativo.
3. FastAPI inicia e responde health/readiness.
4. React inicia; rotas e reload direto funcionam.
5. Comunicação web/API/DB verificada por E2E.
6. PostgreSQL local iniciado.
7. Migrations executadas, repetidas e revertidas em teste.
8. Design system funcional, sem persistência simulada.
9. Fronteiras verificadas e guard testado contra violações.
10. Testes: 18 Python + 4 React + 6 E2E aprovados.
11. Build frontend aprovado.
12. README validado em clone limpo: `init` e `up`, banco novo, migrations e serviços saudáveis.
13. Contratos reais gerados; identidade/reserva documentadas como futuras.
14. AGENTS.md criado.
15. Plano/PDF integrais incorporados com hashes registrados.
16. Nenhum segredo real adicionado; .env local ignorado; scan inicial passou.
17. Funcionalidades posteriores identificadas como planejadas.

## Decisões / impedimentos / continuidade

Decisões D01–D11 respondidas no pedido P03; pontos incompletos seguem as recomendações por autorização expressa. Registro vigente em docs/product/decisions.md. D08 dispensa migração de dados legados; D10 adia publicação/provedor.

Próximo card: **PL3-10**, fase P04, capacidade/funcionamento configuráveis por funcionários e horários, com atribuição pelo servidor. D03 exige resumo e confirmação do cliente; D04 sem taxas; duração/preço por porte alimentam snapshots de reservas. Comunicação de cancelamento/reagendamento faz parte da próxima entrega operacional. Não existe reserva ou disponibilidade simulada nesta P03.

Não há impedimento ambiental local pendente. Não foram realizados merge, deploy, migração histórica, acesso ao MySQL ou criação de recurso pago.

Entrega anterior P01: `a6912886b2155a56a93c12b4b053eef7f6751ea2`. [CI desse commit aprovado](https://github.com/O-marqs/petland-2.0/actions/runs/35990830904), incluindo os jobs `checks` e `browser`. [PR #1 em rascunho](https://github.com/O-marqs/petland-2.0/pull/1), sem merge.

P02: 39 testes Python e 10 React aprovados; Playwright com 11 aprovados e um skip explícito do bootstrap singleton no projeto mobile. Build, tipos, lint, contratos, migrations, auditorias de dependências e atualização Compose aprovados. [Evidências P02, escopo e limitações](../evidence/P02.md); [histórico P01](../evidence/P01.md). O commit desta entrega pode ser localizado com `git log -1 -- docs/implementation/progress.md`; seu CI é registrado nos checks do PR. Revisão/aceite humano não implica merge automático.

## P03 — implementação e verificação

Módulos customers, pets e catalog; migration 0003_catalogs; reutilização pública de autenticação/CSRF/auditoria; API e contratos gerados; área do cliente e da equipe, formulário reutilizado, arquivo/restauração, convite de vínculo e catálogo público. Permissão catalog:manage incluída para EMPLOYEE conforme D07. Gestão de identidades continua ADMIN.

Validado localmente: 55 testes Python (PostgreSQL obrigatório, migrations e concorrência do vínculo), 12 React (incluindo fragmento/StrictMode e versão do formulário), 15 E2E aprovados e um skip explícito do bootstrap singleton no projeto mobile. A jornada da equipe é executada uma vez e inclui viewport de celular. Tipos, lint, build, contratos, acessibilidade automatizada e atualização Compose aprovados. Evidências e limites em [P03](../evidence/P03.md). PR/CI são registrados no próprio PR; não houve merge, deploy ou alteração de main.
