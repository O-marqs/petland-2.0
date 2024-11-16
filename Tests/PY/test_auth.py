import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify
from src.auth import auth, gerar_token, verificar_token

# Criar uma aplicação Flask para testes
app = Flask(__name__)
app.register_blueprint(auth)

class TestAuthBlueprint(unittest.TestCase):

    @patch('src.auth.get_db_connection')
    def test_login_cliente_sucesso(self, mock_get_db_connection):
        # Mock da conexão e cursor do banco de dados
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simular cliente no banco de dados
        mock_cursor.fetchone.side_effect = [
            {'cpf_cliente': '12345678900', 'senha_cliente': 'hashed_password'},
            None  # Não há colaborador com esse CPF
        ]

        # Mock da função check_password_hash
        with patch('src.auth.check_password_hash', return_value=True):
            with app.test_client() as client:
                response = client.post('/api/login', json={
                    'cpf': '12345678900',
                    'senha': 'senha_correta'
                })

                self.assertEqual(response.status_code, 200)
                self.assertIn('token', response.json)

    @patch('src.auth.get_db_connection')
    def test_login_colaborador_sucesso(self, mock_get_db_connection):
        # Mock da conexão e cursor do banco de dados
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simular colaborador no banco de dados
        mock_cursor.fetchone.side_effect = [
            None,  # Não há cliente com esse CPF
            {'cpf_colaborador': '98765432100', 'senha_backOffice': 'senha_correta'}
        ]

        with app.test_client() as client:
            response = client.post('/api/login', json={
                'cpf': '98765432100',
                'senha': 'senha_correta'
            })

            self.assertEqual(response.status_code, 200)
            self.assertIn('token', response.json)

    @patch('src.auth.get_db_connection')
    def test_login_usuario_nao_encontrado(self, mock_get_db_connection):
        # Mock da conexão e cursor do banco de dados
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simular nenhum cliente ou colaborador encontrado
        mock_cursor.fetchone.side_effect = [None, None]

        with app.test_client() as client:
            response = client.post('/api/login', json={
                'cpf': '00000000000',
                'senha': 'senha_errada'
            })

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json['message'], "CPF não encontrado")

    def test_gerar_e_verificar_token(self):
        # Gerar e verificar token
        token = gerar_token('12345678900', 'cliente')
        dados = verificar_token(token)

        self.assertIsNotNone(dados)
        self.assertEqual(dados['cpf'], '12345678900')
        self.assertEqual(dados['tipo_usuario'], 'cliente')

    def test_verificar_token_invalido(self):
        # Teste com token inválido
        token = "token_invalido"

        dados = verificar_token(token)
        self.assertIsNone(dados)

    @patch('src.auth.verificar_token', return_value={'cpf': '12345678900', 'tipo_usuario': 'cliente'})
    def test_rota_protegida_sucesso(self, mock_verificar_token):
        with app.test_client() as client:
            response = client.get('/api/protegido', headers={'Authorization': 'Bearer token_falso'})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['cpf'], '12345678900')

    @patch('src.auth.verificar_token', return_value=None)
    def test_rota_protegida_token_invalido(self, mock_verificar_token):
        with app.test_client() as client:
            response = client.get('/api/protegido', headers={'Authorization': 'Bearer token_invalido'})

            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json['message'], "Token inválido")

if __name__ == '__main__':
    unittest.main()
