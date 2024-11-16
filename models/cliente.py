from config.database import create_connection, close_connection
from flask_login import UserMixin
import bcrypt


class Cliente(UserMixin):
    def __init__(self, cpf_cliente, telefone_cliente, email_cliente, endereco_cliente, nome_cliente, senha_cliente, active=True):
        self.cpf_cliente = cpf_cliente
        self.telefone_cliente = telefone_cliente
        self.email_cliente = email_cliente
        self.endereco_cliente = endereco_cliente
        self.nome_cliente = nome_cliente
        self.senha_cliente = senha_cliente
        self.active = active

    def is_active(self):
        return self.active

    def get_id(self):
        return self.cpf_cliente  # Retorna o CPF como

    @staticmethod
    def cadastrar_cliente(data):
        connection = create_connection()
        cursor = connection.cursor()
        # Verifica se o CPF já está cadastrado
        print('Puxou o cursor')
        try:
            cursor.execute(
                "SELECT cpf_cliente FROM cliente WHERE cpf_cliente = %s", (data['cpf'],))
            print('Realizou o select')
            if cursor.fetchone() is not None:
                return {"message": "Cliente já cadastrado. Redirecionando para a tela de login."}, 409
        except Exception as e:
            print(f"Erro ao buscar se pessoa está cadastrada: {e}")
        try:
            hashed_senha = bcrypt.hashpw(
                data['senha'].encode('utf-8'), bcrypt.gensalt())
            print('Criou hash da senha')

            query = """
            INSERT INTO cliente (cpf_cliente, telefone_cliente, email_cliente, endereço_cliente, nome_cliente, senha_cliente)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (
                data['cpf'], data['telefone'], data['email'],
                data['endereco'], data['nome'], hashed_senha
            )
            cursor.execute(query, values)
            print('Realizou insert do cliente novo')
            connection.commit()
            print("Cliente cadastrado com sucesso.")  # Confirmação final
            return Cliente(
                cpf_cliente=data['cpf'],
                telefone_cliente=data['telefone'],
                email_cliente=data['email'],
                endereco_cliente=data['endereco'],
                nome_cliente=data['nome'],
                # A senha não deve ser exposta
                senha_cliente=hashed_senha,
                active=True
            )

        except Exception as e:
            print(f"Erro ao cadastrar cliente: {e}")
            return {"message": "Erro ao cadastrar cliente. Contate o suporte.", "status_code": 500}
        finally:
            close_connection(connection)
            print("Conexão fechada.")  # Confirma fechamento

    @staticmethod
    def login_cliente(email, senha):
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM cliente WHERE email_cliente = %s", (email,))
        cliente = cursor.fetchone()
        close_connection(connection)
        if cliente and bcrypt.checkpw(senha.encode('utf-8'), cliente['senha_cliente'].encode('utf-8')):
            return Cliente(
                cpf_cliente=cliente['cpf_cliente'],
                telefone_cliente=cliente['telefone_cliente'],
                email_cliente=cliente['email_cliente'],
                endereco_cliente=cliente['endereço_cliente'],
                nome_cliente=cliente['nome_cliente'],
                # A senha não deve ser exposta; pode ser omitida
                senha_cliente=cliente['senha_cliente'],
                active=True
            )
        else:
            return {"message": "Email ou senha inválidos"}

    @staticmethod
    def buscar_cliente(cpf_cliente):
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM cliente WHERE cpf_cliente = %s"
        cursor.execute(query, (cpf_cliente,))
        cliente = cursor.fetchone()

        close_connection(connection)
        if cliente:
            return Cliente(
                cpf_cliente=cliente['cpf_cliente'],
                telefone_cliente=cliente['telefone_cliente'],
                email_cliente=cliente['email_cliente'],
                endereco_cliente=cliente['endereço_cliente'],
                nome_cliente=cliente['nome_cliente'],
                # A senha não deve ser exposta
                senha_cliente=cliente['senha_cliente'],
                active=True
            )
        return None  # Se não encontrar, retorna None

    @staticmethod
    def atualizar_cliente(cpf_cliente, data):
        connection = create_connection()
        cursor = connection.cursor()

        query = """
        UPDATE cliente
        SET telefone_cliente = %s, endereço_cliente = %s, nome_cliente = %s
        WHERE cpf_cliente = %s
        """
        values = (
            data['telefone_cliente'],
            data['endereco_cliente'], data['nome_cliente'], cpf_cliente
        )
        cursor.execute(query, values)
        connection.commit()

        close_connection(connection)
        return {"message": "Cliente atualizado com sucesso!"}

    @staticmethod
    def deletar_cliente(cpf_cliente):
        connection = create_connection()
        cursor = connection.cursor()

        query = "DELETE FROM cliente WHERE cpf_cliente = %s"
        cursor.execute(query, (cpf_cliente,))
        connection.commit()

        close_connection(connection)
        return {"message": "Cliente deletado com sucesso!"}
