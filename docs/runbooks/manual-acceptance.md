# Testar uma conta nova e a operação local

Este roteiro usa a demonstração com dados fictícios em **https://localhost:8443**. Ela permite testar o produto completo no computador local. Não há envio para Gmail/Outlook ou outro provedor externo: as mensagens são recebidas na **[caixa de e-mails de teste](http://localhost:8026)**. A publicação e o provedor externo continuam adiados por D10.

## Cliente, começando do zero

1. Abra **[Criar conta](https://localhost:8443/criar-conta)**. Informe nome, e-mail e uma senha de pelo menos 15 caracteres. Na conclusão, siga os próximos passos apresentados.
2. Clique em **Abrir e-mails de teste**. Procure a mensagem de confirmação destinada ao endereço cadastrado. Abra o link e clique em **Confirmar e-mail**. Não é necessário usar a sua caixa pessoal.
3. Clique em **Continuar para minha área**, se já estiver conectado, ou **Ir para o login**. Se entrou antes de confirmar, abra **Minha conta** e use **Já confirmei meu e-mail**. A aplicação consulta a confirmação no servidor; confirmação pendente mantém pets/reservas bloqueados.
4. Na área inicial, use **Completar meu cadastro** e **Salvar cadastro**. Nome e e-mail vêm preenchidos; telefone e endereço são opcionais. A conta de acesso e o cadastro de contato são etapas distintas. Um cadastro assistido pela equipe exige o link de vínculo; o e-mail sozinho não associa cadastros existentes.
5. Abra **Meus pets**, use **Adicionar pet**, preencha nome, espécie e porte e clique em **Salvar pet**. Raça e nascimento podem ficar em branco. Recarregue para conferir que o pet foi salvo.
6. Em **Agendar um cuidado**, selecione pet e serviço. Escolha uma data futura e um horário disponível. Preço/duração dependem de serviço e porte; o cliente não escolhe profissional.
7. Confira o resumo e clique em **Sim, confirmar reserva**. O resumo ainda não cria uma reserva. Depois da confirmação, use **Ver minha reserva** e confira o aviso destinado ao seu endereço na caixa de teste.
8. Em **Minhas reservas**, teste reagendamento e cancelamento dentro do prazo informado no resumo. Confira o horário/status, o histórico e os novos e-mails de teste.

Se não houver horários, confira com o perfil de funcionário o expediente, a habilitação da pessoa para o serviço, as pausas/exceções e a antecedência. A demonstração tem configuração fictícia; o desenvolvimento vazio inicia com agenda desabilitada. Não remova dados para resolver falta de disponibilidade.

## Funcionário, em outra sessão

Use outro perfil/janela privada do navegador para manter cliente e funcionário conectados separadamente. As contas sintéticas geradas ficam no arquivo local ignorado `.local/staging/accounts.json`: `employee` para funcionário e `admin` para administrador. Não copie senhas para documentação pública.

1. Entre como funcionário e abra **Agenda** ou **Reservas**. Localize a reserva criada pelo seu cliente e confira pet, horário e serviço.
2. Antes do atendimento, teste **Reagendar** e **Cancelar reserva**, com motivo. A alteração aparece para o cliente e gera aviso na caixa de teste.
3. Para executar o atendimento, crie uma nova reserva para um horário próximo permitido pela configuração. No horário real, registre chegada, início e conclusão. Não mude o relógio do computador para antecipar o teste.
4. Registre uma anotação interna e um resumo visível ao cliente. Confira o histórico pelo perfil cliente: a anotação interna deve continuar privada.
5. Teste cadastro assistido, pets e serviços em suas telas. Alterações de calendário apresentam impacto antes de salvar; uma execução aberta pode impedir a mudança.

O administrador também pode testar acessos, convites, indicadores e auditoria. Convites e recuperação de senha chegam à mesma caixa local. Leitor de tela e aceite humano final continuam pendentes até serem efetivamente realizados.

## Verificação reproduzível de uma conta nova

Com o staging demo iniciado e o TLS já verificado pelo smoke:

```sh
python scripts/dev.py smoke-demo
node apps/web/scripts/onboarding-staging.mjs
```

O roteiro de onboarding cadastra uma conta sintética pela interface, testa a restrição antes da confirmação, confirma a mensagem SMTP real, salva contato e pet, reserva pela interface e verifica a mesma reserva no back office. A equipe reagenda e cancela essa reserva, preservando o histórico e conferindo os avisos. Não altera serviços/calendário existentes. Relatório e capturas em `.local/staging/browser/onboarding`; uma tentativa interrompida registra o ID da própria reserva em `attempt.json`, quando já criada. Ele recusa bancos fora do namespace demo e não aceita endereço externo.

Desenvolvimento usa **http://localhost:5173** e caixa **http://localhost:8025**. Não misture contas, links de confirmação ou caixas dos dois ambientes. O botão de caixa local só aparece nas origens locais suportadas; não expõe essa caixa em um domínio publicado.
