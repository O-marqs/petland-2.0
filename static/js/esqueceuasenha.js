document.getElementById('recovery-form').addEventListener('submit', function (e) {
            e.preventDefault(); // Impede o envio do formulário para testar a funcionalidade

            var email = document.getElementById('email-recuperacao').value;
            var emailError = document.getElementById('email-error');
            var valid = true;

            // Validação do email
            var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!email) {
                emailError.textContent = 'Por favor, insira um email para recuperação.';
                valid = false;
            } else if (!emailPattern.test(email)) {
                emailError.textContent = 'Por favor, insira um email válido.';
                valid = false;
            } else {
                emailError.textContent = '';
            }

            // Impede o envio do formulário se as validações falharem
            if (!valid) {
                return;
            }

            // Simula o envio de um email de recuperação
            setTimeout(function () {
                alert('Email de recuperação enviado!');
                document.getElementById('resend-button').style.display = 'block';

                // Limpa o campo de email após o envio
                document.getElementById('email-recuperacao').value = '';
            }, 500); // Espera 500ms para simular a operação de envio de email
        });

        document.getElementById('resend-button').addEventListener('click', function () {
            alert('Email de recuperação enviado novamente!');
        });