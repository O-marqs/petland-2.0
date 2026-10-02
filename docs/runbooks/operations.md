# Operação local — P05

1. Entre como funcionário ou administrador e abra Agenda (`/operacao/agenda`). Hoje é calculado no fuso da loja. Dia/Semana, data, situação, pessoa e busca permanecem na URL.
2. Abra um atendimento. Confira contato do tutor e cuidados do pet; registre a chegada quando ele estiver presente. Início só é aceito após chegada e a partir do horário reservado.
3. Use Adicionar anotação. O padrão é **Somente a equipe**. Escolher **Cliente e equipe** publica um resumo deliberadamente. Registros não são editados; correção exige nova anotação.
4. Inicie e conclua o cuidado. O resumo de conclusão é opcional e visível ao cliente. O histórico próprio e os links em cliente/pet mostram o resultado após recarregar.
5. Se atrasar, confira o alerta e use Estender atendimento. Informe minutos, motivo e pessoa elegível. Conflito conserva o original; resolva outras reservas explicitamente antes de tentar de novo. A conclusão não exige extensão retroativa impossível.
6. Falta exige que o pet não tenha chegado e que a tolerância configurada/contratada tenha passado. Confira o limite no detalhe. É um registro manual com motivo, sem cobrança.
7. ADMIN pode cancelar por exceção antes do início real, com motivo. Aviso fica persistido e chega ao Mailpit local. Serviço já iniciado não tem cancelamento/reabertura.

Em caso de conexão perdida, repita a mesma ação pelo botão da tentativa. Ao sair dessa tela, recarregue o atendimento para conferir o estado antes de iniciar outra ação. Conflito de versão exige atualizar; não force estados pelo banco.

Equipe e horários agora fica em `/operacao/configuracoes`. As permissões EMPLOYEE/ADMIN continuam iguais para essa configuração. Tolerância de falta vale para novas reservas; zero é rascunho inicial e precisa de revisão do operador. Identificação e contato públicos usam somente o que foi preenchido.

## Administração

Visão geral (`/gestao`) apresenta volume, concluídas, canceladas, faltas e ocupação. Intervalo máximo: 31 dias, no fuso da loja. Ocupação compara intervalos reservados com os calendários/pessoas **atuais**; não mede horas trabalhadas nem recebimentos. Histórico pode ultrapassar 100% após mudança de capacidade. Denominador zero é apresentado como ausência de capacidade configurada. Fórmulas completas no ADR-012.

Auditoria (`/gestao/auditoria`) exige ADMIN. Datas/horários UTC são explícitos; filtre ação exata, autor ou objeto e navegue pelas páginas. Os detalhes de notas internas continuam no atendimento, sem ir para logs ou eventos de gestão.

## Verificação e manutenção

`check` inclui testes de PostgreSQL para transições, permissões, privacidade, idempotência, corridas, extensões, rollback e indicadores. `e2e` testa reserva até histórico com relógio real; a jornada da equipe pode esperar até dois minutos pelo início contratado e tem prazo maior por isso. Dados são sintéticos e identificados. Uma falha pode deixar atendimento sintético aberto: revise seu estado antes de repetir, sem apagar dados ou inventar conclusão.

API local: `/api/docs`. Schema vigente 0005_operations. Downgrade recusa dados de execução para evitar descarte. Migração reversa e limpeza de testes nunca usam o banco de desenvolvimento.

Se ocorrer problema de Docker, interromper e orientar o usuário. Não recuperar Docker nem apagar volumes automaticamente.
