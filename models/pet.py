from config.database import create_connection, close_connection

class Pet:
    def __init__(self, nome_pet, idade_pet, cliente_cpf, genero_id, animal_idanimal, observacao_pet):
        self.nome_pet = nome_pet
        self.idade_pet = idade_pet
        self.cliente_cpf = cliente_cpf
        self.genero_id = genero_id
        self.animal_idanimal = animal_idanimal
        self.observacao_pet = observacao_pet

    @staticmethod
    def cadastrar_pet(data):
        connection = create_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO pet (nome_pet, idade_pet, cliente_cpf, genero_id, animal_idanimal, observacao_pet)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            data['nome_pet'], data['idade_pet'], data['cliente_cpf'],
            data['genero_id'], data['animal_idanimal'], data['observacao_pet']
        )
        cursor.execute(query, values)
        connection.commit()

        close_connection(connection)
        return {"message": "Pet cadastrado com sucesso!"}
