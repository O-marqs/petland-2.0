# PetLand 3.0 — visão do produto

**CURRENT STATE · código de referência `2549523` · schema `0007_product_operations`.** Release final de portfólio/demo **3.0.0** na `main`; produção comercial não declarada. Aceite humano/leitor de tela e gates D10 continuam pendentes. O [plano consolidado original](PetLand_3.0_Plano_Consolidado.md) é discovery, não uma lista de funcionalidades já entregues.

## Visão e problema

Organizar a jornada do cuidado de um pet, da disponibilidade até a conclusão, conectando tutor, equipe e gestão de **uma loja**. O tutor encontra preço, tempo e horário sem depender de uma conversa para cada reserva. A equipe começa pelo trabalho do dia e pelo contexto do animal. A gestão configura pessoas, habilidades, expediente e recursos físicos sem apagar o histórico ou invalidar silenciosamente uma reserva.

O projeto é um CRM operacional de pet shop para o portfólio de Lucas Marques. As personas são hipóteses de produto orientadas pelas decisões do autor; não houve pesquisa com lojas ou validação comercial.

## Quem usa

| Perfil                 | Jornada principal                                                   | O que consegue fazer                                                                                                                                                                                               |
| ---------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Tutor / CUSTOMER       | Conta → confirmação do e-mail → contato → pet → reserva → histórico | Gerir seus pets, consultar horários, revisar preço/duração, confirmar, cancelar ou reagendar dentro da política e consultar estado/resumo público.                                                                 |
| Funcionário / EMPLOYEE | Painel diário → minha agenda/equipe → atendimento                   | Cadastrar contatos/pets de forma assistida, reservar, registrar chegada/início/conclusão/falta, notas, extensão e transferência; configurar serviços, pessoas, escala e capacidade. Recepção usa este mesmo papel. |
| Administração / ADMIN  | Operação → indicadores → configuração/acessos                       | Tem acesso operacional, consulta gestão/auditoria e administra convites, papéis e revogação de acesso. Não há um papel separado de gerente.                                                                        |

## O produto implementado

**Primeiro acesso guiado.** Criar uma identidade não cria um tutor comercial nem um pet automaticamente. A tela de confirmação explica o próximo passo e a caixa de e-mail local; depois do acesso, a área do tutor orienta perfil, pet e reserva. Contatos criados pela equipe podem ser associados a uma conta por convite verificado, sem fusão por nome.

**Pets e ofertas.** Perfil com espécie, raça opcional, porte, nascimento opcional/estimado, cuidados gerais, alergias e manejo. Arquivar preserva o histórico. Serviços têm compatibilidade por espécie e preço/duração por porte; o que foi contratado fica no snapshot da reserva.

**Disponibilidade real e confirmação.** O horário precisa caber na loja aberta, na escala efetiva de uma pessoa apta, na duração com preparação/intervalo e nos recursos físicos vinculados, sem colisão de pet ou responsável. A consulta não segura a vaga. O tutor vê um resumo e confirma explicitamente; o servidor revalida tudo dentro da transação. Atribuição automática prioriza menor carga planejada diária entre pessoas elegíveis, com desempate estável.

**Operação diária.** Painel com contagens do dia, próximos cuidados, pendências e carga; agenda pessoal por padrão, com visão de equipe e filtro por pessoa. Estados: reservado → chegou → em atendimento → concluído; cancelamento e falta são distintos. Horário previsto e instantes reais ficam separados. Extensão exige nova validação de disponibilidade. Transferência pede motivo, pessoa apta e período livre; registra antes/depois sem reescrever preço ou serviço.

**Continuidade do cuidado.** Alergia do perfil aparece como alerta crítico; iniciar exige reconhecimento da versão atual do pet. O detalhe operacional reúne os três cuidados concluídos anteriores, responsável, duração e notas. Notas internas e motivos operacionais não aparecem na projeção do tutor; resumo público pode acompanhá-lo no histórico.

