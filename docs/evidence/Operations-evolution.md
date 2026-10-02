# Evolução operacional — comportamento, provas e limites

Pedido humano permite implementar lacunas prioritárias e exercer julgamento de produto, inclusive painel do backoffice. Base `18c8945`, incremento em `petland-3.0-operations-evolution`, PR incremental sobre `petland-3.0-onboarding-fix`. D02/D03/D04/D10 preservados. Não houve merge/main/tag/publicação. [Autorização](../implementation/Operations-evolution-request.md), [matriz atualizada](../product/functional-gap-analysis.md), [ADR-016](../adr/0016-operational-evolution.md).

## Resultado funcional

| Dor | Entrega e limite |
|---|---|
| O que fazer hoje? | Painel diário com próximos cuidados pessoais/equipe, contagens, pendências atuais, carga e ações. Sem dados fictícios no dashboard; demo identificada é persistida no banco. |
| Só nesse dia há menos pessoas | Escala coletiva por data com períodos, motivo, quantidade efetiva e prévia; remove exceção para restaurar herança. Calendário da loja continua limitando. |
| Há pessoal mas não banheiras/mesas | Pools físicos configuráveis por serviço, com limite concorrente e impacto protegido. Consumo pelo intervalo inteiro, sem etapas ou equipamento específico. |
| Outra pessoa assume | Transferência independente em confirmado/chegou/em execução; aptidão/calendário/conflitos, motivo e antes/depois estruturados. Contrato e histórico preservados; sem lote. |
| Alergia/contexto esquecido | Campos separados de restrição crítica e manejo; alerta e confirmação da versão lida antes do início. Três cuidados anteriores com notas internas limitadas e link completo. |
| Esqueci / pet está pronto | Antecedência configurável para novos avisos; outbox descarta lembrete obsoleto e avisa conclusão. Estado SMTP consultável, sem alegar entrega/leitura externas. |
| Quantos cada pessoa concluiu / duração? | Concluídos por responsável final, serviços, duração/atraso/desvio, cancelados/faltas e pets/clientes únicos. Sem divisão de esforço, ranking ou receita presumida. |

## Verificação executada

Check final local: **125 Python e 20 React aprovados**, com lint/tipos/contratos/build/arquitetura, migrations e downgrade protegido. Dez cenários novos exercitam escala, capacidade, distribuição, transferência, contexto crítico/anterior, métricas, comunicação e compatibilidade. CI do commit exato consta no PR e relatórios locais, sem transformar esse registro em aceite humano.

PostgreSQL isolado verifica concorrência de três solicitações com duas banheiras, adjacência, cancelamento liberando capacidade e redução recusada. Escala reduz cinco para três somente numa data; dia adjacente permanece com cinco, restauro remove exceção e passa a herdar a semana alterada. Transferência protege alvo ocupado, mantém preço/tempos, repete resposta idempotente, preserva autoria e oculta motivo do tutor. Relatório confirma 42 minutos reais, 11 de atraso e −18 de desvio, atribuindo ao responsável final. Leitura crítica velha é recusada sem avançar estado; notas anteriores privadas permanecem ausentes da projeção pública. Worker confirma aviso devido uma vez no cenário normal, descarte de horários antigos e ausência de nota interna no aviso de conclusão.

E2E de desenvolvimento: **15 aprovados e um skip mobile previsto** do provisionamento singleton; inclui início com leitura crítica, operação, histórico público, gestão, sessões e SMTP reais. HTTPS local novo: escala/capacidade a 1440/320 px, cadastro do pet com restrição, reserva pela interface, transferência, painel e conclusão/relatório passaram com axe/reflow e nenhum erro JavaScript. Lembrete foi capturado no horário real e aviso de pronto chegou ao Mailpit; nota interna ausente da mensagem e interface/payload públicos. Regras temporárias foram restauradas e registros sintéticos preservados. O roteiro adicional confere contexto anterior após a conclusão; resultado detalhado em `.local/staging/browser/operations-evolution/report.json`.

Falhas encontradas e corrigidas: contrato de saúde precisava incluir seis caminhos novos; confirmação considerava apenas conflitos para calcular carga diária (corrigida para agregação SQL do dia); seletor do roteiro de manejo diferia do rótulo real; serviço sintético ativo alterava a contagem fixa do smoke (cleanup passou a inativar somente o serviço do próprio ensaio); teste isolado de pools precisava dos instantes exigidos no domínio. Não se afrouxaram regras, metas ou autorização para fazê-los passar.

## Desempenho e preservação

As primeiras medições locais de carga reprovaram metas, inclusive em leituras anteriores: relatório/captura não foram considerados prontos pelo mero funcionamento. Perfil SQL motivou carga diária agregada na confirmação e uma única agregação de gestão com grupos por pessoa/serviço/total; painel evita métricas detalhadas que não usa. Consultas usam dados atuais sem cache que esconda alterações. [Construção suportada no SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/functions.html#sqlalchemy.sql.functions.grouping_sets). Metas permanecem 400 ms de leitura e 800 ms de reserva com 100 mil reservas/20 sessões. Resultado final e condições são registrados no PR; não reutilizar os números P06/P07 como medição deste incremento.

Banco demo ativo mantido; backup autenticado/criptografado criado antes de aplicar `0007_product_operations`. Backup registra a revisão real do banco (inclusive `0006_hardening` antes da migração); não confunde revisão do código novo com schema antigo. Atualização aditiva mantém dados e volumes, enquanto downgrade protege nova informação. Main/tag/checkout legado/fontes permaneceram preservados. Case recebeu mídia separada do painel; vídeo e capturas P08 continuam históricos.

## Limites e próximos testes humanos

Ainda faltam reserva conjunta de pets/serviços, alteração de serviço na execução, férias por período, redistribuição em lote, console único de recepção, séries de demanda/recorrência/inatividade e rateios de esforço. Preferência de profissional contraria D02; cobrança não entra em D04. Consumo de recursos é conservador, ocupação usa calendários atuais de pessoas, e responsável final recebe a conclusão inteira. Lembrete configurado não recalcula avisos existentes; SMTP pode duplicar após falha/resposta perdida e envio já reclamado pode competir com alteração.

Aceite pessoal de produto e leitor de tela continuam humanos. E-mail externo, hospedagem, custódia/backup fora do host e metas produtivas permanecem D10. Esta entrega não declara todas as dores encerradas nem concede release estável. [Como testar](../runbooks/operational-evolution.md).
