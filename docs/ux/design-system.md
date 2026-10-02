# Design system implementado

**CURRENT · código `2549523`.** Biblioteca CSS/React efetiva, sem alegação de biblioteca Figma ou catálogo completo de padrões. [UX atual](PetLand_3.0_UX_Final.md).

## Foundations

| Fundação         | Valores reais e uso                                                                                                              |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Marca            | `--brand-700 #1f5d50`, `--brand-900 #163c34`, `--brand-50 #e8f2ec`.                                                              |
| Acento           | `--accent-600 #a94f2d`, `--accent-50 #fae9dd`, terracota editorial.                                                              |
| Superfície/texto | Canvas `#f7f5ef`, surface `#fff`, text `#243a35`, muted `#596b65`.                                                               |
| Bordas           | Border `#d5ded8`, control-border `#71867c`.                                                                                      |
| Semântica        | Danger `#b42318`/soft `#fff1f0`, warning `#8a5600`, info `#235b87`/soft `#eef5fa`. Estado também textual.                        |
| Tipografia       | Inter Variable corpo (100–900), Manrope Variable títulos (200–800), Georgia/Times editorial. WOFF2 locais, `font-display: swap`. |
| Escala base      | 0,75/0,875/1/1,25/1,75/3rem; editorial usa `clamp`, incluindo hero 3,3–5,75rem no desktop.                                       |
| Espaçamento      | 4/8/12/16/24/32/48/64 px. Features também têm medidas locais, sem normalização absoluta.                                         |
| Radius/medidas   | Controle 8, card 12, feature 20 px; conteúdo máximo 1280 px, controle base 48 px.                                                |

[Tokens](../../apps/web/src/shared/styles/tokens.css), [fontes](../../apps/web/src/shared/styles/fonts.css), [global](../../apps/web/src/shared/styles/global.css), [editorial](../../apps/web/src/shared/styles/editorial.css). Manrope/Inter OFL por `@fontsource-variable`, sem requisição a Google Fonts/CDN. Retrato WebP é [imagem gerada com proveniência](editorial-image.md); lucide reforça labels, não substitui conteúdo.

## Components

| Componente            | Comportamento                                                | Código                                                                |
| --------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------- |
| Button                | Primary/secondary/danger, busy/disabled, elemento nativo     | [Button](../../apps/web/src/shared/ui/Button.tsx)                     |
| Input                 | Label, required, hint/erro associados por IDs, props nativas | [Input](../../apps/web/src/shared/ui/Input.tsx)                       |
| Select / TextArea     | Controles nativos com label/erro                             | [Select](../../apps/web/src/shared/ui/Select.tsx)                     |
| Badge / Alert         | Estado textual e destaque                                    | [Feedback](../../apps/web/src/shared/ui/Feedback.tsx)                 |
| Skeleton / EmptyState | Loading rotulado e vazio com orientação                      | [Feedback](../../apps/web/src/shared/ui/Feedback.tsx)                 |
| LocalEmailNotice      | Caixa local/limite de entrega pela origem conhecida          | [LocalEmailNotice](../../apps/web/src/shared/ui/LocalEmailNotice.tsx) |
| PetPortrait           | Retrato editorial com alt conforme contexto                  | [PetPortrait](../../apps/web/src/shared/ui/PetPortrait.tsx)           |

## Patterns

Formulários RHF/Zod validam entradas; API permanece soberana para propriedade, versão e disponibilidade. Hint/erro ligado ao campo, foco pertinente e tentativa para falha remota. Galeria tem formulário demonstrativo sem persistência; loading não simula sucesso.

Reserva: seleção → resumo → confirmar → resultado persistido; recuperar resposta perdida reutiliza tentativa idempotente. Conflito requer nova disponibilidade. [BookingPage](../../apps/web/src/features/booking/BookingPage.tsx).

Operação: alerta/contexto antes de iniciar, nota interna separada de resumo público, motivo para transferir, prévia de impacto para escala/capacidade. Feedback específico em [care](../../apps/web/src/features/care/Feedback.tsx) e [booking](../../apps/web/src/features/booking/Feedback.tsx), sem componente genérico que substitua regras.

## Layouts

[PublicLayout](../../apps/web/src/shared/layout/PublicLayout.tsx): header/footer e topo. [HomePage](../../apps/web/src/features/home/HomePage.tsx): hero assimétrico, retrato, trilha numerada, apresentação/link ao catálogo e contato. [CatalogPage](../../apps/web/src/features/care/CatalogPage.tsx) usa linhas de serviços/preço/duração. [AccountLayout](../../apps/web/src/features/identity/AccountLayout.tsx): tutor no topo/equipe lateral; menu e atalhos móveis. Painel/gestão usam números e linhas, com cards nos agrupamentos úteis.

Breakpoints são específicos: 1100/1000/960/900/760/640/600/520 px, não um único grid de tokens. Em 320 px menu recolhe, ações quebram e áreas passam a uma coluna. [identity.css](../../apps/web/src/shared/styles/identity.css), [operational.css](../../apps/web/src/shared/styles/operational.css), [operations.css](../../apps/web/src/shared/styles/operations.css), [booking.css](../../apps/web/src/shared/styles/booking.css), [care.css](../../apps/web/src/shared/styles/care.css). CSS operacional acompanha layout autenticado sob demanda.

## Accessibility e motion

Foco visível, skip link, labels/IDs, landmarks/headings, destino ativo e teclado. [RouteFocus](../../apps/web/src/shared/layout/RouteFocus.tsx) atualiza título/foco. Menu usa `aria-expanded`/`aria-controls`, Escape/retorno de foco; resumo da reserva recebe foco no título. Transições curtas editoriais reforçam ação; global/editorial respeitam `prefers-reduced-motion`. Não há informação disponível apenas por animação.

WCAG 2.2 AA é **meta**. Axe/reflow/teclado são verificações delimitadas; leitor de tela e aceite humano estão pendentes. [Capturas atuais](media/current/capture.json), [revisão visual histórica](visual-review.md), [RNFs](../architecture/non-functional-requirements.md). `/design-system` demonstra componentes, mas não enumera todos os padrões de feature.
