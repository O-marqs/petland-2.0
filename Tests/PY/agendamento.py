from config.database import create_connection, close_connection

class Agendamento:
    def __init__(self, hora_agendamento, data_agendamento, colaboradores_cpf, servico_id, pet_id):
        self.hora_agendamento = hora_agendamento
        self.data_agendamento = data_agendamento
        self.colaboradores_cpf = colaboradores_cpf
        self.servico_id = servico_id
        self.pet_id = pet_id

    @staticmethod
    def criar_agendamento(data):
        connection = create_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO agendamento (hora_agendamento, data_agendamento, colaboradores_cpf, servico_id, pet_id)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            data['hora_agendamento'], data['data_agendamento'], 
            data['colaboradores_cpf'], data['servico_id'], data['pet_id']
        )
        cursor.execute(query, values)
        connection.commit()

        close_connection(connection)
        return {"message": "Agendamento criado com sucesso!"}
