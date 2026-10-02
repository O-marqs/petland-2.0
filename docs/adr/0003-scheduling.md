# ADR-003 — Agenda transacional de uma loja (P04)

Status: aceita pela autorização P04 e pelas decisões D01–D11/recomendações delegadas na P03.

## Capacidade e configuração

Cada unidade representa uma pessoa da equipe, ligada a uma única conta verificada com papel EMPLOYEE ou ADMIN. A unicidade de user_id impede duplicar capacidade da mesma pessoa. Contas de equipe são convidadas pelo fluxo P02; a operação configura disponibilidade e serviços atendidos. Clientes não escolhem nem enviam profissional.

O agregado de configuração contém fuso IANA, habilitação, antecedência em minutos, horizonte em dias, passo entre inícios, prazo de alteração e calendário. O banco começa com agenda desabilitada e sem expediente/recursos. Valores numéricos iniciais são um rascunho técnico, não uma política aprovada de operação: a equipe deve revisá-los e salvar antes de abrir. Não são semeados cinco funcionários, preços ou durações exemplificativas.

Calendário semanal admite até quatro períodos por dia; até cem exceções por calendário. Exceção substitui o dia inteiro; lista vazia fecha a data. Recurso sem calendário herda a loja; calendário próprio é intersectado com o expediente da loja. A configuração pequena fica em JSONB versionado; recursos e reservas têm identidade relacional e FKs. Limites técnicos: passo 1–120 min, horizonte 1–366 dias, antecedência/prazo até 525600 min. Horários não atravessam meia-noite; divida o expediente em dias locais.

Preço/duração vêm da opção do serviço para o porte do pet. Preparação e intervalo após são configuráveis por opção (0–240 min); zero preserva as ofertas P03 sem inventar tempo adicional. A ocupação precisa caber integralmente numa janela. Intervalos são semiabertos. UTC no banco, ZoneInfo na regra e Intl no navegador. Horários locais ambíguos/inexistentes por horário de verão são omitidos em vez de escolher um offset arbitrário.

## Confirmação, versão e concorrência

Consulta não segura vaga. O resumo mantém oferta/versão do calendário; botão explícito confirma. A transação trava primeiro a linha singleton do estabelecimento. Revalida identidade atual, propriedade, elegibilidade, versão, política e intervalos; aloca deterministicamente o primeiro recurso elegível por UUID. Eventos, auditoria, resposta de idempotência e aviso são gravados no mesmo commit.

PostgreSQL btree_gist sustenta duas exclusões independentes: intervalo ocupado por recurso e intervalo de atendimento por pet. BOOKED ocupa; CANCELLED libera. Estados de execução serão incluídos na P05, com migração explícita das constraints. Não há status fictício de atendimento.

Cancelamentos/reagendamentos/configuração, alterações de pet/serviço e escritas de identidade seguem a ordem estabelecimento → demais locks. Identidade mantém também o lock de último administrador. Mutações de pet e catálogo revalidam a permissão sob o lock. Arquivar pet ou mudar porte/espécie com reserva futura é bloqueado. Desativar trabalhador/remover seu papel com reservas é bloqueado. Inativar serviço fecha novas vendas, mas conserva contratos já aceitos, inclusive seu reagendamento. Nenhuma operação cancela outras reservas implicitamente.

Idempotency-Key é UUID, por ator/operação. Assinatura normaliza o instante UTC e inclui o comando completo. Repetir o mesmo comando retorna a resposta originalmente confirmada; mudar payload retorna 409. A resposta é guardada independentemente de futuras alterações da reserva. P04 mantém os registros sem expurgo automático (evita expirar uma tentativa e criar duplicata); retenção produtiva é P08/D12. Falhas/transientes retornam erro seguro; cliente repete explicitamente a mesma chave, sem confirmação otimista.

## Alterações e comunicação

Cliente pode alterar antes do início e dentro do prazo contratado. A equipe pode ajudar fora do prazo, sempre antes do início; não há taxa. Motivo é obrigatório para cancelar/reagendar. Versão antiga retorna STALE_VERSION. Troca conserva pet, serviço, preço, duração, buffers e prazo contratados; mudança de serviço exige nova reserva. Falha mantém integralmente a reserva original.

Preview de calendário informa IDs afetados, somente para equipe. Salvar revalida sob lock, mesmo após preview sem impacto. Mudanças de fuso com reservas futuras, fechamentos e mudanças de recursos incompatíveis são bloqueadas.

Outbox persistente guarda avisos de confirmação, cancelamento e reagendamento. O processo da API tem worker local com lease/SKIP LOCKED, tentativas e atraso crescente até uma hora. SMTP ocorre fora da transação. Reinício não perde os avisos. Entrega é pelo menos uma vez; queda após SMTP e antes do registro pode repetir a mensagem, com Message-ID estável. Caixa local Mailpit; provedor externo continua adiado por D10. Logs não contêm destinatário ou corpo.

## Limites

Uma loja e lock global deliberado. Configuração é de minutos inteiros, sem reservas recorrentes, hold, pagamento ou extensão de atendimento. Horários passados não são remarcados. P05 trata agenda visual diária/semanal, chegada/início/conclusão, notas e indicadores. D10/P08 tratam publicação, retenção e operação produtiva.

