# ADR-015 — Candidata de revisão e case P08

Aceita no escopo de preparação pela autorização “pode seguir para p08 então”, após merge P07 `3dde06b`. PL3-21, RF13 e §20 do plano. Não constitui aceite final de produto, leitor de tela ou publicação.

- Versão candidata explícita `3.0.0-rc.1`, Python equivalente `3.0.0rc1`. OpenAPI/pacotes/factory permanecem coerentes; contratos gerados pelo comando existente. Sem mudança de schema ou regra comercial.
- Case documenta problema, decisões e trade-offs, jornadas, capturas, métricas medidas e limites. Personas continuam hipóteses; não inventar pesquisa, clientes reais ou percentual de ganho frente ao legado sem benchmark.
- Antes é renderização isolada de dois templates/imagem da baseline, com adaptações/hashes. Não executar o legado nem presumir MySQL funcional. Depois é aplicação real; conceitos do Caderno UX não substituem capturas de implementação.
- Gravação local em banco reset próprio, identidades/serviço sintéticos e relógio real. Cadastro/reserva/transições ocorrem pela UI; leituras API conferem persistência/privacidade/impacto. Pré-autenticação e alvo futuro API são declarados; credenciais não são filmadas/logadas. Legendas e transcrição acompanham vídeo sem áudio.
- Pacote de revisão usa `git archive` da árvore limpa do commit. Inventário/hashes e gates vão em manifesto, com verificação sem extração. Ferramenta local não publica, tagueia, faz merge ou concede aprovação. Artefatos privados não entram.
- D10 permanece vigente, sem provedor/publicação/backup externo. O aceite humano com leitor de tela segue pendente; merge/CI/axe não o substituem. Tag/release estável e promoção serão preparadas sobre aceite concreto, conforme gate P08.

Uma release estável seria uma alegação incorreta enquanto esses gates estão pendentes. Entregar candidata e case verificáveis permite revisão concreta sem mudar decisões silenciosamente. Próxima ação depende do aceite, não de nova funcionalidade presumida.
