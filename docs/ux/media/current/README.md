# Capturas atuais

Oito telas reais do código funcional `2549523`: hero da home, tutor, resumo de reserva, painel diário, escala, capacidade, atendimento e gestão. Hero usa viewport; demais capturas mostram página completa. **16 checkpoints** desktop/mobile passam axe/reflow; mobile a 320 px é verificação, não arquivo adicional. [Manifesto e hashes](capture.json).

Data da captura, rotas e preparação estão no manifesto. Painel seleciona referência +1; escala/resumo usam +3; não são contagens de “hoje”. Conta, nomes, preços, tempos, cuidados e indicadores são exclusivamente sintéticos. A captura do resumo não confirma nova reserva. Não houve relógio simulado ou edição de conteúdo da tela; WebP lossless conserva pixels RGBA do PNG original.

## Reproduzir sem usar o banco pessoal

Requisitos do [runbook local](../../../runbooks/local.md), ferramentas host instaladas, staging inicializado/certificados vigentes, imagens funcionais correspondentes à referência e portas 8444/55435/8027 livres. O guard de fonte recusa diferenças em código/migrations/contratos/infra. Um novo estado funcional exige revisar referência/proveniência, não remover esse guard.

```sh
uv run --project apps/api python scripts/documentation_demo.py
node apps/web/scripts/capture-documentation.mjs
# Python com Pillow: na execução documental foi usado o runtime local do Codex.
python scripts/encode_documentation.py
python scripts/check_documentation.py
uv run --project apps/api python scripts/documentation_demo.py --down
```

Se as imagens de referência não existirem, `documentation_demo.py --build` compila a partir da fonte funcional conferida. O label identifica a referência funcional; a árvore documental pode conter ferramentas adicionais. Encoding requer Pillow (opcional para documentação, sem dependência do runtime da API).

Projeto `petlanddocs`, banco/volume/rede próprios; configuração resolvida com credenciais fica **somente em `.local/docs-capture/compose.json`**. Reutiliza contas sintéticas/certificados locais como configuração, sem copiar dados do staging. `down` para/remove somente containers/rede do projeto de documentação e preserva volume; não troca ponteiro de `petland7`, não limpa suas mensagens e não altera cadastros pessoais. Não publicar `.local` ou credenciais.

Fixture idempotente conserva sua data original; para reprodução posterior confira se as datas ainda estão no horizonte de reserva. Não apagar volume como solução automática. Histórico P08/revisão visual/evolução continua em [case/media](../../../case/media), com seus manifestos originais.
