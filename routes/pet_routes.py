from flask import Blueprint, request, jsonify, redirect, url_for, flash, render_template
from models.pet import Pet, CatalogoPet
from models.agendamento import Agendamento, Servicos
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

pet_bp = Blueprint('pet_bp', __name__)


@pet_bp.route('/meus_pets')
@login_required
def meus_pets():
    pets = Pet.get_all_pets(current_user.cpf_cliente)
    return render_template('meuspets.html', pets=pets)


# A rota inclui um parâmetro pet_id
@pet_bp.route('/pet/perfil_pet/<int:id_pet>')
@login_required
def perfil_pet(id_pet):
    print(f"o pet é o n {id_pet}")
    # Busca o pet no banco usando o pet_id
    # Supondo que você tenha essa função na sua classe Pet
    pet = Pet.buscar_por_id(id_pet)
    if pet:
        print(pet)
        # Renderiza o template do perfil do pet
        return render_template('perfilPet.html', pet=pet)
    else:
        # Redireciona para uma página inicial ou de erro
        return redirect(url_for('cliente_bp.tela_inicial'))


@pet_bp.route('/pet/cadastrar', methods=['GET', 'POST'])
@login_required  # Garante que apenas usuários logados podem acessar
def cadastrar_pet():
    if request.method == 'POST':
        # Captura os dados do formulário
        nome_pet = request.form['nome_pet']
        idade_pet = request.form['idade_pet']
        genero_id = request.form['genero_id']
        raca_id = request.form['raca_id']
        observacao_pet = request.form.get(
            'observacao_pet', '')  # Campo opcional

        # Organiza os dados em um dicionário
        data = {
            'nome_pet': nome_pet,
            'idade_pet': idade_pet,
            'genero_id': genero_id,
            'animal_idanimal': raca_id,
            'observacao_pet': observacao_pet
        }
        print(data)
        # Chama a função para salvar o pet no banco
        response = Pet.cadastrar_pet(data, current_user.cpf_cliente)

        # Verifica se houve sucesso ou erro no cadastro e retorna a mensagem
        # Exibe a mensagem para o usuário
        flash(response['message'], 'success')

        # Redireciona após o cadastro
        return redirect(url_for('cliente_bp.tela_inicial'))

    # Se for GET, renderiza o formulário de cadastro
    return render_template('addPet.html')


@pet_bp.route('/pet/editar_pet', methods=['GET', 'POST'])
@login_required  # Garante que apenas usuários logados podem acessar
def editar_pet():
    print('entrou')
    data = request.get_json()  # Usando get_json() para obter dados JSON
    print(data)
    # Verifica se os dados necessários estão presentes
    if not all(key in data for key in ['nome', 'observacoes']):
        print("Por favor, preencha todos os campos obrigatórios. algum dado vazio no back", "danger")
        flash("Por favor, preencha todos os campos obrigatórios.", "danger")
        return redirect(url_for('pet_bp.meus_pets'))

    # Chama o método de atualização da classe Cliente
    try:
        # Adapte os nomes das chaves conforme o que você está enviando no JSON
        Pet.atualizar_pet(data['id_pet'], {
            'observacoes': data['observacoes'],
            'nome': data['nome']
        })
        flash("Cliente atualizado com sucesso!", "success")
        return jsonify({"redirect": url_for('pet_bp.meus_pets')}), 200
    except Exception as e:
        print(f"Ocorreu um erro ao atualizar o cliente: {e}, danger")
        flash("Ocorreu um erro ao atualizar o cliente: " + str(e), "danger")
        # Retorne um status 500
        return jsonify({"redirect": url_for('pet_bp.meus_pets')}), 500

    # Redireciona de volta para a tela de perfil do cliente
    return render_template('editar_cliente.html')


@pet_bp.route('/obter_especies', methods=['GET'])
@login_required
def obter_especies():
    especies = CatalogoPet.get_especies()
    return jsonify(especies)


@pet_bp.route('/racas', methods=['GET'])
@login_required
def obter_racas():
    especie_id = request.args.get('especie_id')
    if especie_id:
        racas = CatalogoPet.get_racas(especie_id)
        return jsonify(racas)
    return jsonify([])


@pet_bp.route('/obter_generos', methods=['GET'])
@login_required
def obter_generos():
    generos = CatalogoPet.get_generos()
    return jsonify(generos)


@pet_bp.route('/agendamento_pets')
@login_required
def agendamento_pets():
    pets = Pet.get_all_pets(current_user.cpf_cliente)
    servicos = Servicos.get_services_from_db()
    return render_template('telagendamento.html', pets=pets, servicos=servicos)
