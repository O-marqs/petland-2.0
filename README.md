# PetLand 3.0

**O cuidado do pet, bem organizado.** Evolução de um sistema acadêmico Flask para um produto com agenda confiável, autorização por objeto e experiência própria para cliente, funcionário e administrador.

**Estado atual: P01 — Fundação e contratos.** Esta entrega executa a aplicação base, conecta frontend/API/PostgreSQL e demonstra o design system. Cadastro, autenticação, pets, catálogo e reservas ainda **não estão implementados**. Não há demonstração pública ou produção publicada.

## Executar localmente

Requisitos: **Git**, **Docker com Compose v2** e **Python 3.11+** para o comando de desenvolvimento. O caminho somente Docker instala Python 3.13, Node 22 e dependências dentro das imagens.

```sh
git clone --branch petland-3.0 https://github.com/O-marqs/petland-2.0.git
cd petland-2.0
python scripts/dev.py init
python scripts/dev.py up
```

`init` gera credenciais aleatórias em `.env` (ignorado pelo Git), preserva arquivo existente e não imprime senhas. `up` compila as imagens, inicia PostgreSQL, executa a migration como job único e espera API/web saudáveis. Portas publicadas exclusivamente no loopback.

- Aplicação: http://localhost:5173
- Galeria interativa: http://localhost:5173/design-system
- OpenAPI/Swagger local: http://localhost:8000/api/docs
- Processo: http://localhost:8000/api/v1/health/live
- Banco/schema: http://localhost:8000/api/v1/health/ready

Parar preservando o banco: `python scripts/dev.py down`. A configuração Compose desta entrega é de **desenvolvimento**, com Vite, não uma receita de produção.

## Desenvolver e validar

Para rodar ferramentas no host: Python **3.13**, **uv 0.12.18**, Node **22.14+ da linha 22**, **pnpm 10.34.5**. O uv pode instalar Python 3.13 com `uv python install 3.13`; instale pnpm com `npm install --global pnpm@10.34.5`.

```sh
python scripts/dev.py init
python scripts/dev.py install
python scripts/dev.py db
python scripts/dev.py migrate
python scripts/dev.py api
# Em outro terminal:
python scripts/dev.py web
```

Não execute API/web no host simultaneamente com os serviços Compose nas mesmas portas. Para usar o host após `up`, execute `down` e depois `db`.

```sh
python scripts/dev.py check
# Com a aplicação iniciada:
python scripts/dev.py e2e
```

`check` verifica Ruff, formatação, mypy, dependências entre camadas, arquivos/segredos do estado ativo, ESLint, TypeScript, formatação web, contratos gerados, build, testes Python e React. O PostgreSQL de testes é separado, efêmero e usa a porta 55433; nenhum teste de migration usa o banco de desenvolvimento. `e2e` instala Chromium e testa navegação, comunicação real, falha/recuperação, formulário, reflow e acessibilidade automatizada em desktop e celular.

Detalhes, comandos individuais e resolução de problemas: [execução local](docs/runbooks/local.md).

## Organização

```text
apps/api/                 FastAPI, bootstrap, módulos, Alembic e testes
apps/web/                 React, rotas, funcionalidades, layouts e UI
packages/api-contract/    OpenAPI e tipos gerados; cliente tipado
infra/                    Compose local, imagens e configuração PostgreSQL
scripts/                  Comandos multiplataforma e verificações
docs/                     Fontes oficiais, decisões, arquitetura e evidências
.github/workflows/        CI, sem deploy automático
```

O backend é um monólito modular com portas pequenas e composição explícita. O módulo técnico `system` demonstra application → port ← infrastructure e adaptação HTTP. Não criamos entidades de negócio artificiais nem diretórios vazios; os módulos de negócio entram nas respectivas fases. A verificação de arquitetura já cobre imports absolutos e relativos de `domain`, `application`, `infrastructure` e `presentation`.

No frontend, React Router carrega páginas sob demanda; TanStack Query gerencia a consulta real de disponibilidade do ambiente; React Hook Form/Zod validam o exemplo da galeria. O exemplo é local e não simula persistência. Manrope/Inter são hospedadas junto à aplicação. Os contratos têm apenas endpoints que realmente existem.

## Legado e continuidade

O histórico de [PetLand 2.0](https://github.com/O-marqs/petland-2.0) permanece intacto. A tag `legacy/petland-2.0-2024-11-24` aponta para `3cc3f898cde896b80fed587bf8c06f4aa46742f6`. A branch principal e o trabalho local anterior foram preservados; ambientes virtuais, caches e código antigo não integram o aplicativo ativo 3.0. Nenhum banco MySQL foi acessado ou migrado.

- [Índice da documentação e documentos oficiais integrais](docs/README.md)
- [Progresso, aceite e próximo card](docs/implementation/progress.md)
- [Resultados verificáveis e limitações](docs/evidence/P01.md)
- [Decisões aprovadas e pendentes](docs/product/decisions.md)
- [Arquitetura e decisões](docs/architecture/README.md)
- [Orientações para próximas sessões](AGENTS.md)

Próxima fase: **P02**, começando pelo **PL3-04**, após resolver D07 (permissões da equipe). Não há merge ou publicação automática.
