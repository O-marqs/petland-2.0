# Decisões arquiteturais

Índice atual para leitura das decisões, motivos e consequências. Os documentos de fase registram o momento da decisão; complementos posteriores não são reescritos como se já existissem naquela fase. [Arquitetura atual](../architecture/overview.md).

| ADR              | Título                                     | Status                                             | Área             | Motivo → consequência                                                                                                     | Link                                             |
| ---------------- | ------------------------------------------ | -------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| 001              | Monólito modular / hexagonal pragmática    | Aceita P01, vigente                                | Estrutura        | Uma loja e equipe pequena → ports/adapters, composição explícita, sem serviços distribuídos.                              | [Fundação abaixo](#fundação-e-notas-preservadas) |
| 002              | PostgreSQL / SQLAlchemy síncrono / Alembic | Aceita P01, vigente                                | Persistência     | Integridade transacional → migrations separadas e testes reais de PostgreSQL.                                             | [Fundação abaixo](#fundação-e-notas-preservadas) |
| 003 / 006 / 010  | Agenda, consistência e configuração        | Aceita P04, complementada por 012/016              | Scheduling       | Capacidade real e concorrência → primeiro lock da loja, GiST, versões, snapshot/idempotência/outbox.                      | [Agenda](0003-scheduling.md)                     |
| 004              | Identidade e autorização                   | Aceita P02, vigente                                | Segurança        | Propriedade e revogação no servidor → sessão opaca/CSRF/RBAC, sem token no localStorage.                                  | [Identidade](0004-identity.md)                   |
| 005              | SPA React / contratos gerados              | Aceita P01, vigente                                | Frontend         | Forms/estado remoto tipados → Query/RHF/Zod e OpenAPI da aplicação real.                                                  | [Fundação abaixo](#fundação-e-notas-preservadas) |
| 007 (baseline)   | Preservar legado / worktree                | Aceita P01, vigente                                | Histórico        | Proteger código e mudanças locais → tag baseline, worktree e sem importação implícita.                                    | [Fundação abaixo](#fundação-e-notas-preservadas) |
| 0007 (cadastros) | Tutor, pet e oferta por porte              | Aceita P03, vigente                                | Produto/dados    | Conta não é tutor; preço/tempo dependem de porte → vínculo verificado e propriedade independente.                         | [Cadastros](0007-p03-customers-pets-catalog.md)  |
| 008              | Hospedagem externa                         | Condicionada a D10                                 | Solução          | Provedor/orçamento não definidos → somente staging local; sem promoção externa.                                           | [Notas abaixo](#propostas-ainda-condicionadas)   |
| 009              | Dados / retenção                           | Decisões locais aceitas; retenção externa pendente | Dados            | Contato mínimo, banco novo e ausência de importação → D06/D08/D12; custódia externa continua dependente de D10.           | [Decisões de produto](../product/decisions.md)   |
| 011              | Runtime / ferramentas / logs               | Aceita P01, vigente                                | Engenharia       | Reprodução e logs seguros → uv/pnpm lockfiles, Compose loopback e allowlist.                                              | [Fundação abaixo](#fundação-e-notas-preservadas) |
| 012              | Execução, visibilidade e gestão            | Aceita P05, vigente                                | Operação         | Acompanhar cuidado real → estados/instantes/notas internas-públicas, fórmulas delimitadas.                                | [Operação](0012-p05-operations.md)               |
| 013              | Hardening e verificação                    | Implementada P06, complementada                    | Qualidade        | Leitura/carga/foco verificáveis → índices/agregação, proteção HTTP e ensaios reproduzíveis.                               | [Hardening](0013-p06-hardening.md)               |
| 014              | Demo / backup / recovery                   | Aceita P07, local                                  | Recuperação      | Preservar origem e comprovar cópia → archive autenticado, restore novo e reconciliação, sem off-host/SLA.                 | [Recovery](0014-p07-operations.md)               |
| 015              | Candidata / case                           | Aceita P08; aceite/publicação pendentes            | Portfólio        | Mostrar jornadas com proveniência → vídeo histórico, pacote local e gates explícitos.                                     | [Case](0015-p08-release-case.md)                 |
| 016              | Escala / capacidade / continuidade         | Implementada, vigente                              | Operação/produto | Resolver dores diárias → escala por data, pools, transferência, alertas, comunicação e atribuição final; sem lote/grupos. | [Evolução](0016-operational-evolution.md)        |

**Numeração histórica:** o índice inicial usou ADR-007 para baseline; o arquivo P03 recebeu `0007` para cadastros. A colisão é mantida explícita por título/área, sem renumerar evidência antiga. 006/010 foram consolidadas no ADR-003; não existem arquivos separados fictícios. As decisões 001/002/005/011 foram registradas neste índice e no plano, não em arquivos individuais.

## Fundação e notas preservadas

Aceitas pelo pedido de P01, em 23/09/2026:

- **ADR-001:** monólito modular e hexagonal pragmática. Domain depende apenas de Python; application define ports e coordena; infrastructure implementa ports; presentation adapta HTTP; bootstrap compõe. Nenhum repositório genérico ou framework de DI.
- **ADR-002:** PostgreSQL, SQLAlchemy 2 síncrono, psycopg e Alembic. Um engine por processo e conexão contextual. Migrações como comando separado, nunca no startup de cada worker. P01 cria apenas baseline técnico, sem tabelas comerciais prematuras.
- **ADR-005:** React/TypeScript/Vite SPA, TanStack Query, React Hook Form/Zod. Tokens CSS e componentes próprios. OpenAPI exportado da aplicação real; tipos gerados e cliente tipado a partir desses tipos. Contratos futuros documentados separadamente, sem endpoints falsos.
- **ADR-007:** preservar histórico/tag e desenvolver na branch `petland-3.0`. Worktree isolado para conservar as alterações não commitadas da main. Retirar legado/dependências do estado ativo após baseline recuperável.
- **ADR-011:** `uv` + Python 3.13 e workspace `pnpm` + Node 22. Lockfiles obrigatórios. Compose de desenvolvimento com portas de loopback. Logs JSON sem payloads, SQL, credenciais ou caminho arbitrário do cliente; request ID gerado no servidor.

## Identidade aprovada em P02

- **ADR-004:** identidade única, sessão opaca revogável no PostgreSQL, CSRF, hash seguro e D07 aprovada. [Decisões de implementação e limites](0004-identity.md).

## Agenda implementada em P04

- **ADR-003 / ADR-006:** unidade por pessoa, transação e exclusões, snapshots e eventos — [agenda, concorrência e avisos](0003-scheduling.md).
- **ADR-010:** parâmetros operacionais configuráveis, sem valores comerciais semeados; termos contratados e regras de assistência no mesmo ADR.

## Propostas ainda condicionadas

- **ADR-008:** hospedagem externa — D10; backup/restore local ensaiado no ADR-014, sem deploy de produção.
- **ADR-009:** dados e retenção — D06/D08/D12.

Mudanças exigem nova decisão documentada, incluindo motivo, impacto e testes. Não alterar silenciosamente o plano.

- [0007 — Cadastros, pets e ofertas por porte](0007-p03-customers-pets-catalog.md): decisões do pedido P03, vínculo, propriedade, preços/duração e evolução para P04.
- [0012 — Operação e gestão P05](0012-p05-operations.md): estados, atrasos, notas, privacidade, histórico, indicadores e auditoria.

- [0013 — Hardening e verificação P06](0013-p06-hardening.md): agregações, índices, proteção HTTP, foco e medições reproduzíveis.
- [0014 — Dados e recuperação P07](0014-p07-operations.md): demo isolada, servidor estático/TLS, backup autenticado e restore reconciliado; limites D08/D10/D12.
- [0015 — Candidata e case P08](0015-p08-release-case.md): versão de revisão, proveniência antes/depois, vídeo real, pacote local e gates explícitos.
- [0016 — Evolução operacional](0016-operational-evolution.md): escala coletiva, pools físicos, transferência, alertas críticos, contexto anterior, comunicação e atribuição de indicadores.
