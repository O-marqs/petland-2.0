# Execução local e qualidade

Leia o [README](../../README.md) para o caminho de entrada e [versão/reprodução](../release/reproducibility.md) para a referência única de checkout, ferramentas e isolamento. Os comandos abaixo partem da raiz. Windows/PowerShell e Linux são suportados pelo mesmo `scripts/dev.py`, sem dependência de Make/bash para desenvolvimento no host.

## Pré-requisitos

- Git; Docker Engine/Desktop em execução com Compose v2.
- Python 3.11+ para `scripts/dev.py`; aplicação Python 3.13 instalada pelo uv ou dentro da imagem.
- Para ferramentas no host: uv 0.12.18, Node 22.14+ (linha 22), pnpm 10.34.5.
- Portas disponíveis: 5173 (web), 8000 (API), 55432 (PostgreSQL dev), 55433 (PostgreSQL efêmero dos testes), 8025 (Mailpit UI) e 1025 (SMTP local). Todas as portas Compose usam 127.0.0.1.

## Instalação

O clone padrão traz PetLand 3.0 da `main`; não é necessário selecionar branch:

```sh
git clone https://github.com/O-marqs/petland.git
cd petland
python scripts/dev.py init
python scripts/dev.py up
```

Versão **3.0.0**, schema `0007_product_operations`, release de portfólio/demo. Legado preservado em `legacy/petland-2.0`. Confira o SHA clonado e a tag `v3.0.0`; [fechamento e ensaio final](../evidence/Portfolio-closure.md).

`python scripts/dev.py init` gera `.env` com segredos locais aleatórios; nunca sobrescreve arquivo existente. O arquivo de exemplo usa marcadores que devem ser substituídos, não senhas default. Não copiar `.env` entre ambientes.

`python scripts/dev.py up` é o caminho somente Docker. Os Dockerfiles instalam pelos lockfiles; imagens base são fixadas por digest. O job `migrate` termina antes de a API subir; web aguarda readiness. Não executar migration automática em cada worker.

Para desenvolver no host: `install`, `db`, `migrate`, depois `api` e `web` em terminais separados. `install` usa lockfiles congelados. O script desconsidera `VIRTUAL_ENV` de outro projeto; a venv fica em `apps/api/.venv`.

```sh
python scripts/dev.py init
python scripts/dev.py install
python scripts/dev.py db
python scripts/dev.py migrate
python scripts/dev.py api
# Em outro terminal na mesma raiz:
python scripts/dev.py web
```

