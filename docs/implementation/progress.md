# Progresso PetLand 3.0

## Estado desta entrega

**Fase:** P07 — Dados e ensaio operacional local, em validação em 01/10/2026. P06 integrada pelo usuário no PR #6; P01–P06 preservadas. Aceite sonoro humano P06 pendente; avanço P07 expressamente autorizado. P08 não iniciada.

**Branch:** `petland-3.0-p07`, criada de `e90e17af095ffa15b13601f25448232d84f36286` da `petland-3.0-p04`. PR incremental com base P04; sem merge automático. **Baseline:** `3cc3f898cde896b80fed587bf8c06f4aa46742f6`; tag `legacy/petland-2.0-2024-11-24`.

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
| PL3-18 | P06, RNF01–04/06/07 | Integrado pelo usuário; CI/medições aprovadas, aceite humano com leitor de tela ainda pendente |
| PL3-19 | Mapeamento/migração condicionais | Dispensados por D08/D12; nenhum MySQL acessado ou histórico importado |
| PL3-20 | Dados/ensaio operacional P07 | Demo, seed/reset, TLS, backup/restore e três perfis verificados localmente; CI/revisão pendentes, publicação externa adiada por D10 |
| PL3-21 | P08, release/case | Pendente; não iniciar automaticamente |

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

Card atual: **PL3-19–20**, fase P07 autorizada em [P07-request.txt](P07-request.txt). Continuidade após merge P06 não comprova aceite sonoro humano; essa pendência acompanha o release. Dados sintéticos e ensaio local seguem [ADR-014](../adr/0014-p07-operations.md). D08/D12 dispensam migração; D10 mantém provedor, publicação e backup externo adiados. Não iniciar P08 automaticamente.

Docker recuperado após reinício autorizado do Windows em 30/09/2026; em 01/10/2026 os serviços voltaram saudáveis, preservando volumes e dados. A falha anterior do backend OTel/socket residual não reapareceu. Saltos de relógio WSL de cerca de cinco segundos foram observados; a sincronização duplicada do Ubuntu foi desabilitada e o horário alinhado ao Windows. Correções menores persistiram; não há prova de estabilidade absoluta nem de que toda contenção veio do relógio. A rodada final confirmou todas as 200 reservas, sem erros de leitura/escrita. Procedimento e reversão no [runbook de qualidade](../runbooks/quality.md). Não foram realizados reset de fábrica, merge automático, deploy, migração histórica, acesso ao MySQL ou criação de recurso pago.

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

## P06 — implementação e verificação

Segurança, foco/títulos, carregamento acessível, estabilidade visual, agregação/índices e redução de consultas implementados. `python scripts/dev.py check` aprovado: **101 Python + 15 React**, tipos, lint, contratos, arquitetura, migrations e build. Auditorias de dependências aprovadas. Compose final saudável e **15 E2E aprovados + um skip explícito do bootstrap mobile**, incluindo SMTP real, três perfis, jornada até histórico, dados privados, teclado e reflow. Fontes oficiais, main, tag e alterações do checkout legado conferidas e preservadas.

Medição API normal com 100 mil agendamentos e 20 sessões: todas as leituras abaixo de 400 ms no p95 e 200 reservas confirmadas, p95 **775,91 ms** (meta 800 ms). Laboratório web: **9/9 amostras aprovadas**, LCP máximo 2028 ms, INP máximo 88 ms, CLS máximo 0,00119. Metas e timeouts mantidos; resultados e limites de ambiente no [registro P06](../evidence/P06.md). CI repete a carga API em Linux limpo, independentemente do relógio WSL local.

P06 integrada pelo usuário no [PR #6](https://github.com/O-marqs/petland-2.0/pull/6), merge `e90e17a`. [CI do commit `1607cbe` aprovada](https://github.com/O-marqs/petland-2.0/actions/runs/36894412439): checks/browser, carga Linux com reserva p95 427,37 ms e leituras até 215,35 ms, 15 E2E + skip mobile previsto. **Aceite humano com leitor de tela continua pendente**; usuário autorizou explicitamente avançar P07. Ver [roteiro de aceite](../runbooks/quality.md).

## P07 — dados e ensaio operacional local

Demo sintética isolada, transação de seed e UUIDs estáveis, reset preservando origem, servidor estático com TLS, imagem identificável, PostgreSQL verify-full, SMTP STARTTLS, cookies Secure/HttpOnly e proxy sem cache da API. Ferramentas offline recusam produção/bancos fora do namespace e não expõem credenciais. D08/D12 dispensam dados históricos; não declarar migração executada.

Backup custom autenticado/criptografado e restore em banco novo, contagens/digests de todas as tabelas, ACLs e duas exclusões GiST conferidos. Cópia ativada e três perfis verificados no navegador a 320 px, depois retorno à origem. Cadastro/SMTP, capacidade, propriedade, notas privadas e idempotência persistida também verificados na cópia. CI adicionada para repetir o ensaio completo em ambiente limpo.

Verificação final local aprovada: 114 testes Python + 15 React no check completo, 15 E2E + 1 skip mobile previsto, auditorias sem vulnerabilidade conhecida e nove verificações de perfis no staging. Falha de startup do destino restaura o apontamento anterior e tenta reiniciar a origem; cenário de falha verificado em teste. Resultados e limitações em [P07](../evidence/P07.md), reprodução em [runbook de recuperação](../runbooks/operations-recovery.md). Próximo passo: PR em rascunho sobre P04 e CI do commit exato. Backup continua no mesmo host; retenção/cópia externa, RPO/RTO produtivos, publicação e P08 dependem de D10 e aceite futuro. Fontes, histórico e alterações do legado preservados.
