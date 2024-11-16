from flask import Flask
from routes.cliente_routes import cliente_bp
from routes.agendamento_routes import agendamento_bp
from flask_login import LoginManager
from models.cliente import Cliente
from models.colaborador import Funcionario
from routes.colaborador_routes import funcionario_bp
from routes.pet_routes import pet_bp
# from routes.servico_routes import servico_bp
# from routes.agendamento_routes import agendamento_bp

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'


# Instanciando o LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'cliente_bp.tela_login'  # Redireciona para a página de login se o usuário não estiver autenticado

@login_manager.user_loader
def load_user(user_id):
  # Tenta carregar primeiro o Cliente
    cliente = Cliente.buscar_cliente(user_id)
    if cliente:
        return cliente
    
    # Se não for um Cliente, tenta carregar um Funcionario
    funcionario = Funcionario.buscar_funcionario(user_id)
    if funcionario:
        return funcionario

    return None    



# Registrar as rotas
app.register_blueprint(cliente_bp, url_prefix='/api')
app.register_blueprint(funcionario_bp, url_prefix='/api')
app.register_blueprint(pet_bp, url_prefix='/api')
# app.register_blueprint(servico_bp, url_prefix='/api')
app.register_blueprint(agendamento_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)
