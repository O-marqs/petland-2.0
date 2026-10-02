# PetLand — revisão visual e navegação

Pedido de 01/10/2026: identidade própria, mais vida e composição autoral; análise crítica do menu lateral; manter leitura, desempenho e usabilidade. A resposta posterior esclareceu: **PetLand e seu case, mantendo a identidade de pet shop**, não um novo portfólio pessoal. Direção: premium, editorial, engenharia e humano; sem glow, glassmorphism, cyberpunk, animação excessiva ou aparência de template SaaS.

## Diagnóstico antes de mudar

| Parte | Padrão que deixava a página genérica | Direção implementada |
|---|---|---|
| Capa | Ilustração pequena em duas colunas equivalentes; título e texto com escala semelhante às outras telas | Retrato editorial grande com recorte em arco; título em três linhas, contraste entre Manrope e itálico serifado; assinatura circular discreta |
| Jornada | Três cards iguais, ícone decorativo, texto e rodapé repetido | Introdução editorial assimétrica + sequência numerada em linhas, com links para ações reais |
| Acesso e catálogo na home | Dois painéis claros muito semelhantes seguidos, ambos com ícones genéricos | Seção de serviços em verde profundo ocupando toda a largura; acesso em composição aberta de duas colunas, sem caixa |
| Contato | Mesmo painel arredondado da seção anterior | Informações reais em linha editorial separada; nenhum telefone, preço ou endereço inventado |
| Entrada | Desenho genérico dentro de mais um card | Fotografia de marca e texto aberto; formulário com divisão clara. Em celular, a história lateral continua oculta para priorizar a tarefa |
| Área do tutor | Banner decorativo, cards de atalho iguais e CTAs repetidos | Próximo cuidado real em primeiro plano, pets com iniciais próprias e lista, utilidades em linhas numeradas. Sem fingir que a foto de marca é o pet cadastrado |
| Operação | Navegação sem grupos e duplicação “Área da equipe”/“Agenda” | Grupos por tarefa, uma entrada de agenda, estado ativo também na rota original `/operacao`; títulos com presença e controles legíveis |
| Case | Cabeçalho comum seguido de muitas caixas iguais | Tipografia editorial, captura atual ampla, explicação visual da jornada, métricas abertas e vídeo em seção escura. Evidência histórica com rótulo explícito |

A assinatura recorrente é **arco do retrato + verde/marfim/terracota + palavras serifadas + percurso numerado**. É uma interpretação visual para PetLand, não uma alegação de pesquisa de marca ou garantia de reconhecimento por usuários. Na operação, números e hierarquia devem informar; fotografia não disputa espaço com a agenda.

## Topo ou lateral?

Minha recomendação é **híbrida por contexto**, não substituir todo menu pelo topo:

- **Tutor:** cinco destinos principais, sem hierarquia profunda. Navegação horizontal conserva o espaço de conteúdo e combina com pets/próximo cuidado. Conta e saída ficam no cabeçalho.
- **Equipe/admin:** alternância frequente entre agenda, reservas, clientes, serviços, equipe e gestão. Lateral permite grupos estáveis e mais destinos sem apertar o cabeçalho. Removida a duplicação da agenda.
- **Celular:** atalhos principais permanecem visíveis. O restante fica em um botão **Menu** com estado anunciado, grupos, Escape e fechamento ao selecionar uma rota. É expansão no fluxo, não drawer modal: não exige aprisionar o foco ou encobrir conteúdo.

Essa é uma **inferência aplicada ao PetLand**. O [Carbon: global header](https://www.carbondesignsystem.com/building-blocks/core/patterns/global-header) distingue produtos com poucas seções, adequados a header-only, de estruturas mais profundas, adequadas a header com painel lateral. O [Carbon: left panel](https://carbondesignsystem.com/components/UI-shell-left-panel/usage/) recomenda o painel quando há mais destinos e trocas frequentes. Isso sustenta avaliar quantidade, hierarquia e frequência, sem tratar “menu superior” como universalmente melhor.

A pesquisa do [NN/g sobre navegação oculta](https://www.nngroup.com/articles/hamburger-menus/) mostra prejuízos de descoberta quando todos os destinos ficam escondidos. Por isso, os atalhos de início/agenda e agendar/reservas ficam visíveis no celular; o menu completo permanece visível em telas amplas. Não se alegou teste A/B, redução de tempo ou satisfação medida no PetLand.

## Fotografia, tipografia e movimento

- Retrato de marca gerado pelo **tool integrado image_gen**, com cachorro/gato, textura fotográfica, iluminação suave, marfim, painel verde e base terracota. Nenhum cliente, funcionário ou loja real é representado. Identificação visível na capa e descrição alternativa.
- Arquivo de consumo: `apps/web/src/shared/assets/petland-editorial.webp`, 1536×1024, **125.962 bytes**. A preparação converteu o formato para WebP; não editou o conteúdo visual. Original preservado na saída do gerador. Prompt/proveniência em [editorial-image.md](editorial-image.md).
- Manrope/Inter continuam locais; o contraste editorial usa Georgia e fallback serifado do sistema. Sem novas fontes remotas, bibliotecas de animação ou dependências de interface.
- Imagem principal tem dimensões, carregamento prioritário e espaço reservado; nos formulários é lazy. Não há carrossel ou vídeo automático.
- Interações pequenas indicam ação: estado ativo, hover de botão e avanço da seta em links. `prefers-reduced-motion` remove transições. Sem conteúdo dependente de hover.
- Preços, disponibilidade, status e próximos cuidados continuam vindo da API. Nenhuma métrica fictícia foi criada para preencher o layout.

## Ajuste da escala diária no formulário

Ao sair de “Seguir o expediente da loja”, o calendário próprio antes começava com semana vazia. Isso tornava fácil fechar todos os dias ao tentar apenas adicionar uma folga. Agora começa com uma cópia da semana atual da loja; a pessoa confere essa base e adiciona datas especiais. O servidor continua intersectando os calendários e protegendo reservas existentes.

Há uma orientação recolhível em **Equipe e horários** explicando folga pontual, janela reduzida e reservas afetadas. Não foi criado um contador coletivo de funcionários; essa lacuna permanece registrada na [matriz funcional](../product/functional-gap-analysis.md).

## Validação e limites

Capturas antes/depois e verificações em `.local/product-review`, sem credenciais exibidas. `apps/web/scripts/review-staging.mjs` verifica quatro contextos, reflow/axe a 1440, 768 e 320 px, navegação por teclado, Escape/foco, fechamento por rota, reload, acessos por papel e calendário sem salvar. A jornada de onboarding/reserva/operação também continua sendo verificada pelos testes existentes. Resultados executados, CI e limitações em [Product-review.md](../evidence/Product-review.md).

O caderno UX original permanece íntegro como referência. Capturas/vídeo P08 não foram substituídos nem apresentados como novos. Acessibilidade automatizada e teclado não concedem aceite humano com leitor de tela. O redesign também não declara resolvidas as lacunas funcionais.
