# Revisão funcional, identidade e navegação — evidência

Executada em 01/10/2026 após o [pedido humano](../implementation/Product-review-request.md), sobre P08 integrada e a correção de onboarding. Continuidade no PR #9 em rascunho, base `petland-3.0-p04`; título/descrição refletem o escopo final. Commit exato e CI nos checks do PR; execução anterior não aprova um commit posterior.

## Entrega

[Matriz funcional](../product/functional-gap-analysis.md) para tutor, funcionário, gestão, perguntas de negócio e recepção: cobertura, limitações, prioridade, conflitos com D02 e equipe por data. **Não declara todas as dores resolvidas.** [Revisão visual](../ux/visual-review.md): diagnóstico, fontes primárias, fotografia editorial, jornada em linhas, áreas do tutor/serviços/pets e operação legíveis. Topo para tutor, lateral agrupada para equipe e atalhos/menu acessível em celular. Conta acessível, Escape/foco, fechamento por rota e estado ativo também na rota original da agenda.

Calendário próprio começa com a semana atual ao sair da herança da loja; orientação para folga pontual e reservas afetadas. Nenhum contador coletivo ou regra comercial nova. Case ganhou captura real e estilos/fontes locais, com licença da fonte e [origem da imagem gerada](../ux/editorial-image.md). Capturas `after-*`, vídeo/legendas e proveniência P08 permanecem históricos, explicitados na página.

## Verificações executadas

| Verificação | Resultado |
|---|---|
| `python scripts/dev.py check` | **115 Python + 18 React aprovados**; PostgreSQL de teste, migrations, arquitetura, scan, lint/tipos/format, contratos e build |
| Capacidade diária nova | Cinco pessoas; **5 / 3 / 5** reservas simultâneas em dias adjacentes; próxima solicitação recusada e pessoas ausentes não alocadas |
| `python scripts/dev.py e2e`, após reconstruir com o novo código | **15 aprovados + 1 skip previsto** do bootstrap singleton mobile; primeiro acesso, CRM, reserva, operação/histórico, gestão, permissões e teclado/reflow |
| `python scripts/dev.py smoke-demo` | TLS estrito, mesma demo e serviços saudáveis |
| `review-staging.mjs` | **16 checkpoints**: 12 contextos/viewport com axe/reflow (público/tutor/equipe/admin × 1440/768/320 px); 3 navegações com teclado/Escape/foco/rota/reload/papel; editor de folga mantém semana normal sem salvar/sem mutações HTTP |
| `onboarding-staging.mjs` | Conta nova UI → SMTP → confirmação → contato → pet persistido → reserva → mesma reserva na equipe → reagendamento/cancelamento; **4 mensagens SMTP** e 9 checkpoints UI |
| `verify-portfolio.mjs` | **1280/320 px**, links locais, vídeo/legendas/capítulos, axe, reflow e ausência de erro JavaScript |
| Revisão visual manual | Capa ampla, tutor móvel, agenda desktop e case desktop/móvel inspecionados; sem sobreposição/rolagem horizontal nos recortes |
| React, lint/tipos/build após ajustes finais | Hooks estáveis, estado de menu ligado à rota, sem efeitos desnecessários, fronteiras shared/features e consultas TanStack preservadas; verificações aprovadas |

Registros privados: `.local/product-review/check.log`, `e2e-final.log`, `after/report.json`, `tls-smoke.log`, `performance-final.json`; onboarding em `.local/staging/browser/onboarding`; player em `.local/p08/player-verification.json`. Sem senhas na documentação pública. Captura e hashes em [visual-review.json](../case/media/visual-review.json).

## Desempenho e ajuste do roteiro

Build de produção, Chromium/Pixel 7, cache frio, CPU 4×, latência 150 ms, download 1,6 Mbps/upload 750 kbps; três amostras de início, entrada e catálogo. Rodada final: **9/9 dentro das metas**, LCP máximo **2424 ms**, INP **56 ms**, CLS **0,0011783**, sem erro inesperado/CSP. Metas mantidas: 2500 ms / 200 ms / 0,1. Laboratório, não dados de usuários em produção ou ganho comparável ao legado.

A primeira rodada, simultânea às verificações de navegador, falhou: uma home marcou **2512 ms**, e o roteiro tratou como erro toda consulta de visitante sem sessão. Não se assumiu causalidade exclusiva da execução simultânea. A rodada isolada passou; LCP próximo do orçamento exige repetir a medição em futuras mudanças de imagem/JS.

O link público da conta, introduzido na correção anterior, consulta `GET /api/v1/auth/me`; visitante sem sessão recebe **401 esperado**. O benchmark registra isso separadamente somente com URL exata, GET, resposta real 401 e entrada correspondente no console. Outros erros, inclusive 401 de outro endpoint, continuam reprovando. API e metas não foram relaxadas. Resultado final: um 401 esperado por amostra, zero erros inesperados.

## Dados e limites

Reconstruções preservaram bancos/volumes. Mesma demo ativa `petland_reset_b5251a7c6b514bd8bfe351b7f0bf37ec_demo`; nenhum reset/restore nesta revisão. Escala testada em PostgreSQL efêmero; formulário abandonado; onboarding cria seus registros sintéticos e cancela sua própria reserva mantendo histórico.

Plano/PDF oficiais e checkout legado preservados. Sem migration comercial, alteração de D02/D03, merge/main/tag estável, publicação, provedor ou recurso pago. Foto gerada é asset identificado de marca. Candidata permanece `production_ready=false`; aceite humano/leitor de tela e D10 pendentes. Escala coletiva e transferência independente são próximas recomendações, não fases entregues nesta revisão.
