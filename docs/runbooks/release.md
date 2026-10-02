# Release de portfólio e pacote local

Versão ativa **3.0.0**, schema `0007_product_operations`, `main` em `O-marqs/petland`. [Notas](../release/3.0.0.md), [metadata](../release/candidate.json), [registro autorizado](../evidence/Portfolio-closure.md). Release final de portfólio/demo; `production_ready=false`, sem aceite humano/leitor de tela presumido.

## Revisar agora

1. Conferir SHA do PR de release e seus três checks exatos: checks, browser, operations. Legado deve permanecer em `3cc3f898cde896b80fed587bf8c06f4aa46742f6` na branch/tag histórica.
2. Reproduzir o clone padrão pelo README. Usar namespace e configurações próprios; nunca copiar contas, secrets, banco ou certificados do autor.
3. Exercitar tutor, equipe e gestão conforme [aceite manual](manual-acceptance.md). [Case final](../case/index.html) e vídeo têm origem RC `f3d70a2`, sem reclassificar P08 nem alterar evidências passadas.
4. Aceite com leitor de tela permanece pendente; axe, vídeo e CI não o substituem. D10 permanece adiado para ambiente comercial.

## Validar e empacotar localmente

```sh
python scripts/dev.py check
python scripts/check_documentation.py
python scripts/render_architecture.py --check
python -m unittest discover -s scripts -p test_release.py
python scripts/release.py check
# Após commit e árvore limpa:
python scripts/release.py bundle
python scripts/release.py verify --folder CAMINHO_DA_PASTA_EMITIDA
```

Saída em `.local/release/3.0.0/<commit>/`: ZIP do Git, inventário, SHA-256, versão/commit e gates. Repetição verifica o pacote existente, sem sobrescrever. `verify` compara commit no comentário do ZIP/manifesto, duplicatas, caminhos privados, assinaturas de segredo conhecidas, inventário, hashes, mídia e versão; não extrai nem publica. ZIP não inclui histórico Git, secrets, contas, `.env`, bancos, backups, chaves, certificados privados ou caches. Staging/reprodução histórica exigem clone Git. Hashes relativos ao manifesto confiável não são assinatura externa ou auditoria integral de PII.

A publicação é estado externo: metadata imutável usa `stable_release_published=null` e aponta à [GitHub Release v3.0.0](https://github.com/O-marqs/petland/releases/tag/v3.0.0). Somente depois de GitHub retornar `draft=false` e `published_at` real, o recibo **publication.json**, anexado à Release, registra `stable_release_published=true`, commit, tag e URL. Assim main/tag ficam no mesmo SHA sem afirmar publicação antecipadamente. O manifesto do ZIP descreve o instante do empacotamento (`publication=not_performed`); não é o recibo de publicação.

## Promoção autorizada de portfólio

O pedido de fechamento autoriza merge commit do PR #13, preservação do legado, branch temporária de release, PR para main com CI verde, rename, clean clone independente, tag anotada exatamente no main validado, GitHub Release e fechamento de drafts obsoletos. Remover branches apenas após conferir tip, zero commits exclusivos e reachability por main/tag. Nunca force push ou mover tags. Registro final e recibo são anexados à GitHub Release; não há atualização circular de SHA no próprio commit.

Para assistir com legendas:

```sh
python scripts/portfolio_preview.py
```

Abrir http://127.0.0.1:8780/. Servir somente a pasta pública no loopback; ranges permitem seek. Vídeo sem áudio, com WebVTT/transcrição e fontes locais. Não servir a raiz, que contém arquivos privados ignorados.

## Capturador histórico P08: uso isolado

Para o material final, use o [roteiro e capturador atual](../case/presentation-script.md#regravar-sem-mudar-o-produto), com namespace/portas próprios, origem `f3d70a2` e mídia em `docs/case/media/final`. O [case final](../case/README.md) é a primeira demonstração; [P08](../case/historical-p08.html) permanece histórico. Checks atuais validam ambos os players e os hashes finais, sem invalidar verificação de bundles históricos que não continham mídia final.

O procedimento abaixo mantém a preparação/proveniência P08. Não substitui as capturas atuais nem autoriza sobrescrever mídia histórica. Uma gravação nova deve ter manifesto separado e referência explícita ao commit executado.

Pré-condição: ferramentas host/Chromium e staging P07 operacionais. Anotar o banco ativo em `.local/staging/active-db.txt`, criar **reset novo** e preservar a origem. O capturador exige banco `petland_reset_<id>_demo` correspondente ao manifesto P07 e recusa uma gravação já iniciada nesse banco. Exportar somente manifesto/identificação/imagens, sem credenciais:

```sh
python scripts/dev.py reset-demo --confirm NOME_EXATO_DO_BANCO_ORIGINAL
uv run --project apps/api --frozen python -c "import sys,json; from pathlib import Path; sys.path.insert(0,'scripts'); import operations as o; e=o.engine_for(); p=Path('.local/p08'); p.mkdir(parents=True,exist_ok=True); (p/'fixture.json').write_text(json.dumps({'database':o.active_database(),'manifest':o.manifest(e),'images':o.image_evidence()})); e.dispose()"
python scripts/dev.py smoke-demo
```

O smoke valida TLS rigoroso antes do Chromium isolado. Depois:

```sh
node apps/web/scripts/capture-portfolio.mjs
python scripts/dev.py activate-demo --target NOME_EXATO_DO_BANCO_ORIGINAL
```

Preparação/gravação usam API/UI existentes: serviço de cinco minutos, passo de um minuto, dia sintético integral, reserva atual e alvo futuro de impacto. Não usar esse capturador contra produção/desenvolvimento ou com dados reais. Usa relógio real e falha ao atravessar meia-noite. Saída privada em `.local/p08/capture`; revisar vídeo/capturas, publicar apenas os dados fictícios selecionados em `docs/case/media` e retornar ao banco anterior com `activate-demo`. Opcional remux WebM com codec copy preserva frames/velocidade, sem cortes; registrar no manifesto de captura.

Antes histórico: `python scripts/legacy_preview.py`; servir exclusivamente `.local/p08/legacy` no loopback e capturar 1280×900. Duas substituições de opções/data, links/forms inativos, scripts/fontes externas removidos e aviso explícito. Copiar `provenance.json` junto às capturas. Nunca executar/importar `app.py`, conectar MySQL ou alterar o checkout antigo.

## Produção comercial permanece adiada

Ambiente público, SMTP externo, backup off-host/custódia, SLO, RPO/RTO produtivos e HA não estão implementados. A release 3.0.0 não aprova esses gates. Definição de provedor/orçamento/domínio e novo ensaio fora do host dependem de D10; leitor de tela depende de execução humana. Licença geral ausente, sem adoção automática.

Falha antes de merge/tag: corrigir e repetir checks afetados; não promover uma CI vermelha. Após troca de banco, preservar origem/escritas novas e seguir P07. Rollback de imagem exige compatibilidade com schema; downgrade destrutivo ou retorno a backup ignorando operações novas não são recuperação.
