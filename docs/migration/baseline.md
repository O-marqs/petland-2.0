# Baseline do PetLand 2.0

Inspeção: 23/09/2026. Repositório: https://github.com/O-marqs/petland-2.0.

- HEAD local e `main` remoto: `3cc3f898cde896b80fed587bf8c06f4aa46742f6` (`Final2`, 24/11/2024). Nenhum commit posterior no remoto durante a inspeção.
- Referência estável criada: tag anotada `legacy/petland-2.0-2024-11-24`, no mesmo commit.
- A cópia local anterior, `Documents/GitHub/petland 2.0`, permanece na main com trabalho não commitado intacto: alteração de host/porta em `app.py`, retirada de validação de CEP no cadastro, troca de imagem no login e imagem `static/images/dogandcat.jpg` não rastreada.
- Impacto: alterações locais de execução e interface do legado, sem mudança da arquitetura planejada. Não foram incorporadas nem descartadas.
- Evolução em worktree separado `Documents/GitHub/petland-3.0`, branch `petland-3.0`, compartilhando o repositório e todo o histórico. Não mover ou remover a pasta original: ela contém o Git comum ao worktree.

O estado ativo 3.0 retira o aplicativo 2.0, ambiente virtual e caches após criar a tag. Para consultar sem tocar no trabalho local: `git show legacy/petland-2.0-2024-11-24:app.py`. Para recuperar uma cópia isolada, usar `git worktree add --detach <pasta-nova> legacy/petland-2.0-2024-11-24`.

Nenhum MySQL foi acessado. Nenhuma migração histórica, teste dinâmico do legado, rotação de credencial histórica ou deploy foi executado. A tag registra proveniência, não certifica segurança do legado.

## Integridade dos documentos recebidos (SHA-256)

| Arquivo | Hash |
|---|---|
| Plano consolidado | `53B8496A4B1AA50EF2A6A26B86975C03C31729120B0521210148B44F0028F2C0` |
| Caderno UX | `7B9A78562B8D23E20C5979655E2A947A88700A151348FCE418E89FFF93D0F3B8` |

Ambos foram copiados byte a byte, sem alterar os originais. O plano foi lido integralmente; as 12 páginas do PDF foram extraídas e renderizadas para inspeção visual.
