# PetLand — dores, cobertura e lacunas

Revisão solicitada em 01/10/2026, sobre P02–P08 e a correção de primeiro acesso. Este documento avalia comportamentos da aplicação, API, persistência e testes; uma tela ou coluna no banco, isoladamente, não conta como funcionalidade entregue. As propostas do pedido são critérios de avaliação, não uma alteração automática das decisões aprovadas em [decisions.md](decisions.md).

**Conclusão: o núcleo funciona, mas a lista completa de dores não está resolvida.** O produto já suporta uma jornada individual com disponibilidade por pessoa apta, confirmação transacional, operação, histórico e comunicação de alterações. O incremento operacional autorizado acrescenta escala coletiva por data, pools físicos, transferência independente, alertas críticos/contexto anterior, agenda pessoal, lembretes/aviso de conclusão e indicadores por pessoa. As lacunas restantes continuam explícitas; relatórios não equivalem a produtividade ou receita.

Legenda: **Coberto** = comportamento implementado no escopo descrito; **Parcial** = atende parte da dor, com a limitação explicitada; **Ausente** = não há fluxo/contrato para isso; **Decisão** = proposta difere de uma decisão vigente. Prioridade **Alta/Média/Baixa** indica a ordem sugerida para lacunas, não promessa de nova fase. “—” significa manter e verificar, sem expansão necessária para a dor delimitada. A matriz não substitui aceite humano ou uso comercial.

## Tutor / cliente

| Dor | Deveria existir | Cobertura atual e limite | Estado | Prioridade |
|---|---|---|---|---|
| Tem horário sábado às 14h? | Loja aberta, pessoa apta, duração suficiente e nenhum conflito | Loja/escala da data/pessoa, habilidades, duração/buffers, conflitos e pools físicos configurados entram no cálculo. Sem pool configurado, vale a equipe. | Coberto nesse modelo | — |
| Dois pets e vários serviços | Reserva coordenada com todos os intervalos e confirmação conjunta | Vários pets cadastrados e reservas individuais. Cada reserva aceita um pet e um serviço; não há grupo atômico, sequência ou combo configurável. | Parcial | Média |
| Quem vai atender? | Identificar responsável, quando pertinente | A equipe vê a pessoa atribuída. O contrato público não expõe o responsável ao tutor; atribuição é do servidor. | Parcial | Média: decidir exposição |
| Quero sempre a mesma pessoa | Preferência ou escolha de profissional | **D02 determina que o cliente não escolhe profissional.** Preferência persistente não existe e alteraria o produto aprovado. | Decisão | Revisar D02 antes de implementar |
| Preciso cancelar | Autoatendimento dentro da política | Cliente cancela reserva confirmada antes do limite; motivo, autoria e histórico permanecem. Equipe pode ajudar fora do prazo nas condições permitidas. Sem taxas. | Coberto | — |
| Preciso trocar o horário | Reagendar a mesma reserva | Reagendamento transacional com versão/idempotência; falha conserva o original. Não é preciso apagar e recriar. | Coberto | — |
| Meu pet já veio? | Histórico por pet | Reservas/histórico filtráveis por pet; resumo público do atendimento e horários registrados. Não inclui notas privadas. | Coberto | — |
| Shampoo, máquina, corte preferido | Preferências persistentes e execução detalhada | `care_notes` no pet e anotações por atendimento em texto livre. Sem campos de material/máquina e sem ficha estruturada de execução. | Parcial | Média |
| Meu pet tem alergia | Alerta importante no perfil e no atendimento | Campo separado de alergias/restrições críticas, alerta destacado e confirmação da versão atual antes do início. Não é diagnóstico/severidade clínica. | Coberto no contexto operacional | — |
| Esqueci o horário | Lembrete agendado e confirmação | Confirmação + lembrete por antecedência configurável, para novas reservas/reagendamentos; aviso obsoleto é descartado. Não há confirmação de presença pelo tutor. SMTP local. | Parcial | Média: presença / D10 externo |
| Já ficou pronto? | Consultar status e receber aviso de conclusão | Conclusão gera aviso de pet pronto; reserva consulta status/resumo e comunicação, com atualização periódica. Sem push/WhatsApp/provedor externo. | Coberto em SMTP local | Gate D10 externo |
| Quanto vai custar? | Preço antes da confirmação | Catálogo por porte; resumo com oferta do servidor; snapshot conserva o preço contratado. Valor agendado não é receita recebida. | Coberto | — |
| Quanto tempo demora? | Duração estimada | Duração por serviço/porte e previsão na reserva. Buffers internos de ocupação são separados do cuidado contratado. | Coberto | — |
| Abre no feriado? | Exceções reais refletidas na disponibilidade | Datas especiais substituem todo o expediente da data; vazio fecha o dia. Calendário individual intersecta o da loja. | Coberto | — |
| Cadastrar, criar pet e começar | Próxima ação clara após o primeiro acesso | Cadastro → confirmação de e-mail → login → contato → pet → reserva. Onboarding orienta os pré-requisitos; não cria sessão ou contato automaticamente. | Coberto | — |
| Não recebi e-mail pessoal | Comunicação efetiva no ambiente usado | SMTP real e caixa Mailpit local para verificação/reserva/alterações. Entrega externa não foi configurada: D10 adia provedor/publicação. | Parcial | Gate de ambiente antes de publicar |

