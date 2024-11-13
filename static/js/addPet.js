function toggleMenu() {
    var menu = document.getElementById('menu-mobile');
    menu.classList.toggle('show');
}

document.getElementById('pet-cadastro-form').addEventListener('submit', function (e) {
    e.preventDefault();
    let isValid = true;

    // Limpar mensagens de erro
    document.querySelectorAll('.error').forEach(function (element) {
        element.textContent = '';
    });

    // Validação dos campos
    const nome = document.getElementById('nome').value.trim();
    const raca = document.getElementById('raca').value.trim();
    const porte = document.getElementById('porte').value.trim();
    const especie = document.getElementById('especie').value.trim();
    const idade = document.getElementById('idade').value.trim();

    if (nome === '') {
        document.getElementById('error-nome').textContent = 'Nome é obrigatório.';
        isValid = false;
    }

    if (raca === '') {
        document.getElementById('error-raca').textContent = 'Raça é obrigatória.';
        isValid = false;
    }

    if (especie === '') {
        document.getElementById('error-especie').textContent = 'Espécie é obrigatória.';
        isValid = false;
    }

    if (porte === '') {
        document.getElementById('error-porte').textContent = 'Porte é obrigatório.';
        isValid = false;
    }

    if (idade === '' || idade <= 0) {
        document.getElementById('error-idade').textContent = 'Idade deve ser um número positivo.';
        isValid = false;
    }

    if (isValid) {
        // Perguntar se o usuário tem certeza
        if (confirm('Você tem certeza de que os dados estão corretos?')) {
            alert('Pet cadastrado com sucesso!');

            // Limpar campos após o envio
            document.getElementById('nome').value = '';
            document.getElementById('raca').value = '';
            document.getElementById('porte').value = '';
            document.getElementById('especie').value = '';
            document.getElementById('idade').value = '';

            // Aqui você pode fazer o submit real ou enviar dados para o servidor
        }
    }

    
});
