# ADR-016 — Escala, capacidade e continuidade do cuidado

Estado: implementado mediante [autorização humana](../implementation/Operations-evolution-request.md). Complementa ADR-003/012; não muda D02, D03, D04 ou D10.

## Disponibilidade

A escala coletiva de uma data substitui as janelas individuais **apenas naquela data** e intersecta o expediente da loja. Ausentes ou pessoas omitidas não oferecem capacidade nessa escala explícita. Restaurar horários habituais remove a exceção, sem copiar a semana. A equipe configurada é composta de identidades verificadas, recursos ativos e serviços habilitados. Uma quantidade sem indicar as pessoas não define corretamente habilidades/horários.

Pools físicos têm nome, quantidade e serviços vinculados. Cada cuidado usa uma unidade de cada pool vinculado durante toda a ocupação, incluindo buffers. É uma regra conservadora: banho+tosa ocupa os recursos associados durante todo o intervalo; ainda não há etapas com consumo distinto. Sem pool, prevalece a capacidade de pessoas. Pool indisponível fecha serviços vinculados; remover o limite retira essa restrição. Capacidade física não representa estoque, manutenção nominal ou uma mesa específica atribuída.

Prévia é informativa; salvar revalida sob o primeiro lock do estabelecimento e a mesma versão. Reservas incompatíveis impedem salvar. Não há cancelamento/redistribuição silenciosos. Alocação automática prioriza a pessoa apta/livre com menor soma de minutos planejados ocupados no dia local; UUID resolve empate. Consulta na confirmação inclui o dia inteiro, além das bordas de ocupação. Não é otimização global, ranking, nem escolha do tutor. Exclusões PostgreSQL de pet/pessoa permanecem.

## Responsabilidade e contexto

Transferência independente vale em confirmado, chegou e em atendimento. Exige motivo, outra pessoa apta/verificada/ativa, calendário, ausência de conflitos e a capacidade física. Preço, serviço e instantes contratados são conservados; versão/idempotência e eventos guardam pessoa anterior/nova. Razão e identificação ficam internas. A assinatura antiga de idempotência é mantida quando não há confirmação crítica; uma nova confirmação inclui a versão lida.

O cadastro do pet separa alergias/restrições críticas de preferências de manejo e texto de cuidado anterior. Não extrai diagnósticos das observações existentes. Iniciar cuidado com restrição crítica exige confirmar a **versão atual** do pet. Mudança entre leitura/início pede nova leitura e conserva o estado. Anotação interna registra a versão confirmada. O detalhe reúne até três cuidados concluídos antes do início agendado atual, com até cinco notas de cada e link para histórico; tutor continua recebendo apenas resumos publicados.

## Indicadores e painel

O painel diário recebe dados da mesma operação: reservas por estado, próximos cuidados pessoais/equipe, chegadas sem início, chegada não registrada e ocupação vencida, carga por pessoa e acesso à escala. Pessoa sem recurso configurado vê orientação e agenda pessoal vazia, não uma agenda coletiva apresentada como sua.

Relatórios agrupam pelo início agendado no fuso da loja, de 1 a 31 dias, com **estado atual**. A conclusão é atribuída ao responsável final; ator do comando pode ser diferente. Uma transferência no meio não divide minutos entre pessoas. Duração real = conclusão − início; atraso = máximo(0, início − previsto); desvio = duração real − duração contratada. Médias consideram concluídos com instantes completos; ausência de amostra aparece sem valor. Pets/clientes únicos contam concluídos distintos. Detalhes por serviço contam concluídos, enquanto total de reservas inclui cancelamentos/faltas.

Ocupação planejada usa intervalos reservados e capacidade atual dos calendários de pessoas. Não mede uso de equipamentos, horas trabalhadas ou capacidade histórica imutável; pode superar 100% se horários atuais forem reduzidos. Preço agendado não é receita. Não há classificação de “melhor funcionário”.

## Comunicação e migração

Antecedência de lembrete é configurável; zero não agenda novos lembretes. Configuração aplica-se a novas reservas/reagendamentos, preservando os avisos já programados. Uma reserva feita dentro da janela já recebe confirmação, sem lembrete imediato duplicado. Reagendar/cancelar/chegar/iniciar/concluir/falta descarta lembretes pendentes. Worker confere estado/horário antes de reclamar o envio; mensagem já reclamada pode competir com alteração. SMTP fora da transação, lease/retry e Message-ID mantêm entrega **pelo menos uma vez**, sem promessa de exactly-once ou recebimento/leitura externos.

Conclusão enfileira aviso de pet pronto com horário e acesso ao resumo; notas internas não entram na mensagem. Tutor/equipe consultam agendado, reenvio, descartado ou aceito pelo SMTP, sem expor destinatário/body/segredos pela projeção. Mailpit confirma envio local; provedor externo continua D10.

Migration `0007_product_operations` adiciona campos sem reconstruir tabelas ou apagar dados. Mensagens antigas têm tipo `legacy`. Downgrade recusa dados novos, escala/pools ou antecedência não nula; quando vazio, remove também as chaves JSONB para compatibilidade. Backup registra a revisão **real do banco**, inclusive antes de migrar a aplicação. Rollback deve usar imagem compatível/roll-forward e preservação, não apagar histórico.

## Limites mantidos

Uma reserva = um pet/serviço; reserva em grupo, serviço alterado em execução, férias por intervalo, redistribuição em lote, console único de recepção, confirmação de presença, séries de demanda/recorrência/inatividade, entrega externa e medição de esforço fracionado continuam fora deste incremento. O registro dessas lacunas permanece na matriz funcional; candidata/CI não substituem aceite humano/leitor de tela.
