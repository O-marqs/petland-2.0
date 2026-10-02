# Qualidade e rastreabilidade — candidata 3.0.0-rc.1

O relatório consolida provas existentes e a demonstração P08. Cada medição identifica sua fase; números de P06/P07 não são apresentados como nova medição P08 nem como tráfego de produção. CI do commit da candidata será registrada nos checks/descrição de seu PR.

## Funcionalidades

| Requisito | Implementação e prova |
|---|---|
| RF01 Conta e autenticação | P02: SMTP real, token único/concorrente, sessão, CSRF, último admin e revogação; [P02](../evidence/P02.md) |
| RF02 Tutor | P03: perfil mínimo, cadastro assistido e associação verificada; [P03](../evidence/P03.md) |
| RF03 Pets | P03: owner A/B, referências, edição/arquivo; cadastro UI e leitura persistida filmados P08 |
| RF04 Serviços | P03: preço/duração por porte, compatibilidade e versão; ofertas reais na revisão P08 |
| RF05 Capacidade | P04: expediente, pausa/exceção, funcionários aptos e atribuição automática; [P04](../evidence/P04.md) |
| RF06 Disponibilidade/reserva | P04: lock, exclusões, concorrência, idempotência e confirmação; mesma reserva filmada ponta a ponta P08 |
| RF07 Cancelar/reagendar | P04/P05: versão, prazo, rollback e outbox/SMTP; testes anteriores mantidos, sem taxas |
| RF08 Execução | P05: chegar/iniciar/concluir/falta/extensão; três transições válidas com relógio real filmadas P08 |
| RF09 Histórico/notas | P05: INTERNAL/PUBLIC e autoria; P08 verifica ausência da nota privada no payload cliente |
| RF10 Gestão/configuração | P05: impacto e proteções; P08 mostra fechamento bloqueado e configuração/reserva inalteradas |
| RF11 Indicadores/auditoria | P05: fórmulas/períodos/autorização; consultas reais filmadas, sem números comerciais inventados |
| RF12 Catálogo | P03: landing e filtros; serviço inativo oculto, reflow/erros E2E |
| RF13 Engenharia/documentação | P01–P08: contratos, migrations, fronteiras, CI, runbooks, imagens/digests, restore e candidato empacotável |

## Provas automatizadas e operacionais

Referência integrada P07: [CI do PR](https://github.com/O-marqs/petland-2.0/actions/runs/36905134678), head `2154801`, merge temporário `ee7216409df6`. **114 Python + 15 React + 15 E2E**, 1 skip mobile previsto do bootstrap singleton; checks/browser/operations verdes. [Push direto](https://github.com/O-marqs/petland-2.0/actions/runs/36905114335) também aprovado. Auditorias de dependências de execução e ferramentas não reportaram vulnerabilidades conhecidas naquele ensaio; pacote local não auditável no PyPI. Isso não é auditoria completa do histórico legado.

P07 Linux: todas as **23 tabelas** com contagens/digests iguais antes das escritas de smoke, grants/exclusões conferidos; três perfis × origem/cópia/retorno; TLS verificado, SMTP STARTTLS, cookies Secure/HttpOnly, owner/capacidade/privacidade e replay de idempotência persistida. Backup 0,251 s, restore/reconciliação 0,557 s, ativação e verificações da cópia 23,449 s. Somente durações observadas, sem SLA/RPO/RTO produtivos. [Runbook](../runbooks/operations-recovery.md).

P08 gravação: **14 checkpoints**, axe sem violação nos critérios exercitados, nenhum erro JavaScript, reflow conferido e histórico público sem nota privada. Configuração/reserva futura permanecem iguais após consulta de impacto. [Registro](../case/media/capture.json), [vídeo e transcrição](../case/README.md#três-jornadas-demonstradas). Cinco minutos de serviço e passo de um minuto são parâmetros sintéticos de demonstração, não alteração das regras do produto.

## Desempenho

| Ensaio | Ambiente/escopo | Resultado observado |
|---|---|---|
| API P07 CI | Linux limpo; 100 mil reservas; 20 sessões; 200 pedidos/cenário | Reserva p95 440,73 ms; maior leitura p95 255,87 ms; metas 800/400 ms; sem erro |
| API P06 local | Windows/WSL/Docker; mesmo dataset, dois workers; limites documentados | Reserva p95 775,91 ms; leituras até 304,80 ms; [relatório](../evidence/P06-api-benchmark.json) |
| Web P06 laboratório | Chromium/Pixel 7, CPU 4×, rede 150 ms/1,6 Mbps, cache frio; três amostras/rota | LCP até 2028 ms, INP até 88 ms, CLS até 0,00119; 9/9 aprovadas; [relatório](../evidence/P06-web-benchmark.json) |

Não comparar diretamente Windows/WSL com Linux para inferir ganho percentual. Não há carga máxima, métricas de campo ou benchmark comparável do 2.0. Metas/timeouts não foram relaxados para passar.

## Aceites e limitações com responsável

| Ponto | Estado | Responsável / próximo passo |
|---|---|---|
| Revisão final dos três perfis | Pendente humana | Lucas: roteiro P08 e registro de resultado |
| Leitor de tela | Pendente humana desde P06 | Lucas: [roteiro NVDA/VoiceOver](../runbooks/quality.md); informar leitor/versão/jornadas/achados |
| Publicação, domínio e e-mail externo | Adiados D10 | Lucas: definir provedor/orçamento e autorizar promoção |
| Backup fora do host/custódia/retenção | Adiados D10 | Lucas: escolher destino, comprovar cópia/restore e responsabilidade operacional |
| RPO/RTO e perda da máquina | Sem garantia produtiva | Lucas: definir metas após D10; demo atual não cobre perda do host |
| Importação histórica | Dispensada D08/D12 | Não executar migração de MySQL ou inventar reconciliação histórica |
| Multiempresa e pagamentos | Fora do MVP aprovado | Novas decisões de produto antes de expandir |
| Relógio WSL e contenção local | Limite ambiental conhecido | Procedimento/reversão P06; CI Linux independente; sem afirmar estabilidade absoluta |

Não há falha crítica conhecida de autorização/integridade nas verificações executadas. Esse recorte não equivale a certificação WCAG, pentest independente ou aprovação comercial. A candidata conserva os gates em [candidate.json](candidate.json).

## Evolução operacional posterior

Schema atual 0007, escala coletiva/pools físicos/transferência/contexto crítico e anterior/comunicação/painel/indicadores por pessoa, conforme [ADR-016](../adr/0016-operational-evolution.md). Check final local 126 Python + 20 React; E2E 15 + skip previsto e revisão 16 checkpoints. Novo roteiro HTTPS usa horário/SMTP reais e restaura regras temporárias; [evidência e limites atuais](../evidence/Operations-evolution.md). Medições locais e uma rodada Linux reprovaram carga e geraram otimização; resultado final/CI fica no PR, sem reutilizar métricas anteriores. Candidata permanece para revisão humana, com todos os gates D10/leitor de tela pendentes.

Web final: 9/9 amostras, LCP até 2452 ms, INP até 104 ms, CLS até 0,0011783, após carregar CSS operacional junto ao layout autenticado. API local ainda reprova relatório/painel/reserva; execução Linux da revisão `a4c2630` passou. [Carga local](../evidence/Operations-evolution-api-local.json), [web e condições](../evidence/Operations-evolution-web-benchmark.json); CI final permanece registrada no PR.
