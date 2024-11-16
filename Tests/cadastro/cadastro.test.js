const validateForm = require('./cadastro');

describe('Validação do Formulário de Cadastro de Cliente', () => {
    // Teste para Nome
    test('Deve retornar erro se o nome estiver vazio', () => {
        const errors = validateForm('', 'test@exemplo.com', '12345678', '12345678909', 'Rua Exemplo, 123', '(12) 34567-8901', '2000-01-01', 'Senha123');
        expect(errors.nome).toBe('Nome é obrigatório.');
    });

    // Teste para Email
    test('Deve retornar erro se o email estiver vazio ou inválido', () => {
        let errors = validateForm('Carlos Silva', '', '12345678', '12345678909', 'Rua Exemplo, 123', '(12) 34567-8901', '2000-01-01', 'Senha123');
        expect(errors.email).toBe('Email é obrigatório.');

        errors = validateForm('Carlos Silva', 'email-invalido', '12345678', '12345678909', 'Rua Exemplo, 123', '(12) 34567-8901', '2000-01-01', 'Senha123');
        expect(errors.email).toBe('Email inválido.');
    });

    // Teste para CEP
    test('Deve retornar erro se o CEP estiver vazio ou inválido', () => {
        let errors = validateForm('Carlos Silva', 'test@exemplo.com', '', '12345678909', 'Rua Exemplo, 123', '(12) 34567-8901', '2000-01-01', 'Senha123');
        expect(errors.cep).toBe('CEP é obrigatório.');

        errors = validateForm('Carlos Silva', 'test@exemplo.com', '12345', '12345678909', 'Rua Exemplo, 123', '(12) 34567-8901', '2000-01-01', 'Senha123');
        expect(errors.cep).toBe('CEP inválido.');
    });

    // Teste para CPF
    test('Deve retornar erro se o CPF estiver vazio ou inválido', () => {
        let errors = validateForm('Carlos Silva', 'test@exemplo.com', '12345678', '', 'Rua Exemplo, 123', '(12) 34567-8901', '2000-01-01', 'Senha123');
        expect(errors.cpf).toBe('CPF é obrigatório.');

        errors = validateForm('Carlos Silva', 'test@exemplo.com', '12345678', '123', 'Rua Exemplo, 123', '(12) 34567-8901', '2000-01-01', 'Senha123');
        expect(errors.cpf).toBe('CPF inválido.');
    });

    // Teste para Endereço
    test('Deve retornar erro se o endereço estiver vazio', () => {
        const errors = validateForm('Carlos Silva', 'test@exemplo.com', '12345678', '12345678909', '', '(12) 34567-8901', '2000-01-01', 'Senha123');
        expect(errors.endereco).toBe('Endereço é obrigatório.');
    });

    // Teste para Telefone
    test('Deve retornar erro se o telefone estiver vazio ou inválido', () => {
        let errors = validateForm('Carlos Silva', 'test@exemplo.com', '12345678', '12345678909', 'Rua Exemplo, 123', '', '2000-01-01', 'Senha123');
        expect(errors.telefone).toBe('Telefone é obrigatório.');

        errors = validateForm('Carlos Silva', 'test@exemplo.com', '12345678', '12345678909', 'Rua Exemplo, 123', '12345', '2000-01-01', 'Senha123');
        expect(errors.telefone).toBe('Telefone inválido.');
    });

    // Teste para Data de Nascimento
    test('Deve retornar erro se a data de nascimento estiver vazia ou inválida', () => {
        let errors = validateForm('Carlos Silva', 'test@exemplo.com', '12345678', '12345678909', 'Rua Exemplo, 123', '(12) 34567-8901', '', 'Senha123');
        expect(errors.dataNascimento).toBe('Data de nascimento é obrigatória.');

        errors = validateForm('Carlos Silva', 'test@exemplo.com', '12345678', '12345678909', 'Rua Exemplo, 123', '(12) 34567-8901', '2010-01-01', 'Senha123');
        expect(errors.dataNascimento).toBe('Idade deve ser entre 18 e 120 anos.');
    });

    // Teste para Senha
    test('Deve retornar erro se a senha estiver vazia ou inválida', () => {
        let errors = validateForm('Carlos Silva', 'test@exemplo.com', '12345678', '12345678909', 'Rua Exemplo, 123', '(12) 34567-8901', '2000-01-01', '');
        expect(errors.senha).toBe('Senha é obrigatória.');

        errors = validateForm('Carlos Silva', 'test@exemplo.com', '12345678', '12345678909', 'Rua Exemplo, 123', '(12) 34567-8901', '2000-01-01', 'senha');
        expect(errors.senha).toBe('Senha deve ter pelo menos 8 caracteres, incluindo uma letra maiúscula e um número.');
    });

    // Teste para todos os campos válidos
    test('Deve passar se todos os campos forem válidos', () => {
        const errors = validateForm('Carlos Silva', 'test@exemplo.com', '12345678', '12345678909', 'Rua Exemplo, 123', '(12) 34567-8901', '2000-01-01', 'Senha123');
        expect(errors).toEqual({});
    });
});
