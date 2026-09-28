# Identidade local — P02

## Cliente

Execute `python scripts/dev.py init` e `python scripts/dev.py up`. O volume existente recebe a migration `0002_identity`; não apague o volume para atualizar.

1. Abra [Criar conta](http://localhost:5173/criar-conta) e use dados sintéticos, por exemplo e-mail em `example.com`.
2. Abra a [caixa local Mailpit](http://localhost:8025). Ela recebe SMTP real, sem enviar para destinatários externos.
3. Abra o link da mensagem e pressione **Confirmar e-mail**. Entre em [Entrar](http://localhost:5173/entrar).
4. Consulte **Minha conta**: dados básicos, confirmação, troca de senha e sessões.
5. Use **Esqueci minha senha**, abra a nova mensagem, redefina e entre novamente. O link não pode ser reutilizado.

Conta não verificada pode consultar sua identidade e pedir reenvio. Conta desativada não inicia nem mantém acesso autorizado.

## Primeiro administrador

Não há senha inicial nem opção ADMIN no cadastro público. Com o ambiente iniciado e sem admin ativo, o operador executa:

```sh
python scripts/dev.py bootstrap-admin --email administrador-sintetico@example.com
```

Abra a mensagem no Mailpit, aceite em até 30 minutos e defina a senha. Conta existente exige sua senha atual. O bootstrap é auditado e recusado após existir admin ativo. Para conceder ADMIN a outra conta, use **Pessoas e acessos** com a senha do administrador atual.

O teste E2E provisiona `p02-admin-sintetico@example.com` apenas na demo local inicialmente vazia, usando credencial de fixture. Isso não é seed de produção. Para demo já provisionada, configure `E2E_ADMIN_EMAIL`/`E2E_ADMIN_PASSWORD` com conta sintética autorizada. Se já houver outro admin e as credenciais não servirem, o teste falha sem alterar esse administrador.

## Convites e papéis

Em [Pessoas e acessos](http://localhost:5173/gestao/acessos), informe e-mail da pessoa e sua senha atual. O destinatário aceita o link e cria senha; conta existente exige a senha atual e preserva CUSTOMER ao receber EMPLOYEE.

Troca de perfil/ativação exige reautenticação e versão atual, revoga sessões e registra auditoria. O último admin ativo é protegido, inclusive sob concorrência. As políticas comerciais ainda pendentes não recebem permissões implícitas.

## Recuperação administrativa

Use recuperação normal pelo e-mail: reset mantém papéis e revoga sessões. Outro admin pode corrigir permissões. Se não existir administrador ativo, bootstrap pode ser executado por operador com acesso ao ambiente. Não há bypass público nem alteração SQL automática de admin existente. Perda simultânea de e-mail e todos os acessos ativos exige procedimento extraordinário aprovado, fora da UI.

## Operação

- `python scripts/dev.py prune-identity`: remove sessões/tokens expirados há mais de 24 h e contadores antigos; preserva contas/auditoria. Planejar execução diária antes de publicar.
- Variáveis SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_SENDER`, `SMTP_STARTTLS`, `SMTP_USERNAME`, `SMTP_PASSWORD`. Host local padrão 127.0.0.1:1025; container usa Mailpit. Produção exige STARTTLS e segredo externo; D10 permanece pendente.
- Mailpit: interface loopback 8025, SMTP loopback 1025; não publicar a caixa de desenvolvimento.
- Falha SMTP: evento `identity_mail_delivery_failed`; corrigir conectividade/configuração e pedir reenvio. `202` não confirma entrega.
- `429`: aguarde a janela de 15 minutos; não remova limites para facilitar testes.
- Link expirado/usado não autentica. Abrir o link não consome automaticamente seu token.
- Mudanças no código Docker exigem `up`. `down` preserva dados; `--volumes` não é rotina.

## Telas e escopo

Públicas: `/entrar`, `/criar-conta`, `/recuperar-acesso`, `/verificar-email`, `/redefinir-senha`, `/aceitar-convite`. Autenticadas: `/app`, `/app/conta`, `/operacao`, `/gestao`, `/gestao/acessos`. Galeria separada: `/design-system`.

As áreas mostram dados reais da conta e recursos disponíveis. Perfil comercial, troca de e-mail, pets, catálogo, reservas, atendimentos, notas e gestão operacional continuam nos cards futuros, sem números simulados.
