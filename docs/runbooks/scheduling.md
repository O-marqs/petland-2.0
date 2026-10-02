# Agenda local — P04

1. Inicie pelo comando up do runbook local. O worker de avisos inicia com a API e usa a caixa Mailpit local.
2. Administrador convida pessoas em Pessoas e acessos; cada pessoa aceita e confirma a conta.
3. Cadastre serviços ativos com preço, duração e eventuais minutos de preparação/intervalo após por porte.
4. Em Equipe e horários (`/operacao/configuracoes` desde P05), adicione cada pessoa uma vez e marque seus serviços.
5. Configure o expediente da loja, pausas, datas especiais, fuso e prazos. Confira o impacto e salve com a agenda aberta.
6. Cliente cadastra contato/pet, escolhe serviço/data/horário, revisa e confirma. A equipe usa Agendar um cuidado dentro do cadastro do cliente.
7. Reservas exibem detalhe, histórico, reagendamento e cancelamento. Alterações geram avisos para o e-mail do cadastro.

Uma data especial sem períodos fecha o dia. Recurso seguindo a loja herda também suas exceções. Recurso com calendário próprio nunca abre a loja fora do expediente dela. A consulta não segura vaga; conflitos preservam escolhas e pedem novo horário.

## Resposta perdida

Se o navegador não receber a resposta, use Tentar confirmar novamente na mesma revisão. A chave mantida em memória recupera o resultado do commit. Não há armazenamento persistente de dados do cliente no navegador. Após fechar/recarregar a tela, consulte Minhas reservas antes de iniciar outra tentativa.

## Reservas impedindo alterações

Use Conferir impacto para localizar reservas que seriam afetadas pelo fechamento. Reagende/cancele explicitamente com motivo e depois repita a configuração. Mudanças de pessoa, porte/espécie ou acesso também respeitam reservas existentes. Não apague registros pelo banco para contornar o conflito.

## Avisos

Mailpit está em http://localhost:8025. Avisos são gravados no mesmo commit da reserva; falha SMTP mantém a reserva e agenda nova tentativa. Atraso cresce até uma hora e a entrega volta após recuperar o serviço. Mensagens são sintéticas/localmente capturadas; não há provedor público.

Diagnóstico somente leitura: verificar saúde da API e eventos de log appointment_mail_delivery_failed/appointment_outbox_unavailable. Não imprimir destinatários, corpos, sessões ou segredos. Registros de appointment_outbox conservam attempts, available_at, lease_until e delivered_at para suporte técnico. Não editar a fila para marcar entrega fictícia.

Se houver problema de Docker, interromper o trabalho e orientar o usuário; não recuperar nem apagar volumes automaticamente.