## Funcionário

| Dor | Deveria existir | Cobertura atual e limite | Estado | Prioridade |
|---|---|---|---|---|
| O que faço hoje? | Agenda pessoal de hoje | Entrada com painel diário, próximos cuidados pessoais/equipe, pendências e carga; agenda usa minha equipe automaticamente, com opção toda a equipe. Sem item explícito de intervalo na linha da agenda. | Coberto nesse recorte | — |
| Cliente chegou antes | Check-in | “Registrar chegada” no mesmo dia local, inclusive antes do horário; início real respeita a regra temporal. `ARRIVED` representa check-in. | Coberto | — |
| Cliente atrasou | Horário real de chegada e atraso claro | `arrived_at` é registrado pelo servidor. Há aviso de ocupação vencida, mas não um fluxo/medida explícita de atraso com motivo. | Parcial | Média |
| Não apareceu | No-show distinto de cancelamento | Estado `NO_SHOW`, tolerância configurável, ação manual e motivo obrigatório. Não converte falta em cancelamento nem marca automaticamente. | Coberto | — |
| Atendimento demorou | Estender ocupação com histórico | Extensão exige motivo, disponibilidade/aptidão e não altera automaticamente outras reservas. Horário previsto permanece; chegada/início/conclusão reais separados. | Coberto | — |
| Comportamento difícil | Observação operacional | Nota interna append-only com autor/data; equipe acessa, tutor não recebe texto privado. Preferência recorrente pode ficar em `care_notes`, com visibilidade de perfil. | Coberto | — |
| Pet tem alergia | Alerta destacado e confiável | Restrição crítica separada de manejo; início exige confirmar a versão atual do pet. Mudança entre leitura/início pede atualização sem avançar o estado. | Coberto | — |
| Preciso saber o que foi feito | Contexto anterior ao executar | Detalhe reúne três últimos cuidados concluídos anteriores, até cinco notas de cada, duração/pessoa e link para histórico completo. Notas privadas não chegam ao tutor. | Coberto com limites de projeção | — |
| Serviço mudou na execução | Mudança controlada de serviço/preço/duração | Oferta contratada é imutável; não existe comando de troca/acréscimo de serviço durante atendimento. | Ausente | Média |
| Terminei | Finalizar e registrar observações | Horário real, nota interna/resumo público separados e aviso de pronto no outbox; estado de comunicação consultável. | Coberto localmente | Gate D10 externo |
| Outra pessoa assume | Transferência independente com elegibilidade e autoria | Ação própria para confirmado/chegou/em atendimento; motivo, pessoa anterior/nova, aptidão/calendário/conflitos e capacidade. Não altera contrato; sem lote. | Coberto individualmente | Média: lote |
| Saio cedo / não trabalho nesse dia | Bloqueio individual por data/horário | Calendário da pessoa tem datas especiais; pode reduzir janela ou fechar um dia. Reservas incompatíveis impedem salvar. Sem gestão coletiva de ausências. | Coberto no modo individual | Média: facilitar escala |
| Férias | Ausência por período | Pode cadastrar exceções dia a dia, até 100 datas. Não há intervalo de férias, motivo de ausência ou ação em lote. | Parcial | Média |
| Quantos pets cada pessoa fez? | Relatório por responsável | Gestão conta cuidados concluídos por responsável final, serviços e médias reais; pets únicos concluídos são contados no conjunto. Transferência não divide esforço entre pessoas. | Coberto nesse modelo de atribuição | — |
| Banhos/tosas/outros, tempo e conclusão por pessoa | Indicadores operacionais | Concluídos por serviço/responsável, média real, atraso e desvio, cancelados/faltas e carga atual. Sem taxa de conclusão calculada ou ranking. | Parcial | Média: denominadores e taxa |

