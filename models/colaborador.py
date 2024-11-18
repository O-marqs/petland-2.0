from flask_login import UserMixin
from config.database import create_connection, close_connection


class Funcionario(UserMixin):
    def __init__(self, id_agendamento=None, nome_pet=None, data_agendamento=None, servico_nome=None, hora_agendamento=None, acesso_id=None, nome_colaborador=None, email_colaborador=None, senha_backOffice=None, cpf_colaborador=None, active=True):
        self.acesso_id = acesso_id
        self.nome_colaborador = nome_colaborador
        self.email_colaborador = email_colaborador
        self.senha_backOffice = senha_backOffice
        self.cpf_colaborador = cpf_colaborador
        self.id_agendamento = id_agendamento
        self.nome_pet = nome_pet
        self.servico_nome = servico_nome
        self.data_agendamento = data_agendamento
        self.hora_agendamento = hora_agendamento
        self.active = active

    def is_active(self):
        return self.active

    def get_id(self):
        return self.cpf_colaborador  # Retorna o CPF como

    @staticmethod
    def buscar_funcionario(user_id):
        # Consulta no banco para encontrar o funcionário com base no ID
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM funcionario WHERE cpf_colaborador = %s", (user_id,))
        row = cursor.fetchone()
        close_connection(connection)

        if row:
            return Funcionario(*row)
        return None

    @staticmethod
    def login_funcionario(email, senha):
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM colaboradores WHERE email_colaborador = %s AND senha_backOffice = %s", (email, senha))
        row = cursor.fetchone()
        print(row)
        close_connection(connection)

        if row:
            return Funcionario(
                cpf_colaborador=row['cpf_colaborador'],
                nome_colaborador=row['nome_colaborador'],
                email_colaborador=row['email_colaborador'],
                active=True
            )
        return None

    @staticmethod
    def buscar_agendamentos_por_data(data):
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT ag.id_agendamento as id_agendamento, p.nome_pet as nome_pet, s.servico_nome as servico_nome, ag.data_agendamento as data_agendamento, ag.hora_agendamento as hora_agendamento
            FROM agendamento ag
            JOIN pet p ON ag.pet_idPet = p.id_pet
            JOIN servico s ON ag.serviço_id = s.id_servico
            WHERE ag.data_agendamento = %s
        """
        cursor.execute(query, (data,))
        agendamentos = cursor.fetchall()
        close_connection(connection)
        return agendamentos
