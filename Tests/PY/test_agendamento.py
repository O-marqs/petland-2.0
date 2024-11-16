# tests/test_agendamento.py
import unittest
from unittest.mock import patch, MagicMock
from agendamento import Agendamento

class TestAgendamento(unittest.TestCase):
    
    @patch('config.database.create_connection')  # Mocka create_connection
    @patch('config.database.close_connection')   # Mocka close_connection
    def test_criar_agendamento(self, mock_close_connection, mock_create_connection):
        # Mock para a conexão e o cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_create_connection.return_value = mock_connection

        # Dados de entrada simulados
        data = {
            'hora_agendamento': '14:00',
            'data_agendamento': '2024-11-09',
            'colaboradores_cpf': '12345678900',
            'servico_id': 1,
            'pet_id': 2
        }

        # Chama a função criar_agendamento
        resultado = Agendamento.criar_agendamento(data)

        # Verifica se o cursor executou a query
        mock_cursor.execute.assert_called_once_with(
            """
            INSERT INTO agendamento (hora_agendamento, data_agendamento, colaboradores_cpf, servico_id, pet_id)
            VALUES (%s, %s, %s, %s, %s)
            """, 
            ('14:00', '2024-11-09', '12345678900', 1, 2)
        )

        # Verifica se commit foi chamado
        mock_connection.commit.assert_called_once()

        # Verifica se a conexão foi fechada
        mock_close_connection.assert_called_once_with(mock_connection)

        # Verifica o resultado final
        self.assertEqual(resultado, {"message": "Agendamento criado com sucesso!"})

if __name__ == '__main__':
    unittest.main()
