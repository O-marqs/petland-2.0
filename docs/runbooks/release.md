# Revisão e pacote local da candidata

Responsável: Lucas. Artefato **3.0.0-rc.1**, schema atual `0007_product_operations`. [Versão/checkout e reprodução](../release/reproducibility.md) são a referência de execução; [candidate.json](../release/candidate.json) registra gates. A versão RC permanece durante incrementos de revisão; identifique o commit, não apenas o número. Não fazer merge/tag/promoção automática. Aceite de produto/leitor de tela e D10 permanecem pendentes.

## Revisar agora

1. Conferir branch/PR atual da [auditoria de reprodução](../evidence/Reproducibility-review.md), CI do commit exato, [produto atual](../product/product-overview.md) e [relatório](../release/quality-report.md). As [notas P08](../release/3.0.0-rc.1.md) conservam seu schema e resultados históricos.
2. Reproduzir setup pelo README. Em demo local, consultar apenas localmente `.local/staging/accounts.json`; não publicar seu conteúdo. Certificado é local de teste.
3. Cliente: cadastrar/editar pet, escolher oferta, conferir resumo, confirmar e acompanhar. Equipe: painel/agenda, chegar/iniciar/concluir, transferir, conferir cuidados e comunicação. Gestão: equipe por data, capacidade física, indicadores e acessos. Siga [aceite manual](manual-acceptance.md) e [operação atual](operational-evolution.md). Compare com [capturas atuais](../ux/PetLand_3.0_UX_Final.md); o [vídeo](../case/index.html) é histórico P08.
4. Realizar aceite com leitor de tela segundo P06. Registrar sistema/leitor/versão, resultado por jornada e achados. Axe/árvore acessível/teclado/vídeo não substituem essa execução.
5. Registrar decisão final de produto e limitações aceitas. Um merge de código não concede automaticamente aprovação de publicação ou SLA.

## Validar e empacotar localmente

```sh
python scripts/release.py check
# Depois de commit e árvore limpa:
python scripts/release.py bundle
python scripts/release.py verify --folder CAMINHO_DA_PASTA_EMITIDA
```

Saída em `.local/release/3.0.0-rc.1/<commit>/`: ZIP, inventário e SHA-256, versão/commit e gates explícitos. Diretório/arquivo existente não é sobrescrito; repetição verifica o pacote. ZIP contém somente arquivos da árvore ativa do commit; não embute histórico legado, credenciais, contas de demo, CA/chaves, archive de banco, venv/node_modules ou `.local`. O pacote não é publicado nem muda refs Git. `verify` lê sem extrair, compara o commit no comentário Git do ZIP e no manifesto, recusa entradas duplicadas/caminhos privados/assinaturas de segredo conhecidas e confere inventário, hashes, mídia e versão. Hashes dependem de manifesto confiável; não são assinatura externa nem auditoria completa de PII/histórico. Para staging/proveniência histórica, use o clone Git do README: ZIP não contém os metadados/histórico exigidos por essas rotinas.

Para assistir o case com legendas, servir **somente a pasta pública do case**:

```sh
python scripts/portfolio_preview.py
```

Abrir http://127.0.0.1:8780/. O servidor fixa loopback/pasta pública, não permite listar/expor arquivos privados e suporta ranges HTTP para saltar capítulos do vídeo. Não servir a raiz do repositório, que contém arquivos privados ignorados. Vídeo sem áudio, com WebVTT e transcrição. Fontes do case não exigem rede externa.

## Capturador histórico P08: uso isolado

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

## Promoção futura, após aceite

Definir D10: ambiente/provedor/orçamento, domínio, e-mail, custódia, backup externo e RPO/RTO. Preparar revisão das mudanças de ambiente, novo restore fora do host e smoke. Só então propor versão estável 3.0.0, tag no commit aprovado, imagens por digest e release com notas/artefatos revisados. Nenhum segredo por variável de build ou PR não confiável; migration em job único antes do smoke.

Falha antes da promoção: candidata permanece local; corrigir e repetir os checks afetados. Falha após troca de banco: preservar origem e escritas novas; usar o runbook P07. Rollback de imagem exige compatibilidade com schema; downgrade destrutivo não é mecanismo de recuperação. Nunca voltar a um backup ignorando operações novas.
