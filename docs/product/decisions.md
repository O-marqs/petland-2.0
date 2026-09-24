# Decisões e gates

O pedido de implementação autoriza G0/P01 e resolve as diretrizes abaixo. Não altera retroativamente os documentos de planejamento.

| Decisão | Estado após o pedido | Consequência |
|---|---|---|
| D01 | Aprovada: uma loja, demonstração de portfólio, cliente/funcionário/admin | Sem multiempresa ou dados pessoais reais |
| D02 | Pendente: profissional, estação ou vaga de equipe; escolha do profissional | Bloqueia PL3-10/11 e P04. Profissional implica recurso único por pessoa; vaga implica capacidade de equipe sem prometer profissional específico |
| D03 | Pendente: confirmação automática/manual; antecedência, horizonte e passo | P04. Confirmação manual exige prazo e estado pendente; não será presumida |
| D04 | Pendente: cancelamento, reagendamento, falta, tolerância, interrupção e exceções | P04/P05; limites mudam políticas, transições e testes |
| D05 | Pendente: preço/duração fixos ou variáveis; escopo de um serviço | P03/P04; valores variáveis exigem oferta versionada e fatores de cálculo |
| D06 | Pendente: dados necessários, espécies e restrições | P03; começar apenas após aprovar campos, sem CPF/idade mínima presumidos |
| D07 | Pendente: permissões operacionais detalhadas | Gate P02/P03/P05. Três perfis aprovados não aprovam cadastro/cancelamento assistido ou publicação de notas |
| D08 | Pendente: banco histórico, retenção e responsável por conflitos | Migração e entrada de dados reais |
| D09 | Aprovada: mesmo repositório, baseline e branch; nome remoto mantido | Histórico preservado; eventual renomeação não realizada |
| D10 | Pendente: provedor, domínio, orçamento, e-mail público e recuperação | Publicação/P07/P08; infraestrutura desta entrega é exclusivamente local |
| D11 | Aprovada como base inicial: verde/marfim/terracota e design system | Telas implementadas ainda sujeitas a revisão visual |
| D12 | Pendente: hashes, identidades e históricos incompletos | Promoção de dados históricos; não usar dados do MySQL |

Próximo gate após P01: D07, antes da fase P02. Alternativas: funcionário limitado à execução dos atendimentos; ou execução mais cadastro/reserva assistidos. A segunda amplia os casos de uso, projeções de dados e matriz de autorização. Cancelamentos excepcionais e gestão de papéis permanecem decisões explícitas. Canal técnico local de e-mail pode ser implementado sem contratar provedor.
