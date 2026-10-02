# P03 — Clientes, pets e serviços

Use apenas dados sintéticos neste ambiente de portfólio. A instalação nova não cria clientes, pets ou serviços; somente referências de cachorro/gato e raças. Dados identificados como sintéticos podem permanecer após executar os testes de navegador locais.

## Cliente

1. Crie uma conta e confirme o e-mail no Mailpit. Entre e abra **Meu cadastro**.
2. Informe nome e, se desejar, telefone com DDD/endereço. O e-mail é o da conta confirmada.
3. Em **Meus pets**, adicione nome, espécie e porte; raça/nascimento podem ficar desconhecidos. Marque data estimada quando aplicável. Cuidados importantes ficam visíveis também à equipe.
4. Edite o pet ou use **Arquivar**, seguido da confirmação. **Arquivados** permite restaurá-lo; os dados não são apagados.

Se a equipe já tem seu cadastro, peça o link de vínculo antes de criar outro perfil. Abra o link no e-mail, entre/crie e confirme a conta com o mesmo endereço, reabra o link se necessário e confirme o vínculo. Validade: 24 horas e um único uso. Reenvio ou edição do cadastro invalida links anteriores. Contas que já têm outro cadastro recebem conflito e precisam de revisão da equipe; não há mesclagem automática nesta fase.

## Equipe

EMPLOYEE e ADMIN podem acessar **Clientes e pets** e **Serviços**. Convites, perfis e acesso de usuários continuam exclusivos do administrador.

- Busque cliente por nome/e-mail/telefone, ou escolha **Novo cliente**. Cadastro assistido não cria conta nem concede acesso automaticamente.
- No cadastro, **Ver pets** permite criação, edição, arquivo e restauração em nome do tutor.
- **Enviar link de vínculo** solicita envio ao e-mail salvo. Confira o contato antes de enviar. No ambiente local, a mensagem chega somente ao Mailpit; o aviso de solicitação não comprova entrega em um provedor externo.
- Em **Serviços**, crie nome/descrição, selecione espécies e portes atendidos. Para cada porte oferecido, informe preço BRL (inclusive zero) e duração em minutos. Marque **Serviço ativo no catálogo público** para publicar no catálogo local. Desmarque e salve para inativar.
- Conflito de versão: os dados digitados permanecem visíveis. No cadastro, **Recarregar dados salvos** descarta o rascunho explicitamente. Para pets/serviços, volte à lista e reabra o formulário para usar a versão atual.

## Verificação e limites

`python scripts/dev.py up` aplica 0003_catalogs preservando identidade existente. Migration reversível apenas em banco descartável; downgrade destrói os novos cadastros. Não faça downgrade para parar o aplicativo. O papel runtime tem leitura nas referências e permissões específicas para escritas comerciais/auditoria.

`python scripts/dev.py check` verifica as regras com PostgreSQL de testes. `python scripts/dev.py e2e` percorre os fluxos reais (incluindo SMTP local) e acessibilidade desktop/mobile. O teste administrativo singleton roda uma vez e também exercita viewport mobile.

Endereços: `/app`, `/app/perfil`, `/app/pets`, `/operacao/clientes`, `/operacao/servicos`, `/servicos` e `/vincular-cadastro`.

P04 entregará disponibilidade por funcionários/horários, revisão/confirmação de reserva, snapshots de condições e políticas de mudança. P03 ainda não bloqueia arquivo de pets por reservas futuras, pois reservas não existem; essa integração é requisito antes de entregar P04. Endereço/contato de loja real não foram fornecidos e não são inventados. Catálogo inicial de raças é limitado e ampliável por migration, sem editor operacional nesta etapa. Taxas, pagamento, deploy e migração histórica estão fora do escopo atual.
