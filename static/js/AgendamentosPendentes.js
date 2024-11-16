 // Função para carregar agendamentos dinamicamente
        function loadAgendamentos() {
            fetch('http://localhost:3001/api/agendamentos')
                .then(response => response.json())
                .then(data => {
                    const tableBody = document.getElementById('agendamentosTableBody');
                    tableBody.innerHTML = ''; // Limpa a tabela antes de carregar novos dados

                    data.forEach(agendamento => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${agendamento.pet}</td>
                            <td>${agendamento.data}</td>
                            <td>${agendamento.horario}</td>
                            <td>${agendamento.servico}</td>
                            <td>${agendamento.subservico || 'N/A'}</td>
                            <td>
                                <button class="edit-btn">Editar</button>
                                <button class="delete-btn" onclick="confirmDelete(${agendamento.id})">Excluir</button>
                            </td>
                        `;
                        tableBody.appendChild(row);
                    });
                })
                .catch(error => console.error('Erro ao carregar agendamentos:', error));
        }

        // Função para exibir a confirmação de exclusão
        function confirmDelete(id) {
            const confirmed = confirm("Tem certeza que deseja deletar este agendamento?");
            if (confirmed) {
                deleteAgendamento(id); // Se confirmado, chama a função para deletar
            }
        }

        // Função para deletar agendamento
        function deleteAgendamento(id) {
            fetch(`http://localhost:3001/api/agendamentos/${id}`, {
                method: 'DELETE',
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message); // Exibe mensagem de sucesso
                loadAgendamentos(); // Recarrega a lista de agendamentos
            })
            .catch(error => console.error('Erro ao deletar agendamento:', error));
        }

        // Carregar agendamentos ao carregar a página
        document.addEventListener('DOMContentLoaded', loadAgendamentos);

        function toggleMenu() {
            const menu = document.getElementById('menu');
            menu.classList.toggle('show');
        }
        
        // Fechar o menu se o usuário clicar fora dele
        document.addEventListener('click', function(event) {
            const menu = document.getElementById('menu');
            const menuHamburguer = document.querySelector('.menu-hamburguer');
        
            // Verifica se o clique foi fora do menu e do ícone de hambúrguer
            if (!menu.contains(event.target) && !menuHamburguer.contains(event.target)) {
                menu.classList.remove('show'); // Fecha o menu
            }
        });