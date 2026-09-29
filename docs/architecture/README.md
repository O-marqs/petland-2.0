# Arquitetura implementada — P01/P02

RF13; RNF05/07/09. Monorepo e monólito modular, FastAPI síncrono com psycopg/SQLAlchemy. Veja plano integral §§9–16 e ADR-001/002/005/007/011.

```mermaid
flowchart LR
  Browser[React / TanStack Query] -->|mesma origem /api| Proxy[Vite local]
  Proxy --> HTTP[Presentation: router e schemas]
  HTTP --> UC[Application: saúde e casos de uso de identidade]
  UC --> Domain[Domain: conta, papéis, sessão e tokens]
  DBAdapter[Infrastructure: PostgresReadinessProbe / PostgresUnitOfWork] -. implementa ports .-> UC
  DBAdapter --> DB[(PostgreSQL)]
  Mail[Infrastructure: SmtpMailer] -. implementa port .-> UC
  Mail --> SMTP[Mailpit local]
  Bootstrap[Bootstrap: settings / factory / composição] --> HTTP
  Bootstrap --> DBAdapter
```

`system` é um módulo técnico mínimo com consulta operacional verdadeira. `identity` implementa contas, papéis, sessões, tokens e casos de uso de autorização. Domínio/aplicação dependem apenas de Python e ports; adapters concretos ficam em infraestrutura e são compostos no bootstrap. O verificador de arquitetura inclui testes negativos com imports proibidos. Não há motor de agenda ou pets nesta fase.

O engine tem pool limitado, pre-ping, connect/pool/statement timeouts e descarte no lifespan. Endpoints de I/O bloqueante usam `def`. Falha do banco não derruba liveness. Readiness lê a revisão Alembic e exige correspondência exata; indisponibilidade, schema ausente, revisão incompatível ou permissão insuficiente resultam em 503 sem DSN.

O baseline `0001_foundation` contém zero DDL de negócio. `0002_identity` cria identidade; `0003_catalogs` acrescenta clientes/pets/ofertas; `0004_scheduling` acrescenta calendário, recursos, reservas, eventos, idempotência e outbox. A cadeia Alembic é exercitada no PostgreSQL com upgrade, repetição, downgrade e comparação com metadata. Estados de execução de atendimento serão P05.

O usuário runtime `petland_app` não é superuser e recebe privilégios por tabela: escrita de identidade, leitura/inserção de auditoria e nenhuma permissão DDL. A credencial de migrations é separada. O administrador local do container é exclusivo de desenvolvimento. Não há migration no startup da API.

O cliente HTTP usa tipos gerados de OpenAPI, cookies habilitados, abort/cancelamento e timeout. Antes de mutações, obtém CSRF vinculado à sessão e envia o header. Mutações não são repetidas automaticamente. A consulta de saúde usa a revisão real da API/banco; estados de falha não permanecem verdes por dados antigos. Identidade e gestão usam respostas reais da API, incluindo erros padronizados.

Scheduling consulta snapshots por contratos públicos dos demais módulos. Toda mutação crítica começa pelo lock da configuração; PostgreSQL mantém exclusões independentes de intervalos. Avisos são persistidos junto com a reserva e entregues fora da transação pelo worker. A interface permite repetir explicitamente uma confirmação com a mesma chave. Ver [ADR-003](../adr/0003-scheduling.md).

## Limites de segurança atuais

Sessões opacas, Argon2id, CSRF, autorização contextual, revogação, rate limit compartilhado, limites de body e auditoria são descritos no [ADR 004](../adr/0004-identity.md). URLs brutas, query strings, bodies, tokens e mensagens de exceção não são registrados. Swagger é local; staging/prod exigem HTTPS, TLS PostgreSQL verificado e SMTP com STARTTLS. Essas validações não equivalem a uma revisão completa ou release de produção.

Referências técnicas consultadas: [lifespan FastAPI](https://fastapi.tiangolo.com/advanced/events/), [pool SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/pooling.html), [Vite](https://vite.dev/guide/), [openapi-fetch](https://openapi-ts.dev/openapi-fetch/).