## Gerente / administrador

| Dor | Deveria existir | Cobertura atual e limite | Estado | Prioridade |
|---|---|---|---|---|
| Quantos atendimentos hoje? | Total e distribuição por situação | Gestão consulta período, inclusive um dia, com total e `by_status`. São reservas pelo início previsto e **estado atual**, não eventos ocorridos naquele dia ou pets únicos. | Coberto nesse recorte | — |
| Quem está sobrecarregado? | Carga por pessoa e faixa horária | Painel mostra minutos planejados/capacidade atual por pessoa; gestão mede duração/atraso. Novas reservas priorizam menor carga diária elegível. Sem mapa por faixa ou redistribuição em lote. | Parcial | Média: faixas/lote |
| Quem pode atender às 15h? | Escala + habilidade + duração + conflitos + recursos | Engine combina escala coletiva/pessoa, habilidade, loja, duração, conflitos e conjuntos físicos configurados. Tutor recebe horários sem escolher profissional (D02). | Coberto nesse modelo | — |
| Cancelar atendimento de uma pessoa | Selecionar, cancelar com motivo e histórico | Agenda filtra por pessoa; detalhe permite operações conforme estado/política. Registro não é apagado. Cancelamento excepcional após chegada exige motivo e não vale para todo estado. | Coberto com restrições explícitas | — |
| Funcionário saiu: redistribuir | Transferir sem alterar outras condições | Transferência independente com motivo e eventos estruturados; valida período/pessoa/capacidade. Sem redistribuição em lote. | Coberto individualmente | Média: lote |
| Amanhã fechado / horário reduzido | Expediente semanal + exceção de data | Implementado no calendário da loja e disponibilidade. | Coberto | — |
| Manutenção das 13h às 16h | Bloqueio nomeado com motivo/intervalo | Exceção do dia pode criar janelas 08–13 e 16–18. Não há entidade própria de bloqueio com motivo/nome e período de vários dias. | Parcial | Média |
| Reservas afetadas por fechamento | Prévia, resolução segura e histórico | Loja, escala coletiva da data e pools físicos têm prévia/links para cuidados; salvar recusa conflito e revalida versão. Calendário individual isolado ainda usa proteção no servidor. | Parcial | Média: prévia individual |
| Reagendar / cancelar / manter exceção em lote | Resolver impactos coletivos com segurança | Reagendamento/cancelamento individuais. Não há lote ou “manter exceção” para aceitar conflitos de calendário. | Ausente | Média |
| 4 pessoas, 2 mesas, 3 banheiras | Capacidade física independente da equipe | Pools configuráveis por serviço com capacidade concorrente; buffers e período inteiro consomem unidade. Não separa etapas/mesas específicas. | Coberto no modelo conservador | Média: etapas |
| Nem todos fazem tosa | Habilidade por pessoa | `service_ids` por recurso; servidor valida alocação/extensão. Pessoa ativa sem habilidade não atende aquele serviço. | Coberto | — |
| Escala por dia da semana | Calendário próprio e exceções | Calendário individual intersecta o da loja. `null` herda expediente; `active` sozinho não determina disponibilidade. | Coberto | — |
| Só nessa data teremos X pessoas | Alterar equipe efetiva apenas nessa data | Equipe por data seleciona pessoas e períodos, mostra total presente, motivo e prévia; substitui somente a data. Restauro remove exceção e mantém herança semanal. | Coberto | — |
| Cancelamento é diferente de falta | Estados e medidas separados | `CANCELLED` e `NO_SHOW` distintos no relatório. Taxas não vêm calculadas com denominador/corte próprios. | Parcial | Média |
| Por que atrasamos? | Previsto × realizado por serviço/pessoa | Gestão mostra duração contratada × média real por serviço; real/atraso/desvio por responsável final. Não presume causa nem pontuação de pessoas. | Coberto nessas medidas | Média: causas |
| Continuidade do histórico operacional | Serviço, pessoa, tempos, observações e contexto seguinte | Alertas de perfil e três cuidados anteriores com duração/pessoa/notas no detalhe atual. Materiais/máquinas continuam texto livre, sem ficha estruturada. | Parcial | Média: execução estruturada |
| O que aconteceu e quem alterou? | Timeline de negócio e auditoria | Transferência antes/depois estruturada e motivos/autores internos; comunicação agendada, reenvio, descarte e aceitação SMTP em histórico próprio. Sem comprovante externo de entrega/leitura; reagendamento ainda sem antes/depois completo. | Parcial | Média |

