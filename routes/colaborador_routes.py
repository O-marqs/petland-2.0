from flask import Blueprint, request, jsonify, redirect, url_for, flash, render_template
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models.colaborador import Funcionario  # Importe a classe Funcionario

funcionario_bp = Blueprint('funcionario_bp', __name__)

login_manager = LoginManager()
login_manager.login_view = 'funcionario_bp.login'  # Rota de login

# Função para carregar o funcionário


@login_manager.user_loader
def load_user(user_id):
    return Funcionario.buscar_funcionario(user_id)

# Rota de logout


@funcionario_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('funcionario_bp.tela_login'))

# Rota de login (formulário)


@funcionario_bp.route('/telalogin_funcionario')
def tela_login():
    return render_template('telalogin_funcionario.html')

# Rota inicial após login

# Rota de login (POST)


@funcionario_bp.route('/funcionario/login', methods=['POST'])
def login_funcionario():
    try:
        if request.method == 'POST':
            data = request.get_json()
            email = data.get('email')
            senha = data.get('senha')

            funcionario = Funcionario.login_funcionario(email, senha)
            if funcionario:  # Se o login for bem-sucedido
                login_user(funcionario)  # Armazena o funcionário na sessão
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('funcionario_bp.meus_agendamentos'))
            else:
                print("Não achou funcionário")
                # Adiciona a mensagem para ser exibida na tela de login
                flash('Credenciais inválidas!')
                return redirect(url_for('funcionario_bp.tela_login'))
        return redirect(url_for('funcionario_bp.tela_login'))
    except Exception as e:
        print(f"Erro {e} ao realizar login. Contate o suporte.")
        flash("Erro ao realizar login. Contate o suporte.")  # Mensagem de erro
        return redirect(url_for('funcionario_bp.tela_login'))


@funcionario_bp.route('/meus_agendamentos', methods=['GET', 'POST'])
@login_required
def meus_agendamentos():
    agendamentos = []
    if request.method == 'POST':
        data = request.form.get('data_agendamento')
        agendamentos = Funcionario.buscar_agendamentos_por_data(data)

    return render_template('agendamentos_funcionario.html', agendamentos=agendamentos)
