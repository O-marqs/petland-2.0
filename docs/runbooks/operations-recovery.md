# P07 — Demonstração, backup e recuperação

Este roteiro atua somente no ambiente local isolado `petland7`, com dados fictícios. D08/D12 dispensam MySQL histórico; D10 mantém publicação externa adiada. Responsável operacional: Lucas. Aceite humano com leitor de tela permanece no roteiro P06.

## Preparar e acessar

Dependências de desenvolvimento do README instaladas; Docker ativo. Da raiz:

```sh
python scripts/dev.py staging-init
python scripts/dev.py staging-up
python scripts/dev.py seed-demo
pnpm --filter @petland/web exec playwright install chromium
python scripts/dev.py smoke-demo
python scripts/dev.py rehearse
```

Aplicação estática: **https://localhost:8443**. Caixa SMTP isolada: http://localhost:8026. PostgreSQL de staging: loopback 55434. Desenvolvimento continua em 5173/8000/55432 e não recebe os dados demo.

`staging-init` gera `.local/staging/config.env`, CA/certificados, chave de backup e `.local/staging/accounts.json` com e-mails/senhas dos perfis. Segredos não são impressos, versionados ou incorporados a imagens. A página informa que todos os dados são fictícios. Para login, consulte `accounts.json` localmente; não cole seu conteúdo em issues, screenshots ou relatórios. Não existe senha compartilhada/default.

Certificado emitido por CA local, sem instalação automática no sistema. Para navegação humana confiável, importe **apenas o certificado público** `.local/staging/certs/ca.crt` no perfil de teste do navegador/sistema ou aceite o certificado somente nesse localhost. A chave da CA não é pública. Smoke Python, PostgreSQL e SMTP verificam TLS integralmente; o Chromium isolado de ensaio aceita a CA não instalada. Certificados expiram em 90 dias; `python scripts/dev.py staging-renew-certs` renova e reinicia apenas staging, preservando dados/credenciais. Depois execute `smoke-demo` e confirme o certificado novo.

Parar sem apagar dados: `python scripts/dev.py staging-down`. Retomar: `staging-up`. Nunca usar `down --volumes` como rotina. `staging-up` etiqueta imagens pelo commit (sufixo `-work` quando há mudanças locais); ensaio registra image IDs e revisão. Artefatos não são publicados em registry externo.

## Cenários de demonstração

UUIDs estáveis e datas relativas à referência. Dois tutores A/B, cachorro/gato, porte grande e pet arquivado. Banho e banho/tosa têm tempos diferentes por porte; terceiro serviço inativo. Dois recursos, almoço, dia fechado em referência +7 e exceção parcial +8. Dois pets ocupam a última capacidade às 09h de referência +1; atendimento longo às 14h. Histórico inclui concluído, cancelado, falta, nota privada e resumo público. São condições fictícias, sem presumir preços/horários de uma loja real.

Seed repetido não duplica ou desloca registros. `seed-demo --reference-date YYYY-MM-DD` aceita data para um banco novo; fixture existente é preservado. Para atualizar a demo, leia o nome em `.local/staging/active-db.txt` e execute:

```sh
python scripts/dev.py reset-demo --confirm NOME_EXATO_DO_BANCO_DEMO_ATIVO
```

Reset cria outro banco e preserva o anterior; não apaga dados para “voltar ao início”. Datas antigas podem impedir reserva/smoke; crie demo nova com referência atual. Não remover marcador para adotar banco com dados existentes.

## Backup e restauração

`python scripts/dev.py backup-demo` pausa a API da demo, confere o marcador, faz dump custom consistente e grava `.local/staging/backups/*.plbackup` criptografado/autenticado, com checksum/contagens em sidecar JSON. Retoma a API ao terminar. Chave em `.local/staging/keys/backup.key`, separada do diretório de archives. Não há dump em claro em disco. Ferramenta limitada a archives de demo com dump até 64 MiB e schema atual; não substitui estratégia para bancos grandes ou produção.

```sh
python scripts/dev.py restore-demo --backup CAMINHO_DO_ARCHIVE.plbackup
```

Cria banco `petland_recovery_<id>_demo` novo. Recusa archive adulterado/chave errada antes de tocar banco; não sobrescreve destinos. Confere todas as tabelas, contas/referências, reservas, eventos, notas, idempotências, outbox, revisão, ACLs e exclusões GiST. Resultado em `.local/staging/restores/<banco>.json`; só depois é permitida a ativação:

```sh
python scripts/dev.py activate-demo --target NOME_DO_BANCO_RECONCILIADO
python scripts/dev.py smoke-demo
node apps/web/scripts/smoke-staging.mjs recovery
```

A ativação verifica marcador/schema antes de parar a API. Se o novo ambiente falhar ao iniciar, restaura o apontamento anterior e tenta reiniciá-lo; a falha continua sendo reportada. Se a origem também não subir, o apontamento continua preservado e exige investigação de readiness/Docker.

O roteiro `rehearse` faz backup, restore, ativação, smoke HTTP/SMTP e três perfis no navegador; tenta retornar à origem mesmo se a verificação da cópia falhar. Relatório `.local/staging/rehearsal.json` contém contagens/digests, tempos e imagens, sem senhas/tokens. Verificar `seed_idempotent`, `reconciled`, smokes e navegador aprovados. Capturas em `.local/staging/browser/{source,recovery,return}`. Sessões e contas sintéticas de smoke são escritas deliberadas durante a verificação; a comparação exata da cópia ocorre antes delas.

## Incidente e operação futura

1. Readiness falha: conferir Docker e logs da API/migration; não confirmar reservas enquanto banco/schema não responderem. E-mail falha: verificar Mailpit/STARTTLS e outbox; gravação local não comprova entrega.
2. Parar escritas com segurança. Escolher archive confiável e chave correspondente; preservar origem e logs.
3. Restaurar em banco novo e conferir relatório/grants/contagens. Só ativar depois de reconciliar; testar login, propriedade, reserva e histórico.
4. Em falha após troca, voltar ao banco anterior com `activate-demo --target`, verificar readiness/smoke e reconciliar escritas feitas após o ponto do backup. Não retornar cegamente perdendo operações novas.
5. Para imagem incompatível, retornar à imagem compatível com o schema. Nunca usar downgrade de migration que descarta dados como mecanismo de rollback; mudanças incompatíveis pedem plano de preservação ou roll-forward.

Os tempos do relatório são observações do ensaio, não SLA. RPO é a perda tolerável entre escritas e último ponto recuperável; RTO inclui restaurar, reconciliar, ativar e verificar. Valores produtivos dependem de D10 e volume/uso. Nesta entrega o backup continua no mesmo host: perda da máquina também perde essa cópia.

Antes de publicar, decidir armazenamento externo/criptografia/custódia da chave e comprovar cópia fora do host. Proposta ainda não executada: backup diário, 7 diários + 4 semanais, restore mensal em ambiente descartável. Alerta de backup ausente/idade >48h aponta para `backup-demo` e investigação do agendamento; restore não ensaiado há >31 dias aponta para `rehearse`. Sem agendamento/alerta automático criado. Provedor, frequência, retenção e metas finais precisam de aceite. A cópia da chave deve ficar em custódia distinta do archive.
