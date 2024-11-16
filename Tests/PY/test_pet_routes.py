import pytest
from flask import Flask, session
from app.routes.pet_bp import pet_bp
from app.models.pet import Pet
from unittest.mock import patch
from flask_login import LoginManager, UserMixin, login_user


# Configura um usuário de teste
class MockUser(UserMixin):
    def __init__(self, cpf_cliente):
        self.cpf_cliente = cpf_cliente


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test_secret"
    app.register_blueprint(pet_bp)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(cpf_cliente):
        return MockUser(cpf_cliente)

    return app


@pytest.fixture
def client(app):
    return app.test_client()


# Mockando o login
@pytest.fixture
def login(client):
    with client.session_transaction() as session:
        session['_user_id'] = '12345678900'  # CPF do cliente fictício
    yield client


# Testando a rota de 'meus_pets'
@patch('app.models.pet.Pet.get_all_pets')
def test_meus_pets(mock_get_all_pets, login):
    mock_get_all_pets.return_value = []
    response = login.get('/meus_pets')
    assert response.status_code == 200
    assert b'Seus Pets' in response.data  # Verifique algo específico do template


# Testando a rota de perfil do pet
@patch('app.models.pet.Pet.buscar_por_id')
def test_perfil_pet(mock_buscar_por_id, login):
    mock_buscar_por_id.return_value = Pet(
        id_pet=1,
        nome_pet="Rex",
        idade_pet=3,
        cliente_cpf1='12345678900',
        genero_id=1,
        animal_idanimal=2,
        observacao_pet="Nada relevante",
        tipo_pet="Cachorro",
        nome_genero="Macho"
    )
    response = login.get('/pet/perfil_pet/1')
    assert response.status_code == 200
    assert b"Rex" in response.data


# Testando o cadastro de pet
@patch('app.models.pet.Pet.cadastrar_pet')
def test_cadastrar_pet(mock_cadastrar_pet, login):
    response = login.post('/pet/cadastrar', data={
        'nome_pet': 'Buddy',
        'idade_pet': '2',
        'tipo_pet': 'Cachorro'
    })
    assert response.status_code == 302  # Redirecionamento
    mock_cadastrar_pet.assert_called_once()


# Testando a edição do pet
@patch('app.models.pet.Pet.atualizar_pet')
def test_editar_pet(mock_atualizar_pet, login):
    data = {
        'id_pet': 1,
        'nome': 'Buddy Atualizado',
        'observacoes': 'Novo comentário'
    }
    response = login.post('/pet/editar_pet', json=data)
    assert response.status_code == 200
    mock_atualizar_pet.assert_called_once_with(data['id_pet'], {
        'nome': data['nome'],
        'observacoes': data['observacoes']
    })


# Testando a rota para obter espécies
@patch('app.routes.pet_bp.Especie.query.all')
def test_get_especies(mock_query, client):
    mock_query.return_value = [
        {'id': 1, 'nome': 'Cachorro'},
        {'id': 2, 'nome': 'Gato'}
    ]
    response = client.get('/especies')
    assert response.status_code == 200
    assert b'Cachorro' in response.data
