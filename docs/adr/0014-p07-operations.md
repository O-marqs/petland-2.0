# ADR-014 — Demonstração e recuperação local P07

Aceita pela autorização expressa P07 e pelas recomendações delegadas. Complementa ADR-008/009 somente no ensaio local; hospedagem, domínio, retenção externa e SLA dependem de D10.

## Escopo

D08/D12 dispensam importação histórica. PL3-19 registra a dispensa, não uma migração executada. PL3-20 prepara e ensaia operação em ambiente distinto. O avanço P07 foi autorizado após merge P06; o aceite humano com leitor de tela continua pendente, sem declaração de aprovação sonora.

## Decisões

- Compose `petland7`, volume e portas próprios, PostgreSQL 17, API com papel restrito e migration como job único. Desenvolvimento `petland3` continua separado. Nenhum serviço comercial é semeado no desenvolvimento ou na inicialização normal da API.
- Build estático multistage, Nginx fixado por digest, assets por hash com cache longo, HTML revalidável e API sem cache. Web/API sem root, filesystem somente leitura, sem capabilities e sem porta pública da API. Nginx substitui headers de encaminhamento; Uvicorn não confia em proxy headers. Logs de acesso Nginx desativados para evitar registrar URLs arbitrárias.
- Staging usa as validações existentes: HTTPS, cookies Secure/HttpOnly, PostgreSQL `verify-full` e SMTP STARTTLS obrigatório. CA local e certificados gerados fora das imagens e do Git; sem desabilitar validação no cliente Python/SMTP/PostgreSQL. O Chromium de ensaio aceita o certificado local não instalado no sistema; verificação Python rigorosa antecede esse ensaio.
- Seed privilegiado exclusivamente offline, com UUIDs estáveis, referência de data explícita, quatro identidades fictícias, dois tutores, quatro pets, três serviços, dois recursos e seis cenários de agenda. Uma transação e lock consultivo; validações de domínio e constraints reais. Repetição preserva o fixture existente. Recusa banco não identificado como demo, banco ocupado sem marcador e execução em produção. Senhas aleatórias apenas em arquivo local ignorado, sem senha default ou token exposto.
- Estados/eventos/notas semeados são fixtures identificados, não alegação de entrega de e-mail. O smoke realiza cadastro/consumo de e-mail real, reserva/repetição/cancelamento reais e revalida propriedade, capacidade e privacidade. A idempotência persistida é exercitada novamente após restore.
- Reset cria outro banco, executa migrations, semeia e troca a API; conserva o anterior. Restore cria destino aleatório e nunca usa `--clean` ou sobrescreve banco existente. Somente destino reconciliado é ativável.
- Backup consistente `pg_dump -Fc`, preservando ACLs; pausa apenas as escritas da demo. Archive e manifesto são autenticados/criptografados com Fernet e a chave permanece separada. Dump em claro só em memória, limite 64 MiB deliberado para demo. Restore verifica formato, versão, hash e todas as contagens/digests por tabela, além de grants e das duas exclusões GiST. `pg_restore` falha atomicamente em transação única. Chave inválida/corrupção são recusadas antes de criar banco.
- Ensaio troca a aplicação para a cópia, verifica API/SMTP e navegador nos três perfis, depois retorna à origem preservada. Falha ao iniciar o destino restaura o apontamento anterior e tenta reiniciar a origem, sem esconder a falha. Registra tempos observados, imagens, hashes, banco alvo e relatório sem credenciais. Não prova PITR, SLA ou recuperação após perda da máquina.
- CI repete staging/seed/reset/backup/restore/navegador em Linux e banco novos. Falhas não são convertidas em sucesso; volumes não são apagados pelos comandos de rotina.

## Limites

Backup local é ensaio, não proteção contra perda do host. Cópia fora do host, custódia da chave, retenção 7 diários + 4 semanais, agendamento diário e restore mensal permanecem propostas para D10. Nenhuma automação ou recurso externo é criado nesta entrega. RPO/RTO produtivos e promoção exigem decisão explícita; downgrade de dados não é rollback operacional. P08 não começa automaticamente.

Fontes técnicas: [pg_dump PostgreSQL 17](https://www.postgresql.org/docs/17/app-pgdump.html), [pg_restore](https://www.postgresql.org/docs/17/app-pgrestore.html), [Fernet](https://cryptography.io/en/stable/fernet/), [SMTP Mailpit](https://mailpit.axllent.org/docs/configuration/smtp/), [proxy Nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).
