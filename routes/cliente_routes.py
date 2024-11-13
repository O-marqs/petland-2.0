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
    return render_template('telainicialCliente.html')


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
        cliente = Cliente.cadastrar_cliente(data)
        if cliente:  # Se o login for bem-sucedido
            print("realizando login depois do cadastro")
            login_user(cliente)  # Armazena o cliente na sessão
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('cliente_bp.tela_inicial'))

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
