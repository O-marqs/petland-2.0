# Documentação PetLand 3.0

**CURRENT: `main`, release final de portfólio/demo `3.0.0`, schema `0007_product_operations`.** [Notas finais](release/3.0.0.md) e [registro de fechamento](evidence/Portfolio-closure.md). Produção comercial não declarada; aceite humano/leitor de tela e gates D10 permanecem pendentes. Discovery, mídias e medições conservam sua versão/SHA de origem, incluindo o código funcional de referência `2549523`.

**Checkout e execução:** [versão/reprodução](release/reproducibility.md) define a branch atual e os cinco caminhos do [README](../README.md). [Auditoria de clone, ambiente, demo e pacote](evidence/Reproducibility-review.md). Branches avançam; evidências e mídias conservam o SHA em que foram produzidas.

## START HERE

| Leitura                                           | Para quê                                                                                      |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| [Product Overview](product/product-overview.md)   | Problema, três perfis, jornadas, escopo e limites em cerca de cinco minutos.                  |
| [Architecture Overview](architecture/overview.md) | Monólito modular, camadas, concorrência, implantação atual e evolução não implementada.       |
| [Case Study](case/README.md)                      | Problema, decisões, engenharia e jornada final com proveniência; P08 separado como histórico. |
| [Quick Start](runbooks/local.md)                  | Clone correto, Docker, acesso e verificações locais.                                          |

## PRODUCT

- [Visão do produto implementado](product/product-overview.md).
- [Decisões D01–D12](product/decisions.md).
- [Dor → cobertura → lacuna → prioridade](product/functional-gap-analysis.md).

## UX

- [UX atual: identidade, jornadas, navegação, mobile e oito capturas](ux/PetLand_3.0_UX_Final.md).
- [Design system efetivo e referências de código](ux/design-system.md).
- [Proveniência das capturas atuais](ux/media/current/capture.json).
- [Revisão visual pós-P08](ux/visual-review.md), [imagem editorial e origem](ux/editorial-image.md).

## ARCHITECTURE

- [Overview](architecture/overview.md), [dados/DER/garantias/JSONB](architecture/data-model.md).
- [Sete diagramas atuais: Draw.io editável, SVG e Mermaid](architecture/diagrams/README.md).
- [Contratos HTTP](architecture/api.md), [segurança/autorização contextual](architecture/authorization.md).
- [Índice de ADRs: status, motivo e consequência](adr/README.md).
- [RNFs: Target / Measurement / Evidence / Limitation](architecture/non-functional-requirements.md).

## ENGINEERING

- [Execução e qualidade local](runbooks/local.md).
- [OpenAPI gerado](../packages/api-contract/openapi.json), [migrations](../apps/api/migrations/versions).
- [CI](../.github/workflows/ci.yml), [fitness functions](../scripts/check_architecture.py).
- [Metadata e gates](release/candidate.json), [qualidade incremental](release/quality-report.md).
- [Auditoria documental e verificações desta revisão](evidence/Documentation-review.md).
- [Reprodução, licença ausente e higiene do pacote](release/reproducibility.md), [resultados do clone limpo](evidence/Reproducibility-review.md).

## RUNBOOKS

| Tarefa                                           | Guia                                                      |
| ------------------------------------------------ | --------------------------------------------------------- |
| Executar/desenvolver                             | [Local](runbooks/local.md)                                |
| Conta, caixa de e-mail, convite e admin          | [Identidade](runbooks/identity.md)                        |
| Tutor/pet/catálogo                               | [Cadastros](runbooks/catalogs.md)                         |
| Disponibilidade/reserva/configuração             | [Agenda](runbooks/scheduling.md)                          |
| Execução/notas/gestão                            | [Operação](runbooks/operations.md)                        |
| Painel/escala/pools/transferência/cuidado/avisos | [Evolução operacional](runbooks/operational-evolution.md) |
| Testar os três perfis pessoalmente               | [Aceite manual](runbooks/manual-acceptance.md)            |
| Benchmark/leitor de tela                         | [Qualidade](runbooks/quality.md)                          |
| TLS/demo/backup/restore/incidentes               | [Recuperação](runbooks/operations-recovery.md)            |
| Revisar/gravar/empacotar localmente              | [Release](runbooks/release.md)                            |

## FINAL PRESENTATION

[Case final](case/README.md) · [Player](case/index.html) · [Roteiro](case/presentation-script.md) · [Transcrição](case/final-transcript.md) · [Capturas/proveniência f3d70a2](case/media/final/capture.json) · [Evidência](evidence/Final-case.md).

## HISTORY / EVIDENCE

**Discovery preservado:** [plano consolidado integral](product/PetLand_3.0_Plano_Consolidado.md), [Caderno UX original PDF](ux/PetLand_3.0_Caderno_UX.pdf). Não representam automaticamente o estado implementado.

**História:** [baseline 2.0](migration/baseline.md), [pedidos/progresso](implementation/progress.md), [visão antiga de arquitetura](architecture/README.md), [Mermaid P08](architecture/release-diagrams.md), [notas da candidata P08](release/3.0.0-rc.1.md).

**Evidências por referência:** [P01](evidence/P01.md), [P02](evidence/P02.md), [P03](evidence/P03.md), [P04](evidence/P04.md), [P05](evidence/P05.md), [P06](evidence/P06.md), [P07](evidence/P07.md), [P08](evidence/P08.md), [onboarding](evidence/Onboarding.md), [revisão de produto](evidence/Product-review.md), [evolução operacional](evidence/Operations-evolution.md).

**Mídia:** [player local/vídeo P08](case/index.html), [transcrição](case/transcript.md), [capturas atuais separadas](ux/PetLand_3.0_UX_Final.md#antesdepois-e-proveniência). Números de fases/capturas antigas não são renomeados como novos. As fases registradas são P01–P08 e incrementos posteriores; número de PR não cria uma fase adicional.
