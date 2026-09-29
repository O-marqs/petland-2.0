# Progresso PetLand 3.0

## Estado desta entrega

**Fase:** P05 — Operação e gestão, implementada em 29/09/2026. P01–P04 preservadas; P06–P08 continuam pendentes. Veja [evidências P05](../evidence/P05.md).

**Branch:** `petland-3.0-p05`, criada de `70bce180a1c1b5edc2d2e8aa5b5c561819b7a111` da `petland-3.0-p04`. PR incremental com base P04; sem merge. **Baseline:** `3cc3f898cde896b80fed587bf8c06f4aa46742f6`; tag `legacy/petland-2.0-2024-11-24`.

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
| PL3-10 | Calendário, recursos, pausas/exceções; RF05 | Implementado; interseção loja/pessoa e impacto revalidado ao salvar |
| PL3-11 | Disponibilidade e reserva; RF06/RNF06 | Implementado; lock, duas exclusões GiST, snapshots, idempotência e testes concorrentes |
| PL3-12 | Jornada de agendamento; RF06/RNF04/06 | Implementado; resumo do servidor, confirmação, 409 sem perder escolhas, repetição após resposta perdida |
| PL3-13 | Cancelar/reagendar; RF07 | Implementado; versão, prazo contratado, assistência, rollback, eventos e avisos SMTP persistentes |
| PL3-14 | Agenda e execução, RF08/RNF01/04/06 | Implementado; dia/semana/filtros, transições, instantes reais, falta, extensão e proteção de ocupação |
| PL3-15 | Notas e histórico, RF09/RNF01 | Implementado; autoria, append-only, visibilidade explícita, resumo próprio sem notas internas |
| PL3-16 | Gestão/configuração, RF10/RF07 | Implementado; impacto protege execução aberta, calendário até meia-noite, identificação pública e gestão existente integrada |
| PL3-17 | Indicadores/auditoria, RF11 | Implementado; fórmulas documentadas, limites de período, capacidade atual e consulta ADMIN paginada |
| PL3-18 a PL3-21 | P06–P08 | Pendentes; revisão transversal de qualidade, preparação e publicação conforme decisões futuras |

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

Próximo card: **PL3-18**, fase P06, revisão transversal de qualidade e UX. P05 entrega a execução e gestão usando o protocolo do [ADR-003](../adr/0003-scheduling.md) e as regras do [ADR-012](../adr/0012-p05-operations.md). A revisão completa de desempenho, segurança, teclado/leitor de tela e setup limpo pertence ao gate P06. D10 mantém publicação/provedor externo adiados.

Não há impedimento ambiental local pendente. Não foram realizados merge, deploy, migração histórica, acesso ao MySQL ou criação de recurso pago.

Entrega anterior P01: `a6912886b2155a56a93c12b4b053eef7f6751ea2`. [CI desse commit aprovado](https://github.com/O-marqs/petland-2.0/actions/runs/35990830904), incluindo os jobs `checks` e `browser`. [PR #1 em rascunho](https://github.com/O-marqs/petland-2.0/pull/1), sem merge.

P02: 39 testes Python e 10 React aprovados; Playwright com 11 aprovados e um skip explícito do bootstrap singleton no projeto mobile. Build, tipos, lint, contratos, migrations, auditorias de dependências e atualização Compose aprovados. [Evidências P02, escopo e limitações](../evidence/P02.md); [histórico P01](../evidence/P01.md). O commit desta entrega pode ser localizado com `git log -1 -- docs/implementation/progress.md`; seu CI é registrado nos checks do PR. Revisão/aceite humano não implica merge automático.

## P03 — implementação e verificação

Módulos customers, pets e catalog; migration 0003_catalogs; reutilização pública de autenticação/CSRF/auditoria; API e contratos gerados; área do cliente e da equipe, formulário reutilizado, arquivo/restauração, convite de vínculo e catálogo público. Permissão catalog:manage incluída para EMPLOYEE conforme D07. Gestão de identidades continua ADMIN.

Validado localmente: 55 testes Python (PostgreSQL obrigatório, migrations e concorrência do vínculo), 12 React (incluindo fragmento/StrictMode e versão do formulário), 15 E2E aprovados e um skip explícito do bootstrap singleton no projeto mobile. A jornada da equipe é executada uma vez e inclui viewport de celular. Tipos, lint, build, contratos, acessibilidade automatizada e atualização Compose aprovados. Evidências e limites em [P03](../evidence/P03.md). PR/CI são registrados no próprio PR; não houve merge, deploy ou alteração de main.

## P04 — implementação e verificação

Módulo scheduling, migration 0004_scheduling, coordenação pública com identity/pets/catalog/customers, buffers opcionais por oferta, worker de avisos e contratos gerados. UI em features/booking com configuração, disponibilidade, revisão, detalhe/histórico e comandos. EMPLOYEE recebe establishment:manage conforme D07.

Validação local final: **77 Python + 12 React aprovados**, lint/tipos/arquitetura/contratos/build aprovados. **15 E2E aprovados + um skip explícito do bootstrap mobile**; a jornada ampliada da equipe foi repetida e aprovada após os ajustes finais, incluindo telas de 390/320 px. SMTP real capturado no Mailpit, disputa de vaga e perda de resposta após commit verificados. Compose final saudável; nenhuma falha de Docker. CI e commit exato são registrados no PR, sem merge.

Fontes originais preservadas; alterações do checkout legado intactas. Evidências, caminhos e limites em [P04](../evidence/P04.md); execução em [agenda local](../runbooks/scheduling.md). O commit desta entrega pode ser localizado por `git log -1 -- docs/implementation/progress.md`.

## P05 — implementação e verificação

Execução integrada ao módulo scheduling, migration 0005_operations e contratos gerados. Agenda hoje/semana, detalhe com chegada/início/conclusão/falta, extensão com proteção de pet/pessoa, notas privadas e resumos públicos, histórico filtrado, indicadores e auditoria ADMIN. Configuração protege atendimentos abertos vencidos e permite expediente até meia-noite; identidade/último administrador e comunicação de alterações preservam P02–P04.

Validação final local: **93 Python + 12 React aprovados**, lint/tipos/arquitetura/contratos/build aprovados. **15 E2E aprovados + um skip explícito do bootstrap mobile**, com jornada completa até o histórico, payload privado protegido, gestão, calendário e revogação de acesso. Acessibilidade automatizada e reflow em celular incluídos. Compose saudável; sem problema de Docker. Regras e limites no [ADR-012](../adr/0012-p05-operations.md), [runbook](../runbooks/operations.md) e [evidências P05](../evidence/P05.md).

PR incremental em rascunho sobre P04, sem merge. Resultado remoto e commit exato são registrados no PR. Próximo card PL3-18/P06; publicação continua adiada por D10.
