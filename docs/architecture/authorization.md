# D07 — autorização do MVP

Aprovação inicial: pedido integral em `docs/implementation/P02-request.txt`, recebido em 24/09/2026. O plano original permanece íntegro; esta matriz registra sua decisão posterior. Perfis fixos são associados à conta no servidor; selecionar uma área visual não altera privilégio.

| Ação | Cliente | Funcionário | Administrador | Fase |
|---|---|---|---|---|
| Conta, senha e sessões | Próprias | Próprias | Próprias | P02 |
| Convites de equipe | Não | Não | Sim, reautenticação; concede EMPLOYEE após confirmação do e-mail | P02 |
| Contas, perfis e ativação | Não | Não | Sim, reautenticação, versão, auditoria e proteção do último admin | P02 |
| Dados/pets próprios | Próprios | Só se também CUSTOMER | Só se também CUSTOMER, além de gestão futura | P03 |
| Cadastro assistido de cliente/pet | Não | Sim, projeção mínima | Sim, auditado | P03 |
| Agendar | Próprio | Assistido em nome de cliente | Assistido | P04 |
| Consultar agenda operacional | Não | Sim, dados necessários à operação | Sim | P05 |
| Chegada/início/conclusão | Não | Sim, transições válidas | Sim | P05 |
| Notas internas | Não | Necessárias ao atendimento | Sim | P05 |
| Publicar resumo do cuidado | Não | Sim, campo/visibilidade explícitos | Sim | P05 |
| Falta e extensão | Não | Sim, regras temporais e ocupação | Sim | P05 |
| Cancelar por exceção BOOKED/ARRIVED | Não | Não | Sim, motivo obrigatório, antes de início real | P05 |
| Indicadores agregados e auditoria | Não | Não | Sim, reporting:read/audit:read | P05 |
| Serviços, preços/duração e ativação | Não | Sim, versão e auditoria | Sim | P03 |
| Horários/capacidade/configuração operacional | Não | Sim, versão e impacto de reservas | Sim | P04 |
| Cancelamento/reagendamento assistidos | Próprios, pelas políticas | Sim, auditado e com comunicação ao cliente | Sim | P04/P05 |

P02 implementou identidade; P03 ampliou EMPLOYEE com catalog:manage e entregou cadastro próprio/assistido, pets e serviços. P04 e P05 completam as capacidades da matriz para reservas, execução e gestão. Propriedade e projeção mínima são aplicadas além da capacidade do perfil. Notas internas não fazem parte do schema público.

## Enforcement

- Visitante só pode criar CUSTOMER. Campos extras, inclusive `roles`/`status`/`user_id`, são rejeitados.
- `/auth/me` deriva papéis da base em cada requisição; conta não verificada recebe somente acesso básico à própria identidade. Contas desativadas não autenticam.
- Gestão reconsulta o ator dentro da transação, exige ADMIN verificado e senha atual. Troca de papéis/desativação revoga todas as sessões da conta afetada. Versão evita atualização obsoleta.
- Sessões são listadas/revogadas com filtro obrigatório por proprietário. ID alheio/inexistente retorna 404.
- Lock transacional compartilhado PostgreSQL serializa mudanças administrativas e bootstrap. Não é possível remover/desativar o último administrador ativo e verificado, mesmo em corrida entre administradores.
- Convite para endereço já cadastrado exige a senha atual dessa conta; nunca associa identidades apenas por coincidência de endereço. CUSTOMER existente é preservado ao adicionar EMPLOYEE. Aceitação revoga sessões anteriores.
- Bootstrap é CLI operacional com acesso ao ambiente, somente quando não existe admin ativo. Não existe endpoint público nem senha inicial default. Link de uso único chega pela caixa configurada.

PL3-07 implementa o vínculo Customer ↔ User por convite de uso único, e-mail verificado coincidente e confirmação explícita. Criar identidade não cria perfil comercial automaticamente. Identificadores de tutor são derivados da conta no servidor para rotas próprias; busca operacional exige customer:assist. Raça/espécie e versões são verificadas na aplicação/banco; pets alheios retornam 404. Escritas comerciais geram auditoria na mesma transação. Ver ADR 0007.

P04 acrescenta establishment:manage ao funcionário, disponibilidade/reservas próprias e assistidas, cancelamento e reagendamento. Escritas de agenda revalidam o ator atual sob o lock do estabelecimento. Cliente nunca escolhe recurso, valor, duração, dono ou status. Mudanças de acesso que retiram uma pessoa da capacidade são bloqueadas enquanto houver reservas. Eventos públicos não expõem identificador do funcionário, credenciais ou mensagens de e-mail.

P05 implementa operation:read, attendance:execute e notes:internal; reporting:read/audit:read são ADMIN. Nota interna nunca entra no schema cliente nem no evento público. Resumo PUBLIC é publicado deliberadamente. Cada mutação reconsulta o ator sob lock. Proteção de pet/equipe inclui atendimento aberto vencido. Gestão de contas permanece com reautenticação, versão e último administrador protegido; configurações comerciais continuam disponíveis à equipe conforme D07.
