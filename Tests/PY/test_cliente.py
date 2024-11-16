import unittest
from unittest.mock import patch, MagicMock
from src.cliente import Cliente


class TestCliente(unittest.TestCase):
    @patch('src.cliente.create_connection')
    @patch('src.cliente.close_connection')
    def test_cadastrar_cliente(self, mock_close_connection, mock_create_connection):
        # Mockando o comportamento do banco
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # Simulando CPF não existente

        # Dados de teste
        cliente_data = {
            'cpf': '12345678900',
            'telefone': '999999999',
            'email': 'teste@example.com',
            'endereco': 'Rua Teste',
            'nome': 'Teste Nome',
            'senha': 'senha123'
        }

        result = Cliente.cadastrar_cliente(cliente_data)

        # Verificações
        mock_cursor.execute.assert_any_call(
            "SELECT cpf_cliente FROM cliente WHERE cpf_cliente = %s", (cliente_data['cpf'],))
        self.assertIsInstance(result, Cliente)
        mock_close_connection.assert_called_once_with(mock_conn)

    @patch('src.cliente.create_connection')
    @patch('src.cliente.close_connection')
    def test_login_cliente_sucesso(self, mock_close_connection, mock_create_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        cliente_db = {
            'cpf_cliente': '12345678900',
            'telefone_cliente': '999999999',
            'email_cliente': 'teste@example.com',
            'endereço_cliente': 'Rua Teste',
            'nome_cliente': 'Teste Nome',
            'senha_cliente': bcrypt.hashpw('senha123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        }
        mock_cursor.fetchone.return_value = cliente_db

        result = Cliente.login_cliente('teste@example.com', 'senha123')

        self.assertIsInstance(result, Cliente)
        self.assertEqual(result.email_cliente, cliente_db['email_cliente'])
        mock_close_connection.assert_called_once_with(mock_conn)

    @patch('src.cliente.create_connection')
    @patch('src.cliente.close_connection')
    def test_login_cliente_falha(self, mock_close_connection, mock_create_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None  # Simulando cliente não encontrado

        result = Cliente.login_cliente('teste@example.com', 'senha123')

        self.assertEqual(result, {"message": "Email ou senha inválidos"})
        mock_close_connection.assert_called_once_with(mock_conn)

    @patch('src.cliente.create_connection')
    @patch('src.cliente.close_connection')
    def test_deletar_cliente(self, mock_close_connection, mock_create_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_create_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        result = Cliente.deletar_cliente('12345678900')

        mock_cursor.execute.assert_called_once_with(
            "DELETE FROM cliente WHERE cpf_cliente = %s", ('12345678900',))
        self.assertEqual(result, {"message": "Cliente deletado com sucesso!"})
        mock_close_connection.assert_called_once_with(mock_conn)


if __name__ == '__main__':
    unittest.main()
