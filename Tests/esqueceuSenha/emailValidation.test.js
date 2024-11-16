const { validateEmail, sendRecoveryEmail } = require('./emailValidation');

describe('Validação de Email', () => {
    test('Deve retornar erro se o email estiver vazio', () => {
        expect(validateEmail('')).toBe('Por favor, insira um email para recuperação.');
    });

    test('Deve retornar erro se o email for inválido', () => {
        expect(validateEmail('email_invalido')).toBe('Por favor, insira um email válido.');
    });

    test('Deve passar se o email for válido', () => {
        expect(validateEmail('test@example.com')).toBe('');
    });
});

describe('Envio de Email de Recuperação', () => {
    jest.useFakeTimers();

    test('Deve simular envio de email com callback', () => {
        const mockCallback = jest.fn();
        sendRecoveryEmail(mockCallback);

        jest.runAllTimers(); // Simula tempo
        expect(mockCallback).toHaveBeenCalledTimes(1);
    });
});

// Mock DOM dentro de um teste (exemplo de simulação com jsdom)
describe('Mock de DOM', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <form id="recovery-form">
                <input id="email-recuperacao" />
                <span id="email-error"></span>
            </form>
        `;
    });

    test('Simular preenchimento e verificação do DOM', () => {
        const emailInput = document.getElementById('email-recuperacao');
        const emailError = document.getElementById('email-error');

        emailInput.value = 'teste@exemplo.com';
        expect(emailError.textContent).toBe('');
    });
});
