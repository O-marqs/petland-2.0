# P06 — Reproduzir qualidade e medições

## Verificações funcionais

Da raiz, com dependências instaladas: `python scripts/dev.py check`. Com a aplicação iniciada por `python scripts/dev.py up`: `python scripts/dev.py e2e`. Integração exige PostgreSQL efêmero; não há substituição por SQLite. CI repete o setup em checkout limpo, com banco novo e lockfiles congelados.

E2E cobre os três perfis, teclado, nomes acessíveis, foco, filtros, estados de erro, dados privados e reflow de 320 px. Capturas ficam em `apps/web/test-results/p06-*-320.png`. A varredura axe é complementar e não certifica WCAG 2.2 AA.

## API: RNF02

Execute `python scripts/dev.py benchmark`. O serviço de qualidade cria 100 mil agendamentos, 100 mil eventos de auditoria, 2 mil clientes/pets e cinco pessoas com capacidade, exclusivamente no PostgreSQL de teste. Cada cenário usa 20 sessões distintas, três leituras de aquecimento e 200 requisições medidas. Reservas são distribuídas em horários válidos, com 20 requisições concorrentes; toda resposta precisa ser 201.

O job `checks` também executa esse ensaio em Linux limpo com PostgreSQL efêmero, após concluir as outras verificações. O relatório é impresso no log do job; a mesma meta e ausência de erros são obrigatórias. Registrar os resultados desse ambiente separadamente dos números do computador local.

Resultado em `.local/benchmarks/api-benchmark.json`: p50/p95/máximo, códigos HTTP, erros de aquecimento, método e ambiente. Percentil usa nearest-rank. Meta p95: leituras ≤400 ms; reserva ≤800 ms. Qualquer erro ou meta não atendida resulta em saída diferente de zero. Não executar builds, testes ou outras cargas pesadas enquanto estiver medindo. A rodada é um teste de carga fechado, não mede capacidade máxima nem representa tráfego de produção.

Para comparar desenvolvimento nativo, execute `scripts/benchmark_api.py` com o Python do projeto, `APP_ENV=test` e `TEST_DATABASE_URL` local terminado em `_test`. O resultado padrão é `.local-p06-api-benchmark.json`. Credenciais ficam no ambiente; não as cole no terminal/documentação. O script recusa banco não identificado como teste e só remove o banco aleatório criado pela própria execução. Interrupção forçada do processo pode deixar esse banco no serviço efêmero; não apague volumes de desenvolvimento.

## Web: RNF03

Com API local saudável:

1. `pnpm build`.
2. Em outro terminal: `pnpm --filter @petland/web preview --port 4173`.
3. `node apps/web/scripts/benchmark-web.mjs`.

São três execuções para início, entrada e catálogo, em Chromium/Pixel 7, cache frio, CPU 4× mais lenta, latência 150 ms, download 1,6 Mbps e upload 750 kbps. Entrada valida o formulário vazio; catálogo muda filtros pelo teclado. Nenhum login é submetido. `web-vitals` é dependência exclusiva de desenvolvimento e não integra o bundle do produto. Resultado em `.local-p06-web-benchmark.json`; metas LCP ≤2500 ms, INP ≤200 ms e CLS ≤0,1 em cada amostra, sem erro de JavaScript ou violação da política de conteúdo.

O INP se limita às interações exercitadas; não se usa TBT como substituto. [Método do web-vitals](https://github.com/GoogleChrome/web-vitals) e [diferença entre INP de laboratório e campo](https://web.dev/articles/inp). O serviço preview aplica a política restrita; o servidor de desenvolvimento abre somente o necessário ao Vite. A futura hospedagem deverá aplicar os mesmos headers, HTTPS e política de proxy conforme o ambiente.

## Aceite com leitor de tela

Responsável: revisão humana de aceite. Usar NVDA com Chrome/Firefox ou VoiceOver com Safari, registrando versões, data e resultado. Ainda não declarar este item aprovado só porque axe/teclado passaram.

- Cliente: entrar, navegar para pets e agendamento, ouvir títulos/rótulos/erros, conferir resumo e dupla confirmação, abrir histórico sem informações internas.
- Funcionário: abrir agenda, mudar filtros, entrar no atendimento e navegar pelas ações/notas; confirmar distinção de nota interna e resumo público.
- Administrador: abrir indicadores/auditoria/acessos, percorrer filtros/listas, verificar mensagens e retorno do foco.
- Nos três: link de pular conteúdo alcançável, navegação e leitura em ordem, carregamento/erro anunciado sem repetição excessiva, nenhum bloqueio de teclado. Registrar qualquer barreira com rota e sequência.

O usuário autorizou posteriormente a recuperação local de Docker/WSL e o reinício do computador para continuar P06. Essa autorização prevalece sobre a orientação inicial de parar. Preservar volumes, imagens e dados; não fazer reset de fábrica ou apagar dados. Registrar a causa observada e a recuperação nas evidências.

## Relógio WSL nesta máquina

Em 01/10/2026, o daemon voltou após reinício do Windows, mas a medição revelou `QueryCanceled` no lock. `dmesg` mostrou `Time jumped backwards`; uma sonda de 45 segundos detectou saltos de aproximadamente −5,4/+5,3 segundos. Ubuntu estava executando `systemd-timesyncd` e o WSL também recebia sincronização Hyper-V. Windows estava aproximadamente 5,4 segundos à frente de NTP; sincronização do Windows foi recusada por falta de privilégio administrativo.

Sob autorização de recuperação, `systemd-timesyncd` foi parado/desabilitado somente no Ubuntu e o horário compartilhado do WSL alinhado ao Windows. A fonte de relógio e `hv_utils.timesync_implicit` foram devolvidos aos valores originais (`tsc` e `Y`); não houve alteração em `.wslconfig`. A sonda seguinte ainda observou correções menores de −0,7/−1,1 segundo. Não confundir eliminação do conflito maior com prova de estabilidade absoluta do relógio.

Esse é um ajuste específico do host, sem alterar timeouts do produto. Quando o Windows tiver sincronização correta e o problema de WSL estiver resolvido, a sincronização do Ubuntu pode ser restaurada com `wsl -d Ubuntu -u root -- systemctl enable --now systemd-timesyncd`, seguida de nova verificação. Há [relato equivalente no WSL](https://github.com/microsoft/WSL/issues/11790); a configuração geral está na [documentação Microsoft](https://learn.microsoft.com/en-us/windows/wsl/wsl-config). Não aplicar essa mudança a outras máquinas sem diagnosticar suas fontes de tempo.
