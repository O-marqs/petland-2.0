import bcrypt
import logging

# Configurando o logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Simulando um "banco de dados" com um dicionário para armazenar os usuários e seus hashes de senha
usuarios_db = {}

def cadastrar_usuario(nome_usuario, senha):
    # Verifica se o usuário já está cadastrado
    if nome_usuario in usuarios_db:
        logging.warning(f"Tentativa de cadastro falhou: usuário '{nome_usuario}' já existe.")
        print(f"Usuário '{nome_usuario}' já existe.")
        return

    # Gerar o hash da senha
    hashed_senha = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
    # Armazenar o usuário e o hash da senha no "banco de dados"
    usuarios_db[nome_usuario] = hashed_senha
    logging.info(f"Usuário '{nome_usuario}' cadastrado com sucesso! Hash: {hashed_senha.decode('utf-8')}")

def fazer_login(nome_usuario, senha_tentativa):
    # Verificar se o usuário está cadastrado
    if nome_usuario in usuarios_db:
        # Obter o hash armazenado da senha
        hashed_senha = usuarios_db[nome_usuario]
        print(f"Hash armazenado: {hashed_senha.decode('utf-8')}")

        # Rehash da senha tentada para comparação
        hashed_tentativa = bcrypt.hashpw(senha_tentativa.encode('utf-8'), hashed_senha[:29])  # Usando o mesmo salt
        print(f"Hash da senha tentada: {hashed_tentativa.decode('utf-8')}")

        # Verificar se a senha tentada corresponde ao hash
        if bcrypt.checkpw(senha_tentativa.encode('utf-8'), hashed_senha):
            logging.info(f"Login bem-sucedido para o usuário '{nome_usuario}'.")
            print("Login bem-sucedido!")
        else:
            logging.warning(f"Senha incorreta para o usuário '{nome_usuario}'.")
            print("Senha incorreta.")
    else:
        logging.warning(f"Tentativa de login falhou: usuário '{nome_usuario}' não encontrado.")
        print("Usuário não encontrado.")

# Exemplo de uso
if __name__ == "__main__":
    # Cadastrar um usuário
    cadastrar_usuario("usuario1", "1234")
    
    # Fazer login com a senha correta
    fazer_login("usuario1", "1234")  # Deve exibir "Login bem-sucedido!"
    
    # Fazer login com a senha incorreta
    fazer_login("usuario1", "senha_errada")  # Deve exibir "Senha incorreta."
    
    # Tentativa de cadastro de um usuário existente
    cadastrar_usuario("usuario1", "1234")  # Deve exibir "Usuário 'usuario1' já existe."
    
    # Tentativa de login com usuário não encontrado
    fazer_login("usuario2", "1234")  # Deve exibir "Usuário não encontrado."
