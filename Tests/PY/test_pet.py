import unittest
from unittest.mock import patch, MagicMock
from your_module import Pet  # Substitua pelo nome do arquivo onde a classe Pet está definida

class TestPet(unittest.TestCase):

    @patch('your_module.create_connection')
    @patch('your_module.close_connection')
    def test_cadastrar_pet(self, mock_close_connection, mock_create_connection):
        # Configurando o mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_create_connection.return_value = mock_conn
        
        data = {
            'nome_pet': 'Bolt',
            'idade_pet': 5,
            'genero_id': 1,
            'animal_idanimal': 2,
            'observacao_pet': 'Muito enérgico'
        }
        cpf_cliente = '12345678900'

        response = Pet.cadastrar_pet(data, cpf_cliente)
        
        # Verificar se o comando SQL foi executado corretamente
        mock_cursor.execute.assert_called_once_with(
            """
            INSERT INTO pet (nome_pet, idade_pet, cliente_cpf1, genero_id, animal_idanimal, observacao_pet)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            ('Bolt', 5, '12345678900', 1, 2, 'Muito enérgico')
        )
        mock_conn.commit.assert_called_once()
        mock_close_connection.assert_called_once_with(mock_conn)
        self.assertEqual(response, {"message": "Pet cadastrado com sucesso!"})

    @patch('your_module.create_connection')
    @patch('your_module.close_connection')
    def test_get_all_pets(self, mock_close_connection, mock_create_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_create_connection.return_value = mock_conn

        mock_cursor.fetchall.return_value = [
            {
                'id_pet': 1,
                'nome_pet': 'Bolt',
                'idade_pet': 5,
                'tipo_pet': 'Cachorro',
                'cliente_cpf1': '12345678900',
                'genero_id': 1,
                'nome_genero': 'Macho',
                'animal_idanimal': 2,
                'observacao_pet': 'Muito enérgico'
            }
        ]

        pets = Pet.get_all_pets('12345678900')

        self.assertEqual(len(pets), 1)
        self.assertEqual(pets[0].nome_pet, 'Bolt')

    @patch('your_module.create_connection')
    @patch('your_module.close_connection')
    def test_buscar_por_id(self, mock_close_connection, mock_create_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_create_connection.return_value = mock_conn

        mock_cursor.fetchone.return_value = {
            'id_pet': 1,
            'nome_pet': 'Bolt',
            'idade_pet': 5,
            'tipo_pet': 'Cachorro',
            'cliente_cpf1': '12345678900',
            'genero_id': 1,
            'nome_genero': 'Macho',
            'animal_idanimal': 2,
            'observacao_pet': 'Muito enérgico'
        }

        pet = Pet.buscar_por_id(1)

        self.assertIsNotNone(pet)
        self.assertEqual(pet.nome_pet, 'Bolt')

    @patch('your_module.create_connection')
    @patch('your_module.close_connection')
    def test_atualizar_pet(self, mock_close_connection, mock_create_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_create_connection.return_value = mock_conn

        data = {'nome': 'Bolt', 'observacoes': 'Atualizado'}

        response = Pet.atualizar_pet(1, data)

        mock_cursor.execute.assert_called_once_with(
            """
            UPDATE pet
            SET nome_pet = %s, observacao_pet = %s
            WHERE id_pet = %s
            """,
            ('Bolt', 'Atualizado', 1)
        )
        mock_conn.commit.assert_called_once()
        self.assertEqual(response, {"message": "Cliente atualizado com sucesso!"})

if __name__ == '__main__':
    unittest.main()
