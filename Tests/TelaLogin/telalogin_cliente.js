// telalogin_cliente.js

function validarEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function mostrarMensagemErro(mensagem) {
    const errorMessageDiv = document.getElementById('error-message');
    errorMessageDiv.style.display = 'block';
    errorMessageDiv.innerHTML = mensagem;
}

async function login() {
    const email = document.getElementById('email').value.trim();
    const senha = document.getElementById('senha').value.trim();
    const errorMessageDiv = document.getElementById('error-message');

    errorMessageDiv.style.display = 'none';
    errorMessageDiv.innerHTML = '';

    if (!email) {
        mostrarMensagemErro('Por favor, preencha o campo de email.');
        return;
    }

    if (!senha) {
        mostrarMensagemErro('Por favor, preencha o campo de senha.');
        return;
    }

    if (!validarEmail(email)) {
        mostrarMensagemErro('Por favor, insira um email válido.');
        return;
    }

    try {
        const response = await fetch('/api/cliente/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, senha })
        });

        if (response.redirected) {
            window.location.href = response.url;
        } else {
            const result = await response.json();
            mostrarMensagemErro(result.message);
        }
    } catch (error) {
        mostrarMensagemErro('Erro ao tentar se comunicar com o servidor.');
    }
}

module.exports = { validarEmail, mostrarMensagemErro, login };
