# Progresso PetLand 3.0

## Estado desta entrega

**Fase:** P08 integrada no PR #8; correção do primeiro acesso em revisão em 01/10/2026. Candidata 3.0.0-rc.1 e case preservados. Aceite final de produto e sonoro humano pendentes; publicação externa permanece adiada por D10.

**Branch atual:** `petland-3.0-onboarding-fix`, criada do merge P08 `3fba52725d5a6e77fd87b40a2e166a0a436f64df` na `petland-3.0-p04`. PR incremental com base P04; sem merge automático. **Baseline:** `3cc3f898cde896b80fed587bf8c06f4aa46742f6`; tag `legacy/petland-2.0-2024-11-24`.

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
| PL3-20 | Dados/ensaio operacional P07 | PR #7 integrado; checks/browser/operations aprovados; demo e restore comprovados, publicação externa adiada D10 |
| PL3-21 | P08, release/case | Candidata, case, antes/depois, vídeo, diagramas e pacote local preparados; aceite final/publicação estável pendentes |

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

Card atual: **PL3-21**, fase P08 autorizada em [P08-request.txt](P08-request.txt), sobre P07 integrada. Continuidade não comprova aceite sonoro/final humano. [ADR-015](../adr/0015-p08-release-case.md) mantém candidata explícita e [procedimento de revisão](../runbooks/release.md). D08/D12 dispensam migração; D10 mantém provedor, publicação e backup externo adiados. Não publicar/taguear/promover ou iniciar escopo adicional automaticamente.

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

Verificação final local aprovada: 114 testes Python + 15 React no check completo, 15 E2E + 1 skip mobile previsto, auditorias sem vulnerabilidade conhecida e nove verificações de perfis no staging. Falha de startup do destino restaura o apontamento anterior e tenta reiniciar a origem; cenário de falha verificado em teste. [CI P07 aprovada](https://github.com/O-marqs/petland-2.0/actions/runs/36905134678): checks/browser/operations, 23 tabelas reconciliadas; merge pelo usuário no PR #7 (`3dde06b`). Resultados e limitações em [P07](../evidence/P07.md), reprodução no runbook. Backup continua no mesmo host; retenção/cópia externa, RPO/RTO produtivos e publicação dependem de D10. Fontes, histórico e alterações do legado preservados.

## P08 — candidata e case de revisão

Versões npm/OpenAPI/factory `3.0.0-rc.1` e Python `3.0.0rc1`, contratos regenerados; nenhuma mudança de schema ou regra comercial. Case com problema/decisões/trade-offs/limites, antes histórico isolado do commit preservado, depois real, vídeo integral de 185,12 segundos sem áudio, WebVTT/transcrição, diagramas de contexto/containers/transação e DER/dicionário. Dados/identidades/serviço fictícios e preparação declarada, sem relógio simulado ou senhas filmadas.

Cadastro e reserva UI → chegada/nota privada/início/conclusão UI → histórico público → gestão/impacto/auditoria: mesma reserva conferida na API; nota interna ausente do payload cliente; impacto não altera configuração/reserva. Quatorze checkpoints de captura aprovados. Origens/reset preservados, demonstração retornou ao banco anterior; smoke real novamente aprovado.

Check completo local: 114 Python + 15 React, lint/tipos/contratos/build/migrations/arquitetura/scan. Player verificado a 1280/320 px: duração real, legendas, capítulos, links locais, axe/reflow e ausência de erro JavaScript. O servidor padrão sem ranges não permitia saltar capítulos; preview dedicado fixa loopback/pasta pública e ranges, agora exercitado na CI. `release.py` confere versões/artefatos, empacota árvore Git limpa com hashes/gates e verifica sem extrair; não publica, tagueia ou concede aceite.

Evidências em [P08](../evidence/P08.md), [case](../case/README.md) e [qualidade](../release/quality-report.md). CI/pacote do commit exato ficam registrados no PR. Próximo gate: revisão humana de produto/leitor de tela e decisão D10 antes de release estável/publicação. Candidata não é serviço comercial nem alegação de recuperação após perda do host.

## Correção do primeiro acesso após P08

P08 integrada pelo usuário no PR #8, merge `3fba527`; correção em `petland-3.0-onboarding-fix` com PR incremental sobre P04. [Pedido humano](Onboarding-request.txt): conta recém-cadastrada sem orientação para confirmar e-mail, criar pet e agendar.

Reproduzido: cadastro/SMTP local e login reais funcionavam; faltavam indicação da caixa local, sequência contato/pet/reserva e pré-requisito claro no agendamento. Corrigidos conclusão/foco do cadastro, caixa de e-mails de teste, atualização da confirmação, links para área atual, primeiros passos do dashboard e guarda de contato no agendamento. Segurança/API/schema/agenda mantidos. [Roteiro manual](../runbooks/manual-acceptance.md), [evidência e limites](../evidence/Onboarding.md).

Check completo: 114 Python + 18 React; E2E 15 aprovados + skip mobile previsto. Conta criada pela interface no HTTPS local confirmou mensagem, salvou contato/pet, reservou e conferiu persistência. Funcionário acessou a mesma reserva, reagendou/cancelou; quatro avisos SMTP capturados. Nove checkpoints com axe/reflow aprovados. CI repete a nova jornada de staging; resultado do commit exato registrado no PR. Nenhum aceite humano ou merge automático concedido. Próximo passo: teste pessoal do usuário com cliente/funcionário, mantendo D10 e leitor de tela pendentes.

## Revisão das dores e identidade PetLand

[Pedido posterior](Product-review-request.md): dores, equipe por data, crítica de navegação e visual autoral do PetLand/case. [Matriz](../product/functional-gap-analysis.md) registra cobertura parcial/ausente e decisões vigentes; recursos físicos, lembretes, transferência independente e indicadores por pessoa permanecem lacunas. Sem presumir todos os novos módulos ou alterar D02.

PostgreSQL confirma 5 → 3 → 5 pessoas em dias adjacentes. Formulário carrega a semana da loja ao sair da herança, com orientação de folga/proteção de reservas. [Direção e padrões UX](../ux/visual-review.md): fotografia identificada, composição editorial e jornada numerada; topo para tutor, lateral agrupada para equipe, atalhos/menu acessível em celular. Case recebeu captura com origem; mídia P08 permanece histórica.

Check 115 Python + 18 React; E2E com novo build: 15 aprovados + skip singleton previsto. Staging TLS preservou mesma demo; 16 checkpoints da revisão, onboarding com 4 avisos SMTP e player aprovados. Desempenho final 9/9: LCP 2424 ms, INP 56 ms, CLS 0,0011783. Primeira rodada/falha de classificação do 401 esperado registrada, sem relaxar metas. [Evidência](../evidence/Product-review.md). PR #9 incremental em rascunho sobre P04; checks do commit exato registrados no PR. Próximo gate: revisão humana; escala coletiva/transferência são recomendações para priorização. D10, leitor de tela e aceite final pendentes.

Na CI, corrigidos seletor do título visível no ensaio móvel e período padrão da auditoria (UTC, separado do dia da loja nas métricas). Dois testes de regressão na passagem de data elevam a suite React a 20 aprovados; lint/tipos/build aprovados. Ensaios locais dos três perfis e retorno à área correta passaram. Falhas e correções registradas na evidência; aguardar os checks do commit final antes de declarar a candidata aprovada.
