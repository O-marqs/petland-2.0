# ADR 0007 — Cadastros, vínculo verificado e ofertas por porte

Estado: aceito para P03 em 28/09/2026, conforme pedido P03. Completa as decisões anteriores sem editar o plano ou PDF originais.

O CRM de uma loja é uma demonstração de portfólio, com base nova. P03 implementa RF02, RF03, RF04 e a parte de RF12 relativa à apresentação/catálogo, nos cards PL3-07–09. Não cria agendamentos ou indicadores fictícios.

## Cadastros e autorização

Identidade e cadastro comercial são distintos. Nome, e-mail, telefone e endereço compõem o cadastro; telefone/endereço opcionais. Não coletamos CPF, idade mínima ou nascimento do tutor. E-mail é obrigatório para permitir comunicação/vínculo; não é chave de mesclagem: famílias podem compartilhar contato e cadastros assistidos não viram contas automaticamente. Dados de identidade e senha nunca aparecem nas respostas comerciais.

A própria conta CUSTOMER verificada pode criar/editar um cadastro e seus pets. EMPLOYEE/ADMIN podem cadastrar e editar clientes, seus pets e serviços. Gestão de papéis/acessos permanece ADMIN (recomendação D07 de separar autorização administrativa de operação). Configuração operacional de capacidade e comunicação de reagendamento/cancelamento será entregue em P04/P05.

O vínculo exige link aleatório de uso único, hash SHA-256 persistido, validade de 24 h e conta CUSTOMER com o mesmo e-mail verificado. O usuário confirma explicitamente. Novo link ou edição do cadastro invalida convites anteriores. Cadastro já vinculado ou conta com outro perfil comercial gera conflito, sem mesclagem automática. Advisory lock por conta e lock da linha do cliente serializam criação/vínculo. Links saem por SMTP/Mailpit local e não são enviados em URLs HTTP: fragmento removido na interface. Falha SMTP gera evento seguro; a equipe pode solicitar reenvio. Não existe promessa de entrega pública sem D10.

## Pets e referências

Nome, espécie, porte e sexo (desconhecido permitido); raça e nascimento opcionais, data estimada identificada. Cuidados informados são compartilhados com tutor/equipe; não são notas internas de atendimento. O pet tem tutor imutável no contrato e acesso filtrado por proprietário. Raça deve corresponder à espécie em aplicação e FK composta no PostgreSQL. Data futura é rejeitada no fuso America/Sao_Paulo.

Referências iniciais: cachorro/gato e um conjunto pequeno de raças, incluindo SRD; desconhecida/não listada permite raça nula. Estas são referências, não dados comerciais sintéticos. Ampliação da taxonomia exige migration versionada; P03 não inclui editor de raças. Arquivar/restaurar conserva a linha e a auditoria. P04 deve integrar o bloqueio/revalidação por reservas futuras antes de permitir arquivo com compromissos.

## Ofertas

Serviço contém nome, descrição, espécies e opções por porte SMALL/MEDIUM/LARGE. Cada opção tem preço Decimal em BRL e duração inteira de 1–1440 minutos; preço zero permitido, máximo técnico R$ 9.999.999,99. Serviço pode oferecer subconjunto dos portes, sem duplicações. Valores do exemplo do usuário não são defaults comerciais. Nenhum serviço é semeado na migration.

Criação começa inativa na interface; ativação é explícita. Catálogo público filtra somente ativos por espécie/porte. Atualização exige versão e lock, incrementa versão e substitui opções na mesma transação. Leituras mantêm lock compartilhado do serviço durante a leitura das opções, evitando misturar uma versão com condições de outra. P04 copiará nome, preço, duração, porte e versão para snapshots imutáveis de reserva; P03 não expõe disponibilidade ou reserva simulada.

## Fronteiras e evolução

customers, pets e catalog mantêm domínio/aplicação sem infraestrutura. Ports específicos e adapters PostgreSQL; bootstrap compõe. Contratos públicos de identity fornecem autenticação/CSRF e auditoria transacional; customers resolve proprietário para pets; pets fornece referências para catalog. Não há repositório genérico.

Edições exigem versão e retornam 409 sem sobrescrever mudanças concorrentes. Escritas comerciais e auditoria confirmam na mesma transação. IDs não autorizados de pets retornam 404; busca de clientes exige equipe. API/DTOs gerados e frontend RHF/Zod/Query mantêm estados vazios, erros e recuperação sem limpar formulários.
