# PetLand 3.0 — Architecture Overview

**CURRENT · `main` · release de portfólio `3.0.0` · schema `0007_product_operations`.** Código funcional de referência `2549523`; promoção de versão sem mudança arquitetural ou comercial.

**Modular Monolith with Hexagonal Architecture and pragmatic DDD principles.** Um processo de aplicação com seis módulos internos, uma implantação local e um PostgreSQL compartilhado. Não são microservices nem DDD puro. [Produto](../product/product-overview.md) · [Dados](data-model.md) · [Autorização](authorization.md) · [ADRs](../adr/README.md).

## C4 L1 — System Context

![Contexto atual](diagrams/system-context.svg)

Tutor gerencia seus próprios objetos; funcionário opera cadastros, agenda e atendimento; administrador acrescenta gestão/acessos. SMTP é a integração de comunicação, atualmente Mailpit local. PostgreSQL é armazenamento interno do sistema, mostrado para explicitar dependência, não um produto externo contratado. Operador offline usa comandos de migrations/backup/recovery; essas ferramentas não são endpoints do tutor. Há apenas uma loja.

## C4 L2 — Containers

![Containers atuais](diagrams/containers.svg)

React/TypeScript é uma SPA entregue por Nginx; chamadas `/api` usam a mesma origem. FastAPI adapta HTTP a casos de uso síncronos, SQLAlchemy/psycopg persistem no PostgreSQL. TanStack Query trata estado remoto; RHF/Zod trata formulários; OpenAPI gera tipos e cliente em [api-contract](../../packages/api-contract/openapi.json).

O processador de outbox é **uma thread no lifespan de cada worker da API**, iniciada fora de `test`, e não um container/fila externa. Claim/lease no banco coordenam as threads; envio SMTP ocorre fora da transação de reserva. É entrega **at least once**, com risco de duplicação se SMTP aceitar antes de uma falha na marcação local. Não há garantia de recebimento/leitura externa.

Alembic é um job separado, com credencial migrator; runtime não tem DDL. Ferramentas offline criptografam backup, restauram em banco novo, reconciliam tabelas/grants/exclusões e só então ativam a cópia. [Composição real](../../infra/compose/staging.yaml) · [Lifespan](../../apps/api/src/petland/bootstrap/app.py) · [Outbox](../../apps/api/src/petland/modules/scheduling/infrastructure/notifications.py).

## C4 L3 — Backend Components

![Módulos e dependências](diagrams/backend-modules.svg)

| Módulo     | Responsabilidade                                                    | Colaboração pública                                                                                              |
| ---------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| system     | Liveness/readiness, revisão Alembic esperada                        | Módulo técnico mínimo; application/infrastructure/presentation, sem domínio comercial artificial.                |
| identity   | Contas, papéis, sessão, CSRF, convites, tokens, auditoria           | Actor, HTTP identity, workforce e auditoria.                                                                     |
| customers  | Contatos e vínculo verificado a uma conta                           | Acesso ao tutor e contato para reserva/comunicação.                                                              |
| pets       | Propriedade, referências, perfil e contexto de cuidado              | Referências, pet para reserva e care context.                                                                    |
| catalog    | Serviços e ofertas por porte/espécie                                | Oferta para contratação.                                                                                         |
| scheduling | Calendários, escala, pools, reserva, execução, indicadores e outbox | Coordenação do primeiro lock e proteção de pet/pessoa. Gestão é leitura deste módulo, sem módulo de BI fictício. |

`domain` contém modelos/valores/regras em Python; `application` coordena autorização, transação e ports; `infrastructure` implementa persistência/SMTP; `presentation` adapta schemas e HTTP. `bootstrap` compõe explicitamente engines, serviços, routers e adapters. Os contratos `public` expõem apenas as colaborações usadas; alguns helpers SQL participam da mesma sessão/transação no adapter consumidor. Não há bancos por módulo ou barreira de rede interna.

**Dependency inversion:** application depende de ports pequenas; o adapter implementa essas interfaces. HTTP não constrói ORM, e domínio não importa FastAPI/SQLAlchemy. Isso permite testes de regras/casos de uso sem banco e testes reais dos adapters com PostgreSQL. As camadas são internas aos módulos; dependência de execução não deve ser confundida com import de implementação.

**DDD pragmático:** linguagem de tutor/pet/oferta/reserva/cuidado, valores de calendário/intervalo, invariantes e snapshot contratado. Não alegamos event sourcing, CQRS completo, agregados independentes com bancos separados ou contextos formalmente validados com especialistas. Eventos persistidos são histórico operacional; não reconstituem todo o estado.

**Architecture fitness functions:** [check_architecture.py](../../scripts/check_architecture.py) verifica imports absolutos/relativos, dependência para dentro, `shared` sem dependência de módulos e colaboração externa via `public`; testes negativos provam rejeições. [check_repository.py](../../scripts/check_repository.py) verifica artefatos privados/segredos conhecidos no estado ativo. Contratos gerados são comparados à aplicação real; migrations são confrontadas com metadata no PostgreSQL. São verificações específicas, não uma prova de correção de qualquer arquitetura.

## Reserva, concorrência e consistência

![Transação de confirmação](diagrams/booking-transaction.svg)

