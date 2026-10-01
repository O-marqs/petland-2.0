# ADR-013 — Verificação P06 e consultas de operação sob carga

Status: implementado; aceite transversal registrado nas evidências P06.

## Contexto

PL3-18/RNF02 exige 100 mil agendamentos e 20 sessões simultâneas. A primeira execução no host Windows encontrou p95 de 451 ms no histórico, 671 ms na agenda e indisponibilidade no relatório mensal durante o aquecimento. O relatório materializava milhares de objetos e serializava todas as leituras no lock exclusivo do estabelecimento.

## Decisão

- Agregar contagem por estado/serviço e minutos ocupados em PostgreSQL, devolvendo `PeriodTotals` pela port. A aplicação continua calculando a capacidade pelo calendário e aplicando as fórmulas do ADR-012. Agendamentos que atravessam o período contribuem somente com sua interseção; a contagem usa o início contratado; cancelados/faltas não ocupam capacidade.
- A reserva consulta somente a janela ocupada pela oferta (incluindo buffers), preservando atendimentos abertos vencidos. O relatório usa `FOR SHARE` no mesmo registro do estabelecimento: relatórios coexistem, enquanto alterações coordenadas continuam esperando. Escritas continuam com `FOR UPDATE`, como primeiro lock; exclusões GiST, revalidação de identidade, versão, idempotência e outbox permanecem obrigatórias. Não há cache de permissões nem de vagas.
- Migration 0006 acrescenta índices para fim da ocupação, execução aberta, histórico do cliente e período da auditoria. Downgrade remove apenas esses índices.
- Carregar sessão, usuário e papéis em uma consulta; cada acesso continua verificando validade e permissões atuais. A lista de usuários carrega papéis em lote. O catálogo obtém serviço, portes e espécies juntos; uma reserva nova usa INSERT diretamente, reduzindo consultas dentro do lock sem mudar a atomicidade.
- A leitura que adquire o lock também carrega a configuração. Esse valor é reutilizado somente pela instância de persistência daquela transação, enquanto o lock permanece adquirido, e atualizado após salvar. Recursos elegíveis são filtrados em SQL pelo contrato público de identidade, mantendo status ativo, e-mail verificado e papel de equipe; não se guarda elegibilidade entre requisições.
- Ao resolver o proprietário, carregar também o destinatário do aviso pelo contrato público de clientes. A transação conserva esse contato para a outbox, eliminando uma segunda leitura e um flush antecipado; alteração assistida sem proprietário informado continua resolvendo o contato pelo atendimento original. Nenhum dado é reutilizado entre requisições.
- Limitar offsets HTTP a 100 mil, coerente com agenda e identidade; aceitar inteiros maiores causava trabalho excessivo ou overflow no banco. Resposta 422 segue o contrato público seguro.
- Definir política de conteúdo nos servidores web locais. Preview do build permite scripts apenas da própria origem; desenvolvimento permite os scripts inline e o websocket usados pelo Vite. Formulários usam Zod sem geração dinâmica de código. Estes headers precisarão ser reproduzidos no servidor escolhido na futura publicação; Vite preview não é um servidor de produção.
- Centralizar foco e título por página. Conteúdo assíncrono recebe anúncio quando aparece, sem retirar foco de quem já começou a digitar. Alterar filtros na query string não reinicia o foco; redirecionamento ao login preserva os filtros.
- Carregar cada página dentro da área de conteúdo, com uma boundary `Suspense` identificada pelo pathname. O menu permanece disponível e o carregamento recebe resposta visual imediata, sem aguardar o download de todo o destino; filtros não remontam a página. O main público reserva ao menos uma viewport para evitar deslocar o rodapé durante o primeiro carregamento. A medição encontrou INP de 528–576 ms na navegação inicial para login antes desse ajuste. Esse uso de chave segue a [redefinição de Suspense na navegação](https://react.dev/reference/react/Suspense#resetting-suspense-boundaries-on-navigation).
- Reservar espaço para os resultados do catálogo, evitando que o bloco seguinte salte durante o carregamento.

## Medição e limites

O benchmark padrão usa API e PostgreSQL dentro da rede Compose, correspondente à execução local documentada. Um banco novo com nome aleatório `_test` é criado por rodada e removido ao final; o banco de desenvolvimento nunca é destino. Sessões e dados são exclusivamente sintéticos. Login/CSRF ficam fora da janela medida; a reserva inclui commit, evento, auditoria e persistência do aviso, mas não entrega SMTP. Dois processos Uvicorn e pool padrão 5+5 por processo, também configurados no Compose; não se aumenta timeout para esconder contenção.

Os resultados do host Windows e da rede Compose são calibrações diferentes e ficam separados. Não extrapolar esses números para infraestrutura externa, ainda adiada por D10. Medição web usa build, cache frio, CPU/rede reduzidas e interações reais automatizadas; não é dado de usuários reais. Axe/árvore acessível/teclado não substituem o aceite sonoro com leitor de tela.

## Verificação

Testes PostgreSQL verificam os limites de período, contagens/ocupação, convivência dos locks de leitura, exclusão de escrita, limites HTTP, tentativas entre contas, origem maliciosa e corpo excessivo sem efeitos. Suíte anterior conserva as disputas de reserva, versão, último administrador, rollback e notas privadas. Ver resultados reais e pendências em [P06](../evidence/P06.md).
