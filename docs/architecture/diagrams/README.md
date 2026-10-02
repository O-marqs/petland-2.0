# Diagramas atuais — PetLand 3.0

Referência funcional: `2549523 / 0007_product_operations`.

Draw.io editável e SVG/Mermaid compartilham o modelo em [render_architecture.py](../../../scripts/render_architecture.py).
Coordenadas, labels, nós e relações são determinísticos; não é exportação via serviço externo.

`python scripts/render_architecture.py` regenera; `python scripts/render_architecture.py --check` detecta divergência.
Editar o modelo e regenerar preserva coerência. Edições manuais no Draw.io continuam editáveis, mas não são importadas pelo gerador.
Os diagramas L1–L3 são aproximações C4, não certificação formal. Setas de containers são comunicação; módulos indicam contratos públicos.

[Abrir arquivo com sete páginas](PetLand_3.0_Architecture.drawio)

## 01-System-Context

Uma loja · personas e dependências atuais

![Uma loja · personas e dependências atuais](system-context.svg)

```mermaid
flowchart LR
  tutor["Tutor / CUSTOMER · Pets, reserva e histórico próprios"]
  staff["Funcionário / EMPLOYEE · Agenda e cuidado do dia"]
  admin["Administrador / ADMIN · Operação, gestão e acessos"]
  petland["PetLand 3.0 · Plataforma operacional de pet shop · Uma loja · monólito modular"]
  smtp["SMTP / Mailpit local · Confirmação, lembrete e pronto · Sem entrega externa comprovada"]
  db["PostgreSQL 17 · Armazenamento interno · Single-node"]
  ops["Operador offline · Migrations, backup e recuperação · Archive e chave no mesmo host"]
  tutor -->|"usa"| petland
  staff -->|"usa"| petland
  admin -->|"usa"| petland
  petland -->|"comunica"| smtp
  petland -->|"persiste"| db
  ops -->|"opera"| db
```

PostgreSQL pertence ao sistema. SMTP atual é local; não há provedor externo contratado.

## 02-Containers

Staging local · containers e processo de outbox

![Staging local · containers e processo de outbox](containers.svg)

```mermaid
flowchart LR
  react["Browser / React SPA · Query, RHF/Zod, TypeScript"]
  nginx["Nginx · Frontend estático e proxy /api · HTTPS localhost:8443"]
  api["FastAPI · 2 Uvicorn workers · Casos de uso síncronos"]
  db["PostgreSQL 17 · SQLAlchemy / psycopg · Volume staging_data"]
  outbox["Outbox processor · Thread no lifespan de cada worker · Claim / lease / retry"]
  smtp["Mailpit · SMTP STARTTLS · UI somente loopback"]
  migration["Alembic job · Executa antes da API · Credencial migrator separada"]
  backup["Ferramentas offline · Backup autenticado local · Restore em banco novo"]
  archive["Archive criptografado · Chave separada / mesmo host · Não publicado"]
  react -->|"HTTPS"| nginx
  nginx -->|"/api"| api
  api -->|"TLS / runtime"| db
  api -->|"lifespan"| outbox
  outbox -->|"fora da transação"| smtp
  outbox -->|"claim"| db
  migration -->|"DDL separado"| db
  backup -->|"dump / encrypt"| archive
  backup -->|"restore isolado"| db
```

Outbox é componente dentro da API, não um container ou broker independente. Entrega at least once.

## 03-Backend-Modules

Composição, fronteiras e dependências internas

![Composição, fronteiras e dependências internas](backend-modules.svg)

```mermaid
flowchart LR
  boot["bootstrap / composition root · Engine, adapters, serviços e routers"]
  system["system · Saúde e revisão do schema · Application / infrastructure / HTTP"]
  identity["identity · Contas, sessões, papéis, auditoria · Public: Actor / HTTP / workforce"]
  customers["customers · Contato e vínculo verificado · Public: acesso / contato"]
  pets["pets · Propriedade e contexto de cuidado · Public: referências / booking"]
  catalog["catalog · Serviço e oferta por porte · Public: booking_service"]
  scheduling["scheduling · Agenda, reserva, cuidado e gestão · Public: coordination / primeiro lock"]
  layers["Camadas nos módulos comerciais: presentation → application → domain · Infrastructure implementa ports; bootstrap compõe. Public conecta módulos na mesma transação. · System é mínimo, sem domínio comercial. Fitness functions verificam imports absolutos e relativos."]
  boot -->|"compõe"| system
  boot -->|"compõe"| identity
  customers -->|"contratos públicos"| identity
  scheduling -->|"Actor / workforce / audit"| identity
  scheduling -->|"oferta pública"| catalog
  scheduling -->|"pet / care context"| pets
  scheduling -->|"contato público"| customers
```

Modular Monolith with Hexagonal Architecture and pragmatic DDD principles. Sem microservices / DDD puro.

## 04-Booking-Transaction

Confirmação e garantias transacionais

![Confirmação e garantias transacionais](booking-transaction.svg)