## Perguntas de negócio

| Pergunta | Hoje | Estado | Prioridade |
|---|---|---|---|
| Quantos pets atendemos? | Pets e clientes únicos com ao menos um cuidado concluído no período, além de contagem de reservas | Coberto nesse recorte | — |
| Quantos atendimentos por funcionário? | Agrupamento por responsável final com concluídos/cancelados/faltas/serviços/médias | Coberto nesse modelo | — |
| Quais serviços vendemos mais? | `by_service` conta reservas por serviço, inclusive não concluídas; sem classificação de venda | Parcial | Média |
| Ticket médio? | Preços contratados existem; sem agregado, pagamentos ou receita realizada | Ausente | Média: definir “ticket agendado” vs recebido |
| Dias de maior demanda? | Recortes de até 31 dias; sem distribuição/série por dia | Ausente | Média |
| Horários de maior demanda? | Sem agrupamento por faixa horária | Ausente | Média |
| Ocupação? | Minutos ocupados ÷ disponíveis no período, por calendários atuais de pessoas; não capacidade física, utilização efetiva ou retrato histórico imutável | Parcial | Média |
| Quantos cancelamentos / no-shows? | Contagens separadas por estado atual; sem taxa nem motivos agregados | Parcial | Média |
| Duração média por serviço / pessoa? | Médias de concluídos com início/conclusão, previsão por serviço e atraso/desvio por pessoa | Coberto | — |
| Clientes e pets que retornam? | Histórico ligado a IDs, sem relatório de recorrência | Ausente | Média |
| Clientes inativos? | Sem segmento de inatividade temporal; cadastro arquivado é outro conceito | Ausente | Baixa |
| Profissionais sobrecarregados? | Carga planejada/capacidade atual por pessoa e distribuição automática por menor carga elegível | Parcial: sem mapa por faixa ou redistribuição automática | Média |
| Horários ociosos? | Horários disponíveis e ocupação agregada, sem mapa de capacidade ociosa | Parcial | Média |

