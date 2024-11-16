from config.database import create_connection, close_connection


class Pet:
    def __init__(self, nome_pet, idade_pet, cliente_cpf1, genero_id, animal_idanimal, observacao_pet, id_pet, tipo_pet, nome_genero):
        self.id_pet = id_pet
        self.nome_pet = nome_pet
        self.idade_pet = idade_pet
        self.cliente_cpfl = cliente_cpf1
        self.genero_id = genero_id
        self.animal_idanimal = animal_idanimal
        self.observacao_pet = observacao_pet
        self.tipo_pet = tipo_pet
        self.nome_genero = nome_genero

    """  def __str__(self):
            return f"Pet(ID: {self.id_pet}, Nome: {self.nome_pet}, Idade: {self.idade_pet}, Espécie: {self.tipo_pet}, cliente: {self.cliente_cpf1}, Porte: {self.porte}, Gênero: {self.nome_genero}, Observações: {self.observacao_pet}"
    """
    @staticmethod
    def cadastrar_pet(data, cpf_cliente):
        connection = create_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO pet (nome_pet, idade_pet, cliente_cpf1, genero_id, animal_idanimal, observacao_pet)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            data['nome_pet'], data['idade_pet'], cpf_cliente,
            data['genero_id'], data['animal_idanimal'], data['observacao_pet']
        )
        
        try:
            cursor.execute(query, values)
            connection.commit()  # Commit para salvar no banco de dados
            print('deu certo')
            return {"message": "Pet cadastrado com sucesso!"}
        except Exception as e:
            print(f"Erro ao cadastrar pet: {e}")
            return {"message": "Erro ao cadastrar o pet. Tente novamente mais tarde."}
        finally:
            # Fecha a conexão e o cursor
            cursor.close()
            close_connection(connection)


    @classmethod
    def get_all_pets(cls, user_id):
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        query = """select p.id_pet as id_pet, 
                     p.nome_pet as nome_pet, 
                     p.idade_pet as idade_pet, 
                     r.descricao_raca as tipo_pet, 
                     p.cliente_cpf1 as cliente_cpf1, 
                     p.genero_id as genero_id, 
                     g.nome_genero as nome_genero,
                     p.animal_idanimal as animal_idanimal, 
                     p.observacao_pet as observacao_pet 
                  from pet p 
                  inner join raca r on animal_idanimal = id_raca
                  INNER JOIN genero g ON p.genero_id = g.id_genero
                  WHERE cliente_cpf1 = %s"""
        cursor.execute(query, (user_id,))
        pets = cursor.fetchall()
        close_connection(connection)
        return [cls(**pet) for pet in pets]

    @classmethod
    def buscar_por_id(cls, pet_id):
        # Implemente a lógica para buscar o pet no banco de dados
        conn = create_connection()  # Sua função de conexão
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT p.id_pet as id_pet, 
               p.nome_pet as nome_pet, 
               p.idade_pet as idade_pet, 
               r.descricao_raca as tipo_pet, 
               p.cliente_cpf1 as cliente_cpf1, 
               p.genero_id as genero_id, 
               g.nome_genero as nome_genero,  -- Novo campo 'nome_genero' vindo da tabela 'genero'
               p.animal_idanimal as animal_idanimal, 
               p.observacao_pet as observacao_pet 
        FROM pet p
        INNER JOIN raca r ON p.animal_idanimal = r.id_raca
        INNER JOIN genero g ON p.genero_id = g.id_genero  -- Fazendo o JOIN com a tabela 'genero'
        WHERE p.id_pet = %s
         """
        cursor.execute(query, (pet_id,))
        pet = cursor.fetchone()
        close_connection(conn)
        if pet:
            return cls(**pet)  # Ajuste conforme o seu construtor
        return None



    @staticmethod
    def atualizar_pet(id_pet, data):
        connection = create_connection()
        cursor = connection.cursor()

        query = """
        UPDATE pet
        SET nome_pet = %s, observacao_pet = %s
        WHERE id_pet = %s
        """
        values = (
            data['nome'],
            data['observacoes'], id_pet
        )
        cursor.execute(query, values)
        connection.commit()

        close_connection(connection)
        return {"message": "Cliente atualizado com sucesso!"}
    
    
    
    
class CatalogoPet:
    @staticmethod
    def get_especies():
        conexao = create_connection()
        cursor = conexao.cursor()
        cursor.execute("SELECT id_especie, descricao_especie FROM especie")
        especies = cursor.fetchall()
        close_connection(conexao)
        return [{"id": e[0], "nome": e[1]} for e in especies]

    @staticmethod
    def get_racas(especie_id):
        conexao = create_connection()
        cursor = conexao.cursor()
        cursor.execute("SELECT id_raca, descricao_raca FROM raca WHERE espécie_id = %s", (especie_id,))
        racas = cursor.fetchall()
        close_connection(conexao)
        return [{"id": r[0], "nome": r[1]} for r in racas]

    @staticmethod
    def get_generos():
        conexao = create_connection()
        cursor = conexao.cursor()
        cursor.execute("SELECT id_genero, nome_genero FROM genero")
        generos = cursor.fetchall()
        close_connection(conexao)
        return [{"id": g[0], "nome": g[1]} for g in generos]
