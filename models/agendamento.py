from config.database import create_connection, close_connection


class Agendamento:
    def __init__(self, id_agendamento=None, pet_id=None, nome_pet=None, servico_nome=None, pet_idPet=None, serviço_id=None, hora_agendamento=None, data_agendamento=None, colaboradores_cpf=None, servico_id=None):
        self.hora_agendamento = hora_agendamento
        self.data_agendamento = data_agendamento
        self.colaboradores_cpf = colaboradores_cpf
        self.servico_id = servico_id
        self.pet_id = pet_id
        self.nome_pet = nome_pet  # Inicializa com None
        self.servico_nome = servico_nome  # Inicializa com Non
        self.pet_idPet = pet_idPet  # Inicializa com Non
        self.serviço_id = serviço_id  # Inicializa com Non
        self.id_agendamento = id_agendamento  # Inicializa com Non

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

    def save(self):
        """
        Salva uma instância de Agendamento no banco de dados.
        """
        connection = create_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO agendamento (hora_agendamento, data_agendamento, colaboradores_cpf, servico_id, pet_id)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            self.hora_agendamento, self.data_agendamento,
            self.colaboradores_cpf, self.servico_id, self.pet_id
        )
        cursor.execute(query, values)
        connection.commit()

        close_connection(connection)
        return {"message": "Agendamento salvo com sucesso!"}

    def get_available_hours_from_db(date):
        connection = create_connection()
        cursor = connection.cursor()

        # Query para obter horários disponíveis
        query = """
        SELECT hora_agendamento FROM agendamento
        WHERE data_agendamento = %s
        """
        cursor.execute(query, (date,))
        agendamentos = cursor.fetchall()
        agendados = [agendamento[0] for agendamento in agendamentos]

        # Supondo que os horários disponíveis sejam das 8h às 17h
        horarios_totais = ["08:00", "09:00", "10:00", "11:00",
                           "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
        available_hours = [
            hora for hora in horarios_totais if hora not in agendados]

        close_connection(connection)
        return available_hours

    @classmethod
    def get_agendamentos_from_db(cls, colaboradores_cpf):
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT agendamento.id_agendamento,
                   agendamento.hora_agendamento as hora_agendamento, 
                   agendamento.data_agendamento as data_agendamento, 
                   servico.servico_nome as servico_nome,  
                   pet.nome_pet as nome_pet
            FROM agendamento
            JOIN servico ON agendamento.serviço_id = servico.id_servico
            JOIN pet ON agendamento.pet_idPet = pet.id_pet
            WHERE agendamento.colaboradores_cpf = %s AND agendamento.data_agendamento >= CURDATE()
        """

        cursor.execute(query, (colaboradores_cpf,))
        agendamentos = cursor.fetchall()
        close_connection(connection)

        return [cls(**agendamento) for agendamento in agendamentos]


class Servicos:

    def __init__(self, id_servico, servico_nome):
        self.id_servico = id_servico
        self.servico_nome = servico_nome

    @classmethod
    def get_services_from_db(cls):
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        query = """select id_servico, servico_nome from servico """
        cursor.execute(query)
        servicos = cursor.fetchall()
        close_connection(connection)
        return [cls(**servico) for servico in servicos]
