document.getElementById('cadastro-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Impede o envio do formulário até a validação ser realizada

    // Captura os valores dos campos
    var nome = document.getElementById('nome').value;
    var email = document.getElementById('email').value;
    var cep = document.getElementById('cep').value;
    var endereco = document.getElementById('endereco').value;
    var cpf = document.getElementById('cpf').value;
    var telefone = document.getElementById('telefone').value;
    var dataNascimento = document.getElementById('data-nascimento').value;
    var senha = document.getElementById('senha').value;
    var confirmarSenha = document.getElementById('confirmar-senha').value;

    // Variáveis de erro
    var valid = true;

    // Função para exibir mensagem de erro
    function showError(field, message) {
        document.getElementById(field + '-error').textContent = message;
        valid = false;
    }

    // Limpa mensagens de erro anteriores
    document.querySelectorAll('.error-message').forEach(function(el) {
        el.textContent = '';
    });

    // Aplicar formatação nos campos enquanto o usuário digita
    document.getElementById('cep').addEventListener('input', function() {
        this.value = formatCEP(this.value);
    });

    document.getElementById('cpf').addEventListener('input', function() {
        this.value = formatCPF(this.value);
    });

    document.getElementById('telefone').addEventListener('input', function() {
        this.value = formatTelefone(this.value);
    });

    // Funções de formatação (mantidas conforme solicitado)
    function formatCEP(cep) {
        cep = cep.replace(/\D/g, ''); // Remove caracteres não numéricos, incluindo "-"
        if (cep.length > 5) {
            cep = cep.replace(/^(\d{5})(\d{0,3})$/, "$1-$2"); // Aplica o formato
        }
        return cep;
    }

    function formatCPF(cpf) {
        cpf = cpf.replace(/\D/g, ''); // Remove caracteres não numéricos
        if (cpf.length > 9) {
            cpf = cpf.replace(/^(\d{3})(\d{3})(\d{3})(\d{0,2})$/, "$1.$2.$3-$4"); // Aplica o formato
        } else if (cpf.length > 6) {
            cpf = cpf.replace(/^(\d{3})(\d{3})(\d{0,3})$/, "$1.$2.$3"); // Aplica o formato parcial
        } else if (cpf.length > 3) {
            cpf = cpf.replace(/^(\d{3})(\d{0,3})$/, "$1.$2"); // Aplica o formato parcial
        }
        return cpf;
    }

    function formatTelefone(telefone) {
        telefone = telefone.replace(/\D/g, ''); // Remove caracteres não numéricos
        if (telefone.length > 6) {
            telefone = telefone.replace(/^(\d{2})(\d{5})(\d{0,4})$/, "($1)$2-$3"); // Aplica o formato
        } else if (telefone.length > 2) {
            telefone = telefone.replace(/^(\d{2})(\d{0,5})$/, "($1)$2"); // Aplica o formato parcial
        }
        return telefone;
    }

    // Validação de preenchimento de todos os campos
    if (nome === '') showError('nome', 'Preencha o campo Nome.');
    if (email === '') showError('email', 'Preencha o campo Email.');
    if (cep === '') showError('cep', 'Preencha o campo CEP.');
    if (endereco === '') showError('endereco', 'Preencha o campo Endereço.');
    if (cpf === '') showError('cpf', 'Preencha o campo CPF.');
    if (telefone === '') showError('telefone', 'Preencha o campo Telefone.');
    if (dataNascimento === '') showError('data-nascimento', 'Preencha o campo Data de Nascimento.');
    if (senha === '') showError('senha', 'Preencha o campo Senha.');
    if (confirmarSenha === '') showError('confirmar-senha', 'Preencha o campo Confirmar Senha.');

    // Validação de CPF (exatamente 11 caracteres, aceitando números e "X")
    cpf = cpf.replace(/[^0-9xX]/g, '').toUpperCase();
    if (cpf && !/^[0-9X]{11}$/.test(cpf)) {
        showError('cpf', 'O CPF deve conter exatamente 11 caracteres.');
    }

    // Validação de CEP (exatamente 8 números)
    cep = cep.replace(/\D/g, '');  // Remove qualquer caractere não numérico, incluindo o "-"
    if (cep && !/^\d{8}$/.test(cep)) {
        showError('cep', 'O CEP deve conter exatamente 8 números.');
    }

    // Validação de telefone (pelo menos 10 números)
    telefone = telefone.replace(/[^0-9]/g, ''); // Remove caracteres não numéricos
    if (telefone && telefone.length < 10) {
        showError('telefone', 'O telefone deve conter pelo menos 10 números.');
    }

    // Validação de senha (mínimo 8 caracteres, incluindo 1 letra maiúscula e 1 número)
    var senhaRegex = /^(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$/;
    if (senha && !senhaRegex.test(senha)) {
        showError('senha', 'A senha deve ter no mínimo 8 caracteres, incluindo pelo menos uma letra maiúscula e um número.');
    }

    // Verifica se as senhas coincidem
    if (senha !== confirmarSenha) {
        showError('confirmar-senha', 'As senhas não coincidem.');
    }

    // Validação de idade (18 a 120 anos)
    if (dataNascimento) {
        var birthDate = new Date(dataNascimento);
        var today = new Date();
        var age = today.getFullYear() - birthDate.getFullYear();
        var monthDifference = today.getMonth() - birthDate.getMonth();
        if (monthDifference < 0 || (monthDifference === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }
        if (age < 18 || age > 100) {
            showError('data-nascimento', 'A idade deve ser entre 18 e 120 anos.');
        }
    }
});