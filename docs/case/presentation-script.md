# PetLand 3.0 — roteiro final de apresentação

**Objetivo:** mostrar como uma reserva conecta tutor, equipe e gestão. Aproximadamente quatro minutos, sem áudio, com legendas descritivas e capítulos. O tempo exato de cada cena vem de [chapters.json](media/final/chapters.json) e da [transcrição final](final-transcript.md), não de tempos estimados usados como evidência.

## A narrativa

O 2.0 revelou uma intenção de autoatendimento, mas não comprovava contratação segura sob concorrência. A modernização trata disponibilidade como capacidade e liga a reserva ao cuidado e à gestão. O case apresenta problema/diagnóstico antes da demonstração e engenharia/resultados/limites depois. O vídeo acompanha a experiência; não vira aula de arquitetura ou catálogo de endpoints.

| Momento aproximado | Cena                                                               | Mensagem                                                                                                        |
| ------------------ | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| 0:00–0:22          | Home e início contextualizado do tutor                             | O cuidado começa com próximo passo claro. Conta fictícia já verificada e contato pronto.                        |
| 0:22–1:10          | Pet, catálogo, disponibilidade, resumo e confirmação               | Nala tem contexto; preço e duração são conhecidos. Escolher horário ainda não confirma.                         |
| 1:10–2:57          | Painel, agenda, alerta, chegada, transferência, início e conclusão | A mesma reserva entra na operação. Alergia é reconhecida; responsável muda com motivo; cuidado mantém história. |
| 2:57–3:08          | Tutor consulta o concluído                                         | Resumo publicado é visível; nota interna é privada. Aviso de pronto conferido no Mailpit local.                 |
| 3:08–3:40          | Indicadores, escala de uma data e capacidade                       | Gestão entende a operação e controla quem trabalha e quais recursos estão disponíveis.                          |
| 3:40–4:00          | Prévia bloqueada e auditoria                                       | Mudança incompatível não apaga a reserva. Histórico, autoria e limites encerram a jornada.                      |

Os intervalos acima correspondem à gravação final. Entre transferência e início há espera literal pelo horário permitido (aproximadamente 1:45–2:38); o capturador atualiza o atendimento, sem adiantar o relógio. O ritmo muda conforme carregamentos e espera real. Não encurtar a gravação para esconder espera, recortar falhas como sucesso ou substituir ações por mocks. Capturas nomeadas `final-*` correspondem às telas vistas. Fotos de marca geradas pertencem à identidade implementada; não são clientes reais.

## Preparações declaradas

Aplicação `f3d70a2cce07d587351eadaa66864b7c1ae4444a`, schema 0007 e imagem OCI correspondente. Namespace `petlandfinalcase`, portas 8445/55436/8028 e CA/contas/volume próprios. Fixture e reset usam ferramentas existentes, sem copiar staging pessoal. Perfis autenticam por API normal antes de suas cenas; senhas não são filmadas.

Serviço fictício de cinco minutos/R$ 40, duas pessoas aptas, pool físico inicialmente com duas unidades, slots de um minuto, antecedência zero/lembrete de um minuto e expediente excepcional na data. Não são configurações comerciais recomendadas. Reserva futura via API comum do tutor prepara a prévia. Cadastro/reserva principal/chegada/transferência/nota/início/conclusão/escala/capacidade são ações reais da interface. Fonte funcional não é alterada; relógio real.

## Regravar sem mudar o produto

Além dos [requisitos de desenvolvimento](../release/reproducibility.md#cinco-caminhos-requisitos-distintos), use Chromium do Playwright, Pillow para conversão lossless e FFmpeg local para ler a duração do container. Não fazem parte das dependências de execução do produto. Ferramentas de captura estão fixadas no snapshot funcional declarado: recusam diferença em src/migrations/contrato/infra. Nova versão funcional exige nova revisão de origem, não atribuição falsa ao SHA anterior.

Na raiz, com Docker ativo e portas da demo livres:

```sh
python scripts/dev.py install
pnpm --filter @petland/web exec playwright install chromium
uv run --project apps/api --frozen python scripts/final_case_demo.py up
uv run --project apps/api --frozen python scripts/final_case_demo.py fresh
pnpm --filter @petland/web exec node scripts/capture-final-portfolio.mjs
# Python com Pillow disponível; informe o caminho local real de FFmpeg:
python scripts/encode_final_case.py --ffmpeg CAMINHO_PARA_FFMPEG
python scripts/check_documentation.py
pnpm --filter @petland/web exec node scripts/verify-portfolio.mjs
pnpm --filter @petland/web exec node scripts/verify-final-roster.mjs
uv run --project apps/api --frozen python scripts/final_case_demo.py down
```

Em Linux, Chromium pode exigir `playwright install --with-deps chromium`. `fresh` cria outro banco sintético e preserva o anterior. `down` para somente o namespace da apresentação, preservando volume/configuração. Preparações e resultados brutos ficam privados em `.local/final-case`; somente mídia conferida/proveniência permitida chegam ao case.

Primeira tentativa encontrou transbordamento de um nome fictício longo no detalhe do tutor a 320 px (334 px). A segunda usa “Nala”. Essa limitação do produto continua registrada; não houve ajuste da aplicação para a gravação.

## Compartilhar

[Abrir o player local](index.html) com `python scripts/portfolio_preview.py --port 8780`. A pasta pública portátil é `docs/case`: manter HTML/CSS, fontes/licença, imagens, WebM, VTT, JSON e transcrições juntos. Links aprofundados apontam ao GitHub; para ler offline toda a documentação, use o clone/bundle do projeto. [Player P08 histórico](historical-p08.html) preserva a demonstração anterior. Sem publicação, merge ou release automático.
