# Design system inicial

Fonte: Caderno UX páginas 2, 4 e 11, com plano §8. Paleta e tokens em `apps/web/src/shared/styles/tokens.css`; estilos compartilhados em `global.css`.

Implementado: Button (primário/secundário/perigo/loading/disabled), Input com label real/hint/erro conectado, Badge, Alert, Skeleton, EmptyState, header/footer, skip link e navegação com estado ativo. Controles com pelo menos 44px; foco visível; redução de movimento; layouts de 320px a desktop. Ilustração vetorial original de cachorro/gato, sem depender de imagens sem licença ou fotos reais.

Manrope e Inter são servidas localmente pelos pacotes `@fontsource-variable`, licença OFL-1.1; os pacotes preservam os arquivos de licença. Não há requisição ao Google Fonts ou CDN de fontes. Valores adicionais de cor são restritos à ilustração e centralizados nos tokens.

`/design-system` é um ambiente explícito de demonstração. Formulário RHF/Zod valida um nome fictício, mantém o valor, foca o erro e nunca chama endpoint de pet. Não há timer que simule uma reserva ou uma persistência.

`/` adapta o conceito público à P01: apresenta a proposta e links funcionais; as jornadas futuras estão rotuladas como planejadas. Não exibe preços, horários, telefone ou endereço inventados. O indicador de conexão consulta a API real; ele não comprova que o módulo de reservas existe.

WCAG 2.2 AA é meta. As verificações automatizadas/teclado/reflow desta entrega estão em `docs/evidence/P01.md`; não foi realizada avaliação com leitor de tela ou usuários e não há certificação de conformidade.
