# Fechamento oficial do portfólio — 02/10/2026

[Pedido integral autorizado](../implementation/Portfolio-closure-request.txt). Operação de release/documentação; sem features, migrations, alteração de regras ou dependências. Os próximos registros externos serão comprovados pelo GitHub, sem afirmar ações futuras como concluídas neste snapshot pré-merge.

## Verificado antes da promoção

- Antigo main: `3cc3f898cde896b80fed587bf8c06f4aa46742f6`.
- Branch `legacy/petland-2.0` confirmada exatamente nesse commit; tag histórica anotada já existente preservada (objeto `4a4a63312a08d5fe7f774863ee9f895ab498873a`, commit `3cc3f898...`).
- PR #13: head revisado `afe5606bfd1045a50cac3e1440781b1a6987673e`, diff somente apresentação/docs/ferramentas; CI 37061426075, checks/browser/operations success. Merge commit `968a1451beaa2587764a97d1d257adf597223dff`.
- PRs 10–12 e aplicação `f3d70a2` estão na linha consolidada; capturas/benchmarks/snapshots originais não recebem versão/data novas.

## Alterações de release

Versões ativas npm/Python/FastAPI/OpenAPI 3.0.0, contratos regenerados; metadata portfolio_release e production_ready=false. Guards aceitam o portfólio estável e mantêm compatibilidade RC histórica, sem conceder aceite/publicação. Workflow passa a observar main, mantendo os mesmos jobs/metas. Clone padrão e URLs canônicas usam O-marqs/petland; links históricos de branches removíveis apontam a commits imutáveis. [Auditoria por ocorrência](../release/reference-audit.json).

## Validação local desta branch

`dev.py check` aprovado: lint/formatação/tipos/arquitetura/higiene, contrato gerado/build, **128 Python (incluindo PostgreSQL/migrations) e 20 React**. Sem alteração de dependências; warning Starlette/httpx de TestClient já existente preservado. `check_documentation.py`: 557 links/âncoras, hashes discovery/mídia; `render_architecture.py --check`: sete páginas/SVG/Mermaid consistentes. **13 testes de release** (oito originais + cinco limites de política) aprovados. `release.py check` aprovado, e bundle RC histórico `afe5606` continua verificável com 440 arquivos.

Players final/P08 aprovados em 1280/320 px: ranges, seek em todos os capítulos, legendas, transcrição, links locais, axe/reflow e ausência de erro JS. Nenhuma meta de performance alterada. CI/E2E/recovery e clean clone final serão ligados ao SHA exato pelo recibo externo, sem atribuir medições históricas à 3.0.0.

## Provas externas após este commit

O SHA final de main é criado pelo merge do [PR de release](https://github.com/O-marqs/petland/pulls?q=is%3Apr+%22final+portfolio+release%22). Os três checks devem aprovar o head exato. Rename deve manter a identidade do repositório. Clean clone final deve usar main, init/up, health live/ready e schema 0007_product_operations, preservando ambientes existentes.

Tag anotada v3.0.0 deve apontar exatamente ao main validado. A [GitHub Release](https://github.com/O-marqs/petland/releases/tag/v3.0.0) recebe ZIP/manifesto verificados e **publication.json** somente após publicação real: SHA, tag, CI, clean clone, PRs fechados, branches auditadas/removidas e stable_release_published=true. Assim o relatório final não exige um commit que faria main avançar além da tag. Ledger operacional local não contém credenciais.

PRs 1/2/3/4/9 só são comentados/fechados depois da publicação; seu histórico é preservado. Cada branch removível deve ter zero commits fora de main e tip alcançável por main/tag; diferenças interrompem a exclusão. Não há force push, tag movida ou remoção de commits.

## Limites preservados

D10, SMTP externo, off-host/HA/SLO/RPO/RTO produtivos, leitor de tela/aceite humano e licença geral ausente permanecem explícitos. Falhas reais de benchmark/visual anteriores não foram apagadas. A tag é estável para o portfólio, sem declaração de produção comercial.