```mermaid
flowchart LR
  review["1 · React / tutor · Consulta não segura vaga · Resumo + confirmar explicitamente"]
  request["2 · HTTP · Sessão + origem / CSRF · Versões + Idempotency-Key"]
  lock["3 · Transação · Primeiro lock: configuração da loja · Reautoriza ator e proprietário"]
  validate["4 · Revalidação · Oferta, escala, pessoa, duração · Buffers, conflitos e pools"]
  write["5 · PostgreSQL · Reserva + snapshot + evento · Auditoria + replay + outbox"]
  integrity["6 · GiST / constraints · Exclusão pet e responsável · Commit ou rollback"]
  response["7 · Resposta · 201 confirmado / 409 conflito · Mesma chave recupera resultado"]
  worker["8 · Depois do commit · Claim persistido da outbox · SMTP fora da transação de reserva"]
  smtp["9 · SMTP aceito · Retry / lease persistidos · Não comprova leitura externa"]
  review -->|"POST"| request
  request -->|"begin"| lock
  lock -->|"sob lock"| validate
  validate -->|"pessoa elegível"| write
  write -->|"atomicidade"| integrity
  integrity -->|"resultado"| response
  integrity -->|"outbox após commit"| worker
  worker -->|"at least once"| smtp
```

Pools são validados no domínio sob o lock comum. Não existe terceira exclusion constraint para equipamento.

## 05-Security-Trust-Boundaries

Entradas não confiáveis e privilégios separados

![Entradas não confiáveis e privilégios separados](security-boundaries.svg)

```mermaid
flowchart LR
  browser["Browser não confiável · Formulário / URL / payload · Cookie opaco HttpOnly / Secure"]
  proxy["Fronteira de transporte · Nginx / TLS local · Mesma origem para /api"]
  identity["Servidor de aplicação · Sessão, CSRF, RBAC e owner · Argon2id / tokens únicos"]
  runtime["Runtime PostgreSQL · Sem superuser / DDL · Audit sem UPDATE"]
  public["Projeção do tutor · Só seus objetos / resumo público · Sem notas ou motivos internos"]
  internal["Operação / gestão · Papel + contexto no servidor · Notas internas / auditoria"]
  privileged["Operador offline privilegiado · Migrations / backup / restore · Credencial e ferramentas separadas"]
  private["Fronteira de artefatos · .env, contas, chaves e dumps fora do Git · Preview serve somente docs/case"]
  browser -->|"HTTPS"| proxy
  proxy -->|"validar entrada"| identity
  identity -->|"privilégio mínimo"| runtime
  identity -->|"autorização contextual"| internal
  identity -->|"projeção filtrada"| public
  privileged -->|"DDL / recovery"| runtime
  privileged -->|"custódia local"| private
```

Menus não são controles de segurança. SMTP aceito não é entrega externa. TLS/backup não cobrem perda do host.

## 06-Data-Flow

Dados operacionais, projeções e comunicação

![Dados operacionais, projeções e comunicação](data-flow.svg)

```mermaid
flowchart LR
  forms["Entradas autenticadas · Contato / pet / serviço / horário · Contratos OpenAPI tipados"]
  domain["Casos de uso / domínio · Propriedade e regras · Transação por mutação"]
  records["PostgreSQL · Estado + snapshot contratado · Notas / eventos / auditoria"]
  outbox["Outbox privada · Destinatário / corpo / prazo · Lease / tentativas / supressão"]
  tutor["Tutor · Seus pets / reservas / resumo · Estado local da comunicação"]
  staff["Equipe · Agenda / alerta de perfil · Últimos três cuidados anteriores"]
  metrics["Gestão agregada · Coorte: início previsto · Estado atual / responsável final"]
  smtp["SMTP / Mailpit · Envio fora da transação · Sem recibo de leitura externa"]
  backup["Backup offline autenticado · Todas as tabelas + ACLs + GiST → banco novo reconciliado · Archive e chave separados no mesmo host; não é projeção pública"]
  forms -->|"validar"| domain
  domain -->|"persistir junto"| records
  records -->|"mesmo commit"| outbox
  outbox -->|"claim / retry"| smtp
  records -->|"SQL agregado"| metrics
  records -->|"contexto interno"| staff
  records -->|"owner / público"| tutor
  records -->|"banco completo, offline"| backup
```

Concluídos usam responsável final; não há divisão de esforço. Indicadores não são receita nem ranking.

## 07-Deployment-Staging

CURRENT · máquina local / sem alta disponibilidade

![CURRENT · máquina local / sem alta disponibilidade](deployment.svg)

```mermaid
flowchart LR
  user["Navegador local · CA de teste · https://localhost:8443"]
  web["petland7 / web · Nginx + React estático · Não root / read-only"]
  api["petland7 / api · 2 workers + outbox threads · Sem porta publicada"]
  pg["petland7 / postgres · PostgreSQL 17 single-node · Volume persistente / TLS"]
  mail["petland7 / mailpit · STARTTLS · UI loopback :8026"]
  job["petland7 / migrate · Job separado antes da API · Alembic head 0007"]
  host["Host / ferramentas offline · Backup local / chave separada · Restore + reconciliação + ativação"]
  other["Ambientes independentes · petland3: dev Vite / outro volume; testes PG efêmeros · petlanddocs: captura temporária sintética / imagem funcional 2549523"]
  future["POSSIBLE PRODUCTION EVOLUTION · Não implementada: provedor, Multi-AZ, PITR, SMTP externo, off-host · SLO/RPO/RTO, observabilidade e balanceamento dependem de D10"]
  user -->|"HTTPS local"| web
  web -->|"/api"| api
  api -->|"verify-full"| pg
  api -->|"STARTTLS"| mail
  job -->|"migrator / DDL"| pg
  host -->|"dump / restore"| pg
```

Rede privada entre containers; portas públicas somente loopback. Archive local não cobre perda da máquina.
