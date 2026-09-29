# Decisões e gates

Registro atualizado em 28/09/2026 pelo pedido P03. Fontes originais permanecem íntegras; a autorização posterior está em [P03-request.txt](../implementation/P03-request.txt). O usuário autorizou seguir as recomendações para os pontos não respondidos ou incompletos.

| Decisão | Decisão vigente | Consequência |
|---|---|---|
| D01 | CRM de pet shop para portfólio; uma loja e três perfis | Demonstração com dados sintéticos, sem multiempresa |
| D02 | Capacidade derivada dos funcionários e dos horários configurados no back office; cliente não escolhe profissional | P04: recursos atribuídos pelo servidor, calendários/capacidade configuráveis; exemplos de cinco funcionários e 40/60/90 min não são defaults |
| D03 | Revisão do resumo e confirmação explícita pelo cliente | P04: confirmação transacional ao clicar, sem aprovação manual da equipe; um pet + um serviço por reserva |
| D04 | Sem taxas ou cobrança por enquanto; demais pontos seguem recomendações | P04/P05: cancelamento/reagendamento auditados, condições explícitas, sem pagamento; detalhes de antecedência/horizonte/passos serão parâmetros documentados ao implementar agenda |
| D05 | Preço e tempo por tamanho e serviço | P03: opções por porte, valores exatos BRL, versão; P04 conserva condições contratadas por snapshot |
| D06 | Nome, e-mail, contato e endereço; demais campos mínimos recomendados | P03: telefone/endereço opcionais, sem CPF/idade do tutor; pets com raça/nascimento desconhecidos permitidos, cachorro/gato como referências iniciais |
| D07 | Equipe executa operações do back office; comunicação com cliente para reagendamento/cancelamento | P03: equipe gerencia clientes/pets/serviços; administração de acessos permanece ADMIN conforme recomendação de perfis separados. P04/P05 incluem configurações operacionais e comunicação efetiva, sem presumir entrega por simples gravação local |
| D08 | Sistema novo, sem banco histórico | Criar PostgreSQL do zero; dispensada importação de MySQL. Preservar dados locais das fases já entregues |
| D09 | Mesmo repositório | Manter histórico, tag legada, branches e PRs incrementais |
| D10 | Publicação/provedor fora do escopo atual | Somente ambiente local; SMTP/Mailpit local, sem domínio/deploy/recurso pago |
| D11 | Direção visual aprovada | Verde/marfim/terracota; cliente acolhedor, equipe mais compacta; revisão responsiva |
| D12 | Migração histórica não se aplica, conforme D08 | Não importar hashes ou identidades legadas |

P03 autorizada e gates D05/D06 resolvidos. D02/D03/D04 orientam a próxima fase; esta entrega não antecipa agendamento. Informações comerciais reais (preços, serviços, funcionários e horários) são configuradas pelo operador, sem inventar dados para preencher telas. A ausência de contato/endereço de uma loja real não é substituída por contato fictício.

Detalhes da implementação em [ADR 0007](../adr/0007-p03-customers-pets-catalog.md) e [matriz de autorização](../architecture/authorization.md).
