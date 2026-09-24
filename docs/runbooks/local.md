# Execução local e qualidade

Leia o README para o caminho de entrada. Os comandos abaixo partem da raiz. Windows/PowerShell e Linux são suportados pelo mesmo `scripts/dev.py`, sem dependência de Make/bash para desenvolvimento no host.

## Pré-requisitos

- Git; Docker Engine/Desktop em execução com Compose v2.
- Python 3.11+ para `scripts/dev.py`; aplicação Python 3.13 instalada pelo uv ou dentro da imagem.
- Para ferramentas no host: uv 0.12.18, Node 22.14+ (linha 22), pnpm 10.34.5.
- Portas disponíveis: 5173 (web), 8000 (API), 55432 (PostgreSQL dev), 55433 (PostgreSQL efêmero dos testes). Todas as portas Compose usam 127.0.0.1.

## Instalação

`python scripts/dev.py init` gera `.env` com segredos locais aleatórios; nunca sobrescreve arquivo existente. O arquivo de exemplo usa marcadores que devem ser substituídos, não senhas default. Não copiar `.env` entre ambientes.

`python scripts/dev.py up` é o caminho somente Docker. Os Dockerfiles instalam pelos lockfiles; imagens base são fixadas por digest. O job `migrate` termina antes de a API subir; web aguarda readiness. Não executar migration automática em cada worker.

Para desenvolver no host: `install`, `db`, `migrate`, depois `api` e `web` em terminais separados. `install` usa lockfiles congelados. O script desconsidera `VIRTUAL_ENV` de outro projeto; a venv fica em `apps/api/.venv`.

## Variáveis

| Nome | Finalidade |
|---|---|
| APP_ENV | development/test/staging/production |
| DATABASE_URL | Conexão runtime `postgresql+psycopg`; sem superuser/DDL |
| MIGRATION_DATABASE_URL | Conexão privilegiada, usada somente por Alembic |
| TEST_DATABASE_URL | Banco descartável com nome terminando `_test` |
| POSTGRES_PASSWORD / APP_DATABASE_PASSWORD / TEST_DATABASE_PASSWORD | Credenciais locais de papéis separados, geradas por `init` |
| PUBLIC_ORIGIN | Origem pública; HTTPS obrigatório fora de dev/test |
| LOG_LEVEL | DEBUG/INFO/WARNING/ERROR, sem payloads sensíveis |
| API_PROXY_TARGET | Opcional para Vite; no host aponta por padrão para 127.0.0.1:8000 |

O script carrega `.env` sem exibir valores e preserva overrides explícitos do processo. Dentro do Compose, URLs de host são substituídas por URLs da rede privada do container. O banco só é exposto localmente para ferramentas de desenvolvimento.

## Comandos

| Comando | Efeito |
|---|---|
| `python scripts/dev.py init` | Cria configuração local se ausente |
| `python scripts/dev.py install` | uv sync/pnpm install com lockfiles |
| `python scripts/dev.py up` | Constrói e inicia toda a fundação por Docker |
| `python scripts/dev.py db` | Inicia só PostgreSQL de desenvolvimento |
| `python scripts/dev.py migrate` | Alembic upgrade head no host |
| `python scripts/dev.py api` | FastAPI com reload, sem access log de URLs arbitrárias |
| `python scripts/dev.py web` | Vite com proxy de mesma origem |
| `python scripts/dev.py lint` | Lint, format, tipos, arquitetura, estado ativo, contratos e build |
| `python scripts/dev.py test` | PostgreSQL de teste + pytest obrigatório + Vitest |
| `python scripts/dev.py check` | Lint e testes completos |
| `python scripts/dev.py e2e` | Instala Chromium e executa Playwright contra aplicação já iniciada |
| `python scripts/dev.py down` | Para containers, preserva volume dev; tmpfs dos testes não persiste |

Comandos granulares: `uv run --directory apps/api pytest`, `uv run --directory apps/api mypy`, `pnpm test`, `pnpm build`, `pnpm typecheck`, `pnpm contracts:generate`, `pnpm contracts:check`. Para pytest de integração granular configure APP_ENV=test e TEST_DATABASE_URL; sem configuração ele é explicitamente pulado, nunca chamado de aprovado. CI define REQUIRE_INTEGRATION=1, que converte ausência de configuração em falha.

Auditoria de dependências: `pnpm audit --prod --audit-level high`; Python: `uv export --project apps/api --frozen --no-dev --no-emit-project -o <arquivo-temporario>` e `uv run --project apps/api pip-audit -r <arquivo-temporario> --disable-pip --no-deps`. Não representa auditoria completa de segurança ou do histórico.

## Problemas comuns

- Readiness 503: iniciar o PostgreSQL e aplicar a migration com a URL de migrations. Processo vivo não comprova banco/schema prontos. O erro público não mostra detalhes de conexão.
- Porta ocupada: pare apenas o processo desta aplicação; não encerre outros projetos indiscriminadamente. Não execute host e Compose ao mesmo tempo.
- Credencial alterada após volume criado: variáveis POSTGRES_* só inicializam volume novo. Não apagar volume automaticamente; restaurar a configuração original ou executar procedimento explícito de troca de senha.
- Nova migration: revisar DDL, atualizar SCHEMA_REVISION e testar upgrade/downgrade em banco efêmero; não usar autogenerate cegamente. P01 só contém marcador técnico.
- Imagem antiga após alteração: `python scripts/dev.py up` reconstrói imagens. O modo Compose não monta todo o código; para hot reload de edição, use o modo host.
- pnpm incorreto no PATH: confirmar `pnpm --version` = 10.34.5 e Node linha 22. Não alterar lockfile com outro gerenciador.

## Limites

Não existe seed comercial em P01: nenhuma tabela de negócio foi antecipada. Também não há SMTP, autenticação, backup/restore operacional, deploy ou dados legados migrados. Essas entregas seguem seus gates. Nunca usar `down --volumes` como comando de rotina: apagar dados não é necessário para parar a aplicação.
