# PetLand 3.0 — um CRM de pet shop com agenda verificável

Case de portfólio de Lucas Marques. **Candidato 3.0.0-rc.1, ambiente local e dados fictícios.** P08 prepara a entrega para revisão; publicação externa e aceite final não estão declarados concluídos.

**Leitura atual:** [produto implementado](../product/product-overview.md), [arquitetura](../architecture/overview.md), [UX e oito capturas atuais](../ux/PetLand_3.0_UX_Final.md), [metas/medições/limites](../architecture/non-functional-requirements.md). O vídeo/`after-*` são históricos P08; `review-home.webp` e `operations-dashboard.webp` são snapshots posteriores com seus próprios manifestos, não novas capturas desta revisão. Somente `docs/ux/media/current` corresponde à captura funcional `2549523` desta documentação.

Revisão posterior de produto/identidade: [matriz completa de dores](../product/functional-gap-analysis.md), [navegação e direção visual](../ux/visual-review.md) e [evidências](../evidence/Product-review.md). A capa atual do case usa uma nova captura real em `media/review-home.webp`, com origem em `media/visual-review.json`. As imagens `after-*` e o vídeo a seguir continuam representando a entrega P08, anterior à revisão visual; sua proveniência não foi alterada.

## O problema

O PetLand 2.0 nasceu como sistema acadêmico em Flask/MySQL. O diagnóstico do commit preservado encontrou SQL junto às rotas e modelos, contratos divergentes, referências por CPF, operações sem proteção suficiente de propriedade e disponibilidade calculada por contagem de horários. A interface mostrava a intenção de autoatendimento, mas não comprovava uma reserva protegida sob concorrência. [Diagnóstico e trechos do código](../product/PetLand_3.0_Plano_Consolidado.md#21-evidências-do-código-e-escopo-auditado), [baseline](../migration/baseline.md).

O trabalho foi reconstruir o fluxo de uma única loja: o cliente escolhe pet, serviço e horário; o servidor escolhe uma pessoa apta e conserva o preço e a duração contratados. A equipe registra o atendimento e publica um resumo. A administração consulta indicadores e configura a capacidade sem invalidar reservas existentes.

## Quem usa e o que foi decidido

Personas são hipóteses de produto, sem alegação de pesquisa com operadores reais. O tutor quer encontrar um cuidado compatível e saber se a reserva foi confirmada. A equipe precisa consultar a agenda, atender e comunicar alterações. O administrador precisa gerir acessos, recursos, expediente e indicadores. Lucas definiu o contexto como demonstração de portfólio, autorizou os três perfis, serviços por porte, profissional atribuído pelo servidor, confirmação explícita e ausência de taxas. [Decisões D01–D12](../product/decisions.md).

## Antes e depois, com proveniência

| Comparação | 2.0 | 3.0 candidata |
|---|---|---|
| Acesso | [Template de login isolado](media/before-login.png) | [Login real da aplicação](media/after-login.png) |
| Reserva | [Template de agendamento isolado](media/before-booking.png) | [Resumo real antes da confirmação](media/after-booking-review.png) |
| Operação | Contratos e estados diagnosticados no código | [Atendimento concluído](media/after-employee-completed.png) |
| Histórico móvel | Sem captura dinâmica equivalente alegada | [Resumo público a 320 px](media/after-customer-mobile.png) |
| Configuração | Sem ensaio de impacto equivalente alegado | [Fechamento bloqueado por reserva existente](media/after-admin-impact.png) |

As capturas 2.0 vêm de **`3cc3f898cde896b80fed587bf8c06f4aa46742f6`**, com hashes em [proveniência](media/before-provenance.json). Apenas dois templates e sua imagem pública foram lidos pelo Git. Links/forms ficaram inativos, scripts/estilos externos foram retirados, flashes ficaram vazios, opções/data receberam valores fictícios e foi acrescentado um aviso. As fontes usam fallback do sistema. Não foi executado o aplicativo legado, acessado MySQL ou alegado um fluxo antigo funcional. Capturas de login/reserva usam 1280×900 nos dois lados; a captura móvel é explicitamente diferente.

O “depois” é a aplicação implementada, servida por Nginx/TLS, com API/PostgreSQL e identidades verdadeiras da demo. Os wireframes do Caderno UX não são usados como evidência de implementação. Imagens/build de trabalho e limites no [registro da gravação](media/capture.json).

## Três jornadas demonstradas

[Assistir com legendas e transcrição](index.html), [vídeo WebM](media/petland-3.0-demo.webm), [legendas](media/petland-3.0-demo.vtt), [transcrição](transcript.md). Vídeo de aproximadamente **3 min 05 s**, sem áudio, sem cortes ou aceleração, com capítulos e dados fictícios.

1. Cliente autenticado cadastra Nala pela interface, escolhe serviço/horário, confere preço e duração e confirma a reserva. O novo pet e a reserva são consultados na API para comprovar persistência.
2. Funcionário encontra a mesma reserva, registra chegada, anota informação interna, aguarda o horário real, inicia e conclui com resumo público. Cliente consulta a mesma reserva concluída; a nota interna é ausente tanto da interface quanto do payload público.
3. Administrador consulta indicadores, propõe fechar uma data com reserva futura e vê a alteração bloqueada. A consulta de impacto não altera versão/configuração nem cancela a reserva. A trilha de auditoria encerra a demonstração.

Preparação declarada: autenticação pela API antes de filmar, serviço fictício de cinco minutos, passo de um minuto e exceção de expediente para o dia. Uma segunda reserva futura é criada pela API própria do cliente para o ensaio de impacto. Não são padrões comerciais nem atalhos de produção. A reserva filmada e suas transições usam o relógio real do servidor; não há endpoint de teste ou relógio simulado. **14 checkpoints** de captura passaram axe/reflow nos critérios exercitados; isso não substitui o aceite humano com leitor de tela.

## Escolhas de engenharia

| Escolha | Motivo e limite |
|---|---|
| Monólito modular com domínio/application separados | Uma loja não justificou serviços distribuídos. Ports/adapters isolam persistência e comunicação; imports são verificados na CI. |
| PostgreSQL + Alembic | Intervalos e duas exclusões GiST protegem ocupação de pet/recurso. Migrations e grants têm ensaio real; SQLite não valida essas invariantes. |
| Primeiro lock do estabelecimento | Simplifica a ordem de locks e preserva atomicidade de reserva/configuração. É uma escolha deliberada de contenção; não há alegação de escala ilimitada. |
| Sessão opaca + CSRF + autorização contextual | Papéis vêm do servidor e cada objeto tem proprietário. Conta, tutor e pet têm identidades próprias; CPF não é identidade pública. |
| Snapshot, idempotência e outbox | Mudança posterior de preço não reescreve contratação; resposta perdida não duplica reserva; commit não é confundido com entrega de e-mail. |
| React, TypeScript e TanStack Query | Formulários/erros e estado remoto usam contratos gerados. UI compartilha tokens; cliente acolhedor e back office compacto. |
| Staging estático isolado e restore em banco novo | Seed/reset e recuperação preservam desenvolvimento/origem. Backup autenticado é ensaiado, mas permanece no mesmo host por D10. |

[Contexto, containers e transação](../architecture/release-diagrams.md), [DER e dicionário](../architecture/data-model.md), [API](../architecture/api.md), [autorização](../architecture/authorization.md), [ADRs](../adr/README.md).

## Resultados medidos e limites

A CI da P07 passou **114 testes Python, 15 React e 15 E2E**, com um skip mobile previsto; duas execuções repetiram instalação limpa, carga e recuperação. O ensaio Linux reconciliou **23 tabelas** e verificou três perfis na origem, cópia e retorno. Com 100 mil agendamentos e 20 sessões, 200 reservas retornaram 201; p95 de reserva **440,73 ms**, maior p95 de leitura **255,87 ms**, dentro das metas 800/400 ms. [Execução de referência](https://github.com/O-marqs/petland-2.0/actions/runs/36905134678). Resultados da candidata P08 ficam nos checks do seu PR, sem reaproveitar números como nova medição.

Laboratório móvel P06: nove amostras, LCP máximo 2028 ms, INP máximo 88 ms, CLS máximo 0,00119. Não são métricas de campo. Não há benchmark comparável do 2.0 e, portanto, **não há percentual de melhoria alegado**. [Relatório de qualidade e rastreabilidade](../release/quality-report.md).

## O que falta para promoção

Aceite final de produto e revisão humana com leitor de tela continuam pendentes. D10 adia provedor, domínio, e-mail externo, publicação, cópia de backup fora do host e metas produtivas. As gravações/capturas publicadas usam dados fictícios; isso não afirma que um banco local de teste pessoal nunca contenha dados fornecidos pelo autor. Sem multiempresa, pagamentos ou importação histórica; D08/D12 dispensam esta última. Ferramentas não fazem tag/release estável, merge ou deploy automático. [Candidato e procedimento de promoção](../runbooks/release.md).

O repositório preserva a baseline, as alterações locais do legado, fontes recebidas e o histórico incremental. A evolução é demonstrada pelas jornadas, constraints e ensaios reproduzíveis; este case não apresenta o candidato como serviço comercial em operação.

## Incremento operacional posterior à gravação

O vídeo P08 é histórico e permanece intacto. O case acrescenta captura separada do painel diário real, com origem em `media/operations-evolution.json`, para mostrar agenda pessoal/equipe, pendências e carga. O incremento autorizado traz escala coletiva, pools físicos, transferência independente, contexto crítico/anterior e avisos programados/de conclusão. Resultados atuais e limites ficam em [Operations-evolution](../evidence/Operations-evolution.md); a referência P07 acima não é nova medição. Reserva em grupo, serviço alterado durante execução, períodos de férias, recepção em tela única, recorrência e D10 continuam lacunas explícitas.
