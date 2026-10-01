# Correção do primeiro acesso — 01/10/2026

Pedido em `docs/implementation/Onboarding-request.txt`. Branch `petland-3.0-onboarding-fix`, base P04 após merge P08 `3fba52725d5a6e77fd87b40a2e166a0a436f64df`. Escopo RF01/RF02/RF03/RF06/RF07 e RNF01/RNF04: tornar o caminho de uma conta nova realizável e visível, mantendo os contratos existentes.

## Reprodução e causa

O cadastro real retornou sucesso, gerou usuário ainda não verificado e entregou confirmação no SMTP local. O login real retornou 200 e levou a `/app/conta`; a API manteve pets/reservas bloqueados até confirmar o e-mail. A tela não explicava onde encontrar a mensagem no ambiente local. O dashboard separava o cadastro de contato do acesso, mas não apresentava essa sequência com destaque. A entrada direta no agendamento sem contato buscava pets e recebia 404, sem orientar o pré-requisito.

Não se constatou falha no envio local nem ausência da funcionalidade de pets/reserva. A entrega para a caixa pessoal externa não está configurada: D10 permanece adiada. A verificação anterior com contas de demonstração já confirmadas não cobria essa experiência de primeiro acesso de ponta a ponta.

## Implementação

- Cadastro apresenta passos seguintes e move o foco ao título de conclusão; preserva resposta pública genérica e não cria sessão automaticamente.
- Caixa de teste em banner, confirmação pendente, cadastro/recuperação e conclusão da reserva. Link somente nas origens locais explicitamente suportadas, com guarda de modo de demonstração/desenvolvimento; ausente em domínio externo.
- Confirmação mantém consumo explícito do token, fragmento removido da URL e consulta da sessão real antes de oferecer a área autenticada. A conta pendente pode conferir a confirmação no servidor e continuar; conta já confirmada tem acesso direto à área.
- Navegação pública oferece a área da sessão atual. Composição em `app` injeta links de identidade no layout compartilhado; `shared` não importa `features`.
- Dashboard apresenta contato → pet → reserva. Entrada direta no agendamento verifica contato e orienta completá-lo antes de consultar pets. Resumo e dupla confirmação da reserva permanecem reais.
- Novo roteiro de aceite manual e ensaio `apps/web/scripts/onboarding-staging.mjs`, também executado pela CI de operações.

Nenhuma migration, mudança de contrato API, bypass de e-mail, associação por endereço ou alteração de preço/agenda. Fontes sincronizadas, documentos originais, main, tag legada e alterações do checkout original preservados.

## Verificações locais

- `python scripts/dev.py check`: **114 testes Python + 18 React aprovados**, Ruff/mypy/arquitetura/scan, lint, tipos, formatação, contratos e build aprovados. PostgreSQL efêmero separado; não usa SQLite.
- `python scripts/dev.py e2e`: **15 aprovados + 1 skip mobile previsto** do bootstrap singleton. A jornada do cadastro pela interface agora entra sem confirmar, comprova API 403, confirma em segunda aba, atualiza a sessão, salva contato/pet, volta à área pela navegação pública e ainda verifica recuperação/revogação. Desktop e celular aprovados.
- Staging com TLS verificado usando a CA local: nova conta pela interface → confirmação SMTP real → contato → pet persistido após reload → seleção/resumo sem reserva → POST reserva 201 → mesmo ID no back office → reagendamento com novo horário → cancelamento preservando histórico. Os quatro e-mails foram capturados no Mailpit do staging.
- **9 checkpoints** de onboarding com axe sem violações e reflow, incluindo 320 px, sem erro JavaScript na página cliente; cookies da sessão Secure/HttpOnly. Relatório/capturas locais em `.local/staging/browser/onboarding`; sem senha/token em documentação ou artefatos públicos.
- Uma primeira tentativa do novo ensaio interrompeu na leitura do envelope do detalhe (`appointment`); a asserção da ferramenta foi corrigida e só a reserva sintética daquela tentativa foi cancelada pela interface. A rodada completa seguinte passou. Não foi corrigido ou ocultado um erro do produto nesse ponto.
- Revisão React: hooks incondicionais, cache remoto TanStack, estados derivados na renderização, efeito de foco apenas ao concluir, links/botões semânticos e fronteiras de importação preservadas.

O check completo antecedeu o último ajuste simples do link de conta confirmada e do texto genérico. Lint/build/tipos e smoke final dos perfis validam esses ajustes; os checks remotos repetem o conjunto no commit da revisão. Resultados remotos e SHA exato ficam registrados no PR. Capturas e vídeo P08 continuam identificados como prova histórica daquela entrega; não são relabelados como esta correção.

## Limites e continuidade

Entrega externa de e-mail, hospedagem externa, leitor de tela e aceite humano final continuam pendentes. Esta correção permite testar cliente/funcionário no staging local existente. Não representa aprovação automática de todos os casos de uso, release estável, publicação ou merge. Repetir o [roteiro manual](../runbooks/manual-acceptance.md) com a conta do usuário e registrar ocorrências concretas.