Não execute esse modo simultaneamente aos containers API/web de `up`. Para testes, `check` inicia somente o PostgreSQL efêmero necessário; `e2e` exige a aplicação previamente iniciada e modifica o banco sintético de desenvolvimento. Staging/demo usa outra configuração, certificado, contas, volume e portas: siga [RUN DEMO](../../README.md#run-demo), sem copiar arquivos locais.

## Variáveis

| Nome                                                               | Finalidade                                                        |
| ------------------------------------------------------------------ | ----------------------------------------------------------------- |
| APP_ENV                                                            | development/test/staging/production                               |
| DATABASE_URL                                                       | Conexão runtime `postgresql+psycopg`; sem superuser/DDL           |
| MIGRATION_DATABASE_URL                                             | Conexão privilegiada, usada somente por Alembic                   |
| TEST_DATABASE_URL                                                  | Banco descartável com nome terminando `_test`                     |
| POSTGRES_PASSWORD / APP_DATABASE_PASSWORD / TEST_DATABASE_PASSWORD | Credenciais locais de papéis separados, geradas por `init`        |
| PUBLIC_ORIGIN                                                      | Origem pública; HTTPS obrigatório fora de dev/test                |
| LOG_LEVEL                                                          | DEBUG/INFO/WARNING/ERROR, sem payloads sensíveis                  |
| API_PROXY_TARGET                                                   | Opcional para Vite; no host aponta por padrão para 127.0.0.1:8000 |
| SMTP_HOST / SMTP_PORT / SMTP_SENDER                                | SMTP local; Compose usa Mailpit, sem entrega externa              |
| SMTP_STARTTLS / SMTP_USERNAME / SMTP_PASSWORD                      | Configuração do futuro provedor; segredo nunca versionado         |

O script carrega `.env` sem exibir valores e preserva overrides explícitos do processo. Dentro do Compose, URLs de host são substituídas por URLs da rede privada do container. O banco só é exposto localmente para ferramentas de desenvolvimento.

## Comandos

| Comando                                                            | Efeito                                                                         |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| `python scripts/dev.py init`                                       | Cria configuração local se ausente                                             |
| `python scripts/dev.py install`                                    | uv sync/pnpm install com lockfiles                                             |
| `python scripts/dev.py up`                                         | Constrói e inicia aplicação, PostgreSQL e Mailpit por Docker                   |
| `python scripts/dev.py db`                                         | Inicia PostgreSQL de desenvolvimento e Mailpit                                 |
| `python scripts/dev.py migrate`                                    | Alembic upgrade head no host                                                   |
| `python scripts/dev.py api`                                        | FastAPI com reload, sem access log de URLs arbitrárias                         |
| `python scripts/dev.py web`                                        | Vite com proxy de mesma origem                                                 |
| `python scripts/dev.py lint`                                       | Lint, format, tipos, arquitetura, estado ativo, contratos e build              |
| `python scripts/dev.py test`                                       | PostgreSQL de teste + pytest obrigatório + Vitest                              |
| `python scripts/dev.py benchmark`                                  | Mede leituras/reservas com 100 mil agendamentos em banco efêmero isolado       |
| `python scripts/dev.py check`                                      | Lint e testes completos                                                        |
| `python scripts/dev.py e2e`                                        | Instala Chromium e executa Playwright contra aplicação já iniciada             |
| `python scripts/dev.py bootstrap-admin --email pessoa@example.com` | Emite convite inicial, apenas enquanto não há administrador ativo e verificado |
| `python scripts/dev.py prune-identity`                             | Remove sessões/tokens expirados e contadores antigos; preserva auditoria       |
| `python scripts/dev.py down`                                       | Para containers, preserva volume dev; tmpfs dos testes não persiste            |

Comandos granulares: `uv run --directory apps/api pytest`, `uv run --directory apps/api mypy`, `pnpm test`, `pnpm build`, `pnpm typecheck`, `pnpm contracts:generate`, `pnpm contracts:check`. Para pytest de integração granular configure APP_ENV=test e TEST_DATABASE_URL; sem configuração ele é explicitamente pulado, nunca chamado de aprovado. CI define REQUIRE_INTEGRATION=1, que converte ausência de configuração em falha.

Auditoria de dependências: `pnpm audit --prod --audit-level high`; Python: `uv export --project apps/api --frozen --no-dev --no-emit-project -o <arquivo-temporario>` e `uv run --project apps/api pip-audit -r <arquivo-temporario> --disable-pip --no-deps`. Não representa auditoria completa de segurança ou do histórico.

## Problemas comuns

- Readiness 503: iniciar o PostgreSQL e aplicar a migration com a URL de migrations. Processo vivo não comprova banco/schema prontos. O erro público não mostra detalhes de conexão.
- Porta ocupada: pare apenas o processo desta aplicação; não encerre outros projetos indiscriminadamente. Não execute host e Compose ao mesmo tempo.
- Credencial alterada após volume criado: variáveis POSTGRES_* só inicializam volume novo. Não apagar volume automaticamente; restaurar a configuração original ou executar procedimento explícito de troca de senha.
- Nova migration: revisar DDL, atualizar SCHEMA_REVISION e testar upgrade/política de downgrade em banco efêmero; não usar autogenerate cegamente. Head atual `0007_product_operations`, com recusa de downgrade destrutivo. `up` aplica todas as revisions pendentes, sem apagar o volume.
- Imagem antiga após alteração: `python scripts/dev.py up` reconstrói imagens. O modo Compose não monta todo o código; para hot reload de edição, use o modo host.
- pnpm incorreto no PATH: confirmar `pnpm --version` = 10.34.5 e Node linha 22. Não alterar lockfile com outro gerenciador.
- Outro clone usando as mesmas portas ou volumes: use o override `COMPOSE_PROJECT_NAME` descrito em [isolamento](../release/reproducibility.md#isolamento-e-portas). Nome distinto separa volumes, mas não altera as portas fixas. Preserve o ambiente anterior ao liberá-las.

## Limites

P04 acrescenta [agenda, capacidade e reservas](scheduling.md), com avisos persistentes no SMTP local. P05 entrega [atendimento e gestão](operations.md), com notas privadas, resumos publicados, indicadores e auditoria. Consulte também [identidade](identity.md) e [cadastros](catalogs.md). P07 acrescenta [demo e recuperação isoladas](operations-recovery.md), com seed explícito e restore ensaiado; desenvolvimento não recebe seed comercial automático. Não há deploy externo ou dados legados migrados. Nunca usar `down --volumes` como comando de rotina: apagar dados não é necessário para parar a aplicação.