**Equipe por data e capacidade física.** Em `/operacao/escala`, indicar quem trabalha e em quais períodos altera somente aquela data; quem não foi incluído fica indisponível nela. Restaurar remove a exceção e volta à semana habitual. Pools como banheiras/mesas limitam serviços simultâneos durante todo o intervalo ocupado. Mudanças têm prévia de impacto; conflitos devem ser resolvidos antes de salvar. O sistema não cancela ou redistribui reservas automaticamente.

**Comunicação e gestão.** Confirmação, alteração, lembrete configurável e aviso de pronto usam comunicação persistida com a mutação. Falha de SMTP conserva tentativas. O histórico diferencia agendado, tentativa, descarte e aceitação SMTP. Gestão mostra contagens por estado, pets/tutores únicos concluídos, cuidados por responsável final/serviço, duração real, atraso e desvio. O recorte é início previsto no período de 1–31 dias e estado atual; ocupação usa minutos reservados e calendários atuais. Não representa receita ou ranking de desempenho.

## Decisões que moldam a experiência

| Decisão                                               | Consequência                                                                                                                                         |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| D02: profissional atribuído pelo servidor             | Tutor escolhe pet, serviço e horário; não escolhe ou prefere uma pessoa.                                                                             |
| D03: confirmação explícita                            | Escolher horário abre revisão; confirmar é uma ação separada.                                                                                        |
| D04/D05: sem taxa; valores/tempos por porte e serviço | Preço é informado antes de confirmar. Não há cobrança, pagamento ou taxa de cancelamento.                                                            |
| D06/D07: contato mínimo e acesso contextual           | Nome/e-mail, telefone/endereço opcionais; conta, tutor e pet são identidades distintas. Equipe assiste clientes; gestão de acessos é administrativa. |
| D08/D12: banco novo, sem importação histórica         | Código e histórico 2.0 preservados; nenhum banco MySQL foi convertido.                                                                               |
| D10: publicação adiada                                | Demonstração local com TLS, Mailpit e backup no host; não é uma loja em produção.                                                                    |

## Limites e escolhas fora do escopo

Uma reserva contém **um pet e um serviço**. Vários pets podem ter reservas individuais, sem confirmação conjunta ou grupo atômico. Não existe troca do serviço durante execução, férias por intervalo, redistribuição em lote, console único de recepção, preferência de profissional, recursos físicos por etapa, ficha estruturada de shampoo/máquina ou divisão de esforço entre responsáveis.

Indicadores de recorrência/inatividade, demanda por faixa, ticket e taxas com denominadores próprios continuam ausentes. Ocupação pode superar 100% após redução do calendário atual; isso é explicado na interface. Não há multiempresa, estoque, prontuário veterinário ou pagamentos. Não há SMTP externo comprovado, disponibilidade Multi-AZ, backup fora do host, PITR ou RPO/RTO produtivos.

Os testes e medições são evidências técnicas delimitadas. Aceite humano dos três perfis e com leitor de tela seguem pendentes. [Matriz completa de dores e lacunas](functional-gap-analysis.md) · [RNFs e resultados](../architecture/non-functional-requirements.md).

## Do 2.0 ao 3.0

O diagnóstico do legado Flask/MySQL encontrou lógica de SQL/HTTP acoplada, referências por CPF, contratos divergentes e disponibilidade por contagem. O 3.0 reconstrói o domínio em um monólito modular, contratos HTTP tipados e PostgreSQL transacional, com proteção de propriedade e intervalos concorrentes. A experiência evoluiu de templates/formulários para jornadas distintas e uma identidade editorial de pet shop. O [case](../case/README.md) conserva capturas históricas com proveniência; a [UX atual](../ux/PetLand_3.0_UX_Final.md) apresenta capturas separadas desta revisão.

**Próxima leitura:** [arquitetura](../architecture/overview.md), [teste manual](../runbooks/manual-acceptance.md) ou [execução local](../runbooks/local.md).
