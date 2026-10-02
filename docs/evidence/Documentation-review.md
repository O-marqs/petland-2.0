# Revisão documental para portfólio

**Escopo autorizado em 02/10/2026:** documentação atual, produto/UX/arquitetura, diagramas e evidência visual. [Pedido integral](../implementation/Documentation-review-request.txt). Sem alteração de regra comercial/schema, merge ou publicação de release. Evidências antigas não são reescritas como medições novas.

## Base auditada antes de editar

HEAD inicial limpo: `25495230b75e06ef61b52b8751c76ef9b280dfd1`, branch `petland-3.0-operations-evolution`. Inspeção de arquivos/código/contratos/migrations e API GitHub precedeu a primeira edição. A branch documental `petland-3.0-portfolio-docs` deriva dessa referência funcional.

Em 02/10, [PR #10](https://github.com/O-marqs/petland-2.0/pull/10) já estava merged na branch `petland-3.0-onboarding-fix`, cujo HEAD `d564114b2268abed217910020801bf3e4202bf3f` não tinha diff de conteúdo em relação a `2549523`. [PR #9](https://github.com/O-marqs/petland-2.0/pull/9) estava aberto/draft, base `petland-3.0-p04`. `main` permanece no legado `3cc3f898cde896b80fed587bf8c06f4aa46742f6`; não presumir merge final. São snapshots de estado dos PRs, não monitoramento contínuo.

| Inventário inicial           | Fonte inspecionada / achado                                                                                                                                                       |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| README / portal              | Fase P08 no topo, resumo contradiz incremento no fim, menu de docs orientado às fases.                                                                                            |
| Product (3 arquivos)         | Discovery/decisões/matriz; recepção ainda negava transferência e guia por data priorizava configuração individual.                                                                |
| UX (4 arquivos)              | PDF original, design system P01, revisão visual/proveniência; faltava visão consolidada dos fluxos atuais.                                                                        |
| Architecture (5 arquivos)    | Visão P08, Mermaid, dados/API/autorização; dados tinham schema 0007, mas faltavam detalhes de garantias/JSONB/atribuição.                                                         |
| ADR (9 arquivos)             | Oito documentos + índice; decisões fundacionais resumidas no índice e colisão histórica de número 007.                                                                            |
| Runbooks (10 arquivos)       | Execução, identidade, catálogos, agenda, operação, qualidade, recovery, release, aceite manual e incremento operacional.                                                          |
| Release (3 arquivos)         | Candidata não produtiva, schema 0007/gates pendentes; qualidade mistura referências temporais corretamente, mas faltava consolidar CI final.                                      |
| Evidence (34 arquivos)       | P01–P08, onboarding/revisões/benchmarks/screens; números são evidências de suas respectivas revisões.                                                                             |
| Implementation (12 arquivos) | Pedidos e progress; fases reais P01–P08, seguidas de onboarding/revisão/evolução operacional. PR #10 não é uma fase P10.                                                          |
| OpenAPI                      | **64 paths / 79 operações HTTP**, contrato gerado da aplicação real; sem edição manual.                                                                                           |
| Migrations / dados           | Sete revisions lineares, head 0007; 21 tabelas ORM + Alembic + manifesto offline da demo = 23 no recovery.                                                                        |
| Backend                      | Seis módulos, ports/adapters/casos de uso, contratos `public`, bootstrap; outbox thread por worker, sem broker externo.                                                           |
| Frontend                     | Rotas reais App/AccountLayout, tokens/CSS/componentes, Query/RHF/Zod, carregamento sob demanda. Administração real em `/gestao/acessos`.                                          |
| Infra                        | Dev Vite separado; staging Nginx/TLS, dois workers, PG single-node, Mailpit, migration job e volumes locais.                                                                      |
| Tests / CI                   | Unit/HTTP/PostgreSQL/migrations/React/E2E, scripts HTTPS/restore/carga; jobs checks/browser/operations. Referência funcional passou 128 Python +20 React, seis checks em push/PR. |

## Correções e preservação

- Visões atuais de produto, UX e arquitetura substituem a necessidade de inferir o estado pelo roteiro de fases. README foi preparado **depois** das demais documentações.
- Escala, pools, transferência, alertas/contexto, lembrete/pronto, painel e indicadores por pessoa são implementados; matriz/README não os apresentam como ausentes.
- Guia coletivo por data passa por `/operacao/escala`; a alternativa individual continua documentada. Não basta um número sem identificar pessoas/aptidão/períodos.
- Outbox é processo dentro da API; pools são regras sob lock, não tabelas/equipamentos ou terceira exclusion constraint. Contagem de recovery distingue tabelas comerciais/técnicas/offline.
- RNFs preservam reprovação Windows/WSL e aprovação Linux, datas/métodos/limites. JSONs finais foram extraídos/copiados de medições existentes, com hashes/origem; não chamados de nova carga.
- Clone aponta à branch que contém o incremento integrado, sem afirmar que `main` já contém 3.0. Versão/schema continuam 3.0.0-rc.1/0007, sem bump fictício.
- Nenhum link de arquivo faltante foi encontrado na varredura inicial de Markdown. A validação final também confere anchors/referências; não se inventou uma lista de links quebrados.
- ADR-007 baseline e 0007 cadastros permanecem identificados por título/área; não renumeramos evidência. Não há arquivos ADR-006/010 separados: decisões estão consolidadas no ADR-003.

## Fontes e evidências históricas

| Documento/material                             | Tratamento                                                                                                                                                                 |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plano original                                 | Discovery íntegro, SHA-256 `53b8496a4b1aa50ef2a6a26b86975c03c31729120b0521210148b44f0028f2c0`.                                                                             |
| Caderno UX original                            | PDF discovery íntegro, SHA-256 `7b9a78562b8d23e20c5979655e2a947a88700a151348fce418e89fff93d0f3b8`. Sem PDF “final” inventado, pois não há processo reprodutível existente. |
| Pedidos/progress/evidências P01–P08            | Histórico válido preservado. Novo registro acrescentado, sem transformar antigas contagens em atuais.                                                                      |
| Mermaid P08 / visão antiga de arquitetura      | Semântica preservada, banner temporal e links atuais; dois pontos e vírgulas em texto de sequenceDiagram corrigidos por erro real de parser.                               |
| Vídeo P08/`after-*` e templates 2.0 `before-*` | Intactos; vídeo é fluxo P08 e antes é template isolado, não execução de MySQL/legado.                                                                                      |
| `review-home` / `operations-dashboard`         | Snapshots pós-P08 com seus manifestos originais, sem recaptura silenciosa.                                                                                                 |
| Capturas atuais                                | Oito novos arquivos `*-current.webp` em UX, separados de case/history, com manifesto de proveniência.                                                                      |

## Capturas e diagramas desta revisão

Projeto Docker **petlanddocs** independente, PostgreSQL/volume/rede próprios, loopback 8444/55435/8027, imagens funcionais `25495230b75e`. Usa fixture existente exclusivamente sintético; origem do staging pessoal e seus cadastros não são copiados/alterados. Preparação declarada: escala de uma data futura, pool de duas unidades e alerta de cuidado em Luna demo. Reserva é captura de revisão sem nova confirmação; painel mostra data futura explicitamente. Relógio real, sem endpoint fake.

[Manifesto público](../ux/media/current/capture.json) associa hash/rota/viewport/tempo/imagem às oito capturas. [Script de captura](../../apps/web/scripts/capture-documentation.mjs) guarda dados privados apenas em `.local` e exige fixture/projeto/imagem esperados; nenhuma senha/token é exportada.

[Sete páginas Draw.io/SVG/Mermaid](../architecture/diagrams/README.md) são geradas determinística e localmente do mesmo modelo. XML editável não comprimido; SVGs têm title/desc e fontes de sistema. Mermaid anterior preservado.

## Verificações desta revisão

Resultados locais executados em 02/10/2026, sobre a árvore documental com a mesma fonte funcional `2549523`:

| Verificação                                     | Resultado observado                                                                                                                                                                                                                                                       |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `python scripts/dev.py check`                   | Aprovado: Ruff lint/format, mypy, fronteiras de arquitetura, scan do estado ativo, ESLint, TypeScript, Prettier, contratos gerados e build; **128 testes Python / 20 React**.                                                                                             |
| `python scripts/dev.py e2e`                     | **15 aprovados / 1 skip previsto**, bootstrap administrativo singleton já exercitado no desktop. Cadastro usa confirmação SMTP real no Mailpit; não é recebimento em caixa externa.                                                                                       |
| `python scripts/check_documentation.py`         | Links/anchors locais, originais de discovery íntegros, XML/referências de células, exportações e hashes de oito capturas aprovados.                                                                                                                                       |
| `python scripts/render_architecture.py --check` | Sete páginas, sete SVGs e Mermaid determinísticos; nenhum diff de bytes em regeneração.                                                                                                                                                                                   |
| Mermaid 11.12.0 / inspeção visual               | **14 blocos atuais e preservados** parseados/renderizados; sete SVGs inspecionados. Dois delimitadores inválidos de texto no sequenceDiagram histórico foram corrigidos sem mudar a semântica. Validador/dependência temporários em `.tools`, sem pacote novo do produto. |
| Captura / encoding                              | **16 checkpoints** desktop/mobile, zero violações axe, overflow ou erros JavaScript. Oito PNGs reais convertidos a WebP lossless com igualdade de pixels RGBA; manifesto público conserva proveniência.                                                                   |
| Reprodução / isolamento                         | Preparação, captura com o script final e teardown do projeto `petlanddocs` aprovados; volume conservado. Ponteiro do staging pessoal permaneceu igual; `petland3` e `petland7` continuaram saudáveis.                                                                     |
| `node apps/web/scripts/verify-portfolio.mjs`    | Player histórico aprovado a 1280/320 px: links locais, duração, legendas, capítulos e axe.                                                                                                                                                                                |
| `python scripts/release.py check`               | Versões/schema/mídia/ativos da candidata consistentes; gates humanos e D10 permanecem pendentes. Empacotamento local não publica release.                                                                                                                                 |
| Formatter documental / `git diff --check`       | Documentos atuais e script de captura formatados; whitespace conferido. README dos diagramas permanece na forma gerada para garantir determinismo.                                                                                                                        |
| Ausência de alteração funcional                 | Diff vazio em `apps/api/src`, migrations, `apps/web/src`, `packages/api-contract` e `infra` contra a referência funcional.                                                                                                                                                |

A primeira passagem de lint encontrou quatro variáveis sem uso no novo script de captura. Corrigidas pela seleção explícita dos campos de atualização do pet; check completo e captura foram repetidos e passaram. Não houve relaxamento de regra/teste. Os logs de execução ficam em `.local`; esta evidência registra resultados, não credenciais.

Benchmarks API/web e rehearsal de recovery citados em RNFs continuam vinculados à revisão que os produziu. Esta revisão não executou uma nova carga nem concede aceite humano, certificação de acessibilidade ou aprovação de produção.

## Pendências de produto / operação

Aceite humano dos três perfis/leitor de tela; lacunas da [matriz](../product/functional-gap-analysis.md); limites de [performance/recuperação](../architecture/non-functional-requirements.md); D10/publicação/SMTP externo/off-host/SLO-RPO-RTO. Nenhum merge ou release publicado por esta revisão. Documentação preparada para revisão humana, sem declaração automática de produto finalizado.
