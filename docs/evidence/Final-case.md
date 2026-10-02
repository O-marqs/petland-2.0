# Apresentação final — evidência e limites

Pedido humano integral em [Final-case-request](../implementation/Final-case-request.txt). Revisão de apresentação após merges humanos dos PRs 11/12. Branch `petland-3.0-final-case` sobre `f3d70a2cce07d587351eadaa66864b7c1ae4444a`, base de PR onboarding. Sem regra de negócio, funcionalidade, dependência, schema, contrato ou infra alterados.

## Origem e ambiente

Aplicação conferida por `git diff f3d70a2 -- apps/api/src apps/api/migrations apps/web/src packages/api-contract infra`: vazio. Imagens com revisão OCI `f3d70a2cce07`, tags próprias e IDs no [manifesto final](../case/media/final/capture.json). Isso identifica o código funcional; não afirma que as ferramentas novas pertenciam ao commit original ou que o checkout de apresentação estava limpo durante a captura.

Windows/PowerShell, Docker Linux/WSL, PostgreSQL 17, Nginx/HTTPS, API FastAPI/SQLAlchemy e build React. Namespace `petlandfinalcase`, portas 8445/55436/8028, volume/CA/chaves/contas novos. TLS rigoroso validado antes do Chromium que ignora a CA local de teste. O staging pessoal não foi pausado ou usado para capturas. Fixture P07 fictício e banco novo; nenhuma credencial/configuração/backup pessoal copiado ou publicado.

Captura final encerrada em **02/10/2026, 20:18:38 UTC**, viewport 1280×900; três capturas móveis a 320×900 após a gravação. Schema 0007, mesma candidata RC. Preparações completas, ações persistidas, rotas, hashes, dimensões e versões de imagem no manifesto. Serviço de cinco minutos/R$ 40, dois recursos aptos, slots de um minuto/antecedência zero/lembrete de um minuto, expediente excepcional e alvo futuro de impacto via API comum: todos sintéticos e declarados. Relógio real, sem endpoints de teste/mocks.

## Jornadas executadas

Tutor com conta demo verificada/contato pronto: início → Nala com alergia/preferência → catálogo → vaga → resumo → confirmação. Pet e reserva criados pela interface e conferidos pela API.

Equipe: painel/agenda → mesma reserva → contexto crítico → chegada → transferência com motivo e horário preservado → nota interna → início no horário permitido/reconhecimento da restrição atual → conclusão/resumo público. Tutor consulta conclusão e não recebe nota interna nem na UI nem no payload. Aviso de pronto encontrado realmente no **Mailpit local**, identificado pela reserva; **sem entrega externa**.

Administração: indicadores reais da demo → escala coletiva salva para uma única data → pool físico alterado de duas para uma unidade → prévia de mudança incompatível com reserva futura. A prévia identifica o conflito, impede salvar e conserva versão e reserva BOOKED. Auditoria encerra o vídeo.

## Arquivos e qualidade

[Player final](../case/index.html) e [case escrito](../case/README.md): problema/diagnóstico → decisões → modernização/arquitetura → experiência → engenharia/resultados/limites. Bloco visual React/FastAPI/PostgreSQL e garantias; detalhes técnicos vinculados aos documentos. [Roteiro](../case/presentation-script.md), [transcrição UTF-8](../case/final-transcript.md), [WebVTT](../case/media/final/petland-final-demo.vtt), [capítulos](../case/media/final/chapters.json).

Vídeo **240,16 segundos**, WebM/VP8 1280×900, 25 fps, sem áudio/cortes/aceleração. Duração de container lida por FFmpeg e confirmada pelo navegador; diferença de 0,15 s para relógio de captura (240,01 s). Arquivo copiado byte a byte, sem remux. **19 capítulos e 22 screenshots**, estes codificados WebP lossless e comparados por pixels RGBA com PNGs originais privados. Hashes públicos não fingem assinatura externa.

Todos os 22 checkpoints de captura final passaram axe/reflow/ausência de erro JS. [Player verificado](Final-case-player.json) em **1280/320 px**, final e histórico: links locais e âncoras, HTTP 206/ranges, duração, legendas em exibição, todos os **19/14 capítulos** com seek real, transcrição alternativa, reflow, zero violações axe/erros JS. Não é aceite humano com leitor de tela.

As contagens Python/React/E2E e p95 mostrados no case são identificados como auditoria/CI anterior `31920b4`, tentativa 2. Primeira falha de desempenho mantida; não são novos benchmarks desta apresentação. CI desta branch e pacote do commit exato ficam registrados no PR/manifesto local, sem aprovação antecipada.

## Falha preservada e limitação do produto

Verificações adicionais desta revisão: `python scripts/dev.py check` aprovado com **128 Python e 20 React**, Ruff/format/mypy/fronteiras/scan/contratos/build. Um aviso de depreciação de TestClient/httpx já existente, sem atualização das dependências. Oito testes dos guards de pacote aprovados; documentação/âncoras/hashes/diagramas/candidata e ESLint dos capturadores/player aprovados. Bytes staged do Git também passaram pelo validador de mídia, para conferir hashes após normalização LF.

Consulta real somente de leitura após a gravação confirma **2 → 1 → 2 pessoas** em 06/07/08 de outubro: a escala alterada vale só no dia 07. [Registro de dias adjacentes](Final-case-adjacent-days.json), reproduzido por `apps/web/scripts/verify-final-roster.mjs` no mesmo banco sintético. Containers da apresentação encerrados com volume/configuração preservados; readiness do staging pessoal novamente HTTP 200.

A tentativa 1 concluiu o fluxo desktop, mas falhou em reflow do detalhe do tutor a 320 px: o nome fictício “Nala · demonstração final” expandiu a largura para aproximadamente 334 px. Log, vídeo e imagem diagnóstica preservados em `.local/clean-review/final-case-attempt-1.log` e `.local/final-case`. Não foram exportados como demonstração aprovada.

Tentativa 2 usa “Nala”, em banco sintético novo; gravação/capturas/checks completos aprovados. **O problema com nomes longos permanece conhecido**, sem alteração da aplicação para melhorar a gravação. A apresentação final não equivale a aprovação de todos os textos/dados possíveis em mobile.

Mídia/manifesta P03–P08 não sobrescritos. [Player histórico P08](../case/historical-p08.html) claramente separado; vídeo anterior conserva 185,12 s e seu SHA. As capturas documentais de `2549523` e snapshots intermediários também permanecem intactos.

## Gates humanos

Revisar material e produto com os três perfis; leitor de tela; decidir licença. D10 continua adiando produção, provedor/domínio/SMTP externo, custódia/backup fora do host e SLO/RPO/RTO. Não houve merge, tag, publicação ou release estável. Encerrar somente os containers da demo de apresentação, preservando seu volume/configuração e o staging pessoal.
