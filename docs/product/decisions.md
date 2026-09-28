# Decisões e gates

Os pedidos de implementação autorizam G0/P01 e P02, incluindo D07, e resolvem as diretrizes abaixo. Não alteram retroativamente os documentos de planejamento.

| Decisão | Estado após o pedido | Consequência |
|---|---|---|
| D01 | Aprovada: uma loja, demonstração de portfólio, cliente/funcionário/admin | Sem multiempresa ou dados pessoais reais |
| D02 | Pendente: profissional, estação ou vaga de equipe; escolha do profissional | Bloqueia PL3-10/11 e P04. Profissional implica recurso único por pessoa; vaga implica capacidade de equipe sem prometer profissional específico |
| D03 | Pendente: confirmação automática/manual; antecedência, horizonte e passo | P04. Confirmação manual exige prazo e estado pendente; não será presumida |
| D04 | Pendente: cancelamento, reagendamento, falta, tolerância, interrupção e exceções | P04/P05; limites mudam políticas, transições e testes |
| D05 | Pendente: preço/duração fixos ou variáveis; escopo de um serviço | P03/P04; valores variáveis exigem oferta versionada e fatores de cálculo |
| D06 | Pendente: dados necessários, espécies e restrições | P03; começar apenas após aprovar campos, sem CPF/idade mínima presumidos |
| D07 | Aprovada em 24/09/2026 para o MVP, conforme pedido P02 | Cliente cuida dos próprios dados/pets/agendamentos/histórico; funcionário consulta agenda, registra chegada/início/conclusão, cadastra clientes/pets e agenda de forma assistida; admin inclui operação e gestão. Dados mínimos; notas internas não são publicadas. Cancelamentos excepcionais e demais políticas continuam D04 |
| D08 | Pendente: banco histórico, retenção e responsável por conflitos | Migração e entrada de dados reais |
| D09 | Aprovada: mesmo repositório, baseline e branch; nome remoto mantido | Histórico preservado; eventual renomeação não realizada |
| D10 | Pendente: provedor, domínio, orçamento, e-mail público e recuperação | Publicação/P07/P08; infraestrutura desta entrega é exclusivamente local |
| D11 | Aprovada como base inicial: verde/marfim/terracota e design system | Telas implementadas ainda sujeitas a revisão visual |
| D12 | Pendente: hashes, identidades e históricos incompletos | Promoção de dados históricos; não usar dados do MySQL |

Gate P02 liberado pela D07. A matriz efetiva está em [autorização](../architecture/authorization.md). Os próximos gates são D05/D06 antes de P03 e D02/D03/D04 antes de P04. Cancelamento/reagendamento assistidos e publicação de notas não recebem aprovação implícita. Canal técnico local de e-mail usa Mailpit; provedor público permanece D10.
