/**
 * @jest-environment jsdom
 */

const { validarEmail, mostrarMensagemErro, login } = require('./telalogin_cliente');

global.fetch = jest.fn();

describe('Função validarEmail', () => {
    test('Deve retornar true para um email válido', () => {
        expect(validarEmail('usuario@exemplo.com')).toBe(true);
    });

    test('Deve retornar false para um email inválido', () => {
        expect(validarEmail('usuario@exemplo')).toBe(false);
    });
});

describe('Função mostrarMensagemErro', () => {
    let errorMessageDiv;

    beforeEach(() => {
        document.body.innerHTML = '<div id="error-message" style="display: none;"></div>';
        errorMessageDiv = document.getElementById('error-message');
    });

    test('Deve exibir a mensagem de erro no elemento correto', () => {
        mostrarMensagemErro('Erro de teste');
        expect(errorMessageDiv.style.display).toBe('block');
        expect(errorMessageDiv.innerHTML).toBe('Erro de teste');
    });
});

describe('Função login', () => {
    let emailInput, senhaInput, errorMessageDiv;

    beforeEach(() => {
        document.body.innerHTML = `
            <input id="email" />
            <input id="senha" />
            <div id="error-message" style="display: none;"></div>
        `;
        emailInput = document.getElementById('email');
        senhaInput = document.getElementById('senha');
        errorMessageDiv = document.getElementById('error-message');
    });

    test('Deve exibir mensagem de erro se o email estiver vazio', async () => {
        emailInput.value = '';
        senhaInput.value = '123456';

        await login();

        expect(errorMessageDiv.style.display).toBe('block');
        expect(errorMessageDiv.innerHTML).toBe('Por favor, preencha o campo de email.');
    });

    test('Deve exibir mensagem de erro se a senha estiver vazia', async () => {
        emailInput.value = 'usuario@exemplo.com';
        senhaInput.value = '';

        await login();

        expect(errorMessageDiv.style.display).toBe('block');
        expect(errorMessageDiv.innerHTML).toBe('Por favor, preencha o campo de senha.');
    });

    test('Deve exibir mensagem de erro se o email for inválido', async () => {
        emailInput.value = 'usuario@exemplo';
        senhaInput.value = '123456';

        await login();

        expect(errorMessageDiv.style.display).toBe('block');
        expect(errorMessageDiv.innerHTML).toBe('Por favor, insira um email válido.');
    });

    test('Deve chamar fetch com os parâmetros corretos se email e senha forem válidos', async () => {
        fetch.mockResolvedValueOnce({
            redirected: false,
            json: async () => ({ message: 'Credenciais inválidas' })
        });

        emailInput.value = 'usuario@exemplo.com';
        senhaInput.value = '123456';

        await login();

        expect(fetch).toHaveBeenCalledWith('/api/cliente/login', expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ email: 'usuario@exemplo.com', senha: '123456' })
        }));
        expect(errorMessageDiv.innerHTML).toBe('Credenciais inválidas');
    });

    test('Deve redirecionar se a resposta for um redirecionamento', async () => {
        fetch.mockResolvedValueOnce({
            redirected: true,
            url: 'http://example.com/dashboard'
        });

        delete window.location;
        window.location = { href: '' };

        emailInput.value = 'usuario@exemplo.com';
        senhaInput.value = '123456';

        await login();

        expect(window.location.href).toBe('http://example.com/dashboard');
    });
});
