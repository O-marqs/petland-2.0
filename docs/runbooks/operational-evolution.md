# Organizar e acompanhar a operação

Acesse https://localhost:8443/entrar com uma conta de funcionário/administrador verificada da demonstração local. A entrada da equipe é `/operacao`; gestão fica em `/gestao` para administrador. Credenciais locais em `.local/staging/accounts.json`, caixa fictícia em http://localhost:8026. Não publique credenciais.

## Preparar e testar o dia

1. **Equipe e horários**: adicione contas da equipe à agenda, marque os serviços que cada pessoa executa e configure a loja/semana individual. Agenda deve estar habilitada. Preço e tempo vêm do serviço e porte.
2. **Equipe por data**: escolha a data. Indique quem trabalha e seus períodos; informe motivo, confira impactos e confirme. Para cinco habituais e três nesse dia, deixe duas pessoas sem período na data. As semanas adjacentes continuam iguais. “Voltar aos horários habituais” remove a exceção após prévia, permitindo voltar a cinco.
3. **Capacidade física**: adicione, por exemplo, duas mesas de tosa e três banheiras. Vincule os serviços que usam cada conjunto. Confira e confirme. Cuidado banho+tosa ocupa todos os conjuntos associados durante todo o período. Um conjunto indisponível fecha seus serviços; remover limite remove a restrição.
4. Com reservas existentes, prévia mostra os cuidados incompatíveis. Abra cada cuidado para transferir/reagendar/cancelar conforme política, então confira de novo. Nada é apagado/redistribuído automaticamente. Versão vencida pede atualização antes de salvar.

## Executar

O painel mostra o dia escolhido, a agenda pessoal ou da equipe, pendências atuais e distribuição. Agenda permite os mesmos recortes; pessoa sem recurso não recebe reserva própria. O painel é uma visão de ações, não autorização para ignorar conflitos.

Abra o cuidado. Confira alertas de alergia/restrição, manejo e cuidados anteriores. Registre chegada; no horário permitido, confirme leitura crítica e inicie. Conclua com resumo público ou escreva notas internas separadas. A confirmação crítica se refere à versão lida: se o cadastro mudar, atualize e confirme novamente.

**Transferir responsável** mantém serviço/preço/horário, exige motivo e verifica a pessoa nova. Uma pessoa sem habilidade, horário ou espaço livre é recusada. Use extensão quando precisa de mais tempo, sem modificar a previsão original. Um cuidado concluído não é reaberto por transferência.

## Lembretes e comunicação

Em **Equipe e horários → Configurar expediente e regras**, defina antecedência do lembrete em minutos (1440 = 24 horas). Zero não programa novos lembretes; alteração não recalcula avisos já programados. Reservas/reagendamentos futuros usam a regra, e reservas dentro da janela recebem confirmação. Alterações de reserva ou chegada descartam o lembrete pendente.

Conclusão gera aviso de pet pronto. Na reserva há **Comunicação** com estado e horário; aceito pelo servidor de e-mail não significa leitura ou entrega na caixa pessoal. Verifique a caixa Mailpit local. Nenhum provedor externo foi configurado. As notas privadas não devem aparecer na reserva/e-mail do tutor.

Para testar lembrete sem alterar o relógio do computador, configure um minuto e reserve um horário alguns minutos à frente. Aguarde o horário real de envio e depois execute o cuidado. Reagende outra reserva e confira que o lembrete antigo foi descartado.

## Entender resultados

Administrador escolhe período na gestão: cuidados por pessoa, serviços realizados, médias de duração/atraso/desvio, cancelamentos/faltas e pets/clientes únicos concluídos. A conclusão inteira conta para o responsável final. Não há divisão de tempo quando duas pessoas executam partes do cuidado. Ocupação compara reserva com calendário atual, sem inferir receita, produtividade ou uso físico.

Verificação automatizada: `python scripts/dev.py check`, E2E habitual, e `node apps/web/scripts/operations-evolution-staging.mjs`. O último cria pet/serviço/reserva sintéticos, usa SMTP e horário reais e restaura regras de escala, capacidade, habilidades e expediente ao terminar; preserva o atendimento concluído como evidência. Relatório/capturas em `.local/staging/browser/operations-evolution`. Execute somente na demo isolada reconhecida; não em uma loja real.

Antes de atualizar a demonstração, `backup-demo` preserva o banco em arquivo autenticado/criptografado. `staging-up` aplica a migração aditiva no mesmo banco, sem reset. Consulte [recuperação](operations-recovery.md) e [regras exatas](../adr/0016-operational-evolution.md).