O incremento resolve pools físicos e distribuição simples, com autoria/atribuição explícitas. Reserva em grupo, etapas de recursos e esforço dividido entre responsáveis continuam lacunas. A métrica deve distinguir **reserva**, **atendimento concluído**, **pet único** e **ator de uma ação**. Ocupação pode ultrapassar 100% após redução do calendário; a interface já avisa que o denominador usa a configuração atual. Não chamar contagem de reservas de produtividade ou receita.

## Recepção

| Dor | Hoje | Estado | Prioridade |
|---|---|---|---|
| Encontrar cliente por nome/telefone/CPF | Busca textual de clientes; cadastro básico sem CPF por D06 | Parcial; CPF fora da decisão | Média |
| Pet + serviço + próximos horários em poucos cliques | Cliente → pets → agendamento assistido, disponibilidade e revisão reais; sem tela única ou sugestão de “próximos horários” com responsáveis | Parcial | Alta |
| Cadastrar cliente novo e pet | Equipe cria contato sem conceder identidade; cadastra pet, convida vínculo quando necessário | Coberto | — |
| Check-in, cancelar e remarcar rapidamente | Ações no detalhe e filtros da agenda; sem console único de recepção | Parcial na UX | Alta |
| Registrar atraso, trocar profissional ou encaixar | Timestamp de chegada; extensão com possível troca. Não há transferência independente ou overbooking/encaixe privilegiado | Parcial | Alta |
| Consultar histórico | Cadastro e reservas/histórico filtrados, respeitando visibilidade | Coberto | — |

Recepção não tem um papel de acesso separado hoje: usa EMPLOYEE conforme D07. Um novo fluxo rápido pode compartilhar as regras existentes; não deve contornar duração, habilidade ou exclusões para “encaixar”.

## Um dia com menos funcionários: como funciona

Exemplo: existem cinco pessoas aptas no expediente normal; somente três trabalharão em uma data.

1. Entre como equipe/admin em `/operacao/configuracoes` (**Equipe e horários**).
2. Edite cada uma das duas pessoas que não trabalharão nessa data.
3. Se a pessoa estiver em “Seguir o expediente da loja”, desmarque essa opção e **confira sua semana normal**. Esta revisão faz o formulário começar com a semana atual da loja, evitando apagar implicitamente os outros dias. Ajuste-a caso a escala da pessoa seja diferente; depois de salvar, essa semana própria não acompanha automaticamente futuras ampliações da semana da loja.
4. Em **Datas especiais**, adicione a data e deixe seus períodos vazios. Isso fecha apenas esse dia. Para sair cedo, informe a janela efetivamente trabalhada; a exceção substitui o dia inteiro, não apenas subtrai uma faixa.
5. Salve. Se houver reservas incompatíveis, resolva-as antes; o sistema não as cancela nem redistribui sozinho.
6. Nos dias adjacentes, a semana normal volta a valer. Não desative a pessoa para representar uma folga pontual: isso fecharia sua disponibilidade global.

Não basta escrever “3” sem indicar quais pessoas estão presentes. Três funcionários com habilidades/janelas diferentes podem gerar capacidades diferentes ao longo do mesmo dia. Para **mais** pessoas, elas precisam ter contas de equipe verificadas, estar adicionadas uma única vez à agenda e estar aptas ao serviço. A loja não pode ficar fechada e, ao mesmo tempo, ser aberta apenas pelo calendário de um funcionário: vale a interseção.

**Verificação automatizada nova:** PostgreSQL isolado, cinco pessoas distintas, duas fechadas em apenas uma data. Reserva simultânea aceita **5 no dia anterior, 3 na data, 5 no seguinte**; a próxima solicitação de cada dia é recusada, e as duas pessoas ausentes não são alocadas na data. Teste: `test_one_day_staff_exceptions_reduce_capacity_and_restore_adjacent_days` em `apps/api/tests/integration/test_scheduling.py`. O resultado executado está no registro de evidência; não se alterou a escala do usuário para testar.

