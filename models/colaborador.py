from config.database import create_connection, close_connection
import bcrypt

class Colaborador:
    def __init__(self, cpf_colaborador, nome_colaborador, senha_backoffice, email_colaborador, acesso_id):
        self.cpf_colaborador = cpf_colaborador
        self.nome_colaborador = nome_colaborador
        self.senha_backoffice = senha_backoffice
        self.email_colaborador = email_colaborador
        self.acesso_id = acesso_id

    @staticmethod
    def cadastrar_colaborador(data):
        connection = create_connection()
        cursor = connection.cursor()

        hashed_senha = bcrypt.hashpw(data['senha_backoffice'].encode('utf-8'), bcrypt.gensalt())

        query = """
        INSERT INTO colaboradores (cpf_colaborador, nome_colaborador, senha_backoffice, email_colaborador, acesso_id)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            data['cpf_colaborador'], data['nome_colaborador'], hashed_senha, 
            data['email_colaborador'], data['acesso_id']
        )
        cursor.execute(query, values)
        connection.commit()
        close_connection(connection)
        return {"message": "Colaborador cadastrado com sucesso!"}

    @staticmethod
    def login_colaborador(email, senha):
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM colaboradores WHERE email_colaborador = %s"
        cursor.execute(query, (email,))
        colaborador = cursor.fetchone()

        close_connection(connection)

        if colaborador and bcrypt.checkpw(senha.encode('utf-8'), colaborador['senha_backoffice'].encode('utf-8')):
            return {"message": "Login bem-sucedido!", "colaborador": colaborador}
        else:
            return {"message": "Email ou senha inválidos"}
