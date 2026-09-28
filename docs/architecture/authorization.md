# D07 — autorização do MVP

Aprovação: pedido integral em `docs/implementation/P02-request.txt`, recebido em 24/09/2026. O plano original permanece íntegro; esta matriz registra sua decisão posterior. Perfis fixos são associados à conta no servidor; selecionar uma área visual não altera privilégio.

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
| Funcionários/serviços/horários/capacidade/configuração | Não | Não | Gestão autorizada | P03–P05 |
| Cancelamentos excepcionais, reagendamento assistido, falta e publicação de notas | Não aprovados por D07; dependem das respectivas políticas D04 | Não presumidos | Não presumidos | P04/P05 |

P02 implementa somente as três primeiras linhas. As demais capacidades estão identificadas na matriz/enum de permissões para orientar os módulos futuros, sem endpoints fictícios. Cada módulo futuro deve aplicar propriedade e projeção mínima além da capacidade do perfil. Notas internas nunca serão parte automática do schema público.

## Enforcement

- Visitante só pode criar CUSTOMER. Campos extras, inclusive `roles`/`status`/`user_id`, são rejeitados.
- `/auth/me` deriva papéis da base em cada requisição; conta não verificada recebe somente acesso básico à própria identidade. Contas desativadas não autenticam.
- Gestão reconsulta o ator dentro da transação, exige ADMIN verificado e senha atual. Troca de papéis/desativação revoga todas as sessões da conta afetada. Versão evita atualização obsoleta.
- Sessões são listadas/revogadas com filtro obrigatório por proprietário. ID alheio/inexistente retorna 404.
- Lock transacional compartilhado PostgreSQL serializa mudanças administrativas e bootstrap. Não é possível remover/desativar o último administrador ativo e verificado, mesmo em corrida entre administradores.
- Convite para endereço já cadastrado exige a senha atual dessa conta; nunca associa identidades apenas por coincidência de endereço. CUSTOMER existente é preservado ao adicionar EMPLOYEE. Aceitação revoga sessões anteriores.
- Bootstrap é CLI operacional com acesso ao ambiente, somente quando não existe admin ativo. Não existe endpoint público nem senha inicial default. Link de uso único chega pela caixa configurada.

O cadastro assistido e o vínculo `Customer` ↔ `User` pertencem a PL3-07. O nome exibido nesta fase é um dado básico da identidade; não cria perfil comercial, CPF, telefone, pet ou cadastro operacional por inferência.
