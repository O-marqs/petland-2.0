document.getElementById('password-form').addEventListener('submit', function (e) {
            e.preventDefault();

            var novaSenha = document.getElementById('nova-senha').value;
            var confirmarSenha = document.getElementById('confirmar-senha').value;
            var errorMessage = '';

            // Validação da senha: pelo menos 8 caracteres, 1 número, 1 letra maiúscula
            var senhaRegex = /^(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$/;

            if (!senhaRegex.test(novaSenha)) {
                errorMessage = 'A senha deve ter no mínimo 8 caracteres, incluindo pelo menos 1 número e 1 letra maiúscula.';
            } else if (novaSenha !== confirmarSenha) {
                errorMessage = 'As senhas não coincidem!';
            }

            if (errorMessage) {
                document.getElementById('password-error').innerText = errorMessage;
            } else {
                document.getElementById('password-error').innerText = '';

                setTimeout(function () {
                    alert('Nova senha salva com sucesso!');
                }, 500);

                // Limpar os campos de senha após o envio
                document.getElementById('nova-senha').value = '';
                document.getElementById('confirmar-senha').value = '';
            }
        });