## Ordem sugerida para fechar lacunas

1. **Operação confiável:** escala coletiva por data com prévia de impacto; transferência independente com autoria e histórico estruturado; alergias/contexto anterior destacados; minha agenda.
2. **Comunicação da jornada:** lembrete e aviso de conclusão, visibilidade de envio/falha. Antes de usar e-mail pessoal fora do computador, resolver provedor/D10; aceitação SMTP não prova entrega na caixa do destinatário.
3. **Capacidade completa:** mesas/estações e consumo por serviço, concorrência envolvendo pessoas + equipamentos; reservar vários pets/serviços com compensação ou confirmação atômica definida.
4. **Gestão que aprende:** concluídos por pessoa/serviço, duração prevista × real, atraso, cancelamento/falta e distribuição; definir atribuição quando houver transferência. Sem ranking automático de “melhor funcionário”.
5. **Recepção e relacionamento:** console rápido, demanda por faixa, recorrência/inatividade; discutir preferência de profissional apenas se D02 for revista.

A revisão inicial entregou análise/visual; a autorização posterior implementa o incremento descrito no ADR-016 e atualiza esta matriz. Não é necessário trazer todas ao primeiro MVP; é necessário tornar o limite claro e não tratar P08/release candidata como aceite de todas as ideias.

## Evidência de implementação

| Referência | O que sustenta |
|---|---|
| `apps/api/src/petland/modules/scheduling/domain/models.py` e `application/service.py` | Calendários, elegibilidade, configuração, reserva, cancelamento/reagendamento |
| `apps/api/tests/integration/test_scheduling.py` | Concorrência, exclusões, impacto, snapshots e capacidade por data |
| `apps/api/src/petland/modules/scheduling/application/operations.py` e `domain/operations.py` | Estados, extensão/troca acoplada, timestamps, notas e indicadores limitados |
| `apps/api/tests/integration/test_attendance.py` | Operação persistida, ações/visibilidade e proteção de ocupação |
| `apps/api/src/petland/modules/scheduling/infrastructure/notifications.py` e `infrastructure/store.py` | Outbox, envio/retry e consulta agregada |
| `apps/web/src/features/booking/CalendarPage.tsx` e `CalendarEditor.tsx` | Interface de calendário semanal e datas especiais individuais |
| `apps/web/src/features/booking/OperationsPage.tsx`, `AttendancePage.tsx`, `AppointmentsPage.tsx` e `ManagementPage.tsx` | Agenda, contexto, timeline, histórico e medidas expostas |
| `apps/web/src/features/care/PetsPage.tsx` e `CustomersPage.tsx` | Pets/observações e cadastro assistido |
| [ADR-003](../adr/0003-scheduling.md), [ADR-012](../adr/0012-p05-operations.md) | Regras e restrições aprovadas |
| [Primeiro acesso](../evidence/Onboarding.md), [roteiro de teste pessoal](../runbooks/manual-acceptance.md) | Jornada real, caixa SMTP local e acesso à equipe |

Não foi executada uma nova campanha manual de cada linha da matriz: há revisão dos contratos/código e reaproveitamento de testes de integração/E2E, com teste específico novo para a dúvida de capacidade diária. O registro de evidência discrimina o que foi executado nesta revisão.

## Atualização operacional autorizada

Procedimento simplificado: **Equipe por data → data → pessoas/períodos → motivo → conferir impactos → confirmar**. O modo individual abaixo permanece válido, mas a tela coletiva elimina a necessidade de abrir cada cadastro. Dashboard em `/operacao`; gestão em `/gestao`. Regras/limites no [ADR-016](../adr/0016-operational-evolution.md), uso no [runbook](../runbooks/operational-evolution.md), resultados executados na [evidência](../evidence/Operations-evolution.md).
