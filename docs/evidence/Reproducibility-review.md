# Auditoria de reprodução e entrega

Pedido: [texto humano integral](../implementation/Reproducibility-review-request.txt). Incremento documental/configuracional sobre `4ef44e03ce4601b753767bfe65fee1d55283f7be`, sem funcionalidade, migration, alteração de contrato ou dependência. A referência de execução é [versão/reprodução](../release/reproducibility.md).

## Fonte de verdade recebida

Snapshot remoto de 02/10/2026, conferido após fetch: `main` em `3cc3f898cde896b80fed587bf8c06f4aa46742f6` (legado); onboarding em `d564114b2268abed217910020801bf3e4202bf3f` (PR #10 integrado, funcional equivalente a `25495230b75e06ef61b52b8751c76ef9b280dfd1`); portfolio-docs em `4ef44e03ce4601b753767bfe65fee1d55283f7be` (PR #11 rascunho, base onboarding, CI aprovada). PR #9 continua aberto sobre P04. Branch incremental desta auditoria: `petland-3.0-reproducibility`, base portfolio-docs; nenhum merge, tag ou release.

Baseline CI: [run 37033856604](https://github.com/O-marqs/petland-2.0/actions/runs/37033856604), três jobs aprovados no HEAD `4ef44e0`. A reprovação de p95 do commit anterior permanece em [evidência própria](Documentation-review-api-ci-attempt-1.json); não foi ocultada ou reapresentada como aprovação.

## Inconsistências e correções

| Achado | Correção |
|---|---|
| README clonava portfolio-docs; runbook clonava onboarding, sem a documentação consolidada. | Uma branch indicada para entrada, tabela de snapshots/SHAs e replay por commit do manifesto. |
| Runbook de release atual ainda descrevia P08/schema 0006. | Guia atual em 0007; notas e capturador P08 identificados como históricos. |
| Identidade descrevia pets/reserva/gestão como futuros; roteiro de escala priorizava a alternativa individual. | Fluxos atuais e equipe coletiva por data como caminho principal. |
| Requisitos host de demo/testes misturados ao caminho Docker mínimo. | Cinco caminhos, versões, rede, portas, Mailpit, contas/CA geradas e isolamento documentados. |
| Nome Compose igual em dois clones compartilha identidade/volume. | Override nativo `COMPOSE_PROJECT_NAME`; portas continuam fixas e precisam ser liberadas. |
| Pacote conferia hashes, mas não comentário Git/entradas duplicadas e alguns arquivos privados. | Guards compartilhadas: caminhos/segredos conhecidos, comentário do commit, duplicatas, inventário e hashes; oito testes de rejeição. |
| Ignore não cobria várias chaves/bancos/dumps/artefatos. | Proteções em Git/Docker; sem arquivos privados existentes removidos ou versionados. |
| Sem licença geral explícita. | Ausência e recomendação registradas; nenhum LICENSE escolhido em nome do autor. |

## Ambiente e clean-start executados

Windows/PowerShell, Docker Linux/WSL. Launcher Python **3.11.9**, Python de projeto **3.13.15** obtido pelo uv **0.12.18**; Node **22.14.0**, pnpm **10.34.5** instalado do npm somente neste clone; PostgreSQL **17.11**, Docker cliente/server **28.0.4**, Compose **2.34.0-desktop.1**. A versão global de pnpm 11 encontrada no host não foi usada nem alterada. Lockfiles, digests e ferramentas do projeto mantidos.

Clone remoto independente em `Documents/GitHub/petland-3.0-clean-review-20261002`, HEAD recebido `4ef44e0`. Inicialmente sem `.env`, `.local/staging`, `.tools`, venv ou node_modules. Nenhuma configuração, certificado, conta, dump ou credencial do autor foi copiada. Registries/rede e caches normais de ferramentas/imagens foram usados: não é medição sem cache nem teste de ambiente offline.

Comandos efetivamente executados na raiz desse clone:

```sh
git clone --branch petland-3.0-portfolio-docs https://github.com/O-marqs/petland-2.0.git petland-3.0-clean-review-20261002
cd petland-3.0-clean-review-20261002
python scripts/dev.py init
python scripts/dev.py init
python scripts/dev.py up
npm install --prefix .tools pnpm@10.34.5
# PATH do processo aponta para a instalação recém-baixada, conforme o guia.
python scripts/dev.py install
python scripts/dev.py check
python scripts/dev.py e2e
python scripts/check_documentation.py
python scripts/release.py check
python scripts/dev.py down
```

Projeto Compose próprio `petlandcleanapp20261002`; portas do desenvolvimento anterior liberadas por pausa, sem apagar volumes. `init` gerou senhas, eliminou os marcadores e a segunda execução preservou o hash do arquivo. `up` construiu imagens; migration job saiu **0**, banco começou com **0 contas, 0 pets, 0 reservas**, schema **0007_product_operations**. HTTP **200** em live/ready da API, React, ready pelo proxy e info do Mailpit. E2E observou mensagens SMTP reais, cadastro/confirmar/login/recuperar, pet/catálogo e convite/permissões.

Resultado do `check`: Ruff/format/mypy/arquitetura/scan/contratos/build aprovados, **128 Python** com PostgreSQL real e **20 React**. E2E: **15 pass + 1 skip mobile previsto** para primeiro administrador singleton; não é integração omitida. Logs privados em `.local/clean-start`, sem contas/segredos exportados.

Incidente do orquestrador de auditoria: ao retomar os containers anteriores, `compose start --wait` foi recusado pela versão instalada. Usado `compose start` e depois verificados readiness/Mailpit HTTP 200 e contagens originais; serviços/dados preservados. Não é falha de `dev.py up` (o `up --wait` documentado é suportado). Nenhuma alteração de Docker/WSL/reset de fábrica foi necessária.

## Demo e recuperação em clone independente

No mesmo clone, staging começou sem arquivos locais, usando `petlandcleanstage20261002` e volume novo. Executados `staging-init` duas vezes, `staging-up`, `seed-demo` duas vezes, `smoke-demo`, `reset-demo --confirm petland_demo`, `smoke-demo`, instalação de Chromium, `rehearse` e `staging-down`. `staging-init` gerou CA/chaves/configuração e quatro contas próprias; repetição preservou hashes da configuração/contas. Repetição do seed preservou contagens, sem duplicação.

TLS verificado com CA gerada, PostgreSQL verify-full, SMTP STARTTLS real, seis deep links estáticos, cookies seguros, autorização/propriedade/notas privadas, conflito de capacidade e idempotência persistida aprovados. Reset criou outro banco demo, preservando a origem. Backup autenticado/criptografado, restore em banco novo, reconciliação e ativação passaram; navegação dos três perfis a 320 px aprovada na origem, cópia e retorno (**nove checkpoints**). Banco original voltou a ficar ativo.

Staging pessoal anterior foi pausado somente para liberar portas; ao final, retomado com as mesmas imagens, ponteiro de banco e contagens. Volume de ensaio preservado, nenhum `down --volumes`. Relatório completo, contas, certificados e backup permanecem privados em `.local/staging`; resumo público usa somente campos permitidos em [JSON de execução](Reproducibility-review.json).

## CI e limites de verificação

Os três jobs existentes permanecem: **checks**, **browser**, **operations**. Checks cobre Ruff/format/mypy/fronteiras/scan/links/diagramas/candidata, pytest com PostgreSQL/migrations, lint/typecheck/format/unit/contratos/build React, advisories e carga API prevista de **100 mil reservas/20 sessões**. Browser constrói um ambiente limpo e executa E2E. Operations constrói staging, seed/reset, backup/restore, origem/cópia/retorno, três perfis, onboarding, operação/SMTP/reflow e player. Oito testes de ferramenta entram na etapa existente; não foram criados jobs artificiais.

Benchmark de latência web é laboratório manual, não etapa de CI. O checkpoint de relatórios da automação operacional não mede p95; não reinterpretar seu nome como benchmark. As [medições e limites anteriores](../architecture/non-functional-requirements.md) continuam válidos para seus commits/ambientes; este ensaio não mede desempenho produtivo.

Pacote local exige árvore limpa e usa Git archive do commit, inventário e SHA-256. A nova ferramenta verificou o bundle anterior `4ef44e0` de **395 arquivos**, sem achar dados privados. Guards reduzem riscos de caminhos/formatos/assinaturas conhecidos; não substituem revisão de PII, auditoria de segredos em todo o histórico ou assinatura externa. Pacote não inclui `.git`; reprodução de staging/histórico usa clone Git.

Aceite humano de produto/leitor de tela e decisão de licença permanecem pendentes. D10 ainda adia ambiente público, provedor SMTP externo, custódia/backup fora do host e SLO/RPO/RTO. E-mails deste ensaio ficaram no Mailpit. Nenhuma publicação/tag/merge/release final foi realizada.
