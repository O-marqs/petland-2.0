function validateForm(nome, email, cep, cpf, endereco, telefone, dataNascimento, senha) {
    const errors = {};

    // Validação do Nome
    if (!nome) errors.nome = 'Nome é obrigatório.';

    // Validação do Email
    if (!email) errors.email = 'Email é obrigatório.';
    else if (!/\S+@\S+\.\S+/.test(email)) errors.email = 'Email inválido.';

    // Validação do CEP
    if (!cep) errors.cep = 'CEP é obrigatório.';
    else if (!/^\d{8}$/.test(cep)) errors.cep = 'CEP inválido.';

    // Validação do CPF
    if (!cpf) errors.cpf = 'CPF é obrigatório.';
    else if (!/^\d{11}$/.test(cpf)) errors.cpf = 'CPF inválido.';

    // Validação do Endereço
    if (!endereco) errors.endereco = 'Endereço é obrigatório.';

    // Validação do Telefone
    if (!telefone) errors.telefone = 'Telefone é obrigatório.';
    else if (!/\(?\d{2}\)?\s?\d{4,5}-\d{4}/.test(telefone)) errors.telefone = 'Telefone inválido.';

    // Validação da Data de Nascimento
    if (!dataNascimento) errors.dataNascimento = 'Data de nascimento é obrigatória.';
    else {
        const birthDate = new Date(dataNascimento);
        const today = new Date();
        let age = today.getFullYear() - birthDate.getFullYear();
        const monthDifference = today.getMonth() - birthDate.getMonth();
        if (monthDifference < 0 || (monthDifference === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }
        if (age < 18 || age > 120) errors.dataNascimento = 'Idade deve ser entre 18 e 120 anos.';
    }

    // Validação da Senha
    if (!senha) errors.senha = 'Senha é obrigatória.';
    else if (!/^(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$/.test(senha)) errors.senha = 'Senha deve ter pelo menos 8 caracteres, incluindo uma letra maiúscula e um número.';

    return errors;
}

module.exports = validateForm;
