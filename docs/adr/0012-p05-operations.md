# ADR-012 — Execução, visibilidade e gestão (P05)

Aceita pela autorização P05 e recomendações delegadas em D01–D11. Complementa ADR-003, sem substituí-lo. Uma loja, nenhuma taxa, nenhuma publicação externa.

## Estados e relógio

Atendimento é a execução da própria reserva: BOOKED → ARRIVED → IN_PROGRESS → COMPLETED. BOOKED também pode virar NO_SHOW ou CANCELLED. Estados finais não reabrem. Cliente não executa transições. Funcionário/administrador registra chegada, início, conclusão e falta. ADMIN pode cancelar excepcionalmente BOOKED/ARRIVED com motivo, inclusive após o horário; após início não se finge cancelamento/conclusão por interrupção. Uma política de interrupção continua fora do MVP.

Chegada é presencial e explícita, no mesmo dia local da reserva; pode anteceder o início. Início exige chegada, horário planejado já atingido, tempo reservado ainda disponível e pessoa válida. A mesma pessoa não inicia o próximo cuidado enquanto o anterior estiver IN_PROGRESS, mesmo que o intervalo planejado tenha terminado. Conclusão exige início e relógio não anterior. Instantes reais vêm do servidor e nunca sobrescrevem starts_at/ends_at ou a oferta contratada. Os botões recebem ações permitidas do servidor; cada comando revalida dentro da transação.

Tolerância de falta (0–1440 minutos após o início) fica na configuração, é mostrada à equipe e copiada para novas reservas. Zero é o rascunho técnico inicial, inclusive para reservas P04 que não tinham esse parâmetro; não é descrito como tolerância informada por uma loja real. O operador revisa antes de usar. Falta nunca é automática: exige equipe, motivo, estado BOOKED e instante limite atingido. Alterar a configuração não muda contratos existentes. Falta/cancelamento liberam ocupação, sem taxa.

## Ocupação e atraso

Migration 0005 inclui ARRIVED, IN_PROGRESS e COMPLETED nas duas exclusões PostgreSQL. COMPLETED conserva intervalo planejado/estendido, inclusive conclusão antecipada; não reutilizar sobra. Cancelamento/falta ficam fora das exclusões.

reserved_until permite estender sem mudar ends_at. Pet ocupa [starts_at, coalesce(reserved_until, ends_at)); recurso ocupa preparação até reserved_until + buffer final. Equipe solicita até oito horas adicionais ao término original como limite técnico, com motivo; horário precisa estar no futuro, ampliar o período e caber integralmente no expediente/interseção. Pode indicar outra pessoa elegível. Colisão com pet/recurso ou fechamento bloqueia a operação inteira. Não mover reservas alheias automaticamente. Mudança de responsável acrescenta nota interna com antes/depois; evento registra o novo término da ocupação.

O alerta de atraso não altera intervalo sozinho. Agenda não vende automaticamente um intervalo maior por inferir execução atrasada. Se houver conflito, equipe resolve a sequência, ajusta explicitamente as reservas afetadas ou usa outra pessoa elegível. Bloqueio de início e de transferência de atendimento em execução evita duas execuções reais simultâneas da mesma pessoa, inclusive quando o atendimento anterior está vencido.

Configuração, arquivo de pet e retirada de pessoa da capacidade preservam reservas abertas, incluindo ARRIVED/IN_PROGRESS vencidos. COMPLETED não exige adaptar retroativamente seu calendário; seu intervalo continua nas exclusões. Recursos únicos por conta e ordem global de locks da P04 permanecem.

## Transações e privacidade

Comandos de execução, anotações e extensão usam versão esperada e Idempotency-Key por ator/operação; gravação de estado, evento, nota, auditoria e resposta é atômica. Repetir resposta perdida recupera exatamente a resposta original, mesmo após outra evolução. Erro de persistência desfaz tudo. UI congela os valores enviados e repete a mesma tentativa; conflito pede atualização explícita.

appointment_notes é append-only para a aplicação: runtime tem SELECT/INSERT, sem UPDATE/DELETE. INTERNAL e PUBLIC são visibilidades separadas. Padrão da tela é INTERNAL; resumo de conclusão possui campo próprio, opcional, explicitamente público. Correções acrescentam anotação, não apagam história. Texto simples, até 2000 caracteres, renderizado como texto; nenhuma publicação automática de nota interna. Eventos públicos removem note_internal; schemas públicos não contêm autores, contatos operacionais, recursos nem notas privadas. Nota e resumo permanecem disponíveis também em históricos arquivados.

Aviso de cancelamento excepcional usa a outbox SMTP/Mailpit P04, na mesma transação. Outras transições ficam na linha do tempo; não se promete e-mail externo ou entrega de conclusão.

## Consultas e indicadores

Agenda padrão é hoje no fuso da loja, com consulta dia/semana/período de até 31 dias, pet/tutor, pessoa e situação; paginação no servidor e filtros na URL. Detalhe operacional reúne contato mínimo, cuidado informado pelo tutor, pessoa alocada, horários, notas e eventos com autoria. Histórico próprio mantém filtro obrigatório de cliente; IDs alheios não concedem acesso.

Resumo administrativo requer reporting:read (ADMIN). Datas são inclusivas na interface, convertidas em [meia-noite local inicial, meia-noite após o último dia). Volume e distribuições contam reservas cujo starts_at está no recorte, pelo estado atual e nome do serviço contratado. Não contam eventos como atendimentos e não alegam receita.

Ocupação = minutos de occupied_start_at/occupied_end_at recortados ao período para BOOKED/ARRIVED/IN_PROGRESS/COMPLETED, divididos por minutos da interseção do calendário atual da loja com cada pessoa ativa/verificada e habilitada para algum serviço. Datas especiais substituem semana; pausas excluídas; nenhuma multiplicação por número de serviços. Denominador zero retorna null, não zero por cento. Arredondamento somente no percentual (duas casas). O numerador inclui reservas atravessando a borda; volume usa início no período. Leitura protegida pelo lock para configuração e reservas coerentes.

É uma comparação com capacidade **atual**, explicitada na tela: mudanças posteriores de equipe/calendário podem gerar mais de 100% em períodos passados. Não é capacidade histórica reconstruída, produtividade real nem receita recebida. Eventos e instantes reais ficam disponíveis para análises futuras.

Auditoria de gestão é somente ADMIN (audit:read), paginada por período máximo de 31 dias, ação, autor e objeto. Datas UTC explicitadas na tela. Projeção omite senhas, sessões, e-mails e corpos de notas. Gestão de identidade continua exigindo reautenticação e protege o último administrador; nenhum construtor de papéis novo.

Identificação pública (nome/telefone/e-mail/endereço) compartilha versão e formulário operacional de configuração; campos não preenchidos não são inventados. Configuração preserva preview/revalidação do calendário.

## Migração e continuidade

0005 é aditiva, preserva P04, idempotências e dados locais. Downgrade recusa descartar execuções/notas/idempotências P05; requer plano explícito de preservação. Testes usam apenas PostgreSQL efêmero dedicado. P06 é revisão transversal de qualidade/UX; D10 mantém publicação/provedor adiado.