A consulta de horários é uma oferta sem retenção de vaga. Confirmar inclui sessão, CSRF, versões e chave de idempotência. O **primeiro lock é a configuração do estabelecimento**. A transação reautoriza tutor/objeto, revalida oferta, prazo, calendário, escala, habilidade, duração/buffers e pools; seleciona uma pessoa elegível com menor carga planejada diária e persiste reserva/snapshot/evento/auditoria/resposta idempotente/outbox juntos.

Versões detectam edição obsoleta; lock pessimista serializa mutações críticas da loja; exclusões GiST impedem sobreposição por pet e responsável. Pools físicos são invariantes do domínio sob o lock comum, não uma terceira exclusion constraint. Erro causa rollback; mesma chave/payload recupera a resposta; chave reutilizada com outro payload conflita. A serialização simplifica integridade de uma loja e impõe contenção deliberada. [Dados e garantias](data-model.md) · [Agenda](../adr/0003-scheduling.md) · [Evolução operacional](../adr/0016-operational-evolution.md).

## Segurança e fluxo de dados

![Fronteiras de confiança](diagrams/security-boundaries.svg)

Browser é entrada não confiável. RBAC e propriedade são impostos no servidor, incluindo projeções públicas de notas/histórico; ocultar menu não autoriza. Sessão opaca persistida e revogável, cookies HttpOnly/Secure no staging, CSRF vinculado à sessão/origem, Argon2id e tokens de uso único. A credencial runtime tem privilégios por tabela e auditoria sem UPDATE; migrations/backup são operações offline privilegiadas. Logs usam allowlist e request ID gerado no servidor. [Matriz completa](authorization.md).

![Fluxo de dados](diagrams/data-flow.svg)

Dados de contato/pet chegam por formulários e contratos reais; reservas conservam termos comerciais; execução acrescenta instantes/notas/eventos. Leituras do tutor projetam seus objetos e resumo público; operação lê contexto interno; gestão agrega início previsto/estado atual, atribuindo concluídos ao responsável final. Outbox não é log técnico: contém destinatário/corpo privados necessários à comunicação. Backup é criptografado e tem chave separada no mesmo host. [API](api.md) · [Dados](data-model.md).

## Current Deployment Model

**CURRENT: staging local, uma máquina, PostgreSQL single-node.**

![Implantação atual](diagrams/deployment.svg)

`petland7`: Nginx/frontend estático em `https://localhost:8443`, API sem porta pública e dois workers, PostgreSQL 17 com volume, Mailpit em loopback 8026. TLS local navegador→Nginx; API→PostgreSQL usa `verify-full`; SMTP usa STARTTLS. CA local não é certificado público. API/web sem root, somente leitura e capabilities removidas. Job Alembic termina antes da API; readiness exige revisão exata. Desenvolvimento `petland3` usa Vite e outro banco/volume; PostgreSQL dos testes é separado/efêmero.

Backup local autenticado, restore isolado e retorno à origem são ensaiados. Não há agendamento automático de backup, retenção implementada fora do host, failover ou garantia de perda da máquina. As capturas desta documentação usam um **terceiro projeto temporário `petlanddocs`**, mesma imagem funcional e dados exclusivamente sintéticos; não altera o staging de teste pessoal. [Operação/recovery](../runbooks/operations-recovery.md).

## Production Evolution — Not Implemented

**POSSIBLE PRODUCTION EVOLUTION: referência condicional, não capacidade atual.** D10 exige decisão de provedor, orçamento e responsabilidade operacional antes de publicação.

| Possível componente                               | Requisito que justificaria sua adoção                                                                       |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| PostgreSQL gerenciado / Multi-AZ / PITR           | Definir disponibilidade/perda aceitável, testar failover e recuperação; hoje há apenas nó local.            |
| Backup off-host e custódia de chave               | Cobrir perda do host, definir frequência/retenção e executar restore independente.                          |
| PgBouncer / várias instâncias API / load balancer | Dimensionar conexões e concorrência medida; o primeiro lock da loja continua um limite a avaliar.           |
| SMTP externo                                      | Verificar domínio, credenciais, entrega/bounces e privacidade; SMTP aceito não é leitura pelo tutor.        |
| Observabilidade centralizada                      | Logs/métricas/traces, alertas e responsáveis; hoje logs e health endpoints não compõem operação monitorada. |
| SLO, RPO e RTO                                    | Estabelecer objetivos e medir recuperação/carga no ambiente contratado; tempos locais não viram SLA.        |

Nada desta tabela foi implantado. Não se promete escala por número de usuários. [RNFs: meta, medição, evidência e limite](non-functional-requirements.md).

## Diagramas, decisões e revisão

[Draw.io editável com sete páginas](diagrams/PetLand_3.0_Architecture.drawio), SVGs e Mermaid atuais são gerados do [mesmo modelo](../../scripts/render_architecture.py). [Índice e reprodução](diagrams/README.md). Os [Mermaid da candidata P08](release-diagrams.md) continuam como histórico. [ADRs](../adr/README.md) explicam motivos/consequências; [auditoria documental](../evidence/Documentation-review.md) identifica diferenças encontradas. Nenhuma alteração funcional/schema é necessária para esta documentação.
