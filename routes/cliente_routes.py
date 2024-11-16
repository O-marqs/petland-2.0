from flask import Blueprint, request, jsonify, redirect, url_for, flash, render_template
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models.cliente import Cliente

cliente_bp = Blueprint('cliente_bp', __name__)


login_manager = LoginManager()
login_manager.login_view = 'cliente_bp.login'  # Rota de login

# Função para carregar o usuário


@login_manager.user_loader
def load_user(user_id):
    # Certifique-se de que esta função existe
    return Cliente.buscar_cliente(user_id)


@cliente_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('cliente_bp.tela_login'))


@cliente_bp.route('/tela_login')
def tela_login():
    return render_template('telalogin_cliente.html')


@cliente_bp.route('/tela_cadastro')
def tela_cadastro():
    return render_template('telacadastro_cliente.html')


@cliente_bp.route('/tela_inicial')
@login_required
def tela_inicial():
    print(
        f'Bem-vindo, {current_user.nome_cliente}! Você está na página principal.')
    return render_template('telainicial.html')


@cliente_bp.route('/cliente/login', methods=['POST'])
def login_cliente():
    try:
        if request.method == 'POST':
            data = request.get_json()
            email = data.get('email')
            senha = data.get('senha')

            cliente = Cliente.login_cliente(email, senha)
            if cliente:  # Se o login for bem-sucedido
                login_user(cliente)  # Armazena o cliente na sessão
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('cliente_bp.tela_inicial'))
            else:
                print("Não achou cliente")
                # Adiciona a mensagem para ser exibida na tela de login
                flash(cliente['message'])
                # Redireciona para a tela de login
                return redirect(url_for('cliente_bp.tela_login'))
        return redirect(url_for('cliente_bp.tela_login'))
    except Exception as e:
        print(f"Erro {e} ao cadastrar cliente. Contate o suporte.")
        flash("Erro ao cadastrar cliente. Contate o suporte.")  # Mensagem de erro
        # Redireciona para a tela de login
        return redirect(url_for('cliente_bp.tela_login'))


@cliente_bp.route('/cliente/cadastrar_cliente', methods=['POST'])
def cadastrar_cliente():

    try:
        data = request.get_json()
        print('pegou os dados do front')
        cliente = Cliente.cadastrar_cliente(data)
        print('cliente criado')
        if cliente:  # Se o login for bem-sucedido
            print("realizando login depois do cadastro")
            login_user(cliente)  # Armazena o cliente na sessão
            flash('Login realizado com sucesso!', 'success')
            print('Login realizado com sucesso!', 'success')
            return redirect(url_for('pet_bp.cadastrar_pet'))

        else:
            # Adiciona a mensagem para ser exibida na tela de login
            flash("Ocorreu algum erro no cadastro")
            print("Ocorreu algum erro no cadastro")
            # Redireciona para a tela de login
            return redirect(url_for('cliente_bp.tela_login'))
    except Exception as e:
        flash("Erro ao cadastrar cliente. Contate o suporte.")  # Mensagem de erro
        # Redireciona para a tela de login
        print(f"Erro {e} ao cadastrar cliente. Contate o suporte.")

        return redirect(url_for('cliente_bp.tela_login'))


@cliente_bp.route('/cliente/<cpf_cliente>', methods=['GET'])
def buscar_cliente(cpf_cliente):
    cliente = Cliente.buscar_cliente(cpf_cliente)
    return jsonify(cliente)


@cliente_bp.route('/cliente/perfil')
@login_required  # Garante que apenas usuários logados podem acessar
def perfil_cliente():
    # Busca o cliente atual no banco usando o ID do current_user
    # Supondo que há uma função `buscar_por_id`
    cliente = Cliente.buscar_cliente(current_user.cpf_cliente)
    print(current_user.cpf_cliente)
    if cliente:
        return render_template('alterarPerfil.html', cliente=cliente)
    else:
        return redirect(url_for('cliente_bp.tela_inicial'))


@cliente_bp.route('/cliente/editar_cliente', methods=['GET', 'POST'])
@login_required  # Garante que apenas usuários logados podem acessar
def editar_cliente():

    data = request.get_json()  # Usando get_json() para obter dados JSON
    print(data)
    # Verifica se os dados necessários estão presentes
    if not all(key in data for key in ['nome', 'endereco', 'telefone']):
        print("Por favor, preencha todos os campos obrigatórios. algum dado vazio no back", "danger")
        flash("Por favor, preencha todos os campos obrigatórios.", "danger")
        return redirect(url_for('cliente_bp.perfil_cliente'))

    # Chama o método de atualização da classe Cliente
    try:
        # Supondo que o CPF do cliente está no objeto do usuário logado
        cpf_cliente = current_user.cpf_cliente
        # Adapte os nomes das chaves conforme o que você está enviando no JSON
        Cliente.atualizar_cliente(cpf_cliente, {
            'telefone_cliente': data['telefone'],
            'endereco_cliente': data['endereco'],
            'nome_cliente': data['nome']
        })
        flash("Cliente atualizado com sucesso!", "success")
        return jsonify({"redirect": url_for('cliente_bp.tela_inicial')}), 200
    except Exception as e:
        print(f"Ocorreu um erro ao atualizar o cliente: {e}, danger")
        flash("Ocorreu um erro ao atualizar o cliente: " + str(e), "danger")
        # Retorne um status 500
        return jsonify({"redirect": url_for('cliente_bp.perfil_cliente')}), 500

    # Redireciona de volta para a tela de perfil do cliente
    return render_template('editar_cliente.html')